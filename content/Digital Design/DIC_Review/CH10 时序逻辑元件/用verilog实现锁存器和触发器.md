**一般不会用结构化和数据流来描述锁存器和触发器**，这样的做法和[[锁存器和触发器]]中提到的门级描述差不多，所以一般采用行为级描述

# 请注意非阻塞赋值
⚠️本节开始介绍用verilog编写时序逻辑模型，注意在时序电路中，需要采用**非阻塞赋值**！

- **阻塞赋值 `=`**：立刻生效，下一行能读到新值 → 适合**组合逻辑**（输入变则输出立刻变）
- **非阻塞赋值 `<=`**：先记下所有 RHS 值，时间步结束时统一更新 → 适合**时序逻辑**（所有触发器在时钟沿同时采样、同时更新）

**如果时序逻辑误用阻塞赋值：**
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

> 本节的锁存器/触发器模型中，`always` 块全部使用 `<=`。组合逻辑（如译码器）则应使用 `=`。

# 行为化锁存器和触发器模型

## D锁存器的行为化模型

[[锁存器和触发器#D锁存器]]

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

## 带异步清零和门使能的D锁存器模型

![[file-20260626155211372.png|878]]

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

## 带锁存输出的n-s位译码器

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

和[[译码器和多路复用器#模块参数化设计]]的区别？
**当 `CLR=0` 且 `G=0` 时**，`always@(*)` 块中没有任何语句对 `Y` 赋值。综合工具为了保持 `Y` 的值不变，**必须推断出锁存器（Latch）** 来存储上一次的状态。

## D触发器的行为化模型

```verilog
module DFF(CLK, D, Q)
	input CLK,D;
	output Q;
	
	always@(posedge CLK)
		Q<=D;
endmodule
```

## 带异步清零端的D触发器
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

## 带有Q_N输出的D触发器的**错误**模型

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

**错误原因**：非阻塞赋值中，`~Q` 读到的是 `Q` 的**旧值**（变化前），因此 `QN` 得到的是**上一个周期** Q 的取反，而非当前周期，**滞后一个时钟周期**。

| 时钟沿 | D | Q(旧) | ~Q(旧) | Q→新值 | QN 应该是 |
|--------|---|--------|--------|--------|-----------|
| ↑₁ | 1 | 0 | **1** | 1 | ~1 = **0** ✗ |
| ↑₂ | 0 | 1 | **0** | 0 | ~0 = **1** ✗ |

**修正**：让 QN 直接取 `~D`，与 Q 同步变化：

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

还有一种更简单的修改方法
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

## 带有时钟使能端和同步置位端的D触发器

[[锁存器和触发器#带使能端的DFF]]

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

# 用verilog实现时钟
## always 与 initial

Verilog 行为级描述的基本块，两者**不能相互嵌套**。

### initial —— 执行一次

- 仿真**开始时执行一次**，之后不再触发
- **不可综合**（综合工具直接忽略），仅用于仿真/testbench
- 典型用途：初始化信号、生成测试激励

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

### always —— 循环执行

- 敏感列表触发后**反复执行**，仿真期间永不终止
- **可综合**（在合理使用下），用于描述实际硬件逻辑
- 触发方式决定电路类型：

```verilog
always @(*)          // 组合逻辑：任何输入变化都触发
always @(posedge CLK)// 时序逻辑：时钟上升沿触发
always @(A or B)     // 组合逻辑：指定信号变化时触发
```

### 对比

|          | `initial`     | `always`   |
| -------- | ------------- | ---------- |
| **执行次数** | 1 次           | 循环无数次      |
| **触发时机** | 仿真开始（t=0）     | 敏感列表事件触发   |
| **可综合性** | ❌ 不可综合        | ✅ 可综合      |
| **典型用途** | testbench 初始化 | 描述组合/时序逻辑  |
| **电路意义** | 无硬件对应         | 对应真实的门/触发器 |

> 实际硬件模块中几乎只用 `always`；`initial` 主要出现在 testbench 中。
## 时钟产生器的设计

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

## 将时钟放入完整 testbench

以 D 触发器（带异步清零）为例，时钟生成有两种写法：

### 内联

将时钟的 `initial` + `always` 直接写在 testbench 中，不需要单独模块：

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

### 模块例化

保留独立的时钟模块，在 TB 中例化：

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

![[file-20260626193424797.png|594]]

注意**always语句**设计时钟的方式以及用**initial语句**对**时钟初始化**的方法