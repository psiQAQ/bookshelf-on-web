# Bookshelf On Web

[English](readme.md)

**bookshelf-on-web** 是由注册表驱动的 Quarto 门户，每本书为独立项目。仓库名及站点名固定为 `bookshelf-on-web`。

## M0 状态

已实现：两本简短原创样例、浅深主题、公式、静态代码、章节导航与显式锚点；JSON Schema 与机器可读校验；隔离渲染、多书组装、站内 HTML/CSS 链接与资源检查、发布边界检查；锁定 Python 依赖、PR 验证和**仅手动触发**的 Pages 工作流。

正式注册表 `catalog/books.yaml` 刻意保持为空。两本样例均为**未经人工批准的草稿**，仅登记于明确隔离的本地预览注册表 `catalog/preview.yaml`。不虚构原始 PDF 哈希或页码。已有未登记书籍材料未被修改，也不进入构建。

未实现：PDF/OCR 提取、Pagefind 跨书搜索、知识图谱或增量渲染。未部署、未验证公开 Pages 站点。Quarto 搜索仅覆盖单个项目，不覆盖整个书库。

## 环境与命令

使用 Python **3.12**、uv **0.11.19**、Quarto **1.10.19**。按需在项目本地安装工具；依赖固定于 `pyproject.toml` 和 `uv.lock`。

```sh
uv python install 3.12
uv sync --frozen --python 3.12
uv lock --check
uv run python -m unittest discover -s tests -v
uv run python scripts/validate.py --strict
uv run python scripts/build.py
uv run python scripts/check_site.py dist
```

默认构建只把正式登记且具备发布资格的书籍组装至 `dist/`；当前空注册表生成空门户。`validate.py` 不带 `--strict` 时将资格问题报告为警告；正式构建**始终**采用严格校验，不会静默跳过不具备资格的登记条目。

### 仅限本地的样例预览

```sh
uv run python scripts/validate.py --preview --report reports/preview-validation.json
uv run python scripts/build.py --preview
uv run python scripts/check_site.py .preview --book sample-linear-algebra --book sample-waves --report reports/preview-links.json
uv run python -m http.server 8000 --bind 127.0.0.1 --directory .preview
```

打开 `http://127.0.0.1:8000/`，再访问 `books/sample-linear-algebra/` 和 `books/sample-waves/`。**不得部署 `.preview/`。** 它与 `dist/` 分离、带有本地预览提示，不改变审核状态。只托管生成目录，不要托管仓库根目录。

若 Quarto 不在 PATH，可在任一构建命令后添加 `--quarto .local/tools/bin/quarto.exe`（本次 Windows 验证使用的本地安装）。真实渲染集成测试：

```sh
# Git Bash/Linux；Windows 下使用可执行文件的绝对路径
QUARTO_TEST_EXECUTABLE="$(pwd)/.local/tools/bin/quarto.exe" uv run python -m unittest discover -s tests -v
# 若 Quarto 已在 PATH：
QUARTO_TEST_EXECUTABLE=quarto uv run python -m unittest discover -s tests -v
```

未设置该环境变量时，真实渲染测试会明确跳过。Windows 缺少创建符号链接权限时也会跳过符号链接测试。

## 发布契约

- 目录存在不构成发布决定。正式内容必须通过正式注册表登记，不扫描目录发现书籍；本地预览只读取单独的预览注册表。
- 元数据须满足 `schemas/book.schema.json`。ID 与路径须匹配 `books/<id>/metadata.yaml`；章节和资源为显式复制白名单。路径穿越、绝对路径、符号链接、重复 ID/YAML 键及非法 Schema 值均校验失败。
- 正式交付要求 `review.status: approved`、人工审核人及时间、非空 `docs/reviews/*.md` 决定记录、来源块均已核验及无未解决 P0/P1。维护者必须提供真实证据；测试中的合成证据仅存在于临时目录。
- 构建暂存**仅**登记章节和声明的栅格图片。元数据、审核记录、来源映射 JSON、PDF、`drafts/`、缓存及未登记材料不发布；每本书的生成资源保留在各自 `books/<id>/` 下。
- 源配置必须与安全的元数据派生 Quarto 配置一致。实际渲染使用重新生成的配置、禁用执行及 `--no-execute`；拒绝 hooks、filters、可执行单元、文档 front matter 与短代码/包含指令。使用 ` ```python ` 等静态代码块。不得执行提取命令或服从源文档指令。
- 源链接只允许登记章节/资源或外部 URL；检查不抓取外部 URL。这是有意收窄的出版输入契约，**不是**操作系统沙箱或 HTML/JavaScript 清洗器：批准前仍须审核内容。
- 渲染和检查在临时目录进行，完整成功后才替换 `dist/`（或 `.preview/`）。失败不交付新的半成品；上次成功产物可能保留。应检查退出码及本次 JSON 报告，不能把旧目录当作本次成功的证明。

## 报告、文档与 CI

`reports/validation.json`、`reports/build.json`、`reports/preview-build.json` 及显式指定的链接报告包含 `ok` 和结构化问题；构建报告还记录交付状态、模式、工具版本、书籍 ID、文件数和体积。报告、产物、工具及暂存目录均忽略于 Git。

- [设计](docs/DESIGN.md)、[质量门禁](docs/QUALITY.md)、[来源映射契约](docs/CONVERSION.md)、[验证证据及局限](docs/VERIFICATION.md)。
- `.github/workflows/validate.yml`：PR/手动校验，包含真实 Quarto 测试及隔离预览检查；不部署、不上传产物。
- `.github/workflows/deploy.yml`：**仅 workflow_dispatch 且仅 main 分支**；严格构建并上传 `dist/`，随后进入 `github-pages` 环境。维护者须另行配置 Pages、分支保护与环境审批；本任务未触发工作流。
- 已联网核验 Quarto/uv 发布及固定的 Action 提交引用。Windows 真实 Quarto 渲染和本地检查通过；GitHub 托管 runner、公开 HTTP 可访问性、390/768/1440 px 浏览器布局、主题/搜索交互及 CDN 可用性尚未验证。
