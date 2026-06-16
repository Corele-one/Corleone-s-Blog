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
8. 门控锁存器

*还可能有的题型：选择题、判断题*

![[IMG_1882.jpeg|1813]]

组合电路设计，常用语句：连续赋值(assign)、过程块

```Verilog
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

![[IMG_1886.jpeg|1486]]

```Verilog
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

```Verilog
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
![[file-20260616112642887.png|601x500]]

此处画的有些不严谨，更严谨的画法是把a所连接的pmos的bubble朝左画，否则这样的画法看起来很像transition gate

---
