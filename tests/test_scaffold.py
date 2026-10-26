"""Smoke checks for the initial workspace, without third-party dependencies."""

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_workspace_is_not_a_python_package(self):
        with (ROOT / "pyproject.toml").open("rb") as source:
            config = tomllib.load(source)
        self.assertEqual(config["project"]["name"], "bookshelf-on-web")
        self.assertFalse(config["tool"]["uv"]["package"])

    def test_portal_sources_exist(self):
        for filename in ("_quarto.yml", "index.qmd", "about.qmd"):
            with self.subTest(filename=filename):
                self.assertTrue((ROOT / "portal" / filename).is_file())


if __name__ == "__main__":
    unittest.main()
