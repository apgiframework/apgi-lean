"""Seeded conflict suite and regression tests for the consistency checker.

Known discrepancies must produce explicit failures (pilot criterion 2):
each test mutates a copy of the registry and asserts the checker reacts.
"""
import json
import math
import shutil
from pathlib import Path

import pytest

import apgi_ref as R
import check_consistency as CC
import extract_sources as X
import generate_lean as G
import registry

HERE = Path(__file__).resolve().parent
KNOWN = registry.load("known-conflicts.json")


def run_mutated(tmp_path, monkeypatch, mutate):
    spec = tmp_path / "specification"
    shutil.copytree(registry.SPEC, spec)
    p = spec / "parameters.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    mutate({x["id"]: x for x in data["parameters"]}, data)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(registry, "SPEC", spec)
    return CC.run(write=False)


def test_registry_state_is_fully_acknowledged():
    r = CC.run(write=False)
    assert r["unacknowledged"] == [], r["unacknowledged"]
    assert r["stale_known_conflicts"] == []


@pytest.mark.parametrize("k", [k["id"] for k in KNOWN["conflicts"] if k["status"] == "open"])
def test_known_conflict_still_detected(k):
    hits = {f["known"] for f in CC.run(write=False)["acknowledged"]}
    assert k in hits


def test_landauer_registry_value():
    P = registry.params()
    truth = float(P["k_B"]["value"]) * float(P["T_body"]["value"]) * math.log(2)
    assert truth == pytest.approx(2.9667e-21, rel=1e-4)
    assert float(P["landauer_310K"]["value"]) == pytest.approx(truth, rel=float(P["landauer_310K"]["rel_tol"]))


def test_landauer_287_is_rejected(tmp_path, monkeypatch):
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["landauer_310K"].update(value="2.87e-21"))
    assert any(f["check"] == "derived_mismatch" for f in r["unacknowledged"])


def test_287_is_the_300K_value():
    """Diagnosis of the corpus error: 2.87e-21 J is k_B·300 K·ln2."""
    assert R.landauer(300) == pytest.approx(2.871e-21, rel=1e-3)


def test_kappa_as_mol_atp_per_bit_is_rejected(tmp_path, monkeypatch):
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["kappa"].update(unit="mol_ATP/bit"))
    assert any(f["check"] == "lean_type_mismatch" and f["params"] == ["kappa"] for f in r["unacknowledged"])


def test_symbol_collision_is_rejected(tmp_path, monkeypatch):
    """ρ/κ collision: giving ρ_crit the symbol κ must fail."""
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["rho_crit"].update(symbol="κ"))
    assert any(f["check"] == "symbol_collision" for f in r["unacknowledged"])


def test_resolving_theta_role_makes_entry_stale(tmp_path, monkeypatch):
    """Resolving the θ conflict forces known-conflicts.json to be updated too."""
    def fix(P, d):
        P["theta_operating_lower"]["role"] = "regime_label"
        P["theta_operating_upper"]["role"] = "regime_label"
    r = run_mutated(tmp_path, monkeypatch, fix)
    assert "KC-THETA-ROLE" in r["stale_known_conflicts"]


def test_euler_precondition_violation(tmp_path, monkeypatch):
    def bad(P, d):
        P["dt"]["value"] = "0.5"
        P["tau_theta"]["value"] = "0.2"
    r = run_mutated(tmp_path, monkeypatch, bad)
    assert any(f["check"] == "precondition_violated" for f in r["unacknowledged"])


def test_euler_precondition_satisfied(tmp_path, monkeypatch):
    def ok(P, d):
        P["dt"]["value"] = "0.001"
        P["tau_theta"]["value"] = "0.2"
    r = run_mutated(tmp_path, monkeypatch, ok)
    assert not any(f["check"].startswith("precondition") and "dt" in f["params"]
                   for f in r["acknowledged"] + r["unacknowledged"])


def test_seeded_corpus_all_detected():
    ids = {h["id"] for h in X.scan([str(HERE / "fixtures" / "seeded_corpus.md")])}
    assert ids == {p["id"] for p in KNOWN["corpus_patterns"]}


def test_clean_corpus_no_false_positives():
    assert X.scan([str(HERE / "fixtures" / "clean_corpus.md")]) == []


def test_spec_lean_in_sync():
    assert G.OUT.read_text(encoding="utf-8").replace("\r\n", "\n") == G.render()


def test_python_floor_matches_registry():
    assert R.THETA_FLOOR == float(registry.params()["theta_floor"]["value"])
