# 结构化模型
利用Verilog内的内置门类型以及其他组件实例化，对这些实例化后的组件进行互联来实现组合逻辑的功能。

![[file-20260615233217346.png|814]]

而且需要注意，在Verilog中涉及一系列的**并发语句**，这是和传统的软件程序语言不同的，因为只有并发语句才能较好地模拟硬件的行为。

门和其他语句需要通过实例语句来将其实例化，一般采用下面这种形式来对模块进行实例化，这样更能明确端口之间的对应关系

实例语句：
``` Verilog
component-name instance-identifier(
.port-name(expr),
.port-name(expr),
.port-name(expr),
……
);
//expr为表达式，必须是连接到端口的本地网格的名字s
```
注意 实例标识符(instance-identifier)在一个模块内必须是唯一的，为了避免在实例化多个模块时发生冲突。

而对于内置的多数入门而言，所定义的端口名顺序应该是
>(输出，输入，输入，……)

对于反向器和三态门，对应的端口顺序应该为
>(输出，数据输入，使能输入)

内置的多输入门只能使用这种实例

一个禁止门的结构化Verilog模型($\text{out} = \text{in} \cdot \overline{\text{invin}}$)

```verilog
module Inh(in,invin,out);
	input in,invin;
	output out;
	wire notinvin;
	
	not U1 (notinvin,invin);
	and U2 (out, notinvin, in);
endmodule
```

使用结构化模型描述以下电路:

![[file-20260616000219246.png|688x176]]

```verilog
module VrXOR(in1,in2,out);
	input in1,in2;
	output out;
	wire inh2,inh1,notinh2,notout;
	//其中一个输入端口带bubble的组件为Inh,就是上一个例题
	VrInh U1(.out(inh1),.invin(in2),.in(in1));
	VrInh U2(.out(inh2),.invin(in1),.in(in2));
	not U3(notinh2,inh2);
	VrInh U4(.out(notout),.invin(inh1),.in(notinh2));
	not U5(out,notout);
endmodule
```

# 数据流模型

假如 Verilog 仅仅有实例语句，那它只不过就是⼀种分层的⽹格列表描述语⾔⽽已。“ 连续赋值语句”允许 Verilog 根据数据流程和电路的操作来描述组合电路，这种描述形式被称为数据流设计或描述dataflow model or description 。
## 连续赋值语句
连续赋值语句的语法：

![[file-20260616001309205.png|808]]

连续赋值语句计算出等号右边的值，赋值给等号左边，如此连续地赋值。
## 例子

eg1:用连续赋值语句来描述下图电路：

![[file-20260616001724532.png|764x257]]

```verilog
module prime(N,F);
	input[3:0] N;
	output F;
	assign F = (~N[3] & N[0])|(~N[3] & ~N[2] & N[1])
				|(~N[2] & N[1] & N[0])|(N[2] & ~N[1] & N[0]);
endmodule
```

eg2:用于选择一个输入字节(一个字节8位)的Verilog模块(其中selA信号的优先级最高，其次是selB,selC，如果没有选择则输出为0)
```verilog
module bytesel(A,B,C,selA,selB,selC,Z);
	input [7:0] A,B,C;
	input selA,selB,selC;
	output [7:0] Z;
	
	assign Z = selA?A:(selB?B:(selC?:C:8'b0));
endmodule
```

# 行为化模型(过程块)

## always语句块

always 程序块中的过程语句是按顺序执⾏的，然⽽，always 程序块本身⼜要跟同⼀个模块（实例、连续赋值以及 always ) 中的其他并发语句⼀起并⾏地执⾏

```verilog
1.
always @ (signal-name or signal-name...or signal-name)
	procedure-statement
2.
always @ (signal-name , signal-name... , signal-name)
		//敏感信号列表，可以用or和,隔开
	procedure-statement
3.
always @ (*) procedure-statement //*指可能改变结果的所有信号
4.
always @ (posedge signal-name) procedure-statement
5.
always @ (negedge signal-name) procedure-statement 
//4.5两种格式用于时序电路的设计
6.
always procedure-statement
```

## 推理产生的锁存器

![[file-20260617235445065.png|738x350]]

说简单点就是，考虑下面这样的一个过程块，假设对信号X赋值，sel为1位选择信号
```verilog

always @(*) begin
	if(sel==1'b0) begin
		X = 1'b0;
	end
end
```

那么在这种情况下，在sel\==1'b1的情况下，X就会无值可赋，这样的话，综合器就会综合出如下的代码，产生锁存器

```verilog
always @(*) begin
	if(sel==1'b0) begin
		X = 1'b0;
	end 
	else begin
		X = X;//此为电路综合出的锁存器❌
	end
end
```

这一行为告诉我们，在条件过程语句中，需要保证对目标信号在每一个执行路径上都有一个值赋给目标信号。

## 赋值语句


```verilog
variable-name = expression;//阻塞赋值
variable-name <= expression;//非阻塞赋值
```

![[file-20260618000240819.png|891]]

而阻塞赋值的区别就是在于，在同一个过程块里，只有在对左边项的赋值结束后，才会到下一行语句的计算。而非阻塞赋值，可以理解为同一过程块中的语句并行进行计算，在过程块结束的时候，把值同时赋给左边。
比如
```verilog
always @(posedge clk) begin   
	 a <= b;    
	 b <= a;
 end
```

在某个 `posedge clk` 到来时，假设原来：

```verilog
a = 1;b = 0;
```

执行过程是：

```verilog
a <= b;   // 先读取旧的 b，也就是 0，预约 a 之后变成 0
b <= a;   // 先读取旧的 a，也就是 1，预约 b 之后变成 1
```

等这个时间步的非阻塞更新阶段到来时：

```
a = 0;b = 1;
```

所以它实现的是**寄存器同时更新**，像两个 D 触发器在同一个时钟沿一起采样。

---
而阻塞赋值 `=` 是：

```verilog
always @(posedge clk) begin    
	a = b;    
	b = a;
end
```

还是假设原来：

```verilog
a = 1;b = 0;
```

执行过程是：

```verilog
a = b;   // a 立刻变成 0
b = a;   // 此时读到的 a 已经是 0，所以 b 也变成 0
```

最后：

```
a = 0;b = 0;
```

这就不是两个寄存器同时更新的效果，而更像软件程序一行一行执行。

### 几个重要的规则

![[file-20260618001051709.png|894]]

**过程块中的被赋值信号必须为reg类型的**
## begin-end 程序块

![[file-20260618001248140.png|901]]

**如果begin-end块中定义了变量，那么必须对该程序块命名**

## if-else

![[file-20260618001547169.png|335x123]]

使用if语句构成素数检测器模块

```verilog
module Vrprimei (N, F);
    input [3:0] N;
    output reg F;
    parameter OneIsPrime = 1; 
    // 如果你不认为 1 是素数的话，就把该值变为 0
    
    always @ (*)
        if (N == 1) 
            F = OneIsPrime;
        else if ( (N % 2) == 0 )
            begin 
                if (N == 2) F = 1; 
                else F = 0; 
            end
        else if (N <= 7) 
            F = 1;
        else if ( (N == 11) || (N == 13) ) 
            F = 1;
        else 
            F = 0;
endmodule
```

## case语句

![[file-20260618001858865.png|362]]

![[file-20260618001923684.png|891]]

case语句中的choice一般都是互斥的，这样就能编译出更便宜更快的MUX，如果不是互斥的话，就会编译出昂贵的优先编码器，因此编码时需要避免出现非互斥的case语句，如果需要优先编码器的话，可以使用嵌套的if语句。

如果choice没有完全包含所有的selection-expressing的话，就需要使用default语句，**防止综合器综合出锁存器**。

最后注意choice和selection-expressing的位宽需要是一致的

### 另外的case语句

![[file-20260618002507205.png|884]]

## 循环语句

![[file-20260618091941574.png|905]]

表中最后两行为循环语句用于模拟的常见语法。

使用for循环语句设计一个八位比较器

```verilog
module comp(X,Y,gt);
	input [7:0] X,Y;
	output reg gt;
	integer i;
	
	always @ (X,Y) begin
		gt = 0;
		for(i=0;i<=7;i=i+1) begin
			if(X[i]&~Y[i]) gt=1;
			else if(~X[i]&Y[i]) gt=0;
		end
	end
endmodule
```

**for 循环不是在硬件里真的像软件一样一个时钟一个时钟地跑 8 次。**

在这个组合逻辑 `always @(X, Y)` 里面，综合器会把这个 `for` 循环展开成一堆组合逻辑，大概等价于：

```verilog
gt = 0;
if (X[0] & ~Y[0]) 
	gt = 1;
else if (~X[0] & Y[0]) 
	gt = 0;
if (X[1] & ~Y[1]) 
	gt = 1;
else if (~X[1] & Y[1]) 
	gt = 0;
...
if (X[7] & ~Y[7]) 
	gt = 1;
else if (~X[7] & Y[7]) 
	gt = 0;
```

所以它本质上是在描述一个**组合比较电路**，不是描述一个真正运行 8 拍的循环控制器。

### disable语句，了解即可

![[file-20260618095517071.png|886]]

### 其他循环语句

![[file-20260618095605306.png|911]]

# 测试平台(testbench)

![[file-20260618095832608.png|889]]

编写素数检测器的testbench

```verilog
`timescale 1ns / 100ps
module prime_tb1();
	reg [3:0] Num;
	wire Prime;
	prime UUT(.N(Num),.F(Prime));
	
	initial begin:TB//begin-end块中定义了局部变量，所以要命名
		integer i;
		for(i=0;i<=15;i=i+1) begin 
			#10 Num=i；//每隔10ns(单位看timescale，仿真步长)对Num赋值
		end
	end
endmodule
```

但是这个testbench只考虑对端口的输入赋不同的值，并没有用任何方式检查这些输入，这样不是很直观，只能通过波形来判断模块的行为是否正确。以下是一个交互性比较高的测试平台

![[file-20260618110754781.png|914]]

![[file-20260618110807562.png|395]]



更多的 testbench 可使用搜索功能寻找一下