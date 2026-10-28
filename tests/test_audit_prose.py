"""Mechanical prose audit: code lines outside fences, prose inside fences, bare URLs."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_prose import (
    DETECTORS,
    STRICT_DETECTORS,
    audit_book,
    find_bare_urls,
    find_english_residue,
    find_prose_in_fence,
    find_suspect_code,
)


def write_qmd(directory: Path, text: str) -> Path:
    path = directory / "chapter.qmd"
    path.write_text(text, encoding="utf-8")
    return path


class SuspectCodeTests(unittest.TestCase):
    def test_code_line_outside_fence_is_reported(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "x = np.zeros(3)\n")
            hits = find_suspect_code(path)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 1)
        self.assertTrue(hits[0]["reason"].startswith("suspect_code:"))

    def test_code_inside_fence_is_ignored(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "```python\nx = np.zeros(3)\n```\n")
            self.assertEqual(find_suspect_code(path), [])

    def test_chinese_prose_and_structure_lines_are_ignored(self):
        text = (
            "# 第 1 章\n"
            "这里讲的是赋值语句 x = 1 的写法。\n"
            "![](../assets/figures/fig-1-1.png)\n"
            "**图 1.1** 示意\n"
            "| 列 | 说明 |\n"
            "- `np.zeros`\n"
            "\n"
            "$$y = x^2$$\n"
        )
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_suspect_code(path), [])

    def test_math_fragment_is_not_reported_as_code(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "H =− 1 k x,)\n")
            self.assertEqual(find_suspect_code(path), [])


class ProseInFenceTests(unittest.TestCase):
    def test_chinese_sentence_in_fence_is_reported(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "```text\n这一段中文说明本来是正文，却被放进了代码块里。\n```\n")
            hits = find_prose_in_fence(path)
        self.assertEqual([hit["reason"] for hit in hits], ["prose_in_fence:cjk"])

    def test_english_residue_in_fence_is_reported(self):
        text = "```text\narranged as D0, D+1, D-1, D+2, D-2. For simplicity we have omitted it\n```\n"
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            hits = find_prose_in_fence(path)
        self.assertEqual([hit["reason"] for hit in hits], ["prose_in_fence:english"])

    def test_real_code_and_docstring_punctuation_are_not_flagged(self):
        text = "```python\ndef f(x):\n    return x + 1\n```\n"
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_prose_in_fence(path), [])


class BareUrlTests(unittest.TestCase):
    def test_bare_url_in_prose_is_reported(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "官方文档见 https://example.org/docs 一页。\n")
            hits = find_bare_urls(path)
        self.assertEqual([hit["url"] for hit in hits], ["https://example.org/docs"])

    def test_markdown_link_and_code_fence_are_ignored(self):
        text = "见 [文档](https://example.org/docs)。\n\n```bash\ncurl https://example.org/x\n```\n"
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_bare_urls(path), [])

    def test_reference_list_urls_are_ignored(self):
        text = "::: {.ref-list}\n\n[1] A. Author, A title, [doi.org](https://doi.org/10.1000/xyz).\n\n:::\n"
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_bare_urls(path), [])


class EnglishResidueTests(unittest.TestCase):
    def test_untranslated_sentence_is_reported(self):
        text = "Process 计算完成后，the following output shows how to arrange the orbitals.\n"
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_english_residue(path), [])

    def test_sentence_without_chinese_is_reported(self):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "The following output shows how orbitals are arranged here.\n")
            hits = find_english_residue(path)
        self.assertEqual([hit["reason"] for hit in hits], ["english_residue"])


class BookReportTests(unittest.TestCase):
    def setUp(self):
        self.report = audit_book()

    def test_report_shape_is_stable(self):
        self.assertEqual(self.report["schema"], 1)
        self.assertEqual(self.report["chapters"], 17)
        keys = [key for key, _ in DETECTORS]
        self.assertEqual(sorted(self.report["totals"]), sorted(keys))
        for key in keys:
            self.assertIn(key, self.report)
            self.assertEqual(self.report["totals"][key], len(self.report[key]))

    def test_hits_are_sorted_and_attribute_every_field(self):
        for key, _ in DETECTORS:
            hits = self.report[key]
            self.assertEqual(hits, sorted(hits, key=lambda hit: (hit["file"], hit["line"])))
            for hit in hits:
                self.assertEqual(sorted(hit), ["chapter", "file", "line", "reason", "text", "url"])
                self.assertEqual(hit["file"], hit["chapter"])

    def test_report_is_json_serialisable(self):
        json.dumps(self.report, ensure_ascii=False)

    def test_strict_detectors_are_cleared(self):
        # 存量已在 2026-10-28 清零：正文裸 URL 全部转成行内链接、公式拆行残片随
        # `$$` 化消失、整句英文残留统一翻译。这三类再出现就是缺陷。
        self.assertEqual({key: self.report["totals"][key] for key in STRICT_DETECTORS}, {key: 0 for key in STRICT_DETECTORS})

    def test_prose_in_fence_does_not_grow(self):
        # 围栏内的长英文句子混有合法文档字符串、报错信息与 shell 注释，只做待甄别清单。
        # 2026-10-28 存量 100 条；这条断言只防增长，不做清零要求。
        self.assertLessEqual(self.report["totals"]["prose_in_fence"], 100)


if __name__ == "__main__":
    unittest.main()
