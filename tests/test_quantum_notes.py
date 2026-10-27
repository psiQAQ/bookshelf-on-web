"""Static checks for original notes; never execute embedded chapter examples."""
import json
import unittest

from scripts.publishing import ROOT, book_config, check_qmd, load_yaml
from scripts.verify_notes import examples


class QuantumNotesTests(unittest.TestCase):
    def setUp(self):
        self.book = ROOT / "books/quantum-python-notes"
        self.metadata = load_yaml(self.book / "metadata.yaml")

    def test_sixteen_ordered_chapters_and_static_guide(self):
        chapters = self.metadata["chapters"]
        self.assertEqual(chapters[0], "index.qmd")
        self.assertEqual(len(chapters), 17)
        for n, chapter in enumerate(chapters[1:], 1):
            self.assertTrue(chapter.startswith(f"chapters/{n:02d}-"))
            text = (self.book / chapter).read_text(encoding="utf-8")
            self.assertIn("{#ch%02d}" % n, text)
            self.assertIn("## 学习目标", text)
            self.assertIn("## 来源与新增内容", text)
        for chapter in chapters:
            check_qmd(self.book / chapter)

    def test_original_provenance_has_one_entry_per_document(self):
        provenance = json.loads((self.book / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["book_id"], self.metadata["id"])
        self.assertEqual([block["qmd"] for block in provenance["blocks"]], self.metadata["chapters"])
        for block in provenance["blocks"]:
            self.assertEqual(block["source"]["type"], "original")
            text = (self.book / block["qmd"]).read_text(encoding="utf-8")
            self.assertIn("{#" + block["qmd_anchor"] + "}", text)

    def test_twenty_six_examples_parse_without_execution(self):
        blocks = list(examples())
        self.assertEqual(len(blocks), 26)
        self.assertEqual(len({path for path, *_ in blocks}), 16)
        self.assertTrue(all(source.strip() for _, _, _, source in blocks))

    def test_fixed_math_scroll_style_and_disabled_execution(self):
        config = book_config(self.metadata)
        self.assertEqual(load_yaml(self.book / "_quarto.yml"), config)
        self.assertEqual(config["execute"], {"enabled": False, "eval": False})
        header = config["format"]["html"]["include-in-header"][0]["text"]
        self.assertIn('mjx-container[display="true"]', header)
        self.assertIn("overflow-x: auto", header)
        self.assertIn("max-width: 100%", header)


if __name__ == "__main__":
    unittest.main()
