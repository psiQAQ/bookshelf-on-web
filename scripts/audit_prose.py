"""把「疑似代码行没进代码块」「代码块里其实是正文」「正文裸 URL」挑出来。

只管机械可判定的事，不做语义判断：命中的行需要人来判断是代码、正文还是公式残片。
口径写在 docs/VERIFICATION.md 的「疑似代码行与正文裸 URL 的机械审计」一节。

用法：
    python scripts/audit_prose.py                      # 打印报告摘要
    python scripts/audit_prose.py --report reports/prose-audit.json
    python scripts/audit_prose.py --check              # 有命中时退出 1
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"
SCHEMA = 1

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# URL 在中文与全角标点处截断，避免把后续正文吞进链接
URL_RE = re.compile(r"https?://\s?[^\s\u4e00-\u9fff（）［］｛｝「」『』【】《》〈〉，。、；：！？…]+")
URL_TRAILING = ".,;:!?)]}'\""
LETTERS_RE = re.compile(r"[A-Za-z]")
# 公式残片里的数学符号：命中就跳过，避免把排版拆散的公式当成代码
MATH_RE = re.compile(r"[−∑∫√≈≤≥±×·∂ψρφθσπλ∞→←⇐⇒∈∉⊂⊃⊗⊕ℏ∇†‡∥∣⟨⟩⌈⌉⌊⌋¯]")
# 代码里常见的字符，用来区分「代码行」与「英文散文」
CODE_CHARS_RE = re.compile(r"[=()\[\]{}<>_/\\@$%#*|]")

# 一眼可判定为正常正文/结构的行，不进入疑似清单
SKIP_LINE_RE = (
    re.compile(r"^#"),                       # 标题
    re.compile(r"^!\["),                     # 图片
    re.compile(r"^\[\]\{"),                  # 图注锚点
    re.compile(r"^\*\*(图|表|公式)"),         # 图表题注
    re.compile(r"^\|"),                      # 表格行
    re.compile(r"^[-*]\s+`[^`]+`$"),         # 只有行内代码的项目符号
    re.compile(r"^`[^`]+`$"),                 # 整行行内代码
    re.compile(r"^\[[0-9]+\]"),              # 参考文献条目
    re.compile(r"^:::"),                     # 围栏标记
    re.compile(r"^---+\s*$"),                # 分隔线
    re.compile(r"^\{"),                      # pandoc 属性块
    re.compile(r"^\$"),                      # 独立公式
)

# 「公式转 LaTeX 后残留的压平副本」：公式本体已在上方的 $$ 块里，正文却还留着一份
# 文本层压平的字形串。整行含 `. )` / `,)` 这类 LaTeX 句读、或「权函数为」后面不是
# 行内公式、或一行里堆着多个数学符号又带等号，都按残片处理。
# 白名单是「形状相同但本身合法」的行内记号（元组、坐标、代码引用），先摘掉再判。
FORMULA_REMNANT_WHITELIST = (
    re.compile(r"\(itemsize \* \(n\+1\),\)"),          # 步长元组 (itemsize * (n+1),)
    re.compile(r"\(0\., 0\., 0\.\)"),                    # 坐标 (0., 0., 0.)
    re.compile(r"\(\{vrr\(\.\.\.\)\}\)"),                # f-string 改写示例 ({vrr(...)})
    re.compile(r"\{vrr\(\.\.\.\)\}"),                    # 同上，去掉外层括号的写法
    re.compile(r"vrr\(\.\.\.\)"),                         # 正文里引用函数调用 vrr(...)
    re.compile(r"\(slice\(None\),\)\*axis \+ \(0,0\)"),     # 索引等价写法
    re.compile(r"`P \(x\) = x exp\(− ax\)\.\)`"),         # 前言里明说「照原样保留」的样例
)
FORMULA_REMNANT_PUNCT = re.compile(r"\.\)|,\)")
# 「权函数为」与「权函数是」是同一自然句的两种写法，PDF 提取两种都会留下压平串（`权函数是 e`）
WEIGHT_FUNCTION_RE = re.compile(r"权函数(为|是)(?!\s*[\$`])")
# 句首残留的公式编号：`(12.62) 为了与……` —— 公式本体已在 $$ 块里，这里的编号是文本层遗留
EQUATION_NUMBER_RE = re.compile(r"^\(\d+\.\d+\)")
FORMULA_REMNANT_SYMBOLS = "∑∇√∫∂"

# 链接被 PDF 换行切断：`[arrow](https://arrow). apache.org/cookbook/...`。
# 目标地址只到 `https://arrow`，`. apache.org/...` 退化成裸文本，点进去是死链。
SPLIT_LINK_RE = re.compile(
    r"\]\((?P<url>[^)\s]+)\)\.?\s+"
    r"(?P<tail>(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}|[A-Za-z]{2,}/)"
)

CODE_PATTERNS = (
    (re.compile(r"^\s{2,}\S"), "缩进开头"),
    (re.compile(r"\b(def|class|import|from|return|yield|lambda|assert|raise|global|nonlocal)\b\s*[(\w]"), "Python 关键字"),
    (re.compile(r"\b(print|len|range|open|list|dict|set|str|int|float)\s*\("), "内置函数调用"),
    (re.compile(r"^[A-Za-z_][\w.\[\]'\"]*\s*(=|\+=|-=|\*=|/=|//=|%=)\s*\S"), "赋值语句"),
    (re.compile(r"^[A-Za-z_][\w.]*\(.*\)\s*[:;]?$"), "函数调用行"),
    (re.compile(r"(\+\+|->|<>|!=)"), "运算符"),
    (re.compile(r"%[0-9.\-]*[dfs]"), "格式化占位符"),
    (re.compile(r"^\s*[)\]}]"), "以闭括号开头"),
)


def iter_lines(path: Path):
    """产出 (行号, 原文, 是否在代码围栏内, 是否在公式块内, 是否在参考文献区内)。"""
    text = path.read_text(encoding="utf-8")
    in_code = in_math = in_ref = False
    for number, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            yield number, line, in_code, in_math, in_ref
            continue
        if stripped.startswith("$$"):
            in_math = not in_math
        elif not in_code and stripped.startswith("::: {.ref-list}"):
            in_ref = True
        elif in_ref and stripped == ":::":
            in_ref = False
        yield number, line, in_code, in_math, in_ref


def link_target_spans(line: str):
    """返回 markdown 链接目标 `](url)` 的字符区间，用于排除已建好的超链接。"""
    spans = []
    for match in re.finditer(r"\]\(([^)]+)\)", line):
        spans.append((match.start(1), match.end(1)))
    return spans


def find_bare_urls(path: Path):
    found = []
    for number, line, in_code, in_math, in_ref in iter_lines(path):
        if in_code or in_math:
            continue
        spans = link_target_spans(line)
        for match in URL_RE.finditer(line):
            if any(start <= match.start() < end for start, end in spans):
                continue
            found.append({
                "file": path.name,
                "line": number,
                "text": line.strip(),
                "url": match.group(0).rstrip(URL_TRAILING),
                "reason": "bare_url",
            })
    return found


def find_suspect_code(path: Path):
    found = []
    for number, line, in_code, in_math, in_ref in iter_lines(path):
        if in_code or in_math or in_ref:
            continue
        stripped = line.strip()
        if not stripped or (SUSPECT_CODE_SKIPS_CJK and CJK_RE.search(stripped)):
            continue
        if any(pattern.search(stripped) for pattern in SKIP_LINE_RE):
            continue
        if MATH_RE.search(stripped) or "`" in stripped:
            continue
        for pattern, reason in CODE_PATTERNS:
            if pattern.search(stripped):
                found.append({
                    "file": path.name,
                    "line": number,
                    "text": stripped,
                    "url": "",
                    "reason": f"suspect_code:{reason}",
                })
                break
    return found


def find_formula_remnant(path: Path):
    """正文里残留的「压平公式副本」：公式已排成 $$ 块，这里又留了一份文本层字形串。"""
    found = []
    for number, line, in_code, in_math, in_ref in iter_lines(path):
        if in_code or in_math or in_ref:
            continue
        stripped = line.strip()
        if not stripped or "$" in line or "`" in stripped:
            continue
        if any(pattern.search(stripped) for pattern in SKIP_LINE_RE):
            continue
        residue = stripped
        for pattern in FORMULA_REMNANT_WHITELIST:
            residue = pattern.sub("", residue)
        if FORMULA_REMNANT_PUNCT.search(residue):
            reason = "formula_remnant:punctuation"
        elif EQUATION_NUMBER_RE.match(residue):
            reason = "formula_remnant:equation_number"
        elif WEIGHT_FUNCTION_RE.search(residue):
            reason = "formula_remnant:weight_function"
        elif sum(residue.count(symbol) for symbol in FORMULA_REMNANT_SYMBOLS) >= 2 and "=" in residue:
            reason = "formula_remnant:operators"
        else:
            continue
        found.append({
            "file": path.name,
            "line": number,
            "text": stripped,
            "url": "",
            "reason": reason,
        })
    return found


def find_broken_links(path: Path):
    """链接目标被 PDF 换行切断，后半截退化成裸文本（读者点进去是死链）。

    参考文献区（`in_ref`）在这里**不豁免**：断链在 ref-list 里最集中，其它探测器跳过
    那一区是为了不误伤英文条目，但「`](url).` 后面紧跟裸域名」没有别的解释。
    """
    found = []
    for number, line, in_code, in_math, in_ref in iter_lines(path):
        if in_code or in_math or "](" not in line:
            continue
        for match in SPLIT_LINK_RE.finditer(line):
            found.append({
                "file": path.name,
                "line": number,
                "text": line.strip(),
                "url": match.group("url"),
                "reason": f"broken_link:{match.group('tail')}",
            })
    return found


def find_prose_in_fence(path: Path):
    """代码围栏里出现整句中文或长段英文，通常是正文/表格碎片被误当成代码。"""
    found = []
    in_code = False
    in_math = False
    for number, line, flag, in_math, _ in iter_lines(path):
        if flag != in_code:  # 围栏开/关那一行
            in_code = flag
            continue
        if not in_code or in_math:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        cjk = len(CJK_RE.findall(stripped))
        letters = len(LETTERS_RE.findall(stripped))
        if cjk >= 6:
            reason = "prose_in_fence:cjk"
        elif cjk == 0 and letters >= 30 and not CODE_CHARS_RE.search(stripped) and len(stripped.split()) >= 4:
            reason = "prose_in_fence:english"
        else:
            continue
        found.append({
            "file": path.name,
            "line": number,
            "text": stripped,
            "url": "",
            "reason": reason,
        })
    return found


def find_english_residue(path: Path):
    """正文里成段的英文句子（没有中文、也没有代码字符），多半是漏译。"""
    found = []
    for number, line, in_code, in_math, in_ref in iter_lines(path):
        if in_code or in_math or in_ref:
            continue
        stripped = line.strip()
        if not stripped or CJK_RE.search(stripped):
            continue
        if any(pattern.search(stripped) for pattern in SKIP_LINE_RE):
            continue
        letters = len(LETTERS_RE.findall(stripped))
        if letters < 30 or CODE_CHARS_RE.search(stripped) or "`" in stripped:
            continue
        if MATH_RE.search(stripped) or len(stripped.split()) < 4:
            continue
        found.append({
            "file": path.name,
            "line": number,
            "text": stripped,
            "url": "",
            "reason": "english_residue",
        })
    return found


# 这三类一旦非空就是缺陷，`--check` 会因此失败；`prose_in_fence` 混有合法文档字符串与
# 报错信息，只作为待人工甄别的清单，不参与 `--check`。
STRICT_DETECTORS = ("bare_urls", "suspect_code", "english_residue", "formula_remnant", "broken_links")

# `find_suspect_code` 的显式口径：只看整行没有中文的行。
# 带中文的行里夹着代码片段时，机械判据的误报率过高（`C/C++` 会命中 `++` 运算符、
# `open()`、`plt.show()` 这类正文里顺口提到的函数名会命中「函数调用行」），所以这一子集
# 不在 suspect_code 的口径内；「中文 + 被压平的公式/代码残片」改由 `find_formula_remnant`
# 与人工复核兜底。若要扩到这里，必须先把中文骨架之外的 ASCII 片段切出来再比对代码特征。
SUSPECT_CODE_SKIPS_CJK = True

DETECTORS = (
    ("bare_urls", find_bare_urls),
    ("suspect_code", find_suspect_code),
    ("prose_in_fence", find_prose_in_fence),
    ("english_residue", find_english_residue),
    ("formula_remnant", find_formula_remnant),
    ("broken_links", find_broken_links),
)


def audit_chapter(path: Path) -> dict:
    result = {}
    for key, detector in DETECTORS:
        hits = detector(path)
        for hit in hits:
            hit["chapter"] = path.name
        result[key] = hits
    return result


def audit_book(book: Path = BOOK) -> dict:
    report = {"schema": SCHEMA, "book": book.name, "chapters": 0}
    totals = {key: 0 for key, _ in DETECTORS}
    findings = {key: [] for key, _ in DETECTORS}
    chapters = sorted((book / "chapters").glob("*.qmd"))
    for path in chapters:
        chapter = audit_chapter(path)
        for key in findings:
            findings[key].extend(chapter[key])
            totals[key] += len(chapter[key])
    report["chapters"] = len(chapters)
    report["totals"] = totals
    for key, _ in DETECTORS:
        findings[key].sort(key=lambda hit: (hit["file"], hit["line"]))
        report[key] = findings[key]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, default=None, help="把 JSON 报告写到这个路径")
    parser.add_argument(
        "--check",
        action="store_true",
        help="严格项（裸 URL、疑似代码行、英文残留、公式残片）有命中时退出 1",
    )
    parser.add_argument("--check-all", action="store_true", help="任何探测器有命中时退出 1")
    args = parser.parse_args()

    report = audit_book()
    payload = json.dumps(report, ensure_ascii=False, indent=1)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8", newline="\n")
        print(f"report: {args.report}")
    print(json.dumps({"chapters": report["chapters"], **report["totals"]}, ensure_ascii=False))
    if args.check and any(report["totals"][key] for key in STRICT_DETECTORS):
        return 1
    if args.check_all and any(report["totals"].values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
