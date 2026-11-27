"""Float64 twins of Apgi/Pipeline.lean and Apgi/Strata.lean (task 62 / 63).

Lean proves each statement over ℝ for the abstract pipeline (`Apgi.pipeStep`, any reference
estimator). These tests hold apgi_ref.core_step, the sliding-window realisation, to the same
statements on random admissible parameters, random inputs and random draws.
"""
import math

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import apgi_ref as R

M0 = R.M0
SETTINGS = settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])

params_st = st.fixed_dictionaries({
    "rho_retain": st.floats(0.0, 1.0),
    "tau_S": st.floats(0.05, 5.0),
    "delta_ref": st.floats(0.0, 0.5),
    "delta_reset": st.floats(-0.5, 0.5),
    "eta_theta": st.floats(-1.0, 1.0),
    "c1": st.floats(-1.0, 1.0), "c2": st.floats(-1.0, 1.0),
    "v1": st.floats(0.0, 1.0), "v2": st.floats(0.0, 1.0),
    "gamma_ne": st.floats(-3.0, 3.0), "g_ne": st.floats(0.0, 3.0),
    "g_ach": st.floats(0.0, 3.0), "beta_da": st.floats(-1.0, 1.0),
    "r_max": st.floats(0.0, 50.0), "gamma_sig": st.floats(0.0, 20.0),
    "eta_pred_e": st.floats(0.0, 0.05), "eta_pred_i": st.floats(0.0, 0.05),
})
draws_st = st.lists(st.tuples(st.floats(-50, 50), st.floats(-50, 50), st.floats(0.0, 1.0)),
                    min_size=1, max_size=60)


def admissible(p: dict) -> bool:
    """Apgi.PipeAdmissible, evaluated on an apgi_ref parameter dict."""
    lam = R.leak_gain(p["dt"], p["tau_S"])
    a_e, a_i = R.ema_alpha(p["dt"], p["T_e"]), R.ema_alpha(p["dt"], p["T_i"])
    return (0 <= p["pi_min"] <= p["pi_max"] and p["pi_bar_e"] > 0 and p["pi_bar_i"] > 0 and M0 >= 0
            and 0 <= a_e <= 1 and 0 <= a_i <= 1 and 0 <= p["rho_retain"] <= 1 and 0 <= lam <= 1
            and p["delta_ref"] >= 0)


def drive_lower(p: dict) -> float:
    """Apgi.driveLower: −m₀·(Π_max/Π̄ᵉ + Π_max/Π̄ⁱ)."""
    return -(M0 * (p["pi_max"] / p["pi_bar_e"] + p["pi_max"] / p["pi_bar_i"]))


def test_cfg_core_is_admissible():
    """The CFG-CORE defaults satisfy every hypothesis of Apgi.traj_inv."""
    assert admissible(dict(R.CORE_DEFAULTS))


@SETTINGS
@given(params_st, draws_st)
def test_traj_inv(over, draws):
    """Lean: Apgi.traj_inv, Apgi.traj_prec_mem_Icc, Apgi.traj_ne_bound, Apgi.pipeLog_Sinst_ge."""
    p = {**R.CORE_DEFAULTS, **over}
    assert admissible(p)
    L = drive_lower(p)
    s = R.core_state(p)
    for xe, xi, u in draws:
        s, log = R.core_step(s, xe, xi, p, u)
        assert s["s2_e"] >= 0 and s["s2_i"] >= 0
        assert s["theta"] >= R.THETA_FLOOR
        assert s["r"] >= 0
        assert s["B_prev"] in (0, 1)
        assert log["S_inst"] >= L - 1e-9
        assert s["S"] >= L - 1e-9
        for k in ("pi_e", "pi_i", "pi_e_eff", "pi_i_eff"):
            assert p["pi_min"] - 1e-12 <= log[k] <= p["pi_max"] + 1e-12
        assert abs(p["gamma_ne"]) * log["g_ne"] <= 0.5 + 1e-12


@SETTINGS
@given(params_st, draws_st, st.floats(0.0, 30.0))
def test_traj_S_le(over, draws, U):
    """Lean: Apgi.traj_S_le (conditional): if every drive is ≤ U, 0 ≤ U and S₀ ≤ U, then S ≤ U."""
    p = {**R.CORE_DEFAULTS, **over}
    s = R.core_state(p)
    for xe, xi, u in draws:
        s_next, log = R.core_step(s, xe, xi, p, u)
        if log["S_inst"] > U:
            return  # hypothesis of the theorem fails from here on
        s = s_next
        assert s["S"] <= U + 1e-9


@SETTINGS
@given(params_st, draws_st, st.floats(-50, 50), st.floats(-50, 50), st.floats(0.0, 1.0))
def test_decision_input_independent(over, draws, xe2, xi2, u):
    """Lean: Apgi.pipeStep_decision_input_independent — B_t and B(t) at t ignore the inputs at t."""
    p = {**R.CORE_DEFAULTS, **over}
    s = R.core_state(p)
    for xe, xi, uu in draws:
        s, _ = R.core_step(s, xe, xi, p, uu)
    _, l1 = R.core_step(s, draws[-1][0], draws[-1][1], p, u)
    _, l2 = R.core_step(s, xe2, xi2, p, u)
    assert l1["B_prop"] == l2["B_prop"] and l1["B"] == l2["B"]


@SETTINGS
@given(params_st, draws_st)
def test_variance_uses_preupdate_mean(over, draws):
    """Lean: Apgi.pipeStep_variance_uses_preupdate_mean and pipeStep_reference_excludes_current."""
    p = {**R.CORE_DEFAULTS, **over}
    s = R.core_state(p)
    a = R.ema_alpha(p["dt"], p["T_e"])
    for xe, xi, u in draws:
        mu, s2, ref = s["mu_e"], s["s2_e"], list(s["ref_e"])
        s, log = R.core_step(s, xe, xi, p, u)
        assert math.isclose(s["s2_e"], (1 - a) * s2 + a * (log["eps_e"] - mu) ** 2, rel_tol=1e-12, abs_tol=1e-12)
        m, sd = R._ref_stats(ref)
        assert math.isclose(log["z_e"], R.standardize(log["eps_e"], m, sd, p["eps_stab"]), rel_tol=1e-12, abs_tol=1e-12)
        assert s["ref_e"][-1] == log["eps_e"]


def test_sampler_frequency_matches_hazard():
    """Lean: Apgi.pipeLog_ignition_measure — under a uniform draw, P(B(t) = 1) = hazard."""
    p = {**R.CORE_DEFAULTS, "r_max": 30.0, "gamma_sig": 5.0}
    s = {**R.core_state(p), "S": 0.6}
    rng = np.random.default_rng(62)
    us = rng.random(200_000)
    _, log = R.core_step(s, 0.0, 0.0, p, 0.5)
    q = R.hazard_prob(p["r_max"], log["B_prop"], p["dt"])
    freq = np.mean([R.core_step(s, 0.0, 0.0, p, float(u))[1]["B"] for u in us[:20_000]])
    assert abs(freq - q) < 4 * math.sqrt(q * (1 - q) / 20_000) + 1e-12


@given(st.floats(0.1, 20), st.floats(0.01, 1.0), st.floats(-5, 5), st.floats(-5, 5), st.floats(-5, 5))
def test_orders_differ(k, lam, S, Sinst, th):
    """Lean: Apgi.orders_differ and Apgi.decideAfterAccumulation_strictMono_drive."""
    canonical = R.ignition_prob(k, S, th)
    variant = R.ignition_prob(k, R.leak_step(S, Sinst, lam), th)
    Sv = R.leak_step(S, Sinst, lam)
    if abs(Sinst - S) * lam * k > 1e-6 and abs(k * (S - th)) < 20 and abs(k * (Sv - th)) < 20:  # no float saturation
        assert canonical != variant
        assert (variant > canonical) == (Sinst > S)


@given(st.floats(-10, 10), st.floats(-10, 10), st.floats(0.1, 5), st.floats(0.0, 1.0))
def test_standardize_after_update_shrinks(eps, mu, sd, a):
    """Lean: Apgi.standardize_after_update_shrinks — the rejected 'statistics first' order shrinks z by (1 − α)."""
    mu_new = (1 - a) * mu + a * eps
    assert math.isclose(R.standardize(eps, mu_new, sd, 0.0), (1 - a) * R.standardize(eps, mu, sd, 0.0),
                        rel_tol=1e-9, abs_tol=1e-9)


# ------------------------------------------------------------ Apgi/Strata.lean ----
def test_level_tau_values_and_limitations():
    """Lean: Apgi.levelTau_values, L1_point_outside_band, L2_point_vs_bands, five_levels_boundary."""
    tau = [R.geo_timescale(l) for l in range(5)]
    for got, want in zip(tau, (1 / 20, 133 / 20, 17689 / 20, 2352637 / 20, 312900721 / 20)):
        assert math.isclose(got, want, rel_tol=1e-12)
    assert tau[1] > 3.0
    assert tau[2] < 25 * 60 and 60 <= tau[2] <= 30 * 60
    assert R.geo_timescale(4, k=133.0) <= 1.58e7 < R.geo_timescale(4, k=134.0)
    assert all(t1 < t2 for t1, t2 in zip(tau, tau[1:]))


@given(st.floats(0, 1e9))
def test_tau_pi_step_rule(tau_l):
    """Lean: Apgi.tauPiLevel_step_rule — τ_Π = max(1 s, τ_ℓ/10) gives dt₀ = 10 ms ≤ τ_Π/10."""
    assert 0.01 <= max(1.0, tau_l / 10) / 10


@given(st.lists(st.tuples(st.floats(-5, 5), st.floats(-5, 5), st.floats(-5, 5), st.floats(-5, 5)),
                min_size=1, max_size=5), st.floats(0.1, 100), st.floats(0.1, 100))
def test_lyapunov_decoupled(rows, tau_pi, tau_th):
    """Lean: Apgi.lyapunov_decoupled (loop gain 0 only; the coupled conjecture CL-26 is unresolved)."""
    V = sum((P - Ps) ** 2 + (t - ts) ** 2 for P, Ps, t, ts in rows)
    Vdot = sum(2 * (P - Ps) * (-(P - Ps) / tau_pi) + 2 * (t - ts) * (-(t - ts) / tau_th) for P, Ps, t, ts in rows)
    assert Vdot <= -min(1 / tau_pi, 1 / tau_th) * V + 1e-9
