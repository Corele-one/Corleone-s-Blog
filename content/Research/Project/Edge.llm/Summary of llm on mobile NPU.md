
| 论文                                            | 核心问题                                                           | 路线定位                                                    |
| --------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------- |
| **llm.npu**                                   | 手机端 LLM 的 **prefill** 很慢，CPU/GPU 不够并行，NPU 有潜力但直接 offload 不work | 第一步：让 mobile NPU 真正能跑 LLM prefill                       |
| **T-MAN**                                     | low-bit LLM 想端到端跑在 NPU 上，但 decoding 的 dequantization / GEMV 很差 | 第二步：从 prefill 扩展到 **prefill + decoding end-to-end NPU** |
| **ShadowNPU / shadowAttn**                    | 即使非 attention 上了 NPU，attention 仍因量化敏感而 fallback 到 CPU/GPU      | 第三步：补齐 NPU-centric inference 中的 **attention 缺口**        |
| **Scaling Test-Time Compute with Mobile NPU** | 小模型质量不够，大模型太贵；NPU decoding 阶段矩阵单元闲置                            | 第四步：不只是加速，而是用 NPU 空闲算力做 **test-time scaling 提升质量**      |

---

## 1. llm.npu：Fast On-device LLM Inference with NPUs

### Motivation

llm.npu 的核心 motivation 是：**手机端 LLM 的主要瓶颈不是大家常优化的 decoding，而是 prefill**。论文分析 UI automation、context-aware QA / email reply、chat summary 等移动场景，发现这些任务通常有长 prompt、短输出；在 CPU 上 prefill 占总时延的 88.3%–98.8%，即使在 GPU 上也占 54.2%–91.7%。所以它把目标聚焦到“如何把 prefill 搬到移动 NPU 上”。

这里的关键机会是 mobile NPU：它的 INT8 矩阵计算能力和能效都更适合 prefill 的大矩阵计算，而且不像 GPU 那样容易和 UI/rendering 抢资源。但论文发现，**直接把 LLM prefill offload 到 NPU 反而会变慢**，所以问题不是“有没有 NPU”，而是“LLM 的执行形态和 NPU 的静态图、低精度整数计算范式严重不匹配”。

### Previous work limitation

已有工作的问题主要有三类。第一，移动 NPU 通常要求 **static shape / static graph**，但 LLM prompt 长度是动态的；每次不同长度都重新 build/optimize graph 很贵，统一 padding 又浪费计算。第二，LLM 为了精度通常需要 AWQ / K-Quant 这类 per-group quantization，但 NPU 不擅长 per-group MatMul，必须拆成多个小 MatMul 再做浮点 reduction，不能充分利用 NPU。第三，LLM 里 Attention、LayerNorm 等浮点算子仍然存在，而 mobile NPU 的强项是 INT8，不是 FP。

此外，已有 decoding 优化，如 speculative decoding、activation sparsity 等，主要针对 token generation；而 llm.npu 指出的移动端场景瓶颈在 prefill，因此这些工作不能直接解决主要问题。相关的 PowerInfer-V2 虽然也用 NPU 做部分 prefill，但没有系统性处理 variable prompt、outlier、CPU/NPU scheduling 这些移动 NPU 特有问题。

### Solution

llm.npu 的 solution 是 **三层重构：prompt-level、tensor-level、block-level**。

第一，**chunk-sharing graph**：把 variable-length prompt 切成 fixed-size chunks，提前为 chunk 构建 NPU graph；同时区分可共享的 static ops 和不可共享的 dynamic ops，减少 graph 数量和内存占用。

第二，**shadow outlier execution**：主路径仍用 per-tensor INT8 MatMul 跑在 NPU 上，以便充分利用 NPU；但 activation outlier 很稀疏，所以把 outlier channel 抽出来，在 CPU/GPU 上用浮点并行补偿。论文观察到一次 inference 中只有约 0.1%–0.3% channel 有 outlier，且少数 hot channels 贡献了大部分 outlier，因此可以只保留 hot-channel weights，并通过 pruning 去掉不重要 outlier 来降低同步开销。

第三，**out-of-order subgraph execution**：把 chunk 内、chunk 间的 CPU/GPU 和 NPU 子图调度成 out-of-order 执行，目标不是最大化所有处理器并行度，而是减少 NPU critical path bubble。论文中的示意显示 naive overlapping 会有较高 bubble，而 out-of-order 调度能明显降低 bubble。

### Evaluation

Evaluation 很完整。实现上，llm.npu 基于 MLLM 和 Qualcomm QNN，约 10K 行 C/C++/assembly；测试了 Qwen1.5-1.8B、Gemma-2B、Phi-2-2.7B、LLaMA-2-7B、Mistral-7B，设备包括 Redmi / Xiaomi 系列 Snapdragon 手机，baseline 包括 llama.cpp、TFLite、MNN、MLC-LLM、PowerInfer-V2。

核心结果是：在 1024-token prompt 下，llm.npu 相比 CPU baseline 快 7.3×–18.4×，相比 GPU baseline 快 1.3×–43.6×；能耗降低 1.9×–59.5×；首次在商用手机 NPU 上实现 billion-size LLM prefill 超过 1000 tokens/s；端到端真实应用中 latency 降低 1.4×–32.8×，且相对 FP16 精度损失小于 1%。

Ablation 也很有说服力：naive NPU offload 反而比 CPU 慢 2.55×–2.68×；chunk-sharing graph 带来 1.46×–5.09× 提升；shadow outlier execution 降低 prefill latency 3.91×–8.68×；out-of-order subgraph execution 再降低 18%–44%。这说明它的贡献不是“用了 NPU”，而是解决了 NPU 不能直接跑 LLM 的结构性 mismatch。

**一句话总结**：llm.npu 的价值在于把 mobile NPU 从“理论上有算力”变成“实际能加速 LLM prefill”。

---

## 2. T-MAN：Enabling End-to-End Low-Bit LLM Inference on NPUs via Unified Table Lookup

### Motivation

T-MAN 的 motivation 是在 llm.npu 之后更进一步：**不仅 prefill 要上 NPU，decoding 也应该端到端留在 NPU 上**。现实部署中的 on-device LLM 普遍依赖 4-bit、2-bit 甚至更低 bit 的权重表示，但 NPU 的硬件格式和这些灵活 low-bit quantization 格式并不匹配。T-MAN 的核心 insight 是：low-bit 的取值空间很小，因此可以用 lookup table 把 NPU 不擅长的 dequantization / flexible quantization 计算编码成查表操作。

它和 llm.npu 的差异在于：llm.npu 主要解决 prefill；T-MAN 关注 **prefill + decoding 的 end-to-end NPU execution**，尤其是 decoding 阶段 GEMV / dequantization 的问题。

### Previous work limitation

T-MAN 批评了两类已有做法。第一类是 **dequantization-based low-bit inference**：把 low-bit 权重在线 dequantize 成 NPU 支持的格式。问题是 decoding 阶段是 memory-bound GEMV，矩阵核优势用不上，dequantization 开销反而主导；论文测到一个 W4A16 mixed-precision GEMV kernel 在 NPU 上比 CPU 慢 3.8×，原因是 NPU dequantization 慢 10×。

第二类是 **硬件格式对齐**，例如 QNN 强制用 NPU 支持的 per-channel / per-tensor quantization。这样可以避免 dequantization，但会损失精度；论文指出 QNN 的 per-channel INT4 weight + per-tensor INT16 activation 会带来 1.45× 更差 perplexity。

第三类是 hybrid 方案，比如 llm.npu：prefill 在 NPU，decoding 和 outlier 在 CPU。它虽然改善 latency，但会增加 CPU 活跃能耗，也需要维护 NPU/CPU 两份不同格式的权重。T-MAN 的评测里，llm.npu 在一些 8B 模型上还会因为同时存 INT8 prefill 权重和 INT4 decode 权重而 OOM。

### Solution

T-MAN 的 solution 是 **unified table lookup**。它试图用一份统一 low-bit weight layout 同时服务 prefill 和 decoding：prefill 阶段仍然用 dequantization-based GEMM 充分利用 NPU matrix core；decoding 阶段则用 LUT-based GEMV 映射到 NPU vector core，从而消除在线 dequantization 的主要开销。

具体技术有两点。第一，**fused two-level LUT dequantization**：把 low-bit value 到 FP16 / INT 表示的转换，以及 scale / zero-point 的 affine transform 融合到 LUT 里，减少大量浮点操作。 第二，**concurrency-hierarchy-guided tiling**：针对 NPU 的 DMA、vector core、matrix core 层次结构设计统一 tiling，让 prefill 的 matrix-core execution 和 decoding 的 vector-core LUT execution 都能高效访问 on-chip memory。T-MAN 还用 DMA–DQ–MM 三阶段 pipeline 隐藏 weight loading 和 dequantization latency。

### Evaluation

T-MAN 的 evaluation 更偏 end-to-end low-bit inference。硬件上测试 OnePlus 12 / Snapdragon 8 Gen 3 和 OnePlus 13T / Snapdragon 8 Elite；模型包括 Qwen3-8B、Llama-3.1-8B-Instruct、BitNet-2B；baseline 包括 QNN、llm.npu、llama.cpp、T-MAC、bitnet.cpp。

性能上，decoding 阶段 T-MAN 相比 QNN 快 1.5×–1.8×，相比 llm.npu 快 3.1×–3.8×；BitNet-2B 在 Snapdragon 8 Gen 3 上达到 49.1 tokens/s。prefill 阶段相较 llm.npu 最高 1.4×，相较 CPU 框架最高 15×；mpGEMM 上最高可比 CPU-only 框架快 30×。

能耗结果也很关键：相比 CPU-only bitnet.cpp，T-MAN 平均功耗降低 40%，结合性能提升后，prefill 能耗降低 24.5×、decoding 能耗降低 4.9×；相比 hybrid NPU-CPU 的 llm.npu，prefill 能耗节省 71%，decoding 能耗节省 84%。

精度方面，T-MAN 的 per-block WINT2 甚至比 QNN 的 per-channel WINT4 有更低 WikiText2 PPL：Llama-3.1-8B-Instruct 为 12.81 vs 18.62，Qwen3-8B 为 13.14 vs 25.37。也就是说它不是用精度换速度，而是通过支持更合适的 quantization granularity 同时改善精度和性能。

**一句话总结**：T-MAN 解决的是“如何让 low-bit LLM 的 prefill 和 decoding 都留在 NPU 上”，路线比 llm.npu 更 end-to-end，也更偏低比特 kernel / layout 设计。

---

## 3. ShadowNPU / shadowAttn：NPU-Centric On-Device LLM Inference

### Motivation

ShadowNPU 的 motivation 是：即使有了 llm.npu，系统仍然不够 NPU-centric，因为 **attention 仍然大量 fallback 到 CPU/GPU**。原因是 attention 涉及 Q/K/V 多个 activation tensor，对量化非常敏感；直接把 attention 用 INT8 per-tensor static graph 跑在 NPU 上，会带来平均 18 percentage points 的 accuracy drop。

它的机会来自 attention sparsity：attention score 高度偏斜，只有少部分 token 重要。如果只在 CPU/GPU 上计算重要 token 的高精度 sparse attention，就能减少 CPU/GPU 依赖。但难点是：要先估计哪些 token 重要，而这个 estimation 本身也很贵。论文显示，在 20% sparsity，也就是剪掉 80% token 的情况下，estimation 占 attention 总计算的 66.7%。粗粒度 block sparse 虽然能减少 estimation，但会漏掉重要 token，导致明显 accuracy drop。

### Previous work limitation

ShadowNPU 认为已有路线各有缺陷。llm.npu、HeteroLLM 这类系统把 attention 留在 CPU/GPU，因此不能真正 NPU-centric；QNN / PowerInferV2 这类 NPU-Full attention 会遭遇 attention quantization 的精度下降；普通 sparse attention 的 estimation 仍然在 CPU/GPU 上，开销太大；block sparse attention 估计太粗，容易错过重要 token；learned sparse attention 又需要训练，迁移到不同下游任务和 fine-tuned model 不方便。

此外，NPU 的 static compute graph 也和 attention 的动态输入冲突：Q/K 的 scale factor 和 shape 会变化，如果只用一个固定 scale 的 graph，精度和利用率都会下降。

### Solution

shadowAttn 的核心 insight 是：**判断 token 重要性只需要 attention score 的相对大小，不需要精确 attention 输出**。因此，top-k estimation 比完整 QKV attention 更能容忍 INT8 量化误差。它先把 Q/K 做 INT8 量化，在 NPU 上跑 dense Q·K estimation；然后把 top-k 位置交给 CPU/GPU；最后 CPU/GPU 只对这些重要 token 做高精度 sparse QKV。

论文还做了三类设计。第一，**head-specific sparsity ratio**：不同 head / layer 重要性不同，因此每个 head 的 sparsity ratio 通过离线 profiling 决定。第二，**NPU compute graph bucketing**：离线为不同 scale factor / shape 建多个 bucket，在线选择最接近输入 scale 的 graph。第三，**head-wise NPU–CPU/GPU pipeline**：重叠 NPU estimation、CPU/GPU top-k、CPU/GPU sparse attention，并把同 scale 的 NPU kernels 一次性 launch，以减少 pipeline bubble。

一个很强的支撑结果是：用 NPU INT8 per-tensor quantization 来预测 Q·K 中重要位置，平均 recall 超过 99%，说明“用 NPU 做 estimation，而不是完整 attention”这个拆分是合理的。

### Evaluation

ShadowNPU 的 evaluation 重点是 attention module 和集成到 llm.npu 后的 end-to-end 效果。实现约 10K 行 C++/Python；设备包括 MI14 / Snapdragon 8 Gen 3 和 Redmi K60 Champion Edition / Snapdragon 8 Gen 2；模型包括 Qwen2-0.5B/1.5B、PhoneLM-0.5B/1.5B；任务包括 ArxivSum、DroidCall、Octopus。实验中特意限制 CPU/GPU 资源，只用一个中核 CPU 做必要控制和 sparse compute，其余尽量放在 NPU。

精度方面，Table 6 显示 shadowAttn 平均结果为 36.4，接近 lossless C/G-Full 的 36.8，平均只损失 0.4 pp；相比之下 C/G-Sparse 平均 29.4、C/G-Block-Sparse 25.4、NPU-Full 18.8。

性能方面，在有限 CPU/GPU 资源下，shadowAttn 相比 C/G-Full 最高 4.5×、平均 2.9× 更快；attention breakdown 最高 6.9×；能耗最高降低 7.7×。与 llm.npu 原生 attention 相比，它只用一个 middle CPU core 就能达到最高 3.0× 更低 latency。

**一句话总结**：ShadowNPU 不是替代 llm.npu，而是补它的短板：让 attention 也尽可能 NPU-centric，减少 CPU/GPU fallback。

---

## 4. Scaling LLM Test-Time Compute with Mobile NPU on Smartphones

### Motivation

这篇的 motivation 和前三篇不太一样。前三篇主要是“同一个模型怎么更快、更省电”；这篇关心的是：**手机端小模型能力不够，大模型又太贵，能不能利用 NPU 的空闲算力在 test time 提升模型质量？**

论文指出，test-time scaling 通过生成多条路径、选择更好答案来提升模型能力，比如 Best-of-N、Beam Search、自一致性等。但这些方法通常假设云端或离线环境有大量计算资源。手机端看似不适合做 test-time scaling，因为本来就资源受限；不过作者观察到 mobile NPU 在 LLM decoding 阶段存在大量闲置矩阵计算能力。原因是 decoding 时 GEMM 退化成 GEMV，大 tile matrix unit 利用率低。

换句话说，这篇的核心问题不是“怎样让单条 decoding 更快”，而是：**能不能把 decoding 阶段浪费掉的矩阵算力用于并行采样，从而让小模型接近或超过大模型效果？**

### Previous work limitation

已有 test-time scaling 方法主要面向 server-class GPU，默认有足够并行计算和显存；而手机端有两个 NPU 特有问题。第一是 **precision**：移动 NPU 原本支持的是 coarse-grained quantization，例如 per-channel / per-tensor，但现代 LLM 低比特部署常需要 fine-grained group quantization。论文给出 Llama3.2-1B-Instruct 的例子：QNN W4A16 在 MATH500 上只有 2.1，而 AutoAWQ W4A16 有 15.9；GSM8K 上 QNN 为 3.4，而 AutoAWQ 为 32.6。

第二是 **efficiency**：NPU matrix unit 很强，但 vector unit 的通用计算和内存访问能力弱；test-time scaling 会放大 Softmax、dequantization、attention 等非矩阵计算瓶颈。论文还指出 fine-grained quantization group 太小，不能填满 128-byte vector register，会导致低效内存访问；FlashAttention breakdown 中 Softmax 在更大 query batch 下成为主要瓶颈。

### Solution

这篇提出一个面向 Qualcomm Snapdragon NPU 的 end-to-end inference system，主要使用 **weight-only 4-bit fine-grained group quantization**，并做两类硬件感知优化。

第一，**hardware-aware tile quantization**：把 quantization group 对齐到 HMX/HVX 的 tile 和 memory access pattern；还把 8 个 fine-grained quantization groups 合成一个 super-group，让 256 个连续 INT4 values 正好填满一个 HVX vector register。

第二，**LUT-based computation**：用 LUT / vector gather 替代 Softmax 里的 exponential computation，以及 mixed-precision GEMM 里的 dequantization，从而减少 vector unit 上的复杂计算。系统实现上，它给 llama.cpp 增加 Hexagon NPU backend，利用 rpcmem shared memory 避免 CPU–NPU 间不必要的数据拷贝，并允许未实现的算子 fallback 到 CPU。

### Evaluation

实验设备覆盖三代 Snapdragon：OnePlus Ace3 / Snapdragon 8 Gen 2，OnePlus 12 / Snapdragon 8 Gen 3，OnePlus Ace5 Pro / Snapdragon 8 Elite。模型主要是 Qwen2.5-1.5B/3B、Llama3.2-1B/3B，也额外用 Qwen2.5-7B 做 accuracy-cost trade-off；test-time scaling 任务包括 MATH500 和 GSM8K。

Operator-level 结果很强：mixed-precision GEMM 最高 19.0× speedup，Softmax 最高 2.2×；Softmax LUT exp 相比 F32 exp 快 1.26×–2.19×，相比 F16 exp 最高快 1.60×；dequantization layout 优化在不同矩阵尺寸下达到 9.65×–19.04× speedup。

更重要的是 end-to-end 质量/成本曲线：论文展示小模型加 test-time scaling 后，可以达到甚至超过更大模型不 scaling 的 accuracy-cost Pareto frontier。能耗上，Qwen2.5-1.5B 在 batch size 8 时的 decoding energy 低于 Qwen2.5-3B batch size 1，但数学任务 test-time scaling accuracy 可以接近 3B base。

这篇也有一个明显 limitation：目前 lm_head / logits computation 保守地放在 CPU 上，因为 Hexagon NPU 32-bit virtual address space 对完整 logits tensor 不友好；当 batch size = 16 时，CPU logits 计算时间接近或超过 50%，后续如果能把 logits 放到 NPU，scaling 特性还会更好。

**一句话总结**：这篇把 mobile NPU 从“加速器”变成“质量提升器”：利用 decoding 阶段闲置矩阵算力，让小模型通过 test-time scaling 获得更好的 accuracy-cost trade-off。

---
