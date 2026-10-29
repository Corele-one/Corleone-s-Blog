npu做推理系统有大致四个方向问题：
# 静态图
因为NPU原本是用来加速CNN计算的，但是当我们在用NPU来加速llm推理的，CNN输入的是图像，对图像而言输入的token可以是固定的，所以NPU在加速CNN运算的时候就可以转化成静态图，然后用静态图来加速该部分的计算。但是到了llm推理的时候就会出现问题，因为llm推理过程中输入的token的大小是不一致的，这就是静态图的问题。

# 量化受限

## 问题本质
NPU的脉动阵列原生支持INT8运算，但LLM推理中存在多种量化方案（W4A4、W4A8等），核心矛盾在于：
- **量化/解量化开销大**：数据在低精度和高精度格式之间反复转换，引入额外延迟，抵消了低精度计算带来的加速收益(**GEMM可以以INT8的格式来计算，但是非线性操作为了保证精度需要解量化为高精度格式再进行计算 ，quant和dequant以及Array与SFU之间的数据搬运都是问题**)
- **NPU硬件格式固定**：NPU只高效支持特定量化格式（如纯INT8），但LLM不同层对量化敏感度不同，需要混合精度策略
- **现有框架不灵活**：QNN等官方框架的量化策略是固定的，无法灵活适配混合精度需求

## 解决方案分类

现有工作从四个不同角度来应对NPU量化格式受限的问题：

### 类别一：离线激活重分布（Offline Activation Redistribution）

**核心思路**：通过离线方式重新分布激活值，防止激活离群值主导逐张量（per-tensor）的激活缩放因子。

常见技术路线包括：
- **激活平滑（Activation Smoothing）**：对激活分布进行平滑处理，缩小离群值与正常值的差距
- **权重等价变换（Weight Equivalent Transformation）**：在不改变模型数学等价性的前提下，对权重进行变换以均衡激活分布
- **激活范围学习（Activation Range Learning）**：通过训练学习更优的激活量化范围
- **静态校准（Static Calibration）**：使用离线校准数据确定固定的量化参数

### 类别二：离群值分离（Outlier Separation）

**核心思路**：NPU负责计算大部分正常值，离群值通过高精度旁路（bypass）单独处理。

典型案例为 **LLM.npu 的 Shadow Outlier Execution**：
- NPU 继续执行高效的逐张量 INT8 矩阵乘法
- 将激活中的离群通道提取为一个小张量，在 CPU/GPU 上以高精度计算
- 将高精度计算结果加回 NPU 的输出
- 论文报告离群通道通常高度稀疏，仅占全部通道的 **0.1%～0.3%**

### 类别三：多静态图近似动态缩放（Multiple Static Graphs Approximating Dynamic Scaling）

**核心思路**：用多个静态缩放图（static-scale graph）来近似动态激活缩放。

典型方案为 **ShadowNPU**：
- 根据缩放因子（scale factor）和形状（shape）将多个计算图组织为不同的"桶"（bucket）
- 在线推理时，先选择缩放因子最接近的桶，再从中选取形状匹配的计算图
- 本质上是用有限个静态图的集合来覆盖动态范围

### 类别四：权重格式转换（Weight Format Conversion On-chip）

**核心思路**：模型权重仍然以更精确的格式存储（如 GPTQ、AWQ 或低位宽分块量化），但在执行前在片上（on-chip）转换为 NPU 支持的格式。

- 权重存储阶段保留高精度量化方案的精度优势
- 执行阶段实时转换为 NPU 原生支持的格式（如 INT8）
- 在存储精度与计算效率之间取得平衡

# Attention内核不高效

## 问题本质

NPU架构对Attention Kernel天然不友好，有两个核心原因：
1. **Attention涉及大量非GEMM操作**（softmax、masking、缩放等），而NPU的向量/标量单元对非线性计算支持较弱
2. **量化粒度受限**：NPU原生仅支持 per-tensor activation quantization 和 per-channel weight quantization，粒度过粗，难以保证Attention计算精度

### FlashAttention在Hexagon NPU上的延迟分解

以Qwen2.5-1.5B、prompt length=4096为例，FlashAttention各阶段的延迟占比如下：

| Batch Size (qo_len) | QKVO Load/Store | MatMul (QK, DO+PV) | Softmax |
|---------------------|-----------------|---------------------|---------|
| q=4 | 58.3% | — | **39.2%** |
| q=8 | 37.5% | — | **58.6%** |
| q=16 | 25.2% | — | **71.3%** |
| q=32 | **84.6%** | 11.3% | — |

**关键观察**：
- 在较小batch size下，**Softmax是非线性算子瓶颈的典型代表**，占比极高（q=8时达58.6%）
- 随着batch size增大，Softmax占比下降，**QKVO Load/Store（访存）成为主要瓶颈**（q=32时达84.6%）

### Hexagon NPU硬件单元性能对比

| 硬件单元 | HVX (1 Thread) | HMX |
|----------|----------------|-----|
| FP16 GEMM GFLOPs | 32.93 | **12032.54** |
| Memory Read BW (GB/s) | 26 | **60 (DMA)** |

HMX的GEMM算力远超HVX（约365倍），但非线性操作（如softmax）无法使用HMX，只能回落到HVX处理，造成严重的计算不匹配。

## 现有解决方案

### 类别一：Attention卸载至CPU/GPU（LLM.npu / MLC-LLM / HeteroLLM）

**核心思路**：将Attention、LayerNorm和Shadow Outlier计算放在CPU/GPU上执行，仅将线性层（Linear）卸载到NPU。

- NPU擅长的GEMM部分（Linear层）交给NPU加速
- Attention中的softmax、masking等非线性操作由CPU/GPU处理
- **Limitation**：CPU/GPU与NPU之间存在频繁的通信和调度开销，且无法利用NPU的算力加速Attention

### 类别二：稀疏注意力 + 异构调度

#### PowerInfer-2

**核心思路**：Prefill阶段由NPU处理Attention；Decode阶段将注意力头在CPU和NPU之间分区并行执行。

#### ShadowNPU (2026'4)

**核心思路**：NPU仅执行重要token的估计（important-token estimation），稀疏Attention实际计算仍在CPU/GPU上完成。

稀疏Attention的工作流程：
1. **Estimation Stage**：Q, K量化后，在NPU上用INT8 dense QK矩阵乘法仅用于估计top-k重要位置
2. **Attention Stage**：CPU/GPU执行top-k选择、mask、RoPE、sparse fragmented QKV，得到sparse attention输出

**关键insight**：估计top-k只需要attention score的**相对顺序**，不需要精确数值。softmax是单调递增的，所以可以直接用softmax前的QK做top-k；mask也不在NPU上做，而是在CPU/GPU top-k时跳过masked positions。

### 类别三：LUT优化Softmax（NPU-kernel视角）

**核心思路**：通过test-time scaling，用查找表（LUT）替代softmax中的dequantization和其他复杂运算。

- 使用16 KB的大查找表存储exp函数的值
- **Limitation**：使用`vgather`从TCM读取查找表会引入过高的延迟

## 总结：现有方案的共同局限

| 局限 | 说明 |
|------|------|
| CPU/GPU通信开销 | 类别一、二均需要CPU/GPU参与，调度和数据搬运开销大 |
| NPU上延迟/资源开销过高 | 类别三虽在NPU上执行，但LUT方案仍存在延迟问题 |
| 无法支持纯INT Attention数据flow | 以上方案均未能实现端到端的纯INT量化Attention计算 |

## 非线性算子瓶颈（Softmax / GeLU / SwiGLU / LayerNorm / RMSNorm）

**核心矛盾**：GEMM-centric加速器中，线性计算（GEMM）通过脉动阵列高效执行INT8低精度运算，而非线性算子仍依赖独立的标量/向量/特殊功能单元（SFU）处理，量化越深、GEMM越快，非线性算子占比越大，成为系统级瓶颈。

### 现有方案及其Limitation

| 方案 | 核心思路 | Limitation |
|------|----------|------------|
| **SFU（特殊功能单元）** | 硬件直接实现exp、log等非线性函数 | 面积和功耗开销大；不随脉动阵列扩展，无法跟上GEMM加速节奏 |
| **查表法（LUT）** | 预计算函数值存入查找表，查表替代计算 | 高精度需要大容量表格，存储开销增长快；可扩展性差 |
| **分段线性近似（PWL）** | 将非线性函数分段用线性函数逼近 | 高精度需要更细的分段，控制逻辑复杂度上升；函数特异性强，通用性差 |
| **学习型替代函数（Learned Surrogate）** | 用可学习的简单函数拟合目标非线性函数 | 训练开销；泛化性与精度难以兼顾 |
| **可编程非线性引擎** | 设计专用可编程单元覆盖多种非线性算子 | 将非线性计算视为**独立执行域**，有独立的映射和控制开销；与主计算阵列耦合度低 |
| **阵列融合设计（Array-fused）** | 将非线性处理移近主计算阵列 | 多数方案仍然 specialized（适用范围窄）；仍依赖大量辅助结构（LUT、缓冲、路由、混合精度处理），并未真正消除开销 |

### 总结：关键Gap
现有方案无法同时满足三个目标：
1. **广泛的算子支持**（覆盖Softmax、GeLU、SwiGLU、LayerNorm等）
2. **高精度逼近**（不显著损失模型质量）
3. **硬件高效、可扩展执行**（能跟上脉动阵列的加速节奏，不引入过大面积/功耗开销）
## 量化scale的匹配问题

GEMM可以以INT8的格式来计算，但是非线性操作为了保证精度需要解量化为高精度格式再进行计算 ，quant和dequant以及Array与SFU之间的数据搬运都是问题

# Decoding利用率太低
npu的脉动阵列在decoding batch较小的情况下，算力运用率很低
可以使用投机解码，insearch，best of N

投机解码的问题:
不同输入的长度不一样
FLash Attention可以解决静态图的问题,把投机解码和flash attention结合起来

投机解码不同输入有不同分支和不同长度，在这个情况下KV-Cache的管理是个问题

Paged Attention 内存管理

# 工具链

## 1.基于QNN的Kernel设计

高通的很多文档是闭源的，QNN虽然是高通公司已经封装好的一个框架(用于模型转换)，转换后的模型可以直接放到NPU上运行， 但是QNN不是一个可以灵活调整的框架，所以不采用这种方案

## 2.使用CPU+NPU的方式

使用llama.cpp

因为在CPU上我们可以灵活的编程，就可以涉及一些pipeline/调度算法把一些NPU友好的算法调度到NPU上来进行计算，这样更加灵活也方便落实我们的idea

## 3.AI编译器
重新设计一套QNN，能够把算法编译到NPU上进行计算，但是这是一个极为hard的工作，需要一整个团队来做。