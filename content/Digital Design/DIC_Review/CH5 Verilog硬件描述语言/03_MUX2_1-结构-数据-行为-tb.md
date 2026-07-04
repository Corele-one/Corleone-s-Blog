![[file-20260627092501775.png|516]]

# 用结构化模型来描述该电路

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

# 用数据流模型来描述

```verilog
module mux2_1(a,sel,b,out);
	input a,sel,b;
	output out;
	wire out;
	
	assign out = (a&(~sel))|(b&sel);
endmodule
```

# 用行为化模型

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

# testbench

![[file-20260627094228545.png|234]]

这是要给到mux2_1的输入组合，根据该输入组合编写tb

![[file-20260627094916925.png|288x200]]

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


