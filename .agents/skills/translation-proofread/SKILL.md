---
name: translation-proofread
description: 直译本成品体检。当新增书籍/笔记、完成一轮直译或润色准备预览/发布、或读者报告「代码没进代码框 / 公式是图片 / 参考文献挤成一段 / 目录树乱了」这类缺陷时使用；按四类缺陷（代码块与围栏、公式、正文结构、文献与链接）逐项检查并跑本仓库门禁脚本。
---

# 直译本成品体检

本仓库的书是「PDF 非 OCR 提取 → 直译 → 润色」的产物。`books/python-for-quantum-chemistry-a-full-stack-programming-guide/`（17 章）用几十轮修复攒下了一批**可复现的缺陷模式**：提取器把正文判成代码、把代码切碎、把公式裁成图、把参考文献并成一段。这个 skill 是那张缺陷清单，不是这本书的说明书。

检查脚本留在 `scripts/` 与 `tests/`（见「脚本地图」）；**问题分类、判据来源、修复思路、验收口径留在本 skill**。

## 五条铁律

1. **机器检查只找疑点，原页才是依据。** 门禁全绿不等于内容正确：`audit_prose.py --check` 通过 ≠ 所有探测器为 0，`prose_in_fence` 是待甄别清单而不是清零项。
2. **先结构，再分类，最后细节。** 先修「块被切碎 / 代码漏在围栏外 / 正文被吞进围栏」，再修语言标记，最后才是缩进、标识符、目录树层级。
3. **脚本绑定本书。** `scripts/audit_prose.py` 已支持 `--book <路径或 slug>` 可直接扫别的书；但 `tests/test_quantum_notes.py` 的计数基线、`tests/test_chapter_markup.py` 的路径、`scripts/check_math_render.py` 的 `BOOK` 仍写死这本 17 章书。新书要先建自己的基线，**不能把旧书通过当作新书通过**。
4. **修复与发布是两件事。** `AGENTS.md` 的发布门禁是约束，不是授权；公开新版本仍需用户明确批准。
5. **每修一类，就写一节 `docs/VERIFICATION.md`**：现象 / 根因 / 判据 / 修复 / 核验数值 / 已知限制。已知限制必须如实写（见文末），不要谎报清零。

## 体检顺序

| 步 | 查什么 | 详细判据 |
| --- | --- | --- |
| 0 | 先跑一遍门禁拿存量基线（下表），不要边改边猜 | — |
| 1 | 代码块断裂、语言标记、围栏外的整行代码、目录树 | [references/code-fences.md](references/code-fences.md) |
| 2 | 公式：裁错、编号、锚点、文本层残片、行内公式、渲染 | [references/formulas.md](references/formulas.md) |
| 3 | 正文结构：空项目符号、断句、被误裁成图的正文、表格残片、英文残留、图注锚点 | [references/prose-structure.md](references/prose-structure.md) |
| 4 | 参考文献、URL/断链、中英间距、发布契约与站点核验 | [references/references-links-typography.md](references/references-links-typography.md) |

逐项打勾的卡片在 [assets/checklist.md](assets/checklist.md)，新增书籍时复制一份到该书目录旁的 `.scratch/`。

## 门禁命令（仓库根目录，Windows bash 下用 `.venv/Scripts/python.exe`，或 `uv run python`）

```bash
# 结构：代码围栏、正文审计（严格项）
python -m unittest discover -s tests -p "test_chapter_markup.py"
python scripts/audit_prose.py --check          # 严格项有命中退出 1
python scripts/audit_prose.py --book sample-waves   # 换一本书扫（新书用 slug）
python scripts/audit_prose.py --report reports/prose-audit.json   # 看全量（含 prose_in_fence）

# 公式：源码形态 + 浏览器渲染
python scripts/check_math.py --check           # LaTeX 命令白名单 / 环境配对 / 控制字符
python scripts/check_math_render.py --root .preview --check

# 文献与链接
python scripts/format_references.py --check    # 有待改章节退出 1；二次运行应是不动点

# 注册表与站点
python scripts/validate.py --strict            # 正式注册表
python scripts/validate.py --preview           # 本地预览注册表
python scripts/build.py --preview --quarto .local/tools/bin/quarto.exe
python scripts/check_site.py .preview --preview

# 全书测试
python -m unittest discover -s tests
```

**退出码语义别混用**：本仓库的 `--check` 都是「有命中退出 1」。AutoCorrect 的退出码 0 **不代表无建议**（读 JSON 的 `count`/`messages`）；Vale 的 1 在有效诊断时是「检查完成、有错误」，2 才是失败。`check_math_render.py` 缺少构建产物或 Edge 时打印 `Not Run` 并退出 0，**不能记为通过**。

## 脚本地图

| 脚本 / 测试 | 归类 | 作用与要点 |
| --- | --- | --- |
| `scripts/audit_prose.py` | 结构 + 链接 | 8 个探测器：`bare_urls` / `suspect_code` / `english_residue` / `formula_remnant` / `broken_links` / `code_outside_fence` / `fence_language`（以上为 `STRICT_DETECTORS`）+ `prose_in_fence`（仅甄别）。`--check` 只看严格项，`--check-all` 才因 `prose_in_fence` 失败；`--book` 换扫描目标（缺省本书） |
| `tests/test_chapter_markup.py` | 结构 | 空项目符号、悬空 `-`、引导语后必须跟列表/代码/图、代码块被空行或围栏切碎；输出豁免用 `OUTPUT_MARKER` |
| `tests/test_quantum_notes.py` | 结构 + 公式 | 本书硬基线：图 59 / 表 18 / `$$` 块 222 / `eq-` 唯一锚点 223；`STATIC_LANGUAGES` 静态围栏白名单 |
| `scripts/check_math.py` + `scripts/latex_commands.txt` | 公式 | 命令名白名单（84 条）、`\begin`/`\end` 配对、数学区控制字符、正文游离转义 |
| `scripts/check_math_render.py` | 公式 | Edge `--dump-dom` 逐章统计 display/inline、`<mjx-merror`、`data-mjx-error`、`;color:red`、未被处理的 math span |
| `scripts/formula_ocr.py` | 公式 | 把 OCR 结果整理成 `$$` 块提案并列出复核点（`normalise` / `build_proposals`）；只出提案，警告不失败 |
| `scripts/format_references.py` | 文献 | `close_gaps` / `fit_ligatures` / `host_label` / `split_url` / `link_urls`；`--check` 有待改退出 1 |
| `scripts/validate.py` | 契约 | 注册表、资产、来源映射、审批（`review.status: approved` + 三条审批信息 + provenance 全 `verified`） |
| `scripts/build.py` | 契约 | 构建白名单 → 检查 → 交付；报告 `reports/{build,preview-build}.json` 的 `delivered`/`file_count`/`size_bytes` |
| `scripts/check_site.py` | 契约 | 拒绝根相对链接、越界目标、缺失锚点、未登记 slug；输出有 error 退出 1 |
| `scripts/publishing.py` | 契约 | `book_config()`（`_quarto.yml` 唯一来源）、`check_qmd()`（单文件锚点重复）、`explicit_anchors()` |

## 一次完整体检（新书）

1. 复制 [assets/checklist.md](assets/checklist.md) 到 `.scratch/<slug>/checklist.md`，先用 `python scripts/audit_prose.py --book <slug>` 看这本书的存量，再把 `tests/test_quantum_notes.py` 的计数基线等本书常量适配到新书。
2. 按 `code-fences → formulas → prose-structure → references` 顺序读对应 reference，边查边勾卡片。
3. 每类修完立即复跑该类门禁，不要攒到最后。
4. 全部清零后跑完整套门禁 + `build.py --preview` + `check_site.py .preview --preview`，宽屏与 390px 各看一眼渲染。
5. 在 `docs/VERIFICATION.md` 追加一节，附核验数值与已知限制。
6. 发布另行取得用户批准；未获批准只登记 `catalog/preview.yaml`，**不要为过严格门禁伪造审批**。

## 已知限制（截至最后一次修订，务必如实转述）

- 570 个 ```python 围栏里约 242 个仍 `ast.parse` 失败：PDF 文本层丢缩进、标识符内被插空格（`l s u m=l x+l y+l z`、`i nrange`、`a i`）。属提取阶段缺陷，只能人工按页修，**不得声称代码块已全部可执行**。
- `prose_in_fence` 存量 100 条是「待甄别」清单（合法 docstring、错误信息、表格碎片混在一起），测试只约束不增长。
- 目录树没有自动保真校验，只能对照 PDF 的横坐标人工核对。
- 表格仍是 PNG（`assets/tables/`），单元格合并不进 HTML 表格。
- 公式的机器检查只覆盖形态；矩阵行数、`\iddots` 方向、编号对错仍要逐式对页。

## 陷阱速查（详细在各自 reference 的「陷阱与反例」）

- `str.replace(old, new, 1)` 只换第一处，同一行第二处残形会留下（`\inom` → 只修了一半）。
- bash heredoc 传给 Python 的字符串吞反斜杠：`\times` 会变成 TAB，`\binom` 会变形成 `\inom`。写 LaTeX 用 `chr(92)` 拼接或 raw string，写完回读校验控制字符数为 0。
- 不要用裸 `mjx-merror` 正则，会命中 MathJax 注入的 CSS 文本；用 `<mjx-merror[ >]|;color=red` 与 `data-mjx-error`。
- 用正则判「这行是代码」会把正文里的 `open()` 算进去；整行判定必须 `ast.parse`。
- `AC_CODE_PATTERNS` 一类常量是 `(正则, 理由)` 二元组，遍历要解包，否则 `AttributeError: 'tuple' object has no attribute 'search'`。
- 禁止用 `git show HEAD:path > 同名文件` 保存基线：重定向先截断目标，会覆盖工作区改动。
- pandoc 会把连续普通行并成一段（「句子被吃」）；文献、清单、正文段落之间必须留空行。
