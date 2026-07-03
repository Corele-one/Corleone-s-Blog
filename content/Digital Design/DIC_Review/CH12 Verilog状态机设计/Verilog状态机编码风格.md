# 三段式状态机编码风格

> [!info] 核心思想
> 基本 Verilog 状态机编码风格将 FSM 代码分为 **三个独立部分**，分别对应 Mealy/Moore 型状态机的三大模块。

![[file-20260630231325336.png]]

## 三个组成部分

### 1. 状态存储器（State Register）

- **功能**：保存当前状态（current state）
- **实现方式**：
  - **行为化风格**：使用对时钟信号边沿敏感的 `always` 程序块（类似边沿触发 D 触发器）
  - **结构化风格**：使用显式触发器实例化（如 `dff` 模块例化）
- **关键点**：
  - 通常在时钟上升沿触发
  - 需要 **复位能力**（reset），确保系统上电后进入已知状态

> [!example] 图 12-1 示例：状态存储器
> ```verilog
> always @ (posedge CLOCK)
>     Sreg <= Snext;
> ```
> - 时钟上升沿触发，将次态 `Snext` 锁存到现态 `Sreg`

### 2. 次态（激励）逻辑（Next State Logic）

- **功能**：根据当前状态和输入信号，计算下一个状态
- **实现方式**：
  - 组合逻辑 `always` 块
  - 敏感信号列表包含：**当前状态 + 输入信号**
  - 通常包含 `case` 语句，枚举所有可能的现态值
- **关键点**：
  - 纯组合逻辑，无时钟信号
  - `case` 语句覆盖所有状态，default 分支防止锁存器

> [!example] 图 12-1 示例：次态逻辑
> ```verilog
> always @ (A, B, Sreg) begin
>     case (Sreg)
>         INIT:  if (A==0) Snext = A0;
>                else      Snext = A1;
>         A0:    ...
>     endcase
> end
> ```
> - 敏感列表：`A, B, Sreg`（输入 + 当前状态）
> - 使用 `case` 枚举所有现态值

### 3. 输出逻辑（Output Logic）

- **实现方式**：
  - 组合逻辑 `always` 块
  - 敏感信号列表包含：**当前状态 + 输入信号**
  - 可能包含也可能不包含 `case` 语句，取决于输出函数的复杂度
- **Moore 型**：输出仅取决于当前状态
- **Mealy 型**：输出取决于当前状态和输入

> [!example] 图 12-1 示例：Moore 型输出逻辑
> ```verilog
> always @ (Sreg)
>     case (Sreg)
>         INIT, A0, A1:  Z = 0;
>         OK0, OK1:      Z = 1;
>         default        Z = 0;
>     endcase
> ```
> - 敏感列表：仅 `Sreg`（隐含的Moore 型：输出只与状态有关）
> - 输出 `Z` 仅取决于当前状态

> [!tip] Moore vs Mealy
> - **Moore 型**：输出逻辑敏感列表只有状态（如上例）
> - **Mealy 型**：输出逻辑敏感列表包含状态 + **输入**

## 编码风格的变化

> [!tip] 灵活组合
> 每一部分的详细代码都可以根据设计需求进行变化。

### 次态与输出逻辑合并

当次态逻辑和输出逻辑的 `case` 分支完全一致，且输出比较简单时，可以合并到一个 `always` 块中：

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

### 寄存器型输出/流水线输出*了解*

[[三段式状态机]]这个笔记里说的设计方法就是带寄存器/流水线输出的状态机

在输出逻辑后加一级 **寄存器**，让输出延迟一拍，改善时序：

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

| 输出类型 | 特点 |
|---------|------|
| 组合逻辑输出 | 无延迟，可能有毛刺 |
| 寄存器型输出 | 延迟一拍，时序稳定，适合高速设计 |

## 其他重要方面

1. **状态编码**：使用 `parameter` 语句定义状态编码（如 `parameter S0 = 2'b00`）
2. **复位能力**：状态存储器必须具备复位功能，确保 FSM 可以从已知状态开始运行

