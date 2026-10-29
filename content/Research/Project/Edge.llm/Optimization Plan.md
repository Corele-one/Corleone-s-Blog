# Origin

[[2026-07-31_2026-08-06_SCNA_Bottleneck-Analysis]]

# PLAN1

对目前实现的scnaKernel做实现冗余上的优化
## Previous

```c
//每个 block 都重新获取取/并转换 w,b (FP32-FP16)
sum = 0;
for (i = 0; i < runtime_width; ++i) {  
//在运行时进行判断，编译器难以对特定的neuron数进行彻底的优化
//d8-d16-d32共用一套循环
    w = convert_and_broadcast(wk[i]);
    b = convert_and_broadcast(bk[i]);
    affine = b + x * w; //vmpyacc
    sum += max(affine, 0);//累加依赖
}
```

## Optimazation

```c
pack_fp16_bits_once(wk, bk);       
// Attention 开始时一次完成

//两行共享一次 `w/b` broadcast
scna_d8_pair(row0, row1) {        
	// d8 专用、编译期固定 kernel，去掉了内层的判断
    for (i = 0; i < 8; ++i) {
        w = broadcast(packed_w[i]); // 两行共用一次
        b = broadcast(packed_b[i]);
        sum0 += relu(vmpyacc(b, row0, w));
        sum1 += relu(vmpyacc(b, row1, w)); 
    }
}
```


## 阶段二的目标：不改变算法，只消除实现冗余

阶段二没有改变 d8 SCNA 的数学公式：

$$
f(x)=\sum_{i=0}^{7}\max(x\cdot w_i+b_i,0)
$$

也没有改变 FlashAttention 的 mask、online softmax、rowsum、P tile 或 HMX `QK/PV` 数据流。它优化的是：同一组不变的参数 `w_i,b_i` 被过于频繁地转换、广播和调度。

### 先区分三种“共享”

| 层级 | 被共享的对象 | 没有被共享的对象 |
| --- | --- | --- |
| 数学层 | 所有 score 使用同一组 d8 参数 `(w0,b0)...(w7,b7)` | 每个 score 的输入 `x` 和输出 `f(x)` |
| HVX 向量层 | 一个标量 `w[i]` 或 `b[i]` 可 broadcast 成一个 64-lane 向量 | 该 broadcast 向量只在当前 kernel 的寄存器生命周期内有效 |
| Attention 行层 | 两个 row 可以在同一时刻复用同一个 `w_vec/b_vec` | 每个 row 的 rowmax、rowsum、mask、accumulator 和输出 |

因此，阶段二不是让两行“共用一个 softmax”。两行仍是完全独立的 Attention 行；它只是让同一次 `w/b` broadcast 被两行连续消费。

## 阶段二的 dataflow

### 1. `row0` 与 `row1` 从哪里来

HMX 计算 `QK^T` 后，得到 score tile `S`。代码先将一个 KV head 对应的 `G` 个 Q head 展平：

```text
G = n_heads / n_kv_heads
本实验：G = 12 / 2 = 6

展平 row r 的含义：
query token index = r / G
Q head within this KV group = r % G
```

这里有两个完全不同的数字：

```text
G = 6：一个 KV head 服务 6 个 Q head（GQA 的语义）
2：pair kernel 每次只拿 2 条已展平的 score row（HVX 实现的粒度）
```

以 `qo_len=4`、一个 KV head 为例，score tile 有 `4 * 6 = 24` 条 row，而不是只有 2 条：

```text
token 0: Qh0 Qh1 Qh2 Qh3 Qh4 Qh5  -> 三个 pair: (0,1), (2,3), (4,5)
token 1: Qh0 Qh1 Qh2 Qh3 Qh4 Qh5  -> 三个 pair: (0,1), (2,3), (4,5)
token 2: ...
token 3: ...
```

所以“pair=2”不是将 6 个 Q head 缩减为 2 个；它只是把 6 条 row 分成三次两行计算。代码的内层正是以 `r += 2` 遍历这 24 条已展平的 row。

所以，对于一个 64-column K block，前两行实际是：

```text
                     K column 0                           K column 63
row0 = (query 0, Q head 0): S[0,0]  S[0,1] ... S[0,63]  -> x0：一个 64-lane FP16 HVX vector
row1 = (query 0, Q head 1): S[1,0]  S[1,1] ... S[1,63]  -> x1：另一个 64-lane FP16 HVX vector
```

- 一个 128-byte HVX vector 恰好容纳 64 个 FP16 score。
- `row0,row1` 是当前 score tile 中相邻的两个 **Attention row**。在本实验 `G=6` 且循环从偶数 `r` 开始时，它们通常是同一个 query token 的两个不同 Q head；它们属于同一 GQA group，因此共享同一个 KV head 的 K/V。
- 接下来会依次得到 `(query 0, head 2/3)`、`(query 0, head 4/5)`，然后才是 `(query 1, head 0/1)`。若 G 或起始对齐方式改变，pair 也可能跨 query token；pair SCNA 本身不依赖“必须同一 token”这个条件。
- GQA 解释了这两行在 QK/PV 阶段为什么使用同一份 K/V 数据；但 pair SCNA 调用发生在 QK 已经产生 score 之后。它之所以可以成对计算，是因为两行的 SCNA 参数相同、而且代码的数据布局和 `r += 2` 循环正好一次解码两条行。

每行必须分别执行 online softmax：

```text
row0 / (query 0, head 0): S0 -> mask -> m0=rowmax(S0) -> x0=clamp(S0-m0, -256, 0) -> SCNA -> P0 -> rowsum0 -> P0*V
row1 / (query 0, head 1): S1 -> mask -> m1=rowmax(S1) -> x1=clamp(S1-m1, -256, 0) -> SCNA -> P1 -> rowsum1 -> P1*V
```

`m0 != m1`、`rowsum0 != rowsum1`，所以不能把两行合并成一行计算。

### 2. 阶段一的实际 dataflow：按行处理，重复准备参数

```text
对每个 score row r：
    x = 该行当前 64 个 score
    sum = 0
    对 i = 0 .. runtime_width-1：
        从 wk[i], bk[i] 参数数组读取系数
        做 FP16 -> float -> FP16 的格式准备/转换
        将标量 w[i], b[i] broadcast 到 64 个 HVX lane
        affine = FP16 multiply/add/conversion 序列
        sum += ReLU(affine)
```

这里的“查表”只是读取很小的 `wk[]/bk[]` 参数数组，**不是** `exp-LUT` 那种按照输入值查指数表。问题在于参数对整个 Attention op 都不变，却在每个 64-score block、每个 row 中都反复准备。

### 3. 阶段二的实际 dataflow：先准备参数，再成对计算行

```text
Attention op 开始时（一次）：
    wk[0..7], bk[0..7]
        -> 转为 FP16 的 16-bit 表示
        -> 打包为 coeff_bits[0..7] = {w_bits, b_bits}

对一对 score row (x0, x1)：
    sum0 = 0；sum1 = 0
    对 i = 0 .. 7：                    // d8 专用；编译期固定，完整展开
        w_vec = broadcast(coeff_bits[i].w)
        b_vec = broadcast(coeff_bits[i].b)

        affine0 = vmpyacc(b_vec, x0, w_vec)
        affine1 = vmpyacc(b_vec, x1, w_vec)
        sum0 += ReLU(affine0)
        sum1 += ReLU(affine1)
```

可以把最重要的循环变换理解为：

```text
阶段一：对每一行 -> 对每个 neuron -> 准备并 broadcast 参数
阶段二：对每个 neuron -> 准备并 broadcast 一次参数 -> 用于 row0 和 row1
```

HVX 并没有用“一条 FMA 指令同时计算两个 row”。它仍需要：

```text
FMA(x0, w_vec, b_vec)  // 一个 64-lane 向量 FMA
FMA(x1, w_vec, b_vec)  // 另一个 64-lane 向量 FMA
```

被省掉的是第二次 `w_vec/b_vec` 的构造，而两个独立 accumulator 还可以给指令调度器更多可交错的工作。

## 各项优化分别解决什么问题

| 改动 | 阶段一的问题 | 阶段二的做法 | 为什么有效 |
| --- | --- | --- | --- |
| FP16 参数预打包 | 每个 block 反复做 `w/b` 格式转换 | Attention 开始时转换一次，热循环只读 `coeff_bits` | 将不随 score 改变的工作移出热点 |
| 静态 d8 kernel | d8/d16/d32 共用运行时 `width` 循环 | 只分派一次 d8，随后进入循环上界固定为 8 的专用函数 | 编译器可完整展开 8 次，改善寄存器和指令调度；不仅仅是少一个 `if` |
| row pair | row0、row1 分别构造相同的 `w_vec/b_vec` | 同一参数向量先后用于 `x0,x1` | 对一对行，将该参数 broadcast 成本减半 |
| `vmpyacc` | affine 要经过较长的乘、加、转换指令链 | 一条 FP16 FMA 计算 `b+x*w` | 缩短 affine 指令链，并可与 `vmax/vadd` 交错 |
| `noinline` 专用 kernel | 把所有 single/pair、d8/d16/d32 kernel 内联到 Attention worker 会导致函数/栈帧过大 | 将 width kernel 作为独立可调用函数 | 避免 cDSP stack overflow 和寄存器压力；它主要保证稳定性，不是 13x 加速的直接来源 |

## 为什么只 pair 两个 row，而不一次 pair 所有 row？

理论上更多 row 都能复用 `w_vec/b_vec`。但每多一个 row，至少要多保存一个输入 vector、一个 sum vector 和临时 affine vector；寄存器压力会增加，可能产生 spill 到栈/内存，反而降低性能。与此同时，每行仍有独立的 rowmax/rowsum/mask 状态。两个 row 是“参数复用 + 可交错计算”与“寄存器压力”之间的折中。

## 数据证明了什么，不能证明什么

| Qo | 阶段一 SCNA 子阶段 (us) | 阶段二 SCNA 子阶段 (us) | SCNA 加速 | 完整 DSP 加速 |
| --: | --: | --: | --: | --: |
| 4 | 1984.0 | 158.0 | 12.56x | 3.33x |
| 8 | 3962.0 | 313.0 | 12.66x | 4.08x |
| 16 | 7946.5 | 607.0 | 13.09x | 5.90x |
| 32 | 15869.5 | 1206.0 | 13.16x | 7.09x |

完整 DSP 加速小于 SCNA 子阶段加速，是因为阶段二没有优化 HMX QK/PV、K/V load、mask、row reduction、P store 与 host 开销。

> 口径注意：阶段一/二的完整 Attention 实现在后续被发现存在 rowsum、reciprocal 和 padded-mask stride 的正确性问题。上表可用于解释阶段二消除了多少 **SCNA 实现开销**，不能作为最终正确 Attention 的性能或精度结论。

![[route_stage2.svg]]



# PLAN2

> **与已完成阶段二的关系：** 本节是后续的专用化实验假设，不是阶段二已经采用的实现。阶段二最终将 d8/d16/d32 kernel 设为 `noinline`，因为把所有 width/single/pair 路径都 `inline` 到 Attention worker 曾导致 cDSP stack overflow。若要验证本节的 `static inline`，应作为独立消融实验，额外记录 stack frame、寄存器 spill 和性能，不能直接假定它优于 `noinline`。

- 为 `d8/direct/FP16` 做专用 `static inline` pair kernel，直接内联到 `flash_attn.c` 的 64-score 循环。
- 将 `w[i]`、`b[i]` 的 broadcast 提到 `c += 64` 循环外。参数对所有 score block 相同，不应每个 block 重建。
- 让编译器看到固定 d8 和固定参数布局，检查是否真的 hoist 了 load/splat。
- 使用两个独立 partial accumulators，把 `FMA(i)` 与 `ReLU/add(i-1)` 交错，减少单个 `sum` 的串行依赖。
- 保留当前 `scna_exp2.c` 作为 out-of-line、可配置的 reference kernel；新 header 只服务一个冻结配置，避免破坏 d16/d32/INT8 的可测性。

对 SCNA，循环应沿着**输入样本块**展开，而不是围绕“8 个 neuron”建立动态循环。因为 neuron 数固定为 8，最好的初始实现通常是编译期展开这 8 步；硬件循环则用于遍历很多个
# ~~PLAN3~~ 否决 会引入更多的实现冗余

- 对目前的软硬件计算架构做重构，希望能发挥simd的结构优势以及HVX的单元的并行化优势

![[image_0.jpg]]

# PLAN4
纯INT8的实现方案——探索
