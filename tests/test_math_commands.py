"""`scripts/check_math.py` 的回归测试。

重点是「门禁不许空转」：拿真实出现过的残形（`\\inom`、被吃掉转义的 TAB、`\\begin`
没有配对）喂给探测器，必须都能抓到；同时要求当前仓库的十九章都是干净的。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_math  # noqa: E402


class AllowlistTests(unittest.TestCase):
    def test_allowlist_is_sorted_and_unique(self) -> None:
        entries = [
            line.strip()
            for line in check_math.ALLOWLIST.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(entries, sorted(entries))
        self.assertEqual(len(entries), len(set(entries)))

    def test_allowlist_entries_carry_no_backslash(self) -> None:
        for name in check_math.load_allowlist():
            self.assertNotIn("\\", name)

    def test_allowlist_covers_every_command_in_use(self) -> None:
        # 白名单就是全书命令词表：仓库里出现未知命令时这条会失败，迫使留下审阅痕迹。
        self.assertEqual(check_math.audit(), [])


class DetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.chapter = self.root / "books" / "demo" / "chapters" / "01-demo.qmd"

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def write(self, body: str) -> list[check_math.Finding]:
        self.chapter.parent.mkdir(parents=True, exist_ok=True)
        self.chapter.write_text(body, encoding="utf-8", newline="\n")
        return check_math.audit(self.root)

    def test_unknown_command_is_reported(self) -> None:
        findings = self.write("规模均为 $\\inom{14}{7}^{2} \\times 142$。\n")
        self.assertEqual([f.kind for f in findings], ["unknown_command"])
        self.assertEqual(findings[0].detail, "\\inom")

    def test_known_commands_pass(self) -> None:
        self.assertEqual(self.write("规模均为 $\\binom{14}{7}^{2} \\times 142$。\n"), [])

    def test_double_backslash_is_a_linebreak_not_a_command(self) -> None:
        body = "$$\n\\begin{pmatrix} c_1 \\\\ c_2 \\end{pmatrix}\n$$\n"
        self.assertEqual(self.write(body), [])

    def test_control_character_in_math_is_reported(self) -> None:
        findings = self.write("规模为 $\\binom{14}{7}^{2} \times 142$。\n")
        # TAB/BEL/BS/VT/FF 都是写文件时转义被吃掉的痕迹
        self.assertEqual([f.kind for f in findings], ["control_char"])
        self.assertEqual(findings[0].detail, "TAB")

    def test_control_character_outside_math_is_reported(self) -> None:
        findings = self.write("正文里混进了制表符\t的地方。\n")
        self.assertEqual([f.kind for f in findings], ["control_char"])

    def test_unbalanced_environment_is_reported(self) -> None:
        findings = self.write("$$\n\\begin{aligned}\na &= b\n$$\n")
        self.assertEqual([f.kind for f in findings], ["env_unbalanced"])
        self.assertTrue(findings[0].detail.startswith("aligned:"))

    def test_stray_escape_in_prose_is_reported(self) -> None:
        findings = self.write("造成歧义。\\n这引出了一个相关问题：\n")
        self.assertEqual([f.kind for f in findings], ["stray_escape"])

    def test_code_fences_are_ignored(self) -> None:
        body = "```python\nprint(r'\\n')\n```\n\n正文正常。\n"
        self.assertEqual(self.write(body), [])

    def test_escaped_dollar_is_not_a_math_span(self) -> None:
        self.assertEqual(self.write("价格是 5 \\$，不是公式。\n"), [])


class RepositoryTests(unittest.TestCase):
    def test_chapters_are_scanned(self) -> None:
        names = {path.name for path in check_math.chapters(ROOT)}
        self.assertIn("14-fci.qmd", names)
        self.assertIn("12-integrals.qmd", names)

    def test_main_exits_zero_when_clean(self) -> None:
        self.assertEqual(check_math.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
