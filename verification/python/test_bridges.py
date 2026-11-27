"""Bridge and measurement assumptions (bridges.json) and the Apgi/Epistemic.lean twins.

A bridge is an assumption, not a result. These tests check that the registry never presents
one as calibrated, that every record is complete, and that apgi_ref.kappa_verdict implements
the registered κ calibration rule exactly as Apgi/Epistemic.lean states it.
"""
from hypothesis import given
from hypothesis import strategies as st

import apgi_ref as R
import registry

B = registry.load("bridges.json")
RECORDS = B["bridges"] + B["observables"]


def test_records_complete():
    """Every record has an id, a record status, an owner, SSOT evidence, and either a falsifier or a reason it has none."""
    ids = [r["id"] for r in RECORDS]
    assert len(ids) == len(set(ids))
    for r in RECORDS:
        assert r["record_status"] and r["owner"] and r["evidence"], r["id"]
        assert r.get("falsifier") or r.get("falsifier_unresolved_reason"), r["id"]
    for r in B["bridges"]:
        assert r["status"] in B["statuses"], r["id"]


def test_no_calibration_map_registered():
    """Lean: Apgi.tier_exit_needs_au_inverse. Leaving Tier 3 needs a constant with AU⁻¹; units.json registers none,
    so no record may claim a calibrated Tier-3 bridge."""
    U = registry.load("units.json")
    assert U["calibration_maps"] == []
    assert next(r for r in B["bridges"] if r["id"] == "BR-T3-T2")["status"] == "unresolved"
    assert not any(o["validated"] for o in B["observables"])


def test_kappa_has_no_value():
    """CL-8 / BR-KAPPA-SYN: κ has no canonical value in the registry, and the bridge is inert."""
    P = registry.params()
    assert P["kappa"]["value"] is None
    assert next(r for r in B["bridges"] if r["id"] == "BR-KAPPA-SYN")["status"] == "inert"


iv = st.tuples(st.floats(0, 1e6), st.floats(0, 1e6)).map(lambda t: (min(t), max(t)))


@given(st.lists(iv, max_size=6))
def test_kappa_rule_twin(ivs):
    """Lean: Apgi.kappa_single_never_retires, kappa_inert, kappa_consistent_not_retires, kappa_straddle_not_outside."""
    v = R.kappa_verdict(ivs)
    if len(ivs) <= 1:
        assert v != "retired"
    if not ivs:
        assert v == "indeterminate"
    lo, hi = R.KAPPA_BAND
    if v == "bridge-consistent":
        assert len(ivs) >= 2 and all(lo <= a and b <= hi for a, b in ivs)
    straddling = [x for x in ivs if x[0] <= hi and lo <= x[1]]
    if len(ivs) - len(straddling) < 2:
        assert v != "retired"
