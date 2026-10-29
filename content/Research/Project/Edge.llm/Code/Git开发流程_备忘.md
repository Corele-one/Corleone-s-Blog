## 🛠️ Snapdragon-NPU Attention Kernel 开发 SOP

总体流程包含 **3 大阶段**：


```Plaintext
【开启新任务/切分支】 ➔ 【在新分支上编写与提交】 ➔ 【提交 PR 请求合并】
```

---

### 第一阶段：开启新任务 / 新功能开发（同步与建分支）

在开始写任何新功能或做新实验前，先确保你的本地主干与学长原仓库同步，并开启独立分支：


```bash
# 1. 切回本地 main 分支
git switch main

# 2. 从学长原仓库 (upstream) 拉取最新代码并合并到本地 main
git fetch upstream
git merge --ff-only upstream/main

# 3. 将同步后的 main 推送到你自己的 Fork 仓库 (origin)，保持远程 Fork 干净
git push origin main

# 4. 基于最新的 main 创建并切换到你的新开发分支
# 命名建议：perf/功能名 或 feat/功能名
git switch -c perf/flash-attn-lut-exp
```

---

### 第二阶段：在新分支上本地开发与提交

切换到你的新分支（如 `perf/flash-attn-lut-exp`）后，就可以安心开始修改代码了。

主要修改目录：

`projects/flashattention/src/htp-ops-lib-main/src/dsp/ops/flash_attn.c`

代码修改或阶段性测试通过后：


```bash
# 1. 查看改动的文件状态
git status

# 2. 暂存改动（避免误提交生成的 .so 或 log 大文件）
git add projects/flashattention/

# 3. 提交改动（写清楚做了什么）
git commit -m "perf: optimize flash attention exp lookup via LUT"

# 4. 推送到你的 Fork 仓库 (origin)
git push -u origin perf/flash-attn-lut-exp
```

---

### 第三阶段：向学长原仓库提交 Pull Request (PR)

1. 打开 GitHub 你的 Fork 仓库页面：[Corele-one/Snapdragon-NPU](https://github.com/Corele-one/Snapdragon-NPU.git)。

2. 页面上方会弹出绿色的 **"Compare & pull request"** 按钮，点击进入。

3. 仔细核对分支方向：
    - **Base repository**: `zcy-001-001/Snapdragon-NPU` $\rightarrow$ **base**: `main`
    
    - **Head repository**: `Corele-one/Snapdragon-NPU` $\rightarrow$ **compare**: `perf/flash-attn-lut-exp`
4. 填写本次修改的简要说明（做了什么优化、测试结论等），点击 **Create pull request**。


---

### 第四阶段：多个分支/任务之间切换

如果你在开发 `perf/flash-attn-lut-exp` 的途中，想临时切换去处理另一个任务（例如修改 KV Cache 布局）：

```bash
# 1. 保存或提交当前分支的代码
git add .
git commit -m "wip: interim commit for lut exp"

# 2. 切换回 main 分支
git switch main

# 3. 开启另一个新分支
git switch -c feat/kv-cache-layout

# 4. 之后如果想切回之前的分支继续写：
git switch perf/flash-attn-lut-exp
```

---

### 💡 核心避坑口诀

1. **`main` 永远是只读主线**：绝不在 `main` 上直接提交代码，它只用来与 `upstream/main` 保持同步。

2. **一任务一分支**：改 Softmax 算法开一个分支，改内存布局开另一个分支，隔离风险。

3. **提交前先检查**：提交前务必 `git status`，切勿把 `.so` 动态库、build 产生的二进制文件或个人调试日志文件推送到 GitHub。