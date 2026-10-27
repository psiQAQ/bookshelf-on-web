## Review

No issues found.

### Correct

- **静态配置与固定 CSS**：`D:/workspace/bookshelf-on-web/scripts/publishing.py:90-99` 仅生成固定样式，显示公式采用限宽和横向滚动；`D:/workspace/bookshelf-on-web/scripts/publishing.py:216-218` 仍要求源配置严格等于安全配置，没有放开任意 `include-in-header` 或执行选项。三本书的实际 `_quarto.yml` 均已全文读取，样式一致。
- **原创示例验证边界**：`D:/workspace/bookshelf-on-web/scripts/verify_notes.py:23,54-60` 固定读取本书章节的普通 `python` 围栏，不读取原书代码。`D:/workspace/bookshelf-on-web/scripts/verify_notes.py:67-79` 使用临时目录、环境白名单和独立解释器进程；文件开头明确说明防护**不是敌对代码的 OS 沙箱**。验证脚本没有接入 Quarto 构建自动执行。
- **预览与发布隔离**：`D:/workspace/bookshelf-on-web/catalog/preview.yaml:6-7` 仅登记本地预览；`D:/workspace/bookshelf-on-web/catalog/books.yaml:2` 仍为空。`D:/workspace/bookshelf-on-web/scripts/build.py:76-84` 区分 `.preview` 与 `dist`，发布模式采用严格门禁。本书保持 `draft`、`public: false` 和待审核来源映射，没有伪造批准。
- **fixture 独立性**：`D:/workspace/bookshelf-on-web/tests/test_publishing.py:24-36` 在临时目录重建仅含两本样书的预览注册和空发布注册，不再依赖真实预览新增了哪些书。
- **浏览器核验没有虚报通过**：`D:/workspace/bookshelf-on-web/scripts/verify_notes_browser.py:36-66` 检查三个尺寸的页面状态、页面宽度与数学渲染；`D:/workspace/bookshelf-on-web/scripts/verify_notes_browser.py:67-112` 实际操作搜索、主题、复制及前后章导航，要求 51 条页面记录、3 条交互记录且无已记录请求失败或页面异常才通过。

### 前次 P2 修复核对

- **空闲费用双计**：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd:25` 已明确排除另列空闲时段。原反例现在得到计算费 `4` 加空闲费 `0.8`，合计 `4.8`，不再重复计算。
- **末次确认丢失**：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd:127-133` 已增加结果核对分支；`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd:166-172` 补充 `max_attempts=1`、提交后丢失确认的回归断言，检查结果 `26.0`、恢复状态及仅一次提交/计算；第185行说明远端无法核实时应保留未知状态。

### Fixed

无；本次严格只读，未修改文件。

### 证据与限制

已全文读取任务指定的全部文件，包括未跟踪文件；另读构建实现、两本样书配置及已有示例、浏览器报告。没有重审另外15章正文，没有执行测试、代码、构建或浏览器。

读取时，`D:/workspace/bookshelf-on-web/reports/notes-browser.json:2` 为 **`ok: false`**。报告含51条页面记录和三个尺寸的交互记录，但 `D:/workspace/bookshelf-on-web/reports/notes-browser.json:1453-1477` 记录了6次外部字体请求 `net::ERR_ABORTED`。因此只能确认脚本如实报告失败，**不能宣称浏览器总验收通过**。

已有示例报告记录通过，但本次没有重新执行或独立计算哈希来确认其与当前文件版本完全一致。后续应运行发布测试及两个验证脚本，并重新核对报告。

### Merge verdict

**OK with notes**：集成实现静态复审未发现实际缺陷；浏览器总验收尚未通过。此结论不构成公开发布、合并 main 或部署。