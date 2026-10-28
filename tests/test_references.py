import re
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.format_references import (  # noqa: E402
    Stats,
    close_gaps,
    fit_ligatures,
    format_section,
    host_label,
    split_url,
)


class SplitUrlTests(unittest.TestCase):
    def test_sentence_punctuation_stays_outside_the_link(self):
        self.assertEqual(split_url("https://pyscf.org/,"), ("https://pyscf.org/", ","))
        self.assertEqual(split_url("https://doi.org/10.1/x."), ("https://doi.org/10.1/x", "."))
        self.assertEqual(split_url("https://docs.python.org/3/"), ("https://docs.python.org/3/", ""))

    def test_closing_parenthesis_is_not_stripped(self):
        url = "https://en.wikipedia.org/wiki/JIT_(computing)"
        self.assertEqual(split_url(url), (url, ""))


class CloseGapsTests(unittest.TestCase):
    def test_typeset_space_inside_a_domain_is_closed(self):
        line = "Team, Docs, https://docs. python.org/3/library/, 2024."
        self.assertEqual(close_gaps(line), ("Team, Docs, https://docs.python.org/3/library/, 2024.", 1))

    def test_space_after_underscore_or_slash_is_closed(self):
        joined, count = close_gaps("https://books.google.com/books?id=D_ Ph20OZu0YC.")
        self.assertEqual((joined, count), ("https://books.google.com/books?id=D_Ph20OZu0YC.", 1))

    def test_month_abbreviation_is_left_alone(self):
        line = "Creator, Post, https://blog.example/post/, Jul. 2022."
        self.assertEqual(close_gaps(line), (line, 0))

    def test_capitalised_word_is_not_glued(self):
        line = "Books, https://books.google.com/books?id=x. References 21"
        self.assertEqual(close_gaps(line), (line, 0))


class HostLabelTests(unittest.TestCase):
    def test_doi_is_labelled(self):
        self.assertEqual(host_label("https://doi.org/10.1063/1.4758987"), "DOI")

    def test_www_prefix_and_subdomains_are_dropped(self):
        self.assertEqual(host_label("https://docs.python.org/3/"), "python.org")
        self.assertEqual(host_label("https://www.brendangregg.com/perf.html"), "brendangregg.com")

    def test_country_second_level_domain_keeps_three_labels(self):
        self.assertEqual(host_label("https://books.google.co.in/books?id=x"), "google.co.in")


class LigatureTests(unittest.TestCase):
    def test_pdf_ligatures_are_folded(self):
        self.assertEqual(fit_ligatures("https://\ufb02ake8.pycqa.org/"), "https://flake8.pycqa.org/")


class FormatSectionTests(unittest.TestCase):
    def test_entries_become_separate_paragraphs_with_hidden_urls(self):
        stats = Stats()
        block = format_section(
            ["[1] A. Author, Title, https://doi.org/10.1/x.", "", "[2] B. Author, Book, 1996."], stats)
        self.assertEqual(block, [
            "::: {.ref-list}", "",
            "[1] A. Author, Title, [DOI](https://doi.org/10.1/x).", "",
            "[2] B. Author, Book, 1996.", "",
            ":::",
        ])
        self.assertEqual((stats.entries, stats.links), (2, 1))

    def test_empty_section_is_left_alone(self):
        self.assertEqual(format_section([], Stats()), [])

    def test_existing_links_are_not_relinked(self):
        stats = Stats()
        once = format_section(["[1] Title, [scipy.org](https://docs.scipy.org/doc/), 2024."], stats)
        stats = Stats()
        twice = format_section(once, stats)
        self.assertEqual(once, twice)
        self.assertEqual(stats.links, 0)


class CorpusTests(unittest.TestCase):
    """Locks the committed chapters: every reference list stays formatted and complete."""

    CHAPTERS = Path(__file__).resolve().parents[1] / "books" / (
        "python-for-quantum-chemistry-a-full-stack-programming-guide" ) / "chapters"

    def sections(self):
        for path in sorted(self.CHAPTERS.glob("*.qmd")):
            text = path.read_text(encoding="utf-8")
            self.assertIn("## 参考文献", text, path.name)
            start = text.index("## 参考文献")
            section = text[start:]
            match = re.search(r"^#{1,2} ", section[3:], re.M)
            yield path.name, section[:match.start() + 3] if match else section

    def test_every_list_is_a_ref_list_block_with_one_paragraph_per_entry(self):
        for name, section in self.sections():
            with self.subTest(chapter=name):
                lines = [line.strip() for line in section.splitlines()]
                self.assertIn("::: {.ref-list}", lines)
                opening = lines.index("::: {.ref-list}")
                closing = max(i for i, line in enumerate(lines) if line == ":::")
                self.assertTrue(all(not line for line in lines[closing + 1:]), name)
                body = [line for line in lines[opening + 1:closing] if line]
                self.assertTrue(body)
                self.assertTrue(all(line.startswith("[") for line in body), name)

    def test_entries_are_sequentially_numbered_without_duplicates(self):
        for name, section in self.sections():
            with self.subTest(chapter=name):
                entries = [line.strip() for line in section.splitlines() if line.startswith("[")]
                numbers = [int(line.split("]")[0][1:]) for line in entries]
                self.assertEqual(numbers, list(range(1, len(entries) + 1)))
                self.assertEqual(len(set(entries)), len(entries))

    def test_no_url_is_rendered_as_bare_text(self):
        pattern = re.compile(r"https?://")
        for name, section in self.sections():
            with self.subTest(chapter=name):
                remainder = re.sub(r"\[[^\]]+\]\(https?://[^)\s]+\)", "", section)
                self.assertEqual(pattern.findall(remainder), [])


if __name__ == "__main__":
    unittest.main()
