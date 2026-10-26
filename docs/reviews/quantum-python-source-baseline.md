# Python 量子化学笔记：来源与 M0 基线

核对日期：2026-10-27。状态：来源基线已核对；内容尚未完成；未获公开发布批准。

## Git 与基础设施

- 从 `feat/m0-publishing` 的 `3a5ee71` 新建 `feat/quantum-python-notes`。
- 起始未跟踪材料：`books/Python for Quantum Chemistry A Full Stack Programming Guide/`、`skills-lock.json`。保留且不纳入本任务提交。
- `uv run python -m unittest discover -s tests -v`：45 项，成功，2 项跳过。跳过项不计作已执行验证。
- `uv run python scripts/validate.py --strict`：通过；正式注册表无获批书籍。
- `uv run python scripts/build.py --preview --quarto .local/tools/bin/quarto.cmd`：真实 Quarto 1.10.19 渲染通过，原有两本样例输出到 `.preview/`；未批准和来源未审阅警告符合预期。
- 未推送、合并或部署本任务内容。

## 本地资料

资料目录：`books/Python for Quantum Chemistry A Full Stack Programming Guide/`。

| 文件 | 核实结果 |
| --- | --- |
| `Python_for_Quantum_Chemistry.md` | 12,807 bytes；中文前言、范围、章简介、支持信息与致谢，不是全书正文。不能作为已完成笔记或逐章正文来源。 |
| `raw/Python for Quantum Chemistry A Full Stack Programming Guide (Qiming Sun).pdf` | 9,674,294 bytes，717 个 PDF 页面。 |

PDF SHA-256：`c7553b895fc4caf52359df14007190a83bc5b94162dea1d22f4dc41314e383aa`。

主会话使用 `uv run --with pypdf==6.12.0 python .local/extract_quantum_source.py` 读取文本层，无 OCR、无书中代码执行、无源文件上传。临时工具未加入项目依赖。提取缓存位于被忽略的 `.local/quantum-source/`，包括逐页文本与 `inventory.json`，不进入站点或 Git 提交。

717 页均提取到至少 40 个字符。主会话逐章核实开章标题、目录起页与章末页眉，逐页检查各章预期印刷页码是否出现在页首/页尾，700 个正文/参考文献页面均匹配。此检查只证明章内页码序列一致，不证明每个公式、图表和字符正确。

PDF 9–17 为目录；正式目录含三部分、16章，未列附录。各章物理页与印刷页的偏移不同，不能采用统一偏移。

## 资料缺项与用户决定

- 文件止于第16章参考文献的印刷第712页，缺目录所列 Index（713起）。
- 目录所列 List of acronyms（xxiii）未包含在现有文件中。
- 章间/分部页未全部包含：不能推断缺页一定是空白；不补造其内容。
- 现有文件不是完整出版物；但16章内部页码连续，各章均有开头及参考文献末页。准确范围见覆盖表。
- 2026-10-27，用户选择“继续制作 16 章笔记”，同意在来源说明披露这些缺项；公式和图表仍需逐项核验。此决定仅允许继续本地制作，不是公开批准。

## 书目与使用边界

PDF 题名页核实：Qiming Sun，*Python for Quantum Chemistry: A Full Stack Programming Guide*，丛书 *Theoretical and Computational Chemistry*，Volume 23。开章页脚载 Elsevier B.V. 2025 版权声明及 ISSN 1380-7323；各章有独立 DOI。未核实独立版权页、ISBN 或全书 DOI，不从章节 DOI 推断这些字段。

版权声明保留全部权利，未见开放许可。用户批准不等于原书转载许可。最终网页只包括独立中文讲解、自创示例与练习，以及书目/章节来源指引；不转载既有中文前言、原书代码、插图、长引文或 PDF。`source.type: original` 仅说明笔记文本和例子的创作来源，不隐瞒参考书；每章和 provenance 都须记录主题参考。`publication_mode: notes` 不免除内容、来源与权利审查。

## 待完成的科学与内容核验

文本层存在连字、断词和项目符号损坏。上下标、张量指标、图例及跨页代码不能凭提取文本认定无误。后续只核验拟采用的科学关系和自创示例，不重建全书排版；必要时对原 PDF 页面做非 OCR 渲染查看。每章记录来源页、采用的公式、假设和验证方法。无法可靠核实的内容应标记并请求处理，不臆造。

## 调查子代理状态

`openai-codex/gpt-6.1-sol` 的 researcher 运行 `0166843f-8a14-40c8-9b91-0db8a71885e6` 保存了调查报告，但最终因请求不可用的 `web_search, fetch_content, get_search_content, source_check` 工具失败。不能将其视为成功的独立审阅。主会话已检查报告；上述页数、哈希、开章/章末页码、章内序列和基线测试均由主会话实际核实。后续写作与独立审阅使用另行可用的角色；不改全局工具配置、不以别的 CLI 绕过故障。
