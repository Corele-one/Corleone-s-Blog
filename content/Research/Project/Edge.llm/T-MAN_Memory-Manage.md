# §2.3 Snapdragon NPU
>硬件组成

1个32x32的HMX，矩阵计算单元，4-6个HVX单元(1x256 tile)，以及标量计算单元

![[file-20260811214710509.png]]



>硬件内存层级

每个计算单元都拥有其专属的寄存器堆。向量寄存器和标量寄存器可容纳 4 至 6 个上下文，支持 4 至 6 个硬件线程并发运行。寄存器之下是容量为 8 MB、由软件管理的片上存储器，即紧耦合存储器（TCM）；该存储器至 HMX 的突发传输宽度为 2 KB，与 HMX 和 HVX 的宏计算宽度相匹配。此外，向量单元和标量单元还共享一个容量为 1 MB、访问宽度为 128 B 的通用二级缓存（L2 cache）。数据从片外 DDR 加载至 TCM 通过 DMA 通道进行，带宽可达 40-60 GB/s；而加载至二级缓存的带宽则可达 20-30 GB/s

![[file-20260812163945207.png]]

- 寄存器
- **TCM**：约 8 MB、软件管理的片上存储
- **L2**：约 1 MB、共享缓存
- **DDR**：模型权重和大容量数据所在的外部内存
- DDR→TCM 使用 DMA；论文给出 TCM→HMX 的 2 KB burst 设计背景。  

# §4.1 NPU concurrency hierarchy / Unified tiling strategy
>根据寄存器、TCM 容量、并发线程和 DMA 连续访问，设计 tile 和数据布局。


# §4.2 Pipelining to Hide Dequantization Overhead
>数据搬运中的三级流水

# §4.3 和 §5 Mapping / Asynchronous DMA




# Take-out






> How to Pipeline

```
DDR 中的 K/V cache tile
  → DMA 预取进 TCM
  → HVX/HMX 计算 QKᵀ 与 softmax / PV
  → 下一 KV tile 同时 DMA
```
  
