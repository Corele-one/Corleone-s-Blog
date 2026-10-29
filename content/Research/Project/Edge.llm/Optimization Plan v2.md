下面这份可以直接作为给 Codex 的执行计划。核心原则是：**不要把项目继续收缩成“优化 exp”**，而是把 Attention Kernel 当作一个完整的异构流水来优化。

目标分成你指定的三层：

\[ \boxed{ \text{Exp microkernel} \rightarrow \text{HVX Softmax dataflow} \rightarrow \text{HMX/HVX/DMA pipeline} } \]

其中第一阶段的 SCNA 只是 candidate。**即使 SCNA 最终打不过 EXP-LUT，也不影响后两阶段继续推进。**

---

# PLAN: Optimize FlashAttention on Hexagon NPU

## 0. Overall Goal

当前目标不是寻找新的 exponential approximation，而是：

> **系统性降低 FlashAttention Attention Kernel 在 Hexagon NPU 上的执行时间，重点解决 HVX vector-side bottleneck，并进一步让 HVX、HMX 与 DMA 形成高利用率流水。**

优化分为三个逐级层次：

```
Stage 1
Exp Microkernel
    ↓
Stage 2
HVX Softmax Dataflow
    ↓
Stage 3
HMX / HVX / DMA Pipeline
```

三个阶段的关系不是：

```
SCNA success
    ↓
Stage 2
```

而是：

```
              ┌─ SCNA
              ├─ EXP-LUT
Stage 1 ──────┼─ current polynomial
              └─ optional other candidate
                     │
                     ↓
           select best microkernel
                     │
                     ↓
Stage 2: optimize entire HVX Softmax
                     │
                     ↓
Stage 3: overlap HMX/HVX/DMA
```

因此：

> **不要为了证明 SCNA 有效而强行继续优化 SCNA。**

如果 SCNA 在公平 benchmark 下仍然慢于 EXP-LUT，则保留实验结果，选择当前最快实现进入 Stage 2。

---

# 1. General Experimental Rules

所有性能优化必须遵循以下原则。

### 1.1 One optimization at a time

禁止一次同时修改：

- exp algorithm；
- softmax layout；
- tile size；
- HMX scheduling；
- DMA pipeline。

每次 commit 尽量只改变一个因素，否则 benchmark 无法归因。

建议维护：

```
baseline
candidate/scna
opt/exp-microkernel
opt/softmax-register
opt/softmax-unroll
opt/softmax-threading
opt/fa-double-buffer
opt/fa-overlap
```

或者使用等价的独立实验目录。

---

## 1.2 每个优化都必须测三类结果

### Correctness

至少记录：

```
max_abs_error
max_rel_error
mean_abs_error
```

以及最终 Attention output 与 reference 的误差。

如果已有 correctness/reference test，优先复用现有测试。

---

### Microbenchmark latency

至少测：

```
exp latency
softmax latency
QK latency
PV latency
whole attention tile latency
whole attention kernel latency
```

不要只记录端到端时间。

---

### System utilization

如果现有 trace / PMU 支持，尽量记录：

```
HVX busy time
HMX busy time
DMA busy time

HVX idle gaps
HMX idle gaps
DMA wait

L2/VTCM traffic
DMA bytes
```

最终希望能够画出：

```
time -------------------------------------------------->

HMX   ███████      ███████      ███████
HVX          ████         ████
DMA   ██        ██        ██

                ↓

HMX   █████████████████████████████
HVX       █████████████████████
DMA   █████████████████████████
```

即从串行阶段执行变成 overlap pipeline。

---

# 2. Stage 0 — Establish a Reliable Baseline

在做任何优化之前，先得到可靠 baseline。

## 2.1 Locate current Attention implementation

首先阅读代码并明确：

```
QK HMX kernel
Softmax HVX kernel
PV HMX kernel
DMA helper
VTCM allocation/layout
FlashAttention outer loop
```

Codex 首先输出一份代码路径说明：

```
Attention entry:
QK implementation:
Softmax implementation:
exp implementation:
PV implementation:
DMA helper:
VTCM allocator:
benchmark:
correctness test:
```

此时不要修改代码。

---

## 2.2 Draw current execution path

根据实际代码得到类似：

```
DDR / L2
   │
 DMA
   ↓
VTCM K/Q
   │
   ↓
 HMX
 QK^T
   │
   ↓
VTCM S
   │
 load
   ↓
 HVX
max / subtract
   ↓
 exp
   ↓
 reduction
   ↓
VTCM P
   │
   ↓
 HMX
 P × V
   │
   ↓
 output
```

同时标注：

```
DMA begin/end
HMX begin/end
HVX begin/end
barrier/synchronization
VTCM store/load
```

特别寻找类似：

```
wait_dma();
run_hmx();
wait_hmx();
run_softmax();
run_hmx();
```

这种强制串行关系。

---

## 2.3 Establish baseline numbers

至少选择几个典型尺寸。

例如：

```
HeadDim:
64
128

Q length:
1
32
128
256

KV length:
128
512
2048
```

如果工作重点目前是 prefill，可以偏重：

```
Q = 32 / 64 / 128 / 256
KV = 128 / 512 / 2048
```

如果 GQA 已支持，再至少增加：

```
GQA factor = 1
GQA factor = 4
```

输出：

|Case|QK|Softmax|PV|Total|
|---|---|---|---|---|
|D64 Q32 KV512|||||
|D128 Q32 KV512|||||
|D128 Q128 KV2048|||||

Stage 0 完成前不要开始优化。

---

# 3. Stage 1 — Exp Microkernel

## Goal

这一阶段不是寻找新的 exp 算法。

目标是：

> **确定当前 HVX 上最适合作为 Softmax primitive 的 exp microkernel，并分析 SCNA 为什么快或慢。**

候选：

```
Candidate A: existing EXP-LUT baseline
Candidate B: current SCNA
Candidate C: existing polynomial/Horner implementation
Candidate D: optional Estrin / improved arithmetic implementation
```

重点是 ISA mapping，而不是数学形式。

---

# 3.1 Candidate A — EXP-LUT

保持当前 EXP-LUT 实现不动，作为 baseline。

记录：

```
instructions/vector
cycles/vector
cycles/element

number of:
load
gather
permute
multiply
add
convert
```

如果可能，同时观察：

```
vgather latency
LUT location
LUT cache behavior
VTCM/L2 behavior
```

参考 baseline：

**Scaling LLM Test-Time Compute with Mobile NPU on Smartphones / EXP-LUT**，arXiv:2509.23324。

[EXP-LUT paper — arXiv 2509.23324](https://arxiv.org/abs/2509.23324?utm_source=chatgpt.com)

---

# 3.2 Candidate B — SCNA

SCNA 仍然作为第一个 alternative candidate。

但这一次不要只测：

```
SCNA latency
```

而需要拆解成：

```
SCNA math
SCNA parameter setup
SCNA comparison/tree traversal
SCNA activation/ReLU
SCNA lane permutation
SCNA reduction
SCNA format conversion
```

尤其统计：

```
permute instructions
shuffle instructions
vsplat
multiply
FMA
comparison
format conversion
```

核心问题：

> SCNA 的性能问题究竟来自 nonlinear computation 本身，还是来自为 SCNA 构造 vector data layout？

当前假设是：

\[ T_{\rm SCNA} = T_{\rm arithmetic} + T_{\rm layout} + T_{\rm permute} + T_{\rm dependency} \]

其中：

\[ T_{\rm layout}+T_{\rm permute} \]

可能已经超过并行计算获得的收益。

SCOPE 已被 MICRO 2026 接收，可作为 SCNA 算法来源。[Xinyu Chen (陈鑫宇) — HKUST(GZ)](https://soldierchen.github.io/publications/?utm_source=chatgpt.com)

[SCOPE publication page](https://soldierchen.github.io/publications/?utm_source=chatgpt.com)

---

# 3.3 Inspect generated HVX assembly

这一项是 Stage 1 的重点。

不要只看 intrinsic C。

保存：

```
SCNA assembly
EXP-LUT assembly
polynomial assembly
```

分析：

### Dependency chain

寻找：

```
A -> B -> C -> D
```

形式的连续 dependency。

例如：

```
mul
 ↓
add
 ↓
mul
 ↓
add
```

---

### VLIW packet composition

统计能否形成：

```
{ instruction A
  instruction B
  instruction C }
```

或者实际大量变成：

```
{ instruction A }
{ instruction B }
{ instruction C }
```

如果 SCNA 理论 SIMD 并行但 packet utilization 很差，需要明确记录。

---

### Permute pressure

寻找：

```
Q6_V_vdelta
Q6_V_vrdelta
shuffle
deal
pack
mux
vlalign
```

或者等价指令。

判断：

\[ \frac{\text{permute instructions}} {\text{total instructions}} \]

是否已经非常高。

---

# 3.4 Optional experiment — reduce dependency depth

如果现有 polynomial 使用 Horner，可以做一个**小规模对照实验**：

```
Horner
vs
Estrin
```

目标不是把它变成新研究方向，而是验证：

> HVX 是否显著受 dependency depth 限制。

例如：

\[ P(x) = (c_0+c_1x) +x^2(c_2+c_3x) +x^4(c_4+c_5x) \]

重点观察：

```
latency
packet utilization
multiply/add overlap
```

而不是只比较 FLOPs。

可以参考向量处理器上的 FlashAttention 工作，它同样强调 vectorization、tiling 和低成本 exp，而不是简单调用 scalar math library。[arXiv](https://arxiv.org/abs/2510.06834?utm_source=chatgpt.com)

[Vectorized FlashAttention with Low-cost Exponential Computation](https://arxiv.org/abs/2510.06834?utm_source=chatgpt.com)

---

# 3.5 Optional experiment — independent-vector interleaving

如果一个 exp 的 dependency chain 无法消除，可以尝试：

```
vector 0 stage A
vector 1 stage A
vector 2 stage A

vector 0 stage B
vector 1 stage B
vector 2 stage B
```

而不是：

```
vector 0 all stages
vector 1 all stages
vector 2 all stages
```

即：

```
software pipeline across independent vectors
```

测试：

```
1-vector
2-vector interleave
4-vector interleave
```

观察是否可以利用不同 score vectors 隐藏 latency。

---

# 3.6 Stage 1 exit criteria

Stage 1 最后只输出一个结论：

```
Selected exp microkernel = XXX
```

选择依据：

```
latency
correctness
register pressure
integration difficulty
```

不要求 SCNA 获胜。

如果：

```
SCNA > EXP-LUT latency
```

则明确记录：

```
SCNA is rejected as the production microkernel.
Reason:
    permutation overhead / dependency / register pressure / ...
```

然后直接使用 EXP-LUT 进入 Stage 2。

**不要继续无休止优化 SCNA。**

---

# 4. Stage 2 — HVX Softmax Dataflow

Stage 2 才是整个计划里最重要的部分之一。

## Goal

从：

```
load S
max
store
load
exp
store
load
sum
store
```

逐渐改造成：

```
load S
 │
 ├─ max
 │
 ├─ exp
 │
 ├─ sum
 │
 └─ P
      ↓
keep intermediate values
in HVX registers as long as possible
```

核心目标：

\[ \boxed{ \text{减少 VMEM/VTCM round-trip} } \]

和：

\[ \boxed{ \text{增加 HVX instruction-level parallelism} } \]

---

# 4.1 Make the current Softmax dataflow explicit

先画出当前一个 row/tile 的实际过程。

例如：

```
S from VTCM
    ↓
row max
    ↓
M_new
    ↓
store/load?
    ↓
S - M
    ↓
exp
    ↓
P
    ↓
rowsum
    ↓
L_new
    ↓
rescale old O
    ↓
store P
```

标出每个 intermediate：

```
S
M
M_new
M_old - M_new
P
row_sum
L
rescale
```

它分别位于：

```
HVX register
scalar register
VTCM
L2
```

---

# 4.2 Register-resident Softmax

第一项真正的 Stage 2 优化：

> **尽量延长 intermediate 在 HVX Vector Register File 中的生命周期。**

优先避免：

```
HVX
 ↓
VTCM
 ↓
HVX
```

尤其是：

```
rowmax
rowsum
m
l
rescale factor
```

查看是否能够把：

```
M_vec
L_vec
row_sum
row_max
```

在一个 KV block iteration 中持续保留在 vector register。

不要为了寄存器驻留导致严重 spill。

因此同时记录：

```
register count
spill loads
spill stores
```

---

# 4.3 Fuse Softmax stages

检查当前是否存在分离 pass：

```
Pass 1: max
Pass 2: exp
Pass 3: sum
```

尽量融合。

目标：

```
one S load
    ↓
max / subtract
    ↓
exp
    ↓
sum
```

避免：

\[ S \rightarrow VTCM \rightarrow HVX \rightarrow VTCM \rightarrow HVX \]

---

# 4.4 Unroll the Softmax loop

测试：

```
unroll = 1
unroll = 2
unroll = 4
```

不要默认越大越好。

测：

```
latency
code size
register pressure
spill
```

FlashAttention-V 在 scalable vector architectures 上明确将 **loop reordering 和 loop unrolling**作为核心优化，并通过跨 head 并行增加 register reuse 与 ILP。[arXiv](https://arxiv.org/abs/2608.18656?utm_source=chatgpt.com)

[FlashAttention for Scalable Vector Architectures — arXiv 2608.18656](https://arxiv.org/abs/2608.18656?utm_source=chatgpt.com)

重点借鉴思想，而不是直接照搬 RVV 实现。

HVX 是固定宽度架构，因此关注：

```
loop reorder
unroll
independent work interleaving
register reuse
```

比“超长 vector packing”本身更重要。

---

# 4.5 Reorder work across rows / heads

测试 Softmax 是否可以从：

```
row0 complete
row1 complete
row2 complete
```

调整成：

```
row0 stage A
row1 stage A
row2 stage A

row0 stage B
row1 stage B
row2 stage B
```

让 HVX 在一个 row 等待 dependency 时处理另一个 row。

如果存在 GQA，再测试：

```
multiple Q heads sharing K/V
```

是否可以成为 natural independent work。

目标是让 VLIW scheduler 有更多 independent instructions 可 packet。

---

# 4.6 Reduce online-softmax bookkeeping

这一阶段不要马上实现新的 Attention algorithm。

先统计 online softmax 每 KV tile 实际成本：

```
rowmax
M_new
M_old - M_new
exp(M_old-M_new)
old-O rescale
P exp
rowsum
L update
```

计算：

\[ T_{\rm vector} = T_{\max} + T_{\exp} + T_{\sum} + T_{\rm rescale} \]

然后判断真正瓶颈是不是已经从：

```
exp
```

迁移到了：

```
reduction + rescale
```

如果是，进入 VFA exploration。

---

# 4.7 Explore VFA only after profiling

VFA 的价值在于：

> 不再只优化 exp，而是减少 FlashAttention online-softmax 本身需要做的 vector operations。

论文指出，当矩阵单元越来越快时，rowmax、rowsum 和 rescale chain 可能成为 vector/SIMD bottleneck。[arXiv](https://arxiv.org/abs/2604.12798?utm_source=chatgpt.com)

[VFA: Relieving Vector Operations in Flash Attention](https://arxiv.org/abs/2604.12798?utm_source=chatgpt.com)

Codex 此阶段**先做 feasibility study，不立即重写算法**：

回答：

```
1. 当前 kernel 每个 KV block 更新几次 max？
2. 每次 max update 是否触发 old output rescale？
3. rescale 占 Softmax latency 的比例是多少？
4. VFA 的 max stabilization/reordering 是否适用于当前 causal attention？
5. 是否需要额外 metadata？
6. 是否仍保持 exact / numerically acceptable attention？
```

只有 profiling 显示：

```
rowmax + rescale
```

确实显著时才继续实现。

---

# 4.8 Use llama.cpp Hexagon implementation as primary engineering reference

这一项非常重要。

Qualcomm 最近 upstream 的 llama.cpp Hexagon FlashAttention 已经实现了一批与当前目标高度一致的优化。

PR：

**hexagon: further improved pipeline of the core bits (L2, DMA, MM, FA), #26049**。[GitHub](https://github.com/ggml-org/llama.cpp/pull/26049)

[llama.cpp Hexagon PR #26049](https://github.com/ggml-org/llama.cpp/pull/26049?utm_source=chatgpt.com)

重点分析：

```
keep things in HVX registers
softmax unrolling
work distribution
VTCM layout
double buffering
DMA prefetch
QK/softmax overlap
rescale/HMX overlap
```

当前 upstream 的 `flash-attn-ops.h` 已经包含 VTCM layout、S/P double buffers 和基于 softmax cost 的 `(Br,Bc)` search。[GitHub](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.h?utm_source=chatgpt.com)

[llama.cpp Hexagon flash-attn-ops.h](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.h?utm_source=chatgpt.com)

对应 implementation：

[llama.cpp Hexagon flash-attn-ops.c](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.c?utm_source=chatgpt.com)

Codex 不要直接 copy。

应该输出：

```
Technique in llama.cpp
Current implementation equivalent
Difference
Can port?
Expected benefit
Implementation complexity
```

---

# 4.9 Build a Softmax cost model

Stage 2 后期建立：

\[ C_{\rm softmax} = C_{\rm load} + C_{\rm max} + C_{\rm exp} + C_{\rm reduction} + C_{\rm rescale} + C_{\rm store} \]

进一步拆成：

\[ C_{\rm softmax} = N_{\rm vec} \cdot C_{\rm vec} + N_{\rm permute} \cdot C_{\rm permute} + N_{\rm memory} \cdot C_{\rm memory} \]

至少可以通过 microbenchmark 得到经验系数。

目的不是精确模拟硬件。

而是回答：

```
为什么 Br=32 比 Br=64 快？
为什么 Bc=64 比 Bc=128 快？
为什么更多 parallelism 反而变慢？
```

---

# 4.10 Stage 2 exit criteria

Stage 2 最终要得到：

### A. 一个更快的 HVX Softmax

相对于 Stage 0：

```
Softmax latency ↓
Attention latency ↓
```

---

### B. 一个明确 bottleneck breakdown

例如：

```
before:

exp          45%
reduction    20%
memory       20%
rescale      15%

after:

exp          25%
reduction    30%
memory       15%
rescale      30%
```

---

### C. 确定下一阶段 overlap target

例如：

```
T_HMX QK   = 15 us
T_HVX SFM  = 11 us
T_HMX PV   = 13 us
T_DMA      = 8 us
```

这会直接决定 Stage 3 pipeline。

---

# 5. Stage 3 — HMX / HVX / DMA Pipeline

这是系统级优化阶段。

## Goal

从：

\[ T = T_{\rm DMA} + T_{\rm QK} + T_{\rm Softmax} + T_{\rm PV} \]

向：

\[ T \approx \max ( T_{\rm DMA}, T_{\rm HMX}, T_{\rm HVX} ) \]

逼近。

---

# 5.1 First reconstruct the current timeline

使用已有 trace instrumentation。

画：

```
time ------------------------------------------------>

DMA K0 ███

QK0        █████

SFM0             ████

PV0                   █████

DMA K1                       ███

QK1                              █████
```

识别：

```
HMX idle
HVX idle
DMA idle

barrier
wait
synchronization
```

每一个空洞都作为 optimization target。

---

# 5.2 Double-buffer K/V

最基础 pipeline：

```
buffer 0:
K0 V0 → compute

buffer 1:
K1 V1 → DMA
```

执行：

```
compute block i
       +
prefetch block i+1
```

也就是：

```
DMA:   K0 ─ K1 ─ K2 ─ K3

HMX:       QK0─ QK1─ QK2
```

检查现有代码是否已有 double buffer。

如果已有，不要重新实现，验证 DMA 是否真的 overlap。

---

# 5.3 Double-buffer S/P

进一步：

```
S buffer 0
S buffer 1

P buffer 0
P buffer 1
```

目标：

```
HMX computes S[i+1]

while

HVX softmaxes S[i]

while

HMX consumes P[i-1]
```

概念目标：

```
time ------------------------------------------------>

HMX-QK   QK0 █████
              QK1 █████
                   QK2 █████

HVX-SFM       SFM0 ████
                   SFM1 ████
                        SFM2 ████

HMX-PV             PV0 █████
                        PV1 █████
```

---

# 5.4 Overlap QK and Softmax

优先寻找：

```
QK[i+1]
||
Softmax[i]
```

前提：

```
different buffers
no data hazard
HMX/HVX can execute concurrently
```

测：

```
serialized latency
vs
overlap latency
```

如果：

\[ T_{\rm QK}=10 \]\[ T_{\rm SFM}=8 \]

理想 overlap 应接近：

\[ 10 \]

而不是：

\[ 18 \]

---

# 5.5 Overlap Softmax and PV

随后尝试：

```
Softmax[i+1]
||
PV[i]
```

注意：

```
P buffer ownership
HMX resource conflicts
VTCM bandwidth
```

不要只看 HMX 和 HVX 是否逻辑独立。

它们可能仍竞争：

```
VTCM
memory ports
scheduler
```

因此必须真实 benchmark。

---

# 5.6 Move DMA earlier

对每个 DMA：

```
K
V
Q
mask
scale
```

检查当前：

```
when DMA is issued
```

尽量把：

```
DMA issue
```

从：

```
right before use
```

提前到：

```
earliest point with valid source/destination
```

目标：

```
issue early
consume late
```

减少：

```
wait_dma
```

---

# 5.7 Build a three-stage pipeline

最终目标：

```
Stage A:
DMA / preparation

Stage B:
HMX QK

Stage C:
HVX Softmax

Stage D:
HMX PV
```

在 steady state 中：

```
iteration i-1     PV

iteration i       Softmax

iteration i+1     QK

iteration i+2     DMA
```

概念上：

```
time -------------------------------------------------------->

DMA    KV0  KV1  KV2  KV3  KV4

QK          QK0  QK1  QK2  QK3

HVX              SF0  SF1  SF2

PV                     PV0  PV1  PV2
```

---

# 5.8 VTCM capacity must constrain tiling

不能为了 double buffering 无限增加 buffer。

建立：

\[ VTCM = Q + 2K + 2V + 2S + 2P + scratch + M/L + mask + HMX\ buffers \]

对于每组：

```
Br
Bc
head_dim
GQA_factor
thread count
```

计算准确 VTCM usage。

若超过 budget：

```
reject configuration
```

不要等 runtime failure。

---

# 5.9 HMX granularity must influence tile selection

HMX V81 不是任意矩阵抽象。

官方手册规定 FP16 activation crouton 是：

\[ 32\times32\times16\text{ bit}=2\,\text{KB} \]

并要求相应 VTCM address 2 KB 对齐。[Qualcomm Docs](https://docs.qualcomm.com/doc/80-N2040-62/80-N2040-62_REV_AA_Qualcomm_Hexagon_V81_HMX_Programmers_Reference_Manual.pdf)

[Qualcomm Hexagon V81 HMX Programmer Reference Manual](https://docs.qualcomm.com/doc/80-N2040-62/80-N2040-62_REV_AA_Qualcomm_Hexagon_V81_HMX_Programmers_Reference_Manual.pdf?utm_source=chatgpt.com)

因此 tile search 不应该只优化：

\[ Br\times Bc \]

还应该考虑：

```
HMX tile utilization
crouton packing
VTCM alignment
HVX vector count
DMA efficiency
```

---

# 5.10 Build a global tile cost model

最终 cost model 不再只看 HMX。

定义：

\[ C_{\rm HMX}(Br,Bc) \]\[ C_{\rm HVX}(Br,Bc) \]\[ C_{\rm DMA}(Br,Bc) \]\[ C_{\rm sync}(Br,Bc) \]

串行版本：

\[ C= C_{\rm HMX} + C_{\rm HVX} + C_{\rm DMA} + C_{\rm sync} \]

pipeline 版本：

\[ C \approx \max( C_{\rm HMX}, C_{\rm HVX}, C_{\rm DMA} ) + C_{\rm sync} \]

遍历有限候选：

```
Br = ...
Bc = ...
```

选择预测最优 tile。

不要先做复杂 ML cost model。

先用 profiling-calibrated constants。

llama.cpp 当前 Hexagon FlashAttention 已经在做类似的 cost-based `(Br,Bc)` search，并显式将 Softmax HVX cost 纳入选择。[GitHub](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.h?utm_source=chatgpt.com)

这应该作为非常重要的参考。

---

# 5.11 FlashAttention-3 as pipeline inspiration

FA3 的硬件是 NVIDIA Hopper，不要照搬 warp-specialization。

需要借鉴的是思想：

> matrix multiply、softmax 与 memory movement 不应该严格串行。

FA3 使用 asynchronous execution 对 matmul、softmax 和数据搬运进行 interleaving。[arXiv](https://arxiv.org/abs/2407.08608?utm_source=chatgpt.com)

[FlashAttention-3](https://arxiv.org/abs/2407.08608?utm_source=chatgpt.com)

映射关系：

```
FA3 Tensor Core
      ↓
Hexagon HMX

FA3 CUDA/SIMT softmax work
      ↓
HVX

FA3 TMA
      ↓
Hexagon DMA
```

只借鉴：

```
asynchrony
double buffering
producer-consumer pipeline
compute/memory overlap
```

---

# 5.12 Qualcomm Hexagon-MLIR as architecture-level reference

Qualcomm 自己的 Hexagon-MLIR 优化列表包括：

```
operator fusion
TCM tiling
HVX multithreading
double buffering
compute/memory overlap
vectorization
```

这些正好可以作为 Stage 2/3 的官方设计依据。[高通](https://www.qualcomm.com/developer/blog/2026/02/build-faster-on-hexagon-npu-tritor-pytorch-with-hexagon-mlir-open-source?utm_source=chatgpt.com)

[Qualcomm Hexagon-MLIR optimization article](https://www.qualcomm.com/developer/blog/2026/02/build-faster-on-hexagon-npu-tritor-pytorch-with-hexagon-mlir-open-source?utm_source=chatgpt.com)

---

# 6. Optional Stage 4 — Algorithm/System Co-design

这一阶段**不是当前主任务**。

只有前三阶段结束后才考虑。

两个可能方向。

---

## 6.1 Vector-relieved Attention

如果 Stage 2 最终发现：

```
exp no longer dominates
```

而：

```
rowmax
rowsum
rescale
```

占主要 latency，则继续 VFA。

问题从：

> How to make exp faster?

变成：

> How to reduce the number of vector operations required by online softmax?

这会比继续换 exp approximation 更有研究意义。

---

## 6.2 Representation/data-layout co-design

参考 T-MAN 的思想。

T-MAN 不是直接解决 FlashAttention，但它很典型地说明：

> NPU optimization 不应该仅优化 operator arithmetic，而应该围绕 vector unit、local memory、tiling 和 pipeline 重新设计数据表示和执行方式。

其系统使用 unified layout、hardware-aware tiling 和 three-stage pipeline。[arXiv](https://arxiv.org/abs/2511.11248?utm_source=chatgpt.com)

[T-MAN — arXiv 2511.11248](https://arxiv.org/abs/2511.11248?utm_source=chatgpt.com)

只作为 system-design reference。

不要在当前阶段转向 LUT 研究。

---

# 7. Required Final Ablation

完成前三阶段后，必须得到以下 ablation：

|Version|Exp|Softmax Dataflow|Pipeline|
|---|---|---|---|
|V0|EXP-LUT baseline|baseline|baseline|
|V1|best microkernel|baseline|baseline|
|V2|best microkernel|optimized|baseline|
|V3|best microkernel|optimized|HMX/HVX overlap|
|V4|best microkernel|optimized|HMX/HVX/DMA pipeline|

记录：

```
QK latency
Softmax latency
PV latency
Attention latency
speedup
correctness
```

最终需要能够回答：

\[ \text{总加速} = \text{microkernel contribution} + \text{dataflow contribution} + \text{pipeline contribution} \]

而不能只有：

```
final implementation is X% faster
```

---

# 8. Required Negative Results

不要删除失败实验。

至少保留：

```
SCNA serial
SCNA lane-parallel
SCNA optimized
EXP-LUT
polynomial
```

如果 SCNA 失败，需要给出硬件原因。

例如：

```
SCNA arithmetic count is lower,
but the implementation requires 35% more permutation instructions.

The additional permutation and dependency pressure
outweighs lane-level parallelism.
```

这种 negative result 本身非常重要。

它能支持一个更大的 observation：

> **On a heterogeneous NPU, vector-side performance is determined by ISA mapping and dataflow rather than arithmetic operation count alone.**

---

# 9. Reference Priority

Codex 阅读顺序：

### Priority S — 必须读

**1. V79 HVX Programmer Reference Manual**

重点：

```
instruction resources
packet rules
latency
HVX registers
VMEM
permute
multiply
floating-point instructions
```

[Qualcomm V79 HVX Programmer Reference Manual](https://docs.qualcomm.com/doc/80-N2040-61/topic/introduction.html?utm_source=chatgpt.com)

---

**2. llama.cpp Hexagon PR #26049**

重点：

```
L2
DMA
MM
FlashAttention
HVX register reuse
Softmax unroll
double buffer
pipeline
```

[llama.cpp PR #26049](https://github.com/ggml-org/llama.cpp/pull/26049?utm_source=chatgpt.com)

---

**3. Current upstream Hexagon FlashAttention**

[flash-attn-ops.h](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.h?utm_source=chatgpt.com)

[flash-attn-ops.c](https://github.com/ggml-org/llama.cpp/blob/master/ggml/src/ggml-hexagon/htp/flash-attn-ops.c?utm_source=chatgpt.com)

---

**4. HMX V81 Programmer Reference**

重点：

```
HMX tile
crouton
VTCM layout
alignment
matrix operation
```

[Qualcomm V81 HMX Programmer Reference Manual](https://docs.qualcomm.com/doc/80-N2040-62/80-N2040-62_REV_AA_Qualcomm_Hexagon_V81_HMX_Programmers_Reference_Manual.pdf?utm_source=chatgpt.com)

---

### Priority A — 主要研究参考

**5. FlashAttention-V**

重点：

```
loop reorder
loop unroll
cross-head parallelism
register reuse
vector utilization
```

[FlashAttention for Scalable Vector Architectures](https://arxiv.org/abs/2608.18656?utm_source=chatgpt.com)

---

**6. VFA**

重点：

```
vector bottleneck
rowmax
rowsum
rescale
reducing online-softmax vector work
```

[VFA: Relieving Vector Operations in Flash Attention](https://arxiv.org/abs/2604.12798?utm_source=chatgpt.com)

---

**7. FlashAttention-3**

重点：

```
asynchronous pipeline
matmul/softmax overlap
memory/compute overlap
```

[FlashAttention-3](https://arxiv.org/abs/2407.08608?utm_source=chatgpt.com)

---

### Priority B — 补充参考

**8. Vectorized FlashAttention on RISC-V**

重点：

```
vectorized online softmax
exp implementation
tiling
vector execution
```

[Vectorized FlashAttention with Low-cost Exponential Computation](https://arxiv.org/abs/2510.06834?utm_source=chatgpt.com)

---

**9. Qualcomm Hexagon-MLIR**

重点：

```
TCM tiling
fusion
HVX multithreading
double buffering
compute-memory overlap
```

[Hexagon-MLIR optimization article](https://www.qualcomm.com/developer/blog/2026/02/build-faster-on-hexagon-npu-tritor-pytorch-with-hexagon-mlir-open-source?utm_source=chatgpt.com)

---

**10. T-MAN**

重点：

```
NPU system co-design
vector bottleneck
hardware-aware tiling
pipeline
layout
```

[T-MAN](https://arxiv.org/abs/2511.11248?utm_source=chatgpt.com)

---

# 10. Codex Execution Order

严格按以下顺序推进：

```
[0] Inspect repository
      ↓
[1] Reproduce correctness + baseline
      ↓
[2] Profile current Attention timeline
      ↓
[3] Benchmark EXP-LUT / SCNA / polynomial
      ↓
[4] Inspect HVX assembly
      ↓
[5] Select best exp microkernel
      ↓
[6] Register-resident Softmax
      ↓
[7] Softmax fusion
      ↓
[8] Loop unroll / row-head interleaving
      ↓
[9] Profile again
      ↓
[10] Determine vector bottleneck composition
      ↓
[11] Build K/V double buffering
      ↓
[12] Build S/P double buffering
      ↓
[13] QK[i+1] || Softmax[i]
      ↓
[14] Softmax[i+1] || PV[i]
      ↓
[15] Move DMA earlier
      ↓
[16] Build full HMX/HVX/DMA pipeline
      ↓
[17] Build Br/Bc cost model
      ↓
[18] Full ablation
```

不要跳到 Stage 3 后才回来补 baseline。

---

# 11. Definition of Success

项目的成功条件不再定义为：

```
SCNA beats EXP-LUT
```

而定义为：

### Level 1

找到 HVX 最好的 exp microkernel，并解释其他候选为什么输。

### Level 2

显著降低整个 HVX online-softmax latency。

### Level 3

通过 HMX/HVX/DMA overlap 降低 Attention kernel wall-clock latency。

最终优化对象是：

\[ \boxed{ T_{\rm Attention} } \]

而不是：

\[ T_{\rm exp} \]

最理想的结果甚至可能是：

```
EXP-LUT unchanged
+
30% faster HVX Softmax dataflow
+
25% pipeline gain
=
substantially faster Attention
```

这完全符合项目目标。

---

我觉得这版计划有一个很关键的转变：**SCNA 从“必须证明有效的核心方案”降级成了一个 microkernel candidate**。这样后面即使 SCNA 的实验结论仍然是不如 EXP-LUT，你也不会继续被它卡住；真正值得做的主线会自然变成 **HVX vector bottleneck → Softmax dataflow → heterogeneous pipeline**。这条线从你现在已有的实验结果接过去也非常顺。