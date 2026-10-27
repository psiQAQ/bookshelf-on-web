## Review

### 范围与方法

仅对分配的四章进行只读审阅：全文阅读正文、手算例子和练习、对照章末声明的具体来源页。没有修改文件，没有执行原书或笔记代码，也未运行构建、浏览器或测试。

### Correct：逐章结论

- **第8章：未发现问题。** ABI、序列格式、数组布局与所有权的区别清楚，Fortran 与 Rust 的边界条件没有过度泛化。独立手算两种正确布局均得 `[-1, 15]`，错误布局解释得 `[5, 7]`，数据长度为48字节，与正文一致。  
  证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/08-ffi.qmd:74–125`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/08-ffi.qmd:149–165`。

- **第9章：未发现问题。** 测量边界、资源下界、编译摊销和缓存正确性具有实质讲解，且区分了模型与实测。手算区间结果为 `[6, 8, 0, 0]`、直接读取11次；编译方案24次持平、25次首次严格更快。浮点前缀和的消去风险已有明确提示，练习中的加速比和带宽计算正确。  
  证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/09-performance.qmd:61–122`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/09-performance.qmd:135–168`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/09-performance.qmd:186–190`。

- **第10章：未发现问题。** 线程示范没有冒称加速；GIL、进程启动、异步竞态、MPI调用顺序和缓冲区生命周期均说明了适用条件。手算分块平方和为14、5、25，总和44、均方5.5；粒度模型的串行、四工作者、八工作者时间分别为51.2、31.6、25.2毫秒，结果一致。  
  证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/10-parallel.qmd:42–94`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/10-parallel.qmd:96–139`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/10-parallel.qmd:155–187`。

- **第11章：未发现问题。** 递推闭式解、传输成本、设备带宽、异步计时和跨stream事件依赖讲解充分。手算三步结果为 `[1.75, 2, 2.25]`；单步CPU/GPU为0.800/1.090毫秒，20步CPU/驻留GPU/逐步往返GPU为16.000/2.800/21.800毫秒。理想流水线练习的23毫秒正确，正文明确限定了独立资源与可重叠假设。  
  证据：`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/11-gpu.qmd:31–127`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/11-gpu.qmd:162–209`、`D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/11-gpu.qmd:223–227`。

### 来源与原创性

四章均明确区分参考书主题与新增解释、数据、例子、练习。对照实际读取的来源页，未发现原书代码复制、长篇翻译或紧密改写：笔记的布局实验、整数前缀和、平方和摘要、玩具递推，与来源中的结构体、正交化、Coulomb张量等示例不同。

证据入口：

- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/08-ffi.qmd:171–175`
- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/09-performance.qmd:196–200`
- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/10-parallel.qmd:199–203`
- `D:/workspace/bookshelf-on-web/books/quantum-python-notes/chapters/11-gpu.qmd:233–237`

### 实际读取记录

**要求与来源基线，均全文读取：**

- `D:/workspace/bookshelf-on-web/.scratch/quantum-python-notes/spec.md`
- `D:/workspace/bookshelf-on-web/docs/reviews/quantum-python-coverage.md`
- `D:/workspace/bookshelf-on-web/docs/reviews/quantum-python-source-baseline.md`

**正文：**上述四个完整章节文件均全文读取。

**来源文本：**以下编号均对应完整路径  
`D:/workspace/bookshelf-on-web/.local/quantum-source/page-NNN.txt`；所列连续范围内的每页均已读取，编号为PDF物理页：

| 用途 | 实际读取页 |
|---|---|
| 目录 | 012–014 |
| 第8章 | 274、277–282、292、301、305–306、308、310–311 |
| 第9章 | 314–315、322、325、335–336、356、369、375、383–384、389 |
| 第10章 | 404–405、410–412、415、426、428、431、435、444–446、448 |
| 第11章 | 458、461–470、475 |

### Finding与阻断问题

No issues found.

没有符合报告条件的P0/P1/P2问题，没有阻断问题。未应用任何修复。

### 剩余限制

- 来源对照限于上述具体页，不构成原书全章的穷尽相似性检查。
- 未进行PDF视觉核对；没有仅凭提取文本中失真的公式认定错误。
- 数值结论来自静态推理和手算，不代表代码已执行或实际性能已验证。
- 本机FFI、GPU、MPI及框架版本行为未作运行验证；首页、元数据、构建集成不在本次范围。

**Merge verdict：OK with notes。** 仅表示这四章的静态内容审阅未发现问题，不构成发布批准；运行与渲染验证仍由主会话完成。