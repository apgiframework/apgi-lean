"""Theorem-test pairing (plan edit C3).

Each test is the float64 twin of one Lean theorem in Apgi/Pilot.lean. Lean
establishes the mathematics over ℝ; these tests check that the Python
reference code obeys the same statement, within float64 tolerance.
"""
import math

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import apgi_ref as R
import registry

P = registry.params()
BAND_LO = float(P["theta_operating_lower"]["value"])
BAND_HI = float(P["theta_operating_upper"]["value"])
FLOOR = float(P["theta_floor"]["value"])

fin = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
au = st.floats(min_value=0.0, max_value=20.0, allow_nan=False)
unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
EPS = 1e-12
settings.register_profile("ci", max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("ci")


@given(fin, fin, fin)
def test_ignites_antitone_threshold(S, t1, t2):
    """Lean: Apgi.ignites_antitone_threshold."""
    t1, t2 = min(t1, t2), max(t1, t2)
    if R.ignites(S, t2):
        assert R.ignites(S, t1)


@given(unit.map(lambda x: 10 * x), unit.map(lambda x: 10 * x), fin, fin)
def test_ignites_monotone_precision(p1, p2, eps, theta):
    """Lean: Apgi.ignites_monotone_precision."""
    p1, p2 = min(p1, p2), max(p1, p2)
    if R.ignites(R.signal(p1, eps), theta):
        assert R.ignites(R.signal(p2, eps), theta)


@given(st.floats(0, 50), au, au, au)
def test_ignition_prob_antitone_threshold(k, S, t1, t2):
    """Lean: Apgi.ignitionProb_antitone_threshold (requires k ≥ 0)."""
    t1, t2 = min(t1, t2), max(t1, t2)
    assert R.ignition_prob(k, S, t2) <= R.ignition_prob(k, S, t1) + 1e-15


def test_ignition_prob_needs_nonneg_k():
    """The k ≥ 0 hypothesis is load-bearing: with k < 0 monotonicity reverses."""
    assert R.ignition_prob(-1, 3, 4) > R.ignition_prob(-1, 3, 2)


@given(au, au, unit)
def test_clamped_update_floor(theta, target, gain):
    """Lean: Apgi.clampedUpdate_floor."""
    assert R.clamped_update(theta, target, gain) >= R.THETA_FLOOR


def test_operating_range_counterexample():
    """Lean: Apgi.operatingRange_not_invariant, witness (θ, target, gain) = (θ_lower, θ_floor, 1)."""
    assert R.clamped_update(BAND_LO, FLOOR, 1.0) < BAND_LO


@given(st.floats(BAND_LO, BAND_HI), st.floats(BAND_LO, BAND_HI), unit)
def test_operating_range_invariant_of_target(theta, target, gain):
    """Lean: Apgi.operatingRange_invariant_of_target."""
    v = R.clamped_update(theta, target, gain)
    assert BAND_LO - EPS <= v <= BAND_HI + EPS


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(-3, 3))
def test_cusp_derivative(a, theta, x):
    """Lean: Apgi.cuspV_hasDerivAt (central difference vs closed form)."""
    h = 1e-5
    num = (R.cusp_V(a, theta, x + h) - R.cusp_V(a, theta, x - h)) / (2 * h)
    assert num == pytest.approx(R.cusp_dV(a, theta, x), rel=1e-6, abs=1e-6)


@given(st.floats(0, 10), st.floats(-10, 10))
def test_cusp_unique_equilibrium(a, theta):
    """Lean: Apgi.cusp_unique_equilibrium (a ≥ 0 ⇒ one equilibrium)."""
    assert len(R.cusp_equilibria(a, theta)) == 1


def test_cusp_two_equilibria_witness():
    """Lean: Apgi.cusp_two_equilibria_witness (a = −1, θ = 0)."""
    assert R.cusp_dV(-1, 0, 0) == 0 and R.cusp_dV(-1, 0, 1) == 0


@given(st.floats(-10, -0.01), st.floats(-10, 10))
def test_cusp_three_equilibria(a, theta):
    """Lean: Apgi.cusp_three_equilibria (a < 0 ∧ 4a³ + 27θ² < 0 ⇒ three
    distinct equilibria, each a root of x³ + a x + θ). Near-degenerate cases skipped."""
    d = R.cusp_discriminant(a, theta)
    assume(d < -1e-3 * max(1.0, abs(a) ** 3))
    roots = R.cusp_equilibria(a, theta)
    assert len(roots) == 3 and roots[0] < roots[1] < roots[2]
    scale = max(1.0, abs(a), abs(theta))
    for x in roots:
        assert abs(R.cusp_dV(a, theta, x)) <= 1e-8 * scale * max(1.0, abs(x)) ** 3


@given(st.floats(-10, -0.01), st.floats(-10, 10))
def test_cusp_discriminant(a, theta):
    """Both directions of the discriminant rule (Lean: Apgi.cusp_three_equilibria_iff):
    with a < 0, three equilibria iff 4a³ + 27θ² < 0."""
    d = R.cusp_discriminant(a, theta)
    assume(abs(d) > 1e-3 * max(1.0, abs(a) ** 3))
    assert len(R.cusp_equilibria(a, theta)) == (3 if d < 0 else 1)


@given(st.floats(-5, 5), st.floats(0, 10), unit, unit, unit)
def test_convex_update_bounded(lo, width, fx, fu, gain):
    """Lean: Apgi.convex_update_mem_Icc."""
    hi = lo + width
    x, u = lo + fx * width, lo + fu * width
    v = R.convex_update(x, u, gain)
    tol = EPS * max(1.0, abs(lo), abs(hi))
    assert lo - tol <= v <= hi + tol


@given(st.floats(0, 8), st.floats(0, 8), st.floats(1e-3, 10), unit)
def test_euler_step_bounded(x, u, tau, frac):
    """Lean: Apgi.euler_step_mem_Icc (0 ≤ dt ≤ τ)."""
    lo, hi = min(x, u), max(x, u)
    v = R.euler_step(x, u, frac * tau, tau)
    assert lo - EPS * 10 <= v <= hi + EPS * 10


def test_euler_precondition_is_load_bearing():
    """With dt > τ the step overshoots: the Lean hypothesis is necessary."""
    assert R.euler_step(0.0, 1.0, dt=3.0, tau=1.0) > 1.0


@given(st.floats(BAND_LO, BAND_HI), st.floats(BAND_LO, BAND_HI), st.floats(0, 100), st.floats(0.05, 60))
def test_decay_step_bounded(theta, theta0, dt, tau):
    """Lean: Apgi.decay_step_mem_Icc — exact decay toward θ₀ in the band stays in the band."""
    v = R.decay_step(theta, theta0, dt, tau)
    assert BAND_LO - EPS <= v <= BAND_HI + EPS


def test_decay_needs_no_step_bound():
    """Contrast with Euler: at dt = 3τ the exact step stays between θ and θ₀
    (Lean: Apgi.decayGain_mem_Icc has no dt ≤ τ hypothesis)."""
    v = R.decay_step(0.0, 1.0, dt=3.0, tau=1.0)
    assert 0.0 <= v <= 1.0
    assert R.euler_step(0.0, 1.0, dt=3.0, tau=1.0) > 1.0


@given(st.floats(-3, 3), st.floats(0.05, 3), st.floats(0.05, 3))
def test_cusp_three_equilibria_converse(x1, d1, d2):
    """Lean: Apgi.cusp_three_equilibria_converse. Build x³ + a x + θ from three
    distinct roots summing to zero; its discriminant must be negative."""
    x2 = x1 + d1
    shift = (x1 + x2 + (x2 + d2)) / 3
    r = [x1 - shift, x2 - shift, x2 + d2 - shift]
    a = r[0] * r[1] + r[0] * r[2] + r[1] * r[2]
    theta = -r[0] * r[1] * r[2]
    gap = min(d1, d2)
    assert R.cusp_discriminant(a, theta) < 0
    assert R.cusp_discriminant(a, theta) == pytest.approx(-((r[0] - r[1]) * (r[0] - r[2]) * (r[1] - r[2])) ** 2, rel=1e-9, abs=1e-9 * gap)


# ------------------------------------------------- specification 0.3.0 ----
pos = st.floats(1e-3, 50, allow_nan=False)


@given(pos, pos)
def test_leak_gain_in_open_unit_interval(dt, tau):
    """Lean: Apgi.leakGain_mem_Ioo (dt > 0, τ_S > 0)."""
    assume(dt / tau < 30)  # beyond this, 1 − e^{−x} rounds to 1.0 in float64
    assert 0.0 < R.leak_gain(dt, tau) < 1.0


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(0, 100), pos)
def test_leak_step_bounded(S, u, dt, tau):
    """Lean: Apgi.leak_step_mem_Icc (any dt ≥ 0)."""
    lo, hi = min(S, u), max(S, u)
    v = R.leak_step(S, u, R.leak_gain(dt, tau))
    assert lo - 1e-12 <= v <= hi + 1e-12


@given(st.floats(-5, 5), st.floats(-5, 5), st.floats(0, 5), pos)
def test_leak_two_steps(S, u, dt, tau):
    """Lean: Apgi.leak_two_steps (dt-invariance of the exact integrator)."""
    g = R.leak_gain(dt, tau)
    assert R.leak_step(R.leak_step(S, u, g), u, g) == pytest.approx(
        R.leak_step(S, u, R.leak_gain(2 * dt, tau)), rel=1e-9, abs=1e-12)


@given(st.floats(0, 200), unit, st.floats(0, 1))
def test_hazard_prob_in_unit_interval(r, B, dt):
    """Lean: Apgi.hazardProb_mem_Icc."""
    assert 0.0 <= R.hazard_prob(r, B, dt) <= 1.0


@given(st.floats(0, 200), unit, st.floats(0, 0.5))
def test_hazard_two_steps(r, B, dt):
    """Lean: Apgi.hazard_two_steps, (1 − p_dt)² = 1 − p_2dt (task 26)."""
    assert (1 - R.hazard_prob(r, B, dt)) ** 2 == pytest.approx(1 - R.hazard_prob(r, B, 2 * dt), rel=1e-9, abs=1e-15)


@given(st.floats(0, 200), unit, st.floats(0, 0.05), st.integers(0, 50))
def test_hazard_n_steps(r, B, dt, n):
    """Lean: Apgi.hazard_n_steps: n steps of dt equal one step of n·dt."""
    assert (1 - R.hazard_prob(r, B, dt)) ** n == pytest.approx(1 - R.hazard_prob(r, B, n * dt), rel=1e-9, abs=1e-15)


@given(st.floats(0, 200), st.floats(0, 1), unit, unit)
def test_hazard_monotone_propensity(r, dt, b1, b2):
    """Lean: Apgi.hazardProb_monotone_propensity."""
    b1, b2 = min(b1, b2), max(b1, b2)
    assert R.hazard_prob(r, b1, dt) <= R.hazard_prob(r, b2, dt) + 1e-15


@given(st.floats(2, 7.5), st.floats(0, 200), st.floats(0, 1), au, au, au)
def test_hazard_antitone_threshold(k, r, dt, S, t1, t2):
    """Lean: Apgi.hazard_antitone_threshold (γ_sig ≥ 0 carries CL-1 through the hazard)."""
    t1, t2 = min(t1, t2), max(t1, t2)
    assert R.hazard_prob(r, R.ignition_prob(k, S, t2), dt) <= R.hazard_prob(r, R.ignition_prob(k, S, t1), dt) + 1e-15


def test_per_step_bernoulli_is_not_dt_invariant():
    """Math Spec p22: treating Bₜ as a per-step probability makes window ignition depend on dt
    (Bₜ = 0.05, 300 ms window: 0.79 at dt = 10 ms, above 0.999 at dt = 1 ms). The hazard does not."""
    B, window = 0.05, 0.3
    per_step = {dt: 1 - (1 - B) ** round(window / dt) for dt in (0.01, 0.001)}
    assert per_step[0.01] == pytest.approx(0.79, abs=0.005) and per_step[0.001] > 0.999
    r = 10.0
    hz = {dt: 1 - (1 - R.hazard_prob(r, B, dt)) ** round(window / dt) for dt in (0.01, 0.001)}
    assert hz[0.01] == pytest.approx(hz[0.001], rel=1e-9)


@given(st.floats(-10, 10), st.floats(0, 10))
def test_ne_clamp_bound(gamma, g):
    """Lean: Apgi.neClamp_bound, Apgi.neClamp_nonneg."""
    c = R.ne_clamp(gamma, g)
    assert c >= 0 and abs(gamma) * c <= R.NE_BOUND * (1 + 1e-12)


@given(st.floats(-10, 10), st.floats(0, 10))
def test_ne_factor_band(gamma, g):
    """Lean: Apgi.neFactor_band, 1 + γ_NE·g_NE ∈ [0.5, 1.5]."""
    f = R.ne_factor(gamma, g)
    assert 0.5 - 1e-12 <= f <= 1.5 + 1e-12


@given(st.floats(-10, 10), st.floats(0, 10))
def test_ne_clamp_identity_within_bound(gamma, g):
    """Lean: Apgi.neClamp_of_le."""
    assume(abs(gamma) * g <= R.NE_BOUND)
    assert R.ne_clamp(gamma, g) == g


thr = st.floats(0, 2)


@given(thr, st.floats(BAND_LO, BAND_HI), st.floats(0, 1), st.floats(-2, 2), st.floats(-2, 2),
       st.floats(0, 1), unit, st.floats(0, 1), st.floats(10, 30))
def test_threshold_step_floor(theta, theta0, eta, C, V, delta, B, dt, tau):
    """Lean: Apgi.thresholdStep_floor."""
    assert R.threshold_step(theta, theta0, eta, C, V, delta, B, dt, tau) >= FLOOR


@given(thr, st.floats(BAND_LO, BAND_HI), st.floats(0, 1), st.floats(-2, 2), st.floats(-2, 2),
       st.floats(0, 1), unit, unit, st.floats(0, 1), st.floats(10, 30))
def test_threshold_step_monotone_ignition(theta, theta0, eta, C, V, delta, b1, b2, dt, tau):
    """Lean: Apgi.thresholdStep_monotone_ignition (δ_reset ≥ 0)."""
    b1, b2 = min(b1, b2), max(b1, b2)
    args = (theta, theta0, eta, C, V, delta)
    assert R.threshold_step(*args, b1, dt, tau) <= R.threshold_step(*args, b2, dt, tau) + 1e-12


@given(thr, st.floats(BAND_LO, BAND_HI), st.floats(0, 1), st.floats(-2, 2), st.floats(-2, 2),
       st.floats(0, 1), unit, st.floats(0, 1), st.floats(10, 30))
def test_threshold_step_monotone_drive(theta, theta0, eta, d1, d2, delta, B, dt, tau):
    """Lean: Apgi.thresholdStep_monotone_drive (η_θ ≥ 0), drive d = C − V."""
    d1, d2 = min(d1, d2), max(d1, d2)
    lo = R.threshold_step(theta, theta0, eta, d1, 0.0, delta, B, dt, tau)
    hi = R.threshold_step(theta, theta0, eta, d2, 0.0, delta, B, dt, tau)
    assert lo <= hi + 1e-12


@given(st.floats(0.5, 2.0), st.floats(0.5, 2.0), st.floats(1.0, 5.0), st.floats(1.0, 5.0), st.floats(-5, 5))
def test_psi_bounded(ap, am, gp, gm, z):
    """Lean: Apgi.psi_abs_lt (float tanh may round to ±1, hence ≤)."""
    assert abs(R.psi(ap, am, gp, gm, z)) <= max(ap, am)


@given(st.floats(0.5, 2.0), st.floats(1.0, 5.0), st.floats(-5, 5))
def test_psi_symmetric_limit(a, g, z):
    """Lean: Apgi.psi_symmetric."""
    assert R.psi(a, a, g, g, z) == pytest.approx(a * math.tanh(g * z), rel=1e-15, abs=1e-15)


@given(st.floats(0.5, 2.0), st.floats(1.0, 5.0), st.floats(-5, 5))
def test_psi_odd_when_symmetric(a, g, z):
    """Lean: Apgi.psi_odd_of_symmetric."""
    assert R.psi(a, a, g, g, -z) == pytest.approx(-R.psi(a, a, g, g, z), rel=1e-15, abs=1e-15)


@given(st.floats(0, 2), st.floats(0.1, 10), st.floats(0.1, 1.2), st.floats(-2, 2), st.floats(-2, 2))
def test_prec_eff_monotone_marker(g, pb, beta, m1, m2):
    """Lean: Apgi.precEff_monotone_marker, Apgi.precEff_nonneg (β_SM ≥ 0)."""
    m1, m2 = min(m1, m2), max(m1, m2)
    assert 0 <= R.prec_eff(g, pb, beta, m1) <= R.prec_eff(g, pb, beta, m2) * (1 + 1e-15)


@given(st.floats(-1e6, 1e6))
def test_prec_clamp_bounds(x):
    """Lean: Apgi.precClamp_mem_Icc with the canonical clamp [0.1, 10] AU."""
    assert 0.1 <= R.prec_clamp(0.1, 10.0, x) <= 10.0


# ----------------------------------------------------- task 55: Apgi/Core.lean ----
zz = st.floats(min_value=-6.0, max_value=6.0, allow_nan=False)
pp = st.floats(min_value=0.0, max_value=10.0, allow_nan=False)


@given(zz, pp, pp)
def test_drive_term_monotone_iff(z, p1, p2):
    """Lean: Apgi.driveTerm_monotone_iff, Apgi.driveTerm_strictAnti_of_lt."""
    p1, p2 = min(p1, p2), max(p1, p2)
    lo, hi = R.drive_term(p1, z), R.drive_term(p2, z)
    if abs(z) >= R.M0:
        assert lo <= hi + EPS
    elif p1 < p2:
        assert hi < lo


@given(zz, pp, pp, zz, zz, fin)
def test_ignites_drive_monotone_precision(ze, p1, p2, pi, zi, theta):
    """Lean: Apgi.ignites_drive_monotone_precision."""
    assume(abs(ze) >= R.M0)
    p1, p2 = min(p1, p2), max(p1, p2)
    if R.ignites(R.drive(p1, ze, pi, zi), theta):
        assert R.drive(p2, ze, pi, zi) >= R.drive(p1, ze, pi, zi) - EPS


@given(pp, zz, pp, zz)
def test_drive_sign_symmetric_twin(pe, ze, pi, zi):
    """Lean: Apgi.drive_sign_symmetric, Apgi.drive_zero_at_m0."""
    assert R.drive(pe, -ze, pi, -zi) == R.drive(pe, ze, pi, zi)
    assert R.drive(1.0, R.M0, 1.0, -R.M0) == pytest.approx(0.0, abs=EPS)


def test_mean_abs_std_normal():
    """Lean: Apgi.meanAbsStdNormal_eq, Apgi.integral_abs_mul_exp_neg_half_sq."""
    assert R.mean_abs_std_normal() == pytest.approx(math.sqrt(2.0 / math.pi), rel=1e-9)
    assert R.mean_abs_std_normal() == pytest.approx(R.M0, rel=1e-9)


@given(st.floats(min_value=-5, max_value=5), st.floats(min_value=0.05, max_value=5))
def test_ignition_prob_hard_threshold_limit(theta, gap):
    """Lean: Apgi.ignitionProb_at_threshold, Apgi.ignitionProb_tendsto_one, Apgi.ignitionProb_tendsto_zero."""
    assert R.ignition_prob(7.5, theta, theta) == 0.5
    k = 2000.0 / gap
    assert R.ignition_prob(k, theta + gap, theta) > 1 - 1e-12
    assert R.ignition_prob(k, theta - gap, theta) < 1e-12


@given(st.floats(min_value=-3, max_value=3), st.floats(min_value=-3, max_value=3),
       st.floats(min_value=-0.5, max_value=0.5), st.floats(min_value=0, max_value=2),
       st.floats(min_value=0, max_value=2), st.floats(min_value=0.0, max_value=2.0))
def test_readout_noninterference(x_e, x_i, gamma_ne, beta_5ht, u_urg, kappa):
    """Lean: Apgi.coreStep_readout_noninterference, Apgi.coreStep_theta_from_state.
    Same sampled B ⇒ same successor state, whatever the read-out modulators. |γ_NE| ≤ 0.5 keeps the
    NE clamp inactive: the clamped g_NE is shared with Πⁱ_eff (EQ-NE-1), so it is not a pure read-out."""
    s0 = R.core_state()
    a, _ = R.core_step(s0, x_e, x_i, u=1.0)
    b, _ = R.core_step(s0, x_e, x_i, {"gamma_ne": gamma_ne, "beta_5ht": beta_5ht, "u_urg": u_urg,
                                     "kappa_up": kappa}, u=1.0)
    for key in ("S", "theta", "r"):
        assert a[key] == b[key]


@given(st.floats(min_value=0.0, max_value=1.0), st.floats(min_value=0.1, max_value=0.5),
       st.floats(min_value=0.0, max_value=2.0), st.floats(min_value=0.001, max_value=1.0))
def test_exactly_once_increments(theta, delta, C, dt):
    """Lean: Apgi.decay_allostatic_exactly_once, Apgi.coreStep_refractory_exactly_once,
    Apgi.coreStep_retention_exactly_once."""
    t1 = R.decay_step(R.allostatic_step(theta, 0.1, C, 0.0, delta, 1), 0.35, dt, 20.0)
    t0 = R.decay_step(R.allostatic_step(theta, 0.1, C, 0.0, delta, 0), 0.35, dt, 20.0)
    assert t1 - t0 == pytest.approx(delta * math.exp(-dt / 20.0), rel=1e-9)
    r1 = R.refractory_step(0.2, 1, dt, 0.3, delta)
    r0 = R.refractory_step(0.2, 0, dt, 0.3, delta)
    assert r1 - r0 == pytest.approx(delta, rel=1e-12)
    assert R.reset(R.reset(1.0, 1, 0.3), 0, 0.3) == pytest.approx(0.3)


@given(st.floats(min_value=-5, max_value=-0.01), st.floats(min_value=-10, max_value=10))
def test_cusp_fold_iff_three_equilibria(a, th):
    """Lean: Apgi.cusp_discriminant_iff_fold."""
    fold = R.cusp_fold(a)
    assume(abs(abs(th) - fold) > 1e-6 * max(1.0, fold))
    assert (R.cusp_discriminant(a, th) < 0) == (abs(th) < fold)
    assert (len(R.cusp_equilibria(a, th)) == 3) == (abs(th) < fold)


@given(st.floats(min_value=-5, max_value=-0.05), st.floats(min_value=0.1, max_value=3),
       st.floats(min_value=-2, max_value=2), st.floats(min_value=1e-3, max_value=2))
def test_cusp_monostable_past_folds(a, u0, theta_eff, extra):
    """Lean: Apgi.cusp_monostable_of_ignition, Apgi.cusp_monostable_of_extinction."""
    w = R.cusp_hysteresis_width(a, u0) / 2.0
    for S in (theta_eff + w + extra, theta_eff - w - extra):
        assert len(R.cusp_equilibria(a, (theta_eff - S) / u0)) == 1
