# 网络结构的变化

[[A Neural Algorithm of Artistic Style]]中的网络结构更像

>noise y→VGG→L→backprop to pixels​

Johnson 引入了一个新的网络$f^W$
​现在可以直接：
$$\boxed{ c \xrightarrow{f_W} \hat y }
$$
也就是说：
输入实拍照片，经过一次 CNN forward pass，直接输出风格化照片。

论文的方法明确有两个组件：
$$\boxed{\text{Transformation Network } f_W}$$
和：
$$\boxed{\text{Loss Network } \phi}$$

其中 transformation network 负责真正把输入图变成输出图：
$$\hat y=f_W(x)$$
而 loss network 是预训练 VGG-16，用来计算 perceptual loss。

![[file-20260913172339813.png]]

Gatys 在推理阶段通过迭代优化求解风格迁移；Johnson 则在训练阶段学习这个求解过程，使推理阶段只需一次前向传播。

# 训练和推理过程

- c：content image，也就是输入的实拍照片
- s：style image，也就是目标风格图，比如《星月夜》
- $f_W$：Transformation Network，也就是负责真正生成风格化图片的网络
- W：Transformation Network 的可训练参数
- $\hat y$：Transformation Network 输出的风格化图片
- ϕ：固定的 VGG loss network
- $L_{\text{content}}$：内容损失
- $L_{\text{style}}$：风格损失
- L：总损失，一般是两者加权和

![[file-20260913173116821.png]]

