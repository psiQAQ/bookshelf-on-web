# M0 验证记录（2026-10-27）

## 环境与真实渲染

Windows + Git Bash；系统 Python 3.13.12，项目通过 uv 0.11.19 使用 Python 3.12.13。Quarto 不在系统 PATH；从 GitHub 官方 v1.10.19 发布下载 Windows ZIP 到忽略目录 `.local/`，解压为 `.local/tools/bin/quarto.exe`。`--version` 输出 `1.10.19`。

ZIP 的 SHA-256 与 GitHub 发布资产 digest 相符：`a9c62e4fef34ea05d4dd9175d905f80f0542414a1ae17a9d45698f6646c01173`。uv 0.11.19 发布 API 可访问，已确认不是照抄原始规划的 uv/Actions 版本。

已执行：

```sh
uv sync --frozen --python 3.12
uv lock --check
QUARTO_TEST_EXECUTABLE="$(pwd)/.local/tools/bin/quarto.exe" uv run python -m unittest discover -s tests -v
uv run python scripts/validate.py --strict
uv run python scripts/validate.py --preview --report reports/preview-validation.json
uv run python scripts/build.py --quarto .local/tools/bin/quarto.exe
uv run python scripts/build.py --preview --quarto .local/tools/bin/quarto.exe
uv run python scripts/check_site.py dist
uv run python scripts/check_site.py .preview --book sample-linear-algebra --book sample-waves --book quantum-python-notes --report reports/preview-links.json
.local/actionlint/actionlint.exe -color=false
```

- 锁定依赖同步与 lock 检查通过。除 PyYAML/jsonschema，明确锁定 RFC3339/URI 格式校验器，避免 JSON Schema 对未安装格式校验器静默跳过；非法日期及 URI 有回归测试。
- 47 项测试：46 通过、1 跳过。真实渲染集成测试已启用并通过，不是仅模拟 renderer；检查空正式门户、两个独立书籍、数学显示标记、公式锚点、语法高亮、主题样式与侧栏。静态代码中加入临时哨兵写文件语句，验证文件未被创建。跳过项是实际符号链接测试：Windows 当前没有创建符号链接权限。Linux PR 工作流配置执行该项，但未实际远端运行。
- 正式严格校验：0 问题；正式空门户构建 `ok: true, delivered: true`，23 文件、1,700,136 字节，书籍列表为空。
- 本地预览：三本书，104 文件、8,211,747 字节；6 条预期警告（每本书均缺人工批准、来源待核验）。没有为消除警告而改动审核状态。
- 正式与预览站点检查均为 0 问题。临时构建目录均在交付后清除。失败处理测试证明渲染/断链/禁止文件会阻断交付，保留旧成功产物且不残留新半成品。
- 用 Python `ThreadingHTTPServer` 仅绑定 127.0.0.1、根目录 `.preview/`、随机端口验证 `/`、两个 `/books/<id>/` 及两个章节 HTML，共 5 个请求均 HTTP 200；验证后关闭服务。
- 真实渲染揭示 Quarto 1.10.19 浅深主题重复两个 stylesheet `<link>` ID。仅对此模板行为作窄豁免；正文重复 ID 仍失败，且有回归测试。
- `readme.md`/`readme_zh.md` 大小写文件名、开头互链、文档链接及两版命令一致性有自动测试。站点配置和首页名称均测试为 `bookshelf-on-web`，展示标题为 Bookshelf On Web。

以上体积是本次工具版本的输出快照，不是稳定哈希或容量阈值。

## 工作流版本核验

对下列 GitHub tag ref 解析为提交 SHA，并确认相应 SHA 下的 `action.yml` 可获取（Quarto 为 `setup/action.yml`）。本地 actionlint **1.7.12** 验证两个工作流通过。未触发 GitHub Actions、未访问凭据、未发布 Pages。

| Action | 已核验 tag | 配置中固定 SHA |
| --- | --- | --- |
| actions/checkout | v4 | `11d5960a326750d5838078e36cf38b85af677262` |
| astral-sh/setup-uv | v6 | `d0cc045d04ccac9d8b7881df0226f9e82c39688e` |
| quarto-dev/quarto-actions/setup | v2 | `8a96df13519ee81fd526f2dfca5962811136661b` |
| actions/configure-pages | v5 | `983d7736d9b0ae728b81ab479565c72886d7745b` |
| actions/upload-pages-artifact | v4 | `7b1f4a764d45c48632c6b24a0339c27f5614fb0b` |
| actions/deploy-pages | v4 | `d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e` |

只核验引用存在和本地配置合法性，不声称完成供应链审计或托管 runner 执行。Pages 工作流仅手动触发、限 main，上传 `dist/`，不上传 `.preview/`。维护者仍须配置环境保护及真实发布权限。

## 安全边界与未验证项目

- 两本原创样例保持草稿。没有真实 PDF 导入、OCR、全文覆盖或人工原文核验；不伪造 PDF 哈希/页码。
- 既有 `books/Python for Quantum Chemistry A Full Stack Programming Guide/` 未修改、未登记、未暂存或复制；`skills-lock.json`、`.agents/`、`.local/` 原始规划和既有 Agent 规则保持原样。下载工具仅新增到忽略的 `.local/`。
- 外部 URL、MathJax CDN、主题切换/搜索交互、视觉布局与 390/768/1440 px 响应式行为未作浏览器验证。HTML 已真实渲染不等于浏览器效果已验收。
- GitHub 托管 runner、Pages 环境保护和公开站点 URL 尚未验证；本地 HTTP 200 不等于上线。
- M0 的静态输入限制不是 OS 沙箱或 HTML/JS 净化器，正式审批须审查内容。来源 Schema 仅定义 PDF 数据契约，不代表 M1 实现。
- 当前实现留在 `feat/m0-publishing` 的未提交工作区；未执行暂存、提交、合并、推送或部署。文件系统已用中间文件名完成 `README.md` → `readme.md`；遵守不暂存约束，索引中的初始路径要在将来获准暂存时显式记录大小写更名。

## 整书直译上线记录（2026-10-27）

原「学习笔记」任务被整书直译取代（见 `.scratch/quantum-python-notes/revision-request.md`）。本次交付与验证结果：

- 内容：Qiming Sun《Python for Quantum Chemistry: A Full Stack Programming Guide》全书中译，前言 + 16 章；59 张插图、18 张表格、228 张公式图（按版面裁剪，因 PDF 文本层公式已碎散为字形残片）、349 条参考文献（保留英文原文）、全部代码清单（逐字符照录，仅把排版弯引号折回 ASCII）。
- 来源核验：源 PDF SHA-256 `c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`，717 页；17 章的 PDF 页范围写入 `provenance.json` 并逐章核对覆盖，`eq/ref/fig/tbl/code` 计数与源转录逐章相等（`problems=0`）。
- 质量闸门：`uv run python -m unittest discover -s tests` → 49 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/build.py` → `delivered=true`，`dist/` 20 MB、18 个 HTML 与 305 张 PNG；`scripts/check_site.py dist`（不带 `--book`，自动取注册表）→ 0 问题。
- 浏览器核验：桌面 1440 px 与移动 390 px（390 视口经 iframe 复现，因为 headless Chrome 窗口最小宽度约 480 px）逐页检查；文档级 `scrollWidth` 在 390/768 下分别为 375/753，无横向溢出，代码块在自身容器内滚动。
- 上线：提交 `d475d5e`、`01f08e9`、`f8a1472`、`a3f8b9a`、`cad0ac7`、`09b8061`、`879b477`、`e46d7d0` 推送 `main`；手动触发 `deploy.yml`（首次 run 40497222200，公式锚点与 lightbox 的 run 40521570743，未润色版 run 40533170055，全书润色版 run 40571160852）均成功；`main` 当前提交 `92499ac` 另有一次部署，run 号见仓库 Actions 记录，其 headSha 与该提交一致。为首次发布在仓库上启用 Pages（`build_type: workflow`，自定义域名 `notes.psiqaq.cn`）。实测 `https://notes.psiqaq.cn/bookshelf-on-web/`、`/books/quantum-python-notes/index.html`、`/books/quantum-python-notes/chapters/12-integrals.html`、`/books/quantum-python-notes/assets/math/eq-12-001.png` 均 HTTP 200；`search.json` 返回 138 条索引记录（含「高斯型轨道」「积分计算」等正文词），章页 HTML 带 `rel=prev` / `rel=next` 前后章导航。
- 润色：17 章全部经 `gemini-3.8-flash-low`（`agy`，`--effort low`）叠加 humanizer-zh 规则润色，逐章通过结构闸门（代码块逐字符相同、标题/图片/图注/公式锚点逐条相同、汉字数比例 0.85–1.20、段落数偏差 ≤ `max(3, 1%)`）；逐章数字见 `docs/reviews/quantum-python-polish.md`，调用日志 `.local/logs/polish3-<chapter>.log`。
- 已知限制：公式以图片呈现，不可选中或搜索；正文中少量被排版拆散的符号残片按原样保留，未重新排版；代码提取会把部分代码块内的空格打散（如 `np.einsum( 'z ,gz ->g' )`），与「逐字符照录」的表述有出入，属 PDF 文本层限制；机器润色未做人工通读校对。
- 版权：译本未获 Elsevier 授权，按用户决定「公开 Pages，自负风险」发布，`index.qmd` 的「版权」一节记录了下线承诺。
