"""Render an allowlisted registry in isolation, check it, then deliver the site."""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable

import yaml

try:
    from .check_site import check_site
    from .publishing import (ROOT, QUARTO_VERSION, Book, Issue, PublishingError, book_config,
                             portal_config, validate, write_report)
except ImportError:
    from check_site import check_site
    from publishing import (ROOT, QUARTO_VERSION, Book, Issue, PublishingError, book_config,
                            portal_config, validate, write_report)


def portal_index(books: list[Book], preview: bool) -> str:
    text = '# bookshelf-on-web\n\n科学技术资料的在线阅读书架。\n\n'
    if preview:
        text += '**LOCAL PREVIEW ONLY — 未审核、不可部署。**\n\n'
    elif not books:
        text += '目前没有获批发布的书籍。\n\n'
    text += '<ul>\n'
    for book in books:
        m = book.metadata
        text += (f'<li><a href="books/{book.slug}/index.html">{html.escape(m["title"])}</a>'
                 f' — {html.escape(m["language"])} · {html.escape(", ".join(m["categories"]))}</li>\n')
    return text + '</ul>\n\n[关于项目](about.qmd)\n'


def quarto_renderer(executable: str) -> Callable[[Path], Path]:
    found = shutil.which(executable)
    if not found:
        raise PublishingError(f"Quarto not found: {executable}; install Quarto {QUARTO_VERSION}")
    executable = str(Path(found).resolve())
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    if result.stdout.strip() != QUARTO_VERSION:
        raise PublishingError(f"Expected Quarto {QUARTO_VERSION}, got {result.stdout.strip()!r}")

    def render(project: Path) -> Path:
        command = [executable, "render", str(project), "--to", "html", "--no-execute"]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise PublishingError(f"Quarto render failed ({project.name}):\n{result.stdout}\n{result.stderr}")
        config = yaml.safe_load((project / "_quarto.yml").read_text(encoding="utf-8"))
        return project / config["project"]["output-dir"]

    return render


def _deliver(stage: Path, destination: Path) -> None:
    """Replace only a fully checked artifact; roll back if the final rename fails."""
    backup = destination.with_name(destination.name + ".previous")
    if destination.is_symlink() or backup.exists() or backup.is_symlink():
        raise PublishingError("Unsafe destination or leftover .previous artifact; inspect manually")
    if destination.exists():
        if not destination.is_dir():
            raise PublishingError("Output destination must be a directory")
        os.replace(destination, backup)
    try:
        os.replace(stage, destination)
    except OSError:
        if backup.exists():
            os.replace(backup, destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def build(root: Path = ROOT, *, preview: bool = False, quarto: str = "quarto",
          renderer: Callable[[Path], Path] | None = None) -> dict:
    destination = root / (".preview" if preview else "dist")
    report_path = root / "reports" / ("preview-build.json" if preview else "build.json")
    books, issues = validate(root, preview=preview, strict=not preview)
    details = {"mode": "local-preview" if preview else "publish", "delivered": False,
               "output": str(destination), "books": [b.slug for b in books], "quarto_version": QUARTO_VERSION}
    if any(issue.severity == "error" for issue in issues):
        return write_report(report_path, issues, **details)
    try:
        render = renderer or quarto_renderer(quarto)
        with tempfile.TemporaryDirectory(prefix=".build-", dir=root) as temporary:
            temporary = Path(temporary)
            projects, stage = temporary / "projects", temporary / "site"
            projects.mkdir()
            portal = projects / "portal"
            portal.mkdir()
            (portal / "_quarto.yml").write_text(yaml.safe_dump(portal_config(), allow_unicode=True), encoding="utf-8")
            (portal / "index.qmd").write_text(portal_index(books, preview), encoding="utf-8")
            shutil.copyfile(root / "portal/about.qmd", portal / "about.qmd")
            shutil.copytree(render(portal), stage)
            for book in books:
                project = projects / "books" / book.slug
                project.mkdir(parents=True)
                (project / "_quarto.yml").write_text(yaml.safe_dump(book_config(book.metadata), allow_unicode=True), encoding="utf-8")
                for relative in book.metadata["chapters"] + book.metadata["assets"]:
                    target = project / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(book.directory / relative, target)
                if preview:
                    with (project / "index.qmd").open("a", encoding="utf-8") as stream:
                        stream.write('\n\n**LOCAL PREVIEW ONLY — 未审核，不可公开发布。**\n')
                target = stage / "books" / book.slug
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(render(project), target)
            (stage / ".nojekyll").touch()
            issues.extend(check_site(stage, {book.slug for book in books}))
            details["file_count"] = sum(f.is_file() for f in stage.rglob("*"))
            details["size_bytes"] = sum(f.stat().st_size for f in stage.rglob("*") if f.is_file())
            if not any(issue.severity == "error" for issue in issues):
                _deliver(stage, destination)
                details["delivered"] = True
    except (OSError, ValueError, subprocess.SubprocessError, PublishingError) as error:
        issues.append(Issue("build-failed", str(destination), str(error)))
    return write_report(report_path, issues, **details)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Local-only catalog/preview.yaml to .preview/, never dist/")
    parser.add_argument("--quarto", default="quarto", help=f"Quarto {QUARTO_VERSION} executable")
    args = parser.parse_args()
    report = build(preview=args.preview, quarto=args.quarto)
    print(f"Build: {'PASS' if report['ok'] else 'FAIL'}; mode={report['mode']}; delivered={report['delivered']}")
    for issue in report["issues"]:
        print(f"{issue['severity']}: {issue['code']}: {issue['path']}: {issue['message']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
