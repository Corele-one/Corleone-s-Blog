# Git 使用教程

## 一、Git 基本概念

### 1.1 三大区域

Git 的本地仓库由三个核心区域组成，理解它们是掌握 Git 的基础：

![[file-20260802172734672.png]]

| 区域 | 说明 | 对应位置 |
|------|------|----------|
| **工作区 (Working Directory)** | 你直接编辑文件的目录，即项目的文件夹 | 本地文件目录 |
| **暂存区 (Staging Area)** | 准备进行版本保存的文件列表，相当于"待提交清单" | `.git/index` |
| **版本库 / 贮存区 (Repository)** | 已完成版本保存的文件列表，即提交历史 | `.git/objects` |

**简单理解：**

- **工作区** = 你电脑上的文件目录
- **仓库** = 暂存区 + 贮存区（合称 `.git` 目录）



> 工作区的文件（如 `a.txt`、`b.txt`）通过 `git add` 进入暂存区，再通过 `git commit` 进入版本库。

---

### 1.2 文件的六种状态

![[file-20260802174810110.png]]

| 状态 | 含义 | 颜色标识 |
|------|------|----------|
| **已修改 (Modified)** | 文件内容已经被修改 | 黄色 |
| **已删除 (Deleted)** | 文件本身已经被删除 | 红色 |
| **变更 (Renamed/Moved)** | 文件本身没有修改，但改变了存放位置 | 橙色 |
| **未管理 (Untracked)** | 尚未添加到版本管理的文件，比如新添加的文件 | 蓝色 |
| **忽略 (Ignored)** | 不需要添加到版本管理的文件（由 `.gitignore` 指定） | 黑色 |
| **冲突 (Conflict)** | 多个分支修改了同一文件的同一位置，需要手动解决 | 灰色 |

---

## 二、本地仓库搭建与基础操作

### 2.1 初始化仓库

```bash
# 配置用户信息（首次使用 Git 时设置）
git config --global user.name "你的名字"
git config user.name              # 查看用户名
git config --global user.email "xxx@xxx.xxx"
git config user.email             # 查看邮箱

# 在项目目录下初始化 Git 仓库
git init
```

执行 `git init` 后，当前目录下会生成一个 `.git` 隐藏文件夹，这就是 Git 的本地仓库。

---

### 2.2 工作流全景图

![[file-20260802175635601.png]]

上图展示了完整的本地 Git 仓库操作流程：

**从左到右的流向：**

```
本地文件夹 → git init → 本地文件 → git add → 暂存区 → git commit → 版本库
```

**各区域间的命令：**

| 操作 | 命令 | 说明 |
|------|------|------|
| 添加文件到暂存区 | `git add <filename>` | 将指定文件加入暂存区 |
| 添加所有文件 | `git add *` 或 `git add .` | 将所有修改加入暂存区 |
| 提交到版本库 | `git commit -m "xxx"` | 将暂存区内容提交为一个版本 |
| 跳过暂存直接提交 | `git commit -a -m "xxx"` | 已跟踪文件的修改可直接提交 |
| 查看状态 | `git status` | 查看当前各区域文件状态 |
| 查看提交日志 | `git log` | 查看版本提交历史 |
| 查看差异 | `git diff` | 查看工作区与暂存区的差异 |

---

### 2.3 撤销与回退操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 撤销工作区修改 | `git restore <filename>` | 丢弃工作区的修改，恢复到暂存区版本 |
| 从暂存区移除 | `git restore --stage <filename>` | 将文件从暂存区退回到未暂存区 |

---

## 三、版本穿梭（Reset 回退）

### 3.1 选择目标版本

![[file-20260802175601018.png]]

在 GUI 工具（如 SourceTree）中，你可以直观地看到版本时间轴。选中想要回退到的结点，选择 **"将 XXX（分支名）重置到这次提交"**。

### 3.2 三种 Reset 模式

Git 提供三种不同力度的回退方式：

| 模式 | 命令 | 效果 | 适用场景 |
|------|------|------|----------|
| **软合并 (Soft)** | `git reset --soft 版本号` | 保留所有本地改动，仅回退版本库的指针 | 想要重新组织提交 |
| **混合合并 (Mixed)** | `git reset --mix 版本号` | 保持工作副本但重置索引（暂存区清空） | 想要重新选择提交内容（**默认模式**） |
| **强行合并 (Hard)** | `git reset --hard 版本号` | 丢弃所有工作副本改动 | 确定要彻底回退，放弃所有修改 |

```
git reset --soft  版本号   → 版本库回退，暂存区和工作区不变
git reset --mix   版本号   → 版本库和暂存区回退，工作区不变
git reset --hard  版本号   → 三者全部回退（⚠️ 不可恢复！）
```

---

## 四、分支管理

### 4.1 分支的基本概念

分支是 Git 最强大的功能之一。它允许你在不影响主线代码的情况下进行独立开发。

```bash
# 查看所有分支
git branch

# 创建新分支
git branch dev

# 切换分支
git switch dev        # 推荐（新语法）
git checkout dev      # 旧语法

# 创建并切换到新分支
git switch -c dev
git checkout -b dev   # 旧语法

# 删除分支
git branch -d dev     # 删除已合并的分支
git branch -D dev     # 强制删除未合并的分支
```

### 4.2 分支合并 —— 普通合并（Merge）

![[file-20260802175920423.png]]

**Merge（普通合并）** 会创建一个新的 **合并提交 (Merge Commit)**，将两个分支的历史连接在一起。

```bash
# 在 master 分支上合并 dev 分支
git switch master
git merge dev
```

**特点：**
- 保留完整的分支历史
- 会产生一个新的合并提交（图中的节点 10）
- 分支历史呈网状结构

---

### 4.3 分支合并 —— Rebase（变基）

![[file-20260802185635708.png]]

**Rebase（变基）** 会将当前分支的提交"移植"到目标分支的最新位置，使提交历史变成一条直线。

```bash
# 在 dev 分支上执行 rebase
git switch dev
git rebase master
```

**特点：**
- 提交历史呈线性，更加干净整洁
- 不会产生额外的合并提交
- ⚠️ 会改写提交历史，**不要对已推送到远程的公共分支使用 Rebase**

---

### 4.4 分支合并对比

| 特性 | Merge | Rebase |
|------|-------|--------|
| 历史结构 | 保留完整分支历史，呈网状 | 线性历史，更整洁 |
| 额外提交 | 会产生 Merge Commit | 不产生额外提交 |
| 安全性 | 安全，不改写历史 | 会改写提交哈希 |
| 使用场景 | 公共分支合并 | 个人开发分支同步主干 |

---

### 4.5 Cherry-Pick（遴选）

**Cherry-Pick** 允许你从其他分支中**单独挑选**某个特定的提交应用到当前分支。

```bash
# 将 dev 分支上的某次提交应用到 master
git switch master
git cherry-pick <commit-hash>
```

**适用场景：** 只需要某个分支中的某个特定功能修复，而不需要合并整个分支。

---

## 五、冲突处理

### 5.1 什么是冲突？

![[file-20260802195103767.png]]

当多个分支**同时修改了同一个文件的同一个位置**时，Git 无法自动判断应该保留哪个版本，就会产生冲突。

**冲突产生条件：**
1. 从 master 分出 dev 和 dev2 两个分支
2. dev 和 dev2 **同时修改了同一个文件（如 `Fruit.txt`）**
3. 合并时 Git 发现同一位置有不同修改 → **冲突！**

### 5.2 解决冲突的步骤

```bash
# 1. 执行合并，发现冲突
git merge dev

# 2. 查看冲突文件
git status

# 3. 手动编辑冲突文件，解决冲突标记
# 冲突标记格式：
<<<<<<< HEAD
当前分支的内容
=======
要合并分支的内容
>>>>>>> dev

# 4. 删除冲突标记，保留正确内容后保存文件

# 5. 将解决后的文件加入暂存区
git add <冲突文件>

# 6. 提交合并结果
git commit -m "解决冲突: 合并 dev 分支"
```

> ⚠️ 冲突时 **不要直接 `git commit`**，必须先 `git add` 标记冲突已解决。

---

## 六、实战开发流程（Fork + PR 工作流）

以下是一个基于 Fork 的团队协作开发流程，适用于开源项目或团队协作场景：

### 6.1 开启新任务

```bash
# 1. 切回本地 main 分支
git switch main

# 2. 从上游仓库 (upstream) 拉取最新代码并合并
git fetch upstream
git merge --ff-only upstream/main

# 3. 将同步后的 main 推送到你自己的 Fork 仓库 (origin)
git push origin main

# 4. 基于最新的 main 创建并切换到新开发分支
# 命名建议：perf/功能名 或 feat/功能名
git switch -c perf/flash-attn-lut-exp
```

### 6.2 本地开发与提交

```bash
# 1. 查看改动的文件状态
git status

# 2. 暂存改动
git add <修改的目录或文件>

# 3. 提交改动（写清楚做了什么）
git commit -m "perf: optimize flash attention exp lookup via LUT"

# 4. 推送到你的 Fork 仓库
git push -u origin perf/flash-attn-lut-exp
```

### 6.3 提交 Pull Request

1. 打开 GitHub 你的 Fork 仓库页面
2. 点击绿色的 **"Compare & pull request"** 按钮
3. 核对分支方向：
   - **Base repository**: 上游仓库 → **base**: `main`
   - **Head repository**: 你的 Fork → **compare**: `你的开发分支`
4. 填写修改说明，点击 **Create pull request**

### 6.4 多分支切换

```bash
# 保存当前分支的代码
git add .
git commit -m "wip: interim commit"

# 切换到另一个分支
git switch main
git switch -c feat/kv-cache-layout

# 之后切回之前的分支继续开发
git switch perf/flash-attn-lut-exp
```

---

## 七、20 个常用 Git 命令速查

![[file-20260802195103767.png]]

| 序号 | 命令 | 功能 |
|------|------|------|
| 1 | `git init` | 初始化本地仓库 |
| 2 | `git clone <url>` | 克隆远程仓库 |
| 3 | `git config --global user.name "xxx"` | 设置全局用户名 |
| 4 | `git config --global user.email "xxx"` | 设置全局邮箱 |
| 5 | `git add <file>` | 添加文件到暂存区 |
| 6 | `git add .` | 添加所有修改到暂存区 |
| 7 | `git commit -m "msg"` | 提交暂存区内容 |
| 8 | `git status` | 查看工作区状态 |
| 9 | `git log` | 查看提交历史 |
| 10 | `git diff` | 查看文件差异 |
| 11 | `git branch` | 查看/管理分支 |
| 12 | `git switch <branch>` | 切换分支 |
| 13 | `git merge <branch>` | 合并分支 |
| 14 | `git rebase <branch>` | 变基合并 |
| 15 | `git cherry-pick <commit>` | 遴选提交 |
| 16 | `git pull` | 拉取远程更新 |
| 17 | `git push` | 推送本地提交 |
| 18 | `git fetch` | 获取远程分支信息 |
| 19 | `git reset --hard <commit>` | 强制回退到指定版本 |
| 20 | `git restore <file>` | 撤销工作区修改 |

---

## 八、核心避坑口诀

1. **`main` 永远是只读主线** —— 绝不在 `main` 上直接提交代码，它只用来与远程保持同步
2. **一任务一分支** —— 改 A 功能开一个分支，改 B 功能开另一个分支，隔离风险
3. **提交前先检查** —— 提交前务必 `git status`，切勿把 `.so`、build 产物、日志文件推送到远程
4. **Rebase 谨慎用** —— 不要对已推送的公共分支执行 Rebase
5. **冲突别慌张** —— 手动编辑冲突文件 → `git add` → `git commit`，三步搞定
