"""Normalise per-chapter bibliography sections for the translated book.

The extracted source keeps every reference on one long line and leaves bare
``https://`` strings in the running text. Rendered as a single Markdown
paragraph the entries run together, and the URLs dominate the layout. This
script rewrites each ``## 参考文献`` section so that

* every entry is its own paragraph inside a ``.ref-list`` div (the hanging
  indent and spacing come from the book stylesheet),
* each URL becomes an inline link labelled with the site it points at (or
  ``DOI``), so the raw address never appears in the text,
* spaces the PDF typesetting inserted *inside* an address are closed up,
  ligature glyphs such as ``conﬁguration`` are folded back to ASCII, and
  page-header residue such as a trailing ``References 55`` is dropped.

Run with ``--check`` to report what would change without writing files.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide/chapters"
HEADING = "## 参考文献"
LIST_OPEN = "::: {.ref-list}"
LIST_CLOSE = ":::"

URL_RE = re.compile(r"https?://[^\s]+")
LINK_RE = re.compile(r"\[[^\]\n]*\]\(https?://[^)\s]+\)")
URL_OR_LINK_RE = re.compile(LINK_RE.pattern + "|" + URL_RE.pattern)
URL_BODY_RE = re.compile(r"[A-Za-z0-9._~/%#?=&+!-]+")
HEADER_RESIDUE_RE = re.compile(r"\s+References(?:\s+[ivxlcdm]+|\s+\d{1,3})?$", re.I)
TRAILING_PUNCTUATION = ".,;:"
LIGATURES = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
    "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st",
}
MONTHS = ("Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.")
COUNTRY_SECOND_LEVEL = {"uk", "in", "cn", "jp", "kr", "tw", "hk", "sg", "au", "nz", "za", "br", "mx", "ar", "cl"}


@dataclass
class Stats:
    chapters: int = 0
    entries: int = 0
    links: int = 0
    joined_spaces: int = 0
    ligatures: int = 0
    header_residue: int = 0
    changed_chapters: list[str] = field(default_factory=list)


def fit_ligatures(url: str) -> str:
    """Repair PDF ligature glyphs so the address actually resolves."""
    for glyph, ascii_text in LIGATURES.items():
        url = url.replace(glyph, ascii_text)
    return url


def split_url(url: str) -> tuple[str, str]:
    """Separate sentence punctuation from an address so links stay clickable."""
    core = url.rstrip(TRAILING_PUNCTUATION)
    return core, url[len(core):]


def close_gaps(line: str) -> tuple[str, int]:
    """Rejoin addresses that the PDF text layer split with a stray space.

    A space counts as part of the address when the character before it is a URL
    separator (``.``, ``_``, ``/``, ``-``) and the next token still looks like
    the remainder of that address. Month abbreviations and capitalised words
    are left alone, so ``..., Jul. 2022`` and a stray ``References`` survive.
    """
    joined = 0
    out = line
    index = 0
    while True:
        match = URL_RE.search(out, index)
        if not match:
            return out, joined
        tail = out[match.end():]
        if not tail.startswith(" "):
            index = match.end()
            continue
        token = tail[1:].split(" ")[0]
        candidate, _ = split_url(token)
        if not candidate or not URL_BODY_RE.fullmatch(candidate) or token in MONTHS:
            index = match.end()
            continue
        before = out[match.end() - 1]
        keeps_running = before in "_/-" or (before == "." and (token[0].islower() or token[0].isdigit()))
        if not keeps_running:
            index = match.end()
            continue
        out = out[:match.end()] + token + out[match.end() + 1 + len(token):]
        joined += 1
        index = match.end() + len(token)


def host_label(url: str) -> str:
    host = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
    host = re.sub(r"^www\.", "", host)
    if host in {"doi.org", "dx.doi.org"}:
        return "DOI"
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    keep = 3 if labels[-1] in COUNTRY_SECOND_LEVEL else 2
    return ".".join(labels[-keep:])


def link_urls(line: str, stats: Stats) -> str:
    """Replace every bare URL with an inline link labelled by its site."""

    def swap(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("["):
            return token
        core, tail = split_url(token)
        fixed = fit_ligatures(core)
        if fixed != core:
            stats.ligatures += 1
            core = fixed
        stats.links += 1
        return f"[{host_label(core)}]({core}){tail}"

    return URL_OR_LINK_RE.sub(swap, line)


def format_line(raw: str, stats: Stats) -> str:
    line, joined = close_gaps(raw)
    stats.joined_spaces += joined
    stripped = HEADER_RESIDUE_RE.sub("", line)
    if stripped != line:
        stats.header_residue += 1
        line = stripped
    return link_urls(line, stats).rstrip()


def format_section(lines: list[str], stats: Stats) -> list[str]:
    """Turn the reference paragraph(s) of one chapter into one entry per line."""
    entries = [format_line(line.strip(), stats) for line in lines
               if line.strip() and line.strip() not in {LIST_OPEN, LIST_CLOSE}]
    if not entries:
        return []
    stats.entries += len(entries)
    body: list[str] = []
    for entry in entries:
        body.extend(["", entry])
    return [LIST_OPEN, *body, "", LIST_CLOSE]


def format_text(text: str, stats: Stats) -> str:
    heading = re.search(rf"^{re.escape(HEADING)}\s*$", text, re.M)
    if not heading:
        return text
    rest = text[heading.end():]
    stop = re.search(r"^#{1,2} ", rest, re.M)
    body = rest[: stop.start()] if stop else rest
    remainder = rest[stop.start():] if stop else ""
    block = format_section(body.split("\n"), stats)
    if not block:
        return text
    return f"{text[:heading.start()]}{HEADING}\n\n" + "\n".join(block) + "\n\n" + remainder.lstrip("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report differences without writing")
    parser.add_argument("--chapters", type=Path, default=CHAPTERS)
    parser.add_argument("--report", type=Path, default=Path("reports/references.json"))
    args = parser.parse_args()

    stats = Stats()
    for path in sorted(args.chapters.glob("*.qmd")):
        original = path.read_text(encoding="utf-8")
        updated = format_text(original, stats)
        stats.chapters += 1
        if updated == original:
            continue
        stats.changed_chapters.append(path.name)
        if not args.check:
            path.write_text(updated, encoding="utf-8")

    report = {
        "mode": "check" if args.check else "write",
        "changed": stats.changed_chapters,
        "chapters": stats.chapters,
        "entries": stats.entries,
        "links": stats.links,
        "joined_spaces": stats.joined_spaces,
        "ligatures": stats.ligatures,
        "header_residue": stats.header_residue,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.check:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if args.check and stats.changed_chapters else 0


if __name__ == "__main__":
    raise SystemExit(main())
