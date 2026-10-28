"""Guards against list markup that renders as empty or truncated bullets.

The PDF text layer merges some runs (monospace identifiers, small bold lead-ins)
into a single line record, which drops them from the flow. When that happens the
translated chapter keeps the bullet marker but loses its content, so the site
shows empty items or a sentence that stops mid-way. These checks fail if such a
hole is reintroduced.
"""

import re
import unittest

from scripts.publishing import ROOT, load_yaml

BOOK = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"
EMPTY_ITEM = re.compile(r"^\s{0,6}[-*+]\s*$")
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

    def test_no_fence_gap_splitting_a_block(self):
        """一个代码块的闭合围栏后紧跟空行与新围栏（上一行以冒号结尾、下一段继续缩进）说明被切成两块。"""
        offenders = []
        for chapter in self.chapters:
            lines = self.read(chapter)
            for index, line in enumerate(lines):
                if line.strip() != "```":
                    continue
                previous = next((l.rstrip() for l in reversed(lines[:index]) if l.strip()), "")
                probe = index + 1
                blanks = 0
                while probe < len(lines) and not lines[probe].strip():
                    blanks += 1
                    probe += 1
                if probe >= len(lines) or not lines[probe].strip().startswith("```"):
                    continue
                if blanks > 2:
                    continue
                following = lines[probe + 1] if probe + 1 < len(lines) else ""
                if not previous.endswith(":"):
                    continue
                indent = len(following) - len(following.lstrip())
                if indent >= 8 or following.startswith(("return", ")", "]", "...")):
                    offenders.append(f"{chapter}:{index + 1}")
        self.assertEqual(offenders, [], "code block split by a blank line")
if __name__ == "__main__":
    unittest.main()
