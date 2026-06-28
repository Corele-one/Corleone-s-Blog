```
Given a 100-bit input vector [99:0], reverse its bit ordering.
```
```verilog
module top_module( 
    input [99:0] in,
    output [99:0] out
);
```
为了实现这样的位反转操作，最简单的方法是写一堆assign语句，eg：
```verilog
assign out[0] = in[99];
assign out[1] = in[98];
......
```
但是如果这样做，太tedious了，所以我们可以用[[for语句]]来解决这个问题
