# 4. LPBQ INT8 实验路径

> [!warning] 实验性功能
> LPBQ 路径是研究性的，代码中包含大量实验开关和诊断逻辑。本章只做概述。

## 什么是 LPBQ？

LPBQ（Low-Precision Block Quantization）是一种 W4A8 方案：
- **权重**：INT4，但使用 LPBQ 分组量化（比普通 Q4_0 更精细）
- **激活值**：INT8（有符号）
- **HMX**：做 INT8 矩阵乘法

与 [[../w4-w8-a16/00-index|W4/W8 A16]] 的区别：A16 的激活值是 FP16，LPBQ 的激活值是 INT8。INT8 HMX 的吞吐量比 FP16 HMX 更高。

## 运行模式

通过 `switch_llm_inference_route.ps1` 的 `-Mode` 参数选择：

```powershell
-Mode lpbq_int8    # LPBQ INT8 路径
-Mode lpbq_r4      # LPBQ + R4 修正路径
```

对应 `op_reg.h` 中的 mode flags：

```c
LLM_NPU_MODE_LPBQ_INT8        = 1 << 3,
LLM_NPU_MODE_LPBQ_R4          = 1 << 4,
LLM_NPU_MODE_LPBQ_R4_FOLDED_INPUT_SCALE = 1 << 5,
```

## R4 修正

R4 是对 LPBQ 量化误差的一种修正方案。代码中有多种 R4 变体：

| Flag | 含义 |
|------|------|
| `LPBQ_R4` | 基础 R4 修正 |
| `LPBQ_R4_STRUCTURED_FWHT` | 结构化 FWHT（快速 Walsh-Hadamard 变换）sidecar |
| `LPBQ_R4_HMX_DENSE_FP16_SIDECAR` | 预打包 FP16 HMX 密集 R4 tile |
| `LPBQ_R4_FULL_U8_SAFE` | 全 U8 安全路径 |

这些变体在 `build_pure_fp16.ps1` 中通过参数控制，不需要修改源码。

## 操作码

LPBQ 使用独立的操作码：

```c
HTP_OPS_MAT_MUL_LPBQ_A8W8  // 在 pure-fp16 的 op_reg.h 中定义
```

与 W4/W8 的 `HTP_OPS_MAT_MUL_PERMUTED_W4D16A32` 不同，LPBQ 有自己独立的 DSP kernel 路径。

## 与 Pure FP16 的关系

LPBQ 是 pure-fp16 项目中的**实验分支**，不是独立项目。它共享：
- 同一个 `mat_mul.c`（LPBQ kernel 在同一个文件中）
- 同一个构建和部署脚本
- 同一个 server 和测试框架

> [!tip] 如果你只关心 FP16 路径
> 可以完全忽略 LPBQ 相关的代码和参数。默认的 `-Mode pure_fp16` 走的就是纯 FP16 路径。
