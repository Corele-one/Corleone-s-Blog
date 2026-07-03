# Verilog代码汇总

本文整理目录内 Markdown 笔记中的 Verilog/SystemVerilog 代码块。先放 CH5 的 Verilog 基础内容，再按组合逻辑和时序逻辑分类整理其余代码；每部分内部按章节顺序排序。

- 代码块总数：118
- Verilog基础：25 个
- 组合逻辑：41 个
- 时序逻辑：52 个

## 分类索引

### Verilog基础
- [[CH5 Verilog硬件描述语言/Verilog|Verilog]]：2 个代码块
- [[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]：19 个代码块
- [[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]：4 个代码块

### 组合逻辑
- [[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]：12 个代码块
- [[CH7 更多的组合构件/三态门|三态门]]：2 个代码块
- [[CH7 更多的组合构件/优先编码器|优先编码器]]：3 个代码块
- [[CH7 更多的组合构件/异或门和奇偶校验功能|异或门和奇偶校验功能]]：3 个代码块
- [[CH7 更多的组合构件/比较器|比较器]]：4 个代码块
- [[CH8 组合算数元件/乘法器|乘法器]]：1 个代码块
- [[CH8 组合算数元件/加法器和减法器|加法器和减法器]]：7 个代码块
- [[CH8 组合算数元件/移位和旋转|移位和旋转]]：1 个代码块
- [[CH9 状态机设计/关于无效状态的处理|关于无效状态的处理]]：2 个代码块
- [[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]：1 个代码块
- [[Exam_topic]]：3 个代码块
- [[某个老师的测试题]]：2 个代码块

### 时序逻辑
- [[CH8 组合算数元件/移位和旋转|移位和旋转]]：3 个代码块
- [[CH9 状态机设计/用verilog设计状态机|用verilog设计状态机]]：1 个代码块
- [[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]：15 个代码块
- [[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]：11 个代码块
- [[CH11 计数器和移位寄存器/计数器|计数器]]：6 个代码块
- [[CH12 Verilog状态机设计/"1"计数器|"1"计数器]]：3 个代码块
- [[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]：1 个代码块
- [[CH12 Verilog状态机设计/序列发生器|序列发生器]]：3 个代码块
- [[CH12 Verilog状态机设计/序列检测器|序列检测器]]：2 个代码块
- [[CH12 Verilog状态机设计/状态机示例1|状态机示例1]]：3 个代码块
- [[Exam_topic]]：4 个代码块

## Verilog基础

### 来源：[[CH5 Verilog硬件描述语言/Verilog|Verilog]]

#### 1. my_module

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog|Verilog]]，代码块位置 L70-L85
- 上下文：1. 声明模块时的端口声明
- 模块名：`my_module`

功能描述：

`my_module` 属于组合逻辑示例。它来自“1. 声明模块时的端口声明”这一小节。主要接口/信号包括：a, c, y1, y2。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
// ANSI 风格：端口名、方向、类型一起声明
module my_module (
    input  wire       a,        // ✅ input 只能为 wire（net类型）
    input  wire [3:0]  c,       // ✅ wire 向量输入
    output wire       y1,       // ✅ output 可以为 wire
    output reg        y2        // ✅ output 也可以为 reg
);
    // y2 作为 reg 输出，必须在过程块中赋值
    always @(*) begin
        y2 = a & c[0];
    end
    // y1 作为 wire 输出，用 assign 连续赋值
    assign y1 = c[0];
endmodule
```

#### 2. top

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog|Verilog]]，代码块位置 L100-L114
- 上下文：2. 实例化模块时的端口连接
- 模块名：`top`

功能描述：

`top` 属于2. 实例化模块时的端口连接。它来自“2. 实例化模块时的端口连接”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module top;
    reg  [7:0] data_in;    // reg 变量
    wire [7:0] data_out;   // wire 网格
    wire       clk;

    my_module u_inst (
        .a  (clk),          // ✅ input 端口：可接 wire
        .b  (data_in),      // ✅ input 端口：也可接 reg（外部驱动模块输入）
        .y1 (data_out[0]),  // ✅ output 端口：接 wire
        .y2 (data_in[0])    
        // ❌ ERROR！output 端口不能接 reg
    );
endmodule
```

### 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]

#### 3. 结构化模型

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L11-L19
- 上下文：结构化模型

功能描述：

该代码块属于比较器。它来自“结构化模型”这一小节。

代码要点：

- 这是局部语法片段，重点在语句写法而不是完整模块结构。

源代码：

```verilog
component-name instance-identifier(
.port-name(expr),
.port-name(expr),
.port-name(expr),
……
);
//expr为表达式，必须是连接到端口的本地网格的名字s
```

#### 4. Inh

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L32-L41
- 上下文：结构化模型
- 模块名：`Inh`

功能描述：

`Inh` 属于结构化模型。它来自“结构化模型”这一小节。主要接口/信号包括：in, invin, out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module Inh(in,invin,out);
	input in,invin;
	output out;
	wire notinvin;
	
	not U1 (notinvin,invin);
	and U2 (out, notinvin, in);
endmodule
```

#### 5. VrXOR

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L47-L59
- 上下文：结构化模型
- 模块名：`VrXOR`

功能描述：

`VrXOR` 属于异或/奇偶校验逻辑。它来自“结构化模型”这一小节。主要接口/信号包括：in1, in2, out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module VrXOR(in1,in2,out);
	input in1,in2;
	output out;
	wire inh2,inh1,notinh2,notout;
	//其中一个输入端口带bubble的组件为Inh,就是上一个例题
	VrInh U1(.out(inh1),.invin(in2),.in(in1));
	VrInh U2(.out(inh2),.invin(in1),.in(in2));
	not U3(notinh2,inh2);
	VrInh U3(.out(notout),.invin(inh1),.in(notinh2));
	not U5(out,notout);
endmodule
```

#### 6. prime

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L76-L83
- 上下文：例子
- 模块名：`prime`

功能描述：

`prime` 属于组合逻辑示例。它来自“例子”这一小节。主要接口/信号包括：N, F。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module prime(N,F);
	input[3:0] N;
	output F;
	assign F = (~N[3] & N[0])|(~N[3] & ~N[2] & N[1])
				|(~N[2] & N[1] & N[0])|(N[2] & ~N[1] & N[0]);
endmodule
```

#### 7. bytesel

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L86-L94
- 上下文：例子
- 模块名：`bytesel`

功能描述：

`bytesel` 属于组合逻辑示例。它来自“例子”这一小节。主要接口/信号包括：A, B, C, selA, selB, selC, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module bytesel(A,B,C,selA,selB,selC,Z);
	input [7:0] A,B,C;
	input selA,selB,selC;
	output [7:0] Z;
	
	assign Z = selA?A:(selB?B:(selC?:C:8'b0));
endmodule
```

#### 8. always语句块

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L102-L119
- 上下文：always语句块

功能描述：

该代码块属于有限状态机设计。它来自“always语句块”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。

源代码：

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

#### 9. 推理产生的锁存器

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L126-L133
- 上下文：推理产生的锁存器

功能描述：

该代码块属于锁存器/电平敏感存储。它来自“推理产生的锁存器”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog

always @(*) begin
	if(sel==1'b0) begin
		X = 1'b0;
	end
end
```

#### 10. 推理产生的锁存器

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L137-L146
- 上下文：推理产生的锁存器

功能描述：

该代码块属于锁存器/电平敏感存储。它来自“推理产生的锁存器”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

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

#### 11. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L153-L156
- 上下文：赋值语句

功能描述：

该代码块属于赋值语句。它来自“赋值语句”这一小节。

代码要点：

- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
variable-name = expression;//阻塞赋值
variable-name <= expression;//非阻塞赋值
```

#### 12. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L162-L167
- 上下文：赋值语句

功能描述：

该代码块属于触发器/时序寄存器。它来自“赋值语句”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。

源代码：

```verilog
always @(posedge clk) begin   
	 a <= b;    
	 b <= a;
 end
```

#### 13. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L171-L173
- 上下文：赋值语句

功能描述：

该代码块属于赋值语句。它来自“赋值语句”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
a = 1;b = 0;
```

#### 14. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L177-L180
- 上下文：赋值语句

功能描述：

该代码块属于赋值语句。它来自“赋值语句”这一小节。

代码要点：

- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。

源代码：

```verilog
a <= b;   // 先读取旧的 b，也就是 0，预约 a 之后变成 0
b <= a;   // 先读取旧的 a，也就是 1，预约 b 之后变成 1
```

#### 15. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L193-L198
- 上下文：赋值语句

功能描述：

该代码块属于触发器/时序寄存器。它来自“赋值语句”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
always @(posedge clk) begin    
	a = b;    
	b = a;
end
```

#### 16. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L202-L204
- 上下文：赋值语句

功能描述：

该代码块属于赋值语句。它来自“赋值语句”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
a = 1;b = 0;
```

#### 17. 赋值语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L208-L211
- 上下文：赋值语句

功能描述：

该代码块属于赋值语句。它来自“赋值语句”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
a = b;   // a 立刻变成 0
b = a;   // 此时读到的 a 已经是 0，所以 b 也变成 0
```

#### 18. Vrprimei

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L238-L260
- 上下文：if-else
- 模块名：`Vrprimei`

功能描述：

`Vrprimei` 属于if-else。它来自“if-else”这一小节。主要接口/信号包括：N, F。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

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

#### 19. comp

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L286-L300
- 上下文：循环语句
- 模块名：`comp`

功能描述：

`comp` 属于比较器。它来自“循环语句”这一小节。主要接口/信号包括：X, Y, gt。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

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

#### 20. 循环语句

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L306-L321
- 上下文：循环语句

功能描述：

该代码块属于循环语句。它来自“循环语句”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

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

#### 21. prime_tb1

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/Verilog模型以及测试平台|Verilog模型以及测试平台]]，代码块位置 L339-L353
- 上下文：测试平台(testbench)
- 模块名：`prime_tb1`

功能描述：

`prime_tb1` 属于测试平台/激励代码。它来自“测试平台(testbench)”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

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

### 来源：[[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]

#### 22. mux2_1

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]，代码块位置 L5-L15
- 上下文：用结构化模型来描述该电路
- 模块名：`mux2_1`

功能描述：

`mux2_1` 属于多路选择器。它来自“用结构化模型来描述该电路”这一小节。主要接口/信号包括：a, sel, b, out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module mux2_1(a,sel,b,out);
	input a,sel,b;
	output out;
	wire sel_n,sela,selb;
	not U1(sel_n,sel);
	and U2(sela,a,sel_n);
	and U3(selb,b,sel);
	or U4(out,sela,selb);
endmodule
```

#### 23. mux2_1

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]，代码块位置 L19-L27
- 上下文：用数据流模型来描述
- 模块名：`mux2_1`

功能描述：

`mux2_1` 属于多路选择器。它来自“用数据流模型来描述”这一小节。主要接口/信号包括：a, sel, b, out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module mux2_1(a,sel,b,out);
	input a,sel,b;
	output out;
	wire out;
	
	assign out = (a&(~sel))|(b&sel);
endmodule
```

#### 24. mux2_1

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]，代码块位置 L31-L44
- 上下文：用行为化模型
- 模块名：`mux2_1`

功能描述：

`mux2_1` 属于多路选择器。它来自“用行为化模型”这一小节。主要接口/信号包括：a, sel, b, out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module mux2_1(a,sel,b,out);
	input a,sel,b;
	output out;
	reg out;
	
	always @(*) begin
		if(!sel)
			out=a;
		else
			out=b;
	end
endmodule
```

#### 25. mux_tb

- 分类：Verilog基础
- 来源：[[CH5 Verilog硬件描述语言/MUX2_1-结构-数据-行为-tb|MUX2_1-结构-数据-行为-tb]]，代码块位置 L54-L69
- 上下文：testbench
- 模块名：`mux_tb`

功能描述：

`mux_tb` 属于测试平台/激励代码。它来自“testbench”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。
- 包含仿真系统任务，用于输出、监视或结束仿真。

源代码：

```verilog
module mux_tb();
	reg a,b,s;
	//模块外部实例化的时候，输入为reg，输出为wire
	wire o;
	mux2_1(.a(a),.b(b),.sel(s),.out(o));
	
	initial begin
		{a,b,s}=3'b010;
		#5 b=0;
		#5 b=1;s=1;
		#5 a=1;
		#5 $finish;//结束仿真
	end
endmodule
```

## 组合逻辑

### 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]

#### 26. decode2_4

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L59-L71
- 上下文：结构化描述
- 模块名：`decode2_4`

功能描述：

`decode2_4` 属于译码器/显示译码。它来自“结构化描述”这一小节。主要接口/信号包括：A0, A1, EN, Y0, Y1, Y2, Y3。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module decode2_4(A0,A1,EN,Y0,Y1,Y2,Y3);
	input A0,A1,EN;
	output Y0,Y1,Y2,Y3;
	wire not_A0,not_A1;
	not u1(not_A0,A0);
	not u2(not_A1,A1);
	and u3(Y0,not_A0,not_A1,EN);
	and u4(Y1,A0,not_A1,EN);
	and u5(Y2,not_A0,A1,EN);
	and u6(Y3,A0,A1,EN);
endmodule
```

#### 27. decode2_4

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L75-L85
- 上下文：数据流描述
- 模块名：`decode2_4`

功能描述：

`decode2_4` 属于译码器/显示译码。它来自“数据流描述”这一小节。主要接口/信号包括：A0, A1, EN, Y0, Y1, Y2, Y3。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module decode2_4(A0,A1,EN,Y0,Y1,Y2,Y3);
	input A0,A1,EN;
	output Y0,Y1,Y2,Y3;
	assign Y0 = EN?({A1,A0}==2'b00):0;
	assign Y1 = EN?({A1,A0}==2'b01):0;
	assign Y2 = EN?({A1,A0}==2'b10):0;
	assign Y3 = EN?({A1,A0}==2'b11):0;
	//这四条连续赋值语句并行执行
endmodule
```

#### 28. decode2_4

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L94-L114
- 上下文：行为化描述
- 模块名：`decode2_4`

功能描述：

`decode2_4` 属于译码器/显示译码。它来自“行为化描述”这一小节。主要接口/信号包括：A0, A1, EN, Y0, Y1, Y2, Y3。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module decode2_4(A0,A1,EN,Y0,Y1,Y2,Y3);
	input A0,A1,EN;
	output reg Y0,Y1,Y2,Y3;//输出端口定义为reg类型
	always @(A0,A1,EN) begin
		if(EN) begin
			case({A1,A0})
				2'b00:{Y3,Y2,Y1,Y0} = 4'b0001;
				2'b01:{Y3,Y2,Y1,Y0} = 4'b0010;
				2'b10:{Y3,Y2,Y1,Y0} = 4'b0100;
				2'b00:{Y3,Y2,Y1,Y0} = 4'b1000;
				default:{Y3,Y2,Y1,Y0} = 4'b0000;
				//不管条件有没有全覆盖，都要加default
			endcase
		end
		else begin
			{Y3,Y2,Y1,Y0} = 4'b0000;
		end
	end
endmodule
```

#### 29. decode2_4

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L118-L134
- 上下文：行为化描述
- 模块名：`decode2_4`

功能描述：

`decode2_4` 属于译码器/显示译码。它来自“行为化描述”这一小节。主要接口/信号包括：A0, A1, EN, Y0, Y1, Y2, Y3。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module decode2_4(A0,A1,EN,Y0,Y1,Y2,Y3);
	input A0,A1,EN;
	output reg Y0,Y1,Y2,Y3;//输出端口定义为reg类型
	reg [3:0] IY;
	integer i;
	always @(A0,A1,EN) begin
		IY = 4'b0000;
		if(EN==1) begin
			for(i=0;i<=3;i=i+1) begin
				if(i=={A1,A0}) IY[i]=1;
			end//循环产生内部变量IY
		end
		{Y3,Y2,Y1,Y0} = IY;//内部变量复制给输出
	end
endmodule
```

#### 30. decode2_4

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L138-L151
- 上下文：行为化描述
- 模块名：`decode2_4`

功能描述：

`decode2_4` 属于译码器/显示译码。它来自“行为化描述”这一小节。主要接口/信号包括：A0, A1, EN, Y0, Y1, Y2, Y3。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module decode2_4(A0,A1,EN,Y0,Y1,Y2,Y3);
	input A0,A1,EN;
	output reg Y0,Y1,Y2,Y3;//输出端口定义为reg类型
	reg [3:0] IY;
	always @(A0,A1,EN) begin
		IY = 4'b0000;
		if(EN==1) begin
			IY[{A1,A0}] = 1;//简单粗暴
		end
		{Y3,Y2,Y1,Y0} = IY;//内部变量复制给输出
	end
endmodule
```

#### 31. testbench的设计

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L163-L166
- 上下文：testbench的设计

功能描述：

该代码块属于测试平台/激励代码。它来自“testbench的设计”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
{ENs,A1s,A0s} = i;
//i是从0到7递增的，在循环过程中遍历所有输入测试组合
```

#### 32. testbench的设计

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L169-L171
- 上下文：testbench的设计

功能描述：

该代码块属于测试平台/激励代码。它来自“testbench的设计”这一小节。

代码要点：

- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
#10
```

#### 33. testbench的设计

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L175-L177
- 上下文：testbench的设计

功能描述：

该代码块属于测试平台/激励代码。它来自“testbench的设计”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
if(ENs==1) expectY[{A1s,A0s}] = 1'b1;
```

#### 34. segdec

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L196-L225
- 上下文：七段译码器的verilog程序
- 模块名：`segdec`

功能描述：

`segdec` 属于译码器/显示译码。它来自“七段译码器的verilog程序”这一小节。主要接口/信号包括：DIG, EN, SEGA, SEGB, SEGC, SEGD, SEGE, SEGF, SEGG。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module segdec( DIG , EN , SEGA , SEGB , SEGC , SEGD , SEGE , SEGF , SEGG );
    input [3:0] DIG ;//4位BCD码数据输入端
    input EN ;
    output reg SEGA , SEGB , SEGC , SEGD , SEGE , SEGF , SEGG ;
    reg [1:7] SEGS ;//串接和辅助变量

    always @(DIG or EN or SEGS) begin
        if (EN)
            case (DIG) //Segment patterns abcdefg
	            //注意是高有效还是低有效的段码
                4'd0: SEGS = 7'b1111110; //0
                4'd1: SEGS = 7'b0110000; //1
                4'd2: SEGS = 7'b1101101; //2
                4'd3: SEGS = 7'b1111001; //3
                4'd4: SEGS = 7'b0110011; //4
                4'd5: SEGS = 7'b1011011; //5
                4'd6: SEGS = 7'b0011111; //6
                4'd7: SEGS = 7'b1111000; //7
                4'd8: SEGS = 7'b1111111; //8
                4'd9: SEGS = 7'b1111011; //9
                default SEGS = 7'bxxxxxxx;
            endcase
        else 
            SEGS = 7'b0000000;

	{ SEGA , SEGB , SEGC , SEGD , SEGE , SEGF , SEGG } = SEGS;
    end
endmodule
```

#### 35. mux2in8

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L275-L283
- 上下文：数据流描述
- 模块名：`mux2in8`

功能描述：

`mux2in8` 属于多路选择器。它来自“数据流描述”这一小节。主要接口/信号包括：EN_L, S, D0, D1, Y。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module mux2in8(EN_L,S,D0,D1,Y);
	input [7:0] D0,D1;
	input  S;
	input EN_L;
	output [7:0] Y;
	assign Y=(~EN_L==1'b0)?8'b0:(S==1'b0?D0:(S==1'b1?D1:8'bx));
endmodule
```

#### 36. mux2in8

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L287-L300
- 上下文：行为级描述
- 模块名：`mux2in8`

功能描述：

`mux2in8` 属于多路选择器。它来自“行为级描述”这一小节。主要接口/信号包括：EN_L, S, D0, D1, Y。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module mux2in8(EN_L,S,D0,D1,Y);
	input [7:0] D0,D1;
	input  S;
	input EN_L;
	output reg [7:0] Y;
	always @(*) begin
		if(~EN_L==1'b0) Y=8'b0;
		else if(S==1'b0) Y=D0;
		else if(S==1'b1) Y=D1;
		else Y=8'bx;
	end
endmodule
```

#### 37. mux4in8

- 分类：组合逻辑
- 来源：[[CH6 基本组合逻辑元件/译码器和多路复用器|译码器和多路复用器]]，代码块位置 L304-L323
- 上下文：行为级描述
- 模块名：`mux4in8`

功能描述：

`mux4in8` 属于多路选择器。它来自“行为级描述”这一小节。主要接口/信号包括：EN_L, S, A, B, C, D, Y。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module mux4in8(EN_L,S,A,B,C,D,Y);
	input EN_L;
	input [1:0] S;
	input [7:0] A,B,C,D;
	output reg [7:0] Y;
	always@(*) begin
		if(~EN_L==1'b0) Y=8'b0;
		else begin
			case(S)
				2'b00:Y=A;
				2'b01:Y=B;
				2'b10:Y=C;
				2'b11:Y=D;
				default:Y=8'bx;
			endcase
		end
	end
endmodule
```

### 来源：[[CH7 更多的组合构件/三态门|三态门]]

#### 38. Vr74x541

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/三态门|三态门]]，代码块位置 L27-L34
- 上下文：74x541verilog实现
- 模块名：`Vr74x541`

功能描述：

`Vr74x541` 属于三态输出/总线接口。它来自“74x541verilog实现”这一小节。主要接口/信号包括：G1_L, G2_L, A, Y。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用高阻态 `z` 描述三态总线或未驱动输出。

源代码：

```verilog
module Vr74x541(G1_L,G2_L,A,Y);
	input G1_L,G2_L;
	input [7:0] A;
	output [7:0] Y;
	assign Y= (~G1_L & ~G2_L)? A :8'bz;
endmodule
```

#### 39. transceiver

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/三态门|三态门]]，代码块位置 L39-L46
- 上下文：8位收发器的verilog代码实现
- 模块名：`transceiver`

功能描述：

`transceiver` 属于三态输出/总线接口。它来自“8位收发器的verilog代码实现”这一小节。主要接口/信号包括：G_L, DIR, A, B。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用高阻态 `z` 描述三态总线或未驱动输出。

源代码：

```verilog
module transceiver(G_L,DIR,A,B);
	input G_L,DIR;
	inout [7:0] A,B;//注意端口的声明
	assign B=(~G_L & DIR)?A:8'bz;
	assign A=(~G_L & ~DIR)?B:8'bz;
endmodule
```

### 来源：[[CH7 更多的组合构件/优先编码器|优先编码器]]

#### 40. priencoder

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/优先编码器|优先编码器]]，代码块位置 L33-L52
- 上下文：用for语句简化if
- 模块名：`priencoder`

功能描述：

`priencoder` 属于用for语句简化if。它来自“用for语句简化if”这一小节。主要接口/信号包括：I, A, IDLE。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module priencoder(I,A,IDLE);
	input [7:0] I;
	output [2:0] A;
	output IDLE;
	integer i;
	
	always@(*) begin
		IDLE=1;A=0
		for(i==0;i<=7;i=i+1) begin
			if(I[i]==1) begin 
			//问题:为什么从I[0]开始if，这样会导致I[0的优先级最高吗]
				IDLE = 0;
				A=i;
			end
		end
	end
	
endmodule
```

#### 41. Vr8inprior4

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/优先编码器|优先编码器]]，代码块位置 L67-L87
- 上下文：行为级case
- 模块名：`Vr8inprior4`

功能描述：

`Vr8inprior4` 属于组合逻辑示例。它来自“行为级case”这一小节。主要接口/信号包括：I, A, IDLE。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。

源代码：

```verilog
module Vr8inprior4(I, A, IDLE);
    input [7:0] I;
    output reg [2:0] A;
    output reg IDLE;
    
    always @(*) begin
        IDLE = 1; A = 0;
        case (1'b1)//注意此处用常量来与输入对应的有效位来做匹配
            I[7]: begin IDLE = 0; A = 7; end
            I[6]: begin IDLE = 0; A = 6; end
            I[5]: begin IDLE = 0; A = 5; end
            I[4]: begin IDLE = 0; A = 4; end
            I[3]: begin IDLE = 0; A = 3; end
            I[2]: begin IDLE = 0; A = 2; end
            I[1]: begin IDLE = 0; A = 1; end
            I[0]: begin IDLE = 0; A = 0; end
        endcase
    end
endmodule
```

#### 42. Vr8inprior4

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/优先编码器|优先编码器]]，代码块位置 L91-L111
- 上下文：行为级case
- 模块名：`Vr8inprior4`

功能描述：

`Vr8inprior4` 属于组合逻辑示例。它来自“行为级case”这一小节。主要接口/信号包括：I, A, IDLE。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module Vr8inprior4(I, A, IDLE);
    input [7:0] I;
    output reg [2:0] A;
    output reg IDLE;
    
    always @(*) begin
        IDLE = 1; A = 0;
        casez (I)
            8'b1???_????: begin IDLE = 0; A = 7; end
            8'b?1??_????: begin IDLE = 0; A = 6; end
            8'b??1?_????: begin IDLE = 0; A = 5; end
            8'b???1_????: begin IDLE = 0; A = 4; end
            8'b????_1???: begin IDLE = 0; A = 3; end
            8'b????_?1??: begin IDLE = 0; A = 2; end
            8'b????_??1?: begin IDLE = 0; A = 1; end
            8'b????_???1: begin IDLE = 0; A = 0; end
        endcase
    end
endmodule
```

### 来源：[[CH7 更多的组合构件/异或门和奇偶校验功能|异或门和奇偶校验功能]]

#### 43. XOR3

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/异或门和奇偶校验功能|异或门和奇偶校验功能]]，代码块位置 L45-L52
- 上下文：三输入异或、数据流描述
- 模块名：`XOR3`

功能描述：

`XOR3` 属于异或/奇偶校验逻辑。它来自“三输入异或、数据流描述”这一小节。主要接口/信号包括：Y, A, B, C。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module XOR3(Y,A,B,C);
	input A,B,C;
	output Y;
	
	assign Y=A^B^C;
endmodule
```

#### 44. parity9

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/异或门和奇偶校验功能|异或门和奇偶校验功能]]，代码块位置 L56-L69
- 上下文：9输入奇校验电路的行为级描述
- 模块名：`parity9`

功能描述：

`parity9` 属于异或/奇偶校验逻辑。它来自“9输入奇校验电路的行为级描述”这一小节。主要接口/信号包括：I, ODD。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module parity9(I,ODD);
	input [8:0] I;
	output I;
	integer j;
	
	always @(*) begin
		ODD=1'b0;//对输出赋初值
		for(j=1;j<=9;j=j+1)
			if(I[j]) ODD=~ODD;
//行为级所描述的行为是遇到一个1，ODD的值就翻转，很像1bit二进制加法的行为，在加了偶数个1的时候输出为0，奇数个1的时候输出为1
	end
endmodule
```

#### 45. parity9

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/异或门和奇偶校验功能|异或门和奇偶校验功能]]，代码块位置 L75-L87
- 上下文：结构级描述(Structral)
- 模块名：`parity9`

功能描述：

`parity9` 属于异或/奇偶校验逻辑。它来自“结构级描述(Structral)”这一小节。主要接口/信号包括：I, ODD。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module parity9(I,ODD);
	input [8:0] I;
	output ODD;
	wire Y1,Y2,Y3;
	
	XOR3 U1(.Y(Y1),.A(I[0]),.B(I[1]),.C(I[2]));
	XOR3 U2(.Y(Y2),.A(I[3]),.B(I[4]),.C(I[5]));
	XOR3 U3(.Y(Y3),.A(I[6]),.B(I[7]),.C(I[8]));
	XOR3 U4(.Y(ODD),.A(Y3),.B(Y2),.C(Y1));
	
endmodule
```

### 来源：[[CH7 更多的组合构件/比较器|比较器]]

#### 46. Vr8bitcom

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/比较器|比较器]]，代码块位置 L85-L101
- 上下文：8位数值比较器的verilog(if-else)
- 模块名：`Vr8bitcom`

功能描述：

`Vr8bitcom` 属于比较器。它来自“8位数值比较器的verilog(if-else)”这一小节。主要接口/信号包括：P, Q, PEQQ, PGTQ, PLTQ。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Vr8bitcom(P,Q,PEQQ,PGTQ,PLTQ);
	input [7:0] P,Q;
	output reg PEQQ,PGTQ,PLTQ;
	always @(*) begin
		if(P==Q) 
			begin PEQQ=1'b1; PGTQ=1'b0; PLTQ=1'b0; end
		else if(P>Q)
			begin PEQQ=1'b0; PGTQ=1'b1; PLTQ=1'b0; end
		else if(P<Q)
			begin PEQQ=1'b0; PGTQ=1'b0; PLTQ=1'b1; end
		else
			begin PEQQ=1'bx; PGTQ=1'bx; PLTQ=1'bx; end
			//一定要写else，不然会推理出锁存器
	end
endmodule
```

#### 47. Vr8bitcom

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/比较器|比较器]]，代码块位置 L105-L118
- 上下文：8位数值比较器的verilog(if-else)
- 模块名：`Vr8bitcom`

功能描述：

`Vr8bitcom` 属于比较器。它来自“8位数值比较器的verilog(if-else)”这一小节。主要接口/信号包括：P, Q, PEQQ, PGTQ, PLTQ。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Vr8bitcom(P,Q,PEQQ,PGTQ,PLTQ);
	input [7:0] P,Q;
	output reg PEQQ,PGTQ,PLTQ;
	always @(*) begin
		if(P==Q) 
			begin PEQQ=1'b1; PGTQ=1'b0; PLTQ=1'b0; end
		else if(P>Q)
			begin PEQQ=1'b0; PGTQ=1'b1; PLTQ=1'b0; end
		else
			begin PEQQ=1'b0; PGTQ=1'b0; PLTQ=1'b1; end
	end
endmodule
```

#### 48. Vr8bitcom

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/比较器|比较器]]，代码块位置 L122-L132
- 上下文：8位comparator(数据流描述)
- 模块名：`Vr8bitcom`

功能描述：

`Vr8bitcom` 属于比较器。它来自“8位comparator(数据流描述)”这一小节。主要接口/信号包括：P, Q, PEQQ, PGTQ, PLTQ。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module Vr8bitcom(P,Q,PEQQ,PGTQ,PLTQ);
	input [7:0] P,Q;
	output PEQQ,PGTQ,PLTQ;
	
	assign PGTQ = (P>Q)?1'b1:1'b0;
	assign PEQQ = (P==Q)?1'b1:1'b0;
	assign PEQQ = (P<Q)?1'b1:1'b0;//这里会多综合出一个比较器
	
endmodule
```

#### 49. Vr8bitcom

- 分类：组合逻辑
- 来源：[[CH7 更多的组合构件/比较器|比较器]]，代码块位置 L136-L145
- 上下文：8位comparator(数据流描述)
- 模块名：`Vr8bitcom`

功能描述：

`Vr8bitcom` 属于比较器。它来自“8位comparator(数据流描述)”这一小节。主要接口/信号包括：P, Q, PEQQ, PGTQ, PLTQ。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module Vr8bitcom(P,Q,PEQQ,PGTQ,PLTQ);
	input [7:0] P,Q;
	output PEQQ,PGTQ,PLTQ;
	
	assign PGTQ = (P>Q)?1'b1:1'b0;
	assign PEQQ = (P==Q)?1'b1:1'b0;
	assign PEQQ = ~PGTQ & ~PEQQ;//这里会多综合出一个比较器
endmodule
```

### 来源：[[CH8 组合算数元件/乘法器|乘法器]]

#### 50. mul

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/乘法器|乘法器]]，代码块位置 L5-L11
- 上下文：8x8组合乘法器
- 模块名：`mul`

功能描述：

`mul` 属于乘法器。它来自“8x8组合乘法器”这一小节。主要接口/信号包括：X, Y, P。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module mul(X,Y,P);
	input [7:0] X,Y;
	output [15:0] P;//注意P的位宽是怎么定义的
	assign P=X*Y;
endmodule
```

### 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]

#### 51. 半加器

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L6-L9
- 上下文：半加器

功能描述：

该代码块属于半加器。它来自“半加器”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
A+B={CO,HS};
//HS为半加和，CO为半加进位或半加输出
```

#### 52. 半加器

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L14-L16
- 上下文：半加器

功能描述：

该代码块属于半加器。它来自“半加器”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
A+B={COUT,S};
```

#### 53. 减法器

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L39-L45
- 上下文：减法器

功能描述：

该代码块属于加减法算术逻辑。它来自“减法器”这一小节。

代码要点：

- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
assign {BOUT, D} = {1'b0, A} - {1'b0, B} - {1'b0, BIN};

//这里的 {BOUT, D} 不是普通意义上的二进制数值结果，而是
//高位 BOUT：是否借位  
//低位 D：本位差
```

#### 54. VrAdder

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L111-L121
- 上下文：参数化设计，数据流描述
- 模块名：`VrAdder`

功能描述：

`VrAdder` 属于加减法算术逻辑。它来自“参数化设计，数据流描述”这一小节。主要接口/信号包括：A, B, CIN, S, COUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module VrAdder(A,B,CIN,S,COUT);
	parameter N=16;//加数与和的宽度
	input [N-1:0] A,B;
	input CIN;
	output [N-1:0] S;
	output COUT;
	
	assign {COUT,S}=A+B+CIN;
endmodule
```

#### 55. Vradders

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L128-L140
- 上下文：有符号和无符号加法的verilog模块
- 模块名：`Vradders`

功能描述：

`Vradders` 属于加减法算术逻辑。它来自“有符号和无符号加法的verilog模块”这一小节。主要接口/信号包括：A, B, C, D, S, T, OVFL, COUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module Vradders(A,B,C,D,S,T,OVFL,COUT);
	parameter N=16;
	input [N-1;0] A,B,C,D;
	output [N-1] S,T;
	output OVFL,COUT;
	//有符号加法，S和OVFL(overflow)
	assign S = A+B;
	
	//无符号加法，T和进位COUT
	assign {COUT,S}=C+D;
endmodule
```

#### 56. VrSelAdder

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L144-L155
- 上下文：复用的加法器模块
- 模块名：`VrSelAdder`

功能描述：

`VrSelAdder` 属于加减法算术逻辑。它来自“复用的加法器模块”这一小节。主要接口/信号包括：SEL, A, B, C, D, S。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrSelAdder(SEL,A,B,C,D,S);
	input SEL;
	input [7:0] A,B,C,D;
	output reg [7:0] S;//要用过程块，声明为reg
	
	always@(*) begin
		if(SEL) S=A+B;
		else S=C+D;
	end
endmodule
```

#### 57. VrSelAdder

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/加法器和减法器|加法器和减法器]]，代码块位置 L163-L171
- 上下文：数据流描述的复用加法器模块
- 模块名：`VrSelAdder`

功能描述：

`VrSelAdder` 属于加减法算术逻辑。它来自“数据流描述的复用加法器模块”这一小节。主要接口/信号包括：SEL, A, B, C, D, S。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。

源代码：

```verilog
module VrSelAdder(SEL,A,B,C,D,S);
	input SEL;
	input [7:0] A,B,C,D;
	output [7:0] S;//要用过程块，声明为reg
	
	assign SEL?(A+B):(C+D);
endmodule
```

### 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]

#### 58. 用算数右移与符号位拓展

- 分类：组合逻辑
- 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]，代码块位置 L110-L121
- 上下文：用算数右移与符号位拓展

功能描述：

该代码块属于用算数右移与符号位拓展。它来自“用算数右移与符号位拓展”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
// 8位有符号数 a = 8'b1101_0010 （负数，-46）
// 要把它拓展为16位，符号位必须延续

// 逻辑右移（错误！）——高位补0，负数变正数
wire [15:0] logical = {8'b0, a};        
// 16'b0000_0000_1101_0010 → 正数，错了

// 算数右移（正确！）——高位补符号位1
wire [15:0] arithmetic = {{8{a[7]}}, a}; //使用了复制操作
// 16'b1111_1111_1101_0010 → 仍然是负数
```

### 来源：[[CH9 状态机设计/关于无效状态的处理|关于无效状态的处理]]

#### 59. 最小风险法（Minimum Risk Method）

- 分类：组合逻辑
- 来源：[[CH9 状态机设计/关于无效状态的处理|关于无效状态的处理]]，代码块位置 L43-L47
- 上下文：最小风险法（Minimum Risk Method）

功能描述：

该代码块属于最小风险法（Minimum Risk Method）。它来自“最小风险法（Minimum Risk Method）”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
无效状态 101: AB=00→INIT, AB=01→INIT, AB=11→INIT, AB=10→INIT, Z=0
无效状态 110: AB=00→INIT, AB=01→INIT, AB=11→INIT, AB=10→INIT, Z=0
无效状态 111: AB=00→INIT, AB=01→INIT, AB=11→INIT, AB=10→INIT, Z=0
```

#### 60. 最小成本法（Minimum Cost Method）

- 分类：组合逻辑
- 来源：[[CH9 状态机设计/关于无效状态的处理|关于无效状态的处理]]，代码块位置 L65-L69
- 上下文：最小成本法（Minimum Cost Method）

功能描述：

该代码块属于最小成本法（Minimum Cost Method）。它来自“最小成本法（Minimum Cost Method）”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
无效状态 101: AB=00→×××, AB=01→×××, AB=11→×××, AB=10→×××, Z=×
无效状态 110: AB=00→×××, AB=01→×××, AB=11→×××, AB=10→×××, Z=×
无效状态 111: AB=00→×××, AB=01→×××, AB=11→×××, AB=10→×××, Z=×
```

### 来源：[[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]

#### 61. 次态与输出逻辑合并

- 分类：组合逻辑
- 来源：[[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]，代码块位置 L85-L110
- 上下文：次态与输出逻辑合并

功能描述：

该代码块属于组合逻辑示例。它来自“次态与输出逻辑合并”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。

源代码：

```verilog
// 😞 分开写（两段）
always @(*) begin
    case (Sreg)
        INIT: Snext = (A==0) ? A0 : A1;
        A0:   Snext = OK0;
        OK0:  Snext = OK0;
    endcase
end

always @(*) begin
    case (Sreg)
        INIT, A0, A1: Z = 0;
        OK0:          Z = 1;
    endcase
end

// ✅ 合并写（一段）—— 输出只和状态有关，且 case 分支一致
always @(*) begin
    case (Sreg)
        INIT: begin Snext = (A==0) ? A0 : A1; Z = 0; end
        A0:   begin Snext = OK0;              Z = 0; end
        OK0:  begin Snext = OK0;              Z = 1; end
    endcase
end
```

### 来源：[[Exam_topic]]

#### 62. XOR

- 分类：组合逻辑
- 来源：[[Exam_topic]]，代码块位置 L25-L41
- 模块名：`XOR`

功能描述：

`XOR` 属于异或/奇偶校验逻辑。主要接口/信号包括：A, B, C。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module XOR(A,B,C);
	input A,B;
	output C;
	assign C = A^B;
endmodule
//一般两问之间是有联系的
module odd_parity(A,F);//奇校验
	input [3:0] A;
	output F;
	wire A_1,A_2;
	XOR xor1(.A(A[0]),.B(A[1]),.C(A_1));
	XOR xor2(.A(A[2]),.B(A[3]),.C(A_2));
	XOR xor3(.A(A_1),.B(A_2),.C(F));
endmodule
//结构型描述、数据流描述(assign)、行为级描述(always)
```

#### 63. Vr7segdec

- 分类：组合逻辑
- 来源：[[Exam_topic]]，代码块位置 L45-L68
- 模块名：`Vr7segdec`

功能描述：

`Vr7segdec` 属于译码器/显示译码。主要接口/信号包括：Dig, a, b, c, d, e, f, g。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。

源代码：

```verilog
module Vr7segdec(Dig,a,b,c,d,e,f,g);
	input  [3:0] Dig;
	output reg   a,b,c,d,e,f,g;   // 注意低电平有效

	always @(*) begin
		case (Dig)
				//                        a b c d e f g
			4'd0:    {a,b,c,d,e,f,g} = 7'b0_0_0_0_0_0_1;
			4'd1:    {a,b,c,d,e,f,g} = 7'b1_0_0_1_1_1_1;
			4'd2:    {a,b,c,d,e,f,g} = 7'b0_0_1_0_0_1_0;
			4'd3:    {a,b,c,d,e,f,g} = 7'b0_0_0_0_1_1_0;
			4'd4:    {a,b,c,d,e,f,g} = 7'b1_0_0_1_1_0_0;
			4'd5:    {a,b,c,d,e,f,g} = 7'b0_1_0_0_1_0_0;
			4'd6:    {a,b,c,d,e,f,g} = 7'b0_1_0_0_0_0_0;
			4'd7:    {a,b,c,d,e,f,g} = 7'b0_0_0_1_1_1_1;
			4'd8:    {a,b,c,d,e,f,g} = 7'b0_0_0_0_0_0_0;
			4'd9:    {a,b,c,d,e,f,g} = 7'b0_0_0_0_1_0_0;
			default: {a,b,c,d,e,f,g} = 7'b1_1_1_1_1_1_1; 
			// 非法 BCD 全灭
		endcase
	end
endmodule
```

#### 64. Adder10

- 分类：组合逻辑
- 来源：[[Exam_topic]]，代码块位置 L72-L81
- 模块名：`Adder10`

功能描述：

`Adder10` 属于加减法算术逻辑。主要接口/信号包括：A, B, C, S。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
// 10 位加法器：A + B = {C, S}
module Adder10(A, B, C, S);
	input  [9:0] A, B;
	output       C;     // 进位输出
	output [9:0] S;     // 和

	assign {C, S} = A + B;   // 11 位结果，高位即进位
endmodule
```

### 来源：[[某个老师的测试题]]

#### 65. Xnor

- 分类：组合逻辑
- 来源：[[某个老师的测试题]]，代码块位置 L4-L10
- 上下文：II. 用 Verilog HDL 实现以下功能描述（10 分）
- 模块名：`Xnor`

功能描述：

`Xnor` 属于组合逻辑示例。它来自“II. 用 Verilog HDL 实现以下功能描述（10 分）”这一小节。主要接口/信号包括：A, B, C。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
module Xnor(A,B,C);//注意模块命名，不能写成xnor
	input A,B;
	output C;
	assign C=A^B;
endmodule
```

#### 66. parity

- 分类：组合逻辑
- 来源：[[某个老师的测试题]]，代码块位置 L14-L23
- 上下文：II. 用 Verilog HDL 实现以下功能描述（10 分）
- 模块名：`parity`

功能描述：

`parity` 属于异或/奇偶校验逻辑。它来自“II. 用 Verilog HDL 实现以下功能描述（10 分）”这一小节。主要接口/信号包括：A, E。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module parity(A,E);
	input [3:0] A;
	output E;
	wire A1,A2;
	Xnor U1(.A(A[3]),.B(A[2]),.C(A1));
	Xnor U2(.A(A[1]),.B(A[0]),.C(A2));
	Xnor U3(.A(A[1]),.B(A[0]),.C(E));
endmodule
```

## 时序逻辑

### 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]

#### 67. 循环左移桶形移位器-行为级描述

- 分类：时序逻辑
- 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]，代码块位置 L25-L33
- 上下文：循环左移桶形移位器-行为级描述

功能描述：

该代码块属于移位寄存器/移位逻辑。它来自“循环左移桶形移位器-行为级描述”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
//把移位过程分成四部份，分别对应移动了1、2、4、8位
//S[i]每一位代表的移位量不同

if (S[0]) X = 左移1位; else X = DIN;
if (S[1]) Y = X左移2位; else Y = X;
if (S[2]) Z = Y左移4位; else Z = Y;
if (S[3]) DOUT = Z左移8位; else DOUT = Z;
```

#### 68. Vrrol16

- 分类：时序逻辑
- 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]，代码块位置 L35-L53
- 上下文：循环左移桶形移位器-行为级描述
- 模块名：`Vrrol16`

功能描述：

`Vrrol16` 属于移位寄存器/移位逻辑。它来自“循环左移桶形移位器-行为级描述”这一小节。主要接口/信号包括：DIN, S, DOUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Vrrol16(DIN,S,DOUT);
	input [15:0] DIN;
	input [3:0] S;//左移的位数
	output [15:0] DOUT;
	reg [15:0] DOUT,X,Y,Z;
	
	always@(DIN or S) begin
		if(S[0]==1'b1) X={DIN[14:0],DIN[15]};//左移1位
		else X=DIN;
		if(S[1]==1'b1) Y={X[13:0],X[15:14]};//左移2位
		else Y=X;
		if(S[2]==1'b1) Z={Y[11:0],Y[15:12]};//左移4位
		else Z=Y;
		if(S[3]==1'b1) DOUT={Z[7:0],Z[15:8]};//左移8位
		else DOUT=Z;
	end
endmodule
```

#### 69. Vrrol16

- 分类：时序逻辑
- 来源：[[CH8 组合算数元件/移位和旋转|移位和旋转]]，代码块位置 L57-L100
- 上下文：左右循环移位的16位桶状移位器-行为级case
- 模块名：`Vrrol16`

功能描述：

`Vrrol16` 属于移位寄存器/移位逻辑。它来自“左右循环移位的16位桶状移位器-行为级case”这一小节。主要接口/信号包括：DIN, S, DIR, DOUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。

源代码：

```verilog
module Vrrol16(DIN,S,DIR,DOUT);
	input [15:0] DIN;
	input [3:0] S;//移位位数0-15
	input DIR;//DIR为0时左移，为1时右移
	output [15:0] DOUT;
	reg [15:0] DOUT,X,Y,Z

	//两个控制信号，可以在上一个移位器的基础上做更改
	//用DIR分别和S的4位做编码，然后用多个case语句
	
	always@(*) begin
		//移动1位
		case({S[0],DIR})
			2'b00,2'b01:X=DIN;
			2'b10:X={DIN[14:0],DIN[15]};
			2'b11:X={DIN[0],DIN[15:1]};
			default:X=16'bx;
		endcase
		//移动2位
		case({S[1],DIR})
			2'b00,2'b01:Y=X;
			2'b10:Y={X[13:0],X[15:14]};
			2'b11:Y={X[1:0],X[15:2]};
			default:Y=16'bx;
		endcase
		//移动4位
		case({S[2],DIR})
			2'b00,2'b01:Z=Y;
			2'b10:Z={Y[11:0],Y[15:12]};
			2'b11:Z={Y[3:0],Y[15:4]};
			default:Z=16'bx;
		endcase
		//移动8位
		case({S[3],DIR})
			2'b00,2'b01:DOUT=Z;
			2'b10:DOUT={Z[7:0],Z[15:8]};
			2'b11:DOUT={Z[7:0],Z[15:8]};
			//这个左移右移的结果都是一样的
			default:DOUT=16'bx;
		endcase
	end
endmodule
```

### 来源：[[CH9 状态机设计/用verilog设计状态机|用verilog设计状态机]]

#### 70. VrSmax

- 分类：时序逻辑
- 来源：[[CH9 状态机设计/用verilog设计状态机|用verilog设计状态机]]，代码块位置 L21-L68
- 上下文：用verilog描述状态机的5个步骤
- 模块名：`VrSmax`

功能描述：

`VrSmax` 属于有限状态机设计。它来自“用verilog描述状态机的5个步骤”这一小节。主要接口/信号包括：clk, A, B, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrSmax(clk,A,B,Z);
	input clk,A,B;
	output reg Z;
	reg [2:0] Sreg,Snext;//状态寄存器和次态
	
	parameter [2:0] INIT=3'b000;
	parameter [2:0] A0=3'b001;
	parameter [2:0] A1=3'b010;
	parameter [2:0] OK0=3'b011;
	parameter [2:0] OK1=3'b100;
	
	always@(posedge clk) begin
		Sreg<=Snext;//建立触发器作为状态存储器
	end
	
	always @(*) begin//次态逻辑
		case(Sreg)
			INIT:
				if(A==0) Snext=A0;
				else Snext=A1;
			A0:
				if(A==0) Snext=OK0;
				else Snext=A1;
			A1:
				if(A==0) Snext=A0;
				else Snext=OK1;
			OK0:
				if(A==0) Snext=OK0;
				else if((A==1)&&(B==0) Snext=A1;
				else Snext=OK1;
			OK1:
				if(A==1) Snext=OK1;
				else if((A==0)&&(B==0) Snext=A0;
				else Snext=OK0;
			default:Snext=INIT;//最小风险设计，回到INIT
		endcase
	end
	
	always@(Sreg)//输出逻辑
		case(Sreg)
			INIT,A0,A1:Z=0;
			OK0,OK1:   Z=1;
			default:   Z=0;
		endcase
	endcase
endmodule
```

### 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]

#### 71. 请注意非阻塞赋值

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L10-L22
- 上下文：请注意非阻塞赋值

功能描述：

该代码块属于触发器/时序寄存器。它来自“请注意非阻塞赋值”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
// ❌ 交换失败
always @(posedge clk) begin
    a = b;   // a 立刻变成 b 的值
    b = a;   // b 变成 a 的新值（= b），a 和 b 最终相同
end
// ✅ 正确交换
always @(posedge clk) begin
    a <= b;   // 采样：a 记下 b 的当前值
    b <= a;   // 采样：b 记下 a 的当前值
    // 同时生效 → a、b 完成交换
end
```

#### 72. VeDlatch

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L32-L43
- 上下文：D锁存器的行为化模型
- 模块名：`VeDlatch`

功能描述：

`VeDlatch` 属于锁存器/电平敏感存储。它来自“D锁存器的行为化模型”这一小节。主要接口/信号包括：D, G, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VeDlatch(D,G,Q);
	input D,G;
	output reg Q;
	
	always @(D or G) begin //D和G的变化都会影响锁存器的输出
		if(G==1) Q<=D; //注意非阻塞赋值
	//此处没写else，会推理出一个Q<=Q的锁存器
	//但是此时我们就是需要设计一个锁存器，所以可要可不要
	end
endmodule
```

#### 73. DlatchCE

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L49-L58
- 上下文：带异步清零和门使能的D锁存器模型
- 模块名：`DlatchCE`

功能描述：

`DlatchCE` 属于锁存器/电平敏感存储。它来自“带异步清零和门使能的D锁存器模型”这一小节。主要接口/信号包括：D, G, GE, CLR, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module DlatchCE(D,G,GE,CLR,Q);
	input D,G,GE,CLR;
	output reg Q;
	always@(D,G,GE,CLR) begin
		if(CLR==1'b1) Q<=1'b0;
		else if((G==1)&&(GE==1)) Q<=D;
	end
endmodule
```

#### 74. NtoSLatch

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L62-L79
- 上下文：带锁存输出的n-s位译码器
- 模块名：`NtoSLatch`

功能描述：

`NtoSLatch` 属于锁存器/电平敏感存储。它来自“带锁存输出的n-s位译码器”这一小节。主要接口/信号包括：G, CLR, A, Y。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module NtoSLatch(G,CLR,A,Y);
parameter N=3,S=8;
	input [N-1:0] A;
	input G,CLR;
	output reg [S-1:0] Y;
	integer i;
	
	always@(*) begin
		if(CLR) Y <= 0;
		else if(G) begin
			Y <= 0;
			for (i=0;i<=S-1;i=i+1)
				if(i==A) Y[i] <= 1;
		end
	end
endmodule
```

#### 75. DFF

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L86-L94
- 上下文：D触发器的行为化模型
- 模块名：`DFF`

功能描述：

`DFF` 属于触发器/时序寄存器。它来自“D触发器的行为化模型”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。

源代码：

```verilog
module DFF(CLK, D, Q)
	input CLK,D;
	output Q;
	
	always@(posedge CLK)
		Q<=D;
endmodule
```

#### 76. VrDFFCLR

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L97-L107
- 上下文：带异步清零端的D触发器
- 模块名：`VrDFFCLR`

功能描述：

`VrDFFCLR` 属于触发器/时序寄存器。它来自“带异步清零端的D触发器”这一小节。主要接口/信号包括：CLK, CLR, D, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrDFFCLR(CLK,CLR,D,Q);
	input CLK,CLR,D;
	output Q;
	always @(posedge CLK or posedge CLR) begin
			//异步清零，清零信号要写在敏感列表里
		if(CLR) Q<=1'b0;
		else Q<=D;
	end
endmodule
```

#### 77. VrDffCNoops

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L111-L122
- 上下文：带有Q_N输出的D触发器的错误模型
- 模块名：`VrDffCNoops`

功能描述：

`VrDffCNoops` 属于触发器/时序寄存器。它来自“带有Q_N输出的D触发器的错误模型”这一小节。主要接口/信号包括：CLK, CLR, D, Q, QN。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrDffCNoops(CLK, CLR, D, Q, QN);
	input CLK, CLR, D;
	output reg Q, QN;

	always @(posedge CLK or posedge CLR) begin
		if (CLR==1) Q <= 0;
		else Q <= D;
		QN <= ~Q;          // ← 错误！
	end
endmodule
```

#### 78. 带有Q_N输出的D触发器的错误模型

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L133-L143
- 上下文：带有Q_N输出的D触发器的错误模型

功能描述：

该代码块属于触发器/时序寄存器。它来自“带有Q_N输出的D触发器的错误模型”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
always @(posedge CLK or posedge CLR) begin
    if (CLR==1) begin
        Q  <= 0;
        QN <= 1;      // ~0 = 1，同步清零
    end else begin
        Q  <= D;
        QN <= ~D;     // ~D 与 Q 同步
    end
end
```

#### 79. VrDffCNoops

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L146-L160
- 上下文：带有Q_N输出的D触发器的错误模型
- 模块名：`VrDffCNoops`

功能描述：

`VrDffCNoops` 属于触发器/时序寄存器。它来自“带有Q_N输出的D触发器的错误模型”这一小节。主要接口/信号包括：CLK, CLR, D, Q, QN。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrDffCNoops(CLK, CLR, D, Q, QN);
	input CLK, CLR, D;
	output reg Q;
	output QN;

	always @(posedge CLK or posedge CLR) begin
		if (CLR==1) Q <= 0;
		else Q <= D;
		QN <= ~Q; 
	end
	assign QN=~Q;
	//直接用数据流写法设计一个组合逻辑电路，使得QN恒为Q的非
endmodule
```

#### 80. VrDFFSE

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L166-L177
- 上下文：带有时钟使能端和同步置位端的D触发器
- 模块名：`VrDFFSE`

功能描述：

`VrDFFSE` 属于触发器/时序寄存器。它来自“带有时钟使能端和同步置位端的D触发器”这一小节。主要接口/信号包括：CLK, S, CE, D, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VrDFFSE(CLK,S,CE,D,Q);
	input CLK,S,CE,D;
	output reg Q;
	
	always @(posedge CLK)//同步置位，所以说敏感信号列表里只有时钟
		if(S==1) Q<=1;
		else if(CE==1) Q<=D;
	//这里没有else，行为就是Q<=Q是一个锁死的触发器,写不写都行
	endmodule
endmodule
```

#### 81. initial —— 执行一次

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L190-L200
- 上下文：initial —— 执行一次

功能描述：

该代码块属于测试平台/激励代码。它来自“initial —— 执行一次”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
// testbench 中初始化输入信号
initial begin
    CLK = 0;
    D = 0;
    CLR = 1;
    #10 CLR = 0;    // 10个时间单位后释放清零
    #5  D = 1;
    #10 D = 0;
end
```

#### 82. always —— 循环执行

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L208-L212
- 上下文：always —— 循环执行

功能描述：

该代码块属于触发器/时序寄存器。它来自“always —— 循环执行”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。

源代码：

```verilog
always @(*)          // 组合逻辑：任何输入变化都触发
always @(posedge CLK)// 时序逻辑：时钟上升沿触发
always @(A or B)     // 组合逻辑：指定信号变化时触发
```

#### 83. CLKGen

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L227-L240
- 上下文：时钟产生器的设计
- 模块名：`CLKGen`

功能描述：

`CLKGen` 属于时钟产生器的设计。它来自“时钟产生器的设计”这一小节。主要接口/信号包括：MCLK。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
`timescale 1ns/100ps
module CLKGen(MCLK);
	output reg MCLK;
	initial begin
		MCLK = 1;
	end

	always begin
		#6 MCLK=0;//过了6s，时钟置0，所以高电平持续6ns
		#4 MCLK=1;//低电平持续4ns
	end
endmodule
```

#### 84. tb_DFF

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L250-L274
- 上下文：内联
- 模块名：`tb_DFF`

功能描述：

`tb_DFF` 属于测试平台/激励代码。它来自“内联”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。
- 包含仿真系统任务，用于输出、监视或结束仿真。

源代码：

```verilog
`timescale 1ns/100ps
module tb_DFF;
    reg CLK, CLR, D;
    wire Q;

    VrDFFCLR uut(CLK, CLR, D, Q);    // 例化待测模块

    // 时钟生成 —— 直接内联
    initial CLK = 1;
    always begin
        #6 CLK = 0;
        #4 CLK = 1;       // 周期 10ns
    end

    // 测试激励
    initial begin
        CLR = 1;  D = 0;
        #15 CLR = 0;       // 释放清零
        #10 D = 1;
        #10 D = 0;
        #20 $finish;
    end
endmodule
```

#### 85. tb_DFF

- 分类：时序逻辑
- 来源：[[CH10 时序逻辑元件/用verilog实现锁存器和触发器|用verilog实现锁存器和触发器]]，代码块位置 L280-L290
- 上下文：模块例化
- 模块名：`tb_DFF`

功能描述：

`tb_DFF` 属于测试平台/激励代码。它来自“模块例化”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
`timescale 1ns/100ps
module tb_DFF;
    reg CLR, D;
    wire CLK, Q;

    VrDFFCLR uut(CLK, CLR, D, Q);
    CLKGen clk_gen(CLK);    // 例化时钟模块
    ...
endmodule
```

### 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]

#### 86. shift_reg_siso

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L9-L30
- 上下文：串入串出(SISO)的verilog实现
- 模块名：`shift_reg_siso`

功能描述：

`shift_reg_siso` 属于移位寄存器/移位逻辑。它来自“串入串出(SISO)的verilog实现”这一小节。主要接口/信号包括：SERIN, CLOCK, SEROUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
module shift_reg_siso #(
    parameter N = 8  // 移位寄存器位数
)(
    input  wire SERIN,   // 串行输入
    input  wire CLOCK,   // 时钟
    output wire SEROUT   // 串行输出
);

    reg [N-1:0] shift_reg;

    // 每个时钟沿，数据向右移一位，SERIN进入最高位
    always @(posedge CLOCK) begin
        shift_reg <= {SERIN, shift_reg[N-1:1]};
    end

    // SEROUT 为最低位
    assign SEROUT = shift_reg[0];

endmodule
```

#### 87. SIPO

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L45-L57
- 上下文：串入并出移位寄存器的verilog模块
- 模块名：`SIPO`

功能描述：

`SIPO` 属于移位寄存器/移位逻辑。它来自“串入并出移位寄存器的verilog模块”这一小节。主要接口/信号包括：CLK, CLR, SERIN, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module SIPO(CLK,CLR,SERIN,Q);
	input CLK,CLR,SERIN;
	parameter WID=8;//参数化设计
	output reg [WID-1:0] Q;
	always@(*) begin
		if(CLR)
			Q<=0；
		else
			Q<={Q[WID-2:0]，SERIN};
	end
endmodule
```

#### 88. PISO

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L60-L80
- 上下文：并入串出寄存器(PISO)
- 模块名：`PISO`

功能描述：

`PISO` 属于移位寄存器/移位逻辑。它来自“并入串出寄存器(PISO)”这一小节。主要接口/信号包括：CLK, CLR, LOAD, SHIFT, PARIN, SEROUT。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module PISO(CLK,CLR,LOAD,SHIFT,PARIN,SEROUT);
	parameter WID=8;
	input CLK,CLR,SHIFT,LOAD;//时钟和控制信号
	input [WID-1:0] PARIN;
	output SEROUT;
	reg [WID-1:0] Q;
	
	always@(posedge CLK) begin
		if(CLR==1)
			Q<=0;//同步清零
		else if(LOAD==1)
			Q<=PARIN;
		else if(SHIFT==1)//右移
			Q<={1'b0,Q[WID-1:1]};
		else
			Q<=Q;
	end
	assign SEROUT=Q[0];
endmodule
```

#### 89. PIPO

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L87-L104
- 上下文：并入并出寄存器(PIPO)
- 模块名：`PIPO`

功能描述：

`PIPO` 属于移位寄存器/移位逻辑。它来自“并入并出寄存器(PIPO)”这一小节。主要接口/信号包括：CLK, CLR, LOAD, SHIFT, PARIN, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog

module PIPO (CLK, CLR, LOAD, SHIFT, PARIN, Q);
    input CLK, CLR, LOAD, SHIFT;
    input [WID-1:0] PARIN;
    output reg [WID-1:0] Q;
    parameter WID = 8;
    always @(posedge CLK) begin
        if (CLR == 1) 
	        Q <= 0; // 同步清零
        else if (LOAD) 
	        Q <= PARIN;
		else if (SHIFT)  
			  Q <= {Q[WID-2:0], 0}; // 移位
		else   Q<=Q;
   end
endmodule
```

#### 90. Vrshrgu4

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L116-L136
- 上下文：通用4位移位寄存器verilog模块
- 模块名：`Vrshrgu4`

功能描述：

`Vrshrgu4` 属于移位寄存器/移位逻辑。它来自“通用4位移位寄存器verilog模块”这一小节。主要接口/信号包括：CLK, CLR, RIN, LIN, S0, S1, A, B, C, D...。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Vrshrgu4(CLK, CLR, RIN, LIN, S0, S1, A, B, C, D, QA, QB, QC, QD);
    input CLK, CLR, RIN, LIN, S0, S1, A, B, C, D;
    output reg QA, QB, QC, QD;
    always @(posedge CLK) begin
        if (CLR == 1'b1)
            {QA, QB, QC, QD} <= 4'b0;
        else case ({S1, S0})
            2'b00 : {QA, QB, QC, QD} <= {QA, QB, QC, QD};    
            // 保持
            2'b01 : {QA, QB, QC, QD} <= {RIN, QA, QB, QC};   
            // 右移
            2'b10 : {QA, QB, QC, QD} <= {QB, QC, QD, LIN};   
            // 左移
            2'b11 : {QA, QB, QC, QD} <= {A, B, C, D};
            // 并行加载
            default: {QA, QB, QC, QD} <= 4'bx;
        endcase
    end
endmodule
```

#### 91. Vrshrg8ext

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L154-L178
- 上下文：扩展后的8位移位寄存器的verilog模块
- 模块名：`Vrshrg8ext`

功能描述：

`Vrshrg8ext` 属于移位寄存器/移位逻辑。它来自“扩展后的8位移位寄存器的verilog模块”这一小节。主要接口/信号包括：CLK, CLR, RIN, LIN, S, D, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Vrshrg8ext(CLK, CLR, RIN, LIN, S, D, Q);
    input CLK, CLR, RIN, LIN;
    input [2:0] S;
    input [7:0] D;
    output reg [7:0] Q;

    always @(posedge CLK)
        if (CLR == 1) Q <= 0;
        else case (S)
            3'd0: Q <= Q;                    // 保持
            3'd1: Q <= D;                    // 并行载入
            3'd2: Q <= {RIN, Q[7:1]};        // 右移
            3'd3: Q <= {Q[6:0], LIN};        // 左移
            3'd4: Q <= {Q[0], Q[7:1]};       // 循环右移
            3'd5: Q <= {Q[6:0], Q[7]};       // 循环左移
            
            3'd6: Q <= {Q[7], Q[7:1]};       
            // 算术右移(符号位保留)
            3'd7: Q <= {Q[6:0], 1'b0};       
            // 算术左移(低位补0)
            default: Q <= 8'bx;
        endcase
endmodule
```

#### 92. 环形计数器

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L190-L197
- 上下文：环形计数器

功能描述：

该代码块属于计数器/计数逻辑。它来自“环形计数器”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
reg [3:0] Q;
Q={QA,QB,QC,QD};//仅做示意
所以QA对应Q[3],QD对应Q[1]

所以左移的时候，是把最高位QA循环移位到最低位，
右移的时候是把最低位QD循环移位到最高位
```

#### 93. Shift

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L231-L245
- 上下文：自校正环形计数器的verilog代码
- 模块名：`Shift`

功能描述：

`Shift` 属于计数器/计数逻辑。它来自“自校正环形计数器的verilog代码”这一小节。主要接口/信号包括：CLK, INIT, CNTEN, S。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Shift(CLK,INIT,CNTEN,S);
	input CLK,INIT,CNTEN;
	output reg [7:0] S;
	
	always@(posedge CLK) begin
		if(INIT==1)
			S<=8'b0000_0001;//同步初始化
		else if(CNTEN)
			S<={S[6:0],&(~S[6:0])};//移位+自同步逻辑
		else 
			S<=S;
	end
endmodule
```

#### 94. 自同步逻辑拆解

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L264-L274
- 上下文：自同步逻辑拆解

功能描述：

该代码块属于触发器/时序寄存器。它来自“自同步逻辑拆解”这一小节。

代码要点：

- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
wire self_sync; // 低7位全零时为1，否则为0
assign  self_sync= &(~S[6:0]);

always @(posedge CLK) begin
    if (INIT)
        S <= 8'b0000_0001;
    else if (CNTEN)
        S <= {S[6:0], self_sync}; // 左移 + 自同步注入
end
```

#### 95. Johnson

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L287-L299
- 上下文：扭环计数器Verilog设计(无自校正)
- 模块名：`Johnson`

功能描述：

`Johnson` 属于计数器/计数逻辑。它来自“扭环计数器Verilog设计(无自校正)”这一小节。主要接口/信号包括：CLK, rst_n, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Johnson(CLK,rst_n,Q);
	parameter N;//参数化设计
	input CLK,rst_n;
	output reg [N-1:0] Q;
	always @(posedge CLK) begin
		if(~rst_n)//低电平有效
			Q<=8'b0;
		else
			Q<={Q[N-2:0],~Q[N-1]};//左移，最低位=~最高位
	end
endmodule
```

#### 96. LFSR

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/移位寄存器|移位寄存器]]，代码块位置 L374-L398
- 上下文：LFSR的Verilog模型
- 模块名：`LFSR`

功能描述：

`LFSR` 属于线性反馈移位寄存器。它来自“LFSR的Verilog模型”这一小节。主要接口/信号包括：CLK, RESET, RUN, Q。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module LFSR(CLK,RESET,RUN,Q);
	parameter N=8;
	parameter FE=8'b0001_1101;//看上面的反馈方程表
	parameter SEED=8'b0000_0001;//定义初始状态值
	input CLK,RESET,RUN;//RUN为移位使能端(右移)
	output reg [N-1:0] Q;
	reg FEED;//反馈值
	integer i;

	always@(posedge CLK) begin
		if(RESET)
			Q<=SEED;
		else if(RUN==1) begin
			FEED=0;//必须初始化！
			for(i=0;i<=N-1;i=i+1)
			//注意是 i=0 赋值，不是 i==0
				FEED=FEED^(FE[i]&Q[i]);
			//阻塞赋值，AND门控替代if判断
			Q<={FEED,Q[N-1:1]};
		end
		//else Q<=Q; 不需要，reg自动保持原值
	end
endmodule
```

### 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]

#### 97. 4位通用二进制计数器CNTR4U

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L39-L70
- 上下文：4位通用二进制计数器CNTR4U

功能描述：

该代码块属于计数器/计数逻辑。它来自“4位通用二进制计数器CNTR4U”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
modeule Vrcntr4u(CLK,CLR,LD,ENP,ENT,D,Q,RCO);
	input CLK,CLR,LD,ENP,ENT;
	input [3:0] D;
	output reg [3:0] Q;
	output reg RCO;
	//创建该计数器的特性
	always @(posedge CLK) begin
		if(CLR == 1) begin
			Q<=4'd0;
		end
		else if(LD==1) begin
			Q<=D;
		end
		else if((ENP==1)&&(ENT==1)) begin
			Q<=Q+1;
		end
		else begin
			Q<=Q;
		end
	end
	//创建组合输出RCO
	always@(Q or ENT) begin
		if((ENT==1)&&(Q==4'd15)) begin
			//ENT使能时才进位
			RCO=1;
		end
		else begin
			RCO=0;
		end
	end
```

#### 98. CountDec

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L126-L143
- 上下文：寄存器型译码器的verilog模型
- 模块名：`CountDec`

功能描述：

`CountDec` 属于计数器/计数逻辑。它来自“寄存器型译码器的verilog模型”这一小节。主要接口/信号包括：CLK, CLR, S_L。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
module CountDec(CLK,CLR,S_L);
	input CLK,CLR;
	output reg [7:0] S_L;
	reg [2:0] Q;
	integer i;

	always@(posedge CLK) begin
		if(CLR) 
			Q<=3'd0;
		else    
			Q<=Q+1;
		S_L<=8'b1111_1111;//译码器的输出低电平有效
		for(i=0;i<=7;i=i+1)
			if(Q==i) S_L[i]<=0;//译码器的行为级描述
	end
endmodule
```

#### 99. 寄存器型译码器的verilog模型

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L152-L157
- 上下文：寄存器型译码器的verilog模型

功能描述：

该代码块属于译码器/显示译码。它来自“寄存器型译码器的verilog模型”这一小节。

代码要点：

- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。
- 使用 `for` 循环生成重复赋值、扫描或批量初始化逻辑。

源代码：

```verilog
for(i=0; i<=7; i=i+1)
	if(Q==i) S_L[i] <= 1'b0;
	else     S_L[i] <= 1'b1; 
	 // 加 else，确保每个时钟沿 S_L 都有完整赋值
```

#### 100. Counter4

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L162-L191
- 上下文：4位递增/递减的计数器
- 模块名：`Counter4`

功能描述：

`Counter4` 属于计数器/计数逻辑。它来自“4位递增/递减的计数器”这一小节。主要接口/信号包括：CLK, CLR, LD, ENP, ENT, UPDN, D, Q, RCO。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module Counter4(CLK,CLR,LD,ENP,ENT,UPDN,D,Q,RCO);
	input CLK,CLR,LD,ENP,ENT,UPDN;
	input [3:0] D;
	output reg [3:0] Q;
	output RCO;
	
	always@(posedge CLK) begin
		if(CLR==1)
			Q<=4'b0;
		else if(LD==1)
			Q<=D;
		else if(ENP&&ENT&&UPDN)
			Q<=Q+1;
		else if(ENP&&ENT&&!UPDN)
			Q<=Q-1;
		else
			Q<=Q;
	end
	
	always@(Q,ENT,UPDN) begin
		if(ENT&&Q=4'd15&&UPDN)
			RCO=1;
		else if(ENT&&Q=4'd0&&!UPDN)
			RCO=1;
		else
			RCO=0;
	end
endmodule
```

#### 101. 时钟生成的注意事项

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L197-L210
- 上下文：时钟生成的注意事项

功能描述：

该代码块属于时钟生成的注意事项。它来自“时钟生成的注意事项”这一小节。

代码要点：

- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
// ❌ 原始写法：CLK 前 5.5ns 为 x（未初始化）
always begin
    #5.5 CLK = 0;
    #4.0 CLK = 1;
    #0.5 ;
end

// ✅ 正确写法：先初始化 CLK，再用 always 翻转
initial CLK = 0;
always begin
    #5.0 CLK = ~CLK;  // 每 5ns 翻转，周期 10ns，占空比 50%
end
```

#### 102. VrcntrTB1

- 分类：时序逻辑
- 来源：[[CH11 计数器和移位寄存器/计数器|计数器]]，代码块位置 L216-L276
- 上下文：完整的 TB 文件
- 模块名：`VrcntrTB1`

功能描述：

`VrcntrTB1` 属于测试平台/激励代码。它来自“完整的 TB 文件”这一小节。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `initial` 产生仿真初值和激励，通常只用于 testbench。
- 包含 `#` 延时控制，用于仿真波形和 testbench 时序。

源代码：

```verilog
`timescale 1ns/100ps

module VrcntrTB1();
    reg CLK, CLR, LD, ENP, ENT, UPDN;
    reg [3:0] D;
    wire [3:0] Q;
    wire RCO;

    // ========== 时钟生成：周期 10ns ==========
    initial CLK = 0;
    always begin
        #5.0 CLK = ~CLK;
    end

    // ========== 被测模块实例化 ==========
    cntr4u U0(
        .CLK(CLK), .CLR(CLR), .LD(LD),
        .ENP(ENP), .ENT(ENT),
        .D(D), .Q(Q), .RCO(RCO)
    );

    
    // ========== 测试激励 ==========
    initial begin
        // 初始化所有输入
        CLR = 0; LD = 0; ENP = 0; ENT = 0;
        D = 0; UPDN = 0;

        #105;                          
        // 等待FPGA全局复位结束

        // ① 清零：确认 CLR 有效
        CLR = 1; D = 4'b1111; #10;
        // 此时 Q 应为 0000（同步清零）

        // ② 置数：载入 1111
        CLR = 0; LD = 1; #10;
        // 此时 Q 应为 1111 = 15

        // ③ 仅 ENP=1，ENT=0：不计数
        LD = 0; ENP = 1; #10;
        // Q 保持 15（ENT 未使能）

        // ④ 开始递增计数（4 个时钟沿）
        ENT = 1; UPDN = 1; #40;
        // Q: 15→0→1→2→3

        // ⑤ 切换为递减计数（6 个时钟沿）
        UPDN = 0; #40;
        // Q: 3→2→1→0→15→14

        // ⑥ 再切换为递增计数（20 个时钟沿）
        UPDN = 1; #200;

        // ⑦ 停止计数
        ENP = 0; #30;
        $stop(1);
    end
endmodule
```

### 来源：[[CH12 Verilog状态机设计/"1"计数器|"1"计数器]]

#### 103. counter_1

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/"1"计数器|"1"计数器]]，代码块位置 L13-L67
- 上下文：三段式编码(不利用加法功能)
- 模块名：`counter_1`

功能描述：

`counter_1` 属于计数器/计数逻辑。它来自“三段式编码(不利用加法功能)”这一小节。主要接口/信号包括：CLK, RST, X, Y, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module counter_1(CLK,RST,X,Y,Z);
	input CLK,RST,X,Y;
	output reg Z;
	reg [1:0] S,Snext;
	parameter [1:0] S0=00,S1=01,S2=10,S3=11;
	
	always@(posedge CLK) begin
		if(RST)
			S<=S0;
		else
			S<=Snext;
	end
	
	always@(S,X,Y) begin
		case(S)
			S0:begin
				if(X&&Y)
					Snext=S2;
				else if(X||Y)
					Snext=S1;
				else
					Snext=S0;
			end
			S1:begin
				if(X&&Y)
					Snext=S3;
				else if(X||Y)
					Snext=S2;
				else
					Snext=S1;
			end
			S2:begin
				if(X&&Y)
					Snext=S0;
				else if(X||Y)
					Snext=S3;
				else
					Snext=S2;
			end
			S3:begin
				if(X&&Y)
					Snext=S1;
				else if(X||Y)
					Snext=S0;
				else
					Snext=S3;
			end
			default:Snext=S0;
		endcase
	end
	
	assign Z=(Sreg==S0);
endmodule
```

#### 104. counter_1

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/"1"计数器|"1"计数器]]，代码块位置 L71-L105
- 上下文：利用verilog加法功能的编码方式
- 模块名：`counter_1`

功能描述：

`counter_1` 属于计数器/计数逻辑。它来自“利用verilog加法功能的编码方式”这一小节。主要接口/信号包括：CLK, RST, X, Y, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module counter_1(CLK,RST,X,Y,Z);
	input CLK,RST,X,Y;
	output reg Z;
	reg [1:0] S,Snext;
	
	//1.状态存储器
	always@(posedge CLK) begin
		if(RST)
			S<=0;
		else
			S<=Snext;
	end
	//2.次态逻辑	
	always@(S,X,Y) begin
		if(X&&Y)
			Snext<=S+2'd2;
		else if(X||Y)
			Snext<=S+2'd1;
		else
			Snext<=S;
	end
	/*
	更简洁的次态逻辑编码方式:
	assign Qnext=Q+{1'b0,X}+{1'b0,Y};
	*/
	//3.输出逻辑
	always@(S) begin
		if(Q==0)
			Z=1;
		else
			Z=0;
	end
endmodule
```

#### 105. VronescntSMa

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/"1"计数器|"1"计数器]]，代码块位置 L109-L134
- 上下文：将状态存储和次态逻辑组合到一起
- 模块名：`VronescntSMa`

功能描述：

`VronescntSMa` 属于有限状态机设计。它来自“将状态存储和次态逻辑组合到一起”这一小节。主要接口/信号包括：CLOCK, RESET, X, Y, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module VronescntSMa(CLOCK, RESET, X, Y, Z);
    input CLOCK, RESET, X, Y;
    output reg Z;
    reg [1:0] Q;
    
     // 创建状态存储和转移
    always @(posedge CLOCK) begin         
        if (RESET==1)            
	        Q <= 0       // 同步复位
        else if (X & Y)   
	        Q <= Q + 2;
	    else if (X | Y)        
		    Q <= Q + 1;
		/*else      
			Q <= Q;  可选的*/
	end
	//输出逻辑
    always @(Q) begin                             
       if (Q==0) 
	       Z = 1; 
       else 
	       Z = 0;
     end
endmodule
```

### 来源：[[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]

#### 106. 寄存器型输出/流水线输出*了解*

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/Verilog状态机编码风格|Verilog状态机编码风格]]，代码块位置 L118-L130
- 上下文：寄存器型输出/流水线输出*了解*

功能描述：

该代码块属于触发器/时序寄存器。它来自“寄存器型输出/流水线输出*了解*”这一小节。

代码要点：

- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。

源代码：

```verilog
// 组合逻辑输出（可能有毛刺）
always @(*) begin
    case (Sreg)
        INIT, A0, A1: Z_comb = 0;
        OK0:          Z_comb = 1;
    endcase
end

// 寄存器型输出（延迟一拍，时序干净）
always @(posedge clk)
    Z <= Z_comb;
```

### 来源：[[CH12 Verilog状态机设计/序列发生器|序列发生器]]

#### 107. seq_gen

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/序列发生器|序列发生器]]，代码块位置 L8-L21
- 上下文：法1: 移位寄存器预置序列，循环移位
- 模块名：`seq_gen`

功能描述：

`seq_gen` 属于移位寄存器/移位逻辑。它来自“法1: 移位寄存器预置序列，循环移位”这一小节。主要接口/信号包括：clk, rst_n, seq_out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module seq_gen(clk,rst_n,seq_out);
    input clk,rst_n;
    output seq_out;
    reg [5:0] Q;

    always@(posedge clk)
        if(~rst_n)
            Q<=6'b110010;
        else
            Q<={Q[4:0],Q[5]};
    assign seq_out<=Q[5];
endmodule
```

#### 108. seq_gen_counter

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/序列发生器|序列发生器]]，代码块位置 L34-L65
- 上下文：法2: 计数器 + 组合逻辑查表
- 模块名：`seq_gen_counter`

功能描述：

`seq_gen_counter` 属于计数器/计数逻辑。它来自“法2: 计数器 + 组合逻辑查表”这一小节。主要接口/信号包括：clk, rst_n, seq_out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module seq_gen_counter (
    input       clk,      // 时钟
    input       rst_n,    // 异步复位，低有效
    output reg  seq_out   // 序列输出
);
    reg [2:0] cnt;        // 计数器：0 ~ 5 循环

    // 时序逻辑：模6计数器
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 3'd0;
        else if (cnt == 3'd5)
            cnt <= 3'd0;
        else
            cnt <= cnt + 1'b1;
    end

    // 组合逻辑：根据计数值输出对应的序列位
    always @(*) begin
        case (cnt)
            3'd0: seq_out = 1'b1;
            3'd1: seq_out = 1'b1;
            3'd2: seq_out = 1'b0;
            3'd3: seq_out = 1'b0;
            3'd4: seq_out = 1'b1;
            3'd5: seq_out = 1'b0;
            default: seq_out = 1'b0;
        endcase
    end
endmodule
```

#### 109. seq_gen_fsm

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/序列发生器|序列发生器]]，代码块位置 L79-L129
- 上下文：法3: 有限状态机（FSM），6 个状态循环转移
- 模块名：`seq_gen_fsm`

功能描述：

`seq_gen_fsm` 属于有限状态机设计。它来自“法3: 有限状态机（FSM），6 个状态循环转移”这一小节。主要接口/信号包括：clk, rst_n, seq_out。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用组合 `always @*` / `always @(*)`，需要覆盖所有分支以避免意外锁存器。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module seq_gen_fsm (
    input       clk,
    input       rst_n,
    output reg  seq_out
);
    // 状态编码
    parameter [2:0] S0 = 3'b000,  // 输出 1
                    S1 = 3'b001,  // 输出 1
                    S2 = 3'b010,  // 输出 0
                    S3 = 3'b011,  // 输出 0
                    S4 = 3'b100,  // 输出 1
                    S5 = 3'b101;  // 输出 0

    reg [2:0] current_state, next_state;

    // ① 状态寄存器（时序逻辑）
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= S0;
        else
            current_state <= next_state;
    end

    // ② 次态逻辑（组合逻辑）
    always @(*) begin
        case (current_state)
            S0: next_state = S1;
            S1: next_state = S2;
            S2: next_state = S3;
            S3: next_state = S4;
            S4: next_state = S5;
            S5: next_state = S0;
            default: next_state = S0;
        endcase
    end

    // ③ 输出逻辑（组合逻辑）
    always @(*) begin
        case (current_state)
            S0: seq_out = 1'b1;
            S1: seq_out = 1'b1;
            S2: seq_out = 1'b0;
            S3: seq_out = 1'b0;
            S4: seq_out = 1'b1;
            S5: seq_out = 1'b0;
            default: seq_out = 1'b0;
        endcase
    end
endmodule
```

### 来源：[[CH12 Verilog状态机设计/序列检测器|序列检测器]]

#### 110. fsm

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/序列检测器|序列检测器]]，代码块位置 L11-L45
- 上下文：1. 先画状态转移图
- 模块名：`fsm`

功能描述：

`fsm` 属于有限状态机设计。它来自“1. 先画状态转移图”这一小节。主要接口/信号包括：CLK, X, Z, RST。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module fsm(CLK,X,Z,RST);
	input CLK,X;//X为输入的序列
	output Z;
	reg [2:0] S,Snext;//5个状态需要3位来编码
	
	parameter [2:0] INIT=3'b000;
	parameter [2:0] S0  =3'b001;
	parameter [2:0] S1  =3'b010;
	parameter [2:0] S2  =3'b011;
	parameter [2:0] S3  =3'b100;
	//状态存储器
	always@(posedge CLK) begin
		if(RST)
			S<=INIT;
		else
			S<=Snext;
	end
	
	//次态逻辑
	always@(S,X) begin
		case(S)
			INIT:Snext=X?S0:INIT;
			S0  :Snext=X?S1:INIT;
			S1  :Snext=~X?S2:INIT;
			S2  :Snext=X?S3:INIT;
			S3  :Snext=~X?INIT:S1;
			default:Snext=INIT;
		endcase
	end
	
	//输出逻辑
	assign Z=(S==S3)?1'b1:1'b0;
endmodule
```

#### 111. fsm_mealy

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/序列检测器|序列检测器]]，代码块位置 L68-L103
- 上下文：3. Verilog代码（考虑overlap）
- 模块名：`fsm_mealy`

功能描述：

`fsm_mealy` 属于有限状态机设计。它来自“3. Verilog代码（考虑overlap）”这一小节。主要接口/信号包括：CLK, X, Z, RST。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module fsm_mealy(CLK, X, Z, RST);
    input CLK, X;
    output Z;
    reg [1:0] S, Snext; // 4个状态只需2位编码

    parameter [1:0] INIT = 2'b00;
    parameter [1:0] S0   = 2'b01; // 前缀 1
    parameter [1:0] S1   = 2'b10; // 前缀 11
    parameter [1:0] S2   = 2'b11; // 前缀 110

    // 状态存储器
    always @(posedge CLK) begin
        if (RST)
            S <= INIT;
        else
            S <= Snext;
    end

    // 次态逻辑
    always @(S, X) begin
        case (S)
            INIT: Snext = X ? S0 : INIT;
            S0:   Snext = X ? S1 : INIT;
            S1:   Snext = X ? S1 : S2;
            S2:   Snext = X ? S0 : S2; // overlap: X=1→S0
            default: Snext = INIT;
        endcase
    end

    // 输出逻辑（Mealy: 取决于 状态+输入）
    always @(S, X) begin
        Z = (S == S2) & X; // S₂且X=1时输出1
    end
endmodule
```

### 来源：[[CH12 Verilog状态机设计/状态机示例1|状态机示例1]]

#### 112. FSM1

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/状态机示例1|状态机示例1]]，代码块位置 L5-L77
- 上下文：Ex.1
- 模块名：`FSM1`

功能描述：

`FSM1` 属于有限状态机设计。它来自“Ex.1”这一小节。主要接口/信号包括：CLK, RST, A, B, Z。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用 `parameter/localparam` 定义位宽、状态或常量，便于复用和修改。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `case` 枚举选择、译码、状态转移或查表逻辑。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module FSM1(CLK,RST,A,B,Z);
	input CLK,RST;//时钟和复位信号
	input A,B;
	output reg Z;
	//5个状态，要3bit才能编码
	parameter [2:0] INIT=3'b000,
					A0  =3'b001;
					A1  =3'b010;
					OK0 =3'b011;
					OK1 =3'b100;
	reg [2:0] Sreg,S_next;//状态寄存器和次态的命名
	//第一部分：状态存储器
	always @(posedge CLK) begin
		if(RST)
			Sreg<=INIT;//复位时回到初始状态
		else
			Sreg<=S_next;//正常工作锁存次态
	end
	//第二部分:次态转移逻辑
	//敏感信号列表里为状态和输入信号
	//纯组合逻辑，根据当前状态输出次态
	always@(A,B,Sreg) begin
		//然后根据状态转移表编写转移代码
		case(Sreg)
			INIT:begin
				if(A==0)
					S_next<=A0;
				else
					S_next<=A1;
			end
			A0:begin
				if(A==0)
					S_next<=OK0;
				else
					S_next<=A1;
			end
			A1:begin
				if(A==0)
					S_next<=A0;
				else
					S_next<=OK1;
			end
			OK0:begin
				if(A==0)
					S_next<=OK0;
				else if((A==1)&&(B==1))
					S_next<=OK1;
				else
					S_next<=A1;
			end
			OK1:begin
				if(A==1)
					S_next<=OK1;
				else if((A==0)&&(B==0))
					S_next<=A0;
				else
					S_next<=OK0;
			end
			default:S_next<=INIT;//最小风险处理
		endcase
	end
	//输出逻辑
	//敏感信号列表里为状态，暗示这是一个Moore型FSM
	always@(Sreg) begin
		case(Sreg)
			INIT,A0,A1:Z=0;
			OK0,OK1:Z=1;
			default:Z=0;
		endcase
	end
endmodule
```

#### 113. 同步复位

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/状态机示例1|状态机示例1]]，代码块位置 L99-L105
- 上下文：同步复位

功能描述：

该代码块属于触发器/时序寄存器。它来自“同步复位”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
always@(posedge CLK)
	if(RESET==1)
		Sreg<=INIT;
	else
		Sreg<=Snext;
```

#### 114. 异步复位

- 分类：时序逻辑
- 来源：[[CH12 Verilog状态机设计/状态机示例1|状态机示例1]]，代码块位置 L109-L115
- 上下文：异步复位

功能描述：

该代码块属于触发器/时序寄存器。它来自“异步复位”这一小节。

代码要点：

- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
always@(posedge CLK or posedge RESET)
	if(RESET==1)
		Sreg<=INIT;
	else
		Sreg<=Snext;
```

### 来源：[[Exam_topic]]

#### 115. 时序逻辑

- 分类：时序逻辑
- 来源：[[Exam_topic]]，代码块位置 L125-L128
- 上下文：时序逻辑

功能描述：

该代码块属于异或/奇偶校验逻辑。它来自“时序逻辑”这一小节。

代码要点：

- 使用 `assign` 连续赋值描述组合逻辑或输出连接。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。

源代码：

```verilog
wire odd_parity;
assign odd_parity = ~(^(din));
```

#### 116. frequency_divider

- 分类：时序逻辑
- 来源：[[Exam_topic]]，代码块位置 L131-L156
- 上下文：时序逻辑
- 模块名：`frequency_divider`

功能描述：

`frequency_divider` 属于触发器/时序寄存器。它来自“时序逻辑”这一小节。主要接口/信号包括：clk, rst_n, clk_en。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module frequency_divider (
    input  wire clk,
    input  wire rst_n,
    output reg  clk_en
);

    reg [4:0] cnt; // 20分频需要计数 0~19，5位宽足够

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt    <= 5'd0;
            clk_en <= 1'b0;
        end else begin
            if (cnt == 5'd19) begin
                cnt    <= 5'd0;
                clk_en <= 1'b1; // 满20个周期产生一个单脉冲使能
            end else begin
                cnt    <= cnt + 1'b1;
                clk_en <= 1'b0;
            end
        end
    end

endmodule
```

#### 117. parallel_to_serial

- 分类：时序逻辑
- 来源：[[Exam_topic]]，代码块位置 L159-L193
- 上下文：时序逻辑
- 模块名：`parallel_to_serial`

功能描述：

`parallel_to_serial` 属于移位寄存器/移位逻辑。它来自“时序逻辑”这一小节。主要接口/信号包括：clk, rst_n, clk_en, load, din, dout。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。
- 使用边沿敏感 `always` 块描述触发器、寄存器或同步时序逻辑。
- 时序逻辑中使用非阻塞赋值 `<=`，避免寄存器更新顺序错误。
- 组合逻辑、临时变量或 testbench 激励中使用阻塞赋值 `=`。
- 使用 `if/else` 表达优先级、复位、使能或条件分支。

源代码：

```verilog
module parallel_to_serial (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       clk_en,
    input  wire       load,
    input  wire [7:0] din,
    output reg        dout
);

    reg [8:0] shift_reg; // 9位移位寄存器：[7:0]存数据，[8]存奇校验位
    reg [3:0] bit_cnt;   // 计数发送了多少位 (0~8)

    // 奇校验位计算
    wire odd_parity = ~(^din);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 9'd0;
            dout      <= 1'b0;
        end else if (load) begin
            // load为1时，同步加载数据和校验位
            shift_reg <= {odd_parity, din}; 
            // 校验位放在最高位，方便从LSB向右移出
        end else if (clk_en) begin
            // load为0且分频时钟使能到达时，串行移位输出
            dout      <= shift_reg[0];      
            // 输出当前最低位(LSB优先)
            shift_reg <= {1'b0, shift_reg[8:1]}; 
            // 右移一位，高位补0
        end
    end

endmodule
```

#### 118. top

- 分类：时序逻辑
- 来源：[[Exam_topic]]，代码块位置 L196-L226
- 上下文：时序逻辑
- 模块名：`top`

功能描述：

`top` 属于移位寄存器/移位逻辑。它来自“时序逻辑”这一小节。主要接口/信号包括：clk, rst_n, load, din, dout。

代码要点：

- 用 `module ... endmodule` 封装为可例化模块。

源代码：

```verilog
module top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       load,
    input  wire [7:0] din,
    output wire       dout
);

    // 内部连线：分频器输出的使能信号
    wire clk_en;

    // 例化分频器模块
    frequency_divider u_frequency_divider (
        .clk    (clk),
        .rst_n  (rst_n),
        .clk_en (clk_en)
    );

    // 例化并串转换器模块
    parallel_to_serial u_parallel_to_serial (
        .clk    (clk),
        .rst_n  (rst_n),
        .clk_en (clk_en),
        .load   (load),
        .din    (din),
        .dout   (dout)
    );

endmodule
```
