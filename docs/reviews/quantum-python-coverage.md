# 量子化学 Python 直译：页级覆盖表

- 书目 id：`quantum-python-notes`
- 源 PDF：`books/Python for Quantum Chemistry A Full Stack Programming Guide/raw/Python for Quantum Chemistry A Full Stack Programming Guide (Qiming Sun).pdf`
- 源 PDF SHA-256：`c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`
- 物理页总数：717（PDF 1.7，MediaBox 684×810，CropBox 72/72/612/738）
- 机器可读记录：`books/quantum-python-notes/provenance.json`（每块的 `pdf_pages` 与本表一致），计数校验报告 `.local/quantum-source/translation-coverage.json`

本表是整书直译任务的覆盖记录，取代此前「原创学习笔记」版本的覆盖表。旧表描述的 16 章自写笔记形态已作废，相应内容已被同一路径上的译本文件替换。

## 717 页的分配

| PDF 物理页 | 内容 | 处理方式 |
| --- | --- | --- |
| 1 | 书名页（仅标题、作者、出版社） | 不进入译本正文；书目信息记入 `metadata.yaml` 的 `source.work` |
| 2–8 | 前言（Preface） | 译为 `chapters/00-preface.qmd`，7 页 |
| 9–17 | 目录（Contents） | 不译。目录是导航结构，译本由 `_quarto.yml` 的章节表与站点侧栏重建同等导航；逐条重译目录会与章节标题重复 |
| 18–717 | 第 1–16 章正文（含各章参考文献） | 译为 `chapters/01-environment.qmd` … `chapters/16-properties.qmd`，共 707 页 |

707 + 7（前言）+ 10（书名页与目录）= 717，无其他未归属页，无跳页。

## 逐章页印记与资产计数

页数取「源转写中出现的逐页标记数」，资产与代码行取源转写与中文片段两侧逐项计数（`.local/verify_coverage.py`）；两侧相等才记入本表。

| 章 | qmd | PDF 物理页 | 页数 | 公式图 | 插图 | 表格 | 参考文献 | 代码行 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 前言 | `chapters/00-preface.qmd` | 2–8 | 7 | 0 | 0 | 0 | 7 | 0 |
| 1 Python 编程环境 | `chapters/01-environment.qmd` | 18–71 | 54 | 1 | 10 | 0 | 46 | 537 |
| 2 数据处理 | `chapters/02-data.qmd` | 72–132 | 61 | 8 | 1 | 1 | 22 | 898 |
| 3 可视化 | `chapters/03-visualization.qmd` | 133–157 | 25 | 2 | 9 | 0 | 19 | 334 |
| 4 科学计算工具 | `chapters/04-scientific-tools.qmd` | 158–184 | 27 | 8 | 3 | 3 | 12 | 171 |
| 5 元编程与非数值计算 | `chapters/05-metaprogramming.qmd` | 185–206 | 22 | 3 | 1 | 0 | 8 | 248 |
| 6 输入与输出 | `chapters/06-io.qmd` | 207–234 | 28 | 0 | 1 | 1 | 26 | 346 |
| 7 使用云计算 | `chapters/07-cloud.qmd` | 235–273 | 39 | 0 | 11 | 0 | 28 | 581 |
| 8 外部语言接口 | `chapters/08-ffi.qmd` | 274–313 | 40 | 0 | 1 | 0 | 23 | 675 |
| 9 程序性能优化 | `chapters/09-performance.qmd` | 314–403 | 90 | 10 | 8 | 6 | 42 | 1125 |
| 10 并行计算 | `chapters/10-parallel.qmd` | 404–457 | 54 | 1 | 5 | 1 | 16 | 766 |
| 11 GPU 编程 | `chapters/11-gpu.qmd` | 458–483 | 26 | 0 | 1 | 1 | 33 | 307 |
| 12 积分计算 | `chapters/12-integrals.qmd` | 484–565 | 82 | 62 | 4 | 3 | 15 | 1686 |
| 13 平均场方法 | `chapters/13-mean-field.qmd` | 566–618 | 53 | 42 | 1 | 1 | 22 | 850 |
| 14 后 Hartree-Fock 方法 I：完全组态相互作用 | `chapters/14-fci.qmd` | 619–646 | 28 | 27 | 3 | 0 | 5 | 392 |
| 15 后 Hartree-Fock 方法 II：耦合簇 | `chapters/15-coupled-cluster.qmd` | 647–679 | 33 | 29 | 0 | 0 | 7 | 611 |
| 16 分子性质 | `chapters/16-properties.qmd` | 680–717 | 38 | 35 | 0 | 1 | 18 | 557 |
| **合计** | 17 个章节文件 | 2–717 | **707** | **228** | **59** | **18** | **349** | **10084** |

## 图片、表格与公式的落地方式

- 插图：59 张，PyMuPDF 按版面矩形裁剪、220 DPI 栅格化为 `assets/figures/fig-<章>-<号>.png`，不使用 OCR；清单与逐张抽查见 `docs/reviews/quantum-python-figures.md`。
- 表格：18 张，按横线簇定位裁剪、200 DPI 为 `assets/tables/table-<章>-<号>.png`；表注由 pypdf 从版面文本重新拼合后单独翻译。
- 公式：228 张，300 DPI 为 `assets/math/eq-<章>-<号>.png`。PDF 文本层的公式已被拆散成字形残片（全 1,486,750 字符中 3,013 个 U+00AD 顶替真实字母），无法可靠还原为 LaTeX，因此按版面裁剪成图；页面上可点击放大。每张公式图都带 `#eq-<章>-<号>` 锚点，文本层仍能读出的 59 个编号另以 `**公式 (12.1)(12.2)**` 形式写成可检索、可引用的文字。
- 参考文献：349 条，英文原文照录、不译。文本层首次抽取时每条开头的作者缩写或机构名首词被丢进相邻行、部分词被排版拉成单字母（如 `w h a t`），页眉残渣也混进条目尾部；现已改为从原始页面文本重新解析每条条目（恢复 `E.R. Davidson`、`Python Software Foundation`、`NVIDIA Corporation` 之类开头，合并被拆散的单字母，按词表判定修复断词并保留 `coupled-cluster` 一类真连字符，剥离页眉），`segments/` 与 `zh/` 两侧逐条一致，17 章解析条目数与转录条目数全部相等。
- 代码：10,084 行，按转写照录。文本层会把字符间空隙抽成多余空格（`np.einsum( 'z ,gz ->g' )`），
  故另跑 `.local/code_respace.py`：对等宽字体按「0.6 em/字符」的真实字宽重建每行，用相邻 chunks 的
  实际间隙决定空格数（避免列号推演的累计误差），据此修掉了标识符被拆开、`1e -9`、双空格、
  `docker -compose` 一类错误；仍有约 20 行残留可疑间距，如实记为已知限制，不宣称与印刷版逐字节相同。

## 逐段完整性复核

- 前言「致谢」5 段（PDF p7）：原书把这段正文排成小字号，转写时与版权行、页眉碎屑同属一类标记；第一版按规则把这些标记整段清空，导致该节只剩标题。现已从原页文本取回 5 段原文并译入 `chapters/00-preface.qmd`。
- 各章「小结」：正文齐全。第 6 章的小结曾因该段重译时标签错位（标题被译成正文，后续两个标题被并成 `## 总结参考文献`）而缺失，已重译该段，并给装配程序加了「独立小节标题不合并」守卫，17 章统一称「小结」。

## 已知的不完整之处

- 行内公式（如 `E_coul` 的上下标）在文本层中已是扁平字符串，译为中文后保持同样的扁平形式（`Ecoul、Ex 和 Exc`），未重建上下标；这是文本层限制，不是省略——对应符号在 PDF 中不构成独立的可裁剪元素。
- 公式编号在 PDF 里与公式一起栅格化；本项目从文本层还原了 59 个编号（228 张图的 26%），其余编号只在图内可读、无法文字检索。所有公式图仍有锚点，可链接到具体一张图。
