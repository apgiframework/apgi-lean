"""Locate candidate evidence quotes in a pinned source (helper for registry edits).

  python find_quote.py SRC-ID REGEX [REGEX ...]   print page and text of each match
  python find_quote.py SRC-ID --check "quote" PAGE   exit 0 if the quote matches as extract_sources does
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_sources as X  # noqa: E402
from registry import load  # noqa: E402

CORPORA = [Path(r"C:\Claude\Projects\Neuro-Brain\Neuro-Input"), Path(r"C:\Claude\Projects\apgi-lake\apgi-v-1-2")]


def pages_of(sid):
    pin = next(s for s in load("source-manifest.json")["sources"] if s["id"] == sid)["sha256"]
    for f in X.iter_files([str(c) for c in CORPORA if c.exists()]):
        if X.sha256(f) == pin:
            return X.read_pages(f)
    sys.exit(f"{sid}: pinned file not found")


def main():
    sid, *rest = sys.argv[1:]
    pages = pages_of(sid)
    if rest[0] == "--check":
        q, page = X.squash(rest[1]), int(rest[2])
        ok = q in X.squash(pages[page - 1])
        print("found" if ok else "NOT FOUND", [i + 1 for i, p in enumerate(pages) if q in X.squash(p)])
        return 0 if ok else 1
    for pat in rest:
        for n, pg in enumerate(pages, 1):
            for line in pg.splitlines():
                if re.search(pat, line):
                    print(f"[{pat}] p{n}: {X.collapse(line)[:300]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
