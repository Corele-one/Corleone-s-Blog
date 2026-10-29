# Pure FP16 — 全 FP16 推理实现 Tutorial

> 本教程帮助你理解 `projects/pure-fp16/` 中的纯 FP16 推理实现和后续优化。
> 前置阅读：先看 [[../00-roadmap|Tutorial Roadmap]] 获取全景图，再看 [[../flashattention/01-environment-and-architecture]] 了解运行环境和通信架构。

## 核心概念

这个项目走的是**全 FP16**路径：权重和激活值都是 FP16，HMX 做 FP16 矩阵乘法。没有 INT4/INT8 权重量化。

数据流：

```
GGML F16 tensor
  → GGML HTP backend
  → FastRPC W16A32 request
  → FP32 activation 转 FP16 并进入 VTCM
  → HMX-layout FP16 weight
  → HMX FP16 MMA
  → FP16 output 转回 FP32 caller ABI
```

与 [[../w4-w8-a16/00-index|W4/W8 A16]] 的区别：没有 dequant 步骤——权重本身就是 FP16，直接加载到 VTCM 就能用。

## 章节目录

| # | 章节 | 内容 |
|---|------|------|
| 1 | [[01-w16a32-matmul]] | W16A32 矩阵乘法 kernel：DMA/VTCM pipeline、weight layout |
| 2 | [[02-optimizations]] | 后续优化：parallel publish、output store、activation cache、split-K |
| 3 | [[03-scripts-and-deployment]] | PowerShell 自动化脚本、server 部署、smoke/trace/PD sweep |
| 4 | [[04-lpbq-experiments]] | LPBQ INT8 实验路径（实验性） |

## 与其他项目的关系

- 与 [[../flashattention/00-index|FlashAttention]] 共享 HTP 框架和硬件知识
- 与 [[../w4-w8-a16/00-index|W4/W8 A16]] 对比：本项目不压缩权重，精度更高但内存占用更大
- 本项目的 `mat_mul.c` 是仓库中最大的（1.6 MB），包含了大量优化实验代码
