---
drive_id: "19xxWvwJZCrTlB91U26SkDNHsrHJl-a9j"
drive_url: "https://drive.google.com/file/d/19xxWvwJZCrTlB91U26SkDNHsrHJl-a9j/view?usp=drivesdk"
drive_path: "edge-npu/Roofline Model.pdf"
pdf_pages: 2
checked_pdf_pages: [1, 2]
---

# Roofline Model

[打开 Drive 中的 PDF](https://drive.google.com/file/d/19xxWvwJZCrTlB91U26SkDNHsrHJl-a9j/view?usp=drivesdk) · 2 页

## 内容介绍

用 Roofline 模型区分计算受限与带宽受限：定义工作量 W、搬运量 Q、算术强度 W/Q，结合峰值算力和带宽推导性能上界与拐点。

## 主要内容

- 三个基本量：工作量 W、搬运数据量 Q 与算术强度 AI=W/Q。
- 性能上界：将带宽给出的上界与峰值算力比较，取两者中更低的一项。
- Roofline 图：用拐点和运行位置判断 kernel 是带宽受限还是计算受限。

## 查阅用途

适合在分析 GEMM、Prefill 或 Decode 之前建立性能瓶颈的判断框架。

## 相关笔记

- [[GEMM]]
- [[大模型推理流程]]
