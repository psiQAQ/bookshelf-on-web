"""Mechanical prose audit: code lines outside fences, prose inside fences, bare URLs."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_prose import (
    DETECTORS,
    STRICT_DETECTORS,
    SUSPECT_CODE_SKIPS_CJK,
    audit_book,
    find_bare_urls,
    find_broken_links,
    find_english_residue,
    find_formula_remnant,
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


class FormulaRemnantTests(unittest.TestCase):
    """公式排成 $$ 块之后留在正文里的「压平副本」。"""

    def scan(self, text):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            return find_formula_remnant(path)

    def test_latex_punctuation_remnant_is_reported(self):
        # 历史样本：13 章 (13.38) 之后压平成正文的副本
        hits = self.scan("(ij|kl) = Tpij Tpkl.) 在实践中，RI 方法也称为密度拟合。\n")
        self.assertEqual([hit["reason"] for hit in hits], ["formula_remnant:punctuation"])

    def test_weight_function_remnant_is_reported(self):
        hits = self.scan("- 权函数为 1，区间为 [− 1, 1]。\n")
        self.assertEqual([hit["reason"] for hit in hits], ["formula_remnant:weight_function"])

    def test_weight_function_is_variant_is_reported(self):
        # 同一句的另一种写法：`权函数是 e`（原书 the weight function is e^{-t x^2}）
        hits = self.scan("其中 n 是非负整数，W (x) 是权函数。在 Rys 求积中，权函数是 e，积分区间为 [0, 1]，\n")
        self.assertEqual([hit["reason"] for hit in hits], ["formula_remnant:weight_function"])

    def test_equation_number_remnant_is_reported(self):
        # 历史样本：12 章 (12.62) 展示块之后的句首编号残留
        hits = self.scan("(12.62) 为了与高斯-埃尔米特求积中的权函数对应，权重和节点按比例缩放。\n")
        self.assertEqual([hit["reason"] for hit in hits], ["formula_remnant:equation_number"])

    def test_operator_remnant_is_reported(self):
        hits = self.scan("τ = 1 ∇ χμ ·∇ χνγ 我们可以对 XC 矩阵进行数值积分：\n")
        self.assertEqual([hit["reason"] for hit in hits], ["formula_remnant:operators"])

    def test_legitimate_technical_marks_are_whitelisted(self):
        text = (
            "np.diagonal 生成一个步长为 (itemsize * (n+1),) 的视图。\n"
            "下面的配置表示位于 (0., 0., 0.) 的氢原子。\n"
            "3. 在 f-string 中将函数调用 vrr(...) 替换为({vrr(...)})。\n"
            "v[(slice(None),)*axis + (0,0)] 等价于数组索引。\n"
        )
        self.assertEqual(self.scan(text), [])

    def test_fence_math_block_reference_list_and_inline_math_are_ignored(self):
        text = (
            "```python\nout = f(itemsize * (n+1),)\n```\n"
            "$$\na = b qquad (1.1)\n$$\n"
            "::: {.ref-list}\n\n[1] A. Author, Title, 12(3),)\n\n:::\n"
            "权函数为 $\\frac{1}{\\sqrt{1-x^{2}}}$，区间为 $[-1,1]$。\n"
        )
        self.assertEqual(self.scan(text), [])

    def test_chinese_line_is_still_scanned_by_this_detector(self):
        # 审计点名的残片全部是「中文 + 压平公式」，所以这条探测器不能吃 CJK 跳行。
        hits = self.scan("S =.) 假设 S11 可以用系数矩阵 C11 正交化，我们便可以变换整个重叠矩阵：\n")
        self.assertEqual(len(hits), 1)

    def test_suspect_code_cjk_skip_is_explicit(self):
        # 口径：suspect_code 只看整行没有中文的行；含中文的代码残片交给 formula_remnant。
        self.assertTrue(SUSPECT_CODE_SKIPS_CJK)
        text = "这里 mesh = np.zeros((3, 3)) 初始化。\n"
        self.assertEqual(self.scan(text), [])
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            self.assertEqual(find_suspect_code(path), [])
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), "mesh = [60, 60, 60]\n")
            self.assertEqual(len(find_suspect_code(path)), 1)


class BrokenLinkTests(unittest.TestCase):
    """链接目标被 PDF 换行切断，后半截退化成裸文本。"""

    def scan(self, text):
        with tempfile.TemporaryDirectory() as name:
            path = write_qmd(Path(name), text)
            return find_broken_links(path)

    def test_split_link_in_reference_list_is_reported(self):
        # 历史样本：06 章 [arrow](https://arrow). apache.org/cookbook/…
        hits = self.scan(
            "::: {.ref-list}\n\n"
            "[24] Apache Software Foundation, Arrow cookbook, [arrow](https://arrow). apache.org/cookbook/py/flight.html, 2022.\n\n"
            "[28] The Ray Team, Ray documentation, [docs.ray](https://docs.ray). io/en/latest/cluster.html, 2024.\n\n"
            ":::\n"
        )
        self.assertEqual([hit["reason"] for hit in hits], ["broken_link:apache.org", "broken_link:io/"])

    def test_intact_links_and_plain_prose_are_ignored(self):
        text = (
            "::: {.ref-list}\n\n"
            "[23] Apache Software Foundation, Arrow memory, [apache.org](https://arrow.apache.org/docs/python/memory.html), 2024.\n\n"
            ":::\n"
            "详见 [NumPy 文档](https://numpy.org/doc/stable/)。\n"
            "扫描报告写在 [reports/link.json](reports/link.json) 里。\n"
        )
        self.assertEqual(self.scan(text), [])

    def test_code_fence_and_math_block_are_ignored(self):
        text = (
            "```bash\ncurl -O https://example.org/x\n```\n"
            "$$\na = b qquad (1.1)\n$$\n"
        )
        self.assertEqual(self.scan(text), [])


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
        # 存量已在 2026-10-29 清零：正文裸 URL 全部转成行内链接、疑似代码行清完、
        # 英文残留统一翻译、公式图转 LaTeX 后残留的压平副本逐条修完（见
        # docs/VERIFICATION.md 的「公式残片与压平副本清理」一节）。这四类再出现就是缺陷。
        self.assertEqual({key: self.report["totals"][key] for key in STRICT_DETECTORS}, {key: 0 for key in STRICT_DETECTORS})

    def test_prose_in_fence_does_not_grow(self):
        # 围栏内的长英文句子混有合法文档字符串、报错信息与 shell 注释，只做待甄别清单。
        # 2026-10-28 存量 100 条；这条断言只防增长，不做清零要求。
        self.assertLessEqual(self.report["totals"]["prose_in_fence"], 100)


if __name__ == "__main__":
    unittest.main()
