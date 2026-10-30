---
drive_id: "19xWQev5yLfzOWeji2EU_XABYXIZ_8It5"
drive_url: "https://drive.google.com/file/d/19xWQev5yLfzOWeji2EU_XABYXIZ_8It5/view?usp=drivesdk"
drive_path: "edge-npu/GEMM.pdf"
pdf_pages: 2
checked_pdf_pages: [1, 2]
---

# GEMM

[打开 Drive 中的 PDF](https://drive.google.com/file/d/19xWQev5yLfzOWeji2EU_XABYXIZ_8It5/view?usp=drivesdk) · 2 页

## 内容介绍

GEMM 的计算与访存笔记：解释 C=αAB+βC、神经网络中的偏置/残差、2MNK 运算量、算术强度，以及 GPU tile 分块和数据复用。

## 主要内容

- 运算定义：解释 C=αAB+βC 中各项，以及偏置、残差等场景为何会出现类似结构。
- 代价估算：按 M、N、K 统计乘加次数与访问的数据量，联系算术强度。
- 分块实现：从输出 tile 出发说明数据复用与 GPU 并行组织。

## 查阅用途

适合在优化矩阵乘前先估计计算量和访存量，再与 Roofline 模型结合判断瓶颈。

## 相关笔记

- [[Roofline Model]]
- [[NPU Behavior]]
