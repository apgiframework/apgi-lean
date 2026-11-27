"""TC-20 timestep refinement and TC-10 clamp reporting.

Before the first ignition the canonical pipeline is deterministic under deterministic input,
so P(≥ 1 ignition in a window) of the discrete scheme is exactly 1 − exp(−Σ r_max·B_k·dt)
along the no-ignition path. Its error against a fine reference shrinks with dt (weak error).
"""
import math

import pytest

import apgi_ref as R

T = 1.0  # s, observation window


def drive(t: float) -> float:
    """A smooth deterministic drive S_inst(t) in AU."""
    return 0.6 + 0.4 * math.sin(2 * math.pi * t)


def p_ignite_leak(dt: float, tau_s=0.3, k=5.0, theta=0.35, r_max=5.0) -> float:
    """EQ-LEAK-1 + EQ-IGN-2 + EQ-HAZARD-1 with a given drive: exact discrete-scheme probability."""
    lam, S, H = R.leak_gain(dt, tau_s), 0.0, 0.0
    for n in range(round(T / dt)):
        H += r_max * R.ignition_prob(k, S, theta) * dt
        S = R.leak_step(S, drive(n * dt), lam)
    return 1.0 - math.exp(-H)


def p_ignite_pipeline(dt: float) -> float:
    """Full apgi_ref.core_step on a deterministic exteroceptive pulse, u = 1 (no-ignition path)."""
    p = {**R.CORE_DEFAULTS, "dt": dt, "r_max": 5.0, "gamma_sig": 5.0}
    s, H = R.core_state(p), 0.0
    for n in range(round(T / dt)):
        t = n * dt
        x_e = 2.0 * math.sin(2 * math.pi * t) + (1.5 if 0.3 <= t < 0.6 else 0.0)
        s, log = R.core_step(s, x_e, 0.0, p, 1.0)
        H += p["r_max"] * log["B_prop"] * dt
    return 1.0 - math.exp(-H)


def test_weak_convergence_first_order():
    """TC-20: halving dt roughly halves the weak error of P(≥ 1 ignition) (first-order scheme)."""
    ref = p_ignite_leak(1e-5)
    dts = [0.02, 0.01, 0.005, 0.0025]
    err = [abs(p_ignite_leak(d) - ref) for d in dts]
    assert all(a > b for a, b in zip(err, err[1:])), err
    for a, b in zip(err, err[1:]):
        assert 1.6 < a / b < 2.4, err
    assert err[-1] < 1e-3


def test_pipeline_refinement_monotone():
    """TC-20 on the full pipeline: the error against dt = 0.5 ms decreases monotonically under refinement."""
    ref = p_ignite_pipeline(0.0005)
    err = [abs(p_ignite_pipeline(d) - ref) for d in (0.02, 0.01, 0.005)]
    assert err[0] > err[1] > err[2], err
    assert err[-1] < 0.05


def test_hazard_invariance_constant_propensity():
    """TC-20 hazard invariance: with constant B_t the window probability is the same at every dt (CL-10)."""
    vals = [1 - (1 - R.hazard_prob(5.0, 0.4, d)) ** round(T / d) for d in (0.02, 0.01, 0.001)]
    assert max(vals) - min(vals) < 1e-12


def test_clamp_fraction_reported():
    """TC-10: the clamped-step fraction is reported per run and is 1 when the variance pins Π at Π_max."""
    n = 200
    _, logs, rep = R.run_core([0.0] * n, [0.0] * n, [1.0] * n)
    assert rep["steps"] == n and 0.0 <= rep["precision_clamped_fraction"] <= 1.0
    p = {**R.CORE_DEFAULTS, "gamma_ne": 2.0, "g_ne": 1.0}
    _, _, rep2 = R.run_core([0.0] * n, [0.0] * n, [1.0] * n, p)
    assert rep2["ne_clamped_fraction"] == 1.0  # |2|·1 > 0.5, so the clamp binds on every step
    assert all(abs(p["gamma_ne"]) * l["g_ne"] <= 0.5 + 1e-12 for l in R.run_core([0.0] * 5, [0.0] * 5, [1.0] * 5, p)[1])


@pytest.mark.parametrize("dt", [0.01, 0.005])
def test_step_rule_holds_for_refinement_grid(dt):
    """TC-13 / EQ-STEP-1: every dt of the refinement grid satisfies dt ≤ min(τ_S, τ_θ, τ_Π)/10 at CFG-CORE."""
    assert R.step_rule(dt, R.CORE_DEFAULTS["tau_S"], R.CORE_DEFAULTS["tau_theta"], 1.0)
