# 6. Profiling 与分析工具

## 两套 Profile 系统

本项目有两套 profile 系统，服务于不同场景：

### 1. Figure 8 Profile（standalone benchmark 专用）

专为 FlashAttention benchmark 设计，记录每个 KV head 的 8 个阶段耗时。

数据结构（`include/op_reg.h`）：

```c
struct Figure8ProfileHeader {
    int32_t magic;          // 0x46494738 ("FIG8")
    int32_t max_records;    // 最大记录数（每 KV head 一条）
    int32_t record_count;   // 实际记录数
    int32_t max_events;     // 最大事件数（每个 block 一个事件）
    int32_t event_count;
    int32_t event_overflow;
};

struct Figure8ProfileRecord {
    int32_t lut_exp;        // 是否使用 LUT exp
    int32_t qo_len, kv_len, n_heads, n_kv_heads, head_dim;
    int32_t kv_head;        // KV head 索引
    int32_t worker;         // worker 索引
    int64_t profiled_total; // 总耗时 (us)
    int64_t q_load, k_load, v_load;  // 各阶段耗时
    int64_t qk_dot, safe_sm, core_acc, o_scale, o_store;
};
```

输出格式（`FIG8_ATTENTION_TIMERS` 日志行）：

```
FIG8_ATTENTION_TIMERS lut_exp=0 qo_len=4 kv_len=4096 n_heads=12 n_kv_heads=2 head_dim=128 kv_head=0 worker=0 profiled_total=1234 q_load=50 k_load=100 v_load=100 qk_dot=300 safe_sm=400 core_acc=200 o_scale=50 o_store=34
```

### 2. LLM Trace Profile（llama.cpp 集成用）

记录更细粒度的事件，支持跨 op 的 trace 关联。

```c
struct LlmTraceProfileEvent {
    int64_t trace_id;   // 关联 ID
    int32_t op_index;   // 操作码
    int32_t stage;      // LLM_TRACE_STAGE_FLASH_Q_LOAD 等
    int32_t unit;       // DMA / HVX / HMX / ...
    int32_t worker;
    int32_t qo_len, kv_len, n_heads, n_kv_heads, head_dim;
    int32_t block_r, block_c;  // 当前处理的 block 位置
    int64_t t0_us, t1_us, dur_us;  // 时间戳和持续时间
};
```

---

## Python 工具

### `parse_figure8_attention_timers.py`

**功能**：解析 `raw_q*.log` 中的 `FIG8_ATTENTION_TIMERS` 行，生成 CSV 和 JSON summary。

```powershell
python tools/parse_figure8_attention_timers.py `
  --input-dir results/v73/baseline `
  --out-dir results/v73/baseline
```

**输出**：
- `attention_timers.csv`：每行一条 timer 记录
- `attention_timers_summary.json`：按 `qo_len` 分组的统计（median、mean）

**JSON summary 结构**：

```json
{
    "by_qo_len": {
        "4": {
            "valid_iterations": 20,
            "median_us": {
                "profiled_total": 1234,
                "q_load": 50,
                "k_load": 100,
                ...
            },
            "host_elapsed_us": {
                "median": 1500
            }
        }
    }
}
```

### `compare_figure8_lut_exp.py`

**功能**：对比 baseline 和 lut-exp 两个 mode 的 summary JSON，生成差异 CSV 和 summary。

```powershell
python tools/compare_figure8_lut_exp.py `
  --baseline-summary results/v73/baseline/attention_timers_summary.json `
  --lut-exp-summary results/v73/lut_exp/attention_timers_summary.json `
  --out-dir results/v73/lut_exp
```

**输出**：
- `baseline_vs_lut_exp.csv`：逐 `qo_len` 的对比表
- `baseline_vs_lut_exp_summary.json`：包含 delta 和百分比变化

**CSV 列**：

| 列名 | 含义 |
|------|------|
| `qo_len` | query 长度 |
| `baseline_profiled_total_us` | baseline 总耗时 |
| `lut_exp_profiled_total_us` | lut-exp 总耗时 |
| `profiled_total_delta_pct` | 变化百分比（负数 = lut-exp 更快） |
| `baseline_safe_sm_us` | baseline softmax 耗时 |
| `lut_exp_safe_sm_us` | lut-exp softmax 耗时 |
| ... | 其他 8 个阶段的对比 |

### `generate_figure8_perfetto_trace.py`

**功能**：从 parsed timer 数据生成 Perfetto/NTFF 格式的 trace 文件，可在 [Perfetto UI](https://ui.perfetto.dev/) 中可视化。

```powershell
python tools/generate_figure8_perfetto_trace.py `
  --input-dir results/v73/baseline `
  --out-dir results/v73/baseline/ntff
```

**注意**：Perfetto trace 中的事件是 DSP qtimer 软件事件，**不是** Qualcomm PMU 的 HMX/HVX 硬件利用率计数。不能把 `core_acc`、`o_scale` 等直接解释为硬件 active cycle。

### `parse_figure8_long_kv_breakdown.py`

**功能**：针对长 KV 序列的细粒度分析，按 block 级别分解耗时。

### `parse_llm_inference_trace.py`

**功能**：解析 llama.cpp 集成运行时的 LLM trace 日志，生成推理各阶段的时间线。

### `serve_trace_cors.py`

**功能**：本地 HTTP server，为 Perfetto trace 文件提供 CORS 头，方便在浏览器中直接打开。

---

## Results 目录结构

```
results/
├── README.md
├── trace_semantics_audit_*.csv/md   ← trace 语义审计
├── v73/
│   ├── baseline/
│   │   ├── raw_q4.log               ← 原始 benchmark 输出
│   │   ├── raw_q8.log
│   │   ├── raw_q16.log
│   │   ├── raw_q32.log
│   │   ├── attention_timers.csv      ← parsed CSV
│   │   └── attention_timers_summary.json
│   └── lut_exp/
│       ├── raw_q*.log
│       ├── attention_timers.csv
│       ├── attention_timers_summary.json
│       ├── baseline_vs_lut_exp.csv   ← 对比结果
│       ├── baseline_vs_lut_exp_summary.json
│       └── ntff/                     ← Perfetto trace
└── v79/
    ├── baseline/
    └── lut_exp/
        └── v73_vs_v79.*             ← 跨架构对比（历史静态数据）
```

---

## 典型性能分析流程

```
1. 跑 benchmark，保存 raw log
   ↓
2. parse_figure8_attention_timers.py → CSV + JSON summary
   ↓
3. 对比 baseline vs lut-exp
   compare_figure8_lut_exp.py → 差异 CSV
   ↓
4. 可视化
   generate_figure8_perfetto_trace.py → Perfetto trace
   在浏览器中打开 ui.perfetto.dev 查看时间线
   ↓
5. 分析瓶颈
   哪个阶段占比最大？
   safe_sm 高 → softmax 是瓶颈 → lut-exp 有帮助
   qk_dot 高 → HMX 计算是瓶颈 → 需要优化 tile 大小
   k_load 高 → 内存带宽是瓶颈 → 需要优化数据 layout
```

> [!next] 下一步
> 想自己跑一遍？看 [[07-building-and-running]]
