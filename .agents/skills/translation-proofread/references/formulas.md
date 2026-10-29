# 公式

原则：**OCR 只生成候选，PDF 页面才是依据；源码检查、浏览器渲染、逐式核对三者不可互相替代。**

本书的公式走过三条路径：PDF 文本层裁剪成 PNG → 本地 OCR → 人工改写。每条都留下过「看不出来的残形」。

## 1. 裁错、漏行与「假公式图」

**现象**：矩阵少一行、缺 `\iddots`/`\vdots`、公式里混进相邻正文；所谓「公式图」实际是章节标题（`10.8 OpenMP`）、英文正文（Hückel / SAP 模型段落）、`or err` 页边碎片、甚至代码。

**成因**：提取器的兜底启发式 `return len(text.split()) <= 6`（`.local/build_source.py`）会把短正文判成数学；裁剪边界又不等于公式边界，多行公式常被切掉首行或末行。

**机器判据**：`scripts/formula_ocr.py` 的 `normalise(latex) -> (body, numbers, warnings)`，重点警告：

| 警告 | 含义 |
| --- | --- |
| `text_looks_like_prose` | 识别结果里有成句英文 → 多半裁到了正文 |
| `duplicate_line` | 同行重复 → 多行公式被重复识别 |
| `unbalanced_env` | `\begin`/`\end` 不配对 → 环境被截断 |
| `multi_number` / `number_mismatch` | 一个块里出现多个编号，或编号与图注不一致 |
| `env_rewrapped` / `env_normalised` | 环境被改写（`align*` → `aligned`），需人工确认语义未变 |

**无警告不代表正确**：Hankel 矩阵第一次重建就少了 `\iddots` 一行，直到对照 p87 才补成五行。

**修复**：按整页重裁，逐行核对上下标、矩阵行列与省略号方向；假公式图恢复成中文正文／已有标题／代码，**保留锚点**，不强行造数学块。

## 2. 编号兼容与锚点保真

**现象**：OCR 输出 `\eqno(12.3)` —— MathJax／KaTeX 都不支持；合并截图时丢编号、丢锚点。

**判据**：`build_proposals(chapter_path, ocr, inventory=None)` 对每个提案检查 `anchor`、`numbers_alt`、`numbers_ocr`、`warnings`。

**修复**：
- 编号改写为块末独立一行 `\qquad (12.3)`；
- 多式用 `aligned` 排版，逐行保留各自的印刷编号；
- 两张截图合并成一个展示块时，**所有原锚点都要保留**（可以连续几行 `[]{#eq-XX-NNN}`）。

**验收**（本书硬基线，`tests/test_quantum_notes.py`）：`$$` 展示块 **222** 个、`eq-` 唯一锚点 **223** 个，且禁止 `\eqno` 与公式图片。注意测试用的是 `set`，发现不了重复锚点 —— 需要另核对 `len(ids) == len(set(ids))` 与「迁移前后锚点集合相等」（数量相同不代表身份相同，不能靠新增无关锚点凑数）。

## 3. 文本层残片与压平副本

**现象**：正确公式下方还留着 `∑`、`∞ √ ∞ ′`、`− θij X`、`⎟⎟`（矩阵括号字形 U+239B–U+23AD）、孤立「。」，或整条坏副本：「数包含 `\inom{14}{7}^2 …`」这类压平后的公式文本。

**成因**：替换图片不会自动删除 PDF 文本层；只搜公式编号会漏掉无编号副本。

**机器判据**：`find_formula_remnant(path)`（`scripts/audit_prose.py`），命中码：

| 命中码 | 判据 |
| --- | --- |
| `formula_remnant:punctuation` | 整行含 `.)` 或 `,)` |
| `formula_remnant:equation_number` | 整行以 `(12.62)` 这类编号开头且行内无 `$` |
| `formula_remnant:weight_function` | `权函数(为\|是)` 后面不是行内公式 |
| `formula_remnant:operators` | `∑∇√∫∂` 出现 ≥2 次且含 `=` |

先摘白名单 `FORMULA_REMNANT_WHITELIST`（合法记号如 `(itemsize * (n+1),)`、`vrr({...})`、`(slice(None),)*axis + (0,0)`）再判。短碎片另由 `tests/test_chapter_markup.py` 覆盖。

**修复**：先确认公式本体完整，再删副本并接回正文；只剩残片时按 PDF 重建，**不能一删了之**（本书因此补回 (13.20)、(16.24)、(16.25) 三块整式）。

## 4. 行内公式与转义损坏

**现象**：`x_{i+1}` 被压成 `xi +1`；`\binom` 变 `\inom`；`\times` 变成 TAB（页面显示 `   imes`）；`$x'$` 经处理变 `x\'` 触发 MathJax 报错。

**机器判据**：`scripts/check_math.py`（`--check` 有命中退出 1），四类 finding：

| kind | 判据 |
| --- | --- |
| `unknown_command` | 命令名不在 `scripts/latex_commands.txt`（84 条） |
| `env_unbalanced` | 数学区内 `\begin` 与 `\end` 数量不等 |
| `control_char` | 数学区含 TAB/BEL/BS/VT/FF |
| `stray_escape` | 正文出现游离的 `\n`/`\t`/`\r`/`\f` 字面量 |

**修复**：按页面恢复上下标；撇号写 `$x^{\prime}$`；未知命令先查错拼，**不能直接加进白名单**。
**证明门禁不空转**：`tests/test_math_commands.py` 用历史残形（`\inom`、TAB、未配对 `\begin`、字面 `\n`）当正例。

## 5. 浏览器渲染「假通过」

**现象**：源码检查全过，页面仍有红字错误，或直接把 `\(\inom{14}{7}\)` 当正文吐出来。

**关键事实**：MathJax **v4 CHTML 不生成 `<mjx-merror>`**。未定义命令的实体是：

```html
<mjx-mtext data-semantic-attributes="latex:\inom;color:red" style="color: red;">
```

所以判据是 `;color:red`（以及 `data-mjx-error`），**并且不能只数 `display="true"` 容器** —— 行内公式的未定义命令在 `<span class="math inline">` 里。

**机器判据**：`scripts/check_math_render.py`（`--root .preview --check`）逐章统计 `display` / `inline` / `errors` / `unprocessed`：

```python
ERROR_RE      = r"<mjx-merror[ >]|;color:red"
ERROR_ATTR_RE = r"data-mjx-error"
```

`unprocessed` = 没有 `mjx-container` 的 `<span class="math …">`，这是最隐蔽的失败。
缺少构建产物或 Edge 时打印 **`Not Run` 并退出 0 —— 不算通过**。

**验收**：17 章齐全、展示块计数与项目基线吻合、`errors=0`、`unprocessed=0`。

## 新增一本书时的操作顺序

1. 先读文本层与整页，建「页码 → 裁图 → 印刷编号 → 锚点」清单，区分公式／正文／标题／代码。
2. 只对确需 OCR 的裁图跑：

   ```bash
   D:/workspace/OCR/.venv/Scripts/python.exe -B D:/workspace/OCR/scripts/ocr.py run <dir> --mode formula --output <dir>
   ```

3. 整理成提案工具要的 JSON（`name`/`latex`/`page_size`），再跑：

   ```bash
   python scripts/formula_ocr.py --chapter 12-integrals --ocr .local/eq-ocr.json --inventory .local/eq-inventory.json --out .local/formula-proposals
   ```

   该工具**绑定本书**且只扫公式图片；新书必须改路径，且「零提案」不是验收。
4. 逐式核对后再落稿。**复杂矩阵/多行式识别不稳、或重裁后仍错，就停 OCR，按 PDF 手写**；不要从压平文本猜上下标。
5. 跑门禁：

   ```bash
   python scripts/check_math.py --check
   python scripts/audit_prose.py --check
   python -m unittest discover -s tests -p "test_math_commands.py"
   python -m unittest discover -s tests -p "test_formula_ocr.py"
   python -m unittest discover -s tests -p "test_quantum_notes.py"
   python scripts/build.py --preview --quarto .local/tools/bin/quarto.exe
   python scripts/check_math_render.py --root .preview --check
   ```

   OCR 缓存缺失时，存量 OCR 测试会自动跳过 —— 新书要建自己的数量基线，**不要照抄 222/223**。

## 陷阱与反例

- `str.replace(old, new, 1)` 只修第一处：`\inom` 改了一半，整行第二处仍在页面报错。
- bash heredoc / Python 字符串吞反斜杠：`\times` → TAB、`\b` → 退格。写 LaTeX 用 raw string 或 `chr(92)` 拼接，写完回读校验控制字符数为 0。
- `\iddots` 就算在别的书里能用，也不证明当前 MathJax 版本支持，必须实测；不要擅自改成方向不同的 `\ddots`。
- 不能用裸 `mjx-merror` 正则（会命中注入的 CSS 规则 `mjx-merror { display: inline-block; … }`）。
- 机器只验形态：命令合法不等于参数完整，矩阵能渲染不等于行数正确。
