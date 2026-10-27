# bookshelf-on-web：M0 出版平台

入口文档：[English](../readme.md) / [中文](../readme_zh.md)。展示标题为 **Bookshelf On Web**；仓库与站点名称固定为 `bookshelf-on-web`。

## 架构与注册表

一个 Quarto Website 门户，加多个独立 Quarto Book。`catalog/books.yaml` 是唯一**正式**注册表，初始为空；构建不扫描 `books/`。注册条目为 `id` 和 `path: books/<id>/metadata.yaml`，详细元数据定义于 `schemas/book.schema.json`，注册表定义于 `schemas/catalog.schema.json`。

`catalog/preview.yaml` 是独立的、仅本地预览注册表；只有显式传入 `--preview` 才读取，输出固定为 `.preview/`，不会写入 `dist/`。两本原创样例在此登记，保持 `draft`，人工批准为 null。预览不是审核。

正式构建会拒绝任何无资格的登记条目，而非静默跳过。资格要求人工批准身份、时间及本地审核决定记录，来源块已核验，无未解决 P0/P1。空注册表是合法状态，能生成空门户。

## 输入与隔离

每本书保留 `_quarto.yml` 独立项目配置，但校验要求其等于 `book_config(metadata)` 生成的安全配置。门户使用 `portal_config()`。渲染时不直接运行源项目；构建在新临时项目中生成配置，只复制元数据显式声明的章节与栅格图片，拒绝绝对路径、穿越、符号链接与重复 YAML 键。构建不复制源项目中的 hooks、filters、extensions、局部元数据或自动资源 glob。

M0 只接受无 front matter、无可执行单元、无短代码/包含指令的静态 QMD；允许普通章节链接和静态代码块。源链接预检要求本地目标位于章节/资源白名单。实际命令为 `quarto render <temporary-project> --to html --no-execute`，配置同时设置 `execute.enabled: false`、`execute.eval: false`，并核对 Quarto 版本 1.10.19。出版不得执行提取代码；该隔离不是操作系统沙箱，也不是 HTML/JS 清洗器，审核仍须覆盖内容及外部链接。

## 构建事务与产物

1. 读取指定注册表，Schema/路径/资格/来源校验；正式模式强制 strict。
2. 临时目录生成门户列表及安全配置，独立渲染门户和登记书籍。
3. 组装为暂存的 `index.html` 和 `books/<id>/`，各书保留自己的 `site_libs/`。
4. 检查 HTML 站内链接、锚点、资源，CSS `url()`/`@import`，入口及发布边界。
5. 全部通过才替换目标目录；替换失败尝试恢复旧产物。失败报告 `ok: false, delivered: false`，旧成功产物可保留，临时目录自动清除。若进程被强制中断留下 `.previous`，拒绝下一次替换，要求人工检查，不自动清理。

产物禁止 PDF、QMD、源代码、YAML、草稿、缓存、隐藏目录及未登记书籍；允许 Quarto 运行时的 HTML/CSS/JS/JSON、字体和图片等静态资源。元数据、审核决定、provenance 只用于校验，不复制进站点。构建报告记录模式、交付状态、Quarto 版本、书籍 ID、文件数与总字节数。

跨项目引用应使用显式 URL，不能依赖 Quarto 跨项目原生引用。站内链接必须相对路径，根路径 `/...` 在 GitHub Pages 仓库前缀下不安全，会被拒绝。外部 URL 不联网检查；JS 动态生成的 URL 不做静态解析。Quarto 1.10.19 的浅深主题会重复两个 stylesheet link ID；检查仅豁免 `<link>` 上的 `quarto-bootstrap`、`quarto-text-highlighting-styles`，正文重复锚点仍报错。

## 阶段与权限

M0 已实现出版平台、两本样例、Schema、统一构建、链接检查及 CI 配置。M1 PDF 导入、OCR、解析器/缓存，M2 Pagefind、增量构建、概念索引和知识图谱均未实施。

PR 工作流无部署权限；Pages 工作流仅手动触发且限 main，上传路径固定为 `dist`。仓库及环境保护须由维护者配置，本次未实际运行 GitHub Actions 或发布 Pages，也未伪造人工审核。工具版本、真实渲染和未验证项详见 [验证记录](VERIFICATION.md)。
