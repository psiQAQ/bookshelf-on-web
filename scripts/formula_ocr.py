"""把 OCR 出来的公式 LaTeX 整理成可直接写进 qmd 的 `$$` 块，并列出需要人工复核的点。

OCR（local-ocr，`PP-FormulaNet_plus-M`）的结果不能直接上页面，常见问题是：
`\\eqno(12.3)`（MathJax 不认）、`align*` 里塞编号、同一行被识别两遍、裁剪时把
公式旁边的正文一起吃进 `\\text{}`。本脚本只做机械整理并**报警**，是否采用由人判断。

用法：
    python scripts/formula_ocr.py                                  # 打印统计
    python scripts/formula_ocr.py --chapter 12-integrals --out .local/formula-proposals
    python scripts/formula_ocr.py --all --out .local/formula-proposals
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"
DEFAULT_OCR = ROOT / ".local/eq-ocr.json"
DEFAULT_INVENTORY = ROOT / ".local/eq-inventory.json"

IMAGE_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\(\.\./assets/math/(?P<name>[^)]+\.png)\)(?:\{[^}]*\})?\s*$")
CAPTION_RE = re.compile(r"^\*\*(?P<alt>[^*]+)\*\*\[\]\{#(?P<anchor>eq-[0-9]{2}-[0-9]{3})\}\s*$")
ANCHOR_RE = re.compile(r"^\[\]\{#(?P<anchor>eq-[0-9]{2}-[0-9]{3})\}\s*$")
NUMBER_RE = re.compile(r"\((\d{1,2}\.\d{1,3})\)")
EQNO_RE = re.compile(r"\\eqno\s*\(([\d.]+)\)")
EQNO_BARE_RE = re.compile(r"\\eqno\s*\{?([\d.]+)\}?")
ENV_RE = re.compile(r"\\(begin|end)\{(aligned|align\*?|alignat\*?|gathered)\}")
TEXT_RE = re.compile(r"\\text(?:rm|bf|it)?\s*\{([^{}]*)\}")


def load_ocr(path: Path = DEFAULT_OCR) -> dict[str, dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["name"]: entry for entry in entries}


def load_inventory(path: Path = DEFAULT_INVENTORY) -> dict[str, dict]:
    """图片文件名 → PDF 页码与公式位置的文本层摘录，用于对照原始页面。"""
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["file"]: entry for entry in entries}


def numbers_in(text: str) -> list[str]:
    return NUMBER_RE.findall(text or "")


def find_refs(text: str) -> list[dict]:
    """按出现顺序找出章节里所有公式图引用，连同紧随其后的图注/锚点。"""
    lines = text.split("\n")
    refs = []
    for index, line in enumerate(lines):
        match = IMAGE_RE.match(line.strip())
        if not match:
            continue
        alt = match.group("alt")
        caption = ""
        anchor = ""
        for follow in range(index + 1, min(index + 4, len(lines))):
            stripped = lines[follow].strip()
            if not stripped:
                continue
            capt = CAPTION_RE.match(stripped)
            anch = ANCHOR_RE.match(stripped)
            if capt and not caption:
                caption = capt.group("alt")
                anchor = capt.group("anchor")
                continue
            if anch and not anchor:
                anchor = anch.group("anchor")
            break
        refs.append({
            "line": index + 1,
            "name": match.group("name").removesuffix(".png"),
            "alt": alt,
            "caption": caption,
            "anchor": anchor,
            "numbers_alt": numbers_in(caption or alt),
        })
    return refs


def _strip_outer_env(latex: str) -> tuple[str, list[str]]:
    warnings = []
    body = latex.strip()
    match = re.match(r"^\\begin\{(aligned|align\*?|alignat\*?|gathered)\}(.*)\\end\{\1\}$", body, re.S)
    if match:
        body = match.group(2).strip()
        if match.group(1) != "aligned":
            warnings.append("env_rewrapped:aligned")
        elif "&" in body:
            pass
    elif ENV_RE.search(body):
        # 中间夹着环境但没有整体包裹，仍按 aligned 统一
        body = re.sub(r"\\begin\{(align\*?|alignat\*?|gathered)\}", r"\\begin{aligned}", body)
        body = re.sub(r"\\end\{(align\*?|alignat\*?|gathered)\}", r"\\end{aligned}", body)
        warnings.append("env_normalised:aligned")
    return body, warnings


def normalise(latex: str) -> tuple[str, list[str], list[str]]:
    """返回 (整理后的 LaTeX, 从公式里剥出来的编号, 警告列表)。"""
    warnings: list[str] = []
    body = (latex or "").strip()
    if not body:
        return "", [], ["empty"]

    numbers = EQNO_RE.findall(body)
    body = EQNO_RE.sub("", body)
    if EQNO_BARE_RE.search(body):
        numbers += EQNO_BARE_RE.findall(body)
        body = EQNO_BARE_RE.sub("", body)
    numbers = [number.strip(".()") for number in numbers if number.strip(".()")]

    body, env_warnings = _strip_outer_env(body)
    warnings.extend(env_warnings)

    # 行内编号：`x = y,\quad(12.4).` —— 把编号摘出来，标点留在公式里
    if NUMBER_RE.search(body) and not numbers:
        numbers = NUMBER_RE.findall(body)
        body = NUMBER_RE.sub("", body)
        warnings.append("inline_number_extracted")

    # 去掉编号位置留下的悬空空白与装饰
    body = re.sub(r"\\(qquad|quad|hspace\*?\{[^}]*\})\s*$", "", body.strip())
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()
    body = re.sub(r"(\\\\)\s*$", "", body).strip()

    lines = [line.rstrip() for line in body.split("\n")]
    deduped: list[str] = []
    seen_keys: list[str] = []
    for line in lines:
        key = re.sub(r"\\+$", "", line.strip()).strip()
        if key and seen_keys and key == seen_keys[-1]:
            warnings.append("duplicate_line")
            continue
        seen_keys.append(key)
        deduped.append(line)
    body = "\n".join(deduped).strip()

    for chunk in TEXT_RE.findall(body):
        words = len(re.findall(r"[A-Za-z]{2,}", chunk))
        if words >= 4 or re.search(r"[\u4e00-\u9fff]", chunk):
            warnings.append("text_looks_like_prose")
            break

    if body.count("\\begin{") != body.count("\\end{"):
        warnings.append("unbalanced_env")
    if not numbers:
        warnings.append("no_number")
    elif len(numbers) > 1:
        warnings.append("multi_number")
    if "\n" in body and "&" not in body and "\\\\" in body:
        warnings.append("multiline_without_alignment")
    return body, numbers, warnings


def render_block(latex: str, numbers: Iterable[str]) -> str:
    labels = [f"({number})" for number in numbers]
    tail = ""
    if labels:
        tail = "\n\\qquad " + (",\\ ".join(labels))
    return f"$$\n{latex}{tail}\n$$"


def build_proposals(chapter_path: Path, ocr: dict[str, dict], inventory: dict[str, dict] | None = None) -> dict:
    text = chapter_path.read_text(encoding="utf-8")
    inventory = inventory or {}
    proposals = []
    for ref in find_refs(text):
        entry = ocr.get(ref["name"])
        located = inventory.get(ref["name"] + ".png", {})
        raw = entry["latex"] if entry else ""
        latex, numbers, warnings = normalise(raw)
        if not entry:
            warnings = ["ocr_missing"] + warnings
        elif ref["numbers_alt"] and numbers and sorted(ref["numbers_alt"]) != sorted(numbers):
            warnings.append("number_mismatch")
        elif ref["numbers_alt"] and not numbers:
            numbers = ref["numbers_alt"]
            warnings.append("number_from_caption")
        if not ref["anchor"]:
            warnings.append("anchor_missing")
        proposals.append({
            **ref,
            "numbers_ocr": numbers,
            "latex_raw": raw,
            "latex": latex,
            "block": render_block(latex, numbers) if latex else "",
            "warnings": warnings,
            "page": located.get("page"),
            "pdf_text": located.get("text", ""),
            "page_size": entry["page_size"] if entry else None,
        })
    return {
        "chapter": chapter_path.name,
        "count": len(proposals),
        "warnings": sorted({w for item in proposals for w in item["warnings"]}),
        "proposals": proposals,
    }


def chapters_with_math(book: Path = BOOK) -> list[Path]:
    return [path for path in sorted((book / "chapters").glob("*.qmd"))
            if "assets/math/" in path.read_text(encoding="utf-8")]


def render_markdown(report: dict) -> str:
    out = [f"# {report['chapter']}", "", f"公式图 {report['count']} 张；警告类型：{', '.join(report['warnings']) or '无'}", ""]
    for item in report["proposals"]:
        out.append(f"## {item['name']}（原 qmd 第 {item['line']} 行）")
        out.append("")
        out.append(f"- 锚点：`{item['anchor'] or '缺失'}`｜图注编号：{item['numbers_alt'] or '无'}｜OCR 编号：{item['numbers_ocr'] or '无'}｜PDF 页：{item['page'] or '未知'}")
        if item["warnings"]:
            out.append(f"- 警告：{', '.join(item['warnings'])}")
        out.append("")
        out.append("原始 OCR：")
        out.append("")
        out.append("```latex")
        out.append(item["latex_raw"])
        out.append("```")
        out.append("")
        out.append("建议块：")
        out.append("")
        out.append("```markdown")
        out.append(item["block"])
        out.append("")
        out.append(f"[]{item['anchor'] and '{#' + item['anchor'] + '}'}")
        out.append("```")
        out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chapter", action="append", default=None, help="章节文件名或主干名，可重复")
    parser.add_argument("--all", action="store_true", help="处理所有含公式图的章节")
    parser.add_argument("--ocr", type=Path, default=DEFAULT_OCR)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY, help="页码索引（可缺省）")
    parser.add_argument("--out", type=Path, default=None, help="把 JSON 与 Markdown 报告写到这个目录")
    args = parser.parse_args()

    ocr = load_ocr(args.ocr)
    inventory = load_inventory(args.inventory)
    targets = chapters_with_math()
    if args.chapter:
        wanted = {name.removesuffix(".qmd") for name in args.chapter}
        targets = [path for path in targets if path.stem in wanted or path.name in wanted]
        missing = wanted - {path.stem for path in targets}
        if missing:
            raise SystemExit(f"未找到章节：{', '.join(sorted(missing))}")

    summary = []
    for path in targets:
        report = build_proposals(path, ocr, inventory)
        summary.append({"chapter": report["chapter"], "count": report["count"], "warnings": report["warnings"]})
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            stem = path.stem
            (args.out / f"{stem}.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
            (args.out / f"{stem}.md").write_text(render_markdown(report), encoding="utf-8", newline="\n")
    print(json.dumps({"chapters": len(summary), "formulas": sum(item["count"] for item in summary)}, ensure_ascii=False))
    for item in summary:
        print(f"  {item['chapter']}: {item['count']} 条，警告 {', '.join(item['warnings']) or '无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
