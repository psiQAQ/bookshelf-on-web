"""Static checks for the translation; never execute embedded chapter examples."""
import json
import re
import unittest
from collections import Counter

from scripts.publishing import ROOT, book_config, check_qmd, explicit_anchors, load_yaml


class QuantumNotesTests(unittest.TestCase):
    def setUp(self):
        self.book = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"
        self.metadata = load_yaml(self.book / "metadata.yaml")

    def test_preface_sixteen_ordered_chapters_and_static_guide(self):
        chapters = self.metadata["chapters"]
        self.assertEqual(chapters[0], "index.qmd")
        self.assertEqual(len(chapters), 18)
        self.assertEqual(self.metadata["source"]["type"], "translation")
        self.assertRegex((self.book / chapters[0]).read_text(encoding="utf-8"), r"(?m)^# 译本说明 \{#notes-guide \.unnumbered\}$")
        for n, chapter in enumerate(chapters[1:]):
            self.assertTrue(chapter.startswith(f"chapters/{n:02d}-"))
            text = (self.book / chapter).read_text(encoding="utf-8")
            self.assertRegex(text, rf"(?m)^# .+ \{{#ch{n:02d} \.unnumbered\}}$")
        for chapter in chapters:
            check_qmd(self.book / chapter)

    def test_translation_provenance_has_one_entry_per_document(self):
        provenance = json.loads((self.book / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["book_id"], self.metadata["id"])
        self.assertEqual([block["qmd"] for block in provenance["blocks"]], self.metadata["chapters"])
        self.assertEqual(len(provenance["blocks"]), 18)
        self.assertEqual(len({block["block_id"] for block in provenance["blocks"]}), 18)
        for n, block in enumerate(provenance["blocks"]):
            self.assertEqual(block["source"]["type"], "original" if n == 0 else "translation")
            self.assertEqual(block["review_state"], "verified")
            self.assertEqual(block["qmd_anchor"], "notes-guide" if n == 0 else f"ch{n - 1:02d}")
            text = (self.book / block["qmd"]).read_text(encoding="utf-8")
            self.assertEqual(explicit_anchors(text).count(block["qmd_anchor"]), 1)

    def test_book_examples_are_static_without_execution(self):
        # The book includes REPL transcripts and non-Python listings, not just
        # standalone Python programs; validate static fences rather than parse them.
        chapters_with_code = 0
        for chapter in self.metadata["chapters"][1:]:
            path = self.book / chapter
            text = path.read_text(encoding="utf-8")
            check_qmd(path)
            blocks = re.findall(r"(?ms)^```(python|bash|text|yaml)\s*\n(.*?)^```\s*$", text)
            self.assertEqual(len(re.findall(r"(?m)^```", text)), 2 * len(blocks), chapter)
            if blocks:
                chapters_with_code += 1
                self.assertTrue(all(source.strip() for _, source in blocks), chapter)
        self.assertEqual(chapters_with_code, 16)

    def test_translation_images_and_captions(self):
        images = Counter()
        referenced = set()
        for chapter in self.metadata["chapters"][1:]:
            text = (self.book / chapter).read_text(encoding="utf-8")
            for match in re.finditer(r"!\[[^\]]*\]\(\.\./(assets/(figures|tables|math)/([^/)]+\.png))\)[^\n]*", text):
                asset, kind, filename = match.groups()
                images[kind] += 1
                self.assertNotIn(asset, referenced)
                referenced.add(asset)
                self.assertTrue((self.book / asset).is_file(), asset)
                if kind == "math":
                    # Every equation image carries a searchable anchor so a section can
                    # cite #eq-<chapter>-<number> even though the printed number lives
                    # inside the raster.
                    anchor = "eq-" + filename.removesuffix(".png").split("-", 1)[1]
                    self.assertRegex(text[match.end():], rf"^\s*(\*\*公式[^\n]*\*\*)?\[\]\{{#{re.escape(anchor)}\}}")
                else:
                    label = "图" if kind == "figures" else "表"
                    number = filename.removesuffix(".png").split("-", 1)[1].replace("-", ".")
                    self.assertRegex(text[match.end():], rf"^\s*\*\*{label} {re.escape(number)}\*\*\s*\S")
        # 228 → 222 → 0: six equations that were really prose, code fragments or the
        # Hankel matrix now live in the chapters as text / display math, and the
        # remaining 222 equation images were converted to `$$` blocks on 2026-10-28.
        self.assertEqual(images, {"figures": 59, "tables": 18})
        self.assertEqual(referenced, set(self.metadata["assets"]))
        for chapter in self.metadata["chapters"][1:]:
            text = (self.book / chapter).read_text(encoding="utf-8")
            self.assertNotIn("assets/math/", text, chapter)
        self.assertFalse([asset for asset in self.metadata["assets"] if "/math/" in asset])

    def test_equations_are_display_math_with_anchors(self):
        """222 张公式图现在都是 `$$` 块：锚点在，编号对，不再有 `\\eqno` 或图片。"""
        anchors = set()
        blocks = 0
        for chapter in self.metadata["chapters"][1:]:
            text = (self.book / chapter).read_text(encoding="utf-8")
            self.assertNotIn("![公式", text, chapter)
            self.assertNotIn("\\eqno", text, chapter)
            blocks += len(re.findall(r"\$\$\n.*?\n\$\$", text, re.S))
            anchors.update(re.findall(r"\[\]\{#(eq-\d\d-\d+)\}", text))
        # 三处公式在转换时并块或排除：eq-02-007/008 合为一个块、eq-12-042/043 是同一条公式、
        # eq-13-042 实为正文截图（只保留锚点），222 张图对应 219 个展示块；另有 (12.32) 原本只剩文本层残片、补成展示块；(13.20)、(16.24)、(16.25) 三式在提取时整块丢失、只剩压平的正文行，补回后共 222 个展示块。锚点始终是 223 个（补回的三式在原书里没有对应截图）。
        self.assertEqual(blocks, 222)
        self.assertEqual(len(anchors), 223)

    def test_fixed_math_scroll_style_and_disabled_execution(self):
        config = book_config(self.metadata)
        self.assertEqual(load_yaml(self.book / "_quarto.yml"), config)
        self.assertEqual(config["execute"], {"enabled": False, "eval": False})
        header = config["format"]["html"]["include-in-header"][0]["text"]
        self.assertIn('mjx-container[display="true"]', header)
        self.assertIn("overflow-x: auto", header)
        self.assertIn("max-width: 100%", header)
        self.assertIn(".ref-list p", header)
        self.assertIn("text-indent", header)


if __name__ == "__main__":
    unittest.main()
