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


def record_hash(r: dict) -> str:
    """Hash of a bridges.json record's evidence-bearing fields (statement, status, falsifier, quotes)."""
    keep = {k: r.get(k) for k in ("id", "statement", "status", "falsifier", "construct", "candidate", "limitation", "evidence")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def bridge_records() -> list[dict]:
    import registry
    if not (registry.SPEC / "bridges.json").exists():
        return []
    b = load("bridges.json")
    return b.get("bridges", []) + b.get("observables", [])


def param_hash(p: dict) -> str:
    keep = {k: p.get(k) for k in ("id", "value", "range", "unit", "evidence")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


HYP_COLUMNS = ("pred_id", "protocol", "construct", "classification_standard", "severity", "hep_dependent",
               "fallback_proxy")


def hypothesis_register() -> tuple[dict | None, list[dict]]:
    """(table description, prediction records) of specification/hypotheses.json, or (None, [])."""
    import registry
    if not (registry.SPEC / "hypotheses.json").exists():
        return None, []
    h = load("hypotheses.json")
    return h["table"], h["predictions"]


def further_registers() -> list[tuple[dict, list[dict]]]:
    """(table description, row records) of every register in hypotheses.json besides Table 15
    (OSF Tables 12 and 13, TC-26 second slice)."""
    import registry
    if not (registry.SPEC / "hypotheses.json").exists():
        return []
    return [(g["table"], g["rows"]) for g in load("hypotheses.json").get("registers", [])]


def register_hash(r: dict, columns: tuple | list) -> str:
    """Hash of a register record's verified fields: its cells, literal readings and evidence."""
    keep = {k: r.get(k) for k in ("id", *columns, "codes", "severity_tier", "label", "evidence")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def hypothesis_hash(r: dict) -> str:
    """Hash of a Table 15 record's verified fields (cells, codes, literal readings, evidence)."""
    return register_hash(r, HYP_COLUMNS)


def table_segments(table: dict, pages: list[str]) -> tuple[dict[int, str], list[str]]:
    """Squashed text of the registered table on each of its pages: from the table title (first page)
    or the repeated column header (later pages) to the end of the page or to end_before (last page)."""
    first, last = table["first_page"], table["last_page"]
    start, hdr, end = squash(table["start_after"]), squash(table["header"]), squash(table["end_before"])
    seg, problems = {}, []
    for n in range(first, last + 1):
        if not 1 <= n <= len(pages):
            problems.append(f"page {n} not in document")
            continue
        s = pages[n - 1]
        if n == first:
            k = s.find(start)
            if k < 0:
                problems.append(f"table title not on page {n}")
                continue
            s = s[k + len(start):]
        if not s.startswith(hdr):
            problems.append(f"column header not at the start of the table on page {n}")
        else:
            s = s[len(hdr):]
        if n == last:
            k = s.find(end)
            if k < 0:
                problems.append(f"end marker not on page {n}")
            else:
                s = s[:k]
        seg[n] = s
    return seg, problems


def verify_table(table: dict, rows: list[dict], pages: list[str] | None, raw: list[str] | None) -> dict:
    """Every row of a registered table occurs cell for cell, in column order, on its stated page of the
    pinned source; a row split by a page break is registered as head cells on one page and tail cells on
    the next, which must join to the full cells; and the rows reproduce the table on each page exactly,
    so no row of the source is missing from the register and none is invented."""
    cols = tuple(table["columns"])
    if raw is not None and table.get("text_layer_map"):
        # The source's table font emits private-use code points for some punctuation, which squash() would
        # delete. The map is specific to that pinned file (other PDFs use the same code points for other
        # glyphs), so it is applied to this source's raw text only, before squashing.
        glyphs = str.maketrans({int(k, 16): v for k, v in table["text_layer_map"].items()})
        pages = [squash(pg.translate(glyphs)) for pg in raw]
    out = {}
    if pages is None:
        for r in rows:
            out[r["id"]] = {"status": "failed", "record_hash": register_hash(r, cols),
                            "detail": "source not pinned or not found in corpus"}
        return {"table": {"id": table["id"], "status": "failed", "problems": ["source not pinned or not found"]},
                "rows": out}
    seg, problems = table_segments(table, pages)
    expected = {n: "" for n in seg}
    for r in rows:
        ev, why = r.get("evidence") or [], []
        if len(ev) == 1:
            n, part = ev[0]["page"], squash("".join(r[c] for c in cols))
            expected[n] = expected.get(n, "") + part
            if part not in seg.get(n, ""):
                why.append(f"row not on page {n}")
        elif len(ev) == 2 and ev[1]["page"] == ev[0]["page"] + 1:
            heads, tails = ev[0].get("cells") or [], ev[1].get("cells") or []
            if len(heads) != len(cols) or len(tails) != len(cols):
                why.append("split row needs one head and one tail per column")
            else:
                for c, h, t in zip(cols, heads, tails):
                    if squash(h + t) != squash(r[c]):
                        why.append(f"{c}: head + tail != cell")
                for e, cells in ((ev[0], heads), (ev[1], tails)):
                    part = squash("".join(cells))
                    expected[e["page"]] = expected.get(e["page"], "") + part
                    if part not in seg.get(e["page"], ""):
                        why.append(f"row part not on page {e['page']}")
        else:
            why.append("evidence must name one page, or two consecutive pages for a split row")
        out[r["id"]] = {"status": "failed" if why else "verified", "record_hash": register_hash(r, cols),
                        "pages": [e["page"] for e in ev], "detail": "; ".join(why) or None}
    firsts = [(r.get("evidence") or [{"page": 0}])[0]["page"] for r in rows]
    if firsts != sorted(firsts):
        problems.append("rows are not registered in table order (a row's first page precedes the row before it)")
    for n in seg:
        if seg[n] != expected.get(n, ""):
            problems.append(f"page {n}: registered rows do not reproduce the table "
                            f"(table {len(seg[n])} chars, rows {len(expected.get(n, ''))})")
    return {"table": {"id": table["id"], "status": "failed" if problems else "verified", "problems": problems,
                      "rows": len(rows), "pages": [table["first_page"], table["last_page"]]},
            "rows": out}


def verify_hypotheses(pages_cache: dict, raw_pages: dict | None = None) -> dict:
    """TC-26: Table 15 (the Master Prediction Register, first slice) and every further register
    (Tables 12 and 13, second slice), each verified by verify_table against its pinned source."""
    table, preds = hypothesis_register()
    if table is None:
        return {}
    raw_pages = raw_pages or {}
    t15 = verify_table(table, preds, pages_cache.get(table["source"]), raw_pages.get(table["source"]))
    out = {"table": t15["table"], "predictions": t15["rows"], "registers": {}}
    for t, rows in further_registers():
        out["registers"][t["id"]] = verify_table(t, rows, pages_cache.get(t["source"]), raw_pages.get(t["source"]))
    return out


def draft_table_rows(path: Path, heading: str) -> list[list[str]]:
    """Body rows of the first Markdown table after the line starting with `heading`, cells unescaped
    and unbolded (the v1.2 draft's copy of a registered table, for the fidelity comparison)."""
    lines = path.read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(heading))
    rows: list[list[str]] = []
    for line in lines[i + 1:]:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [MD_ESCAPE.sub(r"\1", c.strip()).replace("**", "") for c in re.split(r"(?<!\\)\|", line)[1:-1]]
        if set(cells[0]) <= set(":-") or not rows and cells[0] in ("Pred-ID", "#"):
            continue
        rows.append(cells)
    return rows


# ----------------------------------------------------------- verification --
def verify(corpus: Path | list[Path]) -> dict:
    sources = {s["id"]: s for s in load("source-manifest.json")["sources"]}
    by_hash = {}
    dirs = corpus if isinstance(corpus, list) else [corpus]
    for f in iter_files([str(d) for d in dirs]):
        by_hash.setdefault(sha256(f), f)
    pins, pages_cache, raw_cache = {}, {}, {}
    t15 = hypothesis_register()[0]
    hyp_sources = {t["source"] for t in ([t15] if t15 else []) + [g[0] for g in further_registers()]}
    for sid, s in sources.items():
        if s.get("sha256"):
            f = by_hash.get(s["sha256"])
            pins[sid] = {"sha256": s["sha256"], "found": f is not None, "file": f.name if f else None}
            if f is not None:
                raw = read_pages(f)
                pages_cache[sid] = [squash(pg) for pg in raw]
                if sid in hyp_sources:
                    raw_cache[sid] = raw

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
    records = {}
    for r in bridge_records():
        details, ok = [], True
        for e in r.get("evidence") or []:
            pages = pages_cache.get(e["source"])
            q = squash(e["quote"])
            found = pages is not None and 1 <= e["page"] <= len(pages) and q in pages[e["page"] - 1]
            details.append({"source": e["source"], "page": e["page"], "quote": e["quote"],
                            "status": "found" if found else ("source not pinned or not found in corpus" if pages is None else "NOT FOUND")})
            ok &= found
        records[r["id"]] = {"status": "verified" if ok and details else "failed", "record_hash": record_hash(r), "evidence": details}
    return {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tool": "extract_sources.py --corpus", "source_pins": pins, "parameters": out, "records": records,
            "hypotheses": verify_hypotheses(pages_cache, raw_cache)}


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
        for rid, v in r["records"].items():
            print(f"{'OK  ' if v['status'] == 'verified' else 'FAIL'} {rid}")
            if v["status"] != "verified":
                bad += 1
                for d in v["evidence"]:
                    print(f"       p{d['page']} {d['status']}: {d['quote'][:80]}")
        hyp = r["hypotheses"]
        if hyp:
            t = hyp["table"]
            print(f"{'OK  ' if t['status'] == 'verified' else 'FAIL'} {t['id']} ({t['rows']} rows, "
                  f"pages {t['pages'][0]}-{t['pages'][1]})" if "rows" in t else f"FAIL {t['id']}")
            for pr in t["problems"]:
                print(f"       {pr}")
            bad += t["status"] != "verified"
            for hid, v in hyp["predictions"].items():
                if v["status"] != "verified":
                    bad += 1
                    print(f"FAIL {hid}: {v['detail']}")
            for g in hyp.get("registers", {}).values():
                t = g["table"]
                print(f"{'OK  ' if t['status'] == 'verified' else 'FAIL'} {t['id']} ({t.get('rows')} rows, "
                      f"pages {t['pages'][0]}-{t['pages'][1]})" if "rows" in t else f"FAIL {t['id']}")
                for pr in t["problems"]:
                    print(f"       {pr}")
                bad += t["status"] != "verified"
                for rid, v in g["rows"].items():
                    if v["status"] != "verified":
                        bad += 1
                        print(f"FAIL {rid}: {v['detail']}")
        if a.write:
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            REPORT.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            print(f"wrote {REPORT.relative_to(ROOT)}")
        nh = len(hyp.get("predictions", {})) + (1 if hyp else 0) + sum(
            len(g["rows"]) + 1 for g in hyp.get("registers", {}).values())
        print(f"{len(r['parameters']) + len(r['records']) + nh - bad} verified, {bad} failed "
              f"({len(r['parameters'])} parameters, {len(r['records'])} bridge/observable records, "
              f"{nh} prediction-register records)")
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
