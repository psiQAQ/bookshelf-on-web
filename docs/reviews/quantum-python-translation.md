# 量子化学 Python 直译：复核记录

- 书目 id：`quantum-python-notes`
- 原书：*Python for Quantum Chemistry: A Full Stack Programming Guide*，Qiming Sun，Elsevier 2025
- 来源 PDF SHA-256：`c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`（717 页）
- 译本形态：Quarto 书籍，`index.qmd` 加 17 个章节文件

## 方法

1. 文本用 pypdf 提取（PyMuPDF 的文本层会把 3013 个字形替换为 U+00AD，pypdf 干净）。
2. 版面几何用 PyMuPDF 读取：`CropBox` 与 `MediaBox` 的偏移在裁剪前换算，图、表、公式按版面坐标裁剪后栅格化（图 220 DPI，公式 300 DPI），不使用 OCR。
3. 代码缩进由等宽字体的 x 坐标反推（正文左边距按页奇偶分别为 119.8 / 83.8，步长 4.475pt）。
4. 逐段直译由 `gpt-6.1-terra`（thinking=low）完成，润色由 `gemini-3.8-flash-low` 在不比对原文的前提下完成，只改措辞。
5. 参考文献按原书英文条目照录，不译；图注、表注单独翻译。

## 覆盖核对

页数取「源转写片段里出现的 PDF 页标记数」，其余列为源转写与中文片段逐项计数（`.local/verify_coverage.py`，报告 `.local/quantum-source/translation-coverage.json`）。17 章的页面覆盖与全部计数两侧相等，无缺页、无漏项。

| 章 | PDF 页数 | 公式图 | 参考文献 | 插图 | 表格 | 代码行 |
| --- | --- | --- | --- | --- | --- | --- |
| 前言 | 7/7 | 0 | 7 | 0 | 0 | 0 |
| Python 编程环境 | 54/54 | 1 | 46 | 10 | 0 | 537 |
| 数据处理 | 61/61 | 8 | 22 | 1 | 1 | 898 |
| 可视化 | 25/25 | 2 | 19 | 9 | 0 | 334 |
| 科学计算工具 | 27/27 | 8 | 12 | 3 | 3 | 171 |
| 元编程与非数值计算 | 22/22 | 3 | 8 | 1 | 0 | 248 |
| 输入与输出 | 28/28 | 0 | 26 | 1 | 1 | 346 |
| 使用云计算 | 39/39 | 0 | 28 | 11 | 0 | 581 |
| 外部语言接口 | 40/40 | 0 | 23 | 1 | 0 | 675 |
| 程序性能优化 | 90/90 | 10 | 42 | 8 | 6 | 1125 |
| 并行计算 | 54/54 | 1 | 16 | 5 | 1 | 766 |
| GPU 编程 | 26/26 | 0 | 33 | 1 | 1 | 307 |
| 积分计算 | 82/82 | 62 | 15 | 4 | 3 | 1686 |
| 平均场方法 | 53/53 | 42 | 22 | 1 | 1 | 850 |
| 后 Hartree-Fock 方法 I：完全组态相互作用 | 28/28 | 27 | 5 | 3 | 0 | 392 |
| 后 Hartree-Fock 方法 II：耦合簇 | 33/33 | 29 | 7 | 0 | 0 | 611 |
| 分子性质 | 38/38 | 35 | 18 | 0 | 1 | 557 |
| **合计** | **707** | **228** | **349** | **59** | **18** | **10084** |

## 润色核对

润色前后对比用 `.local/check_qmd.py`：代码块内容、图片列表、标题数、图注数必须完全一致，段落数差 ≤2，汉字数比例须落在 0.85–1.20。任何一章不通过就回滚到润色前副本并重试。

| 章 | 结构校验 |
| --- | --- |
| 00-preface.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/00-preface.qmd`） |
| 01-environment.qmd | **未润色**：源文件 97 KB，agy 两次输出都改变了段落结构，按规则回退到润色前版本；直译原文保留 |
| 02-data.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/02-data.qmd`） |
| 03-visualization.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/03-visualization.qmd`） |
| 04-scientific-tools.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/04-scientific-tools.qmd`） |
| 05-metaprogramming.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/05-metaprogramming.qmd`） |
| 06-io.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/06-io.qmd`） |
| 07-cloud.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/07-cloud.qmd`） |
| 08-ffi.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/08-ffi.qmd`） |
| 09-performance.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/09-performance.qmd`） |
| 10-parallel.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/10-parallel.qmd`） |
| 11-gpu.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/11-gpu.qmd`） |
| 12-integrals.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/12-integrals.qmd`） |
| 13-mean-field.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/13-mean-field.qmd`） |
| 14-fci.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/14-fci.qmd`） |
| 15-coupled-cluster.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/15-coupled-cluster.qmd`） |
| 16-properties.qmd | 已润色并逐项通过结构校验（对照 `.local/quantum-source/pre-polish/chapters/16-properties.qmd`） |

润色只把译文交给 `gemini-3.8-flash-low`，不提供英文原文，因此不对照原文改词；可自动核对的不变量全部用脚本守住：代码块内容与图片列表必须逐项相同（`.local/check_qmd.py`），公式图 / 参考文献 / 插图 / 表格 / 代码行数必须与源转写相等（`.local/verify_coverage.py`，见上表）。数字与编号未做机器比对，属人工抽查范围。

## 已知限制

- 公式以原版面图片呈现，不参与网页换色与字号缩放；行内公式的行高由图片宽度控制。
- PDF 文本层里的数学残片（上下标散开）不再单独输出，避免出现乱码，其内容由同位置的公式图片承载。
- 代码块内的弯引号折回 ASCII 引号，其余字符逐字节保持原样；PDF 断词残留（如 `Elec- tronic`）不作修正。
- 机器直译加机器润色，未做人工通读校对。

## 批准

- 批准人：psiQAQ (repository owner, decision recorded in the translation revision request)
- 批准时间：2026-10-27T08:27:15Z
- 依据：该决定在直译任务的修订请求（`.scratch/quantum-python-notes/revision-request.md`）中以「公开 Pages，我自负风险」记录，用户同时确认未获得 Elsevier 授权，并接受版权与下架处理方式（`index.qmd` 的「版权」一节）。
- 发布范围：GitHub Pages 静态站点，仅个人学习阅读，不做商业发行与宣传。
