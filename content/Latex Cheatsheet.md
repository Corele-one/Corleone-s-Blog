# LaTeX Cheatsheet

---

## 1. 文档基本结构

```latex
\documentclass[12pt, a4paper]{article}  % 文档类：article / report / book
\usepackage[UTF8]{ctex}                 % 中文支持
\usepackage{amsmath}                     % 数学公式扩展
\usepackage{graphicx}                    % 插入图片
\usepackage{hyperref}                    % 超链接

\title{标题}
\author{作者}
\date{\today}

\begin{document}
\maketitle
\tableofcontents  % 目录

\section{章节标题}
正文内容...

\subsection{子章节}
更多内容...

\end{document}
```

**常用文档类：**

| 文档类 | 用途 |
|--------|------|
| `article` | 短文、论文 |
| `report` | 长报告（含 \chapter） |
| `book` | 书籍 |
| `beamer` | 幻灯片 |
| `letter` | 信件 |

---

## 2. 字体与文字格式

```latex
\textbf{粗体}              % **粗体**
\textit{斜体}              % *斜体*
\underline{下划线}          % 下划线
\tt{等宽字体}              % 等宽
\textsc{小型大写字母}       % Small Caps

{\large 大字体}             % 局部放大
{\small 小字体}             % 局部缩小
{\tiny 极小}                % 极小字体
{\Huge 巨大}                % 巨大字体

% 常用字号：\tiny < \scriptsize < \footnotesize < \small < \normalsize
%          < \large < \Large < \LARGE < \huge < \Huge
```

---

## 3. 数学公式

### 3.1 行内与行间公式

```latex
% 行内公式（在文字中）
$E = mc^2$，或者 \(E = mc^2\)

% 行间公式（独占一行，不带编号）
$$E = mc^2$$，或者 \[E = mc^2\]

% 行间公式（带编号）
\begin{equation}
E = mc^2
\end{equation}
```

### 3.2 上下标与分数

```latex
x^{2}           % 上标：x²
x_{i}           % 下标：xᵢ
x^{2}_{i}       % 同时：xᵢ²
\frac{a}{b}     % 分数：a/b
\sqrt{x}        % 平方根
\sqrt[3]{x}     % 三次方根
```

### 3.3 希腊字母

```latex
\alpha \beta \gamma \delta \epsilon \zeta \eta \theta
\iota \kappa \lambda \mu \nu \xi \pi \rho \sigma \tau
\upsilon \phi \chi \psi \omega

% 大写：首字母大写
\Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Phi \Psi \Omega
```

### 3.4 常用数学符号

```latex
% 运算
\times   \div    \pm     \mp     \cdot
\oplus   \otimes \cup    \cap

% 关系
\leq     \geq    \neq    \approx \equiv
\sim     \propto \ll     \gg

% 逻辑
\forall  \exists \neg    \land   \lor
\implies \iff    \Rightarrow \Leftarrow

% 集合
\in      \notin  \subset \supset \subseteq \supseteq
\emptyset \mathbb{N} \mathbb{Z} \mathbb{Q} \mathbb{R} \mathbb{C}

% 箭头
\rightarrow \leftarrow \Rightarrow \Leftarrow
\leftrightarrow \mapsto \uparrow \downarrow

% 其他
\infty   \partial \nabla  \ldots  \cdots  \vdots \ddots
```

### 3.5 求和、积分、极限

```latex
\sum_{i=1}^{n} x_i          % 求和
\prod_{i=1}^{n} x_i         % 连乘
\int_{a}^{b} f(x) \, dx     % 定积分
\int f(x) \, dx              % 不定积分
\iint f(x,y) \, dxdy        % 二重积分
\oint \vec{F} \cdot d\vec{r} % 曲线积分
\lim_{x \to \infty} f(x)    % 极限
\lim_{x \to 0^{+}} f(x)     % 右极限

% 行内模式下，上下标会变小，用 \displaystyle 强制大号
$\displaystyle\sum_{i=1}^{n} i^2$
```

### 3.6 矩阵

```latex
\begin{bmatrix}        % 方括号矩阵
  a & b \\
  c & d
\end{bmatrix}

\begin{pmatrix}        % 圆括号矩阵
  a & b \\
  c & d
\end{pmatrix}

\begin{vmatrix}        % 行列式
  a & b \\
  c & d
\end{vmatrix}

% 多行多列用 & 分隔列，\\ 分隔行
\begin{bmatrix}
  1 & 2 & 3 \\
  4 & 5 & 6 \\
  7 & 8 & 9
\end{bmatrix}
```

### 3.7 多行公式对齐

```latex
\begin{align}
  a &= b + c \label{eq1}  % & 对齐点，\\ 换行
    &= d + e               % 续行对齐到同一个 =
\end{align}

% 不带编号用 align*
\begin{align*}
  f(x) &= x^2 + 2x + 1 \\
       &= (x+1)^2
\end{align*}
```

### 3.8 分段函数

```latex
f(x) = \begin{cases}
  x^2,       & x \geq 0 \\
  -x^2,      & x < 0
\end{cases}
```

### 3.9 常用数学函数

```latex
\sin \cos \tan \cot \sec \csc
\arcsin \arccos \arctan
\log \ln \exp \lg
\max \min \sup \inf
\det \dim \ker \deg
```

### 3.10 括号自适应大小

```latex
\left( \frac{a}{b} \right)         % 自动匹配大小的圆括号
\left[ \frac{a}{b} \right]         % 方括号
\left\{ \frac{a}{b} \right\}       % 花括号（需转义）
\left| \frac{a}{b} \right|         % 绝对值
\left\langle \frac{a}{b} \right\rangle % 尖括号
```

---

## 4. 列表

```latex
% 无序列表
\begin{itemize}
  \item 第一项
  \item 第二项
  \begin{itemize}
    \item 嵌套项
  \end{itemize}
\end{itemize}

% 有序列表
\begin{enumerate}
  \item 第一步
  \item 第二步
\end{enumerate}

% 描述列表
\begin{description}
  \item[关键词] 解释说明
  \item[LaTeX] 一个排版系统
\end{description}
```

---

## 5. 表格

```latex
\begin{table}[htbp]
  \centering
  \caption{表格标题}
  \label{tab:example}
  \begin{tabular}{|l|c|r|}      % l=左对齐 c=居中 r=右对齐
    \hline
    姓名 & 年龄 & 成绩 \\        % & 分列，\\ 换行
    \hline
    张三 & 20   & 95   \\
    李四 & 21   & 88   \\
    \hline
  \end{tabular}
\end{table}

% 列格式修饰
% l c r         —— 基本对齐
% |             —— 竖线
% p{3cm}        —— 固定宽度列，自动换行
% @{自定义}      —— 自定义列间距
```

**三线表（学术论文常用）：**

```latex
\usepackage{booktabs}  % 需要加载此宏包

\begin{tabular}{lcc}
  \toprule
  方法 & 准确率 & F1分数 \\
  \midrule
  Baseline & 85.2 & 83.1 \\
  Our Method & \textbf{92.5} & \textbf{91.3} \\
  \bottomrule
\end{tabular}
```

---

## 6. 插入图片

```latex
\usepackage{graphicx}  % 前置声明

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{图片路径.png}
  \caption{图片标题}
  \label{fig:example}
\end{figure}

% width 选项：
% width=0.5\textwidth  —— 文本宽度的 50%
% width=5cm            —— 固定宽度
% height=3cm           —— 固定高度
% scale=0.5            —— 缩放 50%
```

---

## 7. 交叉引用与超链接

```latex
% 标签与引用
\label{sec:intro}              % 定义标签
见第 \ref{sec:intro} 节        % 引用编号
详见公式 \eqref{eq1}           % 引用公式（带括号）
如图 \ref{fig:example}         % 引用图片
如表 \ref{tab:example}         % 引用表格
第 \pageref{sec:intro} 页       % 引用页码

% 超链接
\href{https://example.com}{链接文字}  % 外部链接
\url{https://example.com}              % 显示 URL
```

---

## 8. 脚注与注释

```latex
这是一个带有脚注的句子\footnote{脚注内容在这里。}

% 注释
% 这是单行注释

\iffalse
这是被注释掉的
多行内容
\fi
```

---

## 9. 参考文献（BibTeX）

```latex
% 在文档末尾
\bibliographystyle{plain}       % 引用样式：plain / ieeetr / acm / apalike
\bibliography{references}       % 对应 references.bib 文件

% 引用方式
\cite{key}             % [1] 或 (Author, Year)
\cite{key1, key2}      % 多篇引用
```

**references.bib 格式：**

```bibtex
@article{key,
  author  = {张三 and 李四},
  title   = {论文标题},
  journal = {期刊名},
  year    = {2024},
  volume  = {10},
  pages   = {1--15},
}

@book{key2,
  author    = {Author Name},
  title     = {Book Title},
  publisher = {Publisher},
  year      = {2023},
}

@inproceedings{key3,
  author    = {Author},
  title     = {Paper Title},
  booktitle = {Conference Name},
  year      = {2024},
}
```

---

## 10. 特殊字符转义

```latex
\#    \$    \%    \&    \{    \}
\textbackslash{}     % 反斜杠
\~{}                 % 波浪号
\^{}                 % 尖号
```

---

## 11. 空白与间距

```latex
% 换行
\\          % 强制换行
\\[10pt]    % 换行 + 额外间距

% 空格
\quad       % 一个字符宽度的空格
\qquad      % 两个字符宽度
\,          % 小空格
\;          % 中等空格
\!          % 负空格（缩进）

% 段落
\par        % 新段落（等价于空行）
\newpage    % 强制分页
\clearpage  % 清除浮动体后分页

% 缩进
\noindent   % 取消首行缩进
\indent     % 强制缩进
\setlength{\parindent}{2em}  % 设置缩进量
```

---

## 12. 颜色

```latex
\usepackage{xcolor}

\textcolor{red}{红色文字}
\textcolor{blue}{蓝色文字}
\textcolor{RGB}{255, 128, 0}{自定义颜色}
\colorbox{yellow}{黄色背景}
\fcolorbox{red}{yellow}{带边框色块}
```

---

## 13. 代码高亮

```latex
\usepackage{listings}

\begin{lstlisting}[language=Python, caption=示例代码]
def hello():
    print("Hello, LaTeX!")
\end{lstlisting}

% 行内代码
\verb|print("hello")|
\lstinline|code here|
```

---

## 14. 常见环境速查

| 环境 | 用途 |
|------|------|
| `equation` | 带编号公式 |
| `align` | 多行对齐公式 |
| `gather` | 多行居中公式 |
| `cases` | 分段函数 |
| `itemize` | 无序列表 |
| `enumerate` | 有序列表 |
| `tabular` | 表格 |
| `figure` | 图片浮动体 |
| `table` | 表格浮动体 |
| `thebibliography` | 参考文献（手动） |
| `abstract` | 摘要 |
| `verbatim` | 原样输出（保留空格） |
| `center` | 居中 |
| `flushleft` | 左对齐 |
| `flushright` | 右对齐 |

---

## 15. 浮动体位置控制 `[htbp]`

- `h` — here（当前位置）
- `t` — top（页顶）
- `b` — bottom（页底）
- `p` — page（单独一页）

> 常用组合：`[htbp]` 让 LaTeX 自动选择最佳位置。加 `!` 如 `[!htb]` 表示更强制。

---

## 16. 实用技巧

```latex
% 1. 引用文字
``引用文字''         % 正确：两个 ` 和两个 '
`单引号文字'         % 单引号

% 2. 破折号
-                      % 连字符（word-break）
--                     % 短破折号（en-dash，如 pp.1--10）
---                    % 长破折号（em-dash）

% 3. 省略号
\ldots                 % 正确的省略号（不要用三个点 ...）

% 4. 生成 Lorem Ipsum
\usepackage{lipsum}
\lipsum[1-3]           % 生成1到3段

% 5. 占位图
\usepackage{graphicx}
\usepackage[demo]{graphicx}  % 生成黑色占位块

% 6. 避免孤行寡行
\widowpenalty=10000     % 防止孤行
\clubpenalty=10000      % 防止寡行
```
