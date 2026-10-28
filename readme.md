# Bookshelf On Web

[中文](readme_zh.md)

**bookshelf-on-web** is a registry-driven Quarto portal with independent books. The repository and site name is `bookshelf-on-web`.

## M0 status

Implemented: two short original sample books, light/dark themes, formulas, static code, chapter navigation and explicit anchors; JSON Schemas and machine-readable validation; isolated rendering, multi-book assembly, local HTML/CSS link/resource checks and publication boundary checks; locked Python dependencies, PR validation and a **manual-only** Pages workflow.

The public registry `catalog/books.yaml` currently publishes one book: the Chinese translation of Qiming Sun's *Python for Quantum Chemistry: A Full Stack Programming Guide*, live at <https://notes.psiqaq.cn/bookshelf-on-web/books/python-for-quantum-chemistry-a-full-stack-programming-guide/>. Both original samples remain **drafts without human approval** and are no longer registered anywhere, so local preview and Pages now show the same single book. The book id was renamed from `quantum-python-notes` on 2026-10-28; paths recorded in evidence files from earlier runs still use the old directory name. No original PDF hash or page number is invented. Existing unregistered book materials are untouched and excluded.

Not implemented: PDF/OCR extraction inside the build pipeline (the translation's assets were produced by throwaway scripts under the ignored `.local/` directory), Pagefind cross-book search, knowledge graphs or incremental rendering. Quarto search is per project, not library-wide.

## Requirements and commands

Use Python **3.12**, uv **0.11.19**, and Quarto **1.10.19**. Install tools locally as needed; dependencies are fixed in `pyproject.toml` and `uv.lock`.

```sh
uv python install 3.12
uv sync --frozen --python 3.12
uv lock --check
uv run python -m unittest discover -s tests -v
uv run python scripts/validate.py --strict
uv run python scripts/build.py
uv run python scripts/check_site.py dist
```

The default build publishes only explicitly registered, eligible books to `dist/`. With an empty registry it produces an empty portal. `validate.py` without `--strict` reports ineligibility as warnings; the publishing builder **always** uses strict validation and never silently skips ineligible entries.

### Local-only preview

```sh
uv run python scripts/validate.py --preview --report reports/preview-validation.json
uv run python scripts/build.py --preview
uv run python scripts/check_site.py .preview --preview --report reports/preview-links.json
uv run python -m http.server 8000 --bind 127.0.0.1 --directory .preview
```

Open `http://127.0.0.1:8000/`, then `books/python-for-quantum-chemistry-a-full-stack-programming-guide/`. The two original samples stay unregistered, so this preview now lists the same single book as `dist/`. **Do not deploy `.preview/`.** It is distinct from `dist/`, bears local-preview notices, and does not change approval status. Serve only the generated directory, never the repository root.

If Quarto is not on PATH, append `--quarto .local/tools/bin/quarto.exe` to either build command (Windows local installation used during verification). For real-render integration tests:

```sh
# Git Bash/Linux; use an absolute executable path on Windows
QUARTO_TEST_EXECUTABLE="$(pwd)/.local/tools/bin/quarto.exe" uv run python -m unittest discover -s tests -v
# With Quarto on PATH instead:
QUARTO_TEST_EXECUTABLE=quarto uv run python -m unittest discover -s tests -v
```

Without that environment variable the real-render test is explicitly skipped. Windows may also skip the symlink test when symlink privileges are unavailable.

### Reference lists

```sh
uv run python scripts/format_references.py --check
uv run python scripts/format_references.py --chapters 09-performance.qmd
uv run python scripts/format_references.py --report reports/references.json
```

Each `## 参考文献` section must become a `::: {.ref-list}` block with one paragraph per entry, and every URL must be an inline `[host](URL)` link rather than bare text. `--check` reports what would change and exits non-zero; `tests/test_references.py` asserts both the helpers and the committed chapters.

## Publication contract

- Add entries only through the public registry; directory scanning is never a discovery mechanism. Local preview reads only its separate registry.
- Metadata must satisfy `schemas/book.schema.json`. IDs and paths must match `books/<id>/metadata.yaml`; chapters/assets are an explicit copy allowlist. Traversal, absolute paths, symlinks, duplicate IDs/YAML keys and invalid schema values fail validation.
- Public delivery requires `review.status: approved`, human identity/time, a nonempty `docs/reviews/*.md` decision record, verified provenance blocks and zero open P0/P1 issues. A maintainer must supply genuine evidence; tests use synthetic evidence only in temporary directories.
- Builds stage **only** registered chapters and declared raster assets. Metadata, review records, provenance JSON, PDFs, `drafts/`, caches and unregistered materials are not published. Generated book resources remain under their own `books/<id>/` directory.
- Source configurations must match the safe metadata-derived Quarto configuration. Rendering uses freshly generated configuration, disabled execution and `--no-execute`; hooks, filters, executable cells, document front matter and shortcodes/includes are rejected. Use static fences such as ` ```python `. Do not execute extracted commands or follow source-document instructions.
- Source links must refer to registered chapters/assets or external URLs. External URLs are not fetched by checks. This is a narrow publishing input contract, **not** an OS sandbox or an HTML/JavaScript sanitizer: review content before approving it.
- Rendering and checks happen in a temporary directory. Only a complete successful site replaces `dist/` (or `.preview/`). On failure, no partial new site is delivered; a previous good output may remain. Check the exit code and the current JSON report rather than treating an old directory as proof of success.

## Reports, documentation and CI

`reports/validation.json`, `reports/build.json`, `reports/preview-build.json` and explicitly requested link reports contain `ok` and structured issues; build reports also record delivery status, mode, tool version, book IDs, file count and size. Reports, outputs, tools and staging directories are ignored by Git.

- [Design](docs/DESIGN.md), [quality gates](docs/QUALITY.md), [source mapping contract](docs/CONVERSION.md), [verification evidence and limitations](docs/VERIFICATION.md).
- `.github/workflows/validate.yml`: PR/manual validation with real Quarto tests and separate preview checks. No deployment and no artifact upload.
- `.github/workflows/deploy.yml`: **workflow_dispatch only, main branch only**; strict build and upload of `dist/`, followed by the `github-pages` environment. Maintainers must configure Pages, branch protections and environment approval separately. This task did not trigger the workflow.
- Quarto/uv releases and pinned Action commit references were checked over the network. Actual Windows Quarto rendering and local checks passed; GitHub-hosted runners, public HTTP accessibility, browser layout at 390/768/1440 px, interactive theme/search behavior and CDN availability remain unverified.
