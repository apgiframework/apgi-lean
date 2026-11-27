"""Task 54: symbols.json (TC-03), configurations.json (B-05, TC-16), revisions.json (R1–R18),
and SSOT equation coverage (B-09)."""
from pathlib import Path

import apgi_ref as R
import registry

HERE = Path(__file__).parent
P = registry.params()
E = {e["id"] for e in registry.load("equations.json")["equations"]}

# Every equation ID the SSOT v1.2 text defines (SSOT §6–§15).
SSOT_EQ = """EQ-ERR-1 EQ-PRED-1 EQ-STD-1 EQ-EMA-1 EQ-EMA-2 EQ-PREC-2 EQ-PREC-REL-1 EQ-PREC-ACH-1 EQ-PREC-SM-1
EQ-SM-1 EQ-DA-1 EQ-NE-1 EQ-DRIVE-1 EQ-EXCESS-1 EQ-LEAK-1 EQ-STEP-1 EQ-ALLO-C1 EQ-ALLO-1 EQ-ALLO-R1 EQ-ANT-1
EQ-COST-1 EQ-VAL-1 EQ-THEFF-1 EQ-URG-1 EQ-IGN-2 EQ-HAZARD-1 EQ-IGN-1 EQ-FLOOR-1 EQ-RESET-1 EQ-REF-1 EQ-OBS-1
EQ-OBS-2 EQ-CUSP-1 EQ-CUSP-2 EQ-NORM-1 EQ-GEO-1 EQ-GRAD-1 EQ-PREC-ODE-1 EQ-PSI-SMALL-1 EQ-LOOP-1 EQ-MS-1
EQ-MS-2 EQ-PSI-1 EQ-MS-3 EQ-MS-4 EQ-KUR-1 EQ-KUR-2 EQ-RES-1 EQ-RES-2 EQ-BR-1 EQ-BR-2 EQ-BR-3 EQ-LAND-1""".split()


def test_every_ssot_equation_is_registered():
    assert len(SSOT_EQ) == len(set(SSOT_EQ)) == 53
    assert sorted(set(SSOT_EQ) - E) == []


def test_symbols_unique_and_not_retired():
    S = registry.load("symbols.json")
    syms = [s["symbol"] for s in S["parameters"]] + [s["symbol"] for s in S["state_variables"]]
    assert len(syms) == len(set(syms)), "TC-03: a symbol is defined twice"
    assert {s["parameter"] for s in S["parameters"]} == set(P), "symbols.json out of step with parameters.json"
    for s in S["parameters"]:
        assert P[s["parameter"]]["symbol"] == s["symbol"]
    retired = {r["symbol"] for r in S["retired"]} | {r["id"] for r in S["retired"]}
    assert not retired & (set(syms) | set(P))
    reserved = {r["symbol"] for r in S["reserved"]}
    assert not reserved & {p["symbol"] for p in P.values()}


def test_configurations_counted_and_consistent():
    C = {c["id"]: c for c in registry.load("configurations.json")["configurations"]}
    assert set(C) == {"CFG-CORE", "CFG-CORE-R", "CFG-FULL"}
    retired = set(registry.load("configurations.json")["retired_names"])
    assert not retired & set(C)
    core = C["CFG-CORE"]
    assert core["sampling"] == "hazard" and core["channel_form"] == "additive"  # TC-16
    for cid in ("CFG-CORE", "CFG-CORE-R"):
        c = C[cid]
        assert set(c["equations"]) <= E, cid
        for pid in c["fitted"] + c.get("measured", core["measured"]):
            assert pid in P, (cid, pid)
        n_fit = len(c["fitted"]) + c["fitted"].count("eta_pred")  # η_pred is per channel
        assert c["counts"]["fitted"] == n_fit, cid
    assert core["counts"]["fixed"] == len(core["fixed"])
    assert core["counts"]["latent_states"] == len(core["latent_states"])
    assert C["CFG-CORE-R"]["counts"]["latent_states"] == len(core["latent_states"]) + 1
    for pid, key in core["fixed"].items():
        assert pid in P, pid
        if key is not None and P[pid]["value"] is not None:
            assert float(P[pid]["value"]) == float(R.CORE_DEFAULTS[key]), pid
    assert C["CFG-FULL"]["counts"] is None and C["CFG-FULL"]["unresolved_reason"]


def test_revisions_complete():
    Rv = registry.load("revisions.json")["revisions"]
    assert [r["id"] for r in Rv] == [f"R{i}" for i in range(1, 19)]
    for r in Rv:
        assert r["status"] in {"Adopted", "Open", "Recorded"}
        if r["test"]:
            file, _, fn = r["test"].partition("::")
            text = (HERE / file).read_text(encoding="utf-8")
            assert not fn or f"def {fn}(" in text, r["id"]
    assert {r["id"] for r in Rv if "Amendment required" in r["type"]} == {"R4", "R8", "R10", "R11"}


def test_label_rows_state_a_value_rule():
    """Task 54b: a parameter row with neither a value nor a range is a label row. It must state the
    rule the SSOT gives instead (computed, participant-estimated, catch-trial rate, …) and carry
    evidence, so no value is invented for it."""
    P = registry.params()
    labels = {k for k, p in P.items() if p.get("value") is None and p.get("range") is None}
    assert {"tau_min", "tau_max", "m_Psi", "K_ell", "K_ell_m", "R_L", "kappa_pop", "kappa_beh",
            "alpha_psy_log", "g_guess", "protocol_seeds"} <= labels
    for k in labels:
        assert P[k].get("value_rule"), k
        assert P[k]["evidence"] and P[k]["verification"] == "extracted", k
