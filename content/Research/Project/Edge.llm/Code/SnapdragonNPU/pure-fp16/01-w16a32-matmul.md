# 1. W16A32 矩阵乘法 Kernel

## 什么是 W16A32？

- **W16**：Weight 是 FP16（16-bit 浮点）
- **A32**：Activation 在 host 侧是 FP32（32-bit 浮点），送入 DSP 后转为 FP16

这是最简单的路径——没有量化、没有解量化，权重直接以 FP16 形式加载到 VTCM。

## 与 W4/W8 的区别

| | W4/W8 A16 | Pure FP16 |
|---|-----------|-----------|
| 权重格式 | Q4_0 / Q8_0 / IQ4_NL | FP16 |
| 权重加载 | DMA → HVX dequant → VTCM | DMA → VTCM（直接用） |
| 精度 | 权重 4/8 bit，计算 FP16 | 全程 FP16 |
| 内存占用 | 小（压缩 2-4×） | 大（原始大小） |
| 计算路径 | dequant + HMX MMA | 只有 HMX MMA |

## mat_mul.c 中的关键流程

核心文件：`src/htp-ops-lib-main/src/dsp/ops/mat_mul.c`（1.6 MB，仓库最大的单文件）

```
1. DMA 加载 FP16 权重到 VTCM weight 区域
   → 不需要解量化，直接是 HMX tile layout

2. FP32 activation → FP16 转换
   transfer_activation_chunk_fp32_to_fp16()
   → HVX 指令 hvx_my_wsf_to_vhf()

3. HMX FP16 矩阵乘法
   hmx_dot_fp16(output, activation, weight, k_tiles)

4. 结果存回（可能需要 FP16 → FP32 转换）
```

## VTCM 分区

和 [[../w4-w8-a16/02-dequant-pipeline|W4/W8]] 相同的 4 区域结构，但 weight 区域直接存 FP16 数据（不需要 dequant 中间空间）：

| 区域 | 默认大小 | 用途 |
|------|---------|------|
| Weight | 1024 KB | FP16 权重 tile |
| Activation | 2048 KB | FP16 activation tile |
| Output | 1536 KB | 矩阵乘法结果 |
| Scratch | 1024 KB | DMA scratch buffer |

纯 FP16 路径还支持 **small-M VTCM 模式**——当 M（batch size）较小时，重新分配 VTCM 各区域的大小以获得更好的 tile 利用率：

```c
#ifndef HTP_FP16_SMALL_M_VTCM_ENABLE
#define HTP_FP16_SMALL_M_VTCM_ENABLE 0
#endif
#ifndef HTP_FP16_SMALL_M_THRESHOLD
#define HTP_FP16_SMALL_M_THRESHOLD 192  // M < 192 时启用
#endif
```

## DMA Weight Load 模式

构建脚本支持 3 种权重加载方式（通过 `-Fp16WeightLoadMode` 参数）：

| 模式 | 说明 |
|------|------|
| `hvx` | 用 HVX 指令直接从 DDR 加载 |
| `dma_direct` | DMA 直接从 DDR 到 VTCM |
| `dma_scratch_hvx` | DMA 到 scratch → HVX 复制到 weight 区域（默认） |

`dma_scratch_hvx` 是默认模式，因为它在 DMA 和 HVX 之间实现了更好的流水线重叠。

> [!next] 下一步
> 这个项目的精华在于后续的优化迭代：[[02-optimizations]]
