From:[比飞鸟贵重的多_HKL](https://space.bilibili.com/218427631/)

# Why CMake？

CMake 的本质是：指定需要编译的 C/C++ 文件（类比让厨师知道做饭时需要哪些原料、从哪里获取）。

![[file-20260728113434869.png]]

上图中，`CMakeLists.txt` 指定了 CMake 所需的最低版本、定义了项目名称，并包含了需要用到的子目录，包含子目录的同时也表示会使用到子目录中的`CmakeList.txt`

## 头文件的作用

在预编译阶段，头文件会被展开到引用它的源文件中。头文件通常用于声明**接口**、**可复用的类型定义**和**宏**等，通过合理使用头文件，可以大幅减少代码中的重复定义。

## 技术优化路径

**现代技术优化的三大目标**

1. **提高效率**（详见 *Effective C++*）
2. **减少重复**
3. **减轻依赖**

使用 `include_directories` 可以减少程序中的重复——例如某个文件夹下的 `.cpp` 文件需要用到另一个文件夹中的头文件。但如果使用不当（如下图所示），会导致**依赖过度**的问题。

![[file-20260728113030244.png]]

# 静态库和动态库

![[file-20260728135914946.png]]

>*静态库与动态库的区别发生在编译阶段的链接过程. 来源：博客园*

### 静态库的工作原理
1. 在代码编译的**链接阶段**，链接器（Linker）会去静态库文件（如 `libmath.a`）中寻找你的程序调用的函数实现代码。
2. 找到后，把这部分二进制代码直接“黏贴”进你的主程序文件（如 `main.exe`）中。
3. 编译完成后，这个静态库文件就可以删掉了，你的主程序依然能独立运行。

生成静态库

![[file-20260728142226746.png]]

在使用生成之后的静态库的时候，库文件需要配套一个头文件来作为调用的入口使用
- **头文件（`.h`）** — 告诉编译器"有哪些函数可以调用"，即**接口声明**
- **库文件（`.lib`）** — 包含这些函数的**实际二进制实现**

**编译时**：编译器读头文件 → 知道函数签名，确认调用方式合法，生成目标代码（`.obj`）

**链接时**：链接器读 `.lib` → 找到函数的实现代码，"拷贝"进最终可执行文件


![[file-20260728143534301.png|200]]

第一行是add函数的声明，之后写到头文件里作为可复用的接口

**为什么一个简单的声明就能链接到库文件？**

关键在于**编译**和**链接**是两个完全独立的阶段：

> **编译阶段**：编译器看到函数声明（如 `int add(int a, int b);`）后，只做两件事：
> 1. 校验调用方式合法（参数类型、个数是否匹配）
> 2. 在生成的 `.obj` 文件中记下一个**符号引用**：*"我要找一个叫 `add` 的函数"*
>
> 编译器**完全不关心**函数的实现代码在哪。

> **链接阶段**：链接器拿到 `.obj` 后，发现未解决的符号 `add`，于是拿着这个名字去 `.lib` 里搜索——找到了，就把对应的二进制代码"粘贴"进最终程序。

因此，函数声明本质上只是一个**符号名的约定**：

| 阶段 | 作用 |
|------|------|
| 编译时 | 告诉编译器符号存在，让编译通过 |
| 链接时 | 链接器根据符号名去 `.lib` 里匹配实现 |

> 💡 在 `.cpp` 里手写 `int add(int a, int b);` 和 `#include "add.h"` 在链接层面**效果完全一样**——链接器只认符号名，不在乎声明是从哪来的。头文件只是一个**方便复用的声明模板**。

链接生成的库文件(lib)

![[file-20260728142044660.png]]

### 动态库的工作原理

1. 编译时，链接器只检查动态库（如 `libmath.so`）中是否存在这些函数名（导出符号），并把这些符号定位信息写进主程序。
2. 程序启动运行时，操作系统中的**动态加载器**（如 Linux 上的 `ld.so`，Windows 上的 `kernel32.dll`）负责把相应的动态库文件加载到内存空间中。
3. 运行时如果多个程序都在调这个动态库，操作系统会将内存中的同一份库代码共享映射给各个进程。

生成动态库

![[file-20260728143826765.png]]

 在window系统里编译动态库还要加上一行关键字(`_declspec(dllexport)`)
 
![[file-20260728144115366.png]]

外部程序在使用该动态库时，需要加上 `_declspec(dllimport)` 关键字来导入符号。但每次都手动加太麻烦，通常的做法是**用一个宏自动切换 `dllexport` 和 `dllimport`**，而这个宏可以在 CMake 中定义。

**头文件中的宏定义（如 `add.h`）：**

```cpp
#ifdef MYLIB_EXPORTS   // 如果定义了 MYLIB_EXPORTS，说明正在编译动态库本身
#define MYLIB_API __declspec(dllexport)
#else                  // 否则，说明是外部程序在引用该库
#define MYLIB_API __declspec(dllimport)
#endif

MYLIB_API int add(int a, int b);  // 用宏统一声明
```

**CMakeLists.txt 中设置该宏：**

```cmake
target_compile_definitions(mylib PRIVATE MYLIB_EXPORTS)
```

- `PRIVATE`：仅在编译 `mylib` 时定义 `MYLIB_EXPORTS`，编译外部程序时该宏不存在
- 这样，同一个 `add.h` 在编译库时自动展开为 `dllexport`，在被引用时自动展开为 `dllimport`

> 💡 这是 Windows 动态库开发的常见模式——库作者只需维护一份头文件，通过 CMake 控制宏的有无，自动适配导出/导入两种场景。

然后在编译过程中会产生成一个.lib一个.dll文件，在Cmake里链接lib文件，供编译使用，但是在执行的时候需要使用到.dll文件，.dll文件和.exe文件放在同一个目录下

![[file-20260728144753240.png]]

# Cmake的跨平台特性

## C++代码的编译

![[file-20260728152319072.png]]

C++ 源代码从 `.cpp` 到最终可执行文件，需要经历**四个阶段**，每个阶段由不同的工具完成：

### 1. 预处理（Preprocessing）

```bash
g++ -E xxx.cpp -o xxx.i
```

处理以 `#` 开头的指令，包括：
- **展开头文件**：`#include "add.h"` → 把 `add.h` 的内容原封不动插入
- **宏替换**：`#define PI 3.14` → 代码中所有 `PI` 替换为 `3.14`
- **删除注释**：去掉所有 `//` 和 `/* */` 内容

输出 `.i` 文件，本质还是 C++ 代码，只是被"展开"和"清理"过了。

### 2. 编译（Compilation）

```bash
g++ -S xxx.i -o xxx.s
```

将预处理后的 `.i` 文件翻译成**汇编语言**：
- 检查语法、类型是否正确
- 生成对应目标平台的汇编指令

输出 `.s` 文件，是人可读的汇编代码。

### 3. 汇编（Assembly）

```bash
g++ -c xxx.s -o xxx.o
```

将汇编代码翻译成**机器码**，生成目标文件：
- 每个 `.cpp` 文件独立编译，各自生成一个 `.o` 文件
- 此时函数调用（如 `add(1,2)`）还未解析，只是记下了"需要 `add` 这个符号"

输出 `.o` 文件（Windows 下为 `.obj`），是二进制格式但还不能运行。

### 4. 链接（Linking）

```bash
g++ add.o main.o -o main
```

将多个 `.o` 文件和库文件合并成最终可执行文件：
- **符号解析**：`main.o` 中调用了 `add`，链接器在 `add.o` 中找到其实现，将两者"缝合"
- **地址重定位**：给所有函数和变量分配最终的内存地址

> 💡 上图中 `add.h` 被 `main.cpp` 引用，预处理时展开进 `main.i`，最终链接阶段 `main.o` 和 `add.o` 合并，`add(1,2)` 的调用才真正指向了 `add` 函数的实现。

![[file-20260728154212776.png]]

## Makefile实现(Linux)

### Makefile 语法基础

Makefile 的核心规则很简单：**目标 : 依赖 → 执行命令**

```makefile
目标 : 依赖1 依赖2
	执行命令（必须用 Tab 缩进，不能用空格）
```

Make 会检查：**目标文件是否比依赖文件新？**
- **是** → 跳过，什么都不做（认为已经是最新的）
- **否** → 重新执行命令，更新目标

此外，还可以用变量简化书写：

```makefile
CC = g++
CFLAGS = -Wall

main: main.o
	$(CC) $(CFLAGS) main.o -o main
```

### Makefile 详解

![[file-20260728155154813.png]]

这个 Makefile 完整实现了上一节中 C++ 编译的**四个阶段**，采用**自底向上**的依赖链：

```makefile
# 第1阶段：链接（最终目标，写在最前面）
main: main.o add.o
	g++ main.o add.o -o main

# 第3阶段：汇编
main.o add.o: main.s add.s
	g++ -c main.s -o main.o
	g++ -c add.s -o add.o

# 第2阶段：编译
main.s add.s: main.i add.i
	g++ -S main.i -o main.s
	g++ -S add.i -o add.s

# 第1阶段：预处理（最底层，最先执行）
main.i add.i: main.cpp add.cpp
	g++ -E main.cpp -o main.i
	g++ -E add.cpp -o add.i
```

**执行流程**（Make 会自动推导依赖顺序）：

```
main.cpp ──→ main.i ──→ main.s ──→ main.o ──┐
                                              ├──→ main（可执行文件）
add.cpp  ──→ add.i  ──→ add.s  ──→ add.o  ──┘
```

> 💡 第一次运行时，所有 `.i` `.s` `.o` 都不存在，Make 会从最底层的预处理开始，逐级向上构建。第二次运行时，如果 `.cpp` 没有修改，Make 发现目标已是最新的，直接跳过，这就是 Make 的**增量编译**优势。


## CMake的跨平台统一

![[file-20260728150759485.png]]

### 核心思路：写一次，到处构建

CMake 本身**不直接编译代码**，它是一个**构建系统的生成器**。你只需要写一份 `CMakeLists.txt`，CMake 会根据当前操作系统自动生成对应的构建文件：

| 平台 | CMake 生成的构建文件 | 构建工具 | 最终产物 |
|------|---------------------|---------|---------|
| Linux / macOS | `Makefile` | `make` | `xxx`（ELF 可执行文件） |
| Windows | `.sln`（Visual Studio 解决方案） | MSBuild | `xxx.exe` |

### 工作流程

```
CMakeLists.txt
      │
      ▼
   cmake 路径
      │
      ├──── Linux/macOS ──→ Makefile ──→ make ──→ xxx
      │
      └──── Windows ──────→ xxx.sln ────→ MSBuild ──→ xxx.exe
```

**1. 配置阶段**（生成构建文件）：

```bash
# 在项目build目录下执行
cmake -B build        # 在 build 文件夹中生成平台对应的构建文件
```

- Linux：`build/` 下生成 `Makefile`
- Windows：`build/` 下生成 `.sln` 和 `.vcxproj`

**2. 构建阶段**（编译链接）：

```bash
cmake --build build   # 跨平台统一命令，无需手动调用 make 或 MSBuild
```

- Linux：实际执行 `cd build && make`
- Windows：实际执行 `msbuild build\xxx.sln`

> 💡 如果不用 CMake，你得在 Linux 写 `Makefile`，在 Windows 写 `.vcxproj` 或手动调用 `cl.exe`。CMake 让你**用一份 `CMakeLists.txt` 覆盖所有平台**，这就是图中"CMake 大一统"的含义。