# CNN-Content-Style

![[file-20260913155833678.png|500]]

可以把卷积核看成一个滤波器，而这个滤波器可以滤出图片相应的Feature Map，低层次的卷积核可以提取出图片的特征，
一层 CNN 中有很多 convolution filter，每个 filter 产生一张 feature map。浅层主要响应比较简单的视觉模式，例如：
- 边缘
- 颜色
- 简单纹理

而高层次的卷积核Higher layers in the network **capture the high-level content in terms of objects and their arrangement in the input image** but do not constrain the exact pixel values of the reconstruction. 网络越深，representation 越关注图像的实际内容，而不是精确像素值。
# Content-Style

## Content
直接使用 CNN 的 Feature Maps
对于 Content，作者实际上是说：

> “我要保留这一层的 feature response 本身。”

The key finding of this paper is that the **representations of content and style in the Convolutional Neural Network are separable.**
## Style

Content image 和 Style image 都经过同一个固定的预训练 VGG 网络，使用同样的 convolution filters。之所以Style能和Content不一样是因为Style采用了Gram Matrix
真正发生变化的是：
Content直接使用：
$$F^l$$
Style先将：
$$F^l$$
变换成：
$$G^l$$

其中：

![[file-20260913165538939.png]]

这就是 Gram Matrix,对不同 feature maps 做 inner product / correlation.Gram Matrix 丢弃了 feature 的精确空间排列，但保留了不同 feature 之间的统计相关关系。

# Neural Style Transfer

从 white noise image 出发，用 gradient descent 找到另一张图片，使其 feature responses 与原始图片匹配。

![[file-20260913165911372.png]]