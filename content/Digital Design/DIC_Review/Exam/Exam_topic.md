组合逻辑
---
填空题

![[IMG_1880.jpeg|1792]]

1. 数制转换，注意十进制的小数和二进制的小数之间的互相转换，以及二进制小数变成十六进制小数
2. ROM，8代表地址线为8位，存储线(输出数据)位宽为16，1byte=8bit，1KB=1024byte，答案为0.5KB
3. SRAM、DRAM的内部原理，以及各个存储设备的控制器的选用
4. 原码、补码转换
5. 最大项、最小项表示逻辑表达式以及各个逻辑表达式之间的互相转换
6. Verilog语法-拼接

![[IMG_1881.jpeg|1894]]

7. Verilog 逻辑操作符
8. D-Latch

*还可能有的题型：选择题、判断题*

![[IMG_1882.jpeg|1813]]

组合电路设计，常用语句：连续赋值(assign)、过程块

```verilog
module XOR(A,B,C);
	input A,B;
	output C;
	assign C = A^B;
endmodule
//一般两问之间是有联系的
module odd_parity(A,F);//生成奇校验位
	input [3:0] A;
	output F;
	wire A_1,A_2,F1;
	XOR xor1(.A(A[0]),.B(A[1]),.C(A_1));
	XOR xor2(.A(A[2]),.B(A[3]),.C(A_2));
	XOR xor3(.A(A_1),.B(A_2),.C(F1));
	not u1(F,F1);
	//取个非，因为奇校验位的意思是
	//偶数个1的时候F=1，奇数个1的时候输出0
endmodule
//结构型描述、数据流描述(assign)、行为级描述(always)
```

![[IMG_1886.jpeg|1486]]

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

![[IMG_1887.jpeg|1926]]

```verilog
// 10 位加法器：A + B = {C, S}
module Adder10(A, B, C, S);
	input  [9:0] A, B;
	output       C;     // 进位输出
	output [9:0] S;     // 和

	assign {C, S} = A + B;   // 11 位结果，高位即进位
endmodule
```

![[IMG_1888.jpeg|1697]]

逻辑表达式
F=(A'&D)|(A'&B'&C)|(B'&C&D)|(B&C'&D)

| **A** | **B** | **C** | **D** | **F** |
| ----- | ----- | ----- | ----- | ----- |
| 0     | 0     | 0     | 0     | **0** |
| 0     | 0     | 0     | 1     | **1** |
| 0     | 0     | 1     | 0     | **1** |
| 0     | 0     | 1     | 1     | **1** |
| 0     | 1     | 0     | 0     | **0** |
| 0     | 1     | 0     | 1     | **1** |
| 0     | 1     | 1     | 0     | **0** |
| 0     | 1     | 1     | 1     | **1** |
| 1     | 0     | 0     | 0     | **0** |
| 1     | 0     | 0     | 1     | **0** |
| 1     | 0     | 1     | 0     | **0** |
| 1     | 0     | 1     | 1     | **1** |
| 1     | 1     | 0     | 0     | **0** |
| 1     | 1     | 0     | 1     | **1** |
| 1     | 1     | 1     | 0     | **0** |
| 1     | 1     | 1     | 1     | **0** |

画CMOS电路：
There is a logic equation Z=a'+bc. Draw its CMOS circuit diagram.

![[file-20260628111907838.png]]


---
# 时序逻辑

![[file-20260618083516465.png|794]]

```verilog
module FSM(clk,X,Z,rst);
	input clk,rst;//rst复位，题目暗示初始状态，所以需要复位信号
	input X;
	output Z;
	reg [1:0] Q1,Q2;//题目要求
	
	parameter [1:0] A=2'b11,B=2'b10,C=2'b01,D=2'b00;
	//1.状态存储器
	always@(posedge clk) begin
		if(rst)//同步复位，本题没有指明
			Q1<=A;
		else
			Q1<=Q2;
	end
	
	//2.次态逻辑
	//纯组合逻辑，敏感信号写@(*)也行，只是课本里习惯写成输入变量和当前状态
	always@(X,Q1) begin 
		case(Q1):
			A: begin
				if(X==1)
					Q2<=C;
				else
					Q2<=B;
			end
			B: begin
				if(X==1)
					Q2<=D;
				else
					Q2<=C;
			end
			C: begin
				if(X==1)
					Q2<=A;
				else
					Q2<=D;
			end
			D: begin
				if(X==1)
					Q2<=B;
				else
					Q2<=A;
			end
			default:Q2<=A;    
		endcase
	end
	
	assign Z=(Q1==D)?1'b1:1'b0;
endmodule
```

![[file-20260618083744575.png|859]]

数据八位，传输9位，最后一位为奇偶校验位(UART)

奇校验编码的方式
```verilog
wire odd_parity;
assign odd_parity = ~(^(din));
```

分频器
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

并串转换(采用移位寄存器)，因为题目要求先传输LSB，所以说要使用一个右移的移位寄存器
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

顶层模块(采用结构化描述)
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
