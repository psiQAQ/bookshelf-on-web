# 成品体检卡片（复制到 `.scratch/<slug>/checklist.md`）

一本书一份。每项都要写「依据」：命中的文件:行，或 PDF 页码。没查过的写 **未查**，查不了写 **Not Run**（不要留空）。

书：`books/<slug>/`　　轮次：　　检查人：　　日期：

## 0. 基线

| 项 | 命令 | 结果 |
| --- | --- | --- |
| 全套测试 | `python -m unittest discover -s tests` | |
| 正文审计（严格项） | `python scripts/audit_prose.py --check` | |
| 正文审计（全量） | `python scripts/audit_prose.py --report reports/prose-audit.json` | `prose_in_fence`: |
| 公式源码 | `python scripts/check_math.py --check` | `findings`: |
| 文献版式 | `python scripts/format_references.py --check` | `changed`: |
| 注册表 | `python scripts/validate.py --preview` | |
| 构建 | `python scripts/build.py --preview --quarto .local/tools/bin/quarto.exe` | `delivered`/`file_count`/`size_bytes`: |
| 站点 | `python scripts/check_site.py .preview --preview` | |
| 渲染 | `python scripts/check_math_render.py --root .preview --check` | `display`/`inline`/`errors`/`unprocessed`: |

## 1. 代码块与围栏（[code-fences.md](../references/code-fences.md)）

- [ ] 无「闭围栏紧跟新围栏」的断裂（`test_no_code_fence_split_in_two`）
- [ ] 无「隔空行断开」的断裂（`test_no_code_block_split_by_a_blank_line`）
- [ ] 无「两块之间没有正文」的相邻围栏（`test_no_adjacent_fences_without_prose`，输出块走 `OUTPUT_MARKER`）
- [ ] 无 `text` 围栏（`fence_language:text_unstyled` 为 0）；REPL/输出/目录树用 `default`
- [ ] `default` 里没有可 `ast.parse` 的真实源码（`fence_language:python` 为 0）
- [ ] 围栏外没有整行代码（`code_outside_fence` 为 0）
- [ ] 围栏里的正文/英文句子已还原（`prose_in_fence` 逐条甄别过，新增命中都有结论）
- [ ] 目录树人工核对过层级与末支连接符（无自动断言）
- [ ] 构建产物里代码都是 `sourceCode … code-with-copy`，无裸 `<pre class="text">`

## 2. 公式（[formulas.md](../references/formulas.md)）

- [ ] `$$` 块与 `eq-` 锚点数量与本项目基线一致，且锚点集合迁移前后相等（`len(ids) == len(set(ids))`）
- [ ] 无 `\eqno`；编号是块末独立一行 `\qquad (n.m)`
- [ ] `check_math.py --check` findings=0（白名单 / 环境配对 / 控制字符 / 游离转义）
- [ ] `formula_remnant` 为 0（无压平副本、无 `⎟⎟` 括号残渣、无孤立算符）
- [ ] 行内公式没有压平上下标（`x_{i+1}` 没写成 `xi +1`）；撇号用 `x^{\prime}`
- [ ] `check_math_render.py --check` errors=0、unprocessed=0（**不能只数 display**）
- [ ] 「公式图」里没有实际是正文/标题/代码的项（逐张看过原页）
- [ ] 多行公式的矩阵行数、`\iddots`/`\vdots` 方向逐式对过页

## 3. 正文结构（[prose-structure.md](../references/prose-structure.md)）

- [ ] 无空项目符号、无悬空 `-`、引导语后都有内容
- [ ] 断句（停在「为」「包括」等）逐处补全，主谓完整
- [ ] 图表数量与名目：图 __ / 表 __（与 `tests/test_quantum_notes.py` 基线一致）
- [ ] 每张图有图注与锚点；资产引用集合 == `metadata.yaml` 声明集合
- [ ] 表格 PNG 后没有重复的文本层残片；表格前句子首词完整
- [ ] `english_residue` 为 0（会话外的英文残留都补译或确认合法）
- [ ] 引用编号（式、图、表、章节）都指向存在的目标

## 4. 文献、链接、排版、发布（[references-links-typography.md](../references/references-links-typography.md)）

- [ ] `format_references.py --check` 干净且二次运行是不动点；条数与编号逐章对过原书
- [ ] `::: {.ref-list}` 围栏闭合，每条一段；悬挂缩进 `padding-left` + 负 `text-indent` 成对
- [ ] `bare_urls` = 0；`broken_links` = 0（主机/路径/锚点续写都查过）
- [ ] 重要外链 curl 过（状态码与锚点真实存在）
- [ ] AutoCorrect 用 `--type markdown` 跑过，复查归零；未采纳的候选有记录
- [ ] `validate.py` 0 error；目录名 == id == slug；`_quarto.yml` == `book_config(metadata)`
- [ ] 宽屏与 390px 各看过一眼（文献换行、代码横向滚动、无横向溢出）

## 结论

- 本轮修了什么（分类 → 提交哈希）：
- 明确不修的（原因 + 已写进 `docs/VERIFICATION.md` 的哪一节）：
- 未查 / Not Run 的项：
- 是否需要用户批准发布：
