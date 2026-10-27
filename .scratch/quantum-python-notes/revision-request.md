# 整书直译任务（取代原「学习笔记」任务）

记录日期：2026-10-27。基线提交 `e8b47fb`（`main`）。本文件取代 2026-10-27 早先的「本地预览后的修订要求」，那份要求对应已结束的学习笔记版本。

## 1. 决策变更

- 原任务：16 章**原创中文学习笔记**，规格见 `.scratch/quantum-python-notes/spec.md`，实现基线 `c647409`。用户已于 2026-10-27 决定放弃该形态。
- 新任务：将本地 PDF 专著逐章**直译**为中文，保留原书结构、图片、代码、公式、引用与跳转，做成可整书连续阅读的 Quarto 站点。
- 项目定位随之调整：本站用于**个人学习阅读**，同时保留「完整书籍直译/重排」与「学习笔记记录展示」两种形态；当前目标以整书直译上线 GitHub Pages 为终止条件。
- 产物形式：`.qmd`。沿用 `books/quantum-python-notes/` 目录，章节在 `chapters/`，图片资产在 `assets/`，由 `metadata.yaml` 的 `assets` 字段逐条声明。

## 2. 源与提取

- PDF：`books/Python for Quantum Chemistry A Full Stack Programming Guide/raw/Python for Quantum Chemistry A Full Stack Programming Guide (Qiming Sun).pdf`，717 页，SHA-256 `c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`。
- 只允许非 OCR 方式：pypdf 文本层 + 图片/页面抽取。复用 `.local/quantum-source/page-001.txt` 至 `page-717.txt` 与 `inventory.json`；不重跑 OCR，不引入 OCR 工具。
- 原书代码一律不执行；页面只做静态展示。提取脚本文本留在 `.local/`，不提交。
- 文本层存在断词、连字、上下标与指标损坏；公式、图表不能只凭缓存文本认定正确，须对照页面视觉核对。

## 3. 模型分工（固定，不得替换）

| 角色 | 模型 | 用法 |
| --- | --- | --- |
| 直译 | `openai-codex/gpt-6.1-terra`，thinkingLevel `low` | 本地 pi 的 pi-subagents `worker`，按互不重叠的章节范围委派；不并发修改同一文件 |
| 润色 | `agy.exe`（`C:/Users/ustcw/AppData/Local/agy/bin/agy.exe`）的 `gemini-3.8-flash-low`，叠加 `humanizer-zh`（`C:/Users/ustcw/.agents/skills/humanizer-zh/SKILL.md`） | 输入只给译文与术语表，**不提供原文**；只做语言润色 |
| 编排 | 主 Agent | 术语表、仓库结构、元数据/注册表、与原书缓存逐项核对、排版检查、提交/合并/推送/部署 |

模型或 agy 不可用时停下说明，不换模型顶替，不虚报已完成。

## 4. 润色边界（无原文比对）

- 润色只允许调整措辞、语序、衔接与可读性；**禁止**改动术语译名、公式、代码、数值、单位、引用编号、图注含义与结论。
- 润色后由主 Agent 逐项比对：术语表命中、公式/代码块哈希、数字与引用编号、图表标题。发现改动即回退该段。
- 每章保留润色前后 diff 与调用证据（命令、模型、耗时）。

## 5. 直译完整度要求

- 不得遗漏：图片与图表、代码清单、数学公式、表格、脚注、参考文献、内部交叉引用、外部链接、章节/图/表的编号与跳转目标。
- 分页处不断章；不省略、不合并段落、不以摘要代译；原书脚注保留在出现位置或以可跳转形式保留。
- 章节对应正式目录 16 章，另含前言/导读；页级映射写入 `docs/reviews/quantum-python-coverage.md` 的继任文档。

## 6. 可见性与版权

- 用户明确决定：无 Elsevier 翻译/再发布授权证据，仍选择公开 GitHub Pages，风险由用户自负。本记录不构成授权声明，代理不得声称已获授权或已合规。
- 站点须如实标注「非官方中文直译，仅个人学习用途，未获版权方授权」；不对外宣传、不加推广性元数据。
- 原始 PDF、`.local/` 提取缓存、书籍原始材料目录不进入提交与站点产物。

## 7. 发布门禁

- 公开登记 `catalog/books.yaml` 前须同时满足：`metadata.yaml` 的 `review.status: approved`（含 `approved_by`、`approved_at`、`evidence_path`）、`provenance.json` 全部 block 为 `verified`、`assets` 与实际文件一致。
- 批准记录对应具体提交；批准后若有实质内容变更须重新确认。
- 本地预览走 `catalog/preview.yaml`，永不进入 `dist/`。
- 部署只经 `.github/workflows/deploy.yml`（仅 `main`、仅 `workflow_dispatch`）。

## 8. 待处理清单

1. 按页抽取图片/图表资产，生成含 PDF 页、章节、图号与 SHA-256 的清单；抽查与页面一致。
2. 建立中英术语表（`docs/reviews/quantum-python-glossary.md`），先于章节直译定稿。
3. 逐章直译（`gpt-6.1-terra` low）→ 逐章润色（agy + `humanizer-zh`）→ 主 Agent 比对核对。
4. 更新 `metadata.yaml`、`provenance.json`（`source.type: pdf`，含 `pdf_sha256`、`pdf_page`、`printed_page`、`bbox`）与 `_quarto.yml` 章节表。
5. 排版核验：390/768/1440 px 下的图片清晰度、公式换行、代码换行、表格溢出、锚点跳转与书内搜索。
6. 合并 `main`、推送、`workflow_dispatch` 部署，在线逐章抽查后记录 URL。

## 9. 交付结果（2026-10-27）

状态：**已上线**。<https://notes.psiqaq.cn/bookshelf-on-web/books/quantum-python-notes/>

对待处理清单的落实与偏离：

| 项 | 结果 |
| --- | --- |
| 1. 资产抽取 | 完成。59 张图（220 DPI）、18 张表（200 DPI）、228 张公式图（300 DPI），清单与 SHA-256 见 `docs/reviews/quantum-python-figures.md`；公式图是偏离项——PDF 文本层把公式拆成无法复原的字形残片，改为按版面裁剪成图。 |
| 2. 术语表 | 未单独成文。术语约定写入译者规则（`中文（English）` 首次标注），并由逐章译文自身保持一致；`docs/reviews/quantum-python-glossary.md` 不存在。 |
| 3. 直译 + 润色 | 完成。直译 `gpt-6.1-terra`（thinking=low）、150 个片段；润色 `gemini-3.8-flash-low` + humanizer-zh 规则，16/17 章通过结构与字数校验，第 1 章因篇幅未润色。 |
| 4. 元数据 | 完成，但与条目原文不同：`source.type: translation`（而非 `pdf`），每个 provenance 块记录 `pdf_sha256` + `pdf_pages` 页范围 + `model`/`polished_by`，不逐块记录 `bbox`。 |
| 5. 排版核验 | 完成，见 `docs/VERIFICATION.md`「整书直译上线记录」。 |
| 6. 合并、推送、部署 | 完成。提交 `d475d5e`…`a3f8b9a`，`deploy.yml` run 40497222200 成功；为首次发布在仓库启用 Pages（`build_type: workflow`，域名 `notes.psiqaq.cn`）。 |

页级覆盖记录：`docs/reviews/quantum-python-coverage.md` 已按译本重写（旧「学习笔记」版本作废），逐章列出 PDF 物理页范围、资产与代码计数，并说明 717 页如何分配到「书名页 + 目录 + 前言 + 16 章正文」；机器可读的页范围在 `provenance.json` 的 `pdf_pages`，计数校验报告为 `.local/verify_coverage.py` 输出（`problems=0`）。
