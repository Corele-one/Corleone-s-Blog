# W4/W8 A16 — Weight-Only 量化实现 Tutorial

> 本教程帮助你理解 `projects/w4-w8-a16/` 中的权重量化实现。
> 前置阅读：先看 [[../00-roadmap|Tutorial Roadmap]] 获取全景图，再看 [[../flashattention/01-environment-and-architecture]] 了解运行环境和通信架构。

## 核心概念

这个项目的准确描述是：

> **Weight-only W4/W8 with FP16 HMX activation/compute and FP32 host ABI.**

也就是说：
- **权重**被量化为 INT4（Q4_0、IQ4_NL）或 INT8（Q8_0）
- **激活值**保持 FP16 精度
- **HMX**做 FP16 矩阵乘法
- **HVX**负责把量化权重实时解码（dequant）为 FP16

这不是"整个模型都用低精度"的方案，而是**只压缩权重来节省内存和带宽**，计算精度仍然用 FP16。

## 章节目录

| # | 章节 | 内容 |
|---|------|------|
| 1 | [[01-quantization-formats]] | Q4_0、Q8_0、IQ4_NL 的数据格式和 block 结构 |
| 2 | [[02-dequant-pipeline]] | HVX 解量化 → HMX FP16 矩阵乘法的完整 pipeline |
| 3 | [[03-gguf-conversion]] | 从 HuggingFace 模型到 HMX-layout GGUF 的转换流程 |
| 4 | [[04-building-and-running]] | 构建、量化、部署和运行 |

## 与 FlashAttention 的关系

本项目和 [[../flashattention/00-index|FlashAttention 项目]] 共享相同的底层架构：
- 同样的 HTP operator 框架（`htp-ops-lib-main`）
- 同样的 FastRPC 通信机制（详见 [[../flashattention/02-inference-pipeline]]）
- 同样的 HMX/HVX 硬件（详见 [[../flashattention/05-hardware-accelerators]]）

区别在于：FlashAttention 的核心是 Attention kernel（`flash_attn.c`），而本项目的核心是**矩阵乘法 kernel**（`mat_mul.c`）中的权重解量化逻辑。
