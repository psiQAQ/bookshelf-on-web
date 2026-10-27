# 原书章节与原创笔记覆盖表

状态：16章均已编写、独立审阅并完成本地核验；未获用户公开批准。每章包含学习目标、展开讲解、原创示例及3道带解题指引的练习。证据见[核验报告](quantum-python-verification.md)。

来源：Qiming Sun，*Python for Quantum Chemistry: A Full Stack Programming Guide*（2025）。下表范围由主会话逐章核实开章/末页并检查章内印刷页码连续性；印刷右端是实际现有章末页，不含缺失章间页。目录在本地 PDF 第9–17页。目录未列附录；缺失的索引和缩略语表不纳入16章笔记覆盖承诺，也不补造内容。

所有笔记路径均相对 `books/quantum-python-notes/`。完整英文标题是引用定位信息，不意味着翻译对应章的全部内容。笔记按原创问题组织，不复刻原书小节和示例。

| 章 | 原书章名 | 印刷页 | PDF物理页 | 笔记路径 | 原创学习重点 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Python programming environment | 3–56 | 18–71 | `chapters/01-environment.qmd` | 解释器与依赖身份、环境隔离、可复现项目与测试 | 已核验 |
| 2 | Data processing | 57–117 | 72–132 | `chapters/02-data.qmd` | 数组形状/布局/广播、视图、表格对齐与误差 | 已核验 |
| 3 | Visualization | 119–143 | 133–157 | `chapters/03-visualization.qmd` | 数据到图的映射、尺度/误导、网格与轨道可视化边界 | 已核验 |
| 4 | Scientific computing tools | 145–171 | 158–184 | `chapters/04-scientific-tools.qmd` | 稳定线代、稀疏表示、张量收缩与频域计算 | 已核验 |
| 5 | Meta-programming and non-numerical computation | 173–194 | 185–206 | `chapters/05-metaprogramming.qmd` | AST/符号表示、代码生成与自动微分的区别 | 已核验 |
| 6 | Input and output | 195–222 | 207–234 | `chapters/06-io.qmd` | 数据格式、模式/单位、缓冲/内存映射、安全持久化 | 已核验 |
| 7 | Working with cloud | 223–261 | 235–273 | `chapters/07-cloud.qmd` | 可重试工作流、资源成本、任务队列与云适用边界 | 已核验；2项P2已修复 |
| 8 | Foreign language interfaces | 265–304 | 274–313 | `chapters/08-ffi.qmd` | ABI、布局/所有权、C/C++/Fortran/Rust接口契约 | 已核验 |
| 9 | Program performance optimization | 305–394 | 314–403 | `chapters/09-performance.qmd` | 测量、成本模型、编译、缓存与算法改写 | 已核验 |
| 10 | Parallel computation | 395–448 | 404–457 | `chapters/10-parallel.qmd` | 线程/进程/异步、通信成本、数据划分与同步 | 已核验 |
| 11 | GPU programming | 449–474 | 458–483 | `chapters/11-gpu.qmd` | 传输/吞吐、数组框架、stream与内核的性能边界 | 已核验 |
| 12 | Integral evaluation | 477–558 | 484–565 | `chapters/12-integrals.qmd` | 高斯积分、递推/求积、对称性和积分变换 | 已核验 |
| 13 | Mean-field methods | 559–611 | 566–618 | `chapters/13-mean-field.qmd` | 非正交基、密度/J/K、SCF收敛、DFT与DIIS限制 | 已核验 |
| 14 | Post Hartree-Fock I: full configuration interaction | 613–640 | 619–646 | `chapters/14-fci.qmd` | 行列式、费米子符号、变分性与矩阵自由求解 | 已核验 |
| 15 | Post Hartree-Fock II: coupled cluster | 641–673 | 647–679 | `chapters/15-coupled-cluster.qmd` | 指数波函数、CCD/CCSD、振幅残差与张量实现 | 已核验 |
| 16 | Molecular properties | 675–712 | 680–717 | `chapters/16-properties.qmd` | 期望值/能量导数、轨道响应、核梯度与隐式微分 | 已核验 |

## 每章完成条件

1. 具有学习目标、足够展开的概念解释、假设/适用边界、原创示例或练习及解题指引；不是目录扩写或简单摘要。
2. 明确哪些是参考书的主题，哪些是笔记新增的解释、数据和练习；来源指向具体印刷/PDF页或章节 DOI。
3. 无整段翻译、紧密改写、原图或原书代码复制。能独立阅读但不宣称替代原书。
4. 公式、代码、站内导航和渲染经过验证；来源不确定性写入核验报告。每一章都经过独立 reviewer 检查。
5. 覆盖状态与证据一致：编写完成不等于审阅完成，更不等于用户批准公开。

## 分工与证据入口

- 第1–4章、第5–7章、第8–11章、第12–16章分组委派给 `openai-codex/gpt-6.1-sol`。同一工作区串行写作；每组仅修改自己章文件。
- 共享首页、元数据、provenance、配置和本覆盖表由主 Agent 串行维护。
- 来源基线：`docs/reviews/quantum-python-source-baseline.md`。
- 科学公式、原创代码、独立审阅与浏览器验收：`docs/reviews/quantum-python-verification.md` 及 `docs/reviews/quantum-python/` 下的原始报告。
- “已核验”指本次原创内容与本地网站的约定检查完成，不表示原书全细节覆盖、真实云/GPU/MPI实测或公开发布批准。
