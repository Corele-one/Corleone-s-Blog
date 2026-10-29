# 5. 硬件加速器：HMX、HVX、VTCM

## Hexagon DSP 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    Hexagon DSP                       │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  HVX Unit 0  │  │  HVX Unit 1  │  │  HVX Unit 2  │ │
│  │  128B SIMD   │  │  128B SIMD   │  │  128B SIMD   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │           HMX (Matrix eXtension)             │    │
│  │  32×32 FP16 tile 矩阵乘法                     │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │        VTCM (Vector TCM) 4-6 MB              │    │
│  │  快速片上存储，类似 GPU shared memory           │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │              L2 Cache                        │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│              ↕ DMA Engine                           │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │           DDR (设备主存)                      │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## HMX（Hexagon Matrix eXtension）

HMX 是 Hexagon DSP 的矩阵加速单元，类似于 NVIDIA GPU 的 Tensor Core 或 Apple 的 AMX。

### 核心能力

- 操作单位：**32×32 FP16 tile**
- 一次 `hmx_dot_fp16` 调用：加载两个 tile 对，做矩阵乘累加，输出结果
- 数据必须在 VTCM 中，且按 **HMX tile layout** 排列

### HMX Tile Layout

普通行主序（row-major）：
```
[row 0: col 0..31] [row 0: col 32..63] ...
[row 1: col 0..31] [row 1: col 32..63] ...
...
```

HMX tile layout：
```
Tile [0,0]: 32×32 elements, stored column-major within tile
Tile [0,1]: 32×32 elements
...
```

一个 `[32, D]` 的矩阵被组织为 `D/32` 个 tile，每个 tile 内部是列主序。这就是为什么加载 Q、K、V 时需要做 layout 转换（用 `vshuff`、`vscatter` 等 HVX 指令）。

### HMX 操作序列

```c
// 1. 设置输出缩放因子
hmx_set_output_scales(scales);  // bias = mxmem2(scales)

// 2. 加载 tile 对并做矩阵乘累加
hmx_load_tiles_fp16(row_tiles, col_tiles, n_tiles);
// 内部：activation.hf = mxmem(row, limit):deep
//       weight.hf = mxmem(col, limit)
// HMX 自动做 32×32 × 32×32 的乘累加

// 3. 读出累加器结果
hmx_consume_accumulator_fp16(out);
// 内部：cvt.hf = acc(2)
//       mxmem(out, 0) = cvt
```

### 在 FlashAttention 中的角色

| 操作 | HMX 做什么 |
|------|-----------|
| QK dot | `S = Q × K^T`，Q 和 K 都在 VTCM 中 |
| PV accumulation | `P × V`，P 和 V 都在 VTCM 中 |
| D × O_old | 对角矩阵 × O_old（用于 softmax rescaling） |
| O scaling | `diag(1/l) × O`（最终归一化） |

---

## HVX（Hexagon Vector eXtension）

HVX 是 Hexagon 的向量处理单元，128 字节宽的 SIMD（1024-bit）。

### 核心能力

- 每个 HVX_Vector 是 128 字节 = 64 个 FP16 或 32 个 FP32
- 支持 FP16/FP32/INT8/INT16 等多种数据类型的向量运算
- 有专用的数学函数：`vmax`、`vadd`、`vmpy`，以及通过组合实现的 `exp2`、`inv` 等

### 在 FlashAttention 中的角色

| 操作 | HVX 做什么 |
|------|-----------|
| FP32→FP16 转换 | `hvx_my_wsf_to_vhf`：加载 Q 时转换 |
| FP16→FP32 转换 | `hvx_my_vhf_to_wsf`：存储 O 时转换 |
| Mask 应用 | `Q6_V_vmux_QVV`：条件选择 |
| Rowmax 归约 | `Q6_Vhf_vmax_VhfVhf`：逐元素 max |
| Rowsum 归约 | `Q6_Vqf16_vadd` / `Q6_Vqf32_vadd`：逐元素 add |
| exp 计算 | `hvx_my_exp2_vhf_vqf16`：多项式近似或 LUT 查表 |
| 求倒数 | `hvx_my_inv_vhf`：用于 1/l |
| Tile layout 转换 | `vshuff`、`vdeal`、`vscatter`：数据重排 |

### HVX vs HMX 的分工

```
HMX: 做"大"的矩阵乘法（32×32 tile 级别）
     → QK dot, PV accumulation, output scaling

HVX: 做"逐元素"的向量运算
     → softmax (mask, max, exp, sum), 数据格式转换
```

这种分工很自然：HMX 擅长 compute-bound 的矩阵乘法，HVX 擅长 memory-bound 的逐元素操作。

---

## VTCM（Vector Tightly Coupled Memory）

VTCM 是 DSP 片上的快速存储，类似 GPU 的 shared memory 或 CPU 的 L1 cache，但有几点不同：

### 特点

- **大小**：通常 4-6 MB（比 GPU shared memory 大得多）
- **速度**：比 L2 cache 快，比 DDR 快很多
- **管理方式**：软件管理（不是硬件 cache），需要显式分配和 DMA 传输
- **对齐要求**：分配通常需要 4KB 对齐

### 在 FlashAttention 中的使用

每个 worker 分配 1 MB VTCM，存放所有 tile buffer：

```c
const size_t vtcm_size_per_thread = 1024 * 1024;  // 1 MB per worker
assert(n_workers * vtcm_size_per_thread <= 6 * 1024 * 1024);  // 总量不超过 6 MB
```

VTCM 的分配是线性的（`vtcm_seq_alloc`），从基地址开始依次分配各个 buffer。

### 为什么 FlashAttention 需要 VTCM？

FlashAttention 的核心是 **tiling**：每次只处理一小块 Q、K、V，中间结果（S、P）也只有一小块。这些频繁访问的数据必须放在快速存储中：

- 如果放在 DDR：每次访问都要走内存总线，延迟高
- 如果放在 L2 cache：cache 大小有限，且 eviction 不可控
- 放在 VTCM：软件控制，保证数据驻留，访问延迟最低

---

## DMA Engine

DMA（Direct Memory Access）引擎负责在 DDR 和 VTCM 之间搬运数据，不占用 HVX/HMX 的计算资源。

### 使用方式

```c
// 2D DMA 描述符
dma_desc_2d_t desc = {0};
desc.src        = (uint32_t) q_ld_base;   // 源地址（DDR）
desc.dst        = (uint32_t) q_tile;      // 目标地址（VTCM）
desc.roi_width  = blk_sz * sizeof(float); // 每行宽度
desc.roi_height = n_rows;                 // 行数
desc.src_stride = stride * sizeof(float); // 源行间距
desc.dst_stride = blk_sz * sizeof(float); // 目标行间距

dma_submit_one(&desc);    // 提交
dma_wait_for_idle();       // 等待完成
```

在 FlashAttention kernel 中，DMA 主要用于加载 Q 块（在 `fa_f32_core` 路径中）。K 和 V 的加载更多使用 `l2fetch`（L2 prefetch）+ HVX load 的方式。

### l2fetch vs DMA

```c
l2fetch(base, stride, width, height, 0);  // 预取到 L2 cache
// 后续 HVX load 会命中 L2
```

`l2fetch` 是一个提示指令，告诉硬件把数据从 DDR 预取到 L2 cache。比 DMA 轻量，但不如 VTCM 可靠（可能被 eviction）。

---

## 硬件利用率观察

从 profile timer 可以看出各硬件的使用情况：

```
典型长序列 (qo_len=4, kv_len=4096, head_dim=128):
  q_load:   ~5%   (内存)
  k_load:   ~8%   (内存)
  v_load:   ~8%   (内存)
  qk_dot:   ~25%  (HMX)  ← 矩阵乘法
  safe_sm:  ~30%  (HVX)  ← softmax 计算
  core_acc: ~15%  (HVX + HMX)
  o_scale:  ~5%   (HMX)
  o_store:  ~4%   (内存)
```

> [!note] softmax 是瓶颈？
> 对于长 KV 序列，softmax 中的逐元素操作（exp、sum）占了相当大的比例。这就是为什么 lut-exp 模式（用 LUT 查表代替多项式计算 exp）能带来显著加速——它减少了 HVX 在 softmax 阶段的计算量。

> [!next] 下一步
> 了解了硬件后，看看怎么用 profiling 工具分析性能：[[06-profiling-and-tools]]
