# 3. GGUF 转换流程

## 两步转换

从 HuggingFace 模型到设备上运行的量化模型，需要两步：

```
HuggingFace 模型 (safetensors)
    ↓  第一步：convert_hf_to_gguf_htp.py
FP16-HMX GGUF（HMX tile layout 的 FP16）
    ↓  第二步：llama-quantize
IQ4_NL+Q8_0 量化 GGUF
```

## 第一步：FP16-HMX GGUF

```bash
python src/llama.cpp-npu-htp-backend/extras/convert_hf_to_gguf_htp.py \
  --outfile /path/to/model.f16-hmx.gguf \
  --outtype f16 \
  /path/to/Qwen2.5-1.5B-Instruct
```

这个脚本基于 llama.cpp 的 `convert_hf_to_gguf.py`，但增加了 HMX layout 转换：把 FP16 权重从普通行主序转为 HMX tile layout。

> [!note] HMX Layout 不影响数值
> `f16-hmx.gguf` 的数值和普通 FP16 GGUF 完全一样，只是存储排列不同。这个 layout 让 DSP 上的 HMX 可以直接加载 tile，省去运行时的 layout 转换开销。

## 第二步：量化

```bash
REPACK_FOR_HVX=1 \
src/llama.cpp-npu-htp-backend/build-android-htp-v73-shared/bin/llama-quantize \
  /path/to/model.f16-hmx.gguf \
  /path/to/model.iq4_nl+q8_0-hmx.gguf \
  IQ4_NL+Q8_0
```

`IQ4_NL+Q8_0` 是混合量化方案：
- 大部分层用 **IQ4_NL**（4-bit 非线性量化）
- Attention 层用 **Q8_0**（8-bit 线性量化）

`REPACK_FOR_HVX=1` 让 quantizer 把 block 重新排列为 super block layout（8 个 block 合一组），便于 HVX 批量解码。

## 转换脚本位置

```
src/llama.cpp-npu-htp-backend/extras/
├── convert_hf_to_gguf_htp.py   ← HuggingFace → FP16-HMX GGUF
└── libcdsprpc_mock.c           ← mock 的 DSP RPC 库（用于离线转换）
```

`libcdsprpc_mock.c` 提供了 `rpcmem_alloc` 等函数的空实现，让量化工具可以在没有 DSP 设备的机器上运行。

> [!next] 下一步
> 准备好了模型，来看怎么构建和运行：[[04-building-and-running]]
