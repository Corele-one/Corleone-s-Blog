# FlashAttention on Snapdragon HTP — Tutorial

> 本教程面向已读过 LLM 推理论文、熟悉 C 语言和基础 Python 的开发者。
> 目标：帮你从零理解 `projects/flashattention/` 下每一部分代码在做什么，以及 Attention Kernel 在 NPU 上是怎么优化的。

> [!tip] 从这里开始
> 如果你是第一次接触这个项目，建议先看 [[../00-roadmap|Tutorial Roadmap]] 获取全景图，再按本教程深入。

## 章节目录

| # | 章节 | 内容 |
|---|------|------|
| 1 | [[01-environment-and-architecture]] | 运行环境、整体架构、Win/WSL/adb 通信链路 |
| 2 | [[02-inference-pipeline]] | 一次 LLM 推理是怎么跑起来的：从 llama.cpp graph 到 DSP kernel |
| 3 | [[03-flash-attn-algorithm]] | FlashAttention 算法原理回顾，以及本项目的 tiling 策略 |
| 4 | [[04-kernel-deep-dive]] | `flash_attn.c` 逐段拆解：QK dot、softmax、PV accumulation、output scaling |
| 5 | [[05-hardware-accelerators]] | HMX、HVX、VTCM 是什么，它们在 kernel 里各自负责什么 |
| 6 | [[06-profiling-and-tools]] | Figure 8 timer、baseline vs lut-exp 对比、Perfetto trace 生成 |
| 7 | [[07-building-and-running]] | 构建、部署、运行 benchmark 和正确性验证的完整命令 |

## 阅读建议

- 如果你只想知道 **推理是怎么跑的**，读 [[01-environment-and-architecture]] → [[02-inference-pipeline]]
- 如果你关心 **Attention Kernel 的优化细节**，读 [[03-flash-attn-algorithm]] → [[04-kernel-deep-dive]] → [[05-hardware-accelerators]]
- 如果你想 **自己跑一遍实验**，读 [[07-building-and-running]] → [[06-profiling-and-tools]]

## 相关项目

- [[../w4-w8-a16/00-index|W4/W8 A16]] — 权重量化实现（Q4_0/Q8_0/IQ4_NL dequant → HMX FP16 MMA）
- [[../pure-fp16/00-index|Pure FP16]] — 全 FP16 推理及后续 DMA/VTCM/split-K 优化
