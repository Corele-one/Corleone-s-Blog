
# 相关手册

Scalar Core:[Hexagon V79 Programmer Reference Manual](https://docs.qualcomm.com/doc/80-N2040-60/topic/introduction.html)

HVX Core:[V79 HVX Programmer Reference Manual](https://docs.qualcomm.com/doc/80-N2040-61/topic/introduction.html)

HMX Core:[V81 HMX](https://docs.qualcomm.com/doc/80-N2040-62/80-N2040-62_REV_AA_Qualcomm_Hexagon_V81_HMX_Programmers_Reference_Manual.pdf)

# Tool-Chain
## MLIR与QNN

### QNN
QNN 是高通官方提供的一个“静态图 Runtime / 算子库”；输入一个 ONNX/PyTorch 图，QNN Converter 将其转化为 QNN IR，经过图优化后编译成一个包含计算图和权重的静态库。但是QNN的局限性在于QNN的可定制性非常差，难以控制细粒度的内存，自定义算子的开发及其繁琐。

### MLIR
而 MLIR 是一个“编译器基础设施”，通常位于 QNN 的上层或作为替代 QNN 的下行编译器。MLIR 可以**生成代码供 QNN 调用**（作为一个自定义算子包 UDO），也可以**完全绕过 QNN**，直接编译生成底层的 DSP 汇编/LLVM 代码，通过 FastRPC 直接送给 NPU 运行。

前端使用PyTorch来构建模型，使用Triton来编写算子 
MLIR在NPU上写算子的相关论文:
[Hexagon-MLIR: An AI Compilation Stack For Qualcomm’s Neural Processing Units (NPUs)](https://arxiv.org/pdf/2602.19762)

![[file-20260721151859940.png]]

## llama.cpp
`llama.cpp` 的灵魂在于 **GGML 引擎**：它是完全**动态的、C/C++ 裸写、极度轻量且控制权完全掌握在开发者手中**的运行时。

1. `llama.cpp` 负责整体的 Token 循环、Context 管理和 CPU 侧调度。当遇到大块的 GEMM/MatMul 算子时，通过 QNN Backend Offload 给 NPU 处理。
2. 绕过 QNN，基于 FastRPC + HVX/HTP 编写原生 GGML 算子
3. 利用 Triton / MLIR $\rightarrow$ Hexagon 生成算子，再嵌入 `llama.cpp`

## llama.npu
From:[llama-npu](https://github.com/haozixu/llama.cpp-npu)
从llama-npu里总结出了该项目所使用的CPP Intrinsic，作为编译器内置的特殊函数，使用时不需要像常规库函数那样去寻找外部文件。它们直接映射到底层的硬件指令，在性能上表现极佳，可以用于定制计算。通过Intrinsic能够实现特定硬件上的数据布局与流水线操作

# Hexagon处理器架构

From:Scaling LLM Test-Time Compute with Mobile NPU on Smartphones NPU的架构图如下图所示

![[file-20260721161123604.png]]

## Scalar Core

作为Hexagon的标量核心的微架构框架，采用VLIW架构，超大指令字,以Packet为一个单位来发射指令

每个周期处理1-4条指令的packet，一个packet包含多个指令的时候，指令并行执行，但是可并行执行的指令同时受限于指令类型

ScalarCore架构: 

![[file-20260721153427191.png]]

Each includes a 64-bit shifter and a vector multiply/accumulate unit with four 16 x 16 multipliers to support both scalar and vector instructions.

### 指令集的特点
For the Hexagon processor to achieve large amounts of work per cycle, the instruction set has the following properties:
- Static grouping (VLIW) architecture
- Static fusing of simple dependent instructions
- Extensive compound instructions
- A large set of SIMD and application-specific instructions
To support efficient compilation, the instruction set is orthogonal with respect to registers, addressing modes, and load/store access size.

### Register(L0 Memory)

 32 个 32 位通用寄存器（编号为 R0 至 R31）。这些寄存器在指令中存储操作数。
 三个通用寄存器——R29 到 R31——支持子程序（调用）和软件栈。子程序和堆栈指令隐式修改寄存器。R29 至 R31 分别被别名为 SP、FP 和 LR。

### Instruction

![[file-20260812120924693.png]]

该处理器支持最多四个并行指令。这些指令在四个并行流水线中执行，这些流水线被称为“slot”。这四个槽分别命名为slot 0、slot 1、slot 2 和slot 3。

## HVX

HVX采用SIMD架构，作为超宽SIMD矢量处理器，极其灵活。擅长处理复杂的 Element-wise（逐元素）运算、Softmax、Quant/Dequant（量化/反量化）、Reshape/Transpose 等。在Attention Kernel中可以用于**SCNA的实现**。
==HVX是Hexagon Core(Scalar Processor)的协处理器==

![[file-20260721161802908.png]]

Hexagon 指令集架构通过添加 HVX 指令得到了扩展。这些指令能够利用 HVX 计算资源，并且可以在非常长的指令字包中自由地与普通的 Hexagon 指令混合使用。此外，HVX 指令还可以使用核心中的Scalar source operands。

### HVX Context
用于描述HVX的状态，一个Thread使用HVX时，不仅需要执行单元，还需要保存:
- vector register file,
- vector predicate file, 
- and the ability to execute instructions using this state

Scalar Core的硬件Thread动态附加到Vector Context中，enabling Thread to execute HVX instructions.

![[file-20260721165209681.png]]

Threads和HVX Context并不是一一对应的，HVX Context是HVX指令执行时所需要的Context，Scalar Core能够在程序运行的过程中附加HVX Context来实现HVX指令。

### Memory Access

#### VTCM(Vector Tight-Coupled Memory)
HVX 支持一种称为向量紧密耦合内存的本地内存类型，用于临时缓冲区和数据分散/收集操作。这种内存的大小由实现方式决定，可以通过配置表来查看其大小。与其它内存一样，VTCM 也需要进行虚拟地址到物理地址的转换。这种内存具有更高的性能和更低的功耗。

VTCM比L2 Cache更快，并可以减轻L2 Cache的压力，**除了HVX之外，普通的Hexagon访存指令也可以访问该内存**，并且Memory采用Unified Byte Access，共享的内存有助于高速pipeline的实现。VTCM很像GPU里的Shared Memory

#### ==VTCM、L1 Cache、L2 Cache之间的区别==

| 属性        | L1 Cache   | L2 Cache | VTCM                |
| --------- | ---------- | -------- | ------------------- |
| 物理位置      | 最靠近核心      | 片上共享层    | 片上 SRAM             |
| 管理者       | 硬件         | 硬件       | 软件                  |
| 数据来源      | 通常来自 DDR   | 通常来自 DDR | 软件显式搬入              |
| 是否自动替换    | 是          | 是        | 否                   |
| 是否可能 miss | 是          | 是        | 通常无传统 cache miss    |
| 容量        | 最小         | 较大       | 通常更大、实现相关           |
| 延迟可预测性    | 较低         | 较低       | 较高                  |
| 常见用途      | 热数据、栈、标量访存 | 大块数据缓存   | tile、中间结果、HMX/HVX共享 |
## HMX

![[file-20260812094221694.png]]

硬化的 Systolic Array（脉冲阵列）/ 矩阵乘加单元。**擅长**极其高效地吞吐 **INT8 / INT16 的 GEMM（矩阵乘法）**。 **在 Attention 中**计算 $Q \times K^T$（MatMul 1）以及 $\text{Score} \times V$（MatMul 2），以及 Q, K, V 的 Linear 投影。 32x32的脉动阵列+三种寄存器堆.


 
HMX是HVX的协处理器，并且是SIMD的计算单元

![[file-20260721204356991.png]]
### HMX包含的寄存器堆
HMX包含三个寄存器堆:
- accumulator registers
- convert state registers
- bias registers
#### Accumulator

**累加的寄存器**(accumulator registers)用于存储积的和

![[file-20260721205439365.png|200]]

#### Convert State
**状态转换的寄存器**(convert state registers)存储了积之和在经过激活函数后的结果。许多激活函数可以应用到状态转换寄存器上

![[file-20260721205456044.png|400]]

#### Bias
**偏置寄存器**(bias registers)存储了激活函数使用的变量的值，从acc到con-state里面，程序需要从VTCM里把值存到bias里面

![[file-20260721210241855.png]]

### 支持的指令类型

1. Multiply(Weight\*Activation所使用到的指令)
2. Convert transfer
3. Write convert state 

#### Multiply Instruction

**先加载激活值，后加载权重**

```c
void Q6_activation_hf_mxmem_RR(Word32 Rs, Word32 Rt); void Q6_weight_hf_mxmem_RR(Word32 Rs, Word32 Rt);
```
该指令实现了以下的计算

![[file-20260721212230046.png]]

Multiply的操作粒度——Crouton

HMX 基础矩阵乘指令不是给一个单独元素地址，而是给出一个 2 KB 对齐的 activation crouton 基地址，硬件按照预定格式成块读取并执行矩阵乘。

![[file-20260721212607500.png]]

An activation crouton is the basic unit in HMX that represents a tensor being operated on by the weights. Each multiply instruction operates on at least one crouton.

Crouton是一个三维张量\[X,Y,C],Crouton和一个二维矩阵的映射关系大概是
- 行：`spatial`，由 (x,y)展平得到；
- 列：`input channel` ccc。
对于YYYXX的mask而言，s=x+4y，所以三维元素a\[x,y,c]
就可以写成A\[s,c],s为spatial，是二维矩阵的spatial索引

**Crouton是逻辑数据块、二维矩阵是计算视图、VTCM是其物理存储格式**

![[file-20260721213922156.png]]

HMX 的 activation 指令不会接收一个 `A[s,c]` 元素，也不会接收一个普通二维数组对象。

它拿到的核心信息是：
- 一个 **2 KB 对齐的 VTCM 基地址**；
- spatial mask；
- input-channel 起止范围；
- 其他 offset/control 字段。

手册明确规定，activation 地址字段指向 VTCM 中的一个 crouton，且必须 2 KB 对齐；一个 FP16 activation crouton包含 323232 个 spatial、323232 个 input channel，每格为 16 bit。
Mult指令中的spatial-mask通过5位来表示三维存储结构到二维结构的映射关系，比如图中的YYYXX-flattened所示，若YYYXX为1决定了偏移量作用在Y方向上，为0的Bit为表示作用在X方向上。
`mask = 11100`（YYYXX）且 `offset = 10100`，意为 Y 方向偏移 5，X 方向偏移 0。可用于实现非对齐的矩阵乘法。

矩阵乘法操作将结果存储在主累加器中，随后的转换传输指令可以选择性地清除并交换累加器。转换指令是访问累加器并将数据存回 VTCM 的唯一途径。

![[file-20260721215217768.png]]

在上图中，HMX 从激活单元和权重灰度单元开始，计算至绿色单元的点积。HMX 将所有灰色、金色和绿色单元的乘积之和存储在位置 (1, 0) 的累加器单元中。而从输出通道也可以看到，ACC(1,0)意味着Activation‘s spatial 1 和 Weight’s spatial 0计算出了ACC(1,0)位置处的值

#### 权重/激活值在VTCM中的存储方式

**Interleaved**

![[file-20260721225434821.png]]

在VTCM中的存储方式不是简单的row-major，HMX 按照下图所示的乘法指令顺序读取输入通道。蓝色单元格应存储在 VTCM 的前 32 位中，然后依次存储向量 1 和向量 2 中的单元格，最后存储橙红色单元格。
图像上的数字表示该特定单元格的 VTCM 的字节偏移地址，假设基地址为B，(Unified Byte Access)那么第一个FP16元素占据B+0和B+1，用起始地址来标记写成0.
A\[0,0]->0,A\[1,0]->2,从该图中可以看出weight和Activation在VTCM中的存储是Interleaved的，而非简单的row-major(是出于SIMD架构的考量吗🤔)

以Interleaved的2x2 FP16的HVX来解释TCM中的layout


#### Convert transfer instruction

转换状态传输指令(Convert transfer)利用偏置寄存器(Bias)值对累加器(Acc)数据执行转换操作，随后将结果传输至转换状态寄存器。累加器中的每个单元均经历相同的转换操作，并存储在转换状态寄存器中的相应位置。该指令随后可选择性地清除累加器数据。此指令将37位浮点累加器值转换为FP16格式。

![[file-20260721215909353.png]]

灰色方框包含转换方程的表示。橙色背景的方框代表指定的偏置寄存器参数。偏置寄存器用于对输入偏置、整形函数、比例及输出偏置进行编程。带有“Rs\[bit]”标注的金色文本表示由转换传输指令中的Rs寄存器所配置的模式。

![[file-20260721220241401.png]]

状态转换指令是由很多简单的指令来实现的

##### State Convert Reg

转换状态存储来自转换传输指令的结果。它具有32个空间单元和32个输出通道。这与累加器类似，因为累加器中的每个单元都映射到转换状态寄存器中的对应位置。

![[file-20260721220852694.png]]

#### Write convert state

![[file-20260721221342030.png]]

写入转换状态（write convert state）指令将转换状态中的 FP16 数据存储到 VTCM 的指定地址。该指令不会修改转换状态中的数据。转换状态中空间维度（spatial）乘输出通道维度（output channel）的二维结构被存储在 VTCM 中，形式为空间-x（spatial-x）乘空间-y（spatial-y）乘输出通道（output channels）的三维结构。这一额外的维度是通过将转换状态中的空间维度拆分为空间-x 和空间-y 两个维度而衍生出来的。