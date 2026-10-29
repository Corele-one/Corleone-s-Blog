# 4. 构建、量化与运行

## 前置条件

与 [[../flashattention/07-building-and-running|FlashAttention 构建环境]] 相同。

## 步骤 1：构建 HTP Operator

```powershell
cd projects/w4-w8-a16

$ProjectWsl = (wsl.exe wslpath -a (Resolve-Path .\src\htp-ops-lib-main)).Trim()
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "
set -e
source /root/llama-npu-env.sh
cd '$ProjectWsl'
build_cmake android
build_cmake hexagon DSP_ARCH=v73
"
```

## 步骤 2：构建 llama.cpp HTP Backend

在 WSL 中：

```bash
cd src/llama.cpp-npu-htp-backend
cmake -S . -B build-android-htp-v73-shared -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-26 \
  -DGGML_HTP=ON \
  -DGGML_OPENMP=OFF \
  -DBUILD_SHARED_LIBS=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build-android-htp-v73-shared \
  --target llama-cli llama-quantize ggml-htp -j8
```

输出在 `build-android-htp-v73-shared/bin/` 下。

## 步骤 3：转换和量化模型

```bash
# HuggingFace → FP16-HMX GGUF
python src/llama.cpp-npu-htp-backend/extras/convert_hf_to_gguf_htp.py \
  --outfile /path/to/qwen2.5-1.5b.f16-hmx.gguf \
  --outtype f16 \
  /path/to/Qwen2.5-1.5B-Instruct

# FP16-HMX → IQ4_NL+Q8_0 量化
REPACK_FOR_HVX=1 \
src/llama.cpp-npu-htp-backend/build-android-htp-v73-shared/bin/llama-quantize \
  /path/to/qwen2.5-1.5b.f16-hmx.gguf \
  /path/to/qwen2.5-1.5b.iq4_nl+q8_0-hmx.gguf \
  IQ4_NL+Q8_0
```

## 步骤 4：部署到设备

把以下文件推送到设备上的同一目录：

```
/data/local/tmp/snapdragon-npu-w4w8/
├── llama-cli                      ← AArch64 可执行文件
├── libllama.so                    ← llama 共享库
├── libggml.so, libggml-htp.so    ← GGML 共享库
├── libhtp_ops.so                  ← host FastRPC stub
├── cdsp/
│   └── libhtp_ops_skel.so        ← DSP skel
├── dsp/
│   └── libhtp_ops_skel.so
└── qwen2.5-1.5b.iq4_nl+q8_0-hmx.gguf  ← 量化模型
```

## 步骤 5：运行

```bash
cd /data/local/tmp/snapdragon-npu-w4w8
export LD_LIBRARY_PATH="$PWD:/vendor/lib64:/system/lib64"
export DSP_LIBRARY_PATH="$PWD:$PWD/cdsp:$PWD/dsp"
./llama-cli \
  -t 4 \
  -fa \
  -m qwen2.5-1.5b.iq4_nl+q8_0-hmx.gguf \
  -p "Hello, my name is"
```

| 参数 | 含义 |
|------|------|
| `-t 4` | 4 个线程 |
| `-fa` | 启用 FlashAttention |
| `-m` | 模型路径 |
| `-p` | 输入 prompt |

## 验证

1. **Standalone smoke**：先运行 HTP operator 的 standalone test，确认 FastRPC 和 skel 可加载
2. **Backend op test**：运行 llama.cpp 的 `test-backend-ops` 做数值对比
3. **端到端对比**：用固定 prompt 比较 CPU 和 HTP 的输出

> [!warning] `ret=0` 不等于正确
> standalone test 返回 0 只表示 RPC/kernel 执行完成，不证明数值正确。
