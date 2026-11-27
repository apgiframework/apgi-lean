"""Second production package: apgi_core in apgiframework/apgi-validation (task 19).

apgi_core implements the spec's ignition, threshold and reset equations
independently of apgi-implementation and backs the Validation/Falsification
protocols, so it is held to the same registry. The commit is pinned in
known-conflicts.json 'production_secondary'.

Set APGI_VALIDATION_PATH to a checkout of that commit and run this module on
its own (both production repositories ship top-level packages such as utils,
so they cannot share one interpreter):

    APGI_VALIDATION_PATH=... python -m pytest -q test_production_validation.py

Known divergences are strict xfails tagged PV-*, as in test_production.py.
"""
import os
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import apgi_ref as R
import registry

VAL = os.environ.get("APGI_VALIDATION_PATH")
if not VAL or not (Path(VAL) / "apgi_core" / "model.py").exists():
    pytest.skip("APGI_VALIDATION_PATH does not point at an apgi-validation checkout", allow_module_level=True)
if os.environ.get("APGI_IMPL_PATH"):
    pytest.skip("run with APGI_VALIDATION_PATH only; APGI_IMPL_PATH puts a second 'utils' package on sys.path",
                allow_module_level=True)
sys.path.insert(0, VAL)
M = pytest.importorskip("apgi_core.model")
F = pytest.importorskip("apgi_core.full_model")
SETTINGS = pytest.importorskip("utils.apgi_settings").APGISettings

P = registry.params()
SEC = registry.load("known-conflicts.json")["production_secondary"]
DIV = {d["id"]: d for d in SEC["divergences"]}
TH = P["theta_baseline"]["range"]
TH_LO, TH_HI = float(TH["lo"]), float(TH["hi"])


def divergence(pv_id):
    """open → strict xfail; declared_variant → skipped (the code is labelled as not the minimal core,
    see test_declared_variants_are_labelled); resolved → must pass."""
    d = DIV[pv_id]
    if d["status"] == "declared_variant":
        return pytest.mark.skip(reason=f"{pv_id}: declared variant ({d.get('resolution', '')})")
    return pytest.mark.xfail(d["status"] == "open", strict=True, reason=f"{pv_id}: {d['summary']}")


def test_declared_variants_are_labelled():
    """SSOT §9: a module that is not the minimal core carries its model form, so no result from it can
    pass as a minimal-core prediction (SSOT-V1: apgi_core.model is the energy-form variant)."""
    for d in DIV.values():
        if d["status"] == "declared_variant":
            mod = pytest.importorskip(d["module"])
            assert getattr(mod, "MODEL_FORM", None) == d["model_form"], d["id"]


# --------------------------------------------- equivalence with apgi_ref ----
@given(st.floats(-1e3, 1e3), st.floats(-1e3, 1e3))
def test_ignite_matches_reference(S, theta):
    """EQ-IGN-1. Lean: Apgi.ignites_antitone_threshold (via apgi_ref.ignites)."""
    assert M.ignite(S, theta) == R.ignites(S, theta)


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(2.0, 7.5))
def test_ignition_probability_matches_reference(S, theta, gamma_sig):
    """EQ-IGN-2: σ(α(S − θ)) with α = γ_sig in the registered range [2, 7.5] /AU."""
    assert M.ignition_probability(S, theta, gamma_sig) == pytest.approx(
        R.ignition_prob(gamma_sig, S, theta), rel=1e-12, abs=1e-15)


def test_model_defaults_in_registry_ranges():
    """apgi_core/model.py APGIConfig: dt₀ = 10 ms, θ₀ in band, γ_sig in range, τ_θ in range."""
    cfg = M.APGIConfig()
    assert cfg.dt == float(P["dt"]["value"])
    assert TH_LO <= cfg.theta0 <= TH_HI
    assert float(P["gamma_sig"]["range"]["lo"]) <= cfg.alpha <= float(P["gamma_sig"]["range"]["hi"])
    assert float(P["tau_theta"]["range"]["lo"]) <= cfg.tau_theta <= float(P["tau_theta"]["range"]["hi"])
    assert cfg.dt <= cfg.tau_S / 10


# ------------------------------------------------------ known divergences ----
@divergence("PV-THETA-SCALE")
def test_baseline_thresholds_in_published_band():
    assert TH_LO <= SETTINGS().theta0 <= TH_HI
    assert TH_LO <= F.APGIParameters().theta_t0 <= TH_HI


@divergence("PV-CLIP")
def test_theta_floor_matches_registry():
    floor = float(P["theta_floor"]["value"])
    assert M.enforce_stability({"S": 0.0, "theta": -1.0, "Pi_e": 1.0, "Pi_i": 1.0})["theta"] == floor
    assert SETTINGS().theta_min == floor


@divergence("PV-HAZARD")
def test_full_model_ignition_is_dt_invariant():
    """Release v1.1: ignition is drawn through 1 − exp(−r_max·Bₜ·dt). The full model draws
    Bernoulli(P) per step, so a step taken as two half-steps fires with a different probability."""
    import inspect

    src = inspect.getsource(F.APGIFullDynamicModel.step)
    assert "rng.random() < prob_ignition" not in src


@divergence("PV-DT")
def test_full_model_step_rule():
    p = F.APGIParameters()
    assert p.delta_t <= p.tau / 10


# ------------------------------------- SSOT v1.2 minimal core (task 53) ----
@divergence("SSOT-V1")
def test_model_accumulates_signal():
    """EQ-LEAK-1: S(t+1) depends on S(t). model.py recomputes S from the current z alone."""
    m1, m2 = M.APGIModel(), M.APGIModel()
    m1.step(1.0)
    m2.step(1.0)
    m2.S += 5.0
    m1.step(0.5)
    m2.step(0.5)
    assert m1.S != pytest.approx(m2.S)


@divergence("SSOT-V1")
def test_model_z_excludes_current_sample():
    """EQ-STD-1: ε(t) is standardized before it enters the running statistics."""
    import inspect

    src = inspect.getsource(M.APGIModel.step)
    assert src.index("self.stats_e.z(eps)") < src.index("self.stats_e.update(eps)")


@divergence("SSOT-V2")
def test_full_model_drive_is_excess_centered():
    """EQ-DRIVE-1 / EQ-EXCESS-1: |ε| = m₀ in both channels gives zero drive, so from S = 0 the
    next S is 0."""
    f = F.APGIFullDynamicModel(seed=10101)
    f.state.S = 0.0
    assert f.signal_accumulation(1.0, 1.0, R.M0, R.M0, beta=1.0) == pytest.approx(0.0, abs=1e-12)


@divergence("SSOT-V2")
def test_full_model_uses_exact_leak_weight():
    """EQ-LEAK-1: S(t+1) = (1 − λ)·S(t) + λ·S_inst, λ = 1 − e^(−Δt/τ); the fixed point is S_inst.
    Checked on the increment from S = 0, which is λ·S_inst whatever the drive's centring."""
    f = F.APGIFullDynamicModel(seed=10101)
    p = f.params
    lam = R.leak_gain(p.delta_t, p.tau)
    f.state.S = 0.0
    a = f.signal_accumulation(1.0, 1.0, 3.0, 3.0, beta=1.0)
    f.state.S = 1.0
    b = f.signal_accumulation(1.0, 1.0, 3.0, 3.0, beta=1.0)
    assert b - a == pytest.approx(1.0 - lam, rel=1e-12)  # retention e^(−Δt/τ) = 1 − λ (holds today)
    s_inst = {(p.we + p.wi) * 3.0, (p.we + p.wi) * (3.0 - R.M0)}  # uncentered or centered drive
    assert any(a == pytest.approx(lam * s, rel=1e-9) for s in s_inst)


# ------------------------------- TC-04: apgi_core.full_model trajectory (task 62b) ----
def _full_model_pair(n=600, seed=404):
    """Reference run (CORE_DEFAULTS) and the full model driven by the reference's own Π and z.

    full_model takes Π and ε as inputs, so the reference supplies them: we = wi = 0.5 and
    Π = 2·Π_rel make its drive we·Π·(|z| − m₀) equal to EQ-DRIVE-1's Π_rel·|z|_ex per channel
    (β = 1). Both see the same uniform draws through the dt-invariant hazard."""
    import numpy as np

    g = np.random.default_rng(seed)
    xe = g.standard_normal(n) + np.where((np.arange(n) % 200) >= 120, 2.0, 0.0)
    xi, us = g.standard_normal(n), g.random(n)
    rp = dict(R.CORE_DEFAULTS)
    par = F.APGIParameters(delta_t=rp["dt"], tau=rp["tau_S"], we=0.5, wi=0.5, theta_t0=rp["theta0"],
                           k=rp["gamma_sig"], beta=1.0, r_max=rp["r_max"], tau_theta=rp["tau_theta"])

    class Draws:
        def __init__(self, u):
            self._it = iter(u)

        def random(self):
            return next(self._it)

    f = F.APGIFullDynamicModel(par, rng=Draws(us))
    s = R.core_state(rp)
    f.state.S, f.state.theta_t = s["S"], s["theta"]
    rows = []
    for k in range(n):
        s, log = R.core_step(s, float(xe[k]), float(xi[k]), rp, u=float(us[k]))
        st = f.step(2 * log["pi_e_eff"] / rp["pi_bar_e"], 2 * log["pi_i_eff"] / rp["pi_bar_i"],
                    log["z_e"], log["z_i_eff"])
        rows.append(dict(ref_S=s["S"], ref_theta=s["theta"], ref_Bt=log["B_prop"], ref_B=log["B"],
                         fm_S=float(st.S), fm_theta=float(st.theta_t), fm_Bt=float(st.ignition_probability),
                         fm_B=int(st.I)))
    return rows


def test_full_model_signal_matches_reference_until_first_event():
    """What full_model shares with the SSOT core (SSOT-V2, resolved): drive and exact leak. Until
    the first ignition the accumulated S agrees with apgi_ref step for step."""
    rows = _full_model_pair()
    first = next(k for k, r in enumerate(rows) if r["ref_B"] or r["fm_B"])
    assert first > 10
    for r in rows[:first]:          # the event step itself applies the reset (EQ-RESET-1)
        assert r["fm_S"] == pytest.approx(r["ref_S"], rel=1e-9, abs=1e-12)


@divergence("SSOT-V3")
def test_full_model_matches_reference_trajectory():
    """TC-04 for apgi_core.full_model: S, θ, Bₜ and B(t) equal apgi_ref.core_step within
    tolerance on 600 seeded steps (the SSOT §8 order, EQ-RESET-1, EQ-ALLO-1)."""
    for k, r in enumerate(_full_model_pair()):
        assert r["fm_Bt"] == pytest.approx(r["ref_Bt"], rel=1e-9, abs=1e-12), (k, "B_t")
        assert r["fm_B"] == r["ref_B"], (k, "B")
        assert r["fm_S"] == pytest.approx(r["ref_S"], rel=1e-9, abs=1e-12), (k, "S")
        assert r["fm_theta"] == pytest.approx(r["ref_theta"], rel=1e-9, abs=1e-12), (k, "theta")


@divergence("SSOT-V3")
def test_full_model_decides_from_existing_signal():
    """SSOT §8 step 8: Bₜ = σ(γ_sig·[S(t) − θ_eff(t)]) uses the existing S. full_model computes the
    propensity from the newly accumulated S(t+1) and the updated θ(t+1)."""
    f = F.APGIFullDynamicModel(seed=1)
    f.state.S, f.state.theta_t = 0.0, f.params.theta_t0
    st = f.step(1.0, 1.0, 5.0, 5.0)
    assert float(st.ignition_probability) == pytest.approx(
        R.ignition_prob(f.params.k, 0.0, f.params.theta_t0), rel=1e-12)


@divergence("SSOT-V3")
def test_full_model_applies_retention_on_ignition():
    """EQ-RESET-1: on B(t) = 1, S ← ρ_retain·S with ρ_retain ∈ [0.1, 0.5], before the leak. With a
    zero drive (|z| = m₀) the post-event S is therefore at most 0.5·(1 − λ)·S."""
    f = F.APGIFullDynamicModel(seed=1)
    f.state.S = 10.0
    st = f.step(1.0, 1.0, R.M0, R.M0, deterministic_ignition=True)
    assert st.I == 1
    assert float(st.S) <= 0.5 * (1 - R.leak_gain(f.params.delta_t, f.params.tau)) * 10.0 + 1e-12
