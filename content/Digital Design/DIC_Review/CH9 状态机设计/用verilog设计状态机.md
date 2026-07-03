# 使用verilog设计状态机

依旧是本节中提到的例子

![[file-20260627123235441.png|441]]
## 用verilog描述状态机的5个步骤

1. **声明输入、输出及局部变量。** 由于将用行为化代码来说明机器的操作，因此输出和局部变量的类型应当是 `reg`。

2. **用 `parameter` 语句给每个命名的状态赋予状态-变量的取值组合。**

3. **第一个 `always` 程序块用于创建状态存储器，** 对应于通用 Moore 状态机结构中的**状态存储器**。

4. **第二个 `always` 程序块定义次态的行为，** 对应于通用 Moore 状态机结构中的**次态（激励）逻辑 $F$**。

5. **第三个 `always` 程序块定义输出逻辑，** 对应于通用 Moore 状态机结构中的**输出逻辑 $G$**。

![[file-20260627124156212.png|902]]


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

