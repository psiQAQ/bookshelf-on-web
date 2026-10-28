"""Run reviewed, original static examples, never extracted reference-book code.

Use a dedicated venv with numpy==2.3.5. Each example runs with Python -I in a
fresh temporary directory and an allowlisted environment without credentials.
An audit hook rejects network/process creation and file access outside the temp
folder and Python installations. This is defense in depth for reviewed examples,
NOT an OS sandbox for arbitrary or adversarial Python/native-extension code.
Quarto and the publication pipeline do not invoke this opt-in verifier.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "books/python-for-quantum-chemistry-a-full-stack-programming-guide"

BOOTSTRAP = r'''
import os
from pathlib import Path
import sys

work = Path.cwd().resolve()
read_roots = (work, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())

def audit(event, args):
    if event.startswith("socket.") or event in {
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn", "os.exec"
    }:
        raise PermissionError("Example isolation blocks network/process creation")
    if event == "open" and not isinstance(args[0], int):
        path = Path(os.fsdecode(args[0])).resolve()
        if not any(path.is_relative_to(root) for root in read_roots):
            raise PermissionError("Example isolation blocks file access: " + str(path))
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)))
        if writing and not path.is_relative_to(work):
            raise PermissionError("Example isolation blocks writes outside temporary cwd")

sys.addaudithook(audit)
source = (work / "example.py").read_text(encoding="utf-8")
exec(compile(source, str(work / "example.py"), "exec"), globals())
'''


def examples():
    for path in sorted((BOOK / "chapters").glob("*.qmd")):
        text = path.read_text(encoding="utf-8")
        for number, match in enumerate(re.finditer(r"(?ms)^```python\n(.*?)^```", text), 1):
            source = match.group(1)
            ast.parse(source)
            yield path, number, text[:match.start()].count("\n") + 1, source


def main():
    import numpy

    records = []
    for path, number, line, source in examples():
        with tempfile.TemporaryDirectory(prefix="notes-example-") as temporary:
            work = Path(temporary)
            (work / "example.py").write_text(source, encoding="utf-8")
            (work / "bootstrap.py").write_text(BOOTSTRAP, encoding="utf-8")
            environment = {key: os.environ[key] for key in ("SystemRoot", "WINDIR") if key in os.environ}
            environment.update({"TEMP": temporary, "TMP": temporary, "HOME": temporary,
                                "USERPROFILE": temporary, "APPDATA": temporary, "LOCALAPPDATA": temporary,
                                "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})
            try:
                result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "bootstrap.py"],
                                        cwd=work, env=environment, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace", timeout=45)
                code, stdout, stderr = result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired:
                code, stdout, stderr = -1, "", "Example timed out after 45 seconds"
        record = {"chapter": path.relative_to(ROOT).as_posix(), "block": number, "line": line,
                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                  "returncode": code, "stdout": stdout, "stderr": stderr,
                  "ok": code == 0 and "FAILED (" not in stderr}
        records.append(record)
        print(f"{'PASS' if record['ok'] else 'FAIL'} {path.name} block {number}")
        if not record["ok"]:
            print(stderr)
    ok = len(records) == 26 and all(record["ok"] for record in records)
    report = {"ok": ok, "python": sys.version, "numpy": numpy.__version__, "examples": records,
              "chapter_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((BOOK / "chapters").glob("*.qmd"))},
              "limits": "Reviewed examples only; environment/file/network guards are not an OS sandbox. "
                        "Exit status and embedded assertions checked; stdout is recorded, not automatically matched."}
    destination = ROOT / "reports/notes-examples.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Examples: {len(records)}; {'PASS' if ok else 'FAIL'}; {destination}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
