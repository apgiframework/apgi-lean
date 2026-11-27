"""TC-26 (first slice): the Master Prediction Register (OSF Table 15) of the locked pre-registration.

specification/hypotheses.json holds one record per table row, cells verbatim. extract_sources.py --corpus
verifies every row cell for cell against the sha256-pinned SRC-OSF PDF and that the rows reproduce the table
exactly; these tests check that the committed extraction report covers the current records, that the literal
readings (tier, label, codes) follow from the cells, that every prediction code cited elsewhere in the
registry is registered, and, where the untracked v1.2 draft is present, that the draft's copy of the table
still equals the locked record (any change needs an amendment, B-14).
"""
from __future__ import annotations

import json
import re

import pytest

import check_consistency as CC
import registry
from extract_sources import HYP_COLUMNS, draft_table_rows, hypothesis_hash

H = registry.load("hypotheses.json")
TABLE, PREDS = H["table"], H["predictions"]
REPORT = registry.ROOT / "verification" / "reports" / "extraction.json"
CODE = re.compile(r"^(?:[0-7]\.[A-Z]|MS-H[0-9])$")


def expand(pred_id: str) -> list[str]:
    m = re.fullmatch(r"(\d)\.([A-Z])–\1\.([A-Z])", pred_id)
    if m:
        return [f"{m[1]}.{chr(c)}" for c in range(ord(m[2]), ord(m[3]) + 1)]
    return [c.strip() for c in pred_id.split(",")]


def test_every_row_is_verified_against_the_locked_record():
    """The committed extraction report verifies the whole table and every current record (hash match)."""
    rep = json.loads(REPORT.read_text(encoding="utf-8"))
    hyp = rep["hypotheses"]
    assert hyp["table"]["status"] == "verified", hyp["table"]["problems"]
    assert hyp["table"]["rows"] == len(PREDS)
    src = {s["id"]: s for s in registry.load("source-manifest.json")["sources"]}[TABLE["source"]]
    pin = rep["source_pins"][TABLE["source"]]
    assert pin["found"] and pin["sha256"] == src["sha256"]
    assert set(hyp["predictions"]) == {p["id"] for p in PREDS}
    for p in PREDS:
        e = hyp["predictions"][p["id"]]
        assert e["status"] == "verified", (p["id"], e["detail"])
        assert e["record_hash"] == hypothesis_hash(p), f"{p['id']} changed since extraction"


def test_consistency_check_is_clean():
    assert CC.hypothesis_check() == []


def test_codes_follow_from_the_pred_id_cell():
    ids = [p["id"] for p in PREDS]
    assert len(ids) == len(set(ids))
    codes = [c for p in PREDS for c in p["codes"]]
    assert len(codes) == len(set(codes)), "a code is registered twice"
    for p in PREDS:
        assert p["codes"] == expand(p["pred_id"]), p["id"]
        assert all(CODE.match(c) for c in p["codes"]), p["codes"]


def test_tier_and_label_are_literal_readings_of_the_severity_cell():
    """No classification is derived beyond what the Severity cell states."""
    for p in PREDS:
        sev = p["severity"]
        m = re.match(r"([AB])(?::\s*(.*))?$", sev)
        assert p["severity_tier"] == (m[1] if m else None), p["id"]
        label = "Exploratory" if sev.startswith("Exploratory") else (m[2] if m and m[2] in ("CE", "Speculative") else None)
        assert p["label"] == label, p["id"]
        assert p["severity_tier"] or p["label"] == "Exploratory", f"{p['id']}: no tier and not exploratory"


def test_every_cited_prediction_code_is_registered():
    """'Pred X.Y' cited anywhere else in the registry names a code of the Master Prediction Register."""
    registered = {c for p in PREDS for c in p["codes"]}
    for name in registry.SPEC_FILES:
        if name == "hypotheses.json" or not (registry.SPEC / name).exists():
            continue
        text = (registry.SPEC / name).read_text(encoding="utf-8")
        for code in re.findall(r"Pred ([0-7]\.[A-Z])", text):
            assert code in registered, f"{name} cites Pred {code}, which Table 15 does not register"


def test_alpha_psy_is_the_pred_1e_threshold():
    """The registry's α_psy = 10 is the registered Pred 1.E decision threshold (α_psy ≥ 10)."""
    row = next(p for p in PREDS if "1.E" in p["codes"])
    assert re.search(r"α_psy ≥ 10\b", row["classification_standard"])
    assert registry.params()["alpha_psy"]["value"] == "10"


def test_record_status_axis():
    for p in PREDS:
        assert p["record_status"] in CC.RECORD_STATUSES and p["owner"] and "approval_date" in p, p["id"]


def test_v12_draft_table_equals_the_locked_record():
    """Fidelity of the v1.2 draft: its Table 15 equals the locked register row for row, cell for cell.
    A difference is a change to a registered decision rule or classification and needs Amendment 2."""
    draft = registry.ROOT / TABLE["draft"]["file"]
    if not draft.exists():
        pytest.skip("v1.2 draft not present (untracked; local check)")
    rows = draft_table_rows(draft, TABLE["draft"]["table_heading"])
    assert [r[0] for r in rows] == [p["pred_id"] for p in PREDS]
    for r, p in zip(rows, PREDS):
        assert r == [p[c] for c in HYP_COLUMNS], p["id"]


# A number in the SSOT's condensed Table 15 that the locked Table 15 cell does not state, but another
# extraction-verified part of the same locked record does: (row, number) -> registry parameter.
SUPPORTED_ELSEWHERE = {("0.A–0.C", "100"): "bf10_threshold_pred_0B"}  # SRC-OSF p. 69, Pred 0.B criterion


def test_ssot_condensed_table_agrees_with_the_locked_record():
    """B-07 (machine half, Table 15): the SSOT's condensed copy of the register names the same codes,
    with the same severity tier and label, and states no number that the locked row (or a named,
    extraction-verified parameter of the same record) does not. Row order is not checked."""
    ssot = registry.ROOT / "docs" / "apgi-v-1-2" / "APGI-Single-Source-of-Truth.md"
    if not ssot.exists():
        pytest.skip("SSOT draft not present (untracked; local check)")
    rows = draft_table_rows(ssot, "## **Master prediction register (OSF Table 15")
    rows = [r for r in rows if r[0] != "Pred"]
    locked = {p["pred_id"]: p for p in PREDS}
    assert sorted(r[0] for r in rows) == sorted(locked)
    params = registry.params()
    num = re.compile(r"\d+(?:\.\d+)?")
    for pid, _prot, _construct, standard, severity, _hep in rows:
        p = locked[pid]
        m = re.match(r"([AB])\b", severity)
        assert (m[1] if m else None) == p["severity_tier"], pid
        label = ("Exploratory" if severity.startswith("Exploratory") else "CE" if "CE" in severity
                 else "Speculative" if "speculative" in severity.lower() else None)
        assert label == p["label"], pid
        stated = set(num.findall(p["classification_standard"] + p["construct"] + p["pred_id"]))
        for n in set(num.findall(standard)) - stated:
            pid_param = SUPPORTED_ELSEWHERE.get((pid, n))
            assert pid_param, f"{pid}: SSOT states {n}, which the locked row does not"
            q = params[pid_param]
            assert q["value"] == n and q["verification"] == "extracted"
            assert all(e["source"] == TABLE["source"] for e in q["evidence"])
