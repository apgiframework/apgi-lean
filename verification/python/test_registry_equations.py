"""Task 54: definitional and twin tests for the SSOT equations registered in spec 0.5.0.

Each test names the equation IDs it covers and, where one exists, the Lean theorem it
twins (Apgi/Extensions.lean, Apgi/Core.lean). Worked values are the SSOT's own numbers."""
import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

import apgi_ref as R

f = st.floats(min_value=-5, max_value=5, allow_nan=False)
pos = st.floats(min_value=0.01, max_value=5, allow_nan=False)


@given(f, f, st.floats(min_value=0.001, max_value=1.999))
def test_err_pred(x, xh, eta_pi):
    """EQ-ERR-1, EQ-PRED-1. Lean: Apgi.pred_error_update."""
    eps = R.prediction_error(x, xh)
    assert eps == x - xh
    new = R.prediction_update(xh, eta_pi, 1.0, eps)
    assert R.prediction_error(x, new) == pytest.approx((1 - eta_pi) * eps, abs=1e-9)


@given(st.floats(min_value=1e-9, max_value=4.0))
def test_twin_pred_contraction(eta_pi):
    """EQ-PRED-1. Lean: Apgi.pred_contraction (0 < η·Π < 2 ⇒ |1 − η·Π| < 1)."""
    assert (abs(1 - eta_pi) < 1) == (eta_pi < 2)


@given(st.floats(min_value=0, max_value=5), st.floats(min_value=0.01, max_value=50))
def test_prec_ach_clamped(g, pi):
    """EQ-PREC-ACH-1. Lean: Apgi.precClamp_mem_Icc."""
    assert 0.1 <= R.prec_ach(g, pi) <= 10.0
    assert R.prec_ach(1.0, 3.0) == 3.0


@given(f, f, f, f)
def test_somatic_marker_clip(gv, b, ga, s):
    """EQ-SM-1. Lean: Apgi.precClamp_mem_Icc with [−2, 2]."""
    m = R.somatic_marker(gv, b, ga, s)
    assert -2.0 <= m <= 2.0


@given(f, st.floats(min_value=0.01, max_value=5))
def test_da_bias_nonmonotone(z, beta):
    """EQ-DA-1. Lean: Apgi.da_salience_iff (|z + β| > |z| ⇔ z > −β/2)."""
    if abs(z + beta / 2) > 1e-9:
        assert (abs(R.da_bias(z, beta)) > abs(z)) == (z > -beta / 2)


def test_allostatic_rate_forms():
    """EQ-ALLO-C1, EQ-ALLO-R1: zero drive gives pure mean reversion, consistent with the exact decay
    of EQ-ALLO-1; the reduced form equals the full form when η[C − V] = γ_M(1 − S_met) + γ_A·A."""
    assert R.allostatic_rate(0.85, 0.35, 20.0, 0.0, 0.0, 0.0) == pytest.approx(-0.5 / 20.0)
    th, dt = 0.85, 1e-4
    euler = th + dt * R.allostatic_rate(th, 0.35, 20.0, 0.0, 0.0, 0.0)
    assert euler == pytest.approx(R.decay_step(th, 0.35, dt, 20.0), rel=1e-9)
    full = R.allostatic_rate(0.5, 0.35, 20.0, 1.0, 0.3 * 0.4 + 0.2 * 0.6, 0.0)
    red = R.allostatic_rate_reduced(0.5, 0.35, 20.0, 0.3, 0.6, 0.2, 0.6)
    assert full == pytest.approx(red)


def test_anticipation_zero_horizon_recovers_reactive():
    """EQ-ANT-1: T_ant = 0 recovers the reactive cost."""
    path = [0.1, 0.4, 0.9, 0.2]
    assert R.anticipated_cost(path, 1, 0) == path[1]
    assert R.anticipated_cost(path, 1, 2) == path[3]


def test_cost_value():
    """EQ-COST-1, EQ-VAL-1, including the β_DA route into V through zⁱ_eff."""
    assert R.cost(0.2, 1, 0.5, 0.3) == pytest.approx(0.4)
    assert R.cost(0.2, 0, 0.5, 0.3, 0.1, 2.0) == pytest.approx(0.3)
    assert R.info_value(-1.0, R.da_bias(0.5, 0.25), 0.2, 0.4) == pytest.approx(0.2 + 0.3)


@given(st.floats(min_value=0, max_value=10), st.floats(min_value=0, max_value=10), pos, st.floats(min_value=0, max_value=2))
def test_urgency(t1, t2, tau, umax):
    """EQ-URG-1. Lean: Apgi.urgency_nonneg, Apgi.urgency_monotone, Apgi.urgency_off."""
    t1, t2 = min(t1, t2), max(t1, t2)
    assert 0 <= R.urgency(t1, umax, tau) <= R.urgency(t2, umax, tau) + 1e-15
    assert R.urgency(t2, 0.0, tau) == 0.0


@given(st.lists(st.floats(min_value=0, max_value=1), min_size=1, max_size=50),
       st.floats(min_value=0, max_value=0.5), st.floats(min_value=0, max_value=0.05))
def test_observation_model(props, g, lapse):
    """EQ-OBS-1, EQ-OBS-2. Lean: Apgi.hazard_survival_add, Apgi.pReport_mem_Icc, Apgi.pReport_monotone."""
    ph = R.p_hit(10.0, props, 0.01)
    surv = math.prod(1 - R.hazard_prob(10.0, b, 0.01) for b in props)
    assert 1 - ph == pytest.approx(surv, rel=1e-9, abs=1e-12)
    pr = R.p_report(ph, g, lapse)
    assert g - 1e-12 <= pr <= 1 - lapse + 1e-12


def test_cusp_fold_criteria():
    """EQ-CUSP-2 worked case: a = −3 gives folds at θ̃ = ±2 and hysteresis width 4u₀."""
    assert R.cusp_fold(-3.0) == pytest.approx(2.0)
    assert R.cusp_hysteresis_width(-3.0, 0.5) == pytest.approx(2.0)
    assert R.cusp_ignites(1.36, 0.35, -3.0, 0.5) and not R.cusp_ignites(1.34, 0.35, -3.0, 0.5)
    assert R.cusp_extinguishes(-0.66, 0.35, -3.0, 0.5) and not R.cusp_extinguishes(-0.64, 0.35, -3.0, 0.5)


@given(pos, pos, pos)
def test_norm_gains(pe, pi1, pi2):
    """EQ-NORM-1. Lean: Apgi.normGain_budget, Apgi.normGain_equal, Apgi.normGain_antitone_other."""
    a, b = R.norm_gains(pe, pi1)
    assert a + b == pytest.approx(2.0)
    assert R.norm_gains(pe, pe) == pytest.approx((1.0, 1.0))
    lo, hi = min(pi1, pi2), max(pi1, pi2)
    assert R.norm_gains(pe, hi)[0] <= R.norm_gains(pe, lo)[0] + 1e-12


def test_geo_values_match_ssot_table():
    """EQ-GEO-1, SSOT §12.2 table (k = 133): 50 ms, 6.65 s, 14.74 min, 32.68 h, 181.1 days.
    Lean: Apgi.geoTau_succ."""
    t = [R.geo_timescale(l) for l in range(5)]
    assert t[0] == pytest.approx(0.05)
    assert t[1] == pytest.approx(6.65)
    assert t[2] / 60 == pytest.approx(14.74, abs=0.005)
    assert t[3] / 3600 == pytest.approx(32.68, abs=0.005)
    assert t[4] / 86400 == pytest.approx(181.1, abs=0.05)
    assert R.geo_timescale(4, k=126) / 86400 == pytest.approx(145.9, abs=0.05)


@given(st.floats(min_value=0.001, max_value=1), st.floats(min_value=1, max_value=100),
       st.floats(min_value=0, max_value=1), st.floats(min_value=0, max_value=1))
def test_gradient_endpoints(tmin, ratio, h1, h2):
    """EQ-GRAD-1. Lean: Apgi.gradTau_zero, Apgi.gradTau_one, Apgi.gradTau_monotone."""
    tmax = tmin * ratio
    assert R.gradient_timescale(0, tmin, tmax) == pytest.approx(tmin)
    assert R.gradient_timescale(1, tmin, tmax) == pytest.approx(tmax)
    h1, h2 = min(h1, h2), max(h1, h2)
    assert R.gradient_timescale(h1, tmin, tmax) <= R.gradient_timescale(h2, tmin, tmax) * (1 + 1e-12)


def test_prec_ode_and_loop_gain():
    """EQ-PREC-ODE-1, EQ-PSI-SMALL-1, EQ-LOOP-1. Lean: Apgi.psiSmall_*, Apgi.loopGain_* .
    PD-LOOP-GAIN numbers from SSOT §12.5: defaults 2 × 10⁴; τ_Π = 5 s gives 0.5; scaled couplings 0.02."""
    assert R.psi_small(0.0, 2.0) == 0.0 and abs(R.psi_small(2.0, 3.0)) < 1  # float tanh rounds to 1 past ~19
    assert R.psi_small(-0.7, 2.0) == -R.psi_small(0.7, 2.0)
    assert R.loop_gain(0.1, 0.05, 1000.0, 2.0) == pytest.approx(2e4)
    assert R.loop_gain(0.1, 0.05, 5.0, 2.0) == pytest.approx(0.5)
    for tau in (1.0, 5.0, 1000.0):
        assert R.loop_gain(0.1 / tau, 0.05 / tau, tau, 2.0) == pytest.approx(0.02)
    assert R.loop_gain(0.5, 0.2, 1.0, 3.0) == pytest.approx(0.9)
    assert R.loop_gain(0.5, 0.2, 1.0, math.sqrt(10)) == pytest.approx(1.0)
    # α_Π = 0 and equal neighbours: pure decay
    assert R.prec_ode_rate(2.0, 1.0, 2.0, 0.0, 5.0, 0.0, 0.1, 0.05, 2.0) == pytest.approx(-0.4)


def test_ms_aggregation():
    """EQ-MS-1, EQ-MS-2, EQ-MS-3. Lean: Apgi.msGlobal_le, Apgi.msGlobal_ge."""
    d = [R.ms_drive(1.0, x, g) for x, g in ((0.5, 1.0), (-0.2, 0.5), (1.5, 1.0), (0.0, 1.0))]
    w = [0.25] * 4
    s = R.ms_global(w, d)
    assert min(d) <= s <= max(d)
    with pytest.raises(ValueError):
        R.ms_global([0.5, 0.6], [1.0, 1.0])
    assert R.ms_integrated(w, [1] * 4, [1] * 4, d) == pytest.approx(s)
    m_psi = 0.6
    assert R.psi_excess(0.0, 1, 1, 2, 2, m_psi) == pytest.approx(-m_psi)


@given(st.floats(min_value=0, max_value=1), st.floats(min_value=0, max_value=5),
       st.floats(min_value=0.1, max_value=10), st.floats(min_value=-7, max_value=7))
def test_ms_threshold_band(theta0, kd, pi, phase):
    """EQ-MS-4. Lean: Apgi.msTarget_band."""
    t = R.ms_threshold_target(theta0, kd, pi, 10.0, phase)
    assert 0.5 * theta0 - 1e-12 <= t <= 1.5 * theta0 + 1e-12


def test_kuramoto():
    """EQ-KUR-1, EQ-KUR-2. Lean: Apgi.kuramotoGate_mem_Icc. R ≈ 0.7 gives Γ ≈ 0.5 (SSOT §12.8)."""
    R1, G1 = R.kuramoto_order([0.3] * 8)
    assert R1 == pytest.approx(1.0) and G1 == pytest.approx(1.0)
    R0, G0 = R.kuramoto_order([0, math.pi / 2, math.pi, 3 * math.pi / 2])
    assert R0 == pytest.approx(0.0, abs=1e-12)
    rng = np.random.default_rng(10101)
    for _ in range(50):
        r, g = R.kuramoto_order(rng.uniform(-2, 2, size=12))
        assert 0 <= g <= r <= 1 + 1e-12
    assert 0.7 ** 2 == pytest.approx(0.49)
    assert R.kuramoto_rate(0, [0.4] * 5, 2.0, 1.5) == pytest.approx(2.0)


def test_reservoir():
    """EQ-RES-1, EQ-RES-2: tanh state bounded; readout rectified, never negative."""
    rng = np.random.default_rng(20202)
    W = rng.normal(size=(20, 20))
    W *= 0.9 / max(abs(np.linalg.eigvals(W)))
    x = np.zeros(20)
    for t in range(30):
        x = R.reservoir_step(x, W, rng.normal(size=(20, 1)), rng.normal())
        assert np.all(np.abs(x) < 1)
        assert R.reservoir_readout(rng.normal(size=20), x) >= 0.0


def test_bridges():
    """EQ-BR-1…3, R12 worked example: 6 × 10⁻³ J over ≈ 3 behavioural bits gives κ_beh ≈ 2 × 10¹⁶ ATP/bit,
    > 12 orders of magnitude above the κ_syn retirement band [10, 10⁴]."""
    e = R.energy_per_bit(6e-3, 3.0)
    kb = R.kappa_atp_per_bit(e)
    assert 1.5e16 < kb < 3e16
    assert math.log10(kb / 1e4) > 12
    assert R.kappa_atp_per_bit(6e-3) == pytest.approx(7.2e16, rel=0.05)
    assert R.erasure_ratio(R.landauer(310.0), 1.0) == pytest.approx(1.0)


# ------------------------------------------ twins of Apgi/Coverage.lean ----
@given(f, f, st.floats(min_value=0.01, max_value=5), st.floats(min_value=0, max_value=3))
def test_twin_standardize(mu, d, sd, a):
    """EQ-STD-1. Lean: Apgi.standardize_at_mean, Apgi.standardize_odd, Apgi.standardize_monotone."""
    assert R.standardize(mu, mu, sd) == 0.0
    assert R.standardize(mu + d, mu, sd) == pytest.approx(-R.standardize(mu - d, mu, sd), abs=1e-9)
    assert R.standardize(mu, mu, sd) <= R.standardize(mu + a, mu, sd)
    assert R.prediction_error(mu, mu) == 0.0 and R.prediction_error(mu, d) == -R.prediction_error(d, mu)


@given(f, st.floats(min_value=0, max_value=4), f, st.floats(min_value=0.0, max_value=1.0),
       st.floats(min_value=1e-4, max_value=1), st.floats(min_value=0.1, max_value=20))
def test_twin_ema(mu, v, eps, a, dt, T):
    """EQ-EMA-1/2. Lean: Apgi.emaAlpha_mem_Ioo, Apgi.emaMean_mem_Icc, Apgi.emaVar_nonneg, Apgi.emaVar_at_mean."""
    assert 0 < R.ema_alpha(dt, T) < 1
    m2, v2 = R.ema_update(mu, v, eps, a)
    assert min(mu, eps) - 1e-12 <= m2 <= max(mu, eps) + 1e-12
    assert v2 >= 0
    assert R.ema_update(mu, v, mu, a)[1] == pytest.approx((1 - a) * v)


@given(st.floats(min_value=0.1, max_value=10), st.floats(min_value=0.1, max_value=10))
def test_twin_prec_rel(pe, pbar):
    """EQ-PREC-REL-1. Lean: Apgi.precRel_self, Apgi.precRel_mem_Icc."""
    assert R.prec_rel(pbar, pbar) == 1.0
    assert 0.1 / pbar - 1e-12 <= R.prec_rel(pe, pbar) <= 10.0 / pbar + 1e-12


@given(st.floats(min_value=0.1, max_value=10), st.floats(min_value=0.05, max_value=1))
def test_twin_soft_floor(k, theta):
    """EQ-FLOOR-1. Lean: Apgi.floor_le_iff, Apgi.floor_le_one_percent_iff (γ_sig·θ ≥ log 99 ≈ 4.595)."""
    if abs(k * theta - math.log(99)) > 1e-9:
        assert (R.ignition_prob(k, 0.0, theta) <= 0.01) == (k * theta >= math.log(99))
    assert math.log(99) == pytest.approx(4.595, abs=5e-4)


def test_twin_step_rule_and_allostatic_path():
    """EQ-STEP-1, EQ-ALLO-C1, EQ-ALLO-R1. Lean: Apgi.euler_step_mem_Icc_of_stepRule,
    Apgi.alloPath_hasDerivAt, Apgi.alloReduced_hasDerivAt (finite-difference check of the closed form)."""
    assert R.step_rule(0.01, 0.3, 20.0, 1.0)
    th0, tau, D, thi = 0.35, 20.0, 0.004, 0.85
    path = lambda t: (th0 + tau * D) + (thi - (th0 + tau * D)) * math.exp(-t / tau)
    for t in (0.0, 1.0, 17.0):
        h = 1e-5
        deriv = (path(t + h) - path(t - h)) / (2 * h)
        assert deriv == pytest.approx(R.allostatic_rate(path(t), th0, tau, 1.0, D, 0.0), rel=1e-6)


def test_twin_cost_value_and_ode():
    """EQ-COST-1, EQ-VAL-1, EQ-PREC-ODE-1, EQ-ANT-1. Lean: Apgi.valueV_nonneg, Apgi.costC_monotone_ignition,
    Apgi.thresholdStep_antitone_value, Apgi.precOdeRate_strictAnti, Apgi.precOdeRate_pure_decay, Apgi.anticipated_zero."""
    assert R.info_value(-1.3, 0.4, 0.2, 0.7) >= 0
    assert R.cost(0.3, 0, 0.2, 0.5) <= R.cost(0.3, 1, 0.2, 0.5)
    lo = R.threshold_step(0.4, 0.35, 0.1, 0.2, 0.5, 0, 0, 0.01, 20)
    hi = R.threshold_step(0.4, 0.35, 0.1, 0.2, 0.1, 0, 0, 0.01, 20)
    assert lo <= hi
    rates = [R.prec_ode_rate(p, 0.4, 1.0, 0.2, 5.0, 0.3, 0.1 / 5, 0.05 / 5, 2.0) for p in (0.5, 1.0, 2.0)]
    assert rates[0] > rates[1] > rates[2]
    assert R.prec_ode_rate(2.0, 9.9, 2.0, 0.0, 5.0, 0.0, 0.3, 0.1, 2.0) == pytest.approx(-0.4)
    assert R.anticipated_cost([0.1, 0.2], 0, 0) == 0.1


@given(st.floats(min_value=0, max_value=3), st.floats(min_value=0.5, max_value=2), st.floats(min_value=1, max_value=5), f)
def test_twin_ms_drive(prel, a, g, z):
    """EQ-MS-1, EQ-MS-3. Lean: Apgi.msDrive_sign_symmetric, Apgi.msDrive_gate_one, Apgi.msDrive_gate_monotone."""
    m = 0.6
    assert R.ms_drive(prel, R.psi_excess(-z, a, a, g, g, m)) == pytest.approx(R.ms_drive(prel, R.psi_excess(z, a, a, g, g, m)))
    assert R.ms_drive(prel, 0.4, 1.0) == pytest.approx(prel * 0.4)
    assert R.ms_drive(prel, 0.4, 0.3) <= R.ms_drive(prel, 0.4, 0.9) + 1e-15


def test_twin_kuramoto_reservoir_bridges():
    """EQ-KUR-2, EQ-RES-1/2, EQ-LAND-1, EQ-BR-1…3. Lean: Apgi.kurRate_synchronized, Apgi.resStep_abs_lt,
    Apgi.resReadout_nonneg, Apgi.landauer_310K_within_tolerance, Apgi.landauer_300K_below,
    Apgi.kappa_of_energy, Apgi.erasureRatio_ge_one_iff."""
    assert R.kuramoto_rate(2, [0.7] * 6, 3.0, 2.0) == pytest.approx(3.0)
    assert abs(R.landauer(310.0) - 2.97e-21) <= 0.005 * 2.97e-21
    assert R.landauer(300.0) < 2.88e-21
    assert R.kappa_atp_per_bit(R.energy_per_bit(6e-3, 3.0)) == pytest.approx(6e-3 / (3.0 * 8.3e-20))
    EL = R.landauer(310.0)
    assert (R.erasure_ratio(2 * EL, 1.0) >= 1) and (R.erasure_ratio(0.5 * EL, 1.0) < 1)
