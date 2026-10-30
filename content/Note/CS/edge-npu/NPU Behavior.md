---
drive_id: "1Mpnapde_u50_ovd8wC8UoJ3cOCpATQ16"
drive_url: "https://drive.google.com/file/d/1Mpnapde_u50_ovd8wC8UoJ3cOCpATQ16/view?usp=drivesdk"
drive_path: "edge-npu/NPU Behavior.pdf"
pdf_pages: 1
checked_pdf_pages: [1]
---

# NPU Behavior

[打开 Drive 中的 PDF](https://drive.google.com/file/d/1Mpnapde_u50_ovd8wC8UoJ3cOCpATQ16/view?usp=drivesdk) · 1 页

## 内容介绍

NPU 硬件及 FlashAttention-2 映射草图，标注 Scalar、HVX/Vector、Tensor、TCM、DMA 与缓存，按步骤拆解分块注意力中的矩阵乘、归约和数据搬运。

## 主要内容

- 硬件分工：图中区分标量、多线程、向量/HVX、Tensor、DMA、TCM 与缓存。
- 注意力映射：以 FlashAttention-2 前向伪代码为参照拆解 tile 的执行过程。
- 数据流：标注矩阵乘、最大值/求和归约、指数计算以及中间结果的读写。

## 查阅用途

适合回看注意力算子如何落到不同执行单元；图中映射是笔记中的分析草图。

## 相关笔记

- [[大模型推理流程]]
- [[GEMM]]
- [[论文 读]]
