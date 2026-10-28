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


if __name__ == "__main__":
    unittest.main()
