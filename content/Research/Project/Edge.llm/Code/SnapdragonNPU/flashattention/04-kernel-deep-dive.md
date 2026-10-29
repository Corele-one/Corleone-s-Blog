# 4. Kernel 逐段拆解：`simple_flash_attn_f16_core`

> 本章对应源码 `src/htp-ops-lib-main/src/dsp/ops/flash_attn.c` 第 252-1057 行。
> 这是 FlashAttention 在 DSP 上的核心实现，也是整个项目最关键的部分。

## 函数签名

```c
void simple_flash_attn_f16_core(
    int kv_head_idx,          // 当前处理的 KV head 索引
    uint8_t *vtcm,            // 本 worker 的 VTCM 起始地址
    uint8_t *vtcm_limit,      // VTCM 上限
    __fp16 *restrict O,       // 输出 [qo_len, n_heads, head_dim]
    const __fp16 *restrict Q, // Q [qo_len, n_heads, head_dim]，FP32 实际
    const __fp16 *restrict K, // K [kv_len, n_kv_heads, head_dim]，FP16
    const __fp16 *restrict V, // V [kv_len, n_kv_heads, head_dim]，FP16
    const __fp16 *restrict mask, // [qo_len, kv_len]
    int qo_len, int kv_len, int n_heads, int n_kv_heads, int head_dim,
    int worker_index, int mode_flags, ...)
```

## 整体流程图

```
for ir in 0..qo_len step Br:          ← 外层循环：遍历 Q 行块
    加载 Q[ir:ir+Br, :] → VTCM
    初始化 m = -inf, l = 0, O = 0

    for jc in 0..kv_len step Bc:      ← 内层循环：遍历 K/V 列块
        ┌─ 加载 K[jc:jc+Bc, :] → VTCM（transposed layout）
        │
        ├─ QK dot: S = Q × K^T       ← HMX 矩阵乘法
        │
        ├─ 加载 mask → 应用到 S
        ├─ rowmax(S)                   ← HVX 向量归约
        ├─ m_new = max(m, rowmax(S))
        ├─ P = exp(S - m_new)          ← HVX 计算 exp（或 LUT 查表）
        │
        ├─ rowsum(P)                   ← HVX 向量归约
        │
        ├─ 加载 V[jc:jc+Bc, :] → VTCM
        │
        ├─ 更新 m, l:
        │   l_new = exp(m - m_new) * l + rowsum(P)
        │
        ├─ O = diag(exp(m - m_new)) × O + P × V  ← HMX 矩阵乘法
        │
        └─ m = m_new, l = l_new

    O = diag(l^{-1}) × O              ← 最终归一化
    存储 O → host 内存
```

下面逐段详解。

---

## 1. 初始化与 VTCM 分配

```c
// 第 257-297 行
const int G = n_heads / n_kv_heads;  // GQA factor
const int D = head_dim;

const bool qo_fp32_element = true;  // Q/O 在 host 侧是 FP32

// 动态计算 tile 大小
size_t blk_sz_r, blk_sz_c;
fa_f16_find_chunk_size(&blk_sz_r, &blk_sz_c, G, head_dim, qo_len, kv_len, vtcm_limit - vtcm);

const size_t g_br = align_up(G * blk_sz_r, HMX_FP16_TILE_N_ROWS);  // 对齐到 32
```

然后在 VTCM 中依次分配所有 buffer：

```c
// 第 300-322 行
__fp16 *q_tile   = vtcm_seq_alloc(&vtcm_cur, qo_tile_size);   // Q 块
__fp16 *o_tile0  = vtcm_seq_alloc(&vtcm_cur, qo_tile_size);   // O buffer 0
__fp16 *o_tile1  = vtcm_seq_alloc(&vtcm_cur, qo_tile_size);   // O buffer 1
__fp16 *k_tile   = vtcm_seq_alloc(&vtcm_cur, kv_tile_size);   // K 块
__fp16 *v_tile   = vtcm_seq_alloc(&vtcm_cur, kv_tile_size);   // V 块
__fp16 *s_tile   = vtcm_seq_alloc(&vtcm_cur, core_tile_size); // S = Q×K^T
__fp16 *p_tile   = vtcm_seq_alloc(&vtcm_cur, core_tile_size); // P = softmax(S)
__fp16 *d_tile   = vtcm_seq_alloc(&vtcm_cur, d_tile_size);    // 对角缩放矩阵
// m, l, rowmax, rowsum 向量...
```

缩放因子设置：

```c
// 第 327-332 行
float qk_scale = 1.0f / sqrtf(head_dim) * 1.44269504f;  // 乘以 log2(e) 把 exp 转为 exp2
__fp16 qk_scale_hf = (__fp16) qk_scale;
hmx_init_column_scales(hmx_output_scales_qk, Q6_V_vsplat_R(fp16_to_bits(&qk_scale_hf)));
```

> [!note] 为什么乘 log2(e)？
> HVX 有高效的 `exp2` 实现（基于多项式近似或 LUT），但没有原生 `exp`。所以把 `exp(x)` 转为 `exp2(x * log2(e))`，在计算 `Q×K^T / sqrt(d)` 时直接把 `1/sqrt(d) * log2(e)` 作为缩放因子乘进去。

---

## 2. 加载 Q 块到 VTCM

```c
// 第 369-446 行
for (int ir = 0; ir < qo_len; ir += blk_sz_r) {
    // Q 的内存布局: [qo_len, n_heads, head_dim]
    // 需要加载 Q[ir:ir+Br, kv_head_idx*G:(kv_head_idx+1)*G, :]

    for (int r = 0; r < n_rows_g; r += 2) {
        // 每次处理 2 行（利用 HVX 的 pair 指令）
        int q_idx0 = r / G;      // 哪个 token
        int h_idx0 = r % G;      // 哪个 head

        const HVX_Vector *pv_in0 = Q + q_idx0 * stride + h_idx0 * head_dim;

        // FP32 → FP16 转换
        const HVX_Vector v_out = hvx_my_wsf_to_vhf(v1, v0);

        // 写入 HMX tile layout
        out_tile[r1 / 2] = v_out;
    }
}
```

> [!important] HMX Tile Layout
> HMX 要求数据按 32×32 tile 排列，不是普通的行主序。一个 `[32, D]` 的行块被组织为 `D/32` 个 tile，每个 tile 是 32×32 的 FP16 元素。`hvx_my_wsf_to_vhf` 做 FP32→FP16 转换，同时完成 layout 转换。

---

## 3. 加载 K 块 + QK Dot

### 加载 K（transposed）

```c
// 第 458-507 行
for (int jc = 0; jc < kv_len; jc += blk_sz_c) {
    // K 的内存布局: [kv_len, n_kv_heads, head_dim]
    // K 需要转置：[Bc, D] → [D, Bc]（HMX tile layout）

    for (int r0 = 0; r0 < n_col_tiles; ++r0) {
        for (int r1 = 0; r1 < 32; ++r1) {
            // 用 vscatter 把连续的行数据分散到转置的 tile 位置
            Q6_vscatter_RMVwV((size_t) out_dual_tile, ..., v_offsets, *pv_in++);
        }
    }
}
```

### QK Dot（HMX 矩阵乘法）

```c
// 第 516-534 行
// S = Q × K^T
// Q: [Br', D] in HMX tile layout
// K: [D, Bc] in HMX tile layout (transposed)
// S: [Br', Bc] in HMX tile layout

hmx_unit_acquire();  // 获取 HMX 单元
{
    hmx_set_output_scales(hmx_output_scales_qk);  // 设置缩放 = 1/sqrt(d) * log2(e)
    for (int r = 0; r < n_row_tiles; ++r) {
        for (int c = 0; c < n_col_tiles; ++c) {
            hmx_dot_fp16(out_tile, row_tiles, col_tiles, head_dim / 32);
        }
    }
}
hmx_unit_release();
```

`hmx_dot_fp16` 是 HMX 的核心操作（`include/dsp/hmx_utils.h`）：

```c
static void hmx_dot_fp16(__fp16 *out, const __fp16 *row_tiles, const __fp16 *col_tiles, size_t n_tiles) {
    hmx_load_tiles_fp16(row_tiles, col_tiles, n_tiles);  // 加载到 HMX 内部寄存器
    hmx_consume_accumulator_fp16(out);                    // 读出累加结果
}
```

HMX 内部会做 32×32 tile 的矩阵乘累加，每次处理一对 tile。`head_dim / 32` 个 tile 对的结果累加得到 S 的一个 tile。

---

## 4. Safe Softmax（HVX 实现）

这是 kernel 中最复杂的部分。对 S 矩阵的每一行：

```
步骤 1: 应用 mask，计算 rowmax(S)
步骤 2: 计算 P = exp(S - m_new)
步骤 3: 计算 rowsum(P)
```

### 步骤 1: Mask + Rowmax

```c
// 第 543-621 行
for (int r_vec_idx = 0; r_vec_idx < n_row_vec_cnt; ++r_vec_idx) {
    // 每次处理 64 行（2 个 HVX vector）

    for (int c = 0; c < n_cols; c += 64) {
        // 加载 mask
        HVX_Vector v_mask0 = vmemu(qk_mask + q_idx0 * kv_pad_len + k_idx);

        // mask 阈值：-16.0（FP16）→ 被 mask 的位置设为 -inf
        q_mask_keep0 = Q6_Q_vcmp_gt_VhfVhf(v_mask0, v_fp16_mask_threshold);
        HVX_Vector v_s_row0 = Q6_V_vmux_QVV(q_mask_keep0, row_buffer0[c/64], v_neg_inf);

        // 逐行 max 归约
        v_s_rowmax0 = Q6_Vhf_vmax_VhfVhf(v_s_rowmax0, v_s_row0);
    }

    // intra-vector 归约：把 64 个 lane 的 max 合并到 lane[63]
    for (int s = 64; s >= 2; s >>= 1) {
        v_s_rowmax0 = Q6_Vhf_vmax_VhfVhf(v_s_rowmax0, Q6_V_vlalign_VVR(v_s_rowmax0, v_neg_inf, s));
    }
}
```

### 步骤 2: 计算 P = exp(S - m_new)

有两种实现，由 `mode_flags` 中的 `LLM_NPU_MODE_LUT_EXP` 控制：

**Baseline 模式**：HVX 多项式近似
```c
v_p_row0_hf = hvx_my_exp2_vhf_vqf16(v_s_minus_m0);
```

**LUT-exp 模式**：VTCM 中的查找表 + vgather
```c
// 预先在 VTCM 中填充 64KB 的 exp2 查找表
uint8_t *vtcm_exp2_table = vtcm_manager_query_area("safe_softmax::exp2_hf_qf16");

// 用 vgather 指令查表
Q6_vgather_ARMVh(&row_buffer0[c/64], (size_t) vtcm_exp2_table, 65535, v_gather_input0);
```

> [!note] baseline vs lut-exp 的区别
> - baseline：用 HVX 指令做多项式近似计算 exp2，纯计算
> - lut-exp：在 VTCM 中预存一个 64KB 的 exp2 查找表，用 vgather 指令查表。对于长 KV 序列，查表比多项式计算更快
>
> 这两种模式共享同一份源码，只是运行时走不同的分支。

### 步骤 3: Rowsum(P)

```c
// 用 qf32 精度累加（比 fp16 精度更高）
HVX_VectorPair vp_p_row0 = hvx_my_vhf_to_wqf32(v_p_row0_hf);
v_p_rowsum0 = Q6_Vqf32_vadd_Vqf32Vqf32(v_p_rowsum0, ...);

// intra-vector 归约
for (int s = 64; s >= 4; s >>= 1) {
    v_p_rowsum0 = Q6_Vqf32_vadd_Vqf32Vqf32(v_p_rowsum0, Q6_V_vlalign_VVR(v_p_rowsum0, v_zero, s));
}
```

---

## 5. 加载 V + PV Accumulation

### 加载 V

```c
// 第 760-804 行
// V 的加载也需要转置：[Bc, D] → [D, Bc]（HMX tile layout）
// 但这次是列主序，因为 V 在 P×V 中是 RHS（右乘）
for (int r = 0; r < n_cols; r += 2) {
    for (int c = 0; c < D; c += 64) {
        // 用 vshuff 把两行数据交错排列到 tile 位置
        const HVX_VectorPair vp = Q6_W_vshuff_VVR(v1, v0, -2);
    }
}
```

### 更新 m 和 l

```c
// 第 820-840 行
for (int i = 0; i < n_row_vec_cnt; ++i) {
    HVX_Vector v_m_prev = mvec_m[i];
    HVX_Vector v_m_curr = Q6_Vhf_vmax_VhfVhf(v_m_prev, mvec_s_rowmax[i]);
    HVX_Vector v_m_diff = Q6_Vqf16_vsub_VhfVhf(v_m_prev, v_m_curr);

    HVX_Vector v_exp_m_diff_hf = hvx_my_exp2_vhf_vqf16(v_m_diff);  // exp(m_old - m_new)

    // l_new = exp(m_old - m_new) * l_old + rowsum(P)
    HVX_Vector v_l_curr = Q6_Vqf16_vmpy_Vqf16Vhf(mvec_l[i], v_exp_m_diff_hf);
    v_l_curr = Q6_Vqf16_vadd_Vqf16Vhf(v_l_curr, mvec_p_rowsum[i]);

    mvec_m[i] = v_m_curr;
    mvec_l[i] = v_l_curr;
    mvec_exp_m_diff[i] = v_exp_m_diff_hf;
}
```

### O = diag(exp(m_old - m_new)) × O_old + P × V

```c
// 第 848-896 行
// 1. 构造对角矩阵 D = diag(exp(m_old - m_new))
for (int i = 0; i < n_row_tiles; ++i) {
    Q6_vscatter_QRMVhV(..., v_offsets, v_content);  // scatter 到对角线位置
}

// 2. HMX 矩阵乘法: O_new = D × O_old + P × V
hmx_unit_acquire();
{
    for (int r = 0; r < n_row_tiles; ++r) {
        for (int c = 0; c < head_dim / 32; ++c) {
            // D × O_old: 对角矩阵乘法
            hmx_load_tiles_fp16(d_tile_in, o_tile_in, n_row_tiles);

            // P × V: 普通矩阵乘法
            for (int k = 0; k < n_col_tiles; k += 32) {
                hmx_load_tiles_fp16(p_tile_in + offset, v_tile_in + offset, n_tiles);
            }

            hmx_consume_accumulator_fp16(o_tile_out);
        }
    }
}
hmx_unit_release();

swap_ptr(&o_tile_curr, &o_tile_prev);  // ping-pong
```

---

## 6. 最终归一化 + 输出

```c
// 第 899-1007 行
// O_final = diag(l^{-1}) × O

// 构造 D = diag(1/l)
for (int i = 0; i < n_row_tiles; ++i) {
    v_content = hvx_my_inv_vhf(Q6_Vhf_equals_Vqf16(mvec_l[i / 2]));
    Q6_vscatter_QRMVhV(..., v_offsets, v_content);
}

// HMX 矩阵乘法
hmx_unit_acquire();
{
    for (int r = 0; r < n_row_tiles; ++r) {
        for (int c = 0; c < head_dim / 32; ++c) {
            hmx_dot_fp16(o_tile_out, d_tile_in, o_tile_in, n_row_tiles);
        }
    }
}
hmx_unit_release();

// 存储回 host 内存（FP16 → FP32 转换）
for (int r = 0; r < n_rows_g; r += 2) {
    const HVX_VectorPair vp = hvx_my_vhf_to_wsf(in_tile[r1 / 2]);  // FP16 → FP32
    *pv_out0++ = Q6_V_lo_W(vp);
    *pv_out1++ = Q6_V_hi_W(vp);
}
```

---

## 性能 Profile

kernel 内部有 8 个计时器，对应 FlashAttention 的 8 个阶段：

| 阶段 | 含义 | 使用的硬件 |
|------|------|-----------|
| `q_load` | 加载 Q 到 VTCM | 内存/DMA |
| `k_load` | 加载 K 到 VTCM（transposed） | 内存/DMA |
| `v_load` | 加载 V 到 VTCM（transposed） | 内存/DMA |
| `qk_dot` | S = Q × K^T | **HMX** |
| `safe_sm` | softmax: mask + rowmax + exp + rowsum | **HVX** |
| `core_acc` | 更新 m, l + O = D×O + P×V | **HVX + HMX** |
| `o_scale` | O = diag(1/l) × O | **HMX** |
| `o_store` | 输出 O 到 host 内存 | 内存 |

这些计时器的数据会通过 `FIG8_ATTENTION_TIMERS` 日志输出，由 Python 工具解析。

> [!next] 下一步
> 想了解更多硬件细节？看 [[05-hardware-accelerators]]
> 想知道怎么跑 benchmark？看 [[07-building-and-running]]
