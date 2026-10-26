# Science Bookshelf

将获准公开的科学技术资料整理为独立的 Quarto Book，通过统一门户提供阅读入口。

## 当前状态

仓库目前只有基础骨架，尚未实现 PDF 转换、审核门禁、批量构建或 Pages 部署。
`catalog/books.yaml` 为空；现有未登记的书籍材料不代表已经获准发布。

## 目录

- `catalog/books.yaml`：书籍注册表；只有显式登记并通过审核的书籍才能进入发布流程。
- `portal/`：Quarto Website 门户。
- `books/`：独立书籍项目；目录存在本身不是发布许可。
- `drafts/`：未经批准的转换草稿，不进入默认发布流程。
- `scripts/`、`schemas/`、`tests/`：后续流水线、数据约束和测试。
- `docs/DESIGN.md`：架构边界与实施范围。
- `.scratch/m0-publishing/spec.md`：下一阶段验收条件。

## 本地准备

使用 Python 3.12 和 uv。依赖配置和锁文件已建立，当前没有第三方 Python 依赖。

```sh
uv sync --frozen
uv run python -m unittest discover -s tests -v
```

安装 Quarto 后，可单独预览空门户：

```sh
quarto preview portal --no-execute
```

规划建议固定 Quarto 1.10.19；实施 M0 时需验证该版本可获取并完成实际渲染。
上面的预览命令不代表整站构建或部署已完成。

## 发布边界

不得自动批准草稿或推定书籍公开授权。PDF 和提取出的代码是不可信输入，出版时不得执行。
原书内容与编辑注释应分开保存，并记录来源映射。OCR、GPU 解析、跨书搜索和知识图谱不属于首次搭建范围。
