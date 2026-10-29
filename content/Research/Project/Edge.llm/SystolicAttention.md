# Motivation

在Systolic-Based的加速器上，有一些操作会fallback到外部的向量/标量单元上，在这样的背景下，数据在不同计算单元之间的搬运会损害矩阵数据的复用，导致Preload的overhead。

因此FSA的想法就是将整个 FlashAttention 完全在脉动阵列上运行来解决，使得矩阵乘法和 Softmax 运算能够以更细的粒度利用并共享脉动阵列的算力（FLOPs/s）。因此，Softmax 不再受限于向量/标量单元的吞吐量，且由于所有计算均在同一位置完成，数据移动开销和 SRAM 端口争用也得以消除。为了高效实现该方法，**除了仅使用脉动阵列执行包括 exp、rowmax 和 rowsum 在内的 Softmax 运算外**，还必须有效地重叠各种操作，以最大化阵列利用率。

FSA 将 rowmax 和 rowsum 视为归约操作，并利用一组比较器和一个专门的向上数据路径对其进行即时（on-the-fly）和原位（in-place）处理，从而无需将其存储在本地 SRAM 中。

对于非线性操作，FSA则采用PWL方法，采用分段线性拟合的方式来把非线性操作也放到SystolicArray上来计算

# Contribution

- FSA的架构，该架构能够在单一Array上执行整个FlashAttention的操作
- 提出了SystolicAttention，是一个针对FSA优化的Kernel，使用这一Kernel可以提高FSA的内存利用率
-  Python 编程接口，允许用户为 FSA 编写自定义内核。https://github.com/VCA-EPFL/FSA

# Flash Attention的伪代码

![[file-20260724160104476.png]]

其中包含大量的element-wise以及reduction的操作，因此文章中对Systolic Array做了如下拓展，使得FlashAttention能够全量在SystolicArray上运行，减少了数据搬运，大大提高了**data reuse**

# Design of FSA

对SystolicArray做了三个扩展:
- 向上的数据通路
- CMP单元
- PE重构以适应PWL的计算

![[file-20260724160506123.png]]

## rowmax的实现
在实现rowmax的时候，Q按列放到FSA里，在on the fly的时候把矩阵乘计算出来的S=QK^T沿向上的数据通路送到CMP里，在CMP中进行S最大值的更新,在更新了之后把最大值沿着向下的数据通路传递

## exp的实现

FlashAttention采用safe softmax，所以指数小于等于0，因此指数函数的范围就可以被限定在一个很小的范围内，采用分段线性的方式来做近似

![[file-20260724165930265.png]]

在具体的硬件中，对SystolicArray的PE单元做了修改，Split单元根据指数移动尾数，使它从“**科学计数法形式”变成“小数点位置确定的定点形式**”，然后从小数点处分开整数位和小数位。从Array的左边和顶部流式传输斜率和截距，对小数位而言使用PWL做近似计算，对整数位而言可以通过改变指数位的方式来乘回指数位。

关于浮点数的表示[[浮点数在计算机中的表示]]

![[file-20260724221050679.png]]


## rowsum的实现

![[file-20260724172023851.png]]

利用了SystolicArray的MAC单元，只不过输入的一个矩阵全1，从上往下输入初始的累加矩阵(全0)，另一个矩阵是目标的rowsum的操作数，这样就实现了rowsum。第二次矩阵乘法 O = PV（算法 1，第 15 行）可以沿下行数据路径（以蓝色突出显示）并行进行，且在行和（rowsum）操作开始后的一个周期即可启动。

## 在FSA上流水化操作

Overlapping Computations with  SystolicAttention

![[file-20260727140325298.png]]

# AttentionCore的实现

![[file-20260727155049481.png]]

注意在计算过程中，Q矩阵先PreLoad到PE之中，K V采用双缓冲结构来存储，使得计算与存储过程能够重叠。

![[file-20260727155710510.png]]

外层循环控制Q tile的Pre Load过程，内存循环进行Score的计算以及Softmax还有Output的计算

![[file-20260727155622701.png]]

