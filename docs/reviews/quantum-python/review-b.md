## Review

只读审阅；未修改文件，未执行原书或笔记代码，未运行构建或浏览器验证。

### Correct：逐章结论

- **第5章**：No issues found. AST、符号表达式与计算图区分清楚；双数规则、方向导数及示例的值 `17`、导数 `14` 正确，立方练习的值 `8`、导数 `12` 正确。安全与适用范围没有过度承诺。证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/05-metaprogramming.qmd:9-159`。
- **第6章**：No issues found. 玩具势能的单位与 `2,0,2` 数值一致；JSON 验证、npy 往返及字节计数逻辑正确；明确区分刷新、持久化和原子提交。证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/06-io.qmd:13-188`。
- **第7章**：具有实质教学内容；给定示例的均方偏差、退避记录、有限重试期望及练习算术正确。另有以下两项 P2 修正建议。
- **来源与原创性**：三章均区分主题参考与新增解释、数据、代码及练习。对照下列实际读取的来源页，未发现原书代码复制、整段翻译或紧密改写；这不代表对未读全书内容的排除性证明。

### Finding：P2 — 成本模型可能重复计算空闲费用

**位置：** `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd:22-27`

公式同时包含 `Σ r_i t_i` 和 `C_idle`，但将 `t_i` 定义为“计费小时数”。空闲资源仍在计费时，其费用已经进入前一项。

**反例：** 沿用正文的10个工作进程，每个计算1小时后空闲0.2小时。按“计费小时数”取 `t_i=1.2`，计算项为 `10×0.4×1.2=4.8`；再加正文的空闲费 `0.8`，得到 `5.6`，重复计费。

**最小修法：** 将 `t_i` 明确定义为“不含另列空闲时段的计费运行小时数”；或者保留全部计费小时数，并删除独立的 `C_idle` 项。正文现有计算示例本身无需改数值。

### Finding：P2 — 最后一次确认丢失仍被记录为失败，遗漏提交后核对分支

**位置：** `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd:121-130`

提交成功后触发 `"after"`，若恰好耗尽尝试次数，代码直接追加 `"failed"` 并抛出异常，没有核对已提交结果。这与本章强调的“提交结果与任务状态一致”及“未知结果不能等同未执行”存在教学上的不一致。

**静态反例：** 对尚未缓存的新任务，取 `values=[1.0,3.0]`、`target=7.0`，调用 `run_task(task, ["after"], max_attempts=1)`。按代码顺序，结果表已登记 `26.0`，提交记录也已增加；随后却进入终止失败分支。该问题在串行内存模型内即可出现，不依赖并发或磁盘故障。

**最小修法：** 终止前核对结果表，存在有效结果则返回已完成结果；若要模拟无法核实的远端状态，则使用 `unknown`／待核对状态并说明恢复流程。补充“末次尝试发生提交后确认丢失”的练习或断言。

### 阻断问题与结论

- **P0/P1 阻断问题：无。**
- **Fixed：无；本次只读。**
- **Merge verdict：OK with notes。** 仅针对分配正文，不构成发布批准。

## 实际读取范围

### 要求与基线

- `D:/workspace/bookshelf-on-web/.scratch/quantum-python-notes/spec.md`
- `D:/workspace/bookshelf-on-web/docs/reviews/quantum-python-coverage.md`
- `D:/workspace/bookshelf-on-web/docs/reviews/quantum-python-source-baseline.md`

### 完整正文

- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/05-metaprogramming.qmd`
- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/06-io.qmd`
- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/07-cloud.qmd`

### 原书文本页

以下均实际完整读取，对应路径为 `D:/workspace/bookshelf-on-web/.local/quantum-source/page-NNN.txt`：

| 用途 | NNN（PDF物理页） |
|---|---|
| 目录定位 | 011、012 |
| 第5章 | 185、186、188、189、190、193、194、198、199、202 |
| 第6章 | 207、208、209、211、214、215、216、217、218、219、220、221 |
| 第7章 | 235、236、237、238、239、240、241、246、253、258、259、265、268、269 |

## 剩余限制

- 数值与控制流结论来自独立手算和静态推演，不是代码运行结果。
- 未视觉核对原 PDF；没有依据提取公式的排版失真判错。
- 未审首页、元数据、构建集成或其他章节；未完成集成未计为正文缺陷。
- 原创示例运行、Quarto 渲染与浏览器验收仍需主会话另行完成。