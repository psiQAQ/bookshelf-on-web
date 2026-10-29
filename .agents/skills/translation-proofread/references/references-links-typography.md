# 参考文献、链接、排版与发布契约

命令一律从仓库根目录执行。本文里的修复、构建、发布步骤**不构成执行授权**。

## 1. 参考文献：先保完整，再调版式

**现象**：`.qmd` 里文献各占一行，网页却挤成一个巨大段落；条数对但内容错位（第 09 章曾把 `[1]–[20]` 重复两遍、真正的 21–42 丢失）。
**成因**：
- Markdown 的普通换行不分段 —— 行间没有空行就被 pandoc 并成一段；
- 旧的重建脚本对每个分页片段都从索引 0 写入，后面的条目覆盖前面的。

**判据**：

```bash
python scripts/format_references.py --check   # 有待改章节退出 1，否则 0
```

它只判断「版式是否已是目标形态」，看 `changed` 而不是要求所有统计为零；`--check` 不写章节、不写报告。
**修复**：按 PDF 对齐作者、标题、编号、顺序 → 用闭合的 `::: {.ref-list}` 包裹、每条之间留空行 → 悬挂缩进必须成对设置：

```css
.ref-list p  { padding-left: 2.2em; text-indent: -2.2em; }
```

`format_section(lines, stats)` 只负责分段，**不负责恢复丢失条目**；`close_gaps` 只修地址内部被排版插入的空格。
**验收**：二次运行是不动点（幂等）；编号连续无重复，逐条对应原书。本书基线 17 章、349 条，重点复核 09/12/13/16 章。

## 2. URL：先修完整目标，再生成短标签

**现象**：正文出现裸 URL；链接看着能点，其实只包住半个主机名、半条路径或丢了锚点。
**成因**：PDF 折行、连字（`ﬁ`）、提前闭合的 `)`。两种典型残形（源码原样）：

- 路径被切断：目标写成 `https://peps.python.org/pep-` ，末尾留个右括号，下一段再接 `0427/#ﬁle-name-convention`；
- 锚点被挤出链接：目标以 `#` 结尾，紧跟的 `)` 后面才是 `authentication-custom-ip` 这类锚点文本。

**判据**（同一条命令，其余严格项一并检查）：

```bash
python scripts/audit_prose.py --check
```

| 命中码 | 判据 |
| --- | --- |
| `bare_urls` | 正文出现 `https?://…`，未包进链接 |
| `broken_links` | `](…)` 之后跟着主机续写（`SPLIT_LINK_HOST_RE`），或链接目标被截断（以 `#`、`-`、`_` 结尾）而后接 ASCII 尾巴（`LINK_TARGET_RE` + `TRUNCATED_URL_SUFFIXES` + `ASCII_TAIL_RE`） |

两者都**不豁免文献区**。

**修复**：`fit_ligatures` 把 `ﬁ` 等还原 ASCII；`split_url` 把句末 `.,;:` 留在链接外（`)` 不剥离）；`host_label(url)` 生成标签：DOI 域标 `DOI`、去掉 `www.`、普通域取末两段、代码列出的国家二级域取三段；`link_urls` 用 `URL_OR_LINK_RE` 优先保留已有链接，避免二次嵌套。
**验收**：裸 URL 与断链均为 0。**注意这不是联网可用性检查** —— 重要目标仍要 curl／打开核对响应与真实锚点（本书就用 curl 证过 `absolute_beginners.html` 200、`absolute beginners.html` 404）。

## 3. 中英文与数字间距

**现象**：中文与拉丁字母/数字之间缺空格（`发布Python软件包`）；或反过来的过度处理（在 `.data` 前插空格）。
**成因**：PDF 排版不区分；机械工具又不知道哪里是代码。

**判据**（AutoCorrect，只开 `space-word`，代码块关闭）：

```powershell
$cfg = 'C:\Users\ustcw\.agents\skills\text-prison\autocorrect\conservative.yml'
$files = (Get-ChildItem 'books/<slug>/chapters/*.qmd' -File).FullName
autocorrect --lint --format json --type markdown --config $cfg $files
```

- **必须显式 `--type markdown`**：AutoCorrect 2.16.3 不认识 `.qmd` 后缀，会静默返回 `{"count":0}`（假通过）；
- 遵守 `.gitignore`，探针文件放在被忽略目录里也会被跳过；
- 禁用 `--fix`；退出码 0 **不等于**无建议，要读 `messages[].lines`；`count` 也不是建议条数。

**修复**：只在中日韩字符与 `[A-Za-z0-9]` 的边界插空格；**不采纳**「在 `.data`/`.indptr` 这类以 `.` 开头的标识符前插空格」；`expm()`、`.to{format}()` 的括号保持半角；代码、公式、标识符内部、引用编号一律不动。
**验收**：复查归零（本书 262 → 0），并如实说明「本轮只做了 space-word 一类检查，不代表中文排版全面体检」。
**退出码别混用**：AutoCorrect 非零按失败处理；Vale 的 1 在有效 error 诊断时是「检查完成、有错误」，2 才是失败。

## 4. 发布契约：过门禁 ≠ 拿到授权

**现象**：改名、删图之后，注册表、metadata、`_quarto.yml`、provenance 不同步。
**成因**：这些文件共同定义构建白名单，必须共享同一个「书籍身份」。

**判据**：

```bash
python scripts/validate.py --strict     # 正式注册表；有 error 退出 1（并写报告）
python scripts/validate.py --preview    # 本地预览注册表
```

约束（`scripts/publishing.py`）：
- 目录名 == 注册表 id == slug（`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`），注册表路径严格是 `books/<id>/metadata.yaml`；
- `_quarto.yml` **解析后**必须等于 `yaml.safe_dump(book_config(load_yaml(metadata)), allow_unicode=True, sort_keys=False)` —— 是解析后比较，不是逐字节比文本；
- `assets` 只能是以 `assets/` 开头的 png/jpg/jpeg/gif/webp 且文件存在；
- 发布需 `review.status: approved` + `approved_by` / `approved_at` / `evidence_path`（非空 `docs/reviews/*.md`），且 `provenance.json` 全部 `verified`。

**验收**：以上同时满足，且无未解决的 P0/P1。**公开发布仍须用户批准具体版本**。

## 5. 新书执行顺序与构建验收

**文献对齐 → 分段/链接 → 间距 → 门禁 → 构建 → 站点核验。**

未获发布批准的书只登记 `catalog/preview.yaml`：

```bash
python scripts/validate.py --preview
python scripts/build.py --preview --quarto .local/tools/bin/quarto.exe
python scripts/check_site.py .preview --preview
```

**站点核验**：`python scripts/check_site.py <dir> [--preview]`（正式产物用 `check_site.py dist`，有 error 退出 1）。它拒绝根相对路径（Pages 有仓库前缀）、越界目标、缺失文件/锚点、未登记 slug；外链不抓取。
**构建**：固定 Quarto 1.10.19，`--no-execute` 静态渲染；预览只进 `.preview/`，永不进 `dist/`。
**验收**：看 `reports/preview-build.json`（或 `reports/build.json`）的 `ok`、`delivered: true`、`file_count`、`size_bytes`；再用宽屏与 390px 各看一下文献换行与横向溢出。

## 陷阱与反例

- `.qmd` 得到 `{"count":0}` 先查 `--type markdown` 与忽略规则，别记成通过。
- `:::` 围栏未闭合会让整章后续布局错乱；机器零命中不能代替渲染检查。
- 链接标签用主机名，不要把整条文献标题变成链接。
- 只设负 `text-indent` 会让文字向容器外突出，必须配等量 `padding-left`。
- `AGENTS.md` 的发布门禁是约束，不是授权；历史批准不自动覆盖新版本。
- 校验／构建／站点检查会写 `reports/` 或产物目录，纯只读核查时别跑它们。
