"""TC-08 parameter recovery and identifiability (SSOT §17, §23).

Two parts.

1. Structural degeneracies TC-08a–c. They are exact and proved in Apgi/Identifiability.lean;
   the tests here are their float64 twins against apgi_ref:
   * TC-08a: a common offset of S and θ_eff leaves the event likelihood unchanged
     (Lean: Apgi.hazardLik_shift);
   * TC-08b: g_NE, Πⁱ and exp(β_SM·M̂) enter only as a product (Lean: Apgi.traj_gain_product);
   * TC-08c: S′ = aS + b, θ′ = aθ + b, γ′ = γ/a preserve the likelihood
     (Lean: Apgi.hazardLik_rescale, Apgi.hazardLik_not_injective).

2. The §17 recovery gate on synthetic data, after the degeneracies are handled as §17 requires
   (S anchored at 0 for zero prediction error, which removes TC-08a; the precision reference
   fixed numerically, which removes TC-08c). Recovered parameters: θ_eff and γ_sig of the
   observation model EQ-HAZARD-1 → EQ-OBS-1 → EQ-OBS-2. Gate (registry): Pearson r > r_HIGH
   (0.85, registered target) and median range-scaled error < err_gate (0.2, proposed reading).

Scope limits, stated so they are not overread:
* The gate is run for the decision stage (θ_eff, γ_sig) only. η_θ, τ_θ, c₁, v₁, v₂ and the
  neuromodulatory gains (TC-08d–g, the declared posterior trade-offs) need fits of the full
  pipeline to behavioral data and are not covered (task 62b).
* The design constants below (stimulus levels, trials, r_max·T_W, guess and lapse rates) are
  synthetic-study choices, not registered values. λ_lapse lies in its registered range
  [0, 0.05]; the guess rate g is not yet a registry row (task 54b).
* Passing recovery is not evidence for APGI, and failing it would not falsify APGI (§17).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import apgi_ref as R
import registry

P = registry.params()
R_HIGH = float(P["r_HIGH"]["value"])  # 0.85
ERR_GATE = float(P["err_gate"]["value"])  # 0.2
THETA_LO, THETA_HI = (float(P["theta_baseline"]["range"][k]) for k in ("lo", "hi"))  # 0.25, 0.85 AU
GAMMA_LO, GAMMA_HI = (float(P["gamma_sig"]["range"][k]) for k in ("lo", "hi"))  # 2, 7.5 1/AU
LAPSE = 0.02
assert float(P["lambda_lapse"]["range"]["lo"]) <= LAPSE <= float(P["lambda_lapse"]["range"]["hi"])

# Synthetic-study design constants (not registered values).
GUESS = 0.02
RATE_WINDOW = 3.0  # r_max·T_W: P(hit) = 1 − exp(−3·Bₜ) for a propensity held over the window
LEVELS = np.linspace(0.0, 1.5, 16)  # anchored drive S (AU), S = 0 at zero prediction error
TRIALS = 60  # per level
N_SUBJECTS = 60
SEED = 20261127


# ---------------------------------------------------------------- observation model

def p_report(levels, theta, gamma):
    """EQ-IGN-2 → EQ-HAZARD-1 → EQ-OBS-1 → EQ-OBS-2, vectorized (numpy broadcasting)."""
    b = 1.0 / (1.0 + np.exp(-gamma * (levels - theta)))
    phit = -np.expm1(-RATE_WINDOW * b)
    return GUESS + (1.0 - GUESS - LAPSE) * phit


def test_vectorized_model_matches_reference():
    """The vectorized model is apgi_ref's scalar chain (ignition_prob, p_hit, p_report)."""
    for s in (0.0, 0.3, 0.9, 1.5):
        for theta, gamma in ((0.35, 5.0), (0.8, 2.0), (0.25, 7.5)):
            b = R.ignition_prob(gamma, s, theta)
            ref = R.p_report(R.p_hit(RATE_WINDOW, [b], 1.0), GUESS, LAPSE)
            assert p_report(np.array([s]), theta, gamma)[0] == pytest.approx(ref, rel=1e-12)


def loglik(k, n, levels, theta, gamma):
    """Binomial log-likelihood (up to a constant) of k reports in n trials per level.
    theta and gamma broadcast against a trailing level axis."""
    p = np.clip(p_report(levels, theta, gamma), 1e-12, 1 - 1e-12)
    return np.sum(k * np.log(p) + (n - k) * np.log1p(-p), axis=-1)


def fit(k, n, levels):
    """Maximum likelihood by a coarse grid and two refinement grids. The search box
    (θ ∈ [−0.2, 1.4] AU, γ ∈ [0.5, 30]) is wider than the generating range on purpose."""
    th = np.linspace(-0.2, 1.4, 161)
    lg = np.linspace(math.log(0.5), math.log(30.0), 161)
    for _ in range(3):
        T, G = np.meshgrid(th, lg, indexing="ij")
        ll = loglik(k, n, levels, T[..., None], np.exp(G)[..., None])
        i, j = np.unravel_index(np.argmax(ll), ll.shape)
        t0, g0 = th[i], lg[j]
        dth, dlg = (th[1] - th[0]) * 3, (lg[1] - lg[0]) * 3
        th = np.linspace(t0 - dth, t0 + dth, 41)
        lg = np.linspace(g0 - dlg, g0 + dlg, 41)
    return float(t0), float(math.exp(g0))


def simulate(rng, theta, gamma):
    return rng.binomial(TRIALS, p_report(LEVELS, theta, gamma))


# ---------------------------------------------------------------- §17 recovery gate

@pytest.fixture(scope="module")
def recovery():
    rng = np.random.default_rng(SEED)
    true_t = rng.uniform(THETA_LO, THETA_HI, N_SUBJECTS)
    true_g = rng.uniform(GAMMA_LO, GAMMA_HI, N_SUBJECTS)
    est = np.array([fit(simulate(rng, t, g), TRIALS, LEVELS) for t, g in zip(true_t, true_g)])
    return true_t, true_g, est[:, 0], est[:, 1]


def _gate(true, est, lo, hi):
    r = float(np.corrcoef(true, est)[0, 1])
    err = float(np.median(np.abs(est - true)) / (hi - lo))
    return r, err


def test_recovery_gate_theta(recovery):
    true_t, _, est_t, _ = recovery
    r, err = _gate(true_t, est_t, THETA_LO, THETA_HI)
    print(f"TC-08 θ_eff: Pearson r = {r:.3f} (target > {R_HIGH}), median range-scaled error = {err:.3f} (gate < {ERR_GATE})")
    assert r > R_HIGH
    assert err < ERR_GATE


def test_recovery_gate_gamma(recovery):
    _, true_g, _, est_g = recovery
    r, err = _gate(true_g, est_g, GAMMA_LO, GAMMA_HI)
    print(f"TC-08 γ_sig: Pearson r = {r:.3f} (target > {R_HIGH}), median range-scaled error = {err:.3f} (gate < {ERR_GATE})")
    assert r > R_HIGH
    assert err < ERR_GATE


def test_recovery_fails_without_the_scale_anchor():
    """TC-08c is real: if the S scale is a free parameter, (θ, γ) and (aθ, γ/a) on a rescaled
    drive have the same likelihood, so the joint fit cannot pick a. The gate above is only
    meaningful because the precision reference (and hence the S scale) is fixed."""
    rng = np.random.default_rng(SEED + 1)
    k = simulate(rng, 0.5, 4.0)
    t, g = fit(k, TRIALS, LEVELS)
    base = loglik(k, TRIALS, LEVELS, t, g)
    for a in (0.5, 2.0, 3.0):
        assert loglik(k, TRIALS, a * LEVELS, a * t, g / a) == pytest.approx(base, rel=1e-10, abs=1e-9)


# ---------------------------------------------------------------- TC-08a–c twins

def _event_loglik(k, S, theta, B, r_max=50.0, dt=0.01):
    """log of Apgi.hazardLik for an event sequence B."""
    out = 0.0
    for s, th, b in zip(S, theta, B):
        q = R.hazard_prob(r_max, R.ignition_prob(k, s, th), dt)
        out += math.log(q if b else 1.0 - q)
    return out


_path = st.lists(st.tuples(st.floats(-3, 3), st.floats(-3, 3), st.booleans()), min_size=1, max_size=30)


@settings(max_examples=200, deadline=None)
@given(_path, st.floats(0.5, 10), st.floats(-5, 5))
def test_tc08a_common_offset_twin(path, k, b):
    """Twin of Apgi.hazardLik_shift."""
    S, th, B = zip(*path)
    lhs = _event_loglik(k, [s + b for s in S], [t + b for t in th], B)
    assert lhs == pytest.approx(_event_loglik(k, S, th, B), rel=1e-9, abs=1e-9)


@settings(max_examples=200, deadline=None)
@given(_path, st.floats(0.5, 10), st.floats(0.1, 10), st.floats(-5, 5))
def test_tc08c_joint_scale_twin(path, k, a, b):
    """Twin of Apgi.hazardLik_rescale."""
    S, th, B = zip(*path)
    lhs = _event_loglik(k / a, [a * s + b for s in S], [a * t + b for t in th], B)
    assert lhs == pytest.approx(_event_loglik(k, S, th, B), rel=1e-9, abs=1e-9)


@given(st.floats(0.1, 5), st.floats(0.1, 10), st.floats(0.1, 3), st.floats(-2, 2), st.floats(-1, 1))
def test_tc08b_gain_product_twin(g, pb, beta, m, shift):
    """Twin of Apgi.traj_gain_product at the level where the gains meet (EQ-PREC-SM-1):
    (g_NE, β_SM, M̂) and (g_NE·e^{shift}, β_SM, M̂ − shift/β_SM) give the same Πⁱ_eff."""
    g2, m2 = g * math.exp(shift), m - shift / beta
    assert R.prec_eff(g2, pb, beta, m2) == pytest.approx(R.prec_eff(g, pb, beta, m), rel=1e-12)
