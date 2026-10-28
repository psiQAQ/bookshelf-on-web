#!/usr/bin/env python3
"""公式的机械检查：LaTeX 命令白名单、环境配对、控制字符与转义残留。

中文直译稿里的公式来自三条路径——PDF 文本层摘抄、local-ocr 识别、人工改写，
每条路径都可能留下「看不出来的残形」：

* `\\inom`（`\\binom` 掉了首字母）这类命令在页面上只会渲染成 MathJax 的
  未定义命令错误，正文源码里却和正常命令长得一模一样；
* 用脚本批量改写时，heredoc / 字符串转义会把 `\\times` 变成 TAB、把 `\\n`
  变成真换行或字面 `\\n`，这些字符在编辑器里几乎不可见；
* 公式块里 `\\begin{...}` 与 `\\end{...}` 数目不一致时 MathJax 会静默截断。

判据有三条：命令名必须在 `scripts/latex_commands.txt` 里、数学区不得含控制字符、
正文不得出现游离的转义序列。退出码 0 表示干净，1 表示有命中。

用法::

    uv run python scripts/check_math.py            # 打印摘要
    uv run python scripts/check_math.py --check    # 有命中则退出 1
    uv run python scripts/check_math.py --report reports/math-commands.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = Path(__file__).resolve().with_name("latex_commands.txt")

BACKSLASH = "\\"
COMMAND_RE = re.compile(re.escape(BACKSLASH) + r"([A-Za-z]+)")
DISPLAY_RE = re.compile(r"\$\$(?P<body>.+?)\$\$", re.S)
INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(?P<body>[^$\n]+?)(?<!\$)\$(?!\$)")
ENV_RE = re.compile(r"\\(begin|end)\{([A-Za-z*]+)\}")
# 数学区里出现这些字符，说明写文件时转义被吃掉了（TAB/BEL/BS/VT/FF）。
CONTROL_CHARS = {7: "BEL", 8: "BS", 9: "TAB", 11: "VT", 12: "FF"}
# 正文（非数学、非代码）里不该出现的转义序列；`\\n` 常用于代码串，所以只查散文行。
STRAY_ESCAPE_RE = re.compile(r"(?<![\\$])\\[ntrf]")


@dataclass(frozen=True)
class Finding:
    chapter: str
    line: int
    kind: str
    detail: str


def load_allowlist(path: Path = ALLOWLIST) -> set[str]:
    names = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        entry = raw.strip()
        if entry and not entry.startswith("#"):
            names.add(entry)
    return names


def chapters(root: Path = ROOT) -> list[Path]:
    return sorted(root.glob("books/*/chapters/*.qmd"))


def split_fences(text: str) -> list[tuple[int, str, bool]]:
    """按围栏代码块切分，返回 (起始行号, 内容, 是否在围栏内)。"""
    chunks: list[tuple[int, str, bool]] = []
    buffer: list[str] = []
    start = 1
    in_fence = False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.strip().startswith("```"):
            chunks.append((start, "\n".join(buffer), in_fence))
            in_fence = not in_fence
            buffer = []
            start = number + 1
            continue
        buffer.append(line)
    chunks.append((start, "\n".join(buffer), in_fence))
    return chunks


def math_spans(body: str) -> list[tuple[str, bool]]:
    """抽出正文里的公式区（展示式优先，其次行内式），返回 (公式体, 是否展示)。"""
    spans: list[tuple[str, bool]] = []
    consumed: list[tuple[int, int]] = []
    for match in DISPLAY_RE.finditer(body):
        spans.append((match.group("body"), True))
        consumed.append(match.span())
    for match in INLINE_RE.finditer(body):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        spans.append((match.group("body"), False))
    return spans


def commands_in(math_body: str) -> list[str]:
    """公式体里出现的命令名；`\\\\` 是换行，不是命令。"""
    cleaned = math_body.replace(BACKSLASH * 2, " ")
    return [match.group(1) for match in COMMAND_RE.finditer(cleaned)]


def check_math_body(chapter: str, line: int, body: str, allowed: set[str]) -> list[Finding]:
    """公式体里的命令与环境配对；控制字符由按行扫描负责（每条只报一次）。"""
    findings: list[Finding] = []
    for name in commands_in(body):
        if name not in allowed:
            findings.append(Finding(chapter, line, "unknown_command", BACKSLASH + name))
    balance: dict[str, int] = {}
    for kind, env in ENV_RE.findall(body):
        balance[env] = balance.get(env, 0) + (1 if kind == "begin" else -1)
    for env, delta in balance.items():
        if delta:
            findings.append(Finding(chapter, line, "env_unbalanced", f"{env}:{delta:+d}"))
    return findings


def audit_chapter(path: Path, allowed: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for start, body, in_fence in split_fences(text):
        if in_fence:
            continue
        spans = math_spans(body)
        for offset, line in enumerate(body.split("\n")):
            number = start + offset
            for code, label in CONTROL_CHARS.items():
                if chr(code) in line:
                    findings.append(Finding(path.name, number, "control_char", label))
            if spans:
                continue
            if line.lstrip().startswith(("#", "|", ">")) or "`" in line:
                continue
            if STRAY_ESCAPE_RE.search(line):
                findings.append(Finding(path.name, number, "stray_escape", line.strip()[:40]))
        for span, _ in spans:
            findings.extend(
                check_math_body(path.name, start, span, allowed)
            )
    return findings


def audit(root: Path = ROOT, allowed: set[str] | None = None) -> list[Finding]:
    allowed = allowed if allowed is not None else load_allowlist()
    findings: list[Finding] = []
    for path in chapters(root):
        findings.extend(audit_chapter(path, allowed))
    return findings


def summarise(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.kind] = counts.get(finding.kind, 0) + 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="有命中则退出 1")
    parser.add_argument("--report", help="把明细写入该 JSON 文件")
    args = parser.parse_args(argv)

    allowed = load_allowlist()
    findings = audit(allowed=allowed)
    counts = summarise(findings)
    for finding in findings:
        print(f"{finding.chapter}:{finding.line}: {finding.kind}: {finding.detail}")
    print(f"allowed_commands={len(allowed)} chapters={len(chapters())} findings={len(findings)}")
    if counts:
        print(" ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "allowed_commands": sorted(allowed),
                    "findings": [finding.__dict__ for finding in findings],
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
