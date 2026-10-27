# 来源契约（M0，无 PDF 转换实现）

本阶段不安装或调用 OCR、MinerU、Docling、Marker，不导入真实 PDF，不运行提取代码，也不把 PDF 指令作为操作指令。

## 原创内容

书籍元数据 `source: {type: original, description: ...}`，来源映射 `provenance.json` 的每个块也使用 `source.type: original` 和创作说明。不填写 PDF 哈希、页码、bbox 或解析器版本。两本样例仅演示该分支，`review_state: needs_review`。

## PDF 数据约束（为来源记录定义，不实现提取）

`schemas/book.schema.json` 定义 PDF 元数据分支：`source.type: pdf`、小写 64 位十六进制 `sha256` 和 HTTPS 来源 URL；不能与原创字段混用。

`schemas/provenance.schema.json` 顶层为 `book_id`、非空 `blocks`。每块包含唯一 `block_id`、登记章节的 `qmd`、实际存在的显式 `qmd_anchor`、`source`、`review_state`（`needs_review` 或 `verified`）。PDF 来源字段：

- `pdf_sha256`：须与书籍元数据一致，不提供 PDF 下载链接。
- `pdf_page`：从 1 开始的文件页序，不等同于印刷页码。
- `printed_page`：印刷页码字符串或 null，可表示罗马数字等。
- `bbox: [x1,y1,x2,y2]`：每个值在 [0,1]，左上角原点，x 向右、y 向下；要求 x1<x2、y1<y2。

校验会检查映射类型/哈希、重复块或目标、章节白名单、锚点存在以及 bbox 次序；正式发布要求每块 verified。Schema 无法证明逐页覆盖或原文准确性，M0 不提供此类保证。元数据与来源映射不进入发布产物；人工对照证据留在审核记录中。
