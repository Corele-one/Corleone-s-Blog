# 1. 运行环境与整体架构

## 环境分层

```
┌─────────────────────────────────────────────┐
│  Windows (你的开发机)                         │
│  PowerShell 脚本、adb push、python tools     │
├─────────────────────────────────────────────┤
│  WSL2 Ubuntu 22.04                          │
│  CMake + Ninja 构建、Hexagon SDK、NDK       │
├─────────────────────────────────────────────┤
│  Android 设备 (Snapdragon 8 Gen 2+)        │
│  AArch64 host binary ↔ FastRPC ↔ DSP skel  │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  Hexagon DSP (HTP)                   │   │
│  │  HMX (矩阵加速) + HVX (向量计算)     │   │
│  │  VTCM (快速片上存储)                  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Windows 层

你直接操作的层。PowerShell 脚本负责：
- 调用 WSL 构建
- 通过 `adb push` 把编译产物推送到设备
- 通过 `adb shell` 在设备上执行命令
- 运行 Python 工具解析结果

### WSL2 层

交叉编译环境。因为目标是 Android ARM64 和 Hexagon DSP，所以需要：
- **Android NDK r25c**：提供 AArch64 交叉编译工具链
- **Hexagon SDK 6.x**：提供 Hexagon DSP 编译工具链和 FastRPC 框架
- **CMake + Ninja**：构建系统

WSL 里有一个环境脚本 `/root/llama-npu-env.sh`，它设置好所有路径变量（`ANDROID_NDK`、`HEXAGON_SDK_ROOT` 等）并提供 `build_cmake` 辅助函数。

### Android 设备层

运行编译好的二进制。设备上需要：
- `htp_ops_test`：standalone benchmark 可执行文件（AArch64）
- `libhtp_ops.so`：host-side FastRPC stub 共享库
- `libhtp_ops_skel.so`：DSP-side skeleton 共享库（推到 `cdsp/` 或 `dsp/` 子目录）

### Hexagon DSP 层

实际执行 Attention 计算的地方。DSP 有三种硬件单元：
- **HMX**（Hexagon Matrix eXtension）：做矩阵乘法，类似于 GPU 的 Tensor Core
- **HVX**（Hexagon Vector eXtension）：做向量运算，128 字节宽的 SIMD
- **VTCM**（Vector Tightly Coupled Memory）：DSP 片上快速存储，类似 GPU 的 shared memory

## 通信链路：FastRPC

```
Host (AArch64)                    DSP (Hexagon)
     │                                │
     │  FastRPC 调用                  
     │ ─────────────────────────────→ │
     │  (共享内存 rpcmem)               
     │                                │  op_executor.cc
     │                                │    ↓ 分发到具体 kernel
     │                                │  flash_attn.c
     │  ←─────────────────────────────│
     │  结果写回 rpcmem                 
```

图中的Host指的是SOC上的CPU
FastRPC 是 Qualcomm 提供的远程过程调用机制。host 端把参数和数据放在 **rpcmem**（host 和 DSP 共享的内存区域）中，通过 FastRPC 发送请求。DSP 端的 `commu.c` 接收请求，`op_executor.cc` 根据操作码分发到对应的 kernel。

## 源码目录结构

```
flashattention/
├── src/
│   ├── htp-ops-lib-main/          ← DSP kernel 和 host stub
│   │   ├── include/
│   │   │   ├── op_reg.h           ← 操作码枚举、参数结构体（ABI 定义）
│   │   │   ├── htp_ops.idl        ← FastRPC 接口定义
│   │   │   ├── message.h          ← host↔DSP 消息格式
│   │   │   └── dsp/
│   │   │       ├── hmx_utils.h    ← HMX 矩阵加速 helper
│   │   │       ├── hvx_math.h     ← HVX 数学函数（exp、softmax 等）
│   │   │       ├── dma_utils.h    ← DMA 传输 helper
│   │   │       └── vtcm_mgr.h     ← VTCM 管理
│   │   ├── src/
│   │   │   ├── host/
│   │   │   │   ├── op_export.c    ← host FastRPC wrapper
│   │   │   │   ├── session.c      ← DSP session 管理
│   │   │   │   └── test.c         ← standalone benchmark（Figure 8 入口）
│   │   │   └── dsp/
│   │   │       ├── commu.c        ← DSP 端 FastRPC 接收和分发
│   │   │       ├── op_executor.cc ← DSP operator 调度核心
│   │   │       ├── worker_pool.c  ← 多线程 worker 管理
│   │   │       ├── vtcm_mgr.cc    ← VTCM 分配管理
│   │   │       └── ops/
│   │   │           ├── flash_attn.c      ← ★ FlashAttention 主 kernel
│   │   │           ├── flash_attn_sp_hdim.c ← 非 64 倍数 head_dim fallback
│   │   │           └── mat_mul.c         ← 矩阵乘法 kernel
│   │   └── CMakeLists.txt
│   └── llama.cpp-npu-htp-backend/ ← llama.cpp 框架 + HTP backend
│       ├── ggml/src/ggml-htp/
│       │   └── htp-ops.cc         ← GGML op → HTP FastRPC 桥接
│       ├── examples/server/       ← HTTP server
│       └── tests/                 ← 正确性测试
├── tools/                         ← Python 分析工具
├── results/                       ← 测量结果（v73/v79 × baseline/lut-exp）
└── README.md
```

> [!tip] Obsidian 提示
> 后续章节中出现的代码路径都相对于 `projects/flashattention/`。

![[ec6d494ad6eadfe629211addd3c295b4_720.png]]
