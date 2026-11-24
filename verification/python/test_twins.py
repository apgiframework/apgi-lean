"""Theorem-test pairing (plan edit C3).

Each test is the float64 twin of one Lean theorem in Apgi/Pilot.lean. Lean
establishes the mathematics over ℝ; these tests check that the Python
reference code obeys the same statement, within float64 tolerance.
"""
import math

import pytest
from hypothesis import assume, given, settings
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
settings.register_profile("ci", max_examples=500, deadline=None)
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
    """Both directions of the discriminant rule (the converse is classical and
    not in Lean): with a < 0, three equilibria iff 4a³ + 27θ² < 0."""
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
