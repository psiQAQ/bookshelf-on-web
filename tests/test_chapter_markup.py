"""Guards against list markup that renders as empty or truncated bullets.

The PDF text layer merges some runs (monospace identifiers, small bold lead-ins)
into a single line record, which drops them from the flow. When that happens the
translated chapter keeps the bullet marker but loses its content, so the site
shows empty items or a sentence that stops mid-way. These checks fail if such a
hole is reintroduced.
"""

import ast
import re
import unittest

from scripts.publishing import ROOT, load_yaml

BOOK = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"
EMPTY_ITEM = re.compile(r"^\s{0,6}[-*+]\s*$")
OUTPUT_MARKER = re.compile(r"^(In \[|Out\[|CPU times|Wall time|Wall clock|%\d|\d+(\.\d+)? seconds)")
DANGLING_TAIL = re.compile(r"^\s{0,6}[-*+]\s+.*(?:例如|包括|如下|分别|由)\s*[-–—]\s*$")


class ChapterMarkupTests(unittest.TestCase):
    def setUp(self):
        self.chapters = load_yaml(BOOK / "metadata.yaml")["chapters"]

    def read(self, chapter):
        return (BOOK / chapter).read_text(encoding="utf-8").split("\n")

    def test_no_empty_list_items(self):
        offenders = []
        for chapter in self.chapters:
            for number, line in enumerate(self.read(chapter), 1):
                if EMPTY_ITEM.match(line):
                    offenders.append(f"{chapter}:{number}")
        self.assertEqual(offenders, [], "empty list items would render as bare bullets")

    def test_no_list_items_without_content_after_lead_in(self):
        offenders = []
        for chapter in self.chapters:
            for number, line in enumerate(self.read(chapter), 1):
                if DANGLING_TAIL.match(line):
                    offenders.append(f"{chapter}:{number}:{line.strip()}")
        self.assertEqual(offenders, [], "list items ending in a dangling dash")

    def test_lead_in_lists_are_followed_by_nested_items(self):
        offenders = []
        for chapter in self.chapters:
            lines = self.read(chapter)
            for index, line in enumerate(lines):
                stripped = line.strip()
                if not re.match(r"^\s{0,6}[-*+]\s+", line):
                    continue
                if not re.search(r"(例如|包括|如下)：$", stripped):
                    continue
                nxt = next(
                    (candidate for candidate in lines[index + 1 :] if candidate.strip()),
                    "",
                )
                is_matrix = nxt.lstrip().startswith(("```", "![ ", "![", "$$", "|"))
                is_list = re.match(r"^\s*[-*+]\s+\S", nxt) is not None
                if not (is_matrix or is_list):
                    offenders.append(f"{chapter}:{index + 1}:{stripped[-30:]}")
        self.assertEqual(offenders, [], "lead-in bullet without a nested list")


    def test_no_stray_formula_fragments(self):
        """公式图片/文本层留下的残片不能再漏进正文（如 `− θij X`、孤立的 `∑`）。"""
        cjk = re.compile(r"[一-鿿]")
        offenders = []
        for chapter in self.chapters:
            in_fence = in_math = False
            for number, line in enumerate(self.read(chapter), 1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_fence = not in_fence
                    continue
                if stripped == "$$":
                    in_math = not in_math
                    continue
                if in_fence or in_math or not stripped or stripped == ":::":
                    continue
                if stripped.startswith(("![", "**", "|", "-", ">", "#", "[]", ":::")):
                    continue
                if len(stripped) <= 14 and not cjk.search(stripped):
                    offenders.append(f"{chapter}:{number}:{stripped}")
        self.assertEqual(offenders, [], "stray fragment lines left in prose")

    def test_no_control_characters(self):
        """文本层提取出的 NUL/退格等控制字符会破坏渲染，必须写成 `\0` 这样的字面量。"""
        offenders = []
        for chapter in self.chapters:
            text = (BOOK / chapter).read_text(encoding="utf-8")
            for index, character in enumerate(text):
                code = ord(character)
                if code < 32 and chr(code) not in (chr(10), chr(9)):
                    line = text.count(chr(10), 0, index) + 1
                    offenders.append(f"{chapter}:{line}:U+{code:04X}")
        self.assertEqual(offenders, [], "control characters in chapter sources")

    def test_no_code_fence_split_in_two(self):
        """两块代码紧挨着出现（``` 后紧跟 ```python）说明一个代码块被空行切断了。"""
        offenders = []
        for chapter in self.chapters:
            lines = self.read(chapter)
            for index, line in enumerate(lines[:-1]):
                if line.strip() == "```" and lines[index + 1].strip().startswith("```"):
                    offenders.append(f"{chapter}:{index + 1}")
        self.assertEqual(offenders, [], "code block split by a blank line")

    def test_no_code_block_split_by_a_blank_line(self):
        """闭合围栏与下一个开围栏之间只有空行，且内容明显是同一段代码时，说明被切断。"""
        offenders = []
        for chapter in self.chapters:
            lines = self.read(chapter)
            fences = [index for index, line in enumerate(lines) if line.strip().startswith("```")]
            for position in range(0, len(fences) - 3, 2):
                close, reopen = fences[position + 1], fences[position + 2]
                gap = lines[close + 1:reopen]
                if any(line.strip() for line in gap) or len(gap) > 2:
                    continue
                last = next((line.rstrip() for line in reversed(lines[fences[position]:close]) if line.strip()), "")
                first = lines[reopen + 1] if reopen + 1 < len(lines) else ""
                if OUTPUT_MARKER.match(first.strip()):
                    continue  # REPL 提示或计时输出是独立的输出块
                unbalanced = sum(last.count(c) for c in "([{") > sum(last.count(c) for c in ")]}")
                tail = last[-1] in ",+*-/=&|(" if last else False
                continues = (
                    last.endswith(":")
                    or unbalanced
                    or tail
                    or first.strip()[:1] in (")", "]", "}")
                    or last[:1] == " "
                    or (first[:1] == " " and bool(first.strip()))
                )
                if continues:
                    offenders.append(f"{chapter}:{close + 1}")
        self.assertEqual(offenders, [], "code block split by a blank line")
    def test_text_fences_carry_no_python_code(self):
        """标成 text 的围栏里若是可解析的 Python 语句，就是语言标记错了（§3.4.3 的同类问题）。"""
        offenders = []
        for chapter in self.chapters:
            lines = self.read(chapter)
            index = 0
            while index < len(lines):
                line = lines[index]
                if line.strip() != "```text":
                    index += 1
                    continue
                close = index + 1
                while close < len(lines) and lines[close].strip() != "```":
                    close += 1
                body = lines[index + 1:close]
                if not any(re.match(r"^\s*\[[\w.\-]+\]\s*$", item) for item in body):
                    try:
                        tree = ast.parse(chr(10).join(body))
                    except SyntaxError:
                        tree = None
                    if tree is not None and any(
                        isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.If,
                                          ast.With, ast.Assign, ast.Import, ast.ImportFrom, ast.Return,
                                          ast.AugAssign, ast.Try))
                        for node in tree.body
                    ):
                        offenders.append(f"{chapter}:{index + 1}")
                index = close + 1
        self.assertEqual(offenders, [], "python code marked as text")

if __name__ == "__main__":
    unittest.main()
