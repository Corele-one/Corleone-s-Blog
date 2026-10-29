# 2. 推理 Pipeline：从 llama.cpp 到 DSP Kernel

## 总览

一次 LLM 推理（比如生成一个 token）的完整路径：

```
用户请求
  → llama.cpp server (HTTP API)
    → 构建计算图 (GGML graph)
      → 对图中每个 op 调用 backend
        → HTP backend: 打包参数 → FastRPC → DSP
          → op_executor 分发 → flash_attn.c 计算
        → 结果写回 host
      → 下一个 op ...
    → 输出 token
```

## 第一步：GGML 计算图

llama.cpp 使用 GGML 作为张量计算库。一次前向推理会被组织成一个**计算图**（`ggml_cgraph`），图中的每个节点是一个算子（`ggml_op`），比如：

- `GGML_OP_MUL_MAT`：矩阵乘法（Linear 层）
- `GGML_OP_RMS_NORM`：归一化
- `GGML_OP_FLASH_ATTN_EXT`：FlashAttention
- `GGML_OP_ROPE`：旋转位置编码
- ...

关键文件：`src/llama.cpp-npu-htp-backend/src/llama.cpp`

```text
GGML 框架调用流程：

1. 构建计算图时
   │
   ▼
2. 对每个操作节点，调用各后端的 support_op()
   ├─ CPU 后端: cpu_support_op(dst) → 返回 true/false
   ├─ HTP 后端: htp_ops_support_op(dst) → 检查约束条件
   └─ 其他后端...
   │
   ▼
3. GGML 选择最佳后端（通常优先专用硬件）
   │
   ▼
4. 执行时调用选中后端的 compute_op()
   └─ HTP: htp_ops_compute_op(params, dst)
      ├─ 准备参数
      ├─ 通过 RPC 发送到 Hexagon NPU
      └─ 等待结果返回
```
## 第二步：HTP Backend 接管

```text

┌─────────────────────────────────────────────────────────────┐
│                     上层（GGML框架）                          │
│  dst->op = GGML_OP_FLASH_ATTN_EXT                           │
│  dst->src[0..3] = {q, k, v, mask}                          │
│  dst->op_params = {scale, max_bias, logit_softcap}         │
│  （完全硬件无关的描述）                                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌──────────────────────┐
              │    HTP 后端适配层     │
              │  （本文件的switch）   │
              └──────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   下层（Hexagon NPU）                         │
│  FlashAttnParams {                                          │
│    .q = {fd=12, offset=0x1000},    ← 共享内存文件描述符      │
│    .k = {fd=12, offset=0x2000},                             │
│    .qo_len = 1, .kv_len = 2048,                             │
│    .n_heads = 32, .n_kv_heads = 8,  ← GQA参数               │
│  }                                                          │
│  （硬件专用的执行参数）                                        │
└─────────────────────────────────────────────────────────────┘
```

该部分为HTP的后端

GGML 支持多个 backend（CPU、CUDA、Metal、Vulkan...）。这个项目添加了一个 **HTP backend**，当检测到 Snapdragon 设备时，把某些 op 卸载到 DSP 上执行。

关键文件：`src/llama.cpp-npu-htp-backend/ggml/src/ggml-htp/htp-ops.cc`

这个文件里有一个大 switch，根据 GGML op 类型决定怎么处理：

```c
// htp-ops.cc 中的 dispatch 逻辑（简化）
switch (ggml_op(dst)) {
    case GGML_OP_FLASH_ATTN_EXT:
        // 1. 从 GGML tensor 中提取 Q, K, V, mask 的参数
        // 2. 把参数打包成 FlashAttnParams 结构体
        // 3. 写入 rpcmem 共享内存
        // 4. 设置 op_index = HTP_OPS_FLASH_ATTN_QO_F32_KV_F16
        // 5. 发送 FastRPC 请求
        break;
    case GGML_OP_MUL_MAT:
        // 类似，但分发到 HTP_OPS_MAT_MUL_PERMUTED_*
        break;
    // ...
}
```

### FlashAttnParams 结构体

这是 host→DSP 传递的参数定义（`include/op_reg.h`）：

```c
struct FlashAttnParams {
  struct RpcmemBufAddr o;     // 输出 buffer（rpcmem fd + offset）
  struct RpcmemBufAddr q;     // Q 矩阵
  struct RpcmemBufAddr k;     // K 矩阵
  struct RpcmemBufAddr v;     // V 矩阵
  struct RpcmemBufAddr mask;  // attention mask
  int32_t qo_len;             // query/output 序列长度
  int32_t kv_len;             // key/value 序列长度
  int32_t n_heads;            // attention head 数
  int32_t n_kv_heads;         // KV head 数（GQA 时 < n_heads）
  int32_t head_dim;           // 每个 head 的维度（通常 128）
  int64_t trace_id;           // 用于 trace 关联
  int32_t mode_flags;         // LLM_NPU_MODE_LUT_EXP 等运行时标志
  int32_t max_profile_events; // profile buffer 大小
  struct RpcmemBufAddr profile; // profile 输出 buffer
};
```

> [!note] RpcmemBufAddr
> 因为 host 和 DSP 共享内存，所以不需要传实际数据——只需要告诉 DSP 数据在 rpcmem 中的位置（fd + offset）。

## 第三步：FastRPC 传输

```
Host (htp-ops.cc)                 DSP (commu.c)
     │                                │
     │  写入共享 message buffer         │
     │  设置 state = 1 (ready)         │
     │                                │
     │                                │  msg_receiver_loop 轮询
     │                                │  检测到 state = 1
     │                                │  读取 MessageHeader
     │                                │    ↓
     │                                │  解析 RequestHeader
     │                                │  op = HTP_OPS_FLASH_ATTN_QO_F32_KV_F16
     │                                │    ↓
     │                                │  op_executor 分发
```

通信格式定义在 `include/message.h`：

```c
struct MessageHeader {
  struct MessageState state;    // 8 字节状态标志
  uint32_t            checksum; // 简单校验
  int32_t             n_reqs;   // 请求数量
  int32_t             req_offsets[0]; // 每个请求的偏移
};

struct RequestHeader {
  int32_t state;
  int32_t type;      // REQUEST_TYPE_OP_COMPUTE
  uint8_t data[0];   // OpComputeRequest → op index + FlashAttnParams
};
```

DSP 端 `commu.c` 中有一个轮询线程（`msg_receiver_loop`），不断检查共享内存中的消息状态。收到请求后调用 `op_executor.cc` 的分发逻辑。

## 第四步：DSP 端分发

`src/dsp/op_executor.cc` 是 DSP 端的调度中心。收到 `HTP_OPS_FLASH_ATTN_QO_F32_KV_F16` 请求后：

```c
// op_executor.cc 中的 flash attn dispatch（简化）
case HTP_OPS_FLASH_ATTN_QO_F32_KV_F16: {
    auto params = reinterpret_cast<FlashAttnParams *>(req->payload);

    // 1. 从 rpcmem 映射中获取 Q, K, V, mask, O 的实际指针
    // 2. 调用 FlashAttention kernel
    simple_flash_attn_llm_profiled(
        (__fp16 *) OUT_PTR(0),  // O
        (__fp16 *) IN_PTR(0),   // Q (FP32 会被转为 FP16)
        (__fp16 *) IN_PTR(1),   // K (已经是 FP16)
        (__fp16 *) IN_PTR(2),   // V (已经是 FP16)
        (__fp16 *) IN_PTR(3),   // mask
        qo_len, kv_len, n_heads, n_kv_heads, head_dim,
        params->trace_id, params->mode_flags, req->op, profile
    );
    break;
}
```

## 第五步：FlashAttention Kernel

`simple_flash_attn_llm_profiled` 调用 `simple_flash_attn_impl`，这是整个 FlashAttention 的入口。

```c
// flash_attn.c:1621
static int simple_flash_attn_impl(...) {
    // 1. 如果 head_dim 不是 64 的倍数，走 fallback 路径
    if (head_dim % 64 != 0) {
        return simple_flash_attn_sp_hdim(...);
    }

    // 2. 设置多线程：每个 KV head 一个 worker
    state.n_tasks = n_kv_heads;
    // worker 数 = HVX 128-bit context 数（通常 4-8 个）

    // 3. 提交到 worker pool
    for (int i = 0; i < n_workers; ++i) {
        worker_pool_submit(NULL, job);
    }
    worker_pool_synctoken_wait(&(state.sync_ctx));  // 等待所有 worker 完成
}
```

每个 worker 调用 `simple_flash_attn_f16_core`，这就是真正的 Attention 计算核心——我们在 [[04-kernel-deep-dive]] 中详细拆解。

## 数据类型流转

```
Host 侧 (GGML/llama.cpp)        DSP 侧 (HTP kernel)
─────────────────────────        ─────────────────────
Q: FP32                      →   转为 FP16，存入 VTCM
K: FP16                      →   转为 HMX tile layout，存入 VTCM
V: FP16                      →   转为 HMX tile layout，存入 VTCM
mask: FP16                   →   直接使用
O: FP32                      ←   kernel 输出 FP16，转回 FP32
```

> [!important] 为什么 Q 是 FP32 而 K/V 是 FP16？
> 这是 llama.cpp 的设计：Q 保持 FP32 精度以减少 attention 计算的数值误差，K/V 用 FP16 节省内存带宽。DSP kernel 内部会把 Q 从 FP32 转为 FP16 再做计算。

## 完整调用链总结

```
[llama.cpp] GGML_OP_FLASH_ATTN_EXT
    ↓
[ggml-htp/htp-ops.cc] 打包 FlashAttnParams → FastRPC
    ↓
[dsp/commu.c] msg_receiver_loop 接收
    ↓
[dsp/op_executor.cc] HTP_OPS_FLASH_ATTN_QO_F32_KV_F16 分发
    ↓
[dsp/ops/flash_attn.c] simple_flash_attn_impl()
    ↓
[dsp/ops/flash_attn.c] simple_flash_attn_f16_core()  ← ★ 核心计算
    ↓
结果写回 rpcmem → host 读取
```

> [!next] 下一步
> 了解了整体流程后，我们来看 FlashAttention 算法本身和 tiling 策略：[[03-flash-attn-algorithm]]
