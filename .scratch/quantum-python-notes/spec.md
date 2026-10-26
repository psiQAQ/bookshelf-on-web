# 量子化学 Python 原创中文学习笔记

## 目标与范围

以 Qiming Sun 的 *Python for Quantum Chemistry: A Full Stack Programming Guide*（Elsevier，2025）为学习参考，覆盖正式目录的 16 章主题。产物为独立组织的中文学习笔记，不是译本、逐段改写或原书替代品。每章必须包含实质讲解、学习目标、适用的原创示例或练习及来源指引。

使用 `books/quantum-python-notes/` 作为笔记目录。共享配置、来源索引、覆盖表和集成由主 Agent 维护；`openai-codex/gpt-6.1-sol` 负责章节写作，独立 reviewer 另行审查。写作按 1–4、5–7、8–11、12–16 四组串行交接，避免同一工作区并发写入。

## 内容与发布边界

- 不复制原始 PDF、既有中文前言、原图、原书代码或长篇引文到站点；不执行提取出的代码。
- 原创示例采用独立的问题、数据和代码组织；完整示例在无凭据的隔离环境验证，页面只静态展示。
- 来源页码区分 PDF 物理页序与印刷页码；公式不能仅依据文本提取认定正确，须对照 PDF 视觉检查或另有可靠验证。
- 未获批准：仅加入 `catalog/preview.yaml`，`rights.public: false`，`review.status` 不得为 `approved`。不得公开推送笔记、合并 main 或部署。
- 用户验收对象包括本地预览、覆盖表、独立审阅及测试报告。批准须对应版本；实质修改后重新确认。
- 最终需真实 Quarto 渲染、链接/资源检查、390/768/1440 px 浏览器验证、科学与代码核验；发布前未解决 P0/P1 为零。

## 已确认的资料限制

2026-10-27，用户在“源资料缺项”问答中选择继续按已核实的 16 章制作笔记，并披露缺失的缩略语表、索引和章间页。不补造这些缺页。此选择不是公开发布许可。

基线与来源证据见 `docs/reviews/quantum-python-source-baseline.md`；章节映射见 `docs/reviews/quantum-python-coverage.md`。
