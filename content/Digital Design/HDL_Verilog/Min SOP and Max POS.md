```
A single-output digital system with four inputs (a,b,c,d) generates a logic-1 when 2, 7, or 15 appears on the inputs, and a logic-0 when 0, 1, 4, 5, 6, 9, 10, 13, or 14 appears. The input conditions for the numbers 3, 8, 11, and 12 never occur in this system. For example, 7 corresponds to a,b,c,d being set to 0,1,1,1, respectively.
```
![[file-20260409192927331.png|600]]
利用无关项将卡诺图化简的圈扩大到4格，可以起到最大的简化
```verilog
assign out_sop = (c&~a&~b)|(c&d);
assign out_pos = (a|c)&(~a|c)&(~c|~a|b)&(~b|~c|d);
```
