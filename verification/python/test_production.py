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
    """The per-step decay exponent equals dt/τ_θ, so τ_θ = dt/exponent must lie in [10, 30] s."""
    tau = CFG["dt"] / CFG["kappa"]
    r = P["tau_theta"]["range"]
    assert float(r["lo"]) <= tau <= float(r["hi"])


@divergence("PD-KAPPA-SYMBOL")
def test_kappa_name_reserved_for_atp_per_bit():
    """Notation Appendix §11: bare κ is reserved exclusively for ATP/bit."""
    assert "kappa" not in CFG


@divergence("PD-FLOOR")
def test_euler_floor_matches_registry():
    floor_default = inspect.signature(PA.update_threshold_euler).parameters["theta_min"].default
    assert floor_default == float(P["theta_floor"]["value"])


@divergence("PD-HAZARD")
def test_ignition_sampling_is_dt_invariant():
    """Release v1.1: ignition is sampled through 1 − exp(−r_max·Bₜ·dt), superseding per-step
    Bernoulli(Bₜ). A sampler without a dt argument cannot be dt-invariant."""
    assert "dt" in inspect.signature(PI.sample_ignition_state).parameters
