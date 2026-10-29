# 2. 优化实验

`mat_mul.c` 中包含大量优化实验代码。这些优化针对的是**纯 FP16 矩阵乘法**的性能，按时间顺序逐步加入。

## 优化 1：DMA/VTCM Pipeline

基本思路：用 DMA 异步加载权重，同时 HVX 处理上一批数据。

```
DMA: [加载 block N+1]  [加载 block N+2]  ...
HVX: [处理 block N  ]  [处理 block N+1]  ...
HMX: [计算 block N-1]  [计算 block N  ]  ...
```

通过 `dma_submit_one` + `dma_wait_for_idle` 实现 DMA 和计算的重叠。

## 优化 2：Parallel Weight Publish

权重从 DMA scratch buffer 到 VTCM weight 区域的复制（publish）可以用多线程并行：

```c
// CMake 参数
HTP_FP16_PARALLEL_WEIGHT_PUBLISH=1
```

每个 worker 处理一部分 weight tile 的复制。

## 优化 3：Parallel Output Store

矩阵乘法的结果从 VTCM 写回 DDR 时，也可以多线程并行：

```c
HTP_FP16_PARALLEL_OUTPUT_STORE=1
```

## 优化 4：Activation Cache

对于 LLM 中相邻的 gate_proj 和 up_proj（它们共享同一个 activation），缓存 activation 避免重复的 FP32→FP16 转换：

```
gate_proj: activation → FP16 → VTCM → HMX MMA → output
up_proj:   同一个 activation → 直接复用 VTCM 中的 FP16 版本
```

## 优化 5：Output-Stationary / Split-K

当 `K > N` 时（即矩阵的"内维度"大于"输出维度"），标准的 GEMM 流程效率不高。Output-stationary 方案改变循环顺序：

- 标准：遍历 K 维度，逐步累加到 O
- Output-stationary：每个 O 的 tile 独立计算所有 K 的贡献

Split-K 把 K 维度拆成多个 slice，每个 slice 独立计算，最后归约。

```c
HTP_ENABLE_OUT_STATIONARY_PREFILL=1
```

## 优化 6：Decode Direct Pipeline

Decode 阶段（M=1）的特殊优化：跳过 scratch buffer，DMA 直接到 weight 区域。

```c
HTP_FP16_DECODE_DIRECT_PIPELINE=1
```

## 优化 7：Direct Final DMA

跳过 VTCM 中间步骤，直接从 DMA 输出到 DDR。默认关闭，供 A/B 对比。

```c
HTP_FP16_DIRECT_FINAL_DMA=1
```

## 构建参数一览

这些优化全部通过 `build_pure_fp16.ps1` 的参数控制，不需要修改源码：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\build_pure_fp16.ps1 `
  -DspArch v73 `
  -Fp16WeightLoadMode dma_scratch_hvx `
  -Fp16ParallelWeightPublish 1 `
  -Fp16ParallelOutputStore 1 `
  -MatmulPipelineMode 0 `
  -Fp16OsMBlock 512 -Fp16OsNBlock 1024 -Fp16OsKBlock 1024 `
  ...
```

> [!note] 这些都是实验性优化
> 每个优化都有对应的 CMake 开关，默认值是经过测试的稳定组合。不建议同时打开所有优化——某些组合可能存在交互问题。

> [!next] 下一步
> 怎么用脚本自动化部署和测试？看 [[03-scripts-and-deployment]]
