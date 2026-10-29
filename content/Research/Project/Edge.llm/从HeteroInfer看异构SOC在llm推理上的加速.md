# HeteroInfer采用的异构方案

CPU 被用作控制平面，负责同步和 GPU 内核调度，因为其能效较低，并不适合处理计算任务。NPU 作为主要计算单元，承担大部分计算任务，而 GPU 则作为次要计算单元，用于提升 NPU 性能的下限。

## Workflow

To leverage both the GPU and NPU, we developed optimized GPU kernels using OpenCL and integrated the NPU operators provided by Qualcomm’s QNN into our framework.

**Emphasis**:最小化端到端延迟

## CPU：控制平面

CPU 不承担主要 LLM 计算，而负责：
- GPU kernel 调度；
- GPU/NPU 同步；
- 状态轮询；
- runtime 控制。
原因是 CPU：
- 算力和能效低；
- 还要服务手机上的其他应用；
- 不适合作为主要 LLM 计算后端。
## NPU：Prefill 中的主计算单元

主要负责：
- QKV Linear；
- Output Linear；
- FFN Linear；
- 适合其 shape 的大型 Matmul。
## GPU：灵活的辅助计算单元

负责：
- RMSNorm；
- RoPE；
- Softmax；
- SwiGLU；
- 动态 shape 部分；
- 不适合 NPU 的 Matmul 分块；
- Decode 中的大部分计算。
# Previous Work

![[file-20260722151029926.png]]

更激进的低精度/稀疏化/模型改造⇒更容易利用 NPU⇒性能提高⇒更可能损失精度

- llama.cpp 是通用推理 runtime，llama.cpp 的核心价值不是提出某一种复杂的 NPU 调度方案，而是建立了一个高度可移植的本地 LLM runtime；
- ONNX Runtime 是通用图执行框架，统一ONNX计算图+不同Execution Provider
- Qualcomm-AI 更接近厂商 NPU 部署方案；
- llm.npu、PowerInfer2、HeteroInfer 是针对移动端 LLM 的系统研究
- MLC：通过编译自动生成跨平台 GPU kernel，LLM graph→tensor compiler→target-specific GPU kernels,通过编译器和自动 kernel 优化，把模型映射到不同硬件后端
- llm.npu：混合精度、outlier保留和 CPU–NPU 协同
- PowerInfer2：利用稀疏激活减少端侧模型权重访问


## Contribution of HeteroInfer
### ① 对移动 GPU、NPU 和内存进行 characterization

作者发现 NPU 性能不是简单由 FLOPS 决定，而具有：

- stage-sensitive；
- order-sensitive；
- shape-sensitive。

也就是 NPU 性能强烈依赖矩阵的尺寸、排列顺序和 shape。

### ② Layer-level 异构分配

Prefill 中：

- Matmul 更适合 NPU；
- RMSNorm、SwiGLU 等更适合 GPU。

Decoding 中：

- GEMV 的维度太小；
- NPU 阵列利用率差；
- GPU 反而成为主要计算单元。

论文明确指出，prefill 的 Matmul 分配给 NPU，而 RMSNorm 和 SwiGLU 更适合 GPU；decoding 阶段则因 NPU 的阶梯式性能特征，以 GPU 为主。

### ③ Tensor-level GPU–NPU partition(解决静态图问题)

同一个矩阵乘法不一定全部交给一个设备，而是将 tensor 切开：

![[file-20260722153725524.png]]

它提出：

- weight-centric partition；
- activation-centric partition；
- hybrid partition。

动态输入中，例如 sequence length 为 300：

300=256+44

- 256 使用预生成静态 NPU graph；
- 44 交给支持动态 shape 的 GPU；
- 两边并行。

### ④ Fast synchronization

由于标准 GPU–NPU 同步可能达到约 400 μs400\,\mu s400μs，已经接近一个 decode kernel 的执行时间，直接异构并行可能得不偿失。

HeteroInfer 利用：

- unified memory；
- 共享 memory pool；
- 预测 kernel 等待时间；
- sleep + 短时间 polling；
- flag-based completion notification。

从而降低 GPU–NPU 同步成本。

整体上，HeteroInfer 的贡献是充分利用 GPU、NPU 的计算能力及 SoC 内存带宽，并设计快速同步机制；论文报告端到端比 GPU-only 和 NPU-only 框架提升约 1.34× 到 6.02×

# 性能特征

NPU 的峰值算力虽然很高，但实际性能强烈依赖矩阵如何切块、哪个矩阵作为权重、以及矩阵各维度的形状。这三点都与 NPU 内部的**固定尺寸脉动阵列和 weight-stationary 数据流**有关。

## NPU 的基本执行方式

以 $C = A \times B$，$A \in \mathbb{R}^{M \times N}$，$B \in \mathbb{R}^{N \times K}$ 为例。NPU 内部通常有固定大小的脉动阵列（如 Snapdragon 8 Gen 3 NPU 包含多个 $32 \times 32$ 的 systolic array）。

执行流程：
1. 将一块权重 $B$ 预加载进 PE 阵列；
2. 权重暂时保持不动（weight-stationary）；
3. 不断将输入 $A$ 流入阵列；
4. PE 执行乘加并累积结果；
5. 一块计算完成后，再加载下一块权重。
这种设计的优势是降低权重的重复读写，但也产生了下面三个性能特性。

## Characteristic 1：Stage Performance

### 现象

对于 GPU，随着输入规模增大，执行时间通常连续增加。但对于 NPU，执行时间像楼梯一样呈阶梯状跳变：

- 张量从 1 增加到 31，时间可能基本不变；
- 从 32 增加到 33，时间突然跳一大截；
- 33 到 64，又可能处在同一平台。

![[file-20260722172040241.png]]

### 原因：固定 tile 大小与 padding

NPU 按固定尺寸的 tile（如 $32 \times 32$）执行计算。当维度不是 32 的整数倍时，编译器需要内部 padding。例如：

- $K=31$：$\lceil 31/32 \rceil = 1$ 个 tile
- $K=32$：$\lceil 32/32 \rceil = 1$ 个 tile
- $K=33$：$\lceil 33/32 \rceil = 2$ 个 tile，可能被补齐为 $K_{\text{pad}}=64$

$K=32$ 与 $K=33$ 的计算规模只差约 3%，但硬件执行量可能相差接近一倍（有效利用率从 100% 降到约 51.6%）。

延迟近似为：

$$T(K) \propto \left\lceil \frac{K}{32} \right\rceil$$

而非连续的 $T(K) \propto K$。

### 对 LLM 的影响

- **Prefill**：sequence length $M$ 较大且规整，NPU 阵列利用率高；
- **Decode**：每次只有一个 token（$M=1$），输入矩阵只有一行，大量 PE 没有有效数据，利用率极差。

> 核心：**NPU 按 tile 为一个计算粒度**

## Characteristic 2：Order-sensitive Performance

### 现象

两种数学等价的矩阵乘法，FLOPs 完全相同，但 NPU 性能可能相差数倍。论文测量中差异可达约 $6\times$。

根据转置性质 $(AB)^T = B^T A^T$，以下两种形式数学等价：

- **形式 A**：$[M,N] \times [N,K]$
- **形式 B**：$[K,N] \times [N,M]$，最后对结果转置

两者运算量都是 $2MNK$，但 NPU 速度可能差很多。

### 原因：input 与 weight 走不同硬件通路

在 weight-stationary 数据流中，**一个矩阵被识别为 input/activation，另一个被识别为 weight**。权重需提前加载到 PE，输入则不断流过阵列。因此 $A \times B$ 和 $B^T \times A^T$ 虽然数学等价，但硬件上谁作为 weight 已经变化。

假设 $M=14336,\ N=4096,\ K=32$：

- **情况 A**：$[14336,4096] \times [4096,32]$，weight 大小为 $4096 \times 32$，相对较小
- **情况 B**：$[32,4096] \times [4096,14336]$，weight 大小为 $4096 \times 14336$，非常大

情况 B 中大权重无法一次放进片上阵列或 SRAM，需要不断从内存加载→计算→更换→再计算，weight-stationary 的复用优势被破坏。

### 直观类比

把 PE 阵列想象成工作台：

- **理想情况**：放一小组工具（小权重），大量零件不断流过（大输入），同一套工具重复使用很多次
- **不理想情况**：每处理很少几个零件就要换一大套工具，大部分时间花在搬工具而不是加工

### HeteroInfer 的利用

HeteroInfer 使用等价变换 $XW = (W^T X^T)^T$ 来改变哪个 tensor 被 NPU 当作 weight，从而优化权重在阵列中的复用方式。

> 核心记忆：**NPU 的矩阵乘法不是左右对称的，因为 input 和 weight 走的是不同硬件数据通路。**

## Characteristic 3：Shape-sensitive Performance

### 现象

即便矩阵顺序已经固定、总 FLOPs 也一样，不同的长宽比例仍然会导致性能不同。

例如保持 $MNK$ 相近：

- **形状 A**：$[1024,4096] \times [4096,32]$（高而窄）
- **形状 B**：$[32,4096] \times [4096,1024]$（矮而宽）

NPU 对这两种形状的利用率和权重流量可能明显不同。

### 原因：权重复用次数

考虑 $A_{M \times N} B_{N \times K}$，其中 $B$ 是固定权重。权重中的一个元素 $B_{n,k}$ 会被 $A$ 的 $M$ 行复用，因此：

$$\text{weight reuse} \propto M$$

$$\frac{\text{MAC 数量}}{\text{权重元素数}} = \frac{MNK}{NK} = M$$

==$M$ 越大，每个权重平均参与的 MAC 越多，权重加载成本被充分摊薄。==

论文指出当 input tensor 的行数大于列数（$M > N$）时 NPU 往往表现更好，因为较大的 column size $N$ 意味着更大的 weight tensor，削弱 weight-stationary 数据流的优势。

### 对 LLM 的影响

- **Prefill**：$M = \text{sequence length}$（如 512），权重可被 512 个 token 复用
- **Decode**：$M = 1$，每个权重只为一个 token 使用一次，几乎没有跨 token 复用，这也是 decode memory-bound 的根本原因之一

> 核心记忆：**看权重能够复用多少次。$M$ 越大，权重复用越充分；$M=1$ 的 decode 最不利。**

## 三个特性的统一理解

| 特性 | 核心问题 | 根本原因 |
|------|---------|---------|
| Stage performance | 需要多少个硬件 tile？ | 固定大小脉动阵列和 padding |
| Order-sensitive | 哪个矩阵作为 weight？ | input 和 weight 数据通路不对称 |
| Shape-sensitive | 权重能够被复用多少次？ | 矩阵长宽比例影响驻留和复用 |

NPU 延迟可近似理解为：

$$T_{\mathrm{NPU}} \approx T_{\mathrm{tile}} + T_{\mathrm{weight\ load}} + T_{\mathrm{padding}}$$

- **Stage performance** 主要影响 $T_{\mathrm{tile}}$ 和 $T_{\mathrm{padding}}$
- **Order-sensitive performance** 主要影响 $T_{\mathrm{weight\ load}}$（改变了谁是 weight）
- **Shape-sensitive performance** 同时影响 $T_{\mathrm{weight\ load}}$ 和 weight reuse

这三个特性说明：**NPU 不是一个只由 FLOPs 决定性能的黑盒矩阵乘法器，而是一个对 tile、数据布局和复用模式高度敏感的数据流加速器。** 因此不能简单地"NPU 算力最高→所有算子全部扔给 NPU"，而需要根据三个 characteristic 决定每个算子的分配策略。


# Design

## Layer-Level

较为粗粒度的设计，根据算子类型的不同把工作负载相应地分配到GPU以及NPU上

![[file-20260722210007539.png]]

## Tensor-Level

矩阵乘法:Y=XW

X是动态的，W是静态的
### Weight-Partition

首先考虑用户输入的固定序列长度，使 NPU 能够基于静态张量形状构建计算图。该策略沿权重张量的行维度(Row)进行划分，将子张量分配给 GPU 和 NPU 进行并发计算。划分比例由离线求解器静态确定。使得计算过程中负载均衡。让NPU的分块形状更规整同时也利用GPU的算力

![[file-20260722210831843.png]]

![[file-20260722202042546.png]]
### Activation-Partition

![[file-20260722202914424.png]]

NPU 只支持静态 graph，但用户输入 sequence length 是动态的。把input sequence拆成固定的可以输入到npu的形状(静态图)，remainder就给GPU来计算。有时 remainder 太大，GPU 执行时间会超过 NPU。利用NPU的多核性质，把sequence拆成更多的小的子块，产生最小的remainder在GPU上执行。
### Hybrid-Partition
Activation-centric 虽然解决动态 shape，但仍可能产生不理想的分工。所以 Hybrid 同时切：activation和weight.

Activation切分：解决动态sequence length
Weight切分：调整GPU/NPU负载比例和NPU shape

![[file-20260722211525212.png]]


## Fast Synchronization

![[file-20260722212109308.png]]

![[file-20260722212506316.png]]

## Put it Together


| **Offline**<br><br>部署前完成：<br><br>- 硬件 profiling；<br>- 模型 shape 分析；<br>- 求最优 partition；<br>- 生成 NPU 静态子图；<br>- 准备 GPU kernel。 | **Online**<br><br>用户真正推理时只需要：<br><br>1. 判断是 prefill 还是 decode；<br>2. 读取当前 sequence length；<br>3. 从预生成方案中选择；<br>4. 启动 GPU/NPU；<br>5. 快速同步；<br>6. 合并结果。 |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |

![[file-20260722212828392.png]]

| **Performance Profiler**<br><br>在目标手机上实际测量：<br>$T_{\mathrm{GPU}}(\text{op},\text{shape})T_{\mathrm{NPU}}(\text{op},\text{shape})$<br><br>以及：<br><br>- 内存带宽；<br>- 同步成本；<br>- 不同矩阵顺序；<br>- 不同分块形状。<br><br>它不是只看理论 TOPS，而是建立实际 performance matrix。 | **Solver 输入**：<br><br>- 模型结构；<br>- 每层权重 shape；<br>- GPU profiling 数据；<br>- NPU profiling 数据；<br>- 同步开销；<br>- 可用静态 graph shape。<br><br>然后枚举或求解不同方案：<br> |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |


