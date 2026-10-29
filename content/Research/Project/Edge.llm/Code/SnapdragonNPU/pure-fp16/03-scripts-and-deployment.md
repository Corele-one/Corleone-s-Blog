# 3. PowerShell 脚本与部署

## 脚本概览

所有脚本在 `projects/pure-fp16/scripts/` 下，通过 PowerShell 运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\<script>.ps1 [参数]
```

| 脚本 | 功能 |
|------|------|
| `common.ps1` | 公共函数库（ADB、模型定位、HTTP 请求等） |
| `build_pure_fp16.ps1` | 构建 HTP ops + llama.cpp，生成 `deploy/` |
| `switch_llm_inference_route.ps1` | 部署并切换 runtime（pure_fp16 / iq4 / lpbq） |
| `run_smoke_pure_fp16.ps1` | 端到端内容 smoke 测试 |
| `run_trace_pure_fp16.ps1` | 单 case detailed trace |
| `run_pd_sweep_pure_fp16.ps1` | prefill/decode 性能 sweep |
| `tune_batch_pure_fp16.ps1` | batch/ubatch/thread 参数搜索 |
| `rebuild_pd_sweep_summary.ps1` | 从已有 CSV 重建 summary（不访问设备） |

## 完整流程

### 1. 构建

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\build_pure_fp16.ps1 `
  -DspArch v73 `
  -Jobs 8 `
  -ModelPath C:\path\to\model.f16-hmx.gguf
```

脚本会：
1. 在 WSL 中构建 Android AArch64 HTP stub 和 Hexagon skel
2. 构建 llama-server、llama-cli 和共享库
3. 从 `deploy-template/run_server.sh` 初始化 `deploy/` 目录
4. 把运行时文件打包进 `deploy/`
5. 写入本地 manifest

### 2. 部署

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\switch_llm_inference_route.ps1 `
  -Mode pure_fp16 `
  -ModelPath C:\path\to\model.f16-hmx.gguf `
  -Serial <device-serial> `
  -Port 8080
```

脚本会：
- 把 `deploy/` 内容推送到设备
- 启动 `llama-server`（HTTP API 服务）
- 设置 API key（默认 `llama-npu-local-key`，生产环境应更换）

> [!warning] API Key 安全
> `deploy-template/run_server.sh` 会启用 API key 验证。不要在局域网环境使用默认 key。部署前设置：
> ```bash
> export LLAMA_API_KEY='<strong-random-secret>'
> ```

### 3. Smoke 测试

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_smoke_pure_fp16.ps1 `
  -Mode pure_fp16 `
  -Port 8080 `
  -Serial <device-serial>
```

验证点：
- 命令退出码为 0
- 返回内容包含预期文本
- 无 NaN / Inf

### 4. PD Sweep（Prefill/Decode 性能扫描）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_pd_sweep_pure_fp16.ps1 `
  -Port 8080 `
  -Serial <device-serial> `
  -Batch 512 `
  -Ubatch 512 `
  -Threads 4 `
  -Repeats 3 `
  -SpeedOnly
```

扫描不同 prefill/decode 长度组合的推理速度。

### 5. Detailed Trace

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_trace_pure_fp16.ps1 `
  -Port 8080 `
  -Serial <device-serial> `
  -CaseName prefill_512_decode_16 `
  -TargetPrefill 512 `
  -Decode 16
```

期望检查：
- trace 中出现 `matmul_f16` 或 `matmul_w16a32`
- pure-FP16 trace 中**不**出现 `weight_hvx_dequant`

> [!note] Trace 改变性能
> detailed trace 会增加 DSP 侧的 profile 开销，不能把 trace wall time 当作正常推理性能。

## deploy 目录结构

```
deploy/
├── htp_ops_test            ← standalone benchmark
├── libhtp_ops.so           ← host stub
├── libhtp_ops_skel.so      ← DSP skel
├── llama-server            ← HTTP server
├── llama-cli               ← CLI 推理
├── libllama.so, libggml.so, libggml-htp.so
├── run_server.sh           ← server 启动脚本
├── model.f16-hmx.gguf      ← 模型（如果 -ModelPath 指定了）
└── manifest.json           ← 构建信息
```

`deploy/`、模型、日志和二进制均被 Git 忽略。

> [!next] 下一步
> 想了解实验性的 LPBQ INT8 路径？看 [[04-lpbq-experiments]]
