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


def test_known_conflicts_still_detected():
    """Every open known conflict is still detected (vacuous once all are resolved;
    a parametrised form would turn the empty set into a skip)."""
    hits = {f["known"] for f in CC.run(write=False)["acknowledged"]}
    open_ids = {k["id"] for k in KNOWN["conflicts"] if k["status"] == "open"}
    assert open_ids <= hits


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


def test_kappa_as_dimensionless_overhead_is_rejected(tmp_path, monkeypatch):
    """The draft registry's κ (dimensionless overhead) contradicts Notation Appendix §11."""
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["kappa"].update(unit="dimensionless"))
    assert any(f["check"] == "lean_type_mismatch" and f["params"] == ["kappa"] for f in r["unacknowledged"])


def test_gamma_theta_must_be_reciprocal_of_tau_theta(tmp_path, monkeypatch):
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["tau_theta"].update(value="25"))
    assert any(f["check"] == "derived_mismatch" and "gamma_theta" in f["params"] for f in r["unacknowledged"])


def test_bf10_disagreement_would_reopen(tmp_path, monkeypatch):
    """Reintroducing the ≥10 candidate must fail: KC-BF10-0B is resolved, not open."""
    def bad(P, d):
        P["bf10_threshold_pred_0B"]["candidates"] = [{"value": "100", "source": "SRC-OSF"},
                                                     {"value": "10", "source": "SRC-OSF"}]
    r = run_mutated(tmp_path, monkeypatch, bad)
    assert any(f["check"] == "candidate_disagreement" for f in r["unacknowledged"])


def test_edited_value_invalidates_extraction(tmp_path, monkeypatch):
    """An 'extracted' value edited without re-running extraction is flagged."""
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["theta_baseline"].update(value="0.4"))
    assert any(f["check"] == "extraction_unverified" and f["params"] == ["theta_baseline"] for f in r["unacknowledged"])


def test_symbol_collision_is_rejected(tmp_path, monkeypatch):
    """ρ/κ collision: giving ρ_crit the symbol κ must fail."""
    r = run_mutated(tmp_path, monkeypatch, lambda P, d: P["rho_crit"].update(symbol="κ"))
    assert any(f["check"] == "symbol_collision" for f in r["unacknowledged"])


def test_unresolving_theta_role_is_rejected(tmp_path, monkeypatch):
    """KC-THETA-ROLE is resolved (regime label); reverting the role must fail loudly."""
    def revert(P, d):
        P["theta_operating_lower"]["role"] = "UNRESOLVED"
        P["theta_operating_upper"]["role"] = "UNRESOLVED"
    r = run_mutated(tmp_path, monkeypatch, revert)
    assert any(f["check"] == "unresolved_role" for f in r["unacknowledged"])


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


def test_retired_patterns_are_inactive():
    """KC-BT-NOTATION flagged the canonical Bₜ 91 times in the published corpus."""
    active = {p["id"] for p in KNOWN["corpus_patterns"]}
    assert all(r["id"] not in active for r in KNOWN.get("retired_patterns", []))


def test_line_wrapped_defect_is_found(tmp_path):
    """Scanning runs on collapsed page text, so a PDF line break cannot hide a defect."""
    f = tmp_path / "wrapped.txt"
    f.write_text("the Landauer limit is 2.87 ×\n10⁻²¹ J per bit\n", encoding="utf-8")
    assert {h["id"] for h in X.scan([str(f)])} == {"KC-LANDAUER-287"}


@pytest.mark.parametrize("text, unit, expected", [
    ("10⁹", None, "1000000000"), ("3 × 10³", None, "3000"), ("2.97 × 10⁻²¹", None, "2.97e-21"),
    ("10 ms", "s", "0.01"), ("300 ms", "s", "0.3"), ("0.35", "AU", "0.35"), ("100", None, "100")])
def test_parse_quantity(text, unit, expected):
    from fractions import Fraction
    assert X.parse_quantity(text, unit) == Fraction(expected)


def test_every_parameter_cites_known_sources():
    src = {s["id"] for s in registry.load("source-manifest.json")["sources"]}
    for p in registry.load("parameters.json")["parameters"]:
        for ev in p.get("evidence") or []:
            assert ev["source"] in src, (p["id"], ev["source"])


def test_spec_lean_in_sync():
    assert G.OUT.read_text(encoding="utf-8").replace("\r\n", "\n") == G.render()


def test_python_floor_matches_registry():
    assert R.THETA_FLOOR == float(registry.params()["theta_floor"]["value"])


def test_ne_bound_registry_value():
    """apgi_ref.NE_BOUND mirrors the registry clamp |γ_NE|·g_NE ≤ 0.5 (Math Spec p14)."""
    assert R.NE_BOUND == float(registry.params()["ne_subdominance_bound"]["value"])


def test_dt_rule_needs_tau_pi(tmp_path, monkeypatch):
    """KC-PRECOND-TAU-PI (resolved by τ_Π ≥ 1 s, task 31) is load-bearing: the registered
    bound discharges dt ≤ τ_Π/10; a support-only range makes the rule unverifiable again,
    and a bound that is too short makes it violated."""
    r = CC.run(write=False)
    assert not any(f["check"].startswith("precondition") and "tau_Pi" in f["params"]
                   for f in r["acknowledged"] + r["unacknowledged"])
    def support_only(P, d):
        P["tau_Pi"].update(range={"lo": "0", "hi": None, "lo_closed": False, "hi_closed": False, "kind": "support"})
    unv = run_mutated(tmp_path / "a", monkeypatch, support_only)
    assert any(f["check"] == "precondition_unverifiable" and "tau_Pi" in f["params"] for f in unv["unacknowledged"])
    def too_short(P, d):
        P["tau_Pi"].update(range={"lo": "0.05", "hi": None, "lo_closed": True, "hi_closed": False, "kind": "design_bound"})
    bad = run_mutated(tmp_path / "b", monkeypatch, too_short)
    assert any(f["check"] == "precondition_violated" and "tau_Pi" in f["params"] for f in bad["unacknowledged"])
