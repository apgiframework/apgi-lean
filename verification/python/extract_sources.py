"""Independent extraction: scan corpus documents for known defect patterns.

Usage:
  python extract_sources.py DIR_OR_FILE ...   scan .md/.txt/.docx files
  python extract_sources.py --hash DIR ...    print sha256 pins to paste into
                                              specification/source-manifest.json
The registry is never modified automatically (plan §4: changes must be
reviewable). Exit 1 if any defect pattern is found.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import load  # noqa: E402

EXTS = {".md", ".txt", ".docx"}


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    return path.read_text(encoding="utf-8", errors="replace")


def iter_files(targets: list[str]):
    for t in targets:
        p = Path(t)
        if p.is_dir():
            yield from sorted(q for q in p.rglob("*") if q.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            yield p


def scan(targets: list[str]) -> list[dict]:
    pats = load("known-conflicts.json")["corpus_patterns"]
    hits = []
    for f in iter_files(targets):
        for n, line in enumerate(read_text(f).splitlines(), 1):
            for p in pats:
                if re.search(p["pattern"], line):
                    hits.append({"id": p["id"], "file": str(f), "line": n, "severity": p["severity"],
                                 "text": line.strip()[:160], "summary": p["summary"]})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.hash:
        for f in iter_files(a.targets):
            print(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f}")
        return 0
    hits = scan(a.targets)
    if a.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for h in hits:
            print(f"{h['severity']} {h['id']}  {h['file']}:{h['line']}  {h['text']}")
        print(f"{len(hits)} defect(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
