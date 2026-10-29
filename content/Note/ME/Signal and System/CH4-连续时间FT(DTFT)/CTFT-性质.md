# 傅里叶变换公式
$$\boxed{x(t)\:=\:\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(\:\mathrm{j}\omega)\mathrm{e}^{\:\mathrm{j}\omega t}\mathrm{d}\omega}$$
$$\boxed{X(j\omega)=\int_{-\infty}^{+\infty}x(t)\mathrm{e}^{-j\omega t}\mathrm{d}t}$$
# 傅里叶变换的性质

| **性 质**     | **时域信号 x(t)**                       | **频域变换 X(jω)**                                                                                                                                                   |
| ----------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **基础定义**    | $x(t)$                              | $X(j\omega)$                                                                                                                                                     |
| **线性**      | $ax(t) + by(t)$                     | $aX(j\omega) + bY(j\omega)$                                                                                                                                      |
| **时移**      | $x(t - t_0)$                        | $e^{-j\omega t_0} X(j\omega)$                                                                                                                                    |
| **频移**      | $e^{j\omega_0 t} x(t)$              | $X(j(\omega - \omega_0))$                                                                                                                                        |
| **共轭**      | $x^*(t)$                            | $X^*(-j\omega)$                                                                                                                                                  |
| **时间反转**    | $x(-t)$                             | $X(-j\omega)$                                                                                                                                                    |
| **尺度变换**    | $x(at)$                             | $\frac{1}{\lvert a \rvert} X\left(\frac{j\omega}{a}\right)$                                                                                                      |
| **卷积**      | $x(t) * y(t)$                       | $X(j\omega) Y(j\omega)$                                                                                                                                          |
| **相乘**      | $x(t)y(t)$                          | $\frac{1}{2\pi} X(j\omega) * Y(j\omega)$                                                                                                                         |
| **时域微分**    | $\frac{d}{dt} x(t)$                 | $j\omega X(j\omega)$                                                                                                                                             |
| **时域积分**    | $\int_{-\infty}^t x(\tau) \, d\tau$ | $\frac{1}{j\omega} X(j\omega) + \pi X(0) \delta(\omega)$                                                                                                         |
| **频域微分**    | $tx(t)$                             | $j \frac{d}{d\omega} X(j\omega)$                                                                                                                                 |
| **实信号共轭对称** | $x(t) \in \mathbb{R}$               | $\begin{aligned} X(j\omega) &= X^*(-j\omega) \\ \lvert X(j\omega) \rvert &= \lvert X(-j\omega) \rvert \\ \angle X(j\omega) &= -\angle X(-j\omega) \end{aligned}$ |
| **实偶信号**    | $x(t) = x(-t)$                      | $X(j\omega)$ 为实偶函数                                                                                                                                               |
| **实奇信号**    | $x(t) = -x(-t)$                     | $X(j\omega)$ 为纯虚奇函数                                                                                                                                              |
| **奇偶分解**    | $x_e(t), x_o(t)$                    | $Re\{X(j\omega)\}, jIm\{X(j\omega)\}$                                                                                                                            |
**帕斯瓦尔定理 (Parseval's Relation):**

$$\int_{-\infty}^{+\infty} |x(t)|^2 \, dt = \frac{1}{2\pi} \int_{-\infty}^{+\infty} |X(j\omega)|^2 \, d\omega$$

---
## 线性性质

![[file-20260507233029101.png|500]]
## 傅里叶变换的时移与频移性质

![[22b3a9eed01d9418be04344e81737b98_720.png]]
## 共轭与共轭对称性
 ![[c8e6516ed0a6e32074e3995065902f50_720.png]]
 ![[file-20260507234118744.png|416]]
 共轭对称性的外推结论：
 ![[file-20260507234237547.png]]
## 微分与积分性质
微分性质：
![[file-20260507234327258.png]]

积分性质：
![[file-20260507234354305.png]]
## 时间与频率的尺度变换
![[file-20260507234434440.png]]

时域压缩，频域扩展
![[file-20260507234441963.png]]
在时间上反转一个信号，在频域上它的傅里叶变换也反转
## 对偶性
![[file-20260508002330695.png]]

## 帕斯瓦尔定理
![[file-20260507235020980.png]]

## 时域卷积相当于频域相乘
![[file-20260507235216251.png]]

## 时域相乘$\to$频域卷积再除以$2\pi$（调制性质）
![[file-20260507235536928.png]]
 ==两个信号相乘可以理解为用一个信号去调制另一个信号的振幅，也被成为幅度调制，上式有时也称为调制性质==
 调制性质可以用于分离不同载波上的信号
 ![[1b74ecb1bb50b6242e26bbd53f8ce3e5_720.png]]
 
## 可变中心频率的频率选择滤波器
 ![[file-20260508000902434.png]]
 