"""Independent extraction from the source corpus.

Usage:
  python extract_sources.py PATH ...                scan .pdf/.docx/.md/.txt for defect patterns
  python extract_sources.py --hash PATH ...         print sha256 pins for source-manifest.json
  python extract_sources.py --corpus DIR [--corpus DIR2 ...] [--write]
                                                    verify every parameter's evidence against the
                                                    sha256-pinned documents found in DIR; --write
                                                    saves verification/reports/extraction.json

Defect scanning runs on whitespace-collapsed page text, so a pattern broken
across PDF lines is still found. Evidence verification is the per-parameter
numeric check (plan Phase 2): each evidence quote must occur on the stated
page of the pinned file, and each value it 'states' must equal the registry
value after unit scaling. The registry is never modified (plan 4: changes are
reviewed by a human); this tool only reports. Exit 1 on any defect or failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import ROOT, load  # noqa: E402

EXTS = {".md", ".txt", ".docx", ".pdf"}
REPORT = ROOT / "verification" / "reports" / "extraction.json"
PAGE_MARK = re.compile(r"<<PAGE \d+>>")
# Characters the PDF text layer drops or mangles; ignored when matching quotes.
SQUASH = re.compile(r"[\s()\[\]{}\-–—−‒-]")
MD_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|=<>~^])")
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


# ------------------------------------------------------------------ reading --
def read_pages(path: Path) -> list[str]:
    """Return the document as a list of page texts (1 page for non-PDF)."""
    suf = path.suffix.lower()
    if suf == ".pdf":
        try:
            import pypdf
        except ImportError:  # pragma: no cover - environment-dependent
            sys.exit("PDF support needs pypdf: pip install pypdf")
        return [p.extract_text() or "" for p in pypdf.PdfReader(str(path)).pages]
    if suf == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        return [re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))]
    text = path.read_text(encoding="utf-8", errors="replace")
    if suf == ".md":  # Markdown exports escape punctuation (γ\\_sig, \\[2, 7.5\\]); patterns see the plain text
        text = MD_ESCAPE.sub(r"\1", text)
    if PAGE_MARK.search(text):  # text dumps with <<PAGE n>> markers after each page
        return PAGE_MARK.split(text)[:-1] or [text]
    return [text]


def iter_files(targets: list[str]):
    for t in targets:
        p = Path(t)
        if p.is_dir():
            yield from sorted(q for q in p.rglob("*") if q.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            yield p


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def squash(s: str) -> str:
    return SQUASH.sub("", s)


# ----------------------------------------------------------------- scanning --
def active_patterns() -> list[dict]:
    return load("known-conflicts.json")["corpus_patterns"]


def scan(targets: list[str]) -> list[dict]:
    """One hit per (pattern, file, page), with the first match as context."""
    pats = active_patterns()
    hits = []
    for f in iter_files(targets):
        for n, page in enumerate(read_pages(f), 1):
            text = collapse(page)
            for p in pats:
                m = re.search(p["pattern"], text)
                if m:
                    hits.append({"id": p["id"], "file": str(f), "page": n, "severity": p["severity"],
                                 "count": len(re.findall(p["pattern"], text)),
                                 "text": text[max(0, m.start() - 60): m.end() + 60].strip(),
                                 "summary": p["summary"]})
    return hits


# --------------------------------------------------------- number handling --
UNIT_RE = re.compile(r"\s*(ms|s|AU|K|J|ATP/bit|J/bit)\s*$")


def parse_quantity(spec, registry_unit: str | None) -> Fraction:
    """'10 ms' -> 0.01 (in s); '3 × 10³' -> 3000; '2.97 × 10⁻²¹' -> 2.97e-21; '−2' -> -2.
    spec may be {'text': '200', 'unit': 'ms'} when the unit sits elsewhere in the quote."""
    if isinstance(spec, dict):
        text, unit = spec["text"], spec.get("unit")
    else:
        m = UNIT_RE.search(spec)
        text, unit = (spec[: m.start()], m.group(1)) if m else (spec, None)
    # The exponent is matched before superscripts are flattened: '10⁹' is 1e9, not 109.
    m = re.fullmatch(r"\s*([−-])?\s*([0-9][0-9.,]*)?\s*(?:[×x]\s*)?(?:10\s*([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+))?\s*", text)
    if not m or not (m.group(2) or m.group(3)):
        raise ValueError(f"cannot parse quantity {spec!r}")
    sign = -1 if m.group(1) else 1
    mant = sign * (Fraction(m.group(2).replace(",", "")) if m.group(2) else Fraction(1))
    val = mant * (Fraction(10) ** int(m.group(3).translate(SUP)) if m.group(3) else 1)
    scale = load("units.json").get("scale_to", {}).get(unit) if unit else None
    if scale and registry_unit == scale[0]:
        val *= Fraction(scale[1])
    return val


def registry_field(p: dict, field: str):
    if field == "value":
        return p.get("value")
    side = field.split(".", 1)[1]
    return (p.get("range") or {}).get(side)


def param_hash(p: dict) -> str:
    keep = {k: p.get(k) for k in ("id", "value", "range", "unit", "evidence")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ----------------------------------------------------------- verification --
def verify(corpus: Path | list[Path]) -> dict:
    sources = {s["id"]: s for s in load("source-manifest.json")["sources"]}
    by_hash = {}
    dirs = corpus if isinstance(corpus, list) else [corpus]
    for f in iter_files([str(d) for d in dirs]):
        by_hash.setdefault(sha256(f), f)
    pins, pages_cache = {}, {}
    for sid, s in sources.items():
        if s.get("sha256"):
            f = by_hash.get(s["sha256"])
            pins[sid] = {"sha256": s["sha256"], "found": f is not None, "file": f.name if f else None}
            if f is not None:
                pages_cache[sid] = [squash(pg) for pg in read_pages(f)]

    out = {}
    for p in load("parameters.json")["parameters"]:
        ev = p.get("evidence") or []
        if not ev:
            continue
        details, ok = [], True
        for e in ev:
            d = {"source": e["source"], "page": e["page"], "quote": e["quote"]}
            pages = pages_cache.get(e["source"])
            if pages is None:
                d["status"] = "source not pinned or not found in corpus"
                ok = False
            else:
                q = squash(e["quote"])
                if 1 <= e["page"] <= len(pages) and q in pages[e["page"] - 1]:
                    d["status"] = "found"
                else:
                    elsewhere = [i + 1 for i, pg in enumerate(pages) if q in pg]
                    d["status"] = f"NOT on page {e['page']}" + (f"; found on page(s) {elsewhere}" if elsewhere else "; not in document")
                    ok = False
            checks = []
            for field, spec in (e.get("states") or {}).items():
                text = spec["text"] if isinstance(spec, dict) else spec
                reg = registry_field(p, field)
                try:
                    got = parse_quantity(spec, p.get("unit"))
                    match = text in e["quote"] and reg is not None and got == Fraction(reg)
                except (ValueError, ZeroDivisionError) as exc:
                    got, match = str(exc), False
                checks.append({"field": field, "document": text, "registry": reg, "match": bool(match)})
                ok &= bool(match)
            d["values"] = checks
            details.append(d)
        out[p["id"]] = {"status": "verified" if ok else "failed", "param_hash": param_hash(p), "evidence": details}
    return {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tool": "extract_sources.py --corpus", "source_pins": pins, "parameters": out}


# --------------------------------------------------------------------- CLI --
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--corpus", action="append", help="directory searched for pinned sources (repeatable)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.hash:
        for f in iter_files(a.targets):
            print(f"{sha256(f)}  {f}")
        return 0
    if a.corpus:
        r = verify([Path(c) for c in a.corpus])
        for sid, pin in r["source_pins"].items():
            print(f"{'PIN ' if pin['found'] else 'MISS'} {sid}  {pin['file'] or pin['sha256'][:16]}")
        bad = 0
        for pid, v in r["parameters"].items():
            print(f"{'OK  ' if v['status'] == 'verified' else 'FAIL'} {pid}")
            if v["status"] != "verified":
                bad += 1
                for d in v["evidence"]:
                    print(f"       p{d['page']} {d['status']}; values {[(c['field'], c['document'], c['registry'], c['match']) for c in d['values']]}")
        if a.write:
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            print(f"wrote {REPORT.relative_to(ROOT)}")
        print(f"{len(r['parameters']) - bad} verified, {bad} failed")
        return 1 if bad or not all(p["found"] for p in r["source_pins"].values()) else 0
    hits = scan(a.targets)
    if a.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        for h in hits:
            print(f"{h['severity']} {h['id']}  {h['file']} p{h['page']}  …{h['text']}…")
        print(f"{len(hits)} defect(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
