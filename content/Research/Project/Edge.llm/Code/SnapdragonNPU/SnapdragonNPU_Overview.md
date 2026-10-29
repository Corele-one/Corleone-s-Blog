基于[Scaling LLM Test-Time Compute with Mobile NPU on Smartphones](https://dl.acm.org/doi/10.1145/3767295.3769382)这篇论文开源的两个repo:

[llama.cpp-npu(main)](https://github.com/haozixu/llama.cpp-npu)
[htp-ops.lib(op library)](https://github.com/haozixu/htp-ops-lib)

# Scaling LLM test-time

提出一个面向 Qualcomm Snapdragon NPU 的 end-to-end inference system，主要使用 **weight-only 4-bit fine-grained group quantization**，并做两类硬件感知优化。

第一，**hardware-aware tile quantization**：把 quantization group 对齐到 HMX/HVX 的 tile 和 memory access pattern；还把 8 个 fine-grained quantization groups 合成一个 super-group，让 256 个连续 INT4 values 正好填满一个 HVX vector register。

第二，**LUT-based computation**：用 LUT / vector gather 替代 Softmax 里的 exponential computation，以及 mixed-precision GEMM 里的 dequantization，从而减少 vector unit 上的复杂计算。系统实现上，它给 llama.cpp 增加 Hexagon NPU backend，利用 rpcmem shared memory 避免 CPU–NPU 间不必要的数据拷贝，并允许未实现的算子 fallback 到 CPU。

# Overview

```text

第 1 层：LLM 模型与 GGML 计算图
        llama.cpp  

第 2 层：GGML HTP Backend
        判断算子能否下放 NPU
        打包参数
        管理共享内存
        发起 FastRPC

第 3 层：DSP Runtime
        接收请求
        rpcmem 映射
        operator dispatch
        worker/VTCM/HMX 管理

第 4 层：真正的 NPU Kernel
        HMX：QKᵀ、PV
        HVX：softmax、数据处理
```

并不是通常意义上的 QNN graph 实现。其完整链路在仓库中明确写成了 
`GGML_OP_FLASH_ATTN_EXT → ggml-htp → FastRPC → DSP op_executor → HMX/HVX kernel`。

完整llama.cpp的推理路径

```text
llama.cpp 构建 Attention 计算图
        ↓
GGML_OP_FLASH_ATTN_EXT
        ↓
ggml/src/ggml-htp/htp-ops.cc
        ↓
检查数据类型和算子支持情况
        ↓
构造 FlashAttnParams
        ↓
HTP_OPS_FLASH_ATTN_QO_F32_KV_F16
        ↓
FastRPC 共享内存消息
        ↓
DSP: op_executor.cc
        ↓
simple_flash_attn_llm_profiled(...)
        ↓
simple_flash_attn_f16_core(...)
        ↓
HMX QKᵀ + HVX Softmax + HMX PV
```

在 DSP 的 `op_executor.cc` 中，该 operator 分支会：

1. 解析 `FlashAttnParams`；
2. 映射 O、Q、K、V、mask；
3. 刷新输入 cache；
4. 调用 `simple_flash_attn_llm_profiled`；
5. 刷新输出 cache；
6. 返回执行结果。

