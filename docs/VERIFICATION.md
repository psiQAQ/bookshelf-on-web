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
uv run python scripts/check_site.py .preview --preview --report reports/preview-links.json
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

- 内容：Qiming Sun《Python for Quantum Chemistry: A Full Stack Programming Guide》全书中译，前言 + 16 章；59 张插图、18 张表格、228 张公式图（按版面裁剪，因 PDF 文本层公式已碎散为字形残片）、349 条参考文献（保留英文原文，逐条从页面文本重建）、全部代码清单（逐字符照录，仅把排版弯引号折回 ASCII）。
- 来源核验：源 PDF SHA-256 `c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`，717 页；17 章的 PDF 页范围写入 `provenance.json` 并逐章核对覆盖，`eq/ref/fig/tbl/code` 计数与源转录逐章相等（`problems=0`）。
- 质量闸门：`uv run python -m unittest discover -s tests` → 49 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/build.py` → `delivered=true`，`dist/` 20 MB、18 个 HTML 与 305 张 PNG；`scripts/check_site.py dist`（不带 `--book`，自动取注册表）→ 0 问题。
- 浏览器核验：桌面 1440 px 与移动 390 px（390 视口经 iframe 复现，因为 headless Chrome 窗口最小宽度约 480 px）逐页检查；文档级 `scrollWidth` 在 390/768 下分别为 375/753，无横向溢出，代码块在自身容器内滚动。
- 上线：提交 `d475d5e`、`01f08e9`、`f8a1472`、`a3f8b9a`、`cad0ac7`、`09b8061`、`879b477`、`e46d7d0` 推送 `main`；手动触发 `deploy.yml`（首次 run 40497222200，公式锚点与 lightbox 的 run 40521570743，未润色版 run 40533170055，全书润色版 run 40571160852）均成功；`main` 的最新提交同样会各触发一次部署，run 号见仓库 Actions 记录，其 headSha 与该提交一致。为首次发布在仓库上启用 Pages（`build_type: workflow`，自定义域名 `notes.psiqaq.cn`）。实测 `https://notes.psiqaq.cn/bookshelf-on-web/`、`/books/quantum-python-notes/index.html`、`/books/quantum-python-notes/chapters/12-integrals.html`、`/books/quantum-python-notes/assets/math/eq-12-001.png` 均 HTTP 200；`search.json` 返回 138 条索引记录（含「高斯型轨道」「积分计算」等正文词），章页 HTML 带 `rel=prev` / `rel=next` 前后章导航。
- 润色：17 章全部经 `gemini-3.8-flash-low`（`agy`，`--effort low`）叠加 humanizer-zh 规则润色，逐章通过结构闸门（代码块逐字符相同、参考文献逐条相同、标题/图片/图注/公式锚点逐条相同、汉字数比例 0.85–1.20、段落数偏差 ≤ `max(3, 1%)`）；润色前修订 `fe35636`、润色后修订见 `docs/reviews/quantum-python-polish.md`，逐章耗时、行级增删与 before/after 计数见该文件与 `docs/reviews/quantum-python-polish-evidence.json`，diff 可用 `git diff fe35636..<润色提交> -- books/quantum-python-notes/chapters/` 复核；调用日志 `.local/logs/polish3-<chapter>.log`。
- 第三次复核修正（2026-10-27，据独立审计意见）：参考文献 349 条从原始页面文本逐条重建（恢复被文本层拆散的首个缩写或机构名首词、合并单字母拆字、修断词、剥离页眉残渣）；前言「致谢」5 段从 p7 小字号正文取回并译入；第 6 章「小结」重译并修正标签错位，装配程序的标题合并增加「独立小节标题不合并」守卫。
- 已知限制：公式以图片呈现，不可选中或搜索；正文中少量被排版拆散的符号残片按原样保留，未重新排版；代码提取会把部分代码块内的空格打散（如 `np.einsum( 'z ,gz ->g' )`）；已用 `.local/code_respace.py` 按等宽字体的真实字宽重写全部代码行，修掉标识符被空格拆开、科学计数被拆成 `1e -9`、双空格与 `docker -compose` 一类错误，仍有约 20 行残留可疑间距，如实记为已知限制；机器润色未做人工通读校对。
- 版权：译本未获 Elsevier 授权，按用户决定「公开 Pages，自负风险」发布，`index.qmd` 的「版权」一节记录了下线承诺。

## 书目改名与书库导航修订（2026-10-28）

- 改名：书目 id 与目录由 `books/quantum-python-notes/` 改为 `books/python-for-quantum-chemistry-a-full-stack-programming-guide/`（`git mv`），原书缓存 `raw/`（PDF 与源转录，仍被 `.gitignore` 的 `**/raw/**` 排除）从带空格的来源目录迁入同一目录，空目录删除。id 必须是 slug、注册表路径必须是 `books/<id>/metadata.yaml`，因此目录名不能照抄原书标题的空格与大小写。
- 联动更新：`catalog/books.yaml`、`books/<id>/metadata.yaml`、`books/<id>/provenance.json` 的 `book_id`、`_quarto.yml`（由 `book_config()` 重新生成）、`readme.md` / `readme_zh.md`、`scripts/verify_notes.py`、`scripts/verify_notes_browser.py`、`tests/test_quantum_notes.py`。`docs/reviews/` 下的日期化证据与 `.scratch/` 规格按当时状态保留旧路径，其中引用的 git diff 命令只对当时提交有效。
- 线上地址：新地址为 `https://notes.psiqaq.cn/bookshelf-on-web/books/python-for-quantum-chemistry-a-full-stack-programming-guide/`；旧地址 `/books/quantum-python-notes/` 未做重定向，按用户决定直接失效（本地 `.preview` 实测 404）。
- 本地预览注册表：`catalog/preview.yaml` 移除两本未审批样例，本地预览与 Pages 都只显示这一本书；样例文件仍留在 `books/` 但不再登记。
- 阅读器模式：移除 `book.reader-mode`。Quarto 1.10.19 的 `quartoToggleReader()` 只给按钮加 `.reader` 高亮、写 `localStorage` 的 `quarto-reader-mode`，再跑一次侧栏遮挡检测；`bootstrap-*.min.css` 里也只有按钮自身的配色规则，没有任何隐藏侧栏或加宽正文的样式，因此该按钮点击后无可见变化。实测渲染产物中 `quarto-reader-toggle` 计数由 2 降为 0。
- 返回书库：`book_config()` 在 `book.sidebar.header` 与 `book.page-footer` 各写入一个 `a.qs-home-link`，并由 `HOME_LINK_SCRIPT` 在 `DOMContentLoaded` 时按 `location.pathname` 反推站内根（`books/<id>/` 之前的全部路径），从而同时适配本地的 `/` 与 Pages 的 `/bookshelf-on-web/` 前缀，且书首页与 `chapters/` 两种深度通用。静态 HTML 里的 `href` 为空串，避免 `check_site.py` 判定根相对链接不安全或相对路径越界。
- 本次核验：`uv run python -m unittest discover -s tests` → 49 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=369`、`size_bytes=19864313`；`scripts/build.py --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=369`、`size_bytes=19864047`；`scripts/check_site.py .preview --preview` → 0 问题（新增 `--preview` 开关，直接读 `catalog/preview.yaml` 的 slug，避免 CI 硬编码书名）；`scripts/check_site.py dist` → 0 问题。本地服务 `python -m http.server 8000 --bind 127.0.0.1 --directory .preview` 下 `/`、书首页、`chapters/12-integrals.html` 均 HTTP 200。
- 未验证：改名后的 Pages 部署（需手动触发 `deploy.yml` 并推送）；禁用脚本时「返回书库」会退化为空 `href`（点击后仍停留原页）的降级路径未做浏览器实测。

## 参考文献换行与超链接修订（2026-10-28）

- 问题一（换行）：17 章的 `## 参考文献` 每条 `[n] …` 各占一行但行间没有空行，pandoc 把整个小节并成一个大段落，渲染后 349 条挤在一起。问题二（链接）：链接以裸 `https://…` 文本出现，被 `#quarto-document-content p { overflow-wrap: anywhere; }` 在任意字符处折断，既难读也无法点击。
- 工具：新增 `scripts/format_references.py`（`--check` 只报告、`--chapters` 限定章节、`--report reports/references.json` 落盘计数）。它把每个参考文献小节改写成 `::: {.ref-list}` 围栏 div，每条单独成段（段间空行），并把每个 URL 就地替换成 `[标签](URL)`；`--check` 模式下计数为 0 表示已格式化（幂等）。
- URL 修复：`close_gaps()` 把排版在 URL 内插进去的空格粘回（`https://docs. python.org/` → `https://docs.python.org/`，本次 93 处；`.` 后要求下一 token 首字符为小写或数字，避免把 `References`、`Jul.` 误粘）；`fit_ligatures()` 折叠 PDF 连字字形（`conﬁguration`、`ﬂake8`、`epﬂ.ch`，U+FB00–U+FB06，共 23 处）；`HEADER_RESIDUE_RE` 剥离页眉残渣（`References 55`、`References xxi`，共 7 处，其中 1 处是第 9 章第 23 条的 `on inlining:w,` 排版残字，改成 `on inlining,`）。
- 链接标签：`host_label()` 让链接触点显示站点名而不是 URL —— `doi.org`/`dx.doi.org` 显示 `DOI`，其余取末两段标签（`docs.python.org` → `python.org`，`www.brendangregg.com` → `brendangregg.com`），末段是国家二级域（`uk`/`in`/`cn`/`jp` 等）时取三段（`books.google.co.in` → `google.co.in`）。句末标点经 `split_url()` 留在链接外，右括号不剥离（`/wiki/JIT_(computing)` 保持完整）。17 章共 349 条、389 个链接。
- 顺带修复内容缺陷：第 9 章（09-performance）、12 章（12-integrals）、13 章（13-mean-field）、16 章（16-properties）的参考文献条数正确但内容错位 —— 第 9 章是 `[1]–[20]` 整段重复两遍再 `[21][22]`，源书实为 1–42，即 20 条丢失、20 条重复。根因在 `.local/rebuild_refs.py` 的 `rewrite(seg, entries)`：它给每个 segment 都从索引 0 开始写，第二个参考文献段的编号因此重新从 0 计，章末条目从未落进译文。本次用同脚本的 `chapter_pages()` + `entries_of()`（从 `.local/quantum-source/page-*.txt` 解析，含首字母缩写、断词、连字符修复）重建这 4 章的完整条目（页范围 09 = 402–403 共 42 条、12 = 564–565 共 15 条、13 = 617–618 共 22 条、16 = 716–717 共 18 条），重建前副本留在 `.local/refs-before-repair/`。先验证重建路径可靠：其余 13 章（含 08 章的 `08-foreign-language.md` 转录）的 `entries_of()` 输出与已提交条目逐条完全相同。修完后 17 章全部编号连续、无重复、合计 349 条。
- 样式：`book_header_style()` 增加 `.ref-list p { margin: 0 0 0.65rem; padding-left: 2.2em; text-indent: -2.2em; }`（悬挂缩进，第二行起与条目文字对齐）、`.ref-list a { text-decoration: none; border-bottom: 1px dotted; }` 与 `:hover` 下划线，提示「这是链接」而不喧宾夺主。
- 新增测试：`tests/test_references.py` 覆盖 `split_url`、`close_gaps`、`host_label`、`fit_ligatures`、`format_section` 的单元行为，并对已提交的 17 章做语料级断言（每个小节是 `.ref-list` 围栏、每条独占一段、编号从 1 连续且无重复、链接外不再出现裸 `https://`）。`tests/test_quantum_notes.py` 补断言 `_quarto.yml` 与 `book_config()` 一致时包含 `.ref-list` 规则。
- 本次核验：`uv run python -m unittest discover -s tests` → 64 项通过（2 跳过）；`scripts/validate.py --preview` 与 `--strict` → 0 问题；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=369`、`size_bytes=19861715`；`scripts/check_site.py .preview --preview` → 0 问题；`scripts/format_references.py --check` → 幂等（`joined_spaces=0`、`ligatures=0`、`header_residue=0`）。渲染产物实测：17 章 `div.ref-list` 内共 349 个 `<p>`、389 个 `<a>`，锚外无裸 URL。
- 浏览器核验：headless Edge 经 `.local/probe-refs-wide.html`（1280 px）与 `.local/probe-refs-narrow.html`（390 px）iframe 加载 `chapters/09-performance.html#参考文献`（hash 直开时截图早于锚点滚动，故用 iframe），两档均见逐条换行、悬挂缩进与站点名链接，390 px 无横向溢出。
- 过程中发现并修掉的工具缺陷：首版 `link_urls()` 用 `URL_RE.sub()` 直接匹配裸 URL，第二次运行会把 `[scipy.org](https://…)` 里的 URL 再包一层，产出 `[scipy.org]([scipy.org](https://…))`，`--check` 因此对 17 章全部报差异。改为 `URL_OR_LINK_RE`（已有 markdown 链接优先匹配，命中即原样返回）后成为不动点，并把 `--check` 的退出码定为「有待改章节即 1」，`tests/test_references.py` 增加 `test_existing_links_are_not_relinked` 断言二次格式化无变化。
- 未验证与取舍：链接未做死链检测、无 DOI 规范化、无 Web Archive 回退；链接标签是站点名而非文献标题，读者无法从标签预判目标；参考文献仍保留英文原文，仅中文语言环境下的排版参数（悬挂缩进、字号）随站点主题走。

## 空列表与断句残缺修复（2026-10-28）

- 问题：读者发现 `chapters/02-data.qmd` 的 §2.1.1「NumPy 基础」在「…列出每个类别中最常用的一些函数：」之后是一长串空项目符号。全库扫描（`^\s*[-*+]\s*$`）共 68 处空项目符号，分布于 `02-data.qmd`（45）、`05-metaprogramming.qmd`（19）、`11-gpu.qmd`（4）。
- 根因：`.local/build_source.py` 的文本提取以 `chunks_of()` 取每块的 y 坐标（`y = e * cb + f * cd + cf`），`build_lines()` 用 `abs(dy) <= 2.6` 归并为一行，`classify()` 再以「等宽字体字符数超过半数」（`CODE_FONTS = ("LetterGothic", "Courier")`）判为代码。原书排版把清单里的函数名整体排成等宽字体，页面上的整块清单因此被并成**一条** line record、判为 `CODE`、输出成一条超长 `[CODE]` 行；原本承载这些名字的项目符号行随之只剩 `-`。转录中 `chapters/02-data.md:83`（508 字符）、`chapters/05-metaprogramming.md:281`（138 字符）、`chapters/03-visualization.md:40`（170 字符）即为该事故的物证。同型事故还有另一种表现：小字号加粗的引导短语被抽成独立的 `[SMALL]` 行，原位置留下半个句子（如「…而不是使用标准名称的」「…根据目标的」）。
- 修复方式：以 PDF 文本层（`.local/quantum-source/page-*.txt`）为准逐处回填，不重译、不改术语。函数名写成两级列表（父项以「：」收尾，子项 2 空格缩进并用反引号包裹），与第 3 章已恢复的清单风格一致。恢复内容：§2.1.1 六组函数清单（创建数组 10、重组数组 15、访问元素 3、索引 10、逐元素算术 5、线性代数 5）与 6 个子模块（`linalg`/`polynomial`/`random`/`ma`/`ctypeslib`/`fft`）；5.2 节 SymPy 综述（化简展开、`sympy.integrals` 变换与逆变换、特殊函数与多项式、物理子模块、Clebsch-Gordan 与 Wigner 系数、二阶量子化、四元数）与 5.3 节四种自动微分术语；11 章 4 个 `cupyx.*_pinned` API；另有 02 章类型映射标签、`02-data.qmd` §2.3.5 三条、`03-visualization.qmd`「文本和注释」、`04-scientific-tools.qmd`「DIA（对角线）」与 `scipy.linalg` 两条清单项、`07-cloud.qmd` 六条 AWS 术语的引用号 `[5]`–`[10]`、`09-performance.qmd` 延迟/吞吐量/递推三项、`10-parallel.qmd`「协程和异步模块」。
- 断句回填（9 处）：`01-environment.qmd` 两处（`KohnShamDFT` 类、`DFTOptimizationMixin` 类）、`06-io.qmd` 的 gRPC 客户端段落、`08-ffi.qmd` 的 `libblas.so` 标准名、`12-integrals.qmd` 图 12.3 图注（「取决于目标坐标」）、`09-performance.qmd`「m 个电子」、`14-fci.qmd`「14792 × 2450/4 ≈ 900 万」（对照 870 万次缺页）、`15-coupled-cluster.qmd` 简并度 `C(n, k)·C(m, k)·k!`。源句在 `page-060/063/230/300/389/639.txt` 与 `chapters/12-integrals.md`、`chapters/15-coupled-cluster.md` 中逐条核对。
- 新增测试：`tests/test_chapter_markup.py` 对全部章节做三项回归断言——无空项目符号、无「例如/包括/如下/分别/由 … -」的悬空项目符号、以「例如：/包括：/如下：」收尾的列表项后面必须跟列表项或代码块/图/表（避免再次出现「引导语后只剩空壳」）。`02-data.qmd:951`「- 与 nan 的比较…」与 `08-ffi.qmd:552`「- 与原生 Python/C API 相比…」是合法句式，扫描时按误报处理。
- 本次核验：`uv run python -m unittest discover -s tests` → 68 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/format_references.py --check` → `ligatures=0`、`header_residue=0`；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=369`、`size_bytes=19863445`。渲染产物实测：17 章无空 `<li>`，`02-data.html` 的 §2.1.1 区间有 14 个嵌套 `<ul>`，`np.zeros`/`np.unique`/`ctypeslib` 均已出现；`05`、`09`、`11`、`12`、`14`、`15` 章的关键字符串在 HTML 中全部命中。截图 `.local/shot-list-wide.png`（1440×2460，经 `.local/probe-list-wide.html` iframe 定位到 §2.1.1）确认两级列表与缩进正常。
- 已知限制：仍按「机器提取 + 人工按页回填」修复，未重跑整书提取；同类事故若发生在只有单个短词被等宽化的位置，不会留下空项目符号，扫描规则（空项、悬空 `-`、行尾「由/包括/例如」）可能漏检，只能靠通读发现；`14-fci.qmd` 与 `15-coupled-cluster.qmd` 的公式在原书中以图片形式给出，本次按纯文本写入算式，未生成对应公式图。

## 公式图、括号残渣与被切碎的代码块（2026-10-28）

- 问题（读者报告）：`chapters/02-data.qmd` §2.1.7.1「用于灵活数组结构的 strides 属性」里，Hankel 矩阵被拆成两张图片，两张图之间和 `def hankel_matrix(a):` 与函数体之间还各多出一行只有 `|` 的分隔；`assets/math/eq-01-001.png` 整张图的内容只是 `2. Directories in PYTHONPATH;` 一行正文。
- 根因一（括号残渣）：原书用大号扩展括号字形（U+239B–U+23A6，如 `⎟⎟`、`⎜⎜`、`⎛`）画矩阵括号，这些字形在 PDF 里是独立的文本行。`.local/build_source.py` 的 `is_math_line()` 只把「无 ≥4 字母小写词且 ≤6 个 token」的行判为公式行，括号行长度只有 1–3 个字符、词数 ≤6，本应命中，但它们与代码行/正文行交错时被 `build_lines()` 归并进相邻块，最终以 `[P]` 行的身份落进转录，再被逐句直译成了段落里孤立的一行 `⎟`。pandoc 把它当普通段落渲染，视觉上就是一条像 `|` 的细线。全库扫描（整行只由 U+239B–U+23AD 组成）共 9 行：`02-data.qmd` 5 行、`13-mean-field.qmd` 4 行。
- 根因二（图片吞正文）：同一个 `is_math_line()` 的兜底规则 `return len(text.split()) <= 6` 会把「没有 ≥4 字母小写词」的短正文行判成公式行。`2. Directories in PYTHONPATH;`（`in` 只有 2 个字母）、`For the code implementation … can be refined to`、代码行 `sol += v * x` 都因此被 `emit_equation()` 连同页面上相邻的行一起裁成 300 dpi 的 PNG，原位置只剩一个图片引用；转录里对应的条目数也随之丢失。
- 修复一（括号与代码）：删掉 9 行括号残渣；把它切断的代码块合回一个 ```` ```python ```` 块。`02-data.qmd` 的两个 `hankel_matrix` 实现、`13-mean-field.qmd` 的 `extrapolate` 函数原本各被切成 2–3 段（`13-mean-field` 的 `extrapolate` 被切成 8 段，语言标记在 `python`/`text` 之间来回跳）。代码以 `page-592.txt` 的文本层为准逐字复原，未改写变量名、空格习惯或注释。
- 修复二（Hankel 矩阵改真矩阵）：删除 `eq-02-003.png`、`eq-02-004.png`，改为一段显示公式 `$$\begin{pmatrix} … \end{pmatrix} \qquad (2.3)$$`，保留 `[]{#eq-02-003}` 锚点便于引用；矩阵元素取自 PDF 第 87 页文本层（4 行 5 列，含 `\cdots`、`\ddots` 填充）。`H_{i,j} = a_{i+j}` 同时从裸文本改为行内公式。
- 修复三（纯文字图）：`eq-01-001.png` 换回正文，并补回被吞掉的第 2、3 条 —— 原文 4 条搜索顺序现在是「1. 输入脚本所在的目录；2. PYTHONPATH 中列出的目录；3. site-packages 目录；4. .pth 文件中列出的目录。」（源 `page-023.txt`；此前第 3 条整条缺失）。`eq-12-039.png`（内容是 `For the code implementation … can be refined to`）换回「…TRR 张量的迭代范围可以优化为：」，并删掉紧邻的一行裸公式残渣 `ix + iy + iz + kx + ky + kz ≤ li j + lk l. (12.59)`；`eq-13-036.png`（内容是代码 `sol += v * x` / `return sol`）与 `eq-13-037.png`（内容只是 `or err` 的页边碎片）直接删除，对应内容留在代码块里。
- 数学渲染：`book_config()` 保持 `html-math-method: mathjax`，构建产物引用 `https://cdn.jsdelivr.net/npm/mathjax@4/tex-chtml.js`。选它是因为改动最小、Pages 表现与既有一致；代价是**完全离线**打开本地预览时，本次新增的公式会显示为原始 LaTeX 源码（`\begin{pmatrix}…`）。仓库内没有自托管 MathJax/KaTeX，如需离线渲染要另行把 KaTeX 引入仓库（js + css + woff2 字体，约 1 MB）并同步改 `book_config()` 与全部 `books/*/_quarto.yml`。
- 图片计数从 228 降到 222（删除 6 张：`eq-01-001`、`eq-02-003`、`eq-02-004`、`eq-12-039`、`eq-13-036`、`eq-13-037`），`metadata.yaml` 的 `assets` 同步删掉这 6 行；`tests/test_quantum_notes.py::test_translation_images_and_captions` 的期望值随之更新并注明原因。
- 本次核验：`uv run python -m unittest discover -s tests` → 68 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/check_site.py .preview --preview` → 0 问题；`scripts/format_references.py --check` → `ligatures=0`、`header_residue=0`；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=363`、`size_bytes=19817854`。渲染产物实测：17 章 HTML 中 U+239B–U+23A0 出现 0 次；`02-data.html` 中矩阵以 `<span class="math display">` + `\begin{pmatrix}` 输出并由 MathJax 排版（`.local/shot-matrix.png`，经 `.local/probe-matrix.html` iframe 定位 `#用于灵活数组结构的-strides-属性`）；`13-mean-field.html` 的 `extrapolate` 代码块是单个 `pre`、16 行、含 `sol += v * x` 与 `return sol`；`01-environment.html` 的搜索顺序 4 条齐全。
- 残留清单（未修）：`assets/math/` 仍有 222 张公式图。用 `.local/build_source.py` 的函数重跑一遍并打补丁记录 `get_pixmap(clip=…)` 的裁剪矩形（产物 `.local/eq-inventory-raw.json`、`.local/eq-inventory.json`），可对每张图回读 PDF 文本层内容；但当前代码与生成已提交图片的旧版本不完全一致（新跑 246 张、已提交 222 张，`eq-06-*`、`eq-09-011/012`、`eq-10-002..`、`eq-12-063` 等编号错位），因此不能按文件名一一对齐。合并后的判据是「图片前后相邻转录行」：`[EQ]` 夹在连续编号的列表项之间、或紧邻 `[CODE]` 行时必定是吞了正文/代码，此判据命中 3 张（本次已全部修掉）。剩余 222 张按高度筛出 14 张多行公式/矩阵候选（`eq-13-022` 1300×746、`eq-15-007` 1370×583、`eq-16-011` 1148×559、`eq-12-024` 1428×505、`eq-15-003` 979×426、`eq-12-030` 1336×424、`eq-16-022` 1330×419、`eq-12-026` 1139×394、`eq-12-029` 1316×392、`eq-13-035` 1106×383、`eq-12-034` 1277×356、`eq-13-041` 1060×330、`eq-12-027` 1339×316、`eq-16-001` 1085×304），它们大多是矩阵或多行方程组，转 LaTeX 需要数学 OCR 或逐条人工转写。
- 已知限制：公式的上下标在 PDF 文本层里是被压平的（`x_{i+1}` 读出来是 `xi +1`），仅凭文本层无法可靠重建 LaTeX，本次只转换了能逐元素核对的结构化内容（矩阵、正文句子、代码）；本次没有引入数学 OCR，读者当地部署的 OCR 服务接上后可复用上述 inventory 产物批量推进。

## 文件结构图（目录树）修复（2026-10-28）

- 问题（读者报告）：`chapters/01-environment.qmd` §1.1.2.3「命名空间包」的目录树显示错乱，「其他地方只要是文件结构都展示有问题」。
- 根因：原书的三处目录树是用矢量线条加节点名绘制的，方框连接符（`├──`、`│`、`└──`）在 PDF 里不在文本层，提取时只剩节点名；转录阶段这些节点名又被判成普通段落/代码行，逐句直译后落进 ```` ```text ```` 块，缩进也随行内空格被打散（`__init__.py` 前有 40 个空格、`module_a.py` 反而顶格），于是渲染成一个既没有树形也没有层级的列表。第 47/48 页那棵树还被分页切成两个代码块。
- 取证方法：`page.get_text("dict")` 读每行 `bbox[0]`，按 x 缩进还原层级（本书级距约 17.9pt，两棵树分别以 x=83.8 / 119.8 为第 0 层）；再用 `page.get_pixmap(clip=…, dpi=200~260)` 裁小图逐棵人眼核对 `├──`/`└──` 的归属。裁图存于 `.local/tree-p24.png`、`.local/tree-p47.png`、`.local/tree-p48-top.png`、`.local/refs-tree-p26.png`。先试过用 `page.get_drawings()` 扫短线段批量找树，但 586 页全部命中（表格线、下划线混入），不可用，已弃用。
- 修复：三处改为标准树写法（`├──`/`│`/`└──` + 4 空格一级），第 47/48 页的两段合并为一棵。改动都在 `chapters/01-environment.qmd`：§1.1.2.1 的 `mypkg`（3 个文件）、§1.1.2.3 的 `core_repo`/`extensions`（含首尾 `...`）、§1.4 的项目布局（`doc`、`LICENSE.txt`、`README.md`、`package_name/subpackage`、`pyproject.toml`、`requirements.txt`、`setup.py`、`tests` 共 18 行）。
- 顺带修掉的同族缺陷（都是「表格图 + 文本层残片」或「等宽片段被抽走」）：`02-data.qmd` 表 2.1 图后 5 个碎块（`scipy.linalg np.linalg mpmath comments`、`qr_solve`/`cholesky_solve`、`norm norm norm norm.`、`cosm cosm cosine.`、`sinm sinm sine.`）、`09-performance.qmd` 表 9.1 后 3 个碎块与表 9.4 后 1 个碎块（`[compiler]`/`cflags=…`）、`11-gpu.qmd` 表 11.1 后错位缩进的 `kernel_v1`/`kernel_v2`/`kernel_v3` 碎块，共 10 个 ```` ```text ````/```` ```python ```` 块整段删除 —— 这些内容与表格图片重复且顺序错乱。句子层面再补 5 处：`09-performance.qmd`「和 Cython 支持…」→「Numba 和 Cython…」、「和 Numba 都提供…」→「Cython 和 Numba…」、「和 Pythran 对 NumPy…」→「Cython 和 Pythran…」（源 `page-370.txt`）；`11-gpu.qmd`「和 PyCUDA 都在…」→「CuPy 和 PyCUDA 都在…」；`14-fci.qmd`「…可将矩阵 A 形式表示如下 / 和本征向量 x：」→「给定一组基向量 {v0, v1, …, vn−1}，可将矩阵 A 及其本征向量 x 表示如下：」（源 `page-623.txt`）。另有 3 处被空行切断的排版：`00-preface.qmd` 第 14 章那条列表项、`09-performance.qmd` 第 5 条优化实践（「…以供将来参考」+「和可能的回退。」）、`09-performance.qmd` 的 `dot_kj = np.dot(…)` 与 `cs[:,j] -= dot_kj * cs[:,k]` 两个代码块（中间夹一个孤立的「和」）。
- 本次核验：`uv run python -m unittest discover -s tests` → 68 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/check_site.py .preview --preview` → 0 问题；`scripts/format_references.py --check` → `ligatures=0`、`header_residue=0`；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=363`、`size_bytes=19816232`。渲染产物实测：`01-environment.html` 三个 `<pre><code>` 内是完整树形，项目布局那棵 18 行齐全；截图 `.local/shot-tree.png`（1440×1220，经 `.local/probe-tree.html` iframe 定位 `#命名空间包`）确认 `├──`/`│`/`└──` 与节点名逐列对齐、四层缩进正确。
- 全库复查：`grep -n "结构如下\|目录结构\|布局如下"` 只命中 `01-environment.qmd:176/251`（本轮已修）与其他普通句子；扫描「所有非空行都是纯文件名的代码块」也只剩已修的三处，说明书里没有别的目录树。
- 已知限制：树形连接符是人工按裁图与 x 缩进复原的，没有自动化校验（原书用矢量线条，文本层不含该信息）；表格目前仍是图片（`assets/tables/*.png`），本轮只清掉了重复的文本层残片，把表格转成 HTML 表格是另一件事。

## 中英文排版的机械检查与修订（2026-10-28）

- 工具与口径：AutoCorrect 2.16.3（text-prison skill 自带引擎），配置 `C:\Users\ustcw\.agents\skills\text-prison\autocorrect\conservative.yml`，其中只打开 `space-word: 2`，其余规则（`space-punctuation`、`space-bracket`、`space-backticks`、`space-dash`、`space-dollar`、`fullwidth`、`no-space-fullwidth`、`halfwidth-word`、`halfwidth-punctuation`、`spellcheck`）全为 0，`context.codeblock: 0`。因此这一轮只覆盖「中文与拉丁字母/数字之间该不该留空格」，不涉及错别字、术语、繁体与标点重复。Vale 未运行（记 `Not Run`：本次只要求 AutoCorrect）。
- 工具坑（值得记住）：`.qmd` 扩展名不被 AutoCorrect 识别，`autocorrect --lint --format json --config … x.qmd` 会静默返回 `{"count": 0}`，看起来像「零问题」。首轮 17 章全部 0 就是假通过。必须显式加 `--type markdown` 才会真正解析（用探针 `ac-probe.qmd` 验证：无 `--type` 得 0 条，有 `--type` 得 1 条）。另外 AutoCorrect 遵守 `.gitignore`，把探针放在 `.local/` 下同样得 0，容易误判为工具失效。
- 首轮结果（`--type markdown`）：17 章共 262 条建议，全部是「插入空格」，代码围栏内命中 0（`codeblock` 保护生效）。分布：`09-performance.qmd` 74、`12-integrals.qmd` 69、`04-scientific-tools.qmd` 63、`16-properties.qmd` 28、`08-ffi.qmd` 19、`01-environment.qmd` 3、`06-io.qmd` 3、`15-coupled-cluster.qmd` 3，其余 9 章为 0 —— 这四五章是不同批次翻译的，没跟全书「中文与拉丁字母之间留空格」的风格对齐。
- 采纳规则（按用户授权）：只在中日韩字符与 `[A-Za-z0-9]` 的边界插空格；不采纳「在 `.` 开头的标识符前插空格」的候选（`.data`、`.indptr` 前不加空格）；`expm()`、`.to{format}()` 这类代码调用里的半角括号保持原样；代码块、公式、标识符内部、引用编号一律不动。实现方式是取 AutoCorrect 给出的 `new`，再逐字符删掉所有「中日韩字符 ↔ 非字母数字 ASCII（`.`、`(`、`[`、`$`、反引号、`-`）」之间的空格，避免把标点当成词边界。
- 机械修订：262 处行级空格插入，涉及 `09-performance.qmd` 74 行、`12-integrals.qmd` 69 行、`04-scientific-tools.qmd` 63 行、`16-properties.qmd` 28 行、`08-ffi.qmd` 19 行、`01-environment.qmd`/`06-io.qmd`/`15-coupled-cluster.qmd` 各 3 行。上述规则会把 `C/C++`、`C#` 这种以 `+`/`#` 结尾的词判成「非字母数字边界」而跳过，因此另按 `[A-Za-z0-9][+#]+` 分词补了 17 处空格（`08-ffi.qmd` 6 处、`09-performance.qmd` 11 处，如 `C/C++中` → `C/C++ 中`）。
- 复查（一轮修订后一轮复查）：17 章建议数 262 → 0，未再出现新命中；`docs/` 目录级顺带扫描得到的「第1章 → 第 1 章」类建议属于历史评审文档，未处理。
- 本次核验：`uv run python -m unittest discover -s tests` → 68 项通过（2 跳过）；`scripts/validate.py --strict` → 0 问题；`scripts/format_references.py --check` → `ligatures=0`、`header_residue=0`；`scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` → `delivered=true`，`file_count=363`、`size_bytes=19819362`；`scripts/check_site.py .preview --preview` → 0 问题。渲染产物实测：`09-performance.html` 含 `C/C++ 中对应` 与 `Python 和 C/C++ 操作的开销比较`，`04-scientific-tools.html` 含 `CSR 的非零元素`。
- 已知限制：只有 `space-word` 一条规则被启用，所以「中文排版已体检」不成立；`.qmd` 需要 `--type markdown` 这个前提没有写进任何脚本，下次手跑仍会踩坑；全书仍存在大量历史评审文档（`docs/reviews/**`）的中英文间距问题，不在本轮范围。
