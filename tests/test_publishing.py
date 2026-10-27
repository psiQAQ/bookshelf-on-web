"""M0 source-named regression tests; all approval records below are temp fixtures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts.build import _deliver, build, portal_index
from scripts.check_site import check_site
from scripts.publishing import (ROOT, PublishingError, book_config, check_qmd, load_yaml,
                                safe_path, schema_errors, validate)


class PublishingFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for folder in ("schemas", "portal", "catalog", "scripts"):
            shutil.copytree(ROOT / folder, self.root / folder, ignore=shutil.ignore_patterns("__pycache__"))
        for slug in ("sample-linear-algebra", "sample-waves"):
            shutil.copytree(ROOT / "books" / slug, self.root / "books" / slug)
        # Fixture catalogs must not depend on books added to the real preview.
        (self.root / "catalog/preview.yaml").write_text(yaml.safe_dump({"books": [
            {"id": slug, "path": f"books/{slug}/metadata.yaml"}
            for slug in ("sample-linear-algebra", "sample-waves")
        ]}), encoding="utf-8")
        (self.root / "catalog/books.yaml").write_text("books: []\n", encoding="utf-8")
        self.directory = self.root / "books/sample-linear-algebra"
        self.metadata_path = self.directory / "metadata.yaml"

    def metadata(self):
        return load_yaml(self.metadata_path)

    def save(self, value):
        self.metadata_path.write_text(yaml.safe_dump(value, allow_unicode=True), encoding="utf-8")

    def register(self):
        shutil.copyfile(self.root / "catalog/preview.yaml", self.root / "catalog/books.yaml")

    def approve_fixture(self):
        """Synthetic test-only evidence; never writes into repository books or docs."""
        for slug in ("sample-linear-algebra", "sample-waves"):
            path = self.root / "books" / slug / "metadata.yaml"
            m = load_yaml(path)
            m["review"].update(status="approved", approved_by="SYNTHETIC TEST FIXTURE", approved_at="2026-01-01T00:00:00Z", evidence_path="docs/reviews/test-fixture.md")
            path.write_text(yaml.safe_dump(m), encoding="utf-8")
            provenance_path = path.parent / "provenance.json"
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            for block in provenance["blocks"]:
                block["review_state"] = "verified"
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
        evidence = self.root / "docs/reviews/test-fixture.md"
        evidence.parent.mkdir(parents=True)
        evidence.write_text("SYNTHETIC TEST FIXTURE, not a publication approval", encoding="utf-8")
        self.register()

    def errors(self, **kwargs):
        return [issue for issue in validate(self.root, **kwargs)[1] if issue.severity == "error"]

    @staticmethod
    def fake_renderer(project):
        config = load_yaml(project / "_quarto.yml")
        output = project / config["project"]["output-dir"]
        output.mkdir()
        (output / "index.html").write_text('<html><h1 id="entry">Test</h1><a href="#entry">Self</a></html>', encoding="utf-8")
        return output


class ValidateTests(PublishingFixture):
    def test_empty_publish_registry_passes_strict(self):
        self.assertEqual(self.errors(strict=True), [])

    def test_preview_samples_remain_drafts_with_no_fabricated_pdf_evidence(self):
        books, issues = validate(self.root, preview=True)
        self.assertEqual(len(books), 2)
        self.assertTrue(issues)
        self.assertFalse(any(i.severity == "error" for i in issues))
        for book in books:
            self.assertEqual(book.metadata["review"]["status"], "draft")
            self.assertNotIn("sha256", book.metadata["source"])

    def test_strict_rejects_registered_drafts(self):
        self.register()
        self.assertTrue(any(i.code == "ineligible" for i in self.errors(strict=True)))

    def test_schema_rejects_wrong_types_unknown_fields_and_invalid_slug(self):
        for field, value in (("id", "../escape"), ("title", 12), ("title", " "), ("surprise", True)):
            with self.subTest(field=field):
                metadata = self.metadata()
                metadata[field] = value
                self.assertTrue(schema_errors(self.root, "book.schema.json", metadata))

    def test_duplicate_registry_id(self):
        path = self.root / "catalog/books.yaml"
        entry = {"id": "sample-linear-algebra", "path": "books/sample-linear-algebra/metadata.yaml"}
        path.write_text(yaml.safe_dump({"books": [entry, entry]}), encoding="utf-8")
        self.assertTrue(any(i.code == "duplicate-id" for i in self.errors(strict=True)))

    def test_registry_id_path_mismatch(self):
        (self.root / "catalog/books.yaml").write_text("books:\n- id: sample-linear-algebra\n  path: books/sample-waves/metadata.yaml\n", encoding="utf-8")
        self.assertTrue(self.errors(strict=True))

    def test_registry_traversal(self):
        (self.root / "catalog/books.yaml").write_text("books:\n- id: sample-linear-algebra\n  path: ../outside.yaml\n", encoding="utf-8")
        self.assertTrue(self.errors(strict=True))

    def test_duplicate_yaml_keys_are_not_silently_overwritten(self):
        (self.root / "catalog/books.yaml").write_text("books: []\nbooks: []\n", encoding="utf-8")
        self.assertTrue(self.errors(strict=True))

    def test_malformed_yaml_and_null_registry_produce_diagnostics(self):
        path = self.root / "catalog/books.yaml"
        for text in ("books: [", "null", "books: nope"):
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.assertTrue(self.errors(strict=True))

    def test_chapter_traversal_is_rejected(self):
        m = self.metadata()
        m["chapters"].append("../../secret.qmd")
        self.save(m)
        self.assertTrue(self.errors(preview=True))

    def test_asset_symlink_and_source_symlink_are_rejected(self):
        source = self.root / "outside.qmd"
        source.write_text("# secret", encoding="utf-8")
        target = self.directory / "linked.qmd"
        try:
            target.symlink_to(source)
        except OSError:
            self.skipTest("Windows symlink privilege unavailable")
        with self.assertRaises(PublishingError):
            safe_path(self.directory, "linked.qmd")

    def test_missing_review_record_blocks_approved_fixture(self):
        self.approve_fixture()
        (self.root / "docs/reviews/test-fixture.md").unlink()
        self.assertTrue(self.errors(strict=True))

    def test_unresolved_p0_p1_block_but_p2_does_not(self):
        self.approve_fixture()
        for severity in ("P0", "P1", "P2"):
            with self.subTest(severity=severity):
                m = self.metadata()
                m["review"]["issues"] = [{"id": "test-risk", "severity": severity, "status": "open"}]
                self.save(m)
                self.assertEqual(bool(self.errors(strict=True)), severity != "P2")

    def test_approval_does_not_override_unreviewed_provenance(self):
        self.approve_fixture()
        path = self.directory / "provenance.json"
        provenance = json.loads(path.read_text(encoding="utf-8"))
        provenance["blocks"][0]["review_state"] = "needs_review"
        path.write_text(json.dumps(provenance), encoding="utf-8")
        self.assertTrue(any(i.code == "unreviewed-provenance" for i in self.errors(strict=True)))

    def test_invalid_date(self):
        m = self.metadata()
        m["review"]["approved_at"] = "yesterday"
        self.assertTrue(schema_errors(self.root, "book.schema.json", m))

    def test_original_mapping_cannot_claim_pdf_coordinates(self):
        path = self.directory / "provenance.json"
        provenance = json.loads(path.read_text(encoding="utf-8"))
        provenance["blocks"][0]["source"]["pdf_page"] = 1
        self.assertTrue(schema_errors(self.root, "provenance.schema.json", provenance))

    def test_duplicate_provenance_and_missing_anchor(self):
        path = self.directory / "provenance.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for duplicate in (True, False):
            value = json.loads(json.dumps(original))
            if duplicate:
                value["blocks"].append(value["blocks"][0])
            else:
                value["blocks"][0]["qmd_anchor"] = "nonexistent"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertTrue(self.errors(preview=True))

    def test_pdf_mapping_hash_bbox_and_page_schema(self):
        source = {"type": "pdf", "pdf_sha256": "a" * 64, "pdf_page": 1, "printed_page": "i", "bbox": [0.1, 0.2, 0.8, 0.9]}
        block = {"block_id": "block-one", "qmd": "index.qmd", "qmd_anchor": "intro", "source": source, "review_state": "needs_review"}
        value = {"book_id": "test-book", "blocks": [block]}
        self.assertEqual(schema_errors(self.root, "provenance.schema.json", value), [])
        source["pdf_page"] = 0
        source["bbox"] = [-1, 0, 2, 1]
        self.assertTrue(schema_errors(self.root, "provenance.schema.json", value))

    def test_static_code_accepted_executable_options_and_shortcodes_rejected(self):
        path = self.root / "input.qmd"
        for text in ('```python\nraise RuntimeError("never run")\n```', '# Static {#sec-static}\n'):
            path.write_text(text, encoding="utf-8")
            check_qmd(path)
        for text in ('```{python}\nprint(1)\n```', '~~~{r}\nx\n~~~', '`{python} 2 + 2`', '{{< include ../private >}}', '---\nfilters: [evil.lua]\n---'):
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(PublishingError):
                    check_qmd(path)

    def test_source_config_hooks_cannot_reach_renderer(self):
        config = book_config(self.metadata())
        config["project"]["pre-render"] = ["python evil.py"]
        (self.directory / "_quarto.yml").write_text(yaml.safe_dump(config), encoding="utf-8")
        self.assertTrue(self.errors(preview=True))

    def test_source_links_cannot_import_unregistered_resources(self):
        for reference in ('![private](../../outside.png)', '<img src="file:///private.png">', '[secret]: ../../outside.png', '<script src="../../outside.js"></script>'):
            with self.subTest(reference=reference):
                (self.directory / "index.qmd").write_text('# Intro\n' + reference, encoding="utf-8")
                self.assertTrue(self.errors(preview=True))

    def test_duplicate_explicit_qmd_anchor(self):
        path = self.directory / "index.qmd"
        path.write_text('# A {#same}\n\n## B {#same}', encoding="utf-8")
        self.assertTrue(self.errors(preview=True))

    def test_safe_path_rejects_platform_specific_escapes(self):
        for value in ("/etc/passwd", "C:/private", "a\\b", "../private", "a//b", "./a", ".hidden", "a/../b"):
            with self.subTest(value=value), self.assertRaises(PublishingError):
                safe_path(self.root, value)

    def test_cli_strict_failure_writes_machine_readable_report(self):
        self.register()
        report_path = self.root / "result.json"
        result = subprocess.run([sys.executable, str(self.root / "scripts/validate.py"), "--strict", "--report", str(report_path)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(report_path.read_text(encoding="utf-8"))["ok"])


class BuildTests(PublishingFixture):
    def test_empty_registry_build_ignores_unregistered_material_and_drafts(self):
        (self.root / "books/private-user-material").mkdir()
        (self.root / "books/private-user-material/secret.pdf").write_bytes(b"secret")
        report = build(self.root, renderer=self.fake_renderer)
        self.assertTrue(report["delivered"])
        self.assertEqual(report["books"], [])
        self.assertFalse((self.root / "dist/books").exists())

    def test_gate_runs_before_renderer(self):
        self.register()
        def forbidden(project):
            self.fail("Ineligible book reached renderer")
        report = build(self.root, renderer=forbidden)
        self.assertFalse(report["ok"])
        self.assertFalse((self.root / "dist").exists())

    def test_preview_two_books_never_delivers_dist(self):
        report = build(self.root, preview=True, renderer=self.fake_renderer)
        self.assertTrue(report["ok"])
        self.assertEqual(report["mode"], "local-preview")
        for slug in ("sample-linear-algebra", "sample-waves"):
            self.assertTrue((self.root / ".preview/books" / slug / "index.html").is_file())
        self.assertFalse((self.root / "dist").exists())

    def test_two_approved_test_fixtures_build_in_isolated_projects(self):
        self.approve_fixture()
        def inspect(project):
            config = load_yaml(project / "_quarto.yml")
            self.assertEqual(config["execute"], {"enabled": False, "eval": False})
            self.assertFalse((project / "metadata.yaml").exists())
            self.assertFalse((project / "provenance.json").exists())
            return self.fake_renderer(project)
        report = build(self.root, renderer=inspect)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["books"]), 2)
        self.assertEqual(check_site(self.root / "dist", set(report["books"])), [])

    def test_render_failure_preserves_previous_dist_and_cleans_staging(self):
        (self.root / "dist").mkdir()
        (self.root / "dist/index.html").write_text("previous good output", encoding="utf-8")
        def fail(project):
            raise PublishingError("intentional render failure")
        report = build(self.root, renderer=fail)
        self.assertFalse(report["delivered"])
        self.assertFalse(report["ok"])
        self.assertEqual((self.root / "dist/index.html").read_text(encoding="utf-8"), "previous good output")
        self.assertEqual(list(self.root.glob(".build-*")), [])

    def test_broken_link_and_pdf_output_block_delivery(self):
        for pdf in (False, True):
            with self.subTest(pdf=pdf):
                def broken(project):
                    out = self.fake_renderer(project)
                    if pdf:
                        (out / "secret.pdf").write_bytes(b"private")
                    else:
                        (out / "index.html").write_text('<a href="missing.html">Broken</a>', encoding="utf-8")
                    return out
                report = build(self.root, renderer=broken)
                self.assertFalse(report["delivered"])
                self.assertFalse((self.root / "dist").exists())

    def test_successful_rebuild_replaces_previous_output(self):
        for _ in range(2):
            self.assertTrue(build(self.root, renderer=self.fake_renderer)["ok"])
        self.assertFalse((self.root / "dist.previous").exists())

    def test_delivery_rename_failure_rolls_back_previous_good_site(self):
        destination, stage = self.root / "dist", self.root / "checked-stage"
        destination.mkdir()
        stage.mkdir()
        (destination / "index.html").write_text("previous", encoding="utf-8")
        (stage / "index.html").write_text("next", encoding="utf-8")
        replace = os.replace
        def fail_stage(source, target):
            if source == stage:
                raise OSError("injected delivery rename failure")
            return replace(source, target)
        with patch("scripts.build.os.replace", side_effect=fail_stage):
            with self.assertRaises(OSError):
                _deliver(stage, destination)
        self.assertEqual((destination / "index.html").read_text(encoding="utf-8"), "previous")
        self.assertFalse((self.root / "dist.previous").exists())

    def test_title_html_is_escaped_in_generated_portal(self):
        books, _ = validate(self.root, preview=True)
        books[0].metadata["title"] = '<script>alert("no")</script>'
        text = portal_index(books, True)
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn('<script>', text)

    @unittest.skipUnless(os.environ.get("QUARTO_TEST_EXECUTABLE"), "Set QUARTO_TEST_EXECUTABLE for real rendering")
    def test_real_quarto_empty_portal_and_two_book_preview(self):
        executable = os.environ["QUARTO_TEST_EXECUTABLE"]
        report = build(self.root, quarto=executable)
        self.assertTrue(report["ok"], report["issues"])
        sentinel = self.root / "CODE_MUST_NOT_RUN"
        with (self.directory / "index.qmd").open("a", encoding="utf-8") as stream:
            stream.write(f'\n```python\nfrom pathlib import Path\nPath({str(sentinel)!r}).write_text("executed")\n```\n')
        report = build(self.root, preview=True, quarto=executable)
        self.assertFalse(sentinel.exists(), "Publication executed static source code")
        self.assertTrue(report["ok"], report["issues"])
        for slug, chapter, anchor in (("sample-linear-algebra", "01-length", "eq-vector-length"), ("sample-waves", "01-phase", "eq-wave-signal")):
            text = (self.root / f".preview/books/{slug}/chapters/{chapter}.html").read_text(encoding="utf-8")
            self.assertIn(f'id="{anchor}"', text)
            self.assertIn('math display', text)
            self.assertIn('sourceCode', text)
            self.assertIn('quarto-color-alternate', text)
            self.assertIn('quarto-sidebar', text)


class CheckSiteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.site = Path(self.temporary.name)

    def test_relative_links_anchors_and_css_resources(self):
        (self.site / "index.html").write_text('<h1 id="intro">Hi</h1><a href="#intro">Hi</a><link href="style.css" rel="stylesheet">', encoding="utf-8")
        (self.site / "style.css").write_text('body {background: url("pixel.png")}', encoding="utf-8")
        (self.site / "pixel.png").write_bytes(b"fixture")
        self.assertEqual(check_site(self.site, set()), [])
        (self.site / "pixel.png").unlink()
        self.assertTrue(any(i.code == "broken-link" for i in check_site(self.site, set())))

    def test_missing_anchors_escape_root_urls_and_srcset(self):
        for url in ("#missing", "../private.png", "/index.html", "%2e%2e/private.png"):
            with self.subTest(url=url):
                (self.site / "index.html").write_text(f'<a href="{url}">Bad</a>', encoding="utf-8")
                self.assertTrue(check_site(self.site, set()))
        (self.site / "index.html").write_text('<img srcset="missing.png 1x, other.png 2x">', encoding="utf-8")
        self.assertEqual(len(check_site(self.site, set())), 2)

    def test_duplicate_content_id_rejected_but_quarto_theme_links_supported(self):
        (self.site / "index.html").write_text('<h1 id="same">A</h1><p id="same">B</p>', encoding="utf-8")
        self.assertTrue(any(i.code == "duplicate-anchor" for i in check_site(self.site, set())))
        (self.site / "style.css").write_text('', encoding="utf-8")
        (self.site / "index.html").write_text('<link id="quarto-bootstrap" href="style.css"><link id="quarto-bootstrap" href="style.css">', encoding="utf-8")
        self.assertEqual(check_site(self.site, set()), [])

    def test_missing_entry_and_unregistered_books_private_paths(self):
        self.assertTrue(check_site(self.site, set()))
        (self.site / "index.html").write_text('OK', encoding="utf-8")
        for folder in ("books/not-registered", "drafts", "cache"):
            directory = self.site / folder
            directory.mkdir(parents=True)
            (directory / "index.html").write_text('private', encoding="utf-8")
        self.assertTrue(any(i.code == "boundary" for i in check_site(self.site, set())))


if __name__ == "__main__":
    unittest.main()
