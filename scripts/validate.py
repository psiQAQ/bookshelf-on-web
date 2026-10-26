"""Validate the explicit registry and emit machine-readable diagnostics."""
import argparse
from pathlib import Path

try:
    from .publishing import ROOT, validate, write_report
except ImportError:
    from publishing import ROOT, validate, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Block every registered but ineligible book")
    mode.add_argument("--preview", action="store_true", help="Validate the isolated local-preview registry")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/validation.json")
    args = parser.parse_args()
    books, issues = validate(preview=args.preview, strict=args.strict)
    report = write_report(args.report, issues, mode="local-preview" if args.preview else "publish", strict=args.strict,
                          books=[book.slug for book in books])
    print(f"Validation: {'PASS' if report['ok'] else 'FAIL'}; {len(issues)} issue(s); {args.report}")
    for issue in issues:
        print(f"{issue.severity}: {issue.code}: {issue.path}: {issue.message}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
