"""TC-26 (second slice): OSF Tables 12 and 13 of the locked pre-registration.

specification/hypotheses.json `registers` holds the falsifiable hypothesis register (Table 12) and the
non-falsifiable, conditional or asymmetric commitments (Table 13), one record per row, cells verbatim.
extract_sources.py --corpus verifies every row cell for cell against the sha256-pinned SRC-OSF PDF and that
the rows reproduce each table exactly. These tests check that the committed report covers the current
records; that codes and tiers are literal readings of their cells; that the two tables partition H1-H15;
that every Table 12 code is registered in Table 15 and that the tier disagreements between the two tables
are exactly the acknowledged conflicts (KC-OSF-TIER-1F, KC-OSF-TIER-H5); that registry citations of H
numbers and the α_DFA band agree with the locked rows; and, where the untracked drafts exist, that the v1.2
draft's copies equal the locked record and the SSOT's condensations agree with it (B-07, machine half).
"""
from __future__ import annotations

import json
import re

import pytest

import check_consistency as CC
import registry
from extract_sources import draft_table_rows, register_hash

H = registry.load("hypotheses.json")
T15 = H["predictions"]
REG = {g["table"]["id"]: g for g in H.get("registers", [])}
T12, T13 = REG["OSF-T12"], REG["OSF-T13"]
REPORT = registry.ROOT / "verification" / "reports" / "extraction.json"
SSOT = registry.ROOT / "docs" / "apgi-v-1-2" / "APGI-Single-Source-of-Truth.md"

# Codes read by hand from each Pred-ID cell of the locked PDF (pp. 43-50); the oracle for codes.
CODES = {"H1": ["1.C"], "H2": ["0.A", "0.B", "0.C"], "H3": ["1.E"], "H4": ["1.F"],
         "H5": ["3.A", "3.B", "3.C", "3.D"], "H6": ["4.A"], "H8": ["MS-H1"], "H9": ["MS-H2"], "H11": ["5.B"],
         "H12": ["6.A", "6.B", "6.C"], "H13": [], "H14": ["7.A", "7.G"], "H7": [], "H10": [], "H15": []}
# Acknowledged tier disagreements between Table 12 and Table 15 (known-conflicts.json, owner Uxod).
TIER_CONFLICTS = {"1.F": "KC-OSF-TIER-1F", "3.C": "KC-OSF-TIER-H5", "3.D": "KC-OSF-TIER-H5"}


def rows(g):
    return g["rows"]


@pytest.mark.parametrize("tid", ["OSF-T12", "OSF-T13"])
def test_register_is_verified_against_the_locked_record(tid):
    rep = json.loads(REPORT.read_text(encoding="utf-8"))
    g, got = REG[tid], rep["hypotheses"]["registers"][tid]
    assert got["table"]["status"] == "verified", got["table"]["problems"]
    assert got["table"]["rows"] == len(g["rows"])
    src = {s["id"]: s for s in registry.load("source-manifest.json")["sources"]}[g["table"]["source"]]
    assert rep["source_pins"][g["table"]["source"]]["sha256"] == src["sha256"]
    assert set(got["rows"]) == {r["id"] for r in g["rows"]}
    for r in g["rows"]:
        e = got["rows"][r["id"]]
        assert e["status"] == "verified", (r["id"], e["detail"])
        assert e["record_hash"] == register_hash(r, g["table"]["columns"]), f"{r['id']} changed since extraction"


def test_consistency_check_is_clean():
    assert CC.hypothesis_check() == []


def test_ids_and_columns():
    for g in (T12, T13):
        cols = g["table"]["columns"]
        for r in g["rows"]:
            assert r["id"] == f"{g['table']['id'].replace('OSF-', '')}-{r['h']}"
            assert all(isinstance(r[c], str) for c in cols), r["id"]
            assert r["record_status"] in CC.RECORD_STATUSES and r["owner"] and "approval_date" in r


def test_codes_are_the_pred_id_cell_read_literally():
    for r in rows(T12) + rows(T13):
        assert r["codes"] == CODES[r["h"]], r["id"]
        for c in r["codes"]:
            assert (f"Pred {c}" in r["pred_id"] or c in r["pred_id"]
                    or re.search(rf"Pred {c[0]}\.[A-Z]–{c[0]}\.[A-Z]|\+ {re.escape(c)}", r["pred_id"])), (r["id"], c)


def test_severity_tier_is_the_first_letter_of_the_severity_cell():
    for r in rows(T12):
        assert r["severity_tier"] == r["severity"][0] and r["severity_tier"] in "AB", r["id"]
    assert all("severity" not in r for r in rows(T13)), "Table 13 has no Severity column"


def test_tables_12_and_13_partition_h1_to_h15():
    """H1-H15 each appear exactly once: falsifiable ones in Table 12, the rest in Table 13."""
    h12, h13 = [r["h"] for r in rows(T12)], [r["h"] for r in rows(T13)]
    assert sorted(h12 + h13, key=lambda h: int(h[1:])) == [f"H{i}" for i in range(1, 16)]
    assert h13 == ["H7", "H10", "H15"]
    assert all(r["falsifier"].strip() for r in rows(T12)), "every Table 12 row states a falsifier"


def test_table13_commitments_name_no_core_battery_code():
    """Table 13 entries are excluded from the confirmatory falsifier set: none names a Table 15 code."""
    t15 = {c for p in T15 for c in p["codes"]}
    for r in rows(T13):
        assert not set(re.findall(r"[0-7]\.[A-Z]|MS-H\d", r["pred_id"])) & t15, r["id"]


def test_table12_codes_are_registered_in_table15():
    t15 = {c for p in T15 for c in p["codes"]}
    for r in rows(T12):
        assert set(r["codes"]) <= t15, r["id"]


def test_tier_disagreements_are_exactly_the_acknowledged_conflicts():
    """The locked record is read, not repaired: every Table 12 / Table 15 tier disagreement is detected and
    acknowledged as an open author item, and no other disagreement exists."""
    found = CC.register_tier_check()
    assert {f["check"] for f in found} <= {"register_tier_conflict"}
    assert {c for f in found for c in f["params"]} == set(TIER_CONFLICTS)
    known = {k["id"]: k for k in registry.load("known-conflicts.json")["conflicts"]}
    for code, kid in TIER_CONFLICTS.items():
        assert known[kid]["status"] == "open" and code in known[kid]["params"]
    ack, unack, stale = CC.reconcile(found, list(known.values()))
    assert not unack and len(ack) == len(found)


def test_registry_citations_of_h_numbers_name_the_right_table():
    """'OSF Table 13 H7' and 'OSF H10' in the registry name commitments registered in Table 13."""
    in13 = {r["h"] for r in rows(T13)}
    for name in registry.SPEC_FILES:
        if name == "hypotheses.json" or not (registry.SPEC / name).exists():
            continue
        text = (registry.SPEC / name).read_text(encoding="utf-8")
        for h in re.findall(r"OSF Table 13 (H\d+)", text):
            assert h in in13, f"{name} cites Table 13 {h}"
        for h in re.findall(r"OSF (H\d+)\b", text):
            assert h in in13 | {r["h"] for r in rows(T12)}, f"{name} cites OSF {h}"


def test_alpha_dfa_band_and_falsifier_are_the_h8_row():
    """The SSOT-sourced α_DFA band [0.85, 0.95] and its falsifier < 0.70 are the locked H8 (MS-H1) row."""
    h8 = next(r for r in rows(T12) if r["h"] == "H8")
    p = registry.params()["alpha_DFA"]
    assert (p["range"]["lo"], p["range"]["hi"]) == ("0.85", "0.95")
    assert "α_DFA ≈ 0.85–0.95 broadband" in h8["benchmark"]
    assert re.search(r"α_DFA < 0\.70\b", h8["falsifier"]) and "< 0.70" in p["definition"]


def test_alpha_psy_is_the_h3_benchmark():
    h3 = next(r for r in rows(T12) if r["h"] == "H3")
    assert re.search(r"α_psy ≥ 10\b", h3["hypothesis"]) and re.search(r"α_psy ≥ 10\b", h3["benchmark"])
    assert registry.params()["alpha_psy"]["value"] == "10"


@pytest.mark.parametrize("tid", ["OSF-T12", "OSF-T13"])
def test_v12_draft_table_equals_the_locked_record(tid):
    """Fidelity of the v1.2 draft: its copy of the table equals the locked register cell for cell."""
    g = REG[tid]
    draft = registry.ROOT / g["table"]["draft"]["file"]
    if not draft.exists():
        pytest.skip("v1.2 draft not present (untracked; local check)")
    got = draft_table_rows(draft, g["table"]["draft"]["table_heading"])
    assert [r[0] for r in got] == [r["h"] for r in g["rows"]]
    for d, r in zip(got, g["rows"]):
        assert d == [r[c] for c in g["table"]["columns"]], r["id"]


NUM = re.compile(r"\d+(?:\.\d+)?")
SECTION_REF = re.compile(r"§\s*\d+(?:\.\d+)*")
# A number the SSOT writes as a digit where the locked cell writes a word: (H, number) -> locked wording.
AS_WORD = {("H2", "2"): "Two or more retention criteria", ("H8", "2"): "Two resting-state datasets"}


def numbers(text: str) -> set[str]:
    return set(NUM.findall(SECTION_REF.sub("", text)))


def condensed(heading: str) -> list[list[str]]:
    return [r for r in draft_table_rows(SSOT, heading) if r[0] != "H"]


def ssot_codes(cell: str) -> list[str]:
    out = []
    for part in re.split(r";\s*", cell):
        m = re.fullmatch(r"([0-7])\.([A-Z])–\1\.([A-Z])", part.strip())
        out += ([f"{m[1]}.{chr(c)}" for c in range(ord(m[2]), ord(m[3]) + 1)] if m
                else re.findall(r"[0-7]\.[A-Z]|MS-H\d", part))
    return out


def test_ssot_condensed_table12_agrees_with_the_locked_record():
    """B-07 (machine half, Table 12): the SSOT's condensation names the same hypotheses with the same codes
    and severity tier, and states no number that the locked row does not (SSOT section references aside)."""
    if not SSOT.exists():
        pytest.skip("SSOT draft not present (untracked; local check)")
    got = condensed("## **Falsifiable hypothesis register (OSF Table 12")
    locked = {r["h"]: r for r in rows(T12)}
    assert [r[0] for r in got] == list(locked)
    for h, pid, hyp, bench, fals, min_n, sev in got:
        r = locked[h]
        assert ssot_codes(pid) == r["codes"], h
        assert sev[0] == r["severity_tier"], h
        cells = " ".join(r[c] for c in T12["table"]["columns"])
        for n in numbers(" ".join((hyp, bench, fals, min_n))) - numbers(cells):
            assert AS_WORD.get((h, n)) and AS_WORD[(h, n)] in cells, f"{h}: SSOT states {n}"


def test_ssot_condensed_table13_agrees_with_the_locked_record():
    if not SSOT.exists():
        pytest.skip("SSOT draft not present (untracked; local check)")
    got = condensed("## **Non-falsifiable, conditional or asymmetric commitments (OSF Table 13")
    locked = {r["h"]: r for r in rows(T13)}
    assert [r[0] for r in got] == list(locked)
    for h, ident, commitment, status in got:
        r = locked[h]
        assert r["pred_id"].startswith(ident), h
        stated = numbers(" ".join(r[c] for c in T13["table"]["columns"]))
        assert numbers(" ".join((ident, commitment, status))) <= stated, h
