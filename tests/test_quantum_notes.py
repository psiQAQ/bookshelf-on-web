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
        self.assertEqual(images, {"figures": 59, "tables": 18, "math": 228})
        self.assertEqual(referenced, set(self.metadata["assets"]))

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
