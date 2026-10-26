"""Registry-driven M0 publishing. Never render source project configuration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]
SLUG = r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
QUARTO_VERSION = "1.10.19"
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class PublishingError(Exception):
    pass


@dataclass
class Issue:
    code: str
    path: str
    message: str
    severity: str = "error"


@dataclass
class Book:
    directory: Path
    metadata: dict[str, Any]

    @property
    def slug(self) -> str:
        return self.metadata["id"]


def safe_path(base: Path, value: str) -> Path:
    """Only canonical relative POSIX paths; reject symlinks, including ancestors."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise PublishingError(f"Unsafe relative path: {value!r}")
    parts = value.split("/")
    if PurePosixPath(value).is_absolute() or any(p in {"", ".", ".."} or p.startswith(".") for p in parts):
        raise PublishingError(f"Unsafe relative path: {value!r}")
    target = base.joinpath(*parts)
    for candidate in (target, *target.parents):
        if candidate.is_symlink():
            raise PublishingError(f"Symlink is forbidden: {candidate}")
    if not target.resolve().is_relative_to(base.resolve()):
        raise PublishingError(f"Path escapes root: {value}")
    return target


class UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: UniqueLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise PublishingError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)
# Treat timestamps as strings so JSON Schema owns date/time validation.
UniqueLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values if tag != "tag:yaml.org,2002:timestamp"]
    for key, values in UniqueLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)


def schema_errors(root: Path, name: str, value: Any) -> list[str]:
    schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in validator.iter_errors(value)]


def book_config(metadata: dict) -> dict:
    return {
        "project": {"type": "book", "output-dir": "_book"},
        "book": {"title": metadata["title"], "chapters": metadata["chapters"],
                 "page-navigation": True, "reader-mode": True, "search": True},
        "format": {"html": {"lang": metadata["language"], "theme": {"light": "cosmo", "dark": "darkly"},
                            "html-math-method": "mathjax", "toc": True, "number-sections": True,
                            "code-copy": True, "code-overflow": "scroll"}},
        "execute": {"enabled": False, "eval": False},
    }


def portal_config() -> dict:
    return {
        "project": {"type": "website", "output-dir": "_site", "render": ["index.qmd", "about.qmd"]},
        "website": {"title": "bookshelf-on-web", "navbar": {"left": [
            {"href": "index.qmd", "text": "图书馆"}, {"href": "about.qmd", "text": "关于"}]}},
        "format": {"html": {"lang": "zh-CN", "theme": {"light": "cosmo", "dark": "darkly"},
                            "toc": True, "html-math-method": "mathjax", "code-copy": True,
                            "code-overflow": "scroll"}},
        "execute": {"enabled": False, "eval": False},
    }


def check_qmd(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    # No document-level options, shortcodes/includes, executable cells or inline engines.
    # Only static code fences are accepted by this deliberately narrow M0 input format.
    if text.lstrip().startswith("---") or re.search(r"\{\{[<%]|(?:`{3,}|~{3,})\s*\{|`\{(?:python|r|julia|ojs)\}", text):
        raise PublishingError(f"Executable cells, front matter and shortcodes are forbidden: {path}")
    anchors = re.findall(r"\{#([A-Za-z][\w:.-]*)\}", text)
    if len(anchors) != len(set(anchors)):
        raise PublishingError(f"Duplicate explicit anchor: {path}")


def check_source_links(directory: Path, chapter: str, inputs: set[str]) -> None:
    """Reject source references outside the explicit copy allowlist before Quarto runs.

    M0 accepts ordinary Markdown links/images, reference definitions and HTML URL
    attributes; this is a conservative preflight, not a general Markdown linter.
    """
    text = (directory / chapter).read_text(encoding="utf-8")
    urls = [a or b for a, b in re.findall(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", text)]
    urls += re.findall(r"^\s*\[[^\]]+\]:\s*<?([^\s>]+)", text, flags=re.M)
    urls += re.findall(r"(?:href|src|poster)\s*=\s*[\"']([^\"']+)[\"']", text, flags=re.I)
    allowed = {safe_path(directory, value).resolve() for value in inputs}
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme in {"http", "https", "mailto", "tel", "data"} or parsed.netloc:
            continue
        if parsed.scheme:
            raise PublishingError(f"Unsupported source URL scheme: {url}")
        value = unquote(parsed.path)
        if not value:
            continue
        if chr(92) in value or value.startswith("/") or "\x00" in value:
            raise PublishingError(f"Unsafe source URL: {url}")
        target = directory / Path(chapter).parent / value
        if target.suffix == ".html":
            target = target.with_suffix(".qmd")
        if target.resolve() not in allowed:
            raise PublishingError(f"Source URL is not a registered chapter/asset: {url}")


def eligibility(metadata: dict) -> list[str]:
    reasons = []
    review, rights = metadata["review"], metadata["rights"]
    if review["status"] != "approved" or not all(review.get(k) for k in ("approved_by", "approved_at", "evidence_path")):
        reasons.append("Explicit human approval and its evidence are required")
    if rights["public"] is not True or not rights.get("license") or not rights.get("evidence_url"):
        reasons.append("Public rights clearance, license and evidence URL are required")
    if any(i["severity"] in {"P0", "P1"} and i["status"] == "open" for i in review["issues"]):
        reasons.append("Unresolved P0/P1 issues block publication")
    return reasons


def validate(root: Path = ROOT, *, preview: bool = False, strict: bool = False) -> tuple[list[Book], list[Issue]]:
    if preview and strict:
        raise PublishingError("--preview and --strict are mutually exclusive")
    registry = "catalog/preview.yaml" if preview else "catalog/books.yaml"
    issues: list[Issue] = []
    books: list[Book] = []

    def add(code: str, path: str, message: str, severity: str = "error") -> None:
        issues.append(Issue(code, path, message, severity))

    try:
        entries = load_yaml(safe_path(root, registry))
        errors = schema_errors(root, "catalog.schema.json", entries)
        if errors:
            for error in errors:
                add("schema", registry, error)
            return books, issues
        seen = set()
        for entry in entries["books"]:
            identifier, location = entry["id"], entry["path"]
            if identifier in seen:
                add("duplicate-id", registry, identifier)
                continue
            seen.add(identifier)
            try:
                metadata_path = safe_path(root, location)
                if location != f"books/{identifier}/metadata.yaml":
                    raise PublishingError("Registry path must be books/<id>/metadata.yaml")
                metadata = load_yaml(metadata_path)
                errors = schema_errors(root, "book.schema.json", metadata)
                if errors:
                    for error in errors:
                        add("schema", location, error)
                    continue
                if metadata["id"] != identifier:
                    raise PublishingError("Registry id does not match metadata id")
                directory = metadata_path.parent
                if metadata["chapters"][0] != "index.qmd":
                    raise PublishingError("First chapter must be index.qmd")
                for chapter in metadata["chapters"]:
                    if Path(chapter).suffix != ".qmd":
                        raise PublishingError("Chapters must be .qmd files")
                    check_qmd(safe_path(directory, chapter))
                for asset in metadata["assets"]:
                    file = safe_path(directory, asset)
                    if not asset.startswith("assets/") or file.suffix.lower() not in ASSET_SUFFIXES or not file.is_file():
                        raise PublishingError(f"Unsupported/missing static asset: {asset}")
                for chapter in metadata["chapters"]:
                    check_source_links(directory, chapter, set(metadata["chapters"] + metadata["assets"]))
                config = load_yaml(safe_path(directory, "_quarto.yml"))
                if config != book_config(metadata):
                    raise PublishingError("_quarto.yml must match the safe metadata-derived configuration")
                provenance = json.loads(safe_path(directory, "provenance.json").read_text(encoding="utf-8"))
                errors = schema_errors(root, "provenance.schema.json", provenance)
                if errors:
                    raise PublishingError("; ".join(errors))
                if provenance["book_id"] != identifier:
                    raise PublishingError("Provenance book_id mismatch")
                block_ids, targets = set(), set()
                for block in provenance["blocks"]:
                    if block["block_id"] in block_ids or (block["qmd"], block["qmd_anchor"]) in targets:
                        raise PublishingError("Duplicate provenance block id or target")
                    block_ids.add(block["block_id"])
                    targets.add((block["qmd"], block["qmd_anchor"]))
                    if block["qmd"] not in metadata["chapters"]:
                        raise PublishingError("Provenance target is not a registered chapter")
                    text = safe_path(directory, block["qmd"]).read_text(encoding="utf-8")
                    if "{#" + block["qmd_anchor"] + "}" not in text:
                        raise PublishingError("Provenance anchor is missing")
                    source = block["source"]
                    if source["type"] != metadata["source"]["type"]:
                        raise PublishingError("Original/PDF provenance type mismatch")
                    if source["type"] == "pdf":
                        if source["pdf_sha256"] != metadata["source"]["sha256"]:
                            raise PublishingError("PDF provenance hash mismatch")
                        x1, y1, x2, y2 = source["bbox"]
                        if x1 >= x2 or y1 >= y2:
                            raise PublishingError("Invalid bbox ordering")
                for reason in eligibility(metadata):
                    add("ineligible", location, reason, "error" if strict else "warning")
                if any(block["review_state"] != "verified" for block in provenance["blocks"]):
                    add("unreviewed-provenance", location, "Source mappings still need review", "error" if strict else "warning")
                evidence = metadata["review"].get("evidence_path")
                if evidence:
                    record = safe_path(root, evidence)
                    if not evidence.startswith("docs/reviews/") or record.suffix != ".md" or not record.is_file() or not record.read_text(encoding="utf-8").strip():
                        raise PublishingError("Review evidence must be a nonempty docs/reviews/*.md record")
                books.append(Book(directory, metadata))
            except (OSError, ValueError, TypeError, yaml.YAMLError, PublishingError) as error:
                add("invalid-book", location, str(error))
        check_qmd(safe_path(root, "portal/about.qmd"))
    except (OSError, ValueError, TypeError, yaml.YAMLError, PublishingError) as error:
        add("invalid-registry", registry, str(error))
    return books, issues


def write_report(path: Path, issues: list[Issue], **details: Any) -> dict:
    report = {"ok": not any(i.severity == "error" for i in issues),
              "issues": [asdict(i) for i in issues], **details}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
