"""公式图 → LaTeX 的机械整理：图注解析、OCR 归一化与报警。"""
import unittest

from scripts.formula_ocr import (
    DEFAULT_OCR,
    build_proposals,
    find_refs,
    load_ocr,
    normalise,
    render_block,
    render_markdown,
)

ANCHOR_STYLE = "![公式图](../assets/math/eq-13-001.png){width=30%}\n\n[]{#eq-13-001}\n"
CAPTION_STYLE = "![公式 (13.8)(13.9)](../assets/math/eq-13-007.png){width=45%}\n\n**公式 (13.8)(13.9)**[]{#eq-13-007}\n"


class FindRefsTests(unittest.TestCase):
    def test_anchor_style_without_numbers(self):
        refs = find_refs(ANCHOR_STYLE)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["name"], "eq-13-001")
        self.assertEqual(refs[0]["anchor"], "eq-13-001")
        self.assertEqual(refs[0]["numbers_alt"], [])

    def test_caption_style_carries_numbers(self):
        refs = find_refs(CAPTION_STYLE)
        self.assertEqual(refs[0]["anchor"], "eq-13-007")
        self.assertEqual(refs[0]["numbers_alt"], ["13.8", "13.9"])
        self.assertEqual(refs[0]["caption"], "公式 (13.8)(13.9)")

    def test_line_numbers_point_at_the_image_line(self):
        refs = find_refs("正文\n\n" + ANCHOR_STYLE)
        self.assertEqual(refs[0]["line"], 3)

    def test_image_without_anchor_is_reported(self):
        refs = find_refs("![公式图](../assets/math/eq-14-001.png){width=50%}\n\n正文\n")
        self.assertEqual(refs[0]["anchor"], "")


class NormaliseTests(unittest.TestCase):
    def test_eqno_becomes_number(self):
        latex, numbers, warnings = normalise("N(\\alpha,l)=\\Big(\\int_0^\\infty r^2 dr\\Big)^{-1/2}.\\eqno(12.3)")
        self.assertNotIn("eqno", latex)
        self.assertEqual(numbers, ["12.3"])
        self.assertTrue(latex.startswith("N(\\alpha,l)="))

    def test_align_star_is_rewrapped_as_aligned(self):
        latex, numbers, warnings = normalise("\\begin{align*}\na&=b,\\quad(12.4).\\\\\nc&=d.\n\\end{align*}")
        self.assertNotIn("align*", latex)
        self.assertIn("env_rewrapped:aligned", warnings)
        self.assertEqual(numbers, ["12.4"])

    def test_duplicate_lines_are_dropped(self):
        latex, _, warnings = normalise("\\begin{aligned}\na&=b\\\\\na&=b\\\\\n\\end{aligned}")
        latex.count("a&=b")
        self.assertEqual(latex.count("a&=b"), 1)
        self.assertIn("duplicate_line", warnings)

    def test_prose_inside_text_is_flagged(self):
        _, _, warnings = normalise("x=1\\text{normalization factor for the radial part}")
        self.assertIn("text_looks_like_prose", warnings)

    def test_unbalanced_environment_is_flagged(self):
        _, _, warnings = normalise("\\begin{aligned}\na&=b")
        self.assertIn("unbalanced_env", warnings)

    def test_missing_number_is_flagged(self):
        _, numbers, warnings = normalise("a=b")
        self.assertEqual(numbers, [])
        self.assertIn("no_number", warnings)


class RenderBlockTests(unittest.TestCase):
    def test_single_number_goes_on_its_own_line(self):
        block = render_block("a=b", ["12.3"])
        self.assertEqual(block, "$$\na=b\n\\qquad (12.3)\n$$")

    def test_two_numbers_are_listed_together(self):
        self.assertTrue(render_block("a=b", ["12.1", "12.2"]).endswith("\\qquad (12.1),\\ (12.2)\n$$"))

    def test_block_without_number_has_no_qquad(self):
        self.assertNotIn("qquad", render_block("a=b", []))


class BuildProposalsTests(unittest.TestCase):
    def write(self, text):
        import tempfile
        from pathlib import Path
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "chapter.qmd"
        path.write_text(text, encoding="utf-8")
        return path

    def test_number_mismatch_between_caption_and_ocr(self):
        path = self.write(CAPTION_STYLE)
        ocr = {"eq-13-007": {"latex": "a=b\\eqno(13.7)", "page_size": [10, 10]}}
        report = build_proposals(path, ocr)
        self.assertIn("number_mismatch", report["proposals"][0]["warnings"])

    def test_caption_supplies_missing_number(self):
        path = self.write(CAPTION_STYLE)
        ocr = {"eq-13-007": {"latex": "a=b", "page_size": [10, 10]}}
        proposal = build_proposals(path, ocr)["proposals"][0]
        self.assertEqual(proposal["numbers_ocr"], ["13.8", "13.9"])
        self.assertIn("number_from_caption", proposal["warnings"])

    def test_missing_ocr_entry_is_reported(self):
        path = self.write(ANCHOR_STYLE)
        proposal = build_proposals(path, {})["proposals"][0]
        self.assertIn("ocr_missing", proposal["warnings"])
        self.assertEqual(proposal["block"], "")

    def test_missing_anchor_is_reported(self):
        path = self.write("![公式图](../assets/math/eq-14-001.png){width=50%}\n")
        proposal = build_proposals(path, {"eq-14-001": {"latex": "a=b", "page_size": [10, 10]}})["proposals"][0]
        self.assertIn("anchor_missing", proposal["warnings"])

    def test_markdown_report_keeps_anchor(self):
        path = self.write(CAPTION_STYLE)
        report = build_proposals(path, {"eq-13-007": {"latex": "a=b", "page_size": [10, 10]}})
        self.assertIn("[]{#eq-13-007}", render_markdown(report))


@unittest.skipUnless(DEFAULT_OCR.exists(), "OCR 汇总（.local/eq-ocr.json）只在本地存在")
class StockOcrTests(unittest.TestCase):
    def test_every_stored_formula_name_is_unique(self):
        entries = load_ocr()
        self.assertEqual(len(entries), len(set(entries)))
        self.assertGreaterEqual(len(entries), 222)

    def test_ocr_output_is_not_empty(self):
        empty = [name for name, entry in load_ocr().items() if not entry["latex"].strip()]
        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
