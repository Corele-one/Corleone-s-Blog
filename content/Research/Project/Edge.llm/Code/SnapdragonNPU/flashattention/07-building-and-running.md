# 7. 构建、部署与运行

## 前置条件

| 项目               | 说明                                                        |
| ---------------- | --------------------------------------------------------- |
| WSL2             | Ubuntu 22.04，已安装 CMake、Ninja                              |
| Hexagon SDK 6.x  | 获授权的 Qualcomm SDK，WSL 中需要 `source /root/llama-npu-env.sh` |
| Android NDK r25c | 通常在 SDK 目录下                                               |
| adb              | Android SDK platform-tools                                |
| 设备               | Snapdragon 8 Gen 2+，Hexagon v73/v79，支持 FP16 HMX           |
| Python 3         | 运行分析工具                                                    |

> [!warning] 缺少的头文件
> `include/dsp/hvx_internal.h` 和 `include/dsp/worker_pool.h` 是 Qualcomm 专有头文件，不在仓库中。你需要从授权的 Hexagon SDK 环境提供这些文件，否则无法编译。

## 步骤 1：构建 HTP Operator

所有命令从 `projects/flashattention/` 目录执行。

### 构建 v73

```powershell
# 把 Windows 路径转为 WSL 路径
$HtpWsl = (wsl.exe wslpath -a (Resolve-Path .\src\htp-ops-lib-main)).Trim()

# 在 WSL 中构建
wsl.exe -d Ubuntu-22.04 -u root -- bash -lc "
set -e
source /root/llama-npu-env.sh
cd '$HtpWsl'
build_cmake android        # 构建 AArch64 host stub + test
build_cmake hexagon DSP_ARCH=v73 \
  FIGURE8_ENABLE_PROFILE_TIMERS=ON \
  FIGURE8_ENABLE_LUT_EXP=OFF
"
```

### 构建 v79

把 `DSP_ARCH=v73` 改为 `DSP_ARCH=v79` 即可。

### 构建产物

```
src/htp-ops-lib-main/
├── android_ReleaseG_aarch64/ship/
│   ├── htp_ops_test        ← AArch64 standalone benchmark
│   └── libhtp_ops.so       ← host FastRPC stub
└── hexagon_ReleaseG_toolv88_v73/ship/
    └── libhtp_ops_skel.so  ← DSP skeleton（推到设备 cdsp/ 或 dsp/）
```

> [!note] 工具版本
> 输出目录中的 `toolv88` 可能因 SDK 版本不同而变化，以实际构建日志为准。

---

## 步骤 2：部署到设备

```powershell
$Remote = '/data/local/tmp/figure8_attn'

# 创建设备目录
adb shell "mkdir -p $Remote/cdsp $Remote/dsp"

# 推送文件
adb push .\src\htp-ops-lib-main\android_ReleaseG_aarch64\ship\htp_ops_test "$Remote/"
adb push .\src\htp-ops-lib-main\android_ReleaseG_aarch64\ship\libhtp_ops.so "$Remote/"
adb push .\src\htp-ops-lib-main\hexagon_ReleaseG_toolv88_v73\ship\libhtp_ops_skel.so "$Remote/cdsp/"
adb push .\src\htp-ops-lib-main\hexagon_ReleaseG_toolv88_v73\ship\libhtp_ops_skel.so "$Remote/dsp/"

# 设置执行权限
adb shell "chmod 755 $Remote/htp_ops_test"
```

设备上的目录结构：

```
/data/local/tmp/figure8_attn/
├── htp_ops_test          ← benchmark 可执行文件
├── libhtp_ops.so         ← host stub
├── cdsp/
│   └── libhtp_ops_skel.so  ← DSP skel（cdsp domain）
└── dsp/
    └── libhtp_ops_skel.so  ← DSP skel（dsp domain）
```

---

## 步骤 3：运行 Benchmark

### Baseline 模式

```powershell
adb shell "cd /data/local/tmp/figure8_attn && \
  LD_LIBRARY_PATH=. \
  DSP_LIBRARY_PATH='./cdsp;./dsp;.' \
  ./htp_ops_test --figure8-attn \
    --mode baseline \
    --qo-len 4 --kv-len 4096 \
    --n-heads 12 --n-kv-heads 2 --head-dim 128 \
    --warmup 5 --iters 20"
```

### LUT-exp 模式

```powershell
adb shell "cd /data/local/tmp/figure8_attn && \
  LD_LIBRARY_PATH=. \
  DSP_LIBRARY_PATH='./cdsp;./dsp;.' \
  ./htp_ops_test --figure8-attn \
    --mode lut-exp \
    --qo-len 4 --kv-len 4096 \
    --n-heads 12 --n-kv-heads 2 --head-dim 128 \
    --warmup 5 --iters 20"
```

### 参数说明

| 参数 | 含义 |
|------|------|
| `--mode baseline` | 使用多项式近似计算 exp |
| `--mode lut-exp` | 使用 VTCM LUT 查表计算 exp |
| `--qo-len 4` | query 序列长度（decode 场景通常很小） |
| `--kv-len 4096` | KV cache 长度 |
| `--n-heads 12` | Q head 数 |
| `--n-kv-heads 2` | KV head 数（GQA） |
| `--head-dim 128` | 每个 head 的维度 |
| `--warmup 5` | 预热次数 |
| `--iters 20` | 正式测量次数 |

### 输出格式

```
FIG8_ATTENTION_TIMERS lut_exp=0 qo_len=4 kv_len=4096 n_heads=12 n_kv_heads=2 head_dim=128 kv_head=0 worker=0 profiled_total=1234 q_load=50 k_load=100 v_load=100 qk_dot=300 safe_sm=400 core_acc=200 o_scale=50 o_store=34
```

### 批量运行

对多个 `qo_len` 重复运行，保存到 `results/` 目录：

```powershell
# 对每个 qo_len 跑 baseline 和 lut-exp，保存 raw log
foreach ($q in @(4, 8, 16, 32)) {
    adb shell "cd /data/local/tmp/figure8_attn && ... --mode baseline --qo-len $q ..." `
        | Out-File "results/v73/baseline/raw_q$q.log"
    adb shell "cd /data/local/tmp/figure8_attn && ... --mode lut-exp --qo-len $q ..." `
        | Out-File "results/v73/lut_exp/raw_q$q.log"
}
```

---

## 步骤 4：解析结果

```powershell
# 解析 baseline
python tools/parse_figure8_attention_timers.py `
  --input-dir results/v73/baseline `
  --out-dir results/v73/baseline

# 解析 lut-exp
python tools/parse_figure8_attention_timers.py `
  --input-dir results/v73/lut_exp `
  --out-dir results/v73/lut_exp

# 对比
python tools/compare_figure8_lut_exp.py `
  --baseline-summary results/v73/baseline/attention_timers_summary.json `
  --lut-exp-summary results/v73/lut_exp/attention_timers_summary.json `
  --out-dir results/v73/lut_exp

# 生成 Perfetto trace
python tools/generate_figure8_perfetto_trace.py `
  --input-dir results/v73/baseline `
  --out-dir results/v73/baseline/ntff
```

---

## 步骤 5：数值正确性验证

standalone benchmark 的 `ret=0` 只表示 FastRPC/kernel 执行完成，**不证明数值正确**。

完整验证需要：

1. 构建 llama.cpp 的 `test-backend-ops`
2. 运行 CPU reference 对比：

```bash
test-backend-ops -o FLASH_ATTN_EXT -b HTP
```

这会比较 HTP backend 的 FlashAttention 输出和 CPU reference 实现的差异，检查是否在容差范围内。

---

## CMake 构建选项

| 选项 | 默认值 | 含义 |
|------|--------|------|
| `DSP_ARCH` | (必须指定) | `v73` 或 `v79` |
| `FIGURE8_ENABLE_PROFILE_TIMERS` | `ON` | 启用 Figure 8 计时器 |
| `FIGURE8_ENABLE_LUT_EXP` | `OFF` | 编译时默认使用 LUT exp |
| `HTP_ENABLE_OUT_STATIONARY_PREFILL` | `OFF` | output-stationary matmul 路径 |
| `HTP_MATMUL_PIPELINE_MODE` | `0` | 0=auto 4-stage, 1=sequential safe |
| `HTP_MATMUL_WEIGHT_AREA_KB` | `1024` | VTCM 中 weight 区域大小 (KiB) |
| `HTP_MATMUL_ACTIVATION_AREA_KB` | `2048` | VTCM 中 activation 区域大小 |
| `HTP_MATMUL_OUTPUT_AREA_KB` | `1536` | VTCM 中 output 区域大小 |
| `HTP_MATMUL_SCRATCH_AREA_KB` | `1024` | VTCM 中 scratch 区域大小 |

> [!note] 编译时 vs 运行时
> `FIGURE8_ENABLE_LUT_EXP` 控制的是**编译时默认值**。运行时通过 `--mode baseline` 或 `--mode lut-exp` 覆盖。standalone profile 和 llama.cpp 路径都由运行时 mode 控制。

---

## 常见问题

### `ret=0` 但输出不对？

`ret=0` 只表示 FastRPC 调用成功返回。数值正确性需要 CPU reference 对比验证。

### `qo_len` 必须很小？

对于 benchmark，`qo_len` 通常设 4-32（模拟 decode 阶段）。`kv_len` 设 4096-8192（模拟长 KV cache）。实际推理时 `qo_len` 可以更大。

### v73 和 v79 的区别？

同一份源码，不同 `DSP_ARCH` 构建目标。v79 是更新的 Hexagon 架构，可能有不同的 VTCM 大小和 HMX/HVX 特性。

### Perfetto trace 里的数字代表什么？

是 DSP qtimer 软件事件的时间戳（微秒），**不是** Qualcomm PMU 的 HMX/HVX 硬件利用率。不能直接解释为 "HMX 忙了 X 微秒"。
