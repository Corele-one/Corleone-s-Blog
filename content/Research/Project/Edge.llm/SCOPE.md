---
source: "SCOPE: Array-Native Nonlinear Acceleration for LLM Inference via Shape-Constrained Neural Approximation"
---
# Impression
**SCOPE**
**S**oftware-hardware **CO**-design **P**rocessing **E**lement

Array-Native 
Nonlinear Acceleration
Shape-Constrained Neural Approximation(**SCNA**)
形状限制下的神经形态近似

用SCNA取代了Attention计算当中的非线性操作，采用异构PE的方式实现，在量化的问题上，利用SCNA的线性，实现了scale fused的计算数据流
# Limitation

![[file-20260730102310643.png]]量化越深、GEMM越快，非线性算子占比越大，成为系统级瓶颈。

## 现有方案及局限

### SFU（特殊功能单元）
- **核心思路**：硬件直接实现exp、log等非线性函数
- **局限**：面积和功耗开销大；不随脉动阵列扩展，无法跟上GEMM加速节奏
### LUT and PWL
#### 查表法（LUT）
- **核心思路**：预计算函数值存入查找表，查表替代计算
- **局限**：高精度需要大容量表格，存储开销增长快；可扩展性差

#### 分段线性近似（PWL,Piecewise Linear）
- **核心思路**：将非线性函数分段用线性函数逼近
- **局限**：高精度需要更细的分段，控制逻辑复杂度上升；函数特异性强，通用性差

#### Limitation

LUT和PWL的本质都是把输入的值切分成小的区间，每个区间用对应的function去处理。所以不可避免会面对segment的操作，随之而来就会造成以下问题
##### breakpoint management
seg和seg之间的分界，当精度要求提高的时候断点数量增加，存储表变大，管理断点的逻辑也更复杂
##### segment selection & comparison logic

 分片选择的时候就是在给定输入X的时候判断x落在哪个segment里，而比较逻辑则会随着分片数量计算精度的提高而变得更加复杂

### 学习型替代函数（Learned Surrogate）
- **核心思路**：用可学习的简单函数拟合目标非线性函数
- **局限**：训练开销；泛化性与精度难以兼顾

### 可编程非线性引擎
- **核心思路**：设计专用可编程单元覆盖多种非线性算子
- **局限**：将非线性计算视为**独立执行域**，有独立的映射和控制开销；与主计算阵列耦合度低。同时在引入Quant的情况下**没有解决量化失配的问题**

### 阵列融合设计（Array-fused）
- **核心思路**：将非线性处理移近主计算阵列
- **局限**：多数方案仍specialized（适用范围窄）；仍依赖大量辅助结构（LUT、缓冲、路由、混合精度处理），并未真正消除开销

## 关键Gap
现有方案无法同时满足三个目标：
1. **广泛的算子支持**（覆盖Softmax、GeLU、SwiGLU、LayerNorm等）
2. **高精度逼近**（不显著损失模型质量）
3. **硬件高效、可扩展执行**（能跟上脉动阵列的GEMM的速度，不引入过大面积/功耗开销）
## Common Limitation

1. depend on function-specific approximation structures
2. hardware cost does not scale cleanly with throughput(难以scale)
3. 低精度执行

# Motivation

## 非线性算子的特性

很多非线性算子在输入域上有着相似的结构，因此可以被**ReLU+仿射变换层**来实现。

**仿射（Affine Transform）** 是一个**数学概念**，指形如 ( y = Wx + b ) 的运算（线性变换加平移）。论文中频繁提到的 **“affine transforms”**（仿射变换），是指构成 SCNA 近似器的基本运算单元，也就是每个神经元里的加权求和部分 。

SCNA 的形式是：

$$
SCNA_\theta(x) = \sum_{i=1}^{S} \text{ReLU}(w_i \cdot x + b_i)
$$

其中 **( w_i x + b_i ) 这一段就是仿射变换**。不同的非线性函数（Exp、Sigmoid、Rsqrt 等）会**学习到不同的权重 (w_i, b_i)**，从而让这组“仿射+ReLU”的和逼近目标函数，但结构不变。  
所以并不是“把不同操作映射到不同 ReLU 激活层”，而是**同一个 ReLU 基函数族，配以不同仿射参数，就构成了通用逼近器**。论文还通过形状约束（单调、凸性、对称）来保证近似效率，这是它与无约束神经网络的关键区别 。

ReLU是为了在训练过程中引入非线性，并且作为一个简单的截断器在硬件上是好实现的。这样就可以在对脉动阵列的微量拓展上实现Array-Native的分线性计算

### 非线性算子的局限

1. 计算规模小 SFU based
2. 非线性算子计算的时候需要把数据搬运到SFU上，产生了流水线bubble
3. Systolic Array内部整体以低精度高速运转，而SFU需要在更高的精度下进行计算，所以在跨域计算的时候就需要在接口处引入quant和de-quant的操作
4. 不同的计算单元对应不同的指令集和映射逻辑，使得在runtime过程里需要把两套计算转化为不同的计算图


## Attention块中存在大量的非线性算子

| 非线性算子              | 出现位置                            | 作用                           |
| ------------------ | ------------------------------- | ---------------------------- |
| **Exp**            | Softmax 中                       | $e^{x_i}$，计算注意力权重            |
| **Rsqrt**          | LayerNorm / RMSNorm 中           | $\frac{1}{\sqrt{ var }}$，归一化 |
| **Erf**            | GELU 激活函数中                      |                              |
| **Sigmoid**        | SwiGLU / SiLU 中                 |                              |
| **归约 (Reduction)** | Softmax 的 、LayerNorm 的 mean/var | 行内求和、求均值                     |
## Quant

Modern accelerators typically provide much higher GEMM throughput at low precision.

为了提高GEMM操作的吞吐量，会在低精度下运用GEMM。

但是非线性操作的特点是**数值敏感**因此需要在高精度下进行计算，所以现有的llm推理都应用了混合精度的计算 

## GEMM和SFU之间的失配

![[file-20260717121820323.png]]

GEMM产生的数据远远多于SFU所能够处理的数据，即使把pipeline设计好了，由于可处理的数据之间的不匹配，仍然会由于速率差造成流水线的是stall
# Solution/Contributor

## SCNA(Shape-Constrained Neuron Approximator)

 本质上就是前文提到的一个单隐藏层的ReLU网络

### 1.非线性操作的structure-constrained

Many LLM nonlinear operators share strong shape priors over their practical domains.如果不做结构约束的话，就相当于是忽略掉了这一在结构上的prior，会导致训练出来的函数存在许多未对齐的值(redundant)

![[file-20260717164038964.png]]

structure prior相当于就是**对非线性函数几何特性的“提前预知”**。以往的研究把非线性函数当成“黑盒”来直接拟合，而 SCOPE 则是将这些数学定理直接写进神经网络的参数设计中，不让网络走弯路。利用这样的结构先验来设计网络，使得设计出的网络更加稳定。

本文抓住的prior包括单调以及凸函数，并且论文发现 LLM 中很多非线性算子经过输入域约束、对称性利用和反射后，可以统一归约到负半轴上的 canonical practical region，因此 SCNA 只需要在该输入区域逼近函数。为了让 ReLU 基函数在这个区域产生有效的分段线性变化，其 hinge point 被约束在该区域内（通常小于0）。针对于非线性操作的负半轴输入设计了一个标准拟合方式

### 2.SCNA的训练

SCNA的训练需要考虑：
1. 怎么准备输入的范围还有输出的target(标签)
2. 怎么编码非线性的约束
3. 怎么定义训练的损失函数，使得训练出来的结果能够满足之前做的一些约束

**对称和反射两个操作可以在Array上做吗**

![[file-20260717173415622.png]]

### solution1:输入域的缩减

把输入的参数限制在x<0的范围内，x>0的部分由x<0的部分翻转过去
### solution2:正-重参数化

如果仅仅把训练过程中的负值替换成一个比较小的正值(硬剪枝)，那么不可避免的会遇到梯度信息难以传回的问题，所以采用的solution是采用原始无约束的参数作为指数来代替原参数
$$
w = e^{w_{\text{raw}}},  b = e^{b_{\text{raw}}}
$$
由于指数函数本身的求导特性，使得梯度信息可以很好的保存

### solution3-损失函数的设计
**Boundary-Aware**

![[file-20260717195118261.png]]

## Array-Native Execution of SCNA 
 除了SCNA网络之外还对脉动阵列做了拓展，使得非线性的运算能够落在Array上
y′ = y + ReLU(wix + bi )SCNA的计算形式和Systolic Array原生的计算架构相契合(**内部包含大量乘加单元**)，因此可以对Systolic Array做拓展来实现该计算过程
### Systolic Array的架构

![[file-20260717203626367.png]]

### 对PE的轻量拓展

![[file-20260717202948209.png]]

在GEMM的计算过程中，左右PE都用于GEMM的计算，但是在SCNA的计算过程中，左边的PE主要用于Affine Reflection的计算，右边的PE则负责ReLU操作以及累加

![[file-20260717210753668.png]]

### 对GEMM和SCNA之间可以overlap的理解

SCNA在执行的时候只使用了垂直方向的dataflow，以及PE阵列中的一部分Register以及水平方向的dataflow是空闲的，那么就可以在SCNA的计算期间进行**权重的预加载**？这样类似于实现了算子的融合。权重按道理应该加载到reg3，但是在SCNA的计算过程里会使用reg3,所以应该是先加载到reg1里面，然后从reg1搬运到reg32

### Array-Native的SCNA嵌入flash-Attention的流水线

![[file-20260718164930620.png]]



Exp等非线性操作不再是独立的SFU阶段，而是从accumulator送回同一个systolic Array，由SCNA来计算
## Scale-fused quantization dataflow

把量化尺度融合到离线的SCNA参数里，使得SCNA的仿射参数能够嵌入到GEMM的流水线当中，如果不对齐的话，*每经过一个affine或者ReLU都要插入量化和反量化步骤*，一旦插入了dequant，就会回到SFU上计算。没对齐的意思就是，拿softmax举例，softmax consume的是GEMM结果，GEMM在systolic Array上如果采用INT8的量化格式，输出的是INT32，INT32的格式在进行softmax的计算的时候，为了保证softmax的计算精度，需要对softmax进行反量化，这样的反量化过程是需要把数据搬运到SFU进行计算的，这样的搬运过程对于会fall back SCNA带来的高吞吐量。

### 量化计算和实际尺度之间的boundary

对于GEMM而言，量化的尺度在计算过程中可以传递

![[file-20260718195447517.png|200]]

在GEMM中scale能够直接传递，但是非线性操作中，计算结果的量化尺度并没有这样的映射关系。所以说非线性操作在计算的时候需要先把操作的数据dequant成实际的具体的数值再进行运算。

![[file-20260718200206582.png]]

为了在Array中使用SCNA，所以要把int32的GEMM输出转换成int8的输入

![[file-20260718201129730.png|400]]

INT32-INT8无论怎么样都会经过舍入和阶段以及不同算子的scale的数据流的管理，本质上没有建立输入的scale、内部参数scale以及输出scale之间可直接传播的关系，因此在计算结束后仍然需要解量化为实值语义才知道怎么编码到下一层所需的INT8.

### 核心目的

让 GEMM 之后的低精度结果可以直接进入 SCNA，而**不需要先反量化成 FP16/实数，再执行非线性**。

### 数学推导

#### 1. GEMM 的量化关系

对于上游量化 GEMM，有权重和激活的量化表示：

$$W \approx s_W \hat{W}, \quad A \approx s_A \hat{A}$$

其中 $s_W, s_A$ 为量化 scale，$\hat{W}, \hat{A}$ 为量化后的整数值。

脉动阵列计算得到 INT32 累加结果：

$$\hat{G} = \hat{W} \hat{A}$$

其对应的真实值（dequant 后）为：

$$G \approx s_W s_A \hat{G}$$

> 关键特性：GEMM 中 scale 能直接传递（$s_W \cdot s_A$），不需要恢复实值。

#### 2. Requantize 为 SCNA 输入

将 $\hat{G}$（INT32）requantize 为 $\hat{P}$（INT8）作为 SCNA 的输入。若这一步的缩放因子记为 $s_P$，则：

$$\hat{G} \approx s_P \hat{P}$$

因此 $\hat{P}$ 所代表的真实输入为：

$$P \approx s_W s_A s_P \hat{P}$$

记 SCNA 输入的**总有效 scale** 为：

$$\boxed{s = s_W s_A s_P}$$

#### 3. 利用 ReLU 正齐次性吸收 scale

原始 SCNA 在实数域中近似目标非线性函数：

$$F_\theta(x) = \sum_i \text{ReLU}(w_i x + b_i)$$

部署时真正需要计算的是 $F_\theta(s\hat{P})$，即需要在量化输入 $\hat{P}$ 上执行，同时还要额外做 scale 乘法。

利用 **ReLU 的正齐次性**：

$$\text{ReLU}(s \cdot z) = s \cdot \text{ReLU}(z), \quad s > 0$$

可将 $F_\theta(s\hat{P})$ 改写为：

$$F_\theta(s\hat{P}) = s \sum_i \text{ReLU}\left(w_i \hat{P} + \frac{b_i}{s}\right)$$

**效果**：scale $s$ 被提到求和外面，内部的 ReLU 只需对整数 $\hat{P}$ 做运算，无需在每一步之后做 dequant。

#### 4. Bias 重参数化（Offline）

将 SCNA 的 bias 重参数化为：

$$b_i' = \frac{b_i}{s_W s_A s_P}$$

而 $w_i$ **保持不变**。

由于静态量化下 $s_W$、$s_A$ 和 $s_P$ 都在 calibration 后固定，这个除法**完全在 offline 阶段完成**。

#### 5. 运行时计算

运行时阵列只执行：

$$\boxed{\hat{Q} = \sum_i \text{ReLU}(w_i \hat{P} + b_i')}$$

即**整数 MAC + 加法 + ReLU**，不包含除法，也不需要显式恢复 FP16 实值。

输出 $\hat{Q}$ 仍携带有效 scale $s_W s_A s_P$，若下一层需要 INT8，再做一次静态 requantization。

