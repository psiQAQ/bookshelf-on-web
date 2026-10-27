# 量子化学 Python 笔记：核验与本地验收

核验日期：2026-10-27。状态：本地内容与网站核验完成，**尚未获用户公开批准**。本记录不是原书转载许可，也不是发布批准。

## 验收对象与证据

- 正文：`books/quantum-python-notes/`，导读及16章；26个完整原创 Python 示例、48道有解题指引的练习。
- 范围与来源：[任务规格](../../.scratch/quantum-python-notes/spec.md)、[来源基线](quantum-python-source-baseline.md)、[章节覆盖表](quantum-python-coverage.md)。
- 独立内容审阅：[第1–4章](quantum-python/review-a.md)、[第5–7章](quantum-python/review-b.md)、[第8–11章](quantum-python/review-c.md)、[第12–16章](quantum-python/review-d.md)。审阅者使用 `openai-codex/gpt-6.1-sol`，与写作运行分离。
- [集成与修复复审](quantum-python/integration-review.md)：配置、预览门禁、验证程序、导读、来源索引与第7章修复。
- 可复算记录：`quantum-python/notes-examples.json`、`quantum-python/notes-browser.json`、`quantum-python/preview-build.json`、`quantum-python/preview-links.json`、`quantum-python/tests.txt`。示例报告含章节及代码块 SHA-256；浏览器报告含页面、尺寸、公式、溢出与交互记录。
- 审阅版本身份见 `quantum-python/manifest.json`（SHA-256前将CRLF统一为LF）；用户批准须对应所交付的 Git 提交及该内容清单。实质内容变更后重新确认。

## 内容与来源核验

四组 reviewer 完整读取各自章节，并对照报告列明的原书文本页，独立复算示例及练习。没有发现 P0/P1、原书代码复制、整段翻译或紧密改写。相似性核查限于已读来源页，不是全书逐字查重或版权鉴定。

第7章发现并修复两项 P2：

1. `cloud-idle-double-count`：将计算时长限定为不包含单列的空闲时段，避免费用双计。10个工作进程的例子为计算费4加空闲费0.8，共4.8。
2. `cloud-final-ack-reconciliation`：最后一次尝试提交成功而确认丢失时，先核对结果表再决定终态；增加单次尝试、结果26.0、仅一次计算/提交的回归断言。无法可靠查询远端结果时保留未知状态，不冒称失败。

集成 reviewer 静态复审确认上述修复。未解决 P0/P1/P2：0。正文标题去掉重复的人工章号，由 Quarto 统一编号；章节锚点未改变。

### 关键科学关系

主会话另以 PyMuPDF 1.26.7 非 OCR 渲染原 PDF，视觉检查以下页面。图片仅保存在被忽略的 `.local/notes-source-visual/`，不提交、不发布。

| 章节 | 视觉检查的 PDF／印刷页 | 核对点及独立验证 |
| --- | --- | --- |
| 12 | 485／478 | 原书12.1–12.3使用球谐／径向归一化；笔记明确区分笛卡尔归一化。原创s高斯例子由高斯积分推导，验证重叠 `exp(-1)` 与归一化。 |
| 13 | 568／561 | 原书13.7–13.10中的含2密度、J与K及交换系数1/2。笔记采用实AO约定，以自造低秩ERI检验J、K、F和电子能 `-35/36 Eh`；只作一次更新，未称自洽解。 |
| 14 | 622／616 | 原书的创建算符排列与“大于目标指标”的计数约定。笔记采用另一明确排列，以低位计数实现其一致符号，不混用。原创两位置模型检查Hermitian矩阵及解析基态根 `(1-sqrt(5))/2 Eh`。未运行原书代码。 |
| 15 | 648／642 | 原书15.1–15.8的指数波函数、相似变换及投影残差；原书限制求和与笔记无约束反对称自旋轨道求和的系数不能直接互抄。原创可分离模型检查残差、联合激发系数及能量可加性。 |
| 16 | 683／678、689／684 | 含2密度、能量加权密度和重叠导数；轨道响应及正交约束。笔记另外独立推导隐式切线/伴随方程，在非对称三变量模型中两条路线均给导数3，并做有限差分检查。 |

第1–11章的标准数学关系和单位由独立审阅手算与原创代码断言交叉检查，包括广播/误差口径、FFT约定、AD链式法则、重试期望、布局解释、编译摊销、并行粒度和GPU传输模型。没有将示意成本当硬件基准，也没有声称执行了真实云、GPU、MPI或FFI工程。

这些检查不证明原书全部公式正确，也不证明玩具程序可用于实际分子研究。各章保留适用条件与未覆盖内容；源文件缺失的索引、缩略语表和章间页没有补造。

## 原创代码与安全边界

`python scripts/verify_notes.py` 在专用虚拟环境（Python 3.12.13、NumPy 2.3.5）运行26个原创普通 `python` 围栏，全部通过退出状态及内嵌断言检查。标准输出与错误输出完整记录，标准输出不自动逐字比对。

每个例子使用独立临时目录、`python -I -B`、凭据环境变量白名单、文件/网络/子进程审计钩子和45秒超时。示例只读取本套笔记，不读取或执行原书程序；隔离防护针对已经审阅的原创代码，**不是可运行敌对 Python 或原生扩展的操作系统沙箱**。Quarto和公开构建不会调用此验证器。

复现依赖在 `.local/notes-verify-env/` 安装，没有修改项目运行依赖或全局配置：

```sh
uv venv .local/notes-verify-env --python .venv/Scripts/python.exe
uv pip install --python .local/notes-verify-env/Scripts/python.exe numpy==2.3.5 playwright==1.56.0
.local/notes-verify-env/Scripts/python.exe scripts/verify_notes.py
```

上述解释器路径适用于本次 Windows 环境；其他平台改用虚拟环境的 `bin/python`。

## 网站与浏览器

- 真实 Quarto 1.10.19：门户、两本既有样书及本书预览渲染成功；不是替身 renderer 的结果。
- 单元／集成测试共49项：48项通过（含设置 `QUARTO_TEST_EXECUTABLE` 后的真实Quarto测试）；1项因Windows无符号链接权限而明确跳过，未宣称该平台分支实测通过。
- 严格发布注册表仍为空。预览注册包含本书，输出仅到 `.preview/`；未批准与来源状态警告被保留，没有关闭门禁。产物链接／资源检查无错误，没有源PDF、QMD、解析缓存或未登记书籍。
- Chromium 141.0.7390.37／Playwright 1.56.0：390、768、1440 px，每个尺寸检查导读和全部16章，共51页；HTTP 200、公式全部渲染且无MathJax错误、页面不横向溢出。
- 三个尺寸均实际操作书内搜索、明暗主题、代码复制及前后章导航。搜索“费米”得到5项本书结果，没有跨书索引。
- 修复390px长显示公式撑宽页面的问题：安全配置内加入固定、限宽且可横向滚动的MathJax样式，没有允许书籍自定义执行配置。长代码由原有代码容器横向滚动。
- 浏览器初测曾记录导航打断字体加载的6次 `net::ERR_ABORTED`；集成 reviewer 读取的是这份失败报告，故其报告没有宣称通过。验证程序补充等待字体/页面就绪后重跑，最终记录无失败请求、无页面异常。没有把失败样本改写成成功。
- 样式使用远端字体及MathJax CDN。本次联网核验成功；离线或CDN不可达时的体验不在通过声明内。未完成公网部署与线上验证。

复现：

```sh
QUARTO_TEST_EXECUTABLE="$PWD/.local/tools/bin/quarto.cmd" .venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/validate.py --strict
.venv/Scripts/python.exe scripts/build.py --preview --quarto .local/tools/bin/quarto.cmd
# 先用 PLAYWRIGHT_BROWSERS_PATH 指向 .local/playwright-browsers 并安装 chromium。
.local/notes-verify-env/Scripts/python.exe scripts/verify_notes_browser.py
.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory .preview
```

浏览器验证脚本自带短生命周期的仅回环HTTP服务。最后一条命令为供用户阅读的持续预览服务；只服务 `.preview/`，不服务仓库根目录。

## 发布门禁与待用户决定

本书保持 `rights.public: false`、`review.status: draft`，来源状态保留 `needs_review`，所有批准字段为空。来源和内容已经过上述核验，但尚未完成最终发布登记，不能凭此报告通过严格发布。用户需确认待发布版本及原创内容许可；不得把用户对笔记的批准当作原书转载许可。

批准后再登记对应证据、更新正式注册及发布状态、复验并快进合并 main、推送和部署；部署成功后还须检查真实公开URL。目前没有进行这些操作。
