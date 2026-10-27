"""Check local HTML/CSS targets and the assembled publication boundary."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

try:
    from .publishing import Issue, PublishingError, load_yaml, write_report
except ImportError:
    from publishing import Issue, PublishingError, load_yaml, write_report

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_SUFFIXES = {".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
                   ".woff", ".woff2", ".ttf", ".otf", ".eot", ".ico", ".map", ".wasm", ".txt", ".xml"}
FORBIDDEN_PARTS = {"drafts", "raw", "cache", "__pycache__", "node_modules"}


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicates: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if not value:
                continue
            if name == "id" or (tag == "a" and name == "name"):
                # Quarto 1.10.19 repeats these stylesheet IDs for light/dark pairs.
                # Keep checking all document anchors; exempt only its <link> assets.
                theme_link = tag == "link" and value in {"quarto-bootstrap", "quarto-text-highlighting-styles"}
                if value in self.ids and not theme_link:
                    self.duplicates.add(value)
                self.ids.add(value)
            if name in {"href", "src", "poster"} or (tag == "object" and name == "data"):
                self.links.append(value)
            if name == "srcset":
                self.links.extend(item.strip().split()[0] for item in value.split(",") if item.strip())


def check_site(site: Path, expected_slugs: set[str]) -> list[Issue]:
    issues: list[Issue] = []
    pages: dict[Path, Page] = {}
    references: list[tuple[Path, str]] = []

    def add(code: str, file: Path, message: str) -> None:
        issues.append(Issue(code, file.relative_to(site).as_posix(), message))

    if not (site / "index.html").is_file():
        return [Issue("missing-entry", "index.html", "Portal entry is missing")]
    for file in site.rglob("*"):
        relative = file.relative_to(site)
        parts = relative.parts
        if file.is_symlink():
            add("boundary", file, "Output symlinks are forbidden")
            continue
        if any(part.lower() in FORBIDDEN_PARTS or (part.startswith(".") and part != ".nojekyll") for part in parts):
            add("boundary", file, "Private/cache path in output")
        if len(parts) > 1 and parts[0] == "books" and parts[1] not in expected_slugs:
            add("boundary", file, "Unregistered book in output")
        if not file.is_file():
            continue
        if file.name != ".nojekyll" and file.suffix.lower() not in OUTPUT_SUFFIXES:
            add("boundary", file, "Unsupported publication file type")
        if file.suffix.lower() == ".html":
            parser = Page()
            parser.feed(file.read_text(encoding="utf-8"))
            pages[file.resolve()] = parser
            for duplicate in parser.duplicates:
                add("duplicate-anchor", file, duplicate)
            references.extend((file, url) for url in parser.links)
        if file.suffix.lower() == ".css":
            text = file.read_text(encoding="utf-8")
            # Ignore CSS comments (including sourceMappingURL comments).
            text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
            references.extend((file, match[1]) for match in re.findall(r"url\(\s*(['\"]?)(.*?)\1\s*\)", text))
            references.extend((file, url) for url in re.findall(r"@import\s+['\"]([^'\"]+)['\"]", text))
    for slug in expected_slugs:
        if not (site / "books" / slug / "index.html").is_file():
            issues.append(Issue("missing-entry", f"books/{slug}/index.html", "Book entry is missing"))
    root = site.resolve()
    for file, url in references:
        try:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue  # External URLs are intentionally not fetched.
            path = unquote(parsed.path)
            if "\\" in path or "\x00" in path:
                raise PublishingError("Invalid local URL")
            if path.startswith("/"):
                raise PublishingError("Root-relative URLs are unsafe under a Pages repository prefix")
            target = ((file.parent / path) if path else file).resolve()
            if not target.is_relative_to(root):
                raise PublishingError("Link escapes publication root")
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                raise PublishingError("Missing local target")
            fragment = unquote(parsed.fragment)
            # CSS/SVG fragment references may address symbols rather than HTML IDs.
            if fragment and target in pages and fragment not in pages[target].ids:
                raise PublishingError(f"Missing HTML anchor: {fragment}")
        except (ValueError, OSError, PublishingError) as error:
            add("broken-link", file, f"{url}: {error}")
    return issues


def registered_slugs(root: Path = ROOT) -> set[str]:
    """Slugs recorded in the publish registry, so CI need not repeat them."""
    registry = load_yaml(root / "catalog/books.yaml")
    books = registry.get("books") if isinstance(registry, dict) else None
    return {str(book["id"]) for book in books or [] if isinstance(book.get("id"), str)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    parser.add_argument("--book", action="append", default=[])
    parser.add_argument("--report", type=Path, default=Path("reports/links.json"))
    args = parser.parse_args()
    issues = check_site(args.site, set(args.book) or registered_slugs())
    report = write_report(args.report, issues, site=str(args.site))
    print(f"Site check: {'PASS' if report['ok'] else 'FAIL'}; {len(issues)} issue(s); {args.report}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
