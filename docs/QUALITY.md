# M0 质量与发布门禁

## 自动检查

- `uv run python scripts/validate.py --strict`：正式注册表、JSON Schema、重复 ID/YAML 键、路径边界、显式输入、配置、来源与发布资格；失败返回 1，默认写 `reports/validation.json`。
- `uv run python scripts/validate.py --preview --report reports/preview-validation.json`：独立预览注册表。内容结构错误仍失败；未批准/无公开权利、未核验来源报告为警告。`--preview` 与 `--strict` 互斥。
- `uv run python scripts/build.py`：内置严格校验，不依赖调用方预先运行 validate。临时渲染后检查再交付，输出 `reports/build.json`。`--preview` 使用隔离目录与 `reports/preview-build.json`。
- `uv run python scripts/check_site.py dist`：默认检查空门户；有书时须逐一传 `--book <id>`。构建内部自动传入所选全部 ID。检查本地 HTML/CSS URL、资源、HTML 锚点、重复内容 ID、登记入口和禁止发布文件。外部 URL、CDN、JS 动态 URL 和浏览器交互不在此检查范围。
- 测试：`uv run python -m unittest discover -s tests -v`。设置 `QUARTO_TEST_EXECUTABLE=quarto` 可启用真实渲染集成测试；未设置则明确跳过。Windows 符号链接权限不足时该项也会跳过。CI 在 Linux 配置执行这两项，但尚未远端运行。

所有 JSON 报告有 `ok` 和 `issues`；issue 字段为 `code`、`path`、`message`、`severity`。构建报告另有 `mode`、`delivered`、`output`、`books`、`quarto_version`，渲染完成后记录 `file_count` 和 `size_bytes`。报告及产物不提交 Git。报告为当前调用的机器判定，不是人工审核证明；失败时旧产物可能仍存在，须核对退出码与 `delivered`。

## 人工决定

P0（授权/泄露/科学含义等严重错误）与 P1（公式、图表、引用、代码或严重布局错误）未解决时阻断正式发布。P2 可记录后继续改进，但不能免除人工审核。

维护者在真实核验后填写 `review.status: approved`、`approved_by`、RFC3339 `approved_at`、`evidence_path: docs/reviews/<record>.md`。审核记录必须存在且非空，记录核验对象、决定和范围；来源块均须 `verified`。另行填写 `rights.public: true`、`license`、`evidence_url: https://...`，证据应覆盖所选 `publication_mode`。不能仅因公开可下载、Agent 原创或 notes 模式就推定公开授权。

机器只能确认结构、门禁及记录存在，不能证明签署者身份、许可真实性或科学内容正确性。不得为通过构建伪造记录。测试所用批准记录只存在于临时夹具中，与仓库两本草稿完全分离。

## 尚需人工/外部验证

- 科学内容、公式含义、来源与真实许可；PDF 全文覆盖和逐页核对属于 M1，不声称已完成。
- 浏览器 390/768/1440 px 布局、公式排版、主题切换、搜索交互、键盘导航与可访问性。
- GitHub runner、分支/部署环境保护及公开 Pages HTTP 地址。当前仅验证本地 HTML 产物与本地 HTTP 入口，不代表上线。
