# Corleone's Blog

一个 ME（微电子专业）学生在 AI 时代的学习历程：从电路与数字设计，到计算机与 AI，再到论文阅读、代码理解和项目实践。

站点：<https://corele-one.github.io/Corleone-s-Blog/>

## 分享范围

Study 是原始笔记库，本站是它的单向发布副本。目录结构与原库保持一致：

```text
content/
├── index.md                    # 网站首页
├── Blog/                       # 专题文章
├── Lecture/                    # 讲座记录
├── Note/
│   ├── ME/                     # 微电子课程与专业基础
│   └── CS/                     # 计算机、AI 与软件工程
└── Research/
    ├── Research-Insight/       # 科研思考与方法
    └── Project/                # 论文、代码与项目实践
```

只读取 Study 中的 `Blog`、`Lecture`、`Note`、`Research/Research-Insight`、`Research/Project`。其他目录不进入本站。

## 日常同步与发布

需要 Node.js 22+、npm 10.9.2+、Python 3.11+ 和 Git。新电脑先运行 `npm ci` 与 `npm run install-plugins`。

在此仓库中执行：

```bash
npm run sync:preview  # 预览新增、修改和删除，不改 content
npm run sync          # 应用同步，只更新本地副本
npm run preview       # 本地浏览 http://localhost:8080
npm run publish       # 同步 → 构建 → 验证 → 提交笔记 → push → GitHub Pages 自动部署
```

只需更新网站时，一条 `npm run publish` 即可。这个命令会执行提交与推送；单独运行 `npm run sync` 不会发布。原来的 `./publish.sh` 入口也可继续使用，可从任意工作目录调用。

源目录默认是 `~/Documents/Study`；换机器或调整位置时可临时指定：

```bash
STUDY_DIR="/path/to/Study" npm run sync:preview
STUDY_DIR="/path/to/Study" npm run publish
# 或：python3 scripts/sync_study.py --source /path/to/Study --apply
```

## 同步规则

- **只读原库**：复制内容，不向 Study 写入，也不做双向合并。请在 Study 中编辑笔记。
- **保持目录和原文**：保留中文文件名、Markdown、图片、PDF 和支持的媒体资源；扩展名白名单见 `sync.config.json`。
- **跟随移动和删除**：已同步的笔记在 Study 中重命名、移动或删除后，下次同步会更新本站对应副本。
- **保护本地编辑**：用 `.study-sync-manifest.json` 记录已管理文件及 SHA-256。若直接改了副本，同步会停止；先把需要的修改手动移回 Study，或恢复副本后再同步。其他未管理文件不自动删除。
- **缺失保护**：任意一个源目录不存在、为空或只剩不支持的文件时，停止同步，避免未挂载目录造成误删。
- **排除隐藏文件与缓存**：如 `.obsidian`、`.claude`、`.env`、`.DS_Store`、`node_modules`。拒绝符号链接、明显的密钥格式及达到 100 MiB 的文件；这不替代发布前对笔记内容的审阅。
- **先暂存再替换**：复制并校验将变更的内容后再应用，普通写入失败会回滚；同一时间只允许一个应用进程。Git 历史保留已提交的旧版本。

首页与分类说明在 `site/` 中维护，再由同步复制到 `content/`。如需在 Study 中维护同路径的 `index.md`，先调整 `sync.config.json` 的 `sitePages`，避免覆盖冲突。首次从旧分类迁移使用 `python3 scripts/sync_study.py --migrate-legacy` 预览，加 `--apply` 执行；已迁移的 checkout 不需要此参数。

同步不在后台自动发布；运行发布命令前可以先预览。发布脚本只暂存清单管理的笔记及其删除记录和清单自身，已有暂存改动会阻止发布，站点代码及配置改动需单独提交。

## 验证

```bash
npm run test:sync    # 在临时目录测试同步，不触碰原笔记
npm run test:links   # 检查相对链接与同名笔记的构建解析
npm run sync:check   # 检查副本与来源是否一致
npm run build
npm run verify:site  # 验证分类导航、上一篇/下一篇，并报告原笔记中的失效链接
```

GitHub Actions 直接构建仓库中的 `content/`，不连接个人 Study 目录。推送到 `clean-v5` 后自动部署。

## 交流与引用

笔记记录阶段性的理解，欢迎通过 [Discussions](https://github.com/Corele-one/Corleone-s-Blog/discussions) 交流纠错。引用个人笔记请注明来源；引用材料、论文、课件及图片的权利归原作者所有。
