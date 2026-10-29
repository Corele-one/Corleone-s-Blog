# 3. FlashAttention 算法与 Tiling 策略

## 标准 Attention 回顾

对于输入序列 Q, K, V，标准 Attention 计算：

```
S = Q × K^T          // [qo_len, kv_len]，注意力分数
P = softmax(S)       // 注意力权重（每行做 softmax）
O = P × V            // [qo_len, head_dim]，输出
```

问题在于：当 `kv_len` 很大时，S 矩阵（`qo_len × kv_len`）会占用大量内存。对于 `kv_len = 4096`、`head_dim = 128`，S 矩阵有 `4096 × 4096 = 16M` 个元素。

## FlashAttention 的核心思想

FlashAttention 不把完整的 S 矩阵存下来，而是**分块（tiling）**计算：

1. 把 Q 沿序列维度分成大小为 Br 的块
2. 把 K, V 沿序列维度分成大小为 Bc 的块
3. 对每个 Q 块，遍历所有 K/V 块，逐步累积结果
4. 使用 **online softmax**（带 running max 的增量 softmax）保证数值正确性

```c
for each Q block (Br rows):
    初始化 O = 0, m = -inf, l = 0
    for each K/V block (Bc cols):
        S_block = Q_block × K_block^T     // [Br, Bc]
        // 应用 mask
        m_new = max(m, rowmax(S_block))    // 更新行最大值
        P_block = exp(S_block - m_new)     // softmax 分子
        l_new = exp(m - m_new) * l + rowsum(P_block)  // 更新分母
        O = diag(exp(m - m_new)) × O + P_block × V_block  // 更新输出
        m = m_new
        l = l_new
    O = diag(l^{-1}) × O  // 最终归一化
```

> [!tip] Online Softmax
> 关键技巧：每次处理新的 K 块时，用 `exp(m_old - m_new)` 来"修正"之前累积的 O 和 l，而不需要回头重新计算。这保证了最终结果和一次性计算完整 softmax 是数学等价的。

## 本项目的 Tiling 策略

在 `flash_attn.c` 中，tile 大小不是硬编码的，而是根据 VTCM 容量**动态计算**：

```c
// flash_attn.c:67
size_t fa_f16_compute_vtcm_usage(int gqa_factor, int head_dim, int n_rows, int n_cols) {
    const size_t g_br = align_up(gqa_factor * n_rows, HMX_FP16_TILE_N_ROWS);  // Br' = G*Br 对齐到 32

    const size_t qo_tile_size   = align_up(g_br * head_dim * sizeof(__fp16), 4096);    // Q, O: [Br', D]
    const size_t kv_tile_size   = align_up(n_cols * head_dim * sizeof(__fp16), 4096);  // K, V: [Bc, D]
    const size_t core_tile_size = align_up(g_br * n_cols * sizeof(__fp16), 4096);      // S, P: [Br', Bc]
    const size_t d_tile_size    = align_up(g_br * g_br * sizeof(__fp16), 4096);        // D: [Br', Br']
    const size_t col_vec_size   = align_up(g_br * sizeof(__fp16), 256);                // m, l 向量

    size_t total = qo_tile_size * 3 + kv_tile_size * 2 + core_tile_size * 2 +
                   d_tile_size + col_vec_size * 4 + row_vec_size * 2 + 512;
    return total;
}
```

VTCM 大小通常是 4-6 MB，每个 worker 分配 1 MB。`find_chunk_size_common` 先增大 Br（行块大小），再增大 Bc（列块大小），直到 VTCM 装不下为止：

```c
// flash_attn.c:86
void find_chunk_size_common(..., size_t limit, ...) {
    size_t nr = nr_unit, nc = nc_unit;

    // 先增大 Br
    for (; nr <= max_nr; nr += nr_unit) {
        if (compute_vtcm_usage(..., nr, nc) > limit) break;
        nr_ok = nr;
    }
    // 再增大 Bc
    for (; nc <= max_nc; nc += nc_unit) {
        if (compute_vtcm_usage(..., nr_ok, nc) > limit) break;
        nc_ok = nc;
    }
}
```

### 典型 tile 大小

对于 `head_dim=128, n_heads=12, n_kv_heads=2`（GQA factor G=6）：
- `nr_unit = ceil(32 / 6) = 6`（因为 HMX tile 是 32×32，G*Br 需要对齐到 32）
- `nc_unit = 64`
- 典型 Br ≈ 6-24，Bc ≈ 64-256，取决于 VTCM 剩余空间

## VTCM 内存布局

处理一个 Q 块时，VTCM 中的 buffer 布局：

```
VTCM (每 worker ~1MB):
┌──────────────────────────────────────────────────┐
│ q_tile   [Br', D]        ← Q 块（从 host 内存加载）  │
│ o_tile0  [Br', D]        ← O 累积 buffer 0          │
│ o_tile1  [Br', D]        ← O 累积 buffer 1（交替使用）│
│ k_tile   [Bc, D]         ← K 块（transposed）        │
│ v_tile   [Bc, D]         ← V 块                      │
│ s_tile   [Br', Bc]       ← S = Q×K^T 中间结果        │
│ p_tile   [Br', Bc]       ← P = softmax(S)            │
│ d_tile   [Br', Br']      ← 对角缩放矩阵 D             │
│ mvec_m   [Br']           ← running max 向量           │
│ mvec_l   [Br']           ← running sum 向量           │
│ mvec_s_rowmax [Br']      ← 当前块的 rowmax             │
│ mvec_p_rowsum [Br']      ← 当前块的 rowsum             │
│ row_buffer0, row_buffer1 ← HVX 行处理 buffer          │
│ hmx_output_scales        ← HMX 缩放参数               │
└──────────────────────────────────────────────────┘
```

> [!note] 为什么要两个 o_tile？
> 在累积 `O = diag(exp(m_old - m_new)) × O + P × V` 时，需要读旧 O 写新 O。用两个 buffer 交替（ping-pong），避免 in-place 读写冲突。

## GQA（Grouped Query Attention）处理

GQA 时 `n_heads > n_kv_heads`，比如 12 个 Q head 共享 2 个 KV head。kernel 用 `G = n_heads / n_kv_heads` 来处理：

- 每次处理一个 KV head（`kv_head_idx` 从 0 到 `n_kv_heads - 1`）
- 对应的 G 个 Q head 一起加载到 VTCM
- `g_br = align_up(G * Br, 32)` 确保对齐到 HMX tile 边界

## 多线程并行

```c
// flash_attn.c:1634
const int n_workers = num_hvx128_contexts;  // 通常 4-8 个 HVX context
state.n_tasks = n_kv_heads;  // 每个 KV head 一个任务

// worker 函数：每个 worker 独立处理一个 KV head
static void simple_flash_attn_worker(void *dptr) {
    while (1) {
        unsigned int task_id = worker_pool_atomic_inc_return(&(s->task_id)) - 1;
        if (task_id >= s->n_tasks) break;
        int kv_head_idx = task_id;
        simple_flash_attn_f16_core(kv_head_idx, ...);
    }
}
```

每个 worker 有自己独立的 VTCM 空间（1 MB），互不干扰。并行粒度是 **KV head 级别**——如果 `n_kv_heads = 2` 而 `n_workers = 4`，则 2 个 worker 各处理一个 KV head，另外 2 个空闲。

> [!next] 下一步
> 现在你理解了算法和 tiling 策略，接下来看 kernel 的逐行实现：[[04-kernel-deep-dive]]
