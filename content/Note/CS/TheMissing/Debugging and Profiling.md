# 调试与性能分析

> 来源：[Missing Semester 2026 · Debugging and Profiling](https://missing-semester-cn.github.io/2026/debugging-profiling/)（中文翻译）

编程的一条黄金法则是：**代码不会按照你期望的方式运行，而是按照你告诉它的方式运行**。弥合这一差距有时是相当困难的事。在本节课中，我们将介绍处理有 bug 和高资源占用代码的有用技术：**调试（debugging）**与**性能分析（profiling）**。

---

## 调试（Debugging）

### Printf 调试与日志（Logging）

> "最有效的调试工具仍然是仔细的思考，配合恰到好处的 print 语句。" —— Brian Kernighan，《Unix for Beginners》。

调试程序的第一种方法，是在你发现问题的位置周围添加 print 语句，然后不断迭代，直到你提取到足够的信息来理解问题所在。

第二种方法是在程序中使用**日志（logging）**，而不是临时拼凑的 print 语句。日志本质上就是"更用心的打印"，通常通过日志框架完成，内置支持：

- 将日志（或日志的子集）定向到其他输出位置；
- 设置严重级别（如 INFO、DEBUG、WARN、ERROR 等），并允许你据此过滤输出；
- 支持对日志条目相关数据进行**结构化记录**，事后可以更容易地提取。

在编程时，你也应该主动添加日志语句，这样调试所需的数据可能已经就位！而且事实上，一旦你用 print 语句找到并修复了问题，在删除它们之前，把这些 print 转换成正式的日志语句通常是值得的。这样，将来如果发生类似的 bug，你无需修改代码就已经拥有所需的诊断信息。

> **第三方日志**：许多程序支持 `-v` 或 `--verbose` 标志，以便在运行时打印更多信息。这对于找出某个命令失败的原因很有用。有些程序甚至允许重复该标志以获得更详细的输出。在调试服务（数据库、Web 服务器等）的问题时，请检查它们的日志——在 Linux 上通常位于 `/var/log/`。使用 `journalctl -u <service>` 查看 systemd 服务的日志。对于第三方库，请检查它们是否支持通过环境变量或配置进行调试日志输出。

### 调试器（Debuggers）

当你明确知道要打印什么，并且可以轻松修改和重新运行代码时，Print 调试很好用。但当你**不确定需要什么信息**、bug 只在**难以复现的条件**下出现，或者**修改并重启程序代价高昂**（启动时间长、需要重建复杂状态等）时，调试器就变得有价值了。

调试器是让你在程序运行时与之交互的程序，使你能够：

- 在到达某一行时暂停执行。
- 一次一条指令地逐步执行。
- 在崩溃后检查变量的值。
- 当给定条件满足时条件性暂停执行。
- 以及许多其他高级功能。

大多数编程语言都支持（或自带）某种形式的调试器。最通用的是**通用调试器**（general-purpose debuggers），如 [`gdb`](https://www.gnu.org/software/gdb/)（GNU 调试器）和 [`lldb`](https://lldb.llvm.org/)（LLVM 调试器），它们可以调试任何原生二进制程序。许多语言还有**语言专属调试器**，与运行时结合得更紧密（如 Python 的 pdb 或 Java 的 jdb）。

`gdb` 是 C、C++、Rust 等编译语言的事实标准调试器。它可以探测几乎任何进程，并获取其当前机器状态：寄存器、栈、程序计数器等。

一些有用的 GDB 命令：

- `run` — 启动程序
- `b {function}` 或 `b {file}:{line}` — 设置断点
- `c` — 继续执行
- `step` / `next` / `finish` — 步入 / 步过 / 步出
- `p {variable}` — 打印变量的值
- `bt` — 显示回溯（调用栈）
- `watch {expression}` — 当值发生变化时中断

> 建议使用 GDB 的 TUI 模式（`gdb -tui`，或在 GDB 内按 `Ctrl-x a`），可以分屏显示源代码和命令提示符。

### 记录-回放调试（Record-Replay Debugging）

一些最令人沮丧的 bug 是**海森堡 bug（Heisenbug）**：当你试图观察它们时，它们似乎消失或改变了行为。竞态条件、依赖时序的 bug，以及只在特定系统条件下出现的问题，都属于这一类。传统调试在这里常常毫无用处，因为重新运行程序会产生不同的行为（例如，print 语句可能会把代码拖慢到竞态不再发生）。

**记录-回放调试**通过记录程序的执行过程，并允许你按需多次确定性重放来解决这个问题。更棒的是，你还可以在执行中**反向**遍历，以精确找到出问题的地方。

[rr](https://rr-project.org/) 是 Linux 上一个强大的工具，可以记录程序执行，并支持完整调试能力的确定性重放。它与 GDB 配合工作，所以你已经有现成的接口了。

基本用法：

```bash
# 记录一次程序执行
rr record ./my_program

# 重放记录（会打开 GDB）
rr replay
```

神奇之处发生在重放过程中。因为执行是确定性的，你可以使用**反向调试**命令：

- `reverse-continue`（`rc`）— 反向运行直到命中断点
- `reverse-step`（`rs`）— 反向单步一行
- `reverse-next`（`rn`）— 反向单步，跳过函数调用
- `reverse-finish` — 反向运行直到进入当前函数

这在调试中极其强大。假设你遇到崩溃——不必猜测 bug 在哪里并设置断点，你可以：

1. 运行到崩溃点
2. 检查被破坏的状态
3. 在被破坏的变量上设置观察点（watchpoint）
4. 使用 `reverse-continue` 精确找到它是在哪里被破坏的

**何时使用 rr：**

- 间歇性失败的随机测试（flaky tests）
- 竞态条件和线程 bug
- 难以复现的崩溃
- 任何你希望"回到过去"的 bug

> 注意：rr 只能在 Linux 上工作，并且需要硬件性能计数器。在未暴露这些计数器的虚拟机中（如大多数 AWS EC2 实例）无法使用，并且不支持 GPU 访问。在 macOS 上，可以看看 [Warpspeed](https://warpspeed.dev/)。

> **rr 与并发**：由于 rr 确定性记录执行，它会序列化线程调度。这意味着一些依赖特定时序的竞态条件在 rr 下可能不会显现。rr 对调试竞态仍然有用——一旦你捕获到一次失败的运行，就可以可靠地重放它——但你可能需要多次录制尝试才能捕捉到间歇性 bug。对于不涉及并发的 bug，rr 最为出色：你总能复现精确的执行过程，并使用反向调试来追查数据破坏。

### 系统调用追踪（System Call Tracing）

有时你需要了解程序如何与操作系统交互。程序通过[系统调用](https://en.wikipedia.org/wiki/System_call)向内核请求服务——打开文件、分配内存、创建进程等。追踪这些调用可以揭示程序为什么挂起、正在尝试访问哪些文件，或者把时间花在等待什么上。

#### strace（Linux）与 dtruss（macOS）

[`strace`](https://www.man7.org/linux/man-pages/man1/strace.1.html) 让你观察程序发出的每一个系统调用：

```bash
# 追踪所有系统调用
strace ./my_program

# 只追踪与文件相关的调用
strace -e trace=file ./my_program

# 跟随子进程（对于启动其他程序的程序很重要）
strace -f ./my_program

# 追踪正在运行的进程
strace -p <PID>

# 显示计时信息
strace -T ./my_program
```

> 在 macOS 和 BSD 上，使用 [`dtruss`](https://www.manpagez.com/man/1/dtruss/)（封装了 `dtrace`）实现类似功能：

> 要深入了解 `strace`，请看 Julia Evans 的精彩 [strace zine](https://jvns.ca/strace-zine-unfolded.pdf)。

#### bpftrace 与 eBPF

[eBPF](https://ebpf.io/)（扩展伯克利包过滤器）是一项强大的 Linux 技术，允许在内核中运行沙箱程序。[`bpftrace`](https://github.com/iovisor/bpftrace) 为编写 eBPF 程序提供了高级语法。这些是运行在内核中的任意程序，因此具有巨大的表达能力（虽然语法有点像笨拙的 awk）。它们最常见的用途是调查正在调用哪些系统调用，包括聚合（如计数或延迟统计）或内省（甚至过滤）系统调用参数。

```bash
# 追踪系统范围的文件打开（立即打印）
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# 按名称统计系统调用（按 Ctrl-C 打印汇总）
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_* { @[probe] = count(); }'
```

不过，你也可以使用像 [`bcc`](https://github.com/iovisor/bcc) 这样的工具链直接用 C 编写 eBPF 程序，它自带[许多实用的工具](https://www.brendangregg.com/blog/2015-09-22/bcc-linux-4.3-tracing.html)，比如打印磁盘操作延迟分布的 `biosnoop`，或打印所有打开文件的 `opensnoop`。

`strace` 的优点是"上手即用"很轻松；而当需要**更低开销**、想**在内核函数层面追踪**、或需要**做某种聚合**时，应该用 `bpftrace`。注意 `bpftrace` 必须以 `root` 身份运行，而且它通常监控整个内核，而不仅仅是一个特定进程。要针对特定程序，可以按命令名或 PID 过滤：

```bash
# 按命令名过滤（按 Ctrl-C 打印汇总）
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_* /comm == "bash"/ { @[probe] = count(); }'

# 使用 -c 从启动时追踪特定命令（cpid = 子进程 PID）
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_* /pid == cpid/ { @[probe] = count(); }' -c 'ls -la'
```

`-c` 标志会运行指定命令并将其 PID 设为 `cpid`，这对于从程序启动那一刻开始追踪非常有用。当被追踪的命令退出时，bpftrace 会打印聚合结果。

#### 网络调试

对于网络问题，[`tcpdump`](https://www.man7.org/linux/man-pages/man1/tcpdump.1.html) 和 [Wireshark](https://www.wireshark.org/) 让你捕获和分析网络数据包：

```bash
# 捕获 80 端口的数据包
sudo tcpdump -i any port 80

# 捕获并保存到文件，供 Wireshark 分析
sudo tcpdump -i any -w capture.pcap
```

对于 HTTPS 流量，加密使 tcpdump 用处不大。[mitmproxy](https://mitmproxy.org/) 之类的工具可以作为拦截代理来检查加密流量。对于调试 Web 应用的 HTTPS 请求，**浏览器开发者工具（Network 标签页）**通常是最简单的方式——它们会显示解密后的请求/响应数据、头部和时序。

### 内存调试（Memory Debugging）

内存 bug——缓冲区溢出、释放后使用（use-after-free）、内存泄漏——是最危险且最难调试的一类问题。它们通常不会立即崩溃，而是以某种方式破坏内存，导致很久之后才出现问题。

#### Sanitizer

查找内存 bug 的一种方法是使用 **sanitizer**，它们是编译器特性，会在运行时检测错误。例如，广泛使用的 **AddressSanitizer（ASan）** 可以检测：

- 缓冲区溢出（栈、堆和全局）
- 释放后使用（use-after-free）
- 返回后使用（use-after-return）
- 内存泄漏

```bash
# 使用 AddressSanitizer 编译
gcc -fsanitize=address -g program.c -o program
./program
```

还有很多有用的 sanitizer：

- **ThreadSanitizer（TSan）**：检测多线程代码中的数据竞争（`-fsanitize=thread`）
- **MemorySanitizer（MSan）**：检测对未初始化内存的读取（`-fsanitize=memory`）
- **UndefinedBehaviorSanitizer（UBSan）**：检测未定义行为，如整数溢出（`-fsanitize=undefined`）

Sanitizer 需要重新编译，但速度足够快，可以用于 CI 流水线和日常开发。

#### Valgrind：当你无法重新编译时

[Valgrind](https://valgrind.org/) 则是在类似虚拟机的方式下运行你的程序来检测内存错误。它比 sanitizer 慢，但不需要重新编译：

```bash
valgrind --leak-check=full ./my_program
```

在以下情况下使用 Valgrind：

- 你没有源代码
- 你无法重新编译（第三方库）
- 你需要 sanitizer 没有提供的特定工具

Valgrind 实际上是一个功能非常强大的受控执行环境，稍后讨论性能分析时我们还会再见到它！

### AI 辅助调试

大型语言模型（LLM）已经成为出奇有用的调试助手。它们擅长某些调试任务，与传统工具互补。

**LLM 擅长的方面：**

- **解释晦涩的错误信息**：编译器错误，尤其是 C++ 模板或 Rust 借用检查器产生的错误，出了名的晦涩。LLM 可以把它们翻译成通俗易懂的语言并建议修复方法。

- **跨越语言和抽象边界**：如果你在调试一个跨多种语言的问题（比如，一个 C 库的 bug 通过 Python 绑定显现出来），LLM 可以帮助你梳理不同层次。它们特别擅长理解 FFI 边界、构建系统问题和跨语言调试（例如："我的程序报错了，但我认为是某个依赖里的 bug 导致的"）。

- **将症状与根因关联**："我的程序运行正常但内存占用比预期高 10 倍"——这类模糊的症状 LLM 可以帮助排查，提出可能的原因以及该查看什么。

- **分析崩溃转储和堆栈跟踪**：粘贴一段堆栈跟踪，问它可能导致的原因。

> **关于调试符号的说明**：要获得有意义的堆栈跟踪和调试信息，请确保你的二进制文件（以及链接的库）使用调试符号编译（`-g` 标志）。调试信息通常以 DWARF 格式存储。此外，使用帧指针编译（`-fno-omit-frame-pointer`）可以使堆栈跟踪更可靠，尤其是对性能分析工具。没有这些，堆栈跟踪可能只显示内存地址或不完整。这对原生编译的程序（C++、Rust）比 Python 或 Java 更重要。

**需要记住的局限性：**

- LLM 可能会编造听起来合理但错误的解释
- 它们可能建议掩盖 bug 而不是真正修复它的方案
- 始终用实际的调试工具验证它们的建议
- 它们最好作为理解代码的**补充**，而不是替代

> 这与开发环境课程中介绍的[通用 AI 编码能力](/2026/development-environment/#ai-powered-development)不同。这里我们专门讨论把 LLM 当作调试辅助工具。

---

## 性能分析（Profiling）

即使你的代码功能上符合预期，如果它占用了你所有的 CPU 或内存，那也不够好。算法课经常教授大 _O_ 记号，但不会教你如何在程序里找到热点。既然[过早优化是万恶之源](https://wiki.c2.com/?PrematureOptimization)，你应该学习性能分析器和监控工具。它们会帮助你理解程序的哪些部分占用了大部分时间和/或资源，从而可以专注优化这些部分。

### 计时（Timing）

衡量性能最简单的方法就是计时。在很多场景下，只要打印代码在两点之间花的时间就够了。

不过，墙上时钟时间（wall clock time）可能有误导性，因为你的计算机可能同时运行其他进程，或在等待事件发生。`time` 命令区分了 **Real**、**User** 和 **Sys** 三种时间：

- **Real** — 从开始到结束的墙上时钟时间，包括等待所花的时间
- **User** — CPU 运行用户代码所花的时间
- **Sys** — CPU 运行内核代码所花的时间

```bash
$ time curl https://missing.csail.mit.edu &> /dev/null
real	0m0.272s
user	0m0.079s
sys	    0m0.028s
```

这里请求花了将近 300 毫秒（real time），但 CPU 时间只有 107 毫秒（user + sys）。其余时间都花在网络等待上。

### 资源监控（Resource Monitoring）

有时分析程序性能的第一步是了解它的实际资源消耗。程序在资源受限时往往运行缓慢。

- **通用监控**：[`htop`](https://htop.dev/) 是 `top` 的改进版，以友好的方式呈现当前运行进程的各项统计信息。有用的按键：`<F6>` 排序进程，`t` 显示树形层次，`h` 切换线程。还有 [`btop`](https://github.com/aristocratos/btop) 监控的东西多得多。
- **I/O 操作**：[`iotop`](https://www.man7.org/linux/man-pages/man8/iotop.8.html) 显示实时的 I/O 使用信息。
- **内存使用**：[`free`](https://www.man7.org/linux/man-pages/man1/free.1.html) 显示总的空闲和已用内存。
- **打开的文件**：[`lsof`](https://www.man7.org/linux/man-pages/man8/lsof.8.html) 列出进程打开的文件信息。常用于检查哪个进程打开了某个特定文件。
- **网络连接**：[`ss`](https://www.man7.org/linux/man-pages/man8/ss.8.html) 让你监控网络连接。一个常见用例是找出哪个进程占用了某个端口：`ss -tlnp | grep :8080`。
- **网络用量**：[`nethogs`](https://github.com/raboof/nethogs) 和 [`iftop`](https://pdw.ex-parrot.com/iftop/) 是监控每个进程网络用量的好用的交互式 CLI 工具。

### 可视化性能数据

人类在图表中识别模式的速度远快于数字表格。分析性能时，绘制数据往往能揭示原始数字中不可见的趋势、尖峰和异常。

**让数据可绘制**：在添加用于调试的 print 或 log 语句时，考虑把输出格式化为以后容易画图的形式。简单的时间戳加数值 CSV 格式（`1705012345,42.5`）比散文式的句子容易绘制得多。JSON 结构化日志也可以花很少力气解析和绘制。换句话说，用[整洁的方式](https://vita.had.co.nz/papers/tidy-data.pdf)记录你的数据。

**用 gnuplot 快速绘图**：对于简单的命令行绘图，[`gnuplot`](http://www.gnuplot.info/) 可以直接从数据文件生成图表：

```bash
# 绘制简单的 CSV（时间戳,数值）
gnuplot -e "set datafile separator ','; plot 'latency.csv' using 1:2 with lines"
```

**用 matplotlib 和 ggplot2 迭代探索**：对于更深入的分析，Python 的 [`matplotlib`](https://matplotlib.org/) 和 R 的 [`ggplot2`](https://ggplot2.tidyverse.org/) 支持迭代探索。与一次性绘图不同，这些工具让你快速切片和变换数据来验证假设。ggplot2 的**分面图（facet plots）**尤其强大——你可以按类别把单个数据集拆分成多个子图（例如，按端点或一天中的时段对请求延迟分面），从而发现隐藏的模式。

**示例用例：**

- 绘制请求延迟随时间的变化，可以揭示周期性变慢（垃圾回收、cron 任务、流量模式），而这些是原始百分位数掩盖的
- 可视化增长数据结构的插入时间可以暴露算法复杂度问题——向量插入图会在底层数组扩容时显示特征性尖峰
- 按不同维度（请求类型、用户群、服务器）对指标分面，往往能揭示"系统级"的问题其实只局限于某一类

### CPU 性能分析器（CPU Profilers）

大多数时候人们说到 _profiler_ 指的是 _CPU profiler_。主要有两种类型：

- **追踪型（tracing）性能分析器**：记录程序做的每一次函数调用
- **采样型（sampling）性能分析器**：周期性探测程序（通常每毫秒一次）并记录程序栈

采样型性能分析器开销更低，在生产环境中通常更受青睐。

#### perf：采样性能分析器

[`perf`](https://www.man7.org/linux/man-pages/man1/perf.1.html) 是 Linux 标准性能分析器。它可以在不重新编译的情况下分析任何程序。

`perf stat` 让你快速概览时间花在哪里：

```bash
$ perf stat ./slow_program

 Performance counter stats for './slow_program':

         3,210.45 msec task-clock                #    0.998 CPUs utilized
               12      context-switches          #    3.738 /sec
                0      cpu-migrations            #    0.000 /sec
              156      page-faults               #   48.587 /sec
   12,345,678,901      cycles                    #    3.845 GHz
    9,876,543,210      instructions              #    0.80  insn per cycle
    1,234,567,890      branches                  #  384.532 M/sec
       12,345,678      branch-misses             #    1.00% of all branches
```

真实程序的性能分析输出包含大量信息。人类是视觉动物，很不擅长阅读大量数字。[火焰图（Flame graphs）](https://www.brendangregg.com/flamegraphs.html) 是一种让性能分析数据更容易理解的图表。

火焰图在 Y 轴显示函数调用层次，在 X 轴按比例显示耗时。它是交互式的——可以点击放大程序的特定部分。

![[flamegraph_cpu_bash.svg]]

*上图：CPU 火焰图示例（来源：[Brendan Gregg](https://www.brendangregg.com/FlameGraphs/cpu-bash-flamegraph.svg)）*

从 `perf` 数据生成火焰图：

```bash
# 记录性能数据
perf record -g ./my_program

# 生成火焰图（需要 flamegraph 脚本）
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

> 可以考虑使用 [Speedscope](https://www.speedscope.app/) 作为交互式网页版火焰图查看器，或使用 [Perfetto](https://perfetto.dev/) 进行全面的系统级分析。

#### Valgrind 的 Callgrind：追踪型性能分析器

[`callgrind`](https://valgrind.org/docs/manual/cl-manual.html) 是一个记录程序调用历史和指令计数的性能分析工具。与采样型性能分析器不同，它提供精确的调用次数，并能显示调用者与被调用者之间的关系：

```bash
# 使用 callgrind 运行
valgrind --tool=callgrind ./my_program

# 用 callgrind_annotate（文本）或 kcachegrind（GUI）分析
callgrind_annotate callgrind.out.<pid>
kcachegrind callgrind.out.<pid>
```

Callgrind 比采样型性能分析器慢，但提供精确的调用次数，并且可以（用 `--cache-sim=yes`）模拟缓存行为，如果你需要这些信息的话。

> 如果你使用特定的语言，可能会有更专门的性能分析器。例如，Python 有 [`cProfile`](https://docs.python.org/3/library/profile.html) 和 [`py-spy`](https://github.com/benfred/py-spy)，Go 有 [`go tool pprof`](https://pkg.go.dev/cmd/pprof)，Rust 有 [`cargo-flamegraph`](https://github.com/flamegraph-rs/flamegraph)（实际上对任何编译型程序都适用！）。

### 内存性能分析器（Memory Profilers）

内存性能分析器帮助你理解程序随时间的内存使用情况，并发现内存泄漏。

#### Valgrind 的 Massif

[`massif`](https://valgrind.org/docs/manual/ms-manual.html) 分析堆内存使用情况：

```bash
valgrind --tool=massif ./my_program
ms_print massif.out.<pid>
```

这可以显示你随时间的堆使用情况，帮助识别内存泄漏和过度分配。

> 对 Python，[`memory-profiler`](https://pypi.org/project/memory-profiler/) 提供逐行的内存使用信息。

### 基准测试（Benchmarking）

当你需要比较不同实现或工具的性能时，[`hyperfine`](https://github.com/sharkdp/hyperfine) 是给命令行程序做基准测试的绝佳工具：

```bash
$ hyperfine --warmup 3 'fd -e jpg' 'find . -iname "*.jpg"'
Benchmark #1: fd -e jpg
  Time (mean ± σ):      51.4 ms ±   2.9 ms    [User: 121.0 ms, System: 160.5 ms]
  Range (min … max):    44.2 ms …  60.1 ms    56 runs

Benchmark #2: find . -iname "*.jpg"
  Time (mean ± σ):      1.126 s ±  0.101 s    [User: 141.1 ms, System: 956.1 ms]
  Range (min … max):    0.975 s …  1.287 s    10 runs

Summary
  'fd -e jpg' ran
   21.89 ± 2.33 times faster than 'find . -iname "*.jpg"'
```

> 对于 Web 开发，浏览器开发者工具内置了优秀的性能分析器。参见 [Firefox Profiler](https://profiler.firefox.com/docs/) 和 [Chrome DevTools](https://developers.google.com/web/tools/chrome-devtools/rendering-tools) 的文档。

---

## 练习（Exercises）

### 调试

1. **调试排序算法**：下面的伪代码实现了归并排序但包含一个 bug。用你选择的语言实现它，然后使用调试器（gdb、lldb、pdb 或你 IDE 的调试器）找到并修复这个 bug。

```python
function merge_sort(arr):
    if length(arr) <= 1:
        return arr
    mid = length(arr) / 2
    left = merge_sort(arr[0..mid])
    right = merge_sort(arr[mid..end])
    return merge(left, right)

function merge(left, right):
    result = []
    i = 0, j = 0
    while i < length(left) AND j < length(right):
        if left[i] <= right[j]:
            append result, left[i]
            i = i + 1
        else:
            append result, right[i]
            j = j + 1
    append remaining elements from left and right
    return result
```

测试向量：`merge_sort([3, 1, 4, 1, 5, 9, 2, 6])` 应返回 `[1, 1, 2, 3, 4, 5, 6, 9]`。使用断点并单步执行 merge 函数，找出哪里选错了元素。

2. 安装 [`rr`](https://rr-project.org/) 并使用反向调试来找到一个数据破坏 bug。把这段程序保存为 `corruption.c`：

```c
#include <stdio.h>

typedef struct {
    int id;
    int scores[3];
} Student;

Student students[2];

void init() {
    students[0].id = 1001;
    students[0].scores[0] = 85;
    students[0].scores[1] = 92;
    students[0].scores[2] = 78;

    students[1].id = 1002;
    students[1].scores[0] = 90;
    students[1].scores[1] = 88;
    students[1].scores[2] = 95;
}

void curve_scores(int student_idx, int curve) {
    for (int i = 0; i < 4; i++) {
        students[student_idx].scores[i] += curve;
    }
}

int main() {
    init();
    printf("=== Initial state ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    curve_scores(0, 5);

    printf("\n=== After curving ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    if (students[1].id != 1002) {
        printf("\nERROR: Student 1's ID was corrupted! Expected 1002, got %d\n",
               students[1].id);
        return 1;
    }
    return 0;
}
```

用 `gcc -g corruption.c -o corruption` 编译并运行它。学生 1 的 ID 被破坏了，但破坏发生在只碰学生 0 的函数里。使用 `rr record ./corruption` 和 `rr replay` 找出元凶。在 `students[1].id` 上设置观察点，并在破坏发生后使用 `reverse-continue` 精确找出是哪一行代码覆盖了它。

3. 用 AddressSanitizer 调试一个内存错误。保存为 `uaf.c`：

```c
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int main() {
    char *greeting = malloc(32);
    strcpy(greeting, "Hello, world!");
    printf("%s\n", greeting);

    free(greeting);

    greeting[0] = 'J';
    printf("%s\n", greeting);

    return 0;
}
```

首先不带 sanitizer 编译运行：`gcc uaf.c -o uaf && ./uaf`。它可能看起来正常工作。然后用 AddressSanitizer 编译：`gcc -fsanitize=address -g uaf.c -o uaf && ./uaf`。阅读错误报告。ASan 发现了什么 bug？修复它指出的问题。

4. 使用 `strace`（Linux）或 `dtruss`（macOS）追踪 `ls -l` 等命令发出的系统调用。它做了哪些系统调用？尝试追踪一个更复杂的程序，看看它打开了哪些文件。

5. 使用 LLM 帮助调试一条晦涩的错误信息。试着复制一条编译器错误（尤其是 C++ 模板或 Rust 的），请它给出解释和修复。也可以把 `strace` 或 address sanitizer 的部分输出喂给它。

### 性能分析

1. 使用 `perf stat` 为你选择的程序获取基本性能统计信息。不同的计数器分别代表什么意思？

2. 使用 `perf record` 进行性能分析。保存为 `slow.c`：

```c
#include <math.h>
#include <stdio.h>

double slow_computation(int n) {
    double result = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < 1000; j++) {
            result += sin(i * j) * cos(i + j);
        }
    }
    return result;
}

int main() {
    double r = 0;
    for (int i = 0; i < 100; i++) {
        r += slow_computation(1000);
    }
    printf("Result: %f\n", r);
    return 0;
}
```

用调试符号编译：`gcc -g -O2 slow.c -o slow -lm`。运行 `perf record -g ./slow`，然后 `perf report` 查看时间花在哪里。尝试用 flamegraph 脚本生成火焰图。

3. 使用 `hyperfine` 对同一任务的两种实现做基准测试（例如 `find` vs `fd`、`grep` vs `ripgrep`，或你自己的代码的两个版本）。

4. 运行资源密集型程序时用 `htop` 监控系统。尝试用 `taskset` 限制进程可以使用的 CPU：`taskset --cpu-list 0,2 stress -c 3`。为什么 `stress` 没有使用三个 CPU？

5. 一个常见问题是你要监听的端口已被另一个进程占用。学习如何找出那个进程：首先执行 `python -m http.server 4444` 在 4444 端口启动一个简易 Web 服务器。在另一个终端运行 `ss -tlnp | grep 4444` 找到进程。用 `kill <PID>` 终止它。

---

*原文链接：[Edit this page](https://github.com/missing-semester-cn/missing-semester-cn/blob/master/_2026/debugging-profiling.md) · 许可协议：[CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0)*
