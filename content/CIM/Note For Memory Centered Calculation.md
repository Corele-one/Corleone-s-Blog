---
source: Onur Mutlu
Property: Overview
---
教授认为计算是一个关于存储的问题，因为存储消耗了计算过程中的大部分能量。所以将我们的注意力集中到以存储为中心的新范式上，能够很好地解决我们目前正在面临的“底层扩展性”的问题。对于未来的展望：
- 存储设备能够自我管理
- 给予存储设备的CIM(Compute in Memory)
也许可以通过以上的几种方法来解决在底层设备scaling过程中导致的能源消耗，也许是跨越计算过程中的bottleneck的一个方法。
![[Energy Comparison.png]]
并且，从当前来看，现在为了克服性能瓶颈，现在才用的一些方法比如多级缓存、pre- fetching还有乱序执行……会让系统的软硬件结构变得越发复杂，会造成大量的能源消耗。大部分功能都用于存储和运输数据，所以内存/存储已经成为了当下计算系统的一大瓶颈。并且复杂运算所用到的能量远远低于访存所用到的能量。所以就会有一个问题：
```
在一个系统中，只有10%-20%的时间和资源是用来完成这个系统所想要实现的功能，那么这个系统是一个好的系统吗？
```
所以在目前的计算系统中，我们遇到的最大问题就是：
==Processing of data is performed far away from the data==
![[Solution.png]]
一个很酷的想法：把加速器看成不同的Agent，在处理过程中彼此交流，构成一个分布式系统。
![[GOAL.png]]

We need intelligence in memory！

![[Romhammer.png]]
Solution to Rowhammer
- 在DDR中集成一个控制器以防止内存访问出现问题
Aging会导致Rowhammer更加严重
还有一个需要考虑的问题就是Read DIsturbance Threshold

## Processing in Memory

![[PIM 2paths.png]]
### Processing near Memory
在封装方面，需要减少垂直方向的互联开销，为逻辑层腾出更多空间

Monolithic Accelerator 统一加速器，但是可重构性不好
异构加速器+中心调度系统
### Processing using Memory

利用存储器的模拟特性来进行计算
![[PIM.png]]

然后还有一个问题是怎么让这些芯片更具编程性？