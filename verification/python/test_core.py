"""SSOT v1.2 minimal core: reference equations and the canonical pipeline (task 53).

These tests check apgi_ref's realisation of the SSOT minimal core and the §13
execution order against the conformance tests the SSOT names (TC-05, 07, 09,
11, 12, 14, 17). test_production.py then holds the production packages to the
same statements; each production divergence is a strict xfail tagged SSOT-P*.
"""
import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

import apgi_ref as R
import registry

P = registry.params()
z_st = st.floats(-8, 8, allow_nan=False)
pos = st.floats(0.1, 10, allow_nan=False)


# ------------------------------------------------------------ equations ----
def test_core_defaults_match_registry():
    """apgi_ref.CORE_DEFAULTS (CFG-CORE) carries the registry values it shares with the registry."""
    D = R.CORE_DEFAULTS
    pairs = {"dt": "dt", "theta0": "theta_baseline", "theta_floor": "theta_floor", "pi_min": "pi_min",
             "pi_max": "pi_max", "T_e": "T_window_e", "T_i": "T_window_i", "eps_stab": "eps_stab",
             "g_ne": "g_NE", "beta_5ht": "beta_5HT"}
    for k, pid in pairs.items():
        assert D[k] == pytest.approx(float(P[pid]["value"])), (k, pid)
    r = P["tau_S"]["range"]
    assert float(r["lo"]) <= D["tau_S"] <= float(r["hi"])
    r = P["tau_theta"]["range"]
    assert float(r["lo"]) <= D["tau_theta"] <= float(r["hi"])
    assert D["gamma_ne"] == 0.0  # R6: no default sign


def test_m0_is_mean_abs_standard_normal():
    """EQ-EXCESS-1: m₀ = √(2/π) = E|z| for z ~ N(0, 1) (registry m0; Lean target, task 55)."""
    assert R.M0 == pytest.approx(math.sqrt(2 / math.pi), rel=1e-15)
    assert R.M0 == pytest.approx(float(P["m0"]["value"]), rel=1e-12)
    z = np.random.default_rng(10101).standard_normal(2_000_000)
    assert np.mean(np.abs(z)) == pytest.approx(R.M0, abs=2e-3)


def test_null_operating_point_drive_mean_zero():
    """TC-07: under stimulus-free Gaussian input and Π_rel = 1 the mean of S_inst is 0 (SSOT §5.5).
    Without the excess correction it would be 2·m₀ ≈ 1.60 AU, above the whole θ₀ band."""
    rng = np.random.default_rng(20202)
    ze, zi = rng.standard_normal(1_000_000), rng.standard_normal(1_000_000)
    s = np.abs(ze) - R.M0 + np.abs(zi) - R.M0
    assert abs(s.mean()) < 5e-3
    assert np.mean(np.abs(ze) + np.abs(zi)) == pytest.approx(2 * R.M0, abs=5e-3)


@given(pos, z_st, pos, z_st)
def test_drive_sign_symmetric(pe, ze, pi, zi):
    """TC-09: equal-magnitude errors of opposite sign contribute equally (EQ-DRIVE-1)."""
    assert R.drive(pe, ze, pi, zi) == R.drive(pe, -ze, pi, -zi)


@given(pos, pos, z_st)
def test_drive_monotone_in_precision_iff_excess_nonneg(p1, p2, z):
    """EQ-DRIVE-1: S_inst is non-decreasing in Π_rel exactly where |z| ≥ m₀ (SSOT-R2; the
    uncentered EQ-PREC-1 theorem does not cover this). Lean target: task 55."""
    p1, p2 = min(p1, p2), max(p1, p2)
    lo, hi = R.drive(p1, z, 0.0, 0.0), R.drive(p2, z, 0.0, 0.0)
    if abs(z) >= R.M0:
        assert lo <= hi + 1e-12
    elif p1 < p2:
        assert lo > hi


@given(st.floats(0.1, 10), st.floats(0.1, 10))
def test_prec_rel_definition(pi_eff, pi_bar):
    """EQ-PREC-REL-1: Π_rel = Π_eff/Π̄; Π_rel = 1 at the calibration mean; not re-clamped."""
    assert R.prec_rel(pi_eff, pi_bar) == pytest.approx(pi_eff / pi_bar)
    assert R.prec_rel(pi_bar, pi_bar) == pytest.approx(1.0)
    assert R.prec_rel(10.0, 0.1) == pytest.approx(100.0)


@given(z_st, st.floats(-5, 5), st.floats(0.01, 5))
def test_standardize_definition(eps, mu, sd):
    """EQ-STD-1."""
    assert R.standardize(eps, mu, sd) == pytest.approx((eps - mu) / (sd + R.EPS_STAB))


@given(st.floats(-5, 5), st.floats(0, 5), st.floats(-5, 5), st.floats(1e-4, 0.5))
def test_ema_uses_pre_update_mean(mu, s2, eps, a):
    """EQ-EMA-1/2 (TC-17): the variance residual is ε − μ(t), not ε − μ(t+1)."""
    mu1, s21 = R.ema_update(mu, s2, eps, a)
    assert mu1 == pytest.approx((1 - a) * mu + a * eps)
    assert s21 == pytest.approx((1 - a) * s2 + a * (eps - mu) ** 2)


def test_ema_alpha_from_window():
    """EQ-EMA-2 at dt₀ = 10 ms: α = 1 − e^(−0.01/5) ≈ 0.0020 (extero), 1 − e^(−0.01/10) ≈ 0.0010 (intero)."""
    assert R.ema_alpha(0.01, 5.0) == pytest.approx(1.99800e-3, rel=1e-4)
    assert R.ema_alpha(0.01, 10.0) == pytest.approx(9.99500e-4, rel=1e-4)


@given(st.floats(0, 5), st.floats(-3, 3), st.floats(0, 5), st.floats(-1, 1), st.floats(0, 1), st.floats(0, 1))
def test_theta_eff_reductions(theta, gamma_ne, g_ne, b5, r, u):
    """EQ-THEFF-1: with all modulators off θ_eff = θ; NE scales θ; 5-HT, r and u shift it."""
    assert R.theta_eff(theta) == theta
    base = R.theta_eff(theta, gamma_ne, g_ne)
    assert base == pytest.approx(theta * R.ne_factor(gamma_ne, g_ne))
    assert R.theta_eff(theta, gamma_ne, g_ne, r=r, beta_5ht=b5, u=u) == pytest.approx(base + r + b5 - u)
    assert R.theta_eff(theta, kappa_up=0.3, lower_ignited=True) == pytest.approx(0.7 * theta)


def test_step_rule_at_defaults():
    """EQ-STEP-1: dt₀ = 10 ms ≤ min(τ_S = 0.3, τ_θ = 20, τ_Π ≥ 1)/10; Δt_res = 1 ms with τ_res ≥ 10 ms."""
    assert R.step_rule(0.01, 0.3, 20.0, 1.0)
    assert R.step_rule(0.001, 0.3, 20.0, 1.0, 0.01)
    assert not R.step_rule(0.5, 0.3, 20.0, 1.0)


@pytest.mark.parametrize("g, th, floor", [(2.0, 0.85, None), (7.5, 0.85, 0.0017), (2.0, 0.25, 0.378),
                                          (2.0, 0.35, 0.332), (5.0, 0.35, 0.148), (7.5, 0.35, 0.068)])
def test_soft_floor_worked_values(g, th, floor):
    """R1 / TC-14 (SSOT §7.3): σ(−γ_sig·θ_eff) at the band corners and at θ₀ = 0.35."""
    op = R.operating_point(g, th, 100.0)
    if floor is not None:
        assert op["propensity_floor"] == pytest.approx(floor, abs=6e-4)
    assert op["baseline_rate"] == pytest.approx(100.0 * op["propensity_floor"])


# ------------------------------------------------------------- pipeline ----
def _run(n, p=None, seed=30303, amp=1.0, u=None):
    rng = np.random.default_rng(seed)
    s, logs = R.core_state(p), []
    for _ in range(n):
        s, log = R.core_step(s, amp * rng.standard_normal(), amp * rng.standard_normal(), p,
                             u=rng.random() if u is None else u)
        logs.append(log)
    return s, logs


def test_pipeline_null_operating_point():
    """TC-07 on the whole loop: stimulus-free Gaussian input, no ignition (u = 1), Π̄ = 1.
    The drive and S keep a mean near zero; S takes negative values (S is signed, never rectified)."""
    s, logs = _run(6000, u=1.0)
    si = np.array([lg["S_inst"] for lg in logs[1000:]])
    S = np.array([lg["S_decided"] for lg in logs[1000:]])
    assert abs(si.mean()) < 0.1 and abs(S.mean()) < 0.1
    assert S.min() < 0 < S.max()


def test_pipeline_decides_from_existing_S():
    """§13 steps 8-13: B_t uses S(t) before reset and accumulation; the one-step lag is by design."""
    s = R.core_state()
    s["S"] = 0.2
    s2, log = R.core_step(s, 50.0, 0.0, {"r_max": 1e9}, u=0.5)
    assert log["B_prop"] == pytest.approx(R.ignition_prob(5.0, 0.2, 0.35))
    assert log["S_decided"] == 0.2


def test_pipeline_readout_never_written_back():
    """TC-11: NE factor, β_5HT, r(t) and u(t) move θ_eff only; with no ignition θ relaxes to θ₀ unchanged."""
    p = {"gamma_ne": 0.4, "g_ne": 1.0, "beta_5ht": 0.2, "u_urg": 0.05}
    s, logs = _run(300, p, u=1.0)
    assert s["theta"] == pytest.approx(0.35, abs=1e-15)
    assert logs[-1]["theta_eff"] == pytest.approx(0.35 * 1.4 + 0.2 - 0.05)


def test_pipeline_exactly_once():
    """TC-12: one ignition applies exactly one δ_reset (inside EQ-ALLO-1), one δ_ref and one retention."""
    p = {"delta_reset": 0.2, "delta_ref": 0.3, "rho_retain": 0.25, "r_max": 1e9}
    s = R.core_state(p)
    s["S"] = 1.0
    s2, log = R.core_step(s, 0.0, 0.0, p, u=0.0)
    assert log["B"] == 1
    assert s2["theta"] == pytest.approx(R.threshold_step(0.35, 0.35, 0.0, 0.0, 0.0, 0.2, 1, 0.01, 20.0))
    assert s2["r"] == pytest.approx(0.3)
    lam = R.leak_gain(0.01, 0.3)
    assert s2["S"] == pytest.approx((1 - lam) * 0.25 * 1.0 + lam * log["S_inst"])


def test_pipeline_estimator_ordering():
    """TC-17: z uses reference statistics that exclude ε(t); Π uses Σ before ε(t) enters it;
    the reference window and the precision EMA are separate estimators."""
    s, _ = _run(50)
    mu, sd = R._ref_stats(s["ref_e"])
    s2, log = R.core_step(s, 3.0, 0.0)
    assert log["z_e"] == pytest.approx((3.0 - mu) / (sd + R.EPS_STAB))
    assert log["pi_e"] == pytest.approx(R.prec_clamp(0.1, 10.0, 1 / (s["s2_e"] + R.EPS_STAB)))
    s_alt = {**s, "s2_e": 4.0}
    assert R.core_step(s_alt, 3.0, 0.0)[1]["z_e"] == log["z_e"]


def test_pipeline_timestep_invariance_of_hazard():
    """TC-06 on the sampler the pipeline uses: survival over a fixed window is dt-invariant."""
    b = 0.3
    one = (1 - R.hazard_prob(10.0, b, 0.02))
    two = (1 - R.hazard_prob(10.0, b, 0.01)) ** 2
    assert one == pytest.approx(two, rel=1e-12)


def test_pipeline_threshold_signature():
    """TC-15 (R2), on the reference loop, qualitative part: raising θ from 0.35 to 0.80 lowers hits
    and false alarms together (a criterion shift). The quantitative d′/c fixture is task 56."""
    def rates(theta0, amp):
        hits = fas = 0
        rng = np.random.default_rng(40404)
        for trial in range(300):
            s = R.core_state({"theta0": theta0})
            sig = trial % 2 == 0
            fired = 0
            for k in range(50):
                xe = (amp if sig and 10 <= k < 30 else 0.0) + rng.standard_normal()
                s, log = R.core_step(s, xe, rng.standard_normal(), {"theta0": theta0, "r_max": 10.0}, u=rng.random())
                fired |= log["B"]
            hits += fired and sig
            fas += fired and not sig
        return hits / 150, fas / 150
    h1, f1 = rates(0.35, 3.0)
    h2, f2 = rates(0.80, 3.0)
    assert h2 < h1 and f2 < f1
