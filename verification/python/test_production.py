"""Production code vs reference and registry (handoff task E21).

test_twins.py checks the reference implementation apgi_ref.py against the
Lean theorems. This module closes the chain: it checks the production package
(apgiframework/apgi-implementation, commit pinned in known-conflicts.json
'production') against apgi_ref.py, the Lean statements, and the registry.

Set APGI_IMPL_PATH to a checkout of that commit. Without it the module is
skipped, and the report says 'skipped', never 'passed'.

Known divergences are strict xfails tagged PD-*: CI stays green while the
divergence is documented, and a fix in production turns the xfail into a
hard failure until the PD entry is marked resolved.
"""
import ast
import inspect
import os
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import apgi_ref as R
import registry

IMPL = os.environ.get("APGI_IMPL_PATH")
if not IMPL or not (Path(IMPL) / "core" / "ignition.py").exists():
    pytest.skip("APGI_IMPL_PATH does not point at an apgi-implementation checkout", allow_module_level=True)
sys.path.insert(0, IMPL)
import config as PCFG  # noqa: E402  production defaults
import core.allostatic as PA  # noqa: E402
import core.ignition as PI  # noqa: E402
import core.threshold as PT  # noqa: E402

P = registry.params()
KNOWN = registry.load("known-conflicts.json")
DIV = {d["id"]: d for d in KNOWN["production"]["divergences"]}
BAND_LO = float(P["theta_operating_lower"]["value"])
BAND_HI = float(P["theta_operating_upper"]["value"])
CFG = PCFG.CONFIG


def divergence(pd_id):
    d = DIV[pd_id]
    return pytest.mark.xfail(d["status"] == "open", strict=True, reason=f"{pd_id}: {d['summary']}")


# --------------------------------------------- equivalence with apgi_ref ----
@given(st.floats(-1e3, 1e3), st.floats(-1e3, 1e3))
def test_detect_ignition_matches_reference(S, theta):
    """EQ-IGN-1. Lean: Apgi.ignites_antitone_threshold (via apgi_ref.ignites)."""
    assert PI.detect_ignition_event(S, theta) == R.ignites(S, theta)


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(0.133, 0.5))
def test_ignition_probability_matches_reference(S, theta, tau_sigma):
    """EQ-IGN-2: production sigmoid((S−θ)/τ_σ) == reference with γ_sig = 1/τ_σ."""
    assert PI.compute_ignition_probability(S, theta, tau_sigma) == pytest.approx(
        R.ignition_prob(1.0 / tau_sigma, S, theta), rel=1e-12, abs=1e-15)


@given(st.floats(BAND_LO, BAND_HI), st.floats(BAND_LO, BAND_HI), st.floats(0, 1), st.floats(10, 30))
def test_threshold_decay_matches_reference(theta, theta0, dt, tau):
    """EQ-DECAY-1: production threshold_decay(θ, θ₀, dt/τ) == apgi_ref.decay_step."""
    assert PT.threshold_decay(theta, theta0, dt / tau) == pytest.approx(
        R.decay_step(theta, theta0, dt, tau), rel=1e-12, abs=1e-15)


# ------------------------------------------ Lean statements on production ----
@given(st.floats(BAND_LO, BAND_HI), st.floats(BAND_LO, BAND_HI), st.floats(0, 50))
def test_production_decay_stays_in_band(theta, theta0, exponent):
    """Lean: Apgi.decay_step_mem_Icc, applied to the production function."""
    v = PT.threshold_decay(theta, theta0, exponent)
    assert BAND_LO - 1e-12 <= v <= BAND_HI + 1e-12


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(-5, 5), st.floats(0.133, 0.5))
def test_production_ignition_antitone_in_threshold(S, t1, t2, tau_sigma):
    """Lean: Apgi.ignitionProb_antitone_threshold, applied to production."""
    t1, t2 = min(t1, t2), max(t1, t2)
    assert PI.compute_ignition_probability(S, t2, tau_sigma) <= PI.compute_ignition_probability(S, t1, tau_sigma) + 1e-15


# ---------------------------------------------- registry conformance ----
def test_default_theta_base_in_band():
    assert BAND_LO <= CFG["theta_base"] <= BAND_HI


@divergence("PD-DT")
def test_default_dt_respects_step_rule():
    """Math Spec p43: dt ≤ min(τ_S, τ_θ, τ_Π, τ_res)/10; τ_S ≥ 0.2 s gives dt ≤ 0.02 s."""
    tau_s_lo = float(P["tau_S"]["range"]["lo"])
    assert CFG["dt"] <= tau_s_lo / 10


@divergence("PD-TAU-THETA")
def test_default_decay_implies_registry_tau_theta():
    """The per-step decay exponent equals dt/τ_θ, so τ_θ = dt/exponent must lie in [10, 30] s.
    Before the fix the exponent was stored as CONFIG['kappa']; after it, CONFIG holds τ_θ."""
    tau = CFG["tau_theta"] if "tau_theta" in CFG else CFG["dt"] / CFG["kappa"]
    r = P["tau_theta"]["range"]
    assert float(r["lo"]) <= tau <= float(r["hi"])
    assert PCFG.decay_exponent(CFG) == pytest.approx(CFG["dt"] / tau, rel=1e-12)


@divergence("PD-KAPPA-SYMBOL")
def test_kappa_name_reserved_for_atp_per_bit():
    """Notation Appendix §11: bare κ is reserved exclusively for ATP/bit, and κ_meta is
    deprecated (R_L replaces it). Old names may survive one release as warning aliases."""
    assert "kappa" not in CFG and "kappa_meta" not in CFG
    params = inspect.signature(PT.threshold_decay).parameters
    assert "kappa" not in params
    with pytest.warns(DeprecationWarning):
        PT.threshold_decay(0.5, 0.35, kappa=0.1)


@divergence("PD-TAU-S")
def test_default_tau_s_in_registry_range():
    """Notation Appendix p2 / Dynamical Formulation p15: τ_S ∈ [200, 500] ms (worked value 300 ms)."""
    r = P["tau_S"]["range"]
    assert float(r["lo"]) <= CFG["tau_s"] <= float(r["hi"])


def test_default_lambda_is_exact_gain():
    """Math Spec Eq. 23–24: λ = 1 − exp(−dt/τ_S) at the configured dt and τ_S."""
    assert CFG["lam"] == pytest.approx(R.leak_gain(CFG["dt"], CFG["tau_s"]), rel=1e-12)


@divergence("PD-CLIP")
def test_pipeline_theta_clip_matches_floor():
    """The pipeline clamps θ to [theta_clip_min, theta_clip_max]; Math Spec §4.5 sets the
    floor θ_floor = 0 unless a study states otherwise, and states no 0.1 AU clip."""
    assert CFG.get("theta_clip_min", 0.0) == float(P["theta_floor"]["value"])


def test_default_tau_pi_meets_registry_bound():
    """Task 31 (KC-PRECOND-TAU-PI): v1.2 fixes τ_Π ≥ 1 s; production τ_Π and dt ≤ τ_Π/10 hold."""
    lo = float(P["tau_Pi"]["range"]["lo"])
    assert CFG["tau_pi"] >= lo
    assert CFG["dt"] <= lo / 10


def _source_tree(relpath):
    return ast.parse((Path(IMPL) / relpath).read_text(encoding="utf-8"))


def _source_params(relpath, qualname):
    """Parameter names of a function in a production file, without importing it."""
    node = _source_tree(relpath)
    for part in qualname.split("."):
        node = next(n for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
    a = node.args
    return {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs}


def _source_all(relpath):
    for n in _source_tree(relpath).body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                return set(ast.literal_eval(n.value))
    return set()


@divergence("PD-KAPPA-RESIDUAL")
def test_no_bare_kappa_for_rates_or_ratios():
    """Notation Appendix: bare κ is ATP/bit only; κ_e, κ_i are withdrawn (η_pred,e, η_pred,i)."""
    import analysis.stability as PS
    import core.dynamics as PD
    import energy.bold_calibration as PB

    assert "kappa_e" not in CFG and "kappa_i" not in CFG
    assert "kappa" not in inspect.signature(PD.update_prediction).parameters
    assert "kappa" not in inspect.signature(PS.compute_jacobian_discrete).parameters
    assert "kappa_meta" not in inspect.signature(PB.estimate_bits_from_bold_energy).parameters
    # engine and models import the full pipeline (structlog etc.), so read their source
    assert "kappa" not in _source_params("engine/somatic.py", "SomaticThresholdAdapter.__init__")
    assert "KAPPA" not in _source_all("models/reduced.py")


@divergence("PD-LOOP-GAIN")
def test_default_cross_level_loop_gain_subcritical():
    """Notation Appendix p19, p34 (proposed): (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² < 1."""
    g = (CFG["C_down"] * CFG["tau_pi"]) * (CFG["C_up"] * CFG["tau_pi"]) * CFG["gamma_psi"] ** 2
    assert g < 1


@divergence("PD-FLOOR")
def test_euler_floor_matches_registry():
    floor_default = inspect.signature(PA.update_threshold_euler).parameters["theta_min"].default
    assert floor_default == float(P["theta_floor"]["value"])


@divergence("PD-HAZARD")
def test_ignition_sampling_is_dt_invariant():
    """Release v1.1: ignition is sampled through 1 − exp(−r_max·Bₜ·dt), superseding per-step
    Bernoulli(Bₜ). A sampler without a dt argument cannot be dt-invariant."""
    sig = inspect.signature(PI.sample_ignition_state).parameters
    assert "dt" in sig and "r_max" in sig
    assert "r_max" in CFG and CFG["r_max"] > 0


@divergence("PD-HAZARD")
@given(st.floats(0, 1), st.floats(0, 0.5), st.floats(0, 200))
def test_production_hazard_matches_reference(B, dt, r_max):
    """EQ-HAZARD-1. Lean: Apgi.hazard_two_steps, applied to the production hazard."""
    p = PI.hazard_probability(B, dt, r_max)
    assert p == pytest.approx(R.hazard_prob(r_max, B, dt), rel=1e-12, abs=1e-15)
    assert (1 - p) ** 2 == pytest.approx(1 - PI.hazard_probability(B, 2 * dt, r_max), rel=1e-9, abs=1e-15)
