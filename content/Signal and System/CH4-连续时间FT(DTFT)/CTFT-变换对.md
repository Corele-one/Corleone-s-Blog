
| **信号 x(t)**                                         | **傅里叶变换 X(jω)**                                                                                     | **级数系数 ak​ (若为周期)**               |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------- |
| $\sum_{k=-\infty}^{+\infty} a_k e^{j k \omega_0 t}$ | $2\pi \sum_{k=-\infty}^{+\infty} a_k \delta(\omega - k\omega_0)$                                    | $a_k$                             |
| $e^{j\omega_0 t}$                                   | $2\pi \delta(\omega - \omega_0)$                                                                    | $a_1=1, a_{k\neq 1}=0$            |
| $\cos \omega_0 t$                                   | $\pi [\delta(\omega - \omega_0) + \delta(\omega + \omega_0)]$                                       | $a_1=a_{-1}=\frac{1}{2}$          |
| $\sin \omega_0 t$                                   | $\frac{\pi}{j} [\delta(\omega - \omega_0) - \delta(\omega + \omega_0)]$                             | $a_1=-a_{-1}=\frac{1}{2j}$        |
| $x(t) = 1$                                          | $2\pi \delta(\omega)$                                                                               | $a_0=1, a_{k\neq 0}=0$            |
| **周期方波** (见注1)                                      | $\sum_{k=-\infty}^{+\infty} \frac{2\sin k\omega_0 T_1}{k} \delta(\omega - k\omega_0)$               | $\frac{\sin k\omega_0 T_1}{k\pi}$ |
| $\sum_{n=-\infty}^{+\infty} \delta(t - nT)$         | $\frac{2\pi}{T} \sum_{k=-\infty}^{+\infty} \delta(\omega - \frac{2\pi k}{T})$                       | $a_k = \frac{1}{T}$               |
| **矩形脉冲** (见注2)                                      | $\frac{2\sin \omega T_1}{\omega}$                                                                   | —                                 |
| $\frac{\sin Wt}{\pi t}$                             | $X(j\omega) = \begin{cases} 1, & \lvert\omega\rvert < W \\ 0, & \lvert\omega\rvert > W \end{cases}$ | —                                 |
| $\delta(t)$                                         | $1$                                                                                                 | —                                 |
| $u(t)$                                              | $\frac{1}{j\omega} + \pi \delta(\omega)$                                                            | —                                 |
| $\delta(t - t_0)$                                   | $e^{-j\omega t_0}$                                                                                  | —                                 |
| $e^{-at} u(t)$                                      | $\frac{1}{a + j\omega}$ ($Re\{a\}>0$)                                                               | —                                 |
| $t e^{-at} u(t)$                                    | $\frac{1}{(a + j\omega)^2}$ ($Re\{a\}>0$)<br>[[CTFT-性质]]<br>由频域微分性质可以推导出                           | —                                 |
| $\frac{t^{n-1}}{(n-1)!} e^{-at} u(t)$               | $\frac{1}{(a + j\omega)^n}$ ($Re\{a\}>0$)                                                           | —                                 |
- **注1：周期方波定义**

时域定义为：在 $x(t)$ 的一个周期 $T$ 内，$|t| < T_1$ 时为 $1$，其余部分为 $0$。其频域分布是离散的冲激序列，幅度受 $\text{sinc}$ 函数调制。
[[周期信号的傅里叶变换]]，先求x(t)的傅立叶级数，然后根据傅立叶级数对和FT的关系就可以写出周期方波的傅立叶变换


- **注2：单矩形脉冲定义**
$x(t) = \begin{cases} 1, & |t| < T_1 \\ 0, & |t| > T_1 \end{cases}$
其频谱为连续的 $Sa$ 函数（采样函数）：$X(j\omega) = 2T_1 \text{Sa}(\omega T_1)$。
==2倍的T1即为脉冲下方的面积==
