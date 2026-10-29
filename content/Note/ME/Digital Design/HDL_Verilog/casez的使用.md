*example*
```verilog
always @(*) begin
    casez (in[3:0])
        4'bzzz1: out = 0;   // in[3:1] can be anything
        4'bzz1z: out = 1;
        4'bz1zz: out = 2;
        4'b1zzz: out = 3;
        default: out = 0;
    endcase
end
```
z是高阻态的意思，在上述的优先编码器中，z所代表的位置表示“don‘t care” ，可以用“?”来代替z，拿 <u>4'bzz1z: out = 1;</u> 举例子，只要in[0]为1，那么out将会变成0，但是这种情况下会出现一个严重的问题，就是case的判断条件之间不是互斥的，==case之间的顺序会影响语句的输出结果==，例如，如果上述代码写成
```verilog
always @(*) begin
    casez (in[3:0])
        4'b1zzz: out = 0;   // this case has been changed
        4'bzz1z: out = 1;
        4'bz1zz: out = 2;
        4'bzzz1: out = 3;
        default: out = 0;
    endcase
end
```
那么无论是输入1000，1100，1010，代码的输出结果都会是0，与我们想要的逻辑功能不符，所以说case之间的逻辑关系最好是互斥的，比如说我们可以做如下的修改：
```verilog
casez (in[3:0])
	4'bzzz1: ...
	4'bzz10: ...
	4'bz100: ...
	4'b1000: ...
	default: ...
endcase
```
这样的话，case和case之间就是独立的，我们就不用去考虑case的顺序问题了
```
It may be less error-prone to explicitly specify the priority behaviour rather than rely on the ordering of the case items.
```
