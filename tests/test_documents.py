"""Naming, bilingual entry points and manual-only workflow contracts."""
from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class DocumentTests(unittest.TestCase):
    def test_lowercase_readmes_link_each_other_and_have_matching_commands(self):
        names = {path.name for path in ROOT.iterdir()}
        self.assertIn("readme.md", names)
        self.assertIn("readme_zh.md", names)
        self.assertNotIn("README.md", names)
        english = (ROOT / "readme.md").read_text(encoding="utf-8")
        chinese = (ROOT / "readme_zh.md").read_text(encoding="utf-8")
        self.assertTrue(english.startswith("# Bookshelf On Web\n\n[中文](readme_zh.md)"))
        self.assertTrue(chinese.startswith("# Bookshelf On Web\n\n[English](readme.md)"))
        def commands(text):
            blocks = re.findall(r"```sh\n(.*?)```", text, flags=re.S)
            return [line for block in blocks for line in block.splitlines() if line and not line.startswith("#")]
        self.assertEqual(commands(english), commands(chinese))
        for document in (english, chinese):
            for target in re.findall(r"\]\(([^)]+\.md)\)", document):
                self.assertTrue((ROOT / target).is_file(), target)

    def test_site_and_project_name(self):
        config = yaml.safe_load((ROOT / "portal/_quarto.yml").read_text(encoding="utf-8"))
        self.assertEqual(config["website"]["title"], "bookshelf-on-web")
        self.assertTrue((ROOT / "portal/index.qmd").read_text(encoding="utf-8").startswith("# bookshelf-on-web"))

    def test_workflows_pin_actions_and_deployment_is_manual_only(self):
        def load(name):
            text = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            # BaseLoader avoids YAML 1.1 interpreting the GitHub key 'on' as a bool.
            return yaml.load(text, Loader=yaml.BaseLoader), text
        deploy, text = load("deploy.yml")
        self.assertEqual(set(deploy["on"]), {"workflow_dispatch"})
        self.assertEqual(deploy["jobs"]["build"]["if"], "github.ref == 'refs/heads/main'")
        self.assertIn("path: dist", text)
        self.assertNotIn("--preview", text)
        validation, validation_text = load("validate.yml")
        self.assertIn("pull_request", validation["on"])
        self.assertNotIn("pages: write", validation_text)
        for workflow in (deploy, validation):
            for job in workflow["jobs"].values():
                for step in job["steps"]:
                    if "uses" in step:
                        self.assertRegex(step["uses"], r"^[\w./-]+@[a-f0-9]{40}$")


if __name__ == "__main__":
    unittest.main()
