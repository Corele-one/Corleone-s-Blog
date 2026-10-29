---
created: 2026-07-28
tags: [tutorial, snapdragon-npu, llm-inference, edge-ai]
source: "zcy-001-001/Snapdragon-NPU, haozixu/llama.cpp-npu, haozixu/htp-ops-lib"
---

# Snapdragon NPU 推理系统 — Tutorial Roadmap

> 本教程帮助你从零理解 Qualcomm Snapdragon NPU 上的 LLM 推理实现。


## 项目概览

这个项目实现了一个 **end-to-end 的 LLM 推理系统**，把模型从 llama.cpp 一路执行到 Snapdragon 手机的 Hexagon DSP 上。

核心思想：**用 NPU（HMX + HVX）加速 Attention 和矩阵乘法**，同时用 weight-only 量化节省内存带宽。

### 四层架构

```
第 1 层：LLM 模型与 GGML 计算图
        llama.cpp

第 2 层：GGML HTP Backend
        判断算子能否下放 NPU → 打包参数 → FastRPC

第 3 层：DSP Runtime
        接收请求 → rpcmem 映射 → operator dispatch

第 4 层：NPU Kernel
        HMX：QK^T、PV（矩阵乘法）
        HVX：softmax、数据处理（向量运算）
```

### 关键仓库

| 仓库 | 作用 |
|------|------|
| [llama.cpp-npu](https://github.com/haozixu/llama.cpp-npu) | llama.cpp + HTP backend |
| [htp-ops-lib](https://github.com/haozixu/htp-ops-lib) | DSP kernel 库（HMX/HVX） |
| [Corele-one/Snapdragon-NPU](https://github.com/Corele-one/Snapdragon-NPU) | 开发 fork |

---

## 三个子项目

本教程覆盖三个子项目，每个子项目聚焦一个核心问题：

### 1. FlashAttention — Attention Kernel 优化

**核心问题**：如何在 Snapdragon DSP 上高效执行 FlashAttention？

| 章节                                                               | 内容                                                     | 关键词    |
| ---------------------------------------------------------------- | ------------------------------------------------------ | ------ |
| [[01-environment-and-architecture\|1. 环境与架构]]     | Win/WSL2/Android/DSP 四层环境，FastRPC 通信                   | 开发环境   |
| [[02-inference-pipeline\|2. 推理 Pipeline]]         | 从 llama.cpp graph 到 DSP kernel 的完整调用链                  | 数据流    |
| [[03-flash-attn-algorithm\|3. FlashAttention 算法]] | Online softmax、tiling 策略、VTCM 内存布局                     | 算法     |
| [[04-kernel-deep-dive\|4. Kernel 深度拆解]]           | `flash_attn.c` 逐段拆解：QK dot → softmax → PV acc → output | **核心** |
| [[05-hardware-accelerators\|5. 硬件加速器]]            | HMX（矩阵）、HVX（向量）、VTCM（片上存储）                             | 硬件     |
| [[06-profiling-and-tools\|6. Profiling 工具]]       | Figure 8 timer、baseline vs lut-exp 对比、Perfetto trace   | 性能分析   |
| [[07-building-and-running\|7. 构建与运行]]             | 构建、部署、benchmark、正确性验证                                  | 动手实践   |

> **推荐阅读路径**：[[01-environment-and-architecture|环境]] → [[02-inference-pipeline|Pipeline]] → [[04-kernel-deep-dive|Kernel]] → [[07-building-and-running|Build]]

### 2. W4/W8 A16 — 权重量化实现

**核心问题**：如何用 INT4/INT8 量化权重来节省内存和带宽？

| 章节 | 内容 | 关键词 |
|------|------|--------|
| [[01-quantization-formats|1. 量化格式]] | Q4_0、Q8_0、IQ4_NL 的 block 结构和 LUT | 数据格式 |
| [[02-dequant-pipeline|2. 解量化 Pipeline]] | HVX dequant → HMX FP16 MMA 的 4-stage pipeline | 计算流 |
| [[03-gguf-conversion\|3. GGUF 转换]] | HuggingFace → FP16-HMX → 量化 GGUF 的两步转换 | 模型准备 |
| [[04-building-and-running\|4. 构建与运行]] | 构建、量化、部署、运行 | 动手实践 |

> **推荐阅读路径**：[[01-quantization-formats|格式]] → [[02-dequant-pipeline|Pipeline]] → [[04-building-and-running|Build]]

### 3. Pure FP16 — 全 FP16 推理及优化

**核心问题**：不量化权重时，如何通过 DMA/VTCM/pipeline 优化提升性能？

| 章节 | 内容 | 关键词 |
|------|------|--------|
| [[01-w16a32-matmul|1. W16A32 MatMul]] | FP16 权重直接加载，HMX FP16 MMA | 基线 |
| [[02-optimizations|2. 优化实验]] | 7 个渐进式优化：DMA pipeline、parallel publish、split-K 等 | 优化 |
| [[03-scripts-and-deployment\|3. 脚本与部署]] | PowerShell 自动化：构建、部署、smoke/trace/PD sweep | 工具链 |
| [[04-lpbq-experiments\|4. LPBQ 实验]] | 实验性 W4A8 路径：LPBQ INT8 + R4 修正 | 实验 |

> **推荐阅读路径**：[[01-w16a32-matmul|MatMul]] → [[02-optimizations|优化]] → [[04-lpbq-experiments|LPBQ]]

---

## 关键概念速查

### 硬件

| 缩写 | 全称 | 作用 |
|------|------|------|
| HMX | Hexagon Matrix eXtension | 32x32 FP16 矩阵乘法（类似 Tensor Core） |
| HVX | Hexagon Vector eXtension | 128B SIMD 向量运算（exp、softmax、数据转换） |
| VTCM | Vector Tightly Coupled Memory | 4-6 MB 片上快速存储（类似 GPU shared memory） |
| DMA | Direct Memory Access | DDR ↔ VTCM 数据搬运 |
| DSP | Digital Signal Processor | Hexagon 处理器 |

### 量化

| 格式 | 精度 | 特点 |
|------|------|------|
| Q4_0 | 4-bit 线性 | 32 参数一组，共享 FP16 scale |
| Q8_0 | 8-bit 线性 | 用于 attention 层（精度敏感） |
| IQ4_NL | 4-bit 非线性 | 16 个非均匀 LUT 值，精度优于 Q4_0 |
| LPBQ | W4A8 | 实验性，INT4 权重 + INT8 激活 + INT8 HMX MMA |

### 关键文件

| 文件 | 大小 | 作用 |
|------|------|------|
| `flash_attn.c` | ~800 行 | FlashAttention 主 kernel |
| `mat_mul.c` | 1.6 MB | 矩阵乘法 kernel（含所有优化实验） |
| `op_executor.cc` | ~200 行 | DSP 端 operator 调度 |
| `htp-ops.cc` | ~500 行 | Host 端 GGML → HTP 桥接 |
| `op_reg.h` | ~300 行 | 操作码枚举、参数结构体定义 |

---

## 与其他笔记的关系

- [[../../SCOPE|SCOPE 论文笔记]] — SCNA（Shape-Constrained Neural Approximation）的理论基础
- [[../../Flash Attention|Flash Attention 论文笔记]] — FlashAttention 算法的原始论文
- [[NPU_Arch-ProgrammerManual_ToolChain_MoreDetailed|NPU 架构笔记]] — Qualcomm NPU 的硬件架构详解
- [[../../从HeteroInfer看异构SOC在llm推理上的加速|HeteroInfer 笔记]] — 异构 SOC 加速的另一个视角
- [[../../SystolicAttention|SystolicAttention 笔记]] — 脉动阵列上的 Attention 实现
- [[../../Code/Git开发流程_备忘|Git 开发流程]] — 项目的 Git 工作流 SOP
