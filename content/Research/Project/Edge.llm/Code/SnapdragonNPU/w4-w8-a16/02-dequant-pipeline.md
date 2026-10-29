# 2. 解量化 Pipeline：HVX Dequant → HMX MMA

## 总览

```
量化权重 (Q4_0/Q8_0/IQ4_NL)     FP32 Activation
         │                              │
         ▼                              ▼
    DMA 加载到 VTCM               FP32 → FP16 转换
         │                              │
         ▼                              ▼
    HVX 解量化为 FP16             HMX tile layout 转换
         │                              │
         └──────────┬───────────────────┘
                    ▼
            HMX FP16 矩阵乘法
                    │
                    ▼
            FP16 结果 → 转回 FP32
```

核心文件：`src/htp-ops-lib-main/src/dsp/ops/mat_mul.c`（114 KB）

## VTCM 分区

矩阵乘法的 VTCM 分成 4 个区域（可在 CMake 中配置大小）：

| 区域 | 默认大小 | 用途 |
|------|---------|------|
| Weight | 1024 KB | 量化权重（从 DDR DMA 加载） |
| Activation | 2048 KB | FP16 activation（在 VTCM 中转为 HMX tile layout） |
| Output | 1536 KB | 矩阵乘法结果 |
| Scratch | 1024 KB | 临时 buffer |

```c
#define WEIGHT_AREA_SIZE     (HTP_MATMUL_WEIGHT_AREA_KB * 1024)
#define ACTIVATION_AREA_SIZE (HTP_MATMUL_ACTIVATION_AREA_KB * 1024)
#define OUTPUT_AREA_SIZE     (HTP_MATMUL_OUTPUT_AREA_KB * 1024)
#define SCRATCH_AREA_SIZE    (HTP_MATMUL_SCRATCH_AREA_KB * 1024)
```

## 步骤 1：加载量化权重到 VTCM

权重存储在 DDR 中，以 super block 为单位 DMA 到 VTCM：

```c
// DMA 1D 传输
dma_issue_load_from_ddr(&desc, vtcm_weight_area, ddr_weight_ptr, block_bytes);
```

权重不需要格式转换——super block 的 layout 直接就是 HVX 友好的连续存储。

## 步骤 2：HVX 解量化

HVX 把量化的权重解码为 FP16。以 Q4_0 为例：

```c
// Q4_0 解量化：每个 4-bit 值通过 LUT 查表得到 FP16
static const __fp16 q4_0_to_fp16_lut[64] = {
  -8, 0, -7, 0, -6, 0, -5, 0, -4, 0, -3, 0, -2, 0, -1, 0,
  0, 0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0,
};
```

解量化过程：
1. 从 super block 中取出 4-bit packed 值
2. 用 HVX 的 `vlut` 指令查表，得到 FP16 值
3. 乘以 block 的 scale 因子
4. 结果按 HMX tile layout 排列到 VTCM 的 activation 区域

IQ4_NL 使用不同的 LUT（16 个非均匀值），但流程相同。

## 步骤 3：Activation 转换

Host 侧的 activation 是 FP32（llama.cpp 的默认精度）。需要：
1. 加载到 VTCM
2. FP32 → FP16 转换（`hvx_my_wsf_to_vhf`）
3. 转为 HMX tile layout

```c
static void transfer_activation_chunk_fp32_to_fp16(__fp16 *vtcm_dst, const float *src, ...) {
    for (int r = 0; r < n_rows; r += 2) {
        // 每次处理 2 行
        HVX_Vector v_out = hvx_my_wsf_to_vhf(v1, v0);  // FP32 → FP16
        tile[r1 / 2] = v_out;  // 写入 HMX tile 位置
    }
}
```

## 步骤 4：HMX 矩阵乘法

解量化后的 FP16 权重和 FP16 activation 送入 HMX：

```c
hmx_dot_fp16(output_tile, activation_tiles, weight_tiles, k_tiles);
```

这和 [[../flashattention/04-kernel-deep-dive|FlashAttention]] 中的 QK dot 使用完全相同的 HMX 操作。区别只在于数据来源——FlashAttention 的 K 来自 KV cache，这里来自解量化后的权重。

## 4-Stage Pipeline

当 M（batch size）足够大时（`m >= 128` 且 `k <= n`），使用 4-stage 流水线：

```
Stage 1: DMA 加载下一个权重 block
Stage 2: HVX 解量化当前权重 block
Stage 3: HMX 计算当前 block 的矩阵乘法
Stage 4: 存储上一个 block 的结果
```

这 4 个 stage 可以重叠执行，隐藏 DMA 延迟。

```c
static inline bool qk_matmul_use_pipeline(int m, int k, int n) {
    return (m >= 128) && (k <= n);  // M 足够大时才用 pipeline
}
```

对于 decode 阶段（M=1），pipeline 没有意义，直接串行执行。

> [!next] 下一步
> 想知道怎么把 HuggingFace 模型转成量化 GGUF？看 [[03-gguf-conversion]]
