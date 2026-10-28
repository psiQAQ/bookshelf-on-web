#!/usr/bin/env python3
r"""渲染层核验：逐页统计 MathJax 的展示式、行内式与真正的错误元素。

`scripts/check_math.py` 只查源码形态，查不出「命令名合法但公式被截断」这类问题；
真正下判断的地方是渲染结果。这里用 Edge 的 headless 模式把每章的 HTML 载入并
`--dump-dom`，然后统计：

* `<mjx-container ... display="true">`：展示式数目；
* 其余 `<mjx-container>`：行内式数目；
* `<mjx-merror`、`data-mjx-error` 与 `;color:red`：MathJax 的**错误标记**。MathJax v4 的
  CHTML 输出不生成 `<mjx-merror>`，未定义命令的实体是
  `<mjx-mtext data-semantic-attributes="latex:\inom;color:red" style="color: red;">`，
  只认 `<mjx-merror` 会漏判——`$\inom{14}{7}$` 就是这么漏过去的；
* 没有 `<mjx-container>` 的 `<span class="math ...">`：**根本没被处理**的公式——这是
  最隐蔽的一种失败，页面上直接把 `\(\inom{14}{7}\)` 当正文吐出来，不报错。

注意两条踩过的坑：

* 不能只数展示式——行内公式里的未定义命令（例如 `$\\inom{14}{7}$`）在页面上是
  `<span class="math inline">`，只统计 `display="true"` 会漏掉；
* 正则不能用裸 `mjx-merror`——MathJax 自己注入的 CSS 里就有
  `mjx-merror { display: inline-block; }` 这条规则，会把页数当成错误数。

用法::

    uv run python scripts/check_math_render.py                  # 读 .preview
    uv run python scripts/check_math_render.py --root dist
    uv run python scripts/check_math_render.py --report reports/math-render.json

没有 Edge 时打印 `Not Run` 并退出 0（不因为缺少浏览器就把门禁判成失败）。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = "python-for-quantum-chemistry-a-full-stack-programming-guide"
EDGE_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)
DISPLAY_RE = re.compile(r"<mjx-container[^>]*display=\"true\"")
CONTAINER_RE = re.compile(r"<mjx-container")
ERROR_RE = re.compile(r"<mjx-merror[ >]|;color:red")
ERROR_ATTR_RE = re.compile(r"data-mjx-error")
MATH_SPAN_RE = re.compile(r'<span class="math (?:inline|display)"(.*?)</span>', re.S)


@dataclass
class PageResult:
    file: str
    display: int
    inline: int
    errors: int
    unprocessed: int


def find_edge() -> str | None:
    for candidate in EDGE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return shutil.which("msedge") or shutil.which("microsoft-edge")


def chapters_dir(root: Path) -> Path:
    return root / "books" / BOOK / "chapters"


def dump_dom(edge: str, page: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="edge-math-") as profile:
        command = [
            edge,
            "--headless=old",
            "--no-sandbox",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={profile}",
            "--virtual-time-budget=15000",
            "--dump-dom",
            page.as_uri(),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return completed.stdout


def inspect(dom: str, name: str) -> PageResult:
    display = len(DISPLAY_RE.findall(dom))
    inline = len(CONTAINER_RE.findall(dom)) - display
    errors = len(ERROR_RE.findall(dom)) + len(ERROR_ATTR_RE.findall(dom))
    unprocessed = sum(1 for body in MATH_SPAN_RE.findall(dom) if "mjx-container" not in body)
    return PageResult(name, display, inline, errors, unprocessed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".preview", help="构建产物根目录（默认 .preview）")
    parser.add_argument("--report", help="把明细写入该 JSON 文件")
    parser.add_argument("--check", action="store_true", help="出现渲染错误时退出 1")
    args = parser.parse_args(argv)

    root = (ROOT / args.root).resolve()
    pages = sorted(chapters_dir(root).glob("*.html"))
    if not pages:
        print(f"Not Run: {chapters_dir(root)} 下没有 HTML，先运行 scripts/build.py")
        return 0
    edge = find_edge()
    if edge is None:
        print("Not Run: 未找到 Microsoft Edge，跳过渲染核验")
        return 0

    results = [inspect(dump_dom(edge, page), page.name) for page in pages]
    for result in results:
        flag = "" if not (result.errors or result.unprocessed) else "  <-- MathJax error"
        print(
            f"{result.file:28s} display={result.display:4d} inline={result.inline:4d} "
            f"errors={result.errors} unprocessed={result.unprocessed}{flag}"
        )
    total_display = sum(r.display for r in results)
    total_inline = sum(r.inline for r in results)
    total_errors = sum(r.errors for r in results)
    total_unprocessed = sum(r.unprocessed for r in results)
    print(
        f"TOTAL display {total_display} inline {total_inline} "
        f"errors {total_errors} unprocessed {total_unprocessed}"
    )

    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "pages": [asdict(r) for r in results],
                    "total": {
                        "display": total_display,
                        "inline": total_inline,
                        "errors": total_errors,
                        "unprocessed": total_unprocessed,
                    },
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.check and (total_errors or total_unprocessed):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
