"""Requirement → proof traceability (requirements.json) and the TC-01 record-status axis."""
import check_consistency as CC
import registry

Q = registry.load("requirements.json")
REQS = Q["requirements"]


def test_every_conformance_test_has_a_requirement():
    """Each of TC-01 … TC-26 (SSOT §23) has exactly one requirement record with a status."""
    tcs = sorted(r["conformance_test"] for r in REQS if r["id"].startswith("REQ-TC-"))
    assert tcs == [f"TC-{n:02d}" for n in range(1, 27)]
    for r in REQS:
        assert r["kind"] in Q["kinds"] and r["status"] in Q["statuses"], r["id"]


def test_passing_requirements_have_evidence():
    """A requirement marked pass names at least one Lean declaration or test; a non-pass one states its limitation."""
    for r in REQS:
        if r["status"] == "pass":
            assert r["lean"] or r["tests"], r["id"]
        else:
            assert r["limitation"], r["id"]


def test_proved_requirements_cite_lean():
    """kind 'proved' or 'conditional' requires Lean evidence; 'empirical' never claims pass."""
    for r in REQS:
        if r["kind"] in ("proved", "conditional"):
            assert r["lean"], r["id"]
        if r["kind"] == "empirical":
            assert r["status"] != "pass", r["id"]


def test_every_record_has_status_axis():
    """TC-01: record_status, owner and approval_date on every parameter, equation, claim, bridge and requirement."""
    P = registry.load("parameters.json")["parameters"]
    E = registry.load("equations.json")["equations"]
    C = registry.load("epistemic-claims.json")["claims"]
    assert CC.record_status_check(P, E, C) == []


def test_axiom_pins_are_standard():
    """TC-22: no pinned axiom list goes beyond [propext, Classical.choice, Quot.sound]; no sorry, admit or axiom."""
    assert CC.axiom_check() == []
