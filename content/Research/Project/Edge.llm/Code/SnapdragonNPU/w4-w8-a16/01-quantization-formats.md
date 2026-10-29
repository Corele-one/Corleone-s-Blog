# 1. 量化格式：Q4_0、Q8_0、IQ4_NL

## 什么是权重量化？

LLM 的权重通常是 FP16（每参数 2 字节）。量化把权重量化为更低位宽的整数：
- **Q4_0**：每参数 4 bit（0.5 字节），压缩比 4×
- **IQ4_NL**：每参数 4 bit，使用非线性量化表，精度略好于 Q4_0
- **Q8_0**：每参数 8 bit（1 字节），压缩比 2×

典型做法是用 `IQ4_NL+Q8_0` 混合量化：大部分层用 IQ4_NL，attention 层用 Q8_0（因为 attention 对精度更敏感）。

## Block 结构

量化不是逐参数独立的，而是按 **block** 分组，每个 block 共享一个缩放因子。

定义在 `include/dsp/quants.h`：

### Q4_0 Block（32 个参数为一组）

```c
typedef struct {
  __fp16  scale;               // 缩放因子（FP16）
  uint8_t quants[QK4_0 / 2];  // 32 个 4-bit 参数，packed 成 16 字节
} __attribute__((packed)) block_q4_0;  // 总共 18 字节
```

32 个 FP16 参数（64 字节）→ 18 字节，压缩比约 3.5×。

### Q8_0 Block

```c
typedef struct {
  __fp16  scale;               // 缩放因子
  uint8_t quants[QK8_0];      // 32 个 8-bit 参数（有符号）
} __attribute__((packed)) block_q8_0;  // 总共 34 字节
```

### IQ4_NL Block

和 Q4_0 类似大小，但 4-bit 值不是线性的 0-15，而是通过一个**非线性查找表**映射：

```c
// mat_mul.c 中的 IQ4_NL 查找表
static const __fp16 iq4_nl_to_fp16_lut[64] = {
  -127, 0, -104, 0, -83, 0, -65, 0,
  -49, 0, -35, 0, -22, 0, -10, 0,
  1, 0, 13, 0, 25, 0, 38, 0,
  53, 0, 69, 0, 89, 0, 113, 0,
};
```

16 个非均匀分布的值，比线性量化能更好地覆盖权重分布。

### Super Block（HVX 批量处理单位）

HVX 处理时不是逐 block 解码，而是按 **super block** 批量处理。一个 super block 包含 8 个连续的 block：

```c
typedef struct {
  __fp16  scales[8];           // 8 个 block 的缩放因子
  uint8_t quants[8 * 32 / 2]; // 8 × 16 = 128 字节的 4-bit 量化值
} __attribute__((packed)) my_block_q4_0;  // 144 字节
```

这种 layout 便于 HVX 一次性加载并解码。

## 精度分派

在 `ggml-htp/htp-ops.cc` 中，根据 GGML tensor 类型选择 DSP kernel：

```c
if (weight->type == GGML_TYPE_F16) {
    op_index = HTP_OPS_MAT_MUL_PERMUTED_W16A32;      // pure FP16
} else if (weight->type == GGML_TYPE_Q4_0) {
    op_index = HTP_OPS_MAT_MUL_PERMUTED_W4D16A32;    // W4 dequant + FP16 MMA
} else if (weight->type == GGML_TYPE_Q8_0) {
    op_index = HTP_OPS_MAT_MUL_PERMUTED_W8D16A32;    // W8 dequant + FP16 MMA
} else if (weight->type == GGML_TYPE_IQ4_NL) {
    op_index = HTP_OPS_MAT_MUL_PERMUTED_W4D16A32_IQ4_NL;  // IQ4_NL dequant
}
```

> [!note] A16 的含义
> "A16" 表示 activation 是 FP16。权重被解码为 FP16 后，和 FP16 的 activation 一起送入 HMX 做矩阵乘法。整个过程中 activation 始终是 FP16 精度。

> [!next] 下一步
> 了解了数据格式后，来看 HVX 解量化 + HMX 计算的完整 pipeline：[[02-dequant-pipeline]]
