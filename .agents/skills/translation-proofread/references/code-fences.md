# 代码块与围栏

目标书的代码块从 PDF 文本层来，不是源码：缩进会丢、标识符里会被插空格、分页与行归并会破坏块边界。本书历史修复累计合并 **190 处**，说明「只检查冒号结尾」这类单条判据远远不够。

## 六类缺陷

### 1. 同一段代码被切碎

**现象**：闭围栏后紧跟新开围栏，第二块是第一块的续写（`def view_contour(...)` | `v = fn(mole, grids)`；`if __name__ == '__main__':` | 块体；表达式中间断开）。
**成因**：提取时按 `abs(dy) <= 2.6` 归并行、按页面高度切块，跨页或行距异常就多开一个围栏。

**机器判据**（`tests/test_chapter_markup.py`，三层按强度递增，最终兜底）：

| 测试 | 判据 |
| --- | --- |
| `test_no_code_fence_split_in_two` | 闭围栏后立即出现新围栏 |
| `test_no_code_block_split_by_a_blank_line` | 间隔只有空行（≤2 行）且满足任一：上一行以冒号或 `,+*-/=&|(` 结尾、上一行括号未闭合、下一行以 `)]}` 开头、上一行仍带缩进（围栏切在 suite 内）、下一行有缩进 |
| `test_no_adjacent_fences_without_prose` | 两块之间没有任何正文即报错，不限语言与缩进，只放过合法输出块 |

输出块豁免必须用真实 `OUTPUT_MARKER`（`tests/test_chapter_markup.py:18`）：

```python
r"^(In \[|Out\[|CPU times|Wall time|Wall clock|RuntimeWarning|Name:|%\d|\d+(\.\d+)? seconds)"
```

**修复**：删掉中间闭围栏、开围栏与多余空行，保留源码。**并块必须自证内容无损**：逐章比较「非空、非围栏行序列」在改前改后完全一致；缩进重建另记差异。

### 2. 围栏语言标错（渲染不出代码框）

**现象**：页面上的代码是等宽正文，没有代码框底色、没有复制按钮。
**成因**：Quarto **1.10.19** 的 skylighting 不认识 `text` / `ipython` / `ipython3` / `console` / `pycon`，pandoc 只输出裸 `<pre class="text">`。实测对照：

| 围栏信息 | 输出 HTML |
| --- | --- |
| ```python | `<pre class="sourceCode python code-with-copy">` |
| ```default | `<pre class="sourceCode default code-with-copy">` |
| ```text / ```ipython / ```console | `<pre class="text">`（无样式、无复制按钮） |

**机器判据**：`find_mislabelled_fence(path)`（`scripts/audit_prose.py`），命中码：

- `fence_language:text_unstyled` —— 凡 `text` 必报（应改 `default` 或真实语言）；
- `fence_language:python` —— `default` 内能 `ast.parse` 且顶层含真实语句（`CODE_STATEMENTS`）；
- `fence_language:toml` —— `default` 首个非空行是 TOML 段头且其余行是 `k = v`／段头／注释；
- `fence_language:default` —— `python`/`py` 围栏里出现 REPL 提示符（`REPL_LINE_RE`）。

相关常量：

```python
FENCE_OPEN_RE   = re.compile(r"^\s*```\s*([A-Za-z0-9_+\-]*)\s*$")
REPL_LINE_RE    = re.compile(r"^\s*(?:In \[\d*\]:|Out\[\d*\]:|>>> )")
TOML_SECTION_RE = re.compile(r"^\s*\[[\w.\-]+\]\s*$")
```

**注意**：探测器只覆盖这几种形状，不是完整的语言白名单；「语言审计零命中」不等于「所有围栏语言都对」。本书实测的合法集合记在 `tests/test_quantum_notes.py` 的 `STATIC_LANGUAGES = frozenset({"python", "default", "bash", "yaml", "toml", "ini", "c", "fortran"})`。

**修复**：源码用真实语言；REPL 会话、终端输出、目录树、文件名清单用 `default`。**不能为了通过解析把坏源码降级成输出**。

### 3. 整行代码漏在围栏外

**机器判据**：`find_code_outside_fence(path)` —— 跳过围栏、公式、文献区、中文行、含 `$` 的行与结构标记后，对被选中的行做 `ast.parse`，得到真实语句即命中 `code_outside_fence`。

**为什么不用正则**：正文里的 `open()`、`file.close()` 会被正则算成代码；AST 才分得清「整行是语句」与「句子里有函数名」。
**放宽**：`CODE_OUTSIDE_FENCE_WHITELIST` 只豁免 `perf stat` 事件名形状 `r"^-\s-?[a-z0-9_.:]+,\s*$"`，不是任意列表豁免。
**局限**：只查顶层节点，独立调用是 `ast.Expr`，`open()` 这类单独一行仍可能漏；不要声称已全覆盖。

### 4. 围栏里其实是正文

**现象**：`generatetheirCartesianpowers (ix, iy, iz)and (jx, jy, jz).`、`color='darkgreen' and color='tab:purple'.Furthermore,Matplotlibsupports` —— 英文正文被粘连后当成代码。
**机器判据**：`find_prose_in_fence(path)`，命中 `prose_in_fence:cjk`（中文字符 ≥6）或 `prose_in_fence:english`（无中文、英文字母 ≥30、空白分词 ≥4、不含 `CODE_CHARS_RE`）。这是**候选清单**：合法 docstring 与错误信息也会命中，粘连英文或含括号的句子反而可能漏。
**修复**：对照 PDF 把整句译回中文，标识符放进行内代码（`` `x` ``）；不要只改围栏语言了事。

### 5. 缩进与标识符被破坏

**现象**：整块顶格、`l s u m=l x+l y+l z`、`i nrange`、`a i`、`R a+a j`、`i= =1`、`x. sum`。
**判据**：对 ```python 围栏统计 `ast.parse` 失败数（本书曾 342/673，写 skill 时为 242/570）。失败即「不可执行」，只能人工按页修。
**修复**：必须看原页，**不能全局删空格**（`a i` 可能是 `ai`，也可能是 `a_i`）。批量正则修补的命中率极低（试过 4 类规则只让 5 个块转好），不要指望自动修好。

### 6. 目录树只剩文件名

**现象**：围栏里全是一行一个文件名，没有任何连接符。
**成因**：树的连接线是 PDF 的矢量图形，文本层里根本不存在；缩进也不足以定父子关系。
**判据**：搜索「目录结构／结构如下／布局如下」标题，找「所有非空行都是纯文件名」的围栏。**仓库没有目录树正确性自动断言**，只能人工核。
**修复**：看 PDF 页面 + 文字横坐标确认层级，用 `├──` / `│` / `└──` 重画，每级四空格（空格，不要 TAB）；跨页的树要合成一块。本书样例：`chapters/01-environment.qmd` 的 mypkg（§1.1.2.1）、core_repo/extensions（§1.1.2.3）、项目布局（§1.4）。

## 新增一本书的执行顺序

1. **先确认扫描对象**：`audit_prose.py` 缺省扫本书，用 `--book <路径或 slug>` 指向新书即可（`resolve_book()` 解析，有测试覆盖）；`audit_book(book: Path = BOOK) -> dict` 也可直接调用。但 `tests/test_chapter_markup.py`、`tests/test_quantum_notes.py`、`scripts/check_math_render.py` 仍绑定本书路径与基线，必须先适配。
2. **先修结构，再修分类**：断裂、漏出代码、夹入正文 → 语言标记 → 缩进/标识符/目录树。
3. **跑回归**：`python -m unittest tests.test_audit_prose tests.test_chapter_markup` + `python scripts/audit_prose.py --check`。
4. **看渲染**：构建预览后确认代码都是 `sourceCode … code-with-copy`，没有裸 `<pre class="text">`。`check_math_render.py` 不是代码框检测器，别拿它当证据。

## 陷阱与反例

- 正则判代码会误报正文里的 `open()`；必须 AST。
- `CODE_PATTERNS` 是 `(正则, 理由)` 二元组，遍历要解包。
- `str.replace(old, new, 1)` 只修第一处，改完全量复扫。
- 「当前零命中」不是测试有效的证据：测试要用真实正例（`CodeOutsideFenceTests` 用增量赋值，`FenceLanguageTests` 覆盖四种命中码 + 裸记号/数字/会话反例）。
- 严格通过 ≠ 源码正确：`prose_in_fence` 仍有 100 条待甄别；不可解析的坏代码不能算已验收。
- 数字口径会随修订变化（673/342 是历史值，570/242 是当前值），引用时标明是哪个版本，别混用。
