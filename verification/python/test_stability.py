"""TC-13 stability (SSOT §23): dt obeys EQ-STEP-1; overflow, NaN and division by zero have
defined handling; NaN/Inf are rejected.

Defined handling in apgi_ref.core_step (production core/ssot_core.py implements the same
contract; test_production.py checks it):
* NaN/Inf inputs raise NonFiniteInputError before any computation;
* a step that would overflow float64 raises NonFiniteStateError (an OverflowError);
* the input state is never mutated, so a rejected step changes nothing;
* division by zero cannot occur: every denominator is ≥ ε_stab > 0 along every trajectory
  (Lean: Apgi.traj_denoms_pos), and the drive is bounded by the explicit error bound of
  Apgi.pipeLog_Sinst_le.

Overflow is a float64 property. Lean's ℝ has no overflow, so this part is a computational
test, not a theorem; the Lean bound shows where the amplification comes from (1/ε_stab).
"""
from __future__ import annotations

import copy
import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import apgi_ref as R

BAD = [float("nan"), float("inf"), -float("inf")]


def _warm(n: int = 20, p: dict | None = None):
    s = R.core_state(p)
    for k in range(n):
        s, _ = R.core_step(s, 0.1 * k, -0.05 * k, p, u=0.5)
    return s


@pytest.mark.parametrize("bad", BAD, ids=["nan", "inf", "-inf"])
@pytest.mark.parametrize("arg", ["x_e", "x_i", "u"])
def test_non_finite_input_rejected_without_state_change(bad, arg):
    s = _warm()
    before = copy.deepcopy(s)
    kw = {"x_e": 0.0, "x_i": 0.0, "u": 0.5, arg: bad}
    with pytest.raises(R.NonFiniteInputError):
        R.core_step(s, kw["x_e"], kw["x_i"], None, u=kw["u"])
    assert s == before


@pytest.mark.parametrize("bad", [True, "1.0", None])
def test_non_numeric_input_rejected(bad):
    with pytest.raises(R.NonFiniteInputError):
        R.core_step(R.core_state(), bad, 0.0)


@pytest.mark.parametrize("big", [1e200, -1e200, 1e308])
def test_overflow_rejected_without_state_change(big):
    s = _warm()
    before = copy.deepcopy(s)
    with pytest.raises(R.NonFiniteStateError) as exc:
        R.core_step(s, big, 0.0, None, u=0.5)
    assert isinstance(exc.value, OverflowError)
    assert s == before
    # The trajectory continues as if the rejected call never happened.
    assert R.core_step(s, 0.2, 0.1, None, u=0.5) == R.core_step(_warm(), 0.2, 0.1, None, u=0.5)


def test_silent_float_overflow_is_rejected():
    """Float64 `*` and `/` overflow to inf without raising (only `**` raises). The post-step
    finiteness check must catch that path too: with Π̄ᵉ = 1e-300, Π_rel·|z| overflows to inf."""
    p = {"pi_bar_e": 1e-300}
    s = _warm(p=p)
    before = copy.deepcopy(s)
    with pytest.raises(R.NonFiniteStateError, match="non-finite state"):
        R.core_step(s, 1e10, 0.0, p, u=0.5)
    assert s == before


def test_constant_input_has_no_division_by_zero():
    """σ_ref → 0 and Σ → 0 under constant input; ε_stab keeps every denominator positive."""
    s = R.core_state()
    for _ in range(3000):
        s, log = R.core_step(s, 1.0, 1.0, None, u=0.5)
    for k in ("z_e", "z_i", "pi_e", "pi_i", "S_inst", "theta_eff", "B_prop"):
        assert math.isfinite(log[k]), k
    assert log["pi_e"] == R.CORE_DEFAULTS["pi_max"]  # Π_raw = 1/(Σ + ε_stab) is clamped, not infinite
    assert s["s2_e"] >= 0.0


@pytest.mark.parametrize("margin", [-1e308, -1e6, -800.0, 800.0, 1e6, 1e308])
def test_propensity_and_hazard_saturate_without_overflow(margin):
    b = R.ignition_prob(7.5, margin, 0.0)
    assert b == (1.0 if margin > 0 else 0.0)
    h = R.hazard_prob(1e300, b, 0.01)
    assert 0.0 <= h <= 1.0


@settings(max_examples=300, deadline=None)
@given(st.lists(st.tuples(st.floats(-1e6, 1e6), st.floats(-1e6, 1e6), st.floats(0, 1)),
                min_size=1, max_size=40))
def test_finite_inputs_never_raise_and_obey_the_drive_bound(seq):
    """Twin of Apgi.pipeLog_Sinst_le and Apgi.standardize_abs_le on float64:
    S_inst ≤ Π_max/Π̄ᵉ·|εᵉ − μᵉ_ref|/ε_stab + Π_max/Π̄ⁱ·(|εⁱ − μⁱ_ref|/ε_stab + |β_DA|)."""
    p = R.CORE_DEFAULTS
    s = R.core_state()
    for xe, xi, u in seq:
        me, _ = R._ref_stats(s["ref_e"])
        mi, _ = R._ref_stats(s["ref_i"])
        s2, log = R.core_step(s, xe, xi, None, u=u)
        es = p["eps_stab"]
        assert abs(log["z_e"]) <= abs(log["eps_e"] - me) / es * (1 + 1e-12)
        bound = (p["pi_max"] / p["pi_bar_e"] * abs(log["eps_e"] - me) / es
                 + p["pi_max"] / p["pi_bar_i"] * (abs(log["eps_i"] - mi) / es + abs(p["beta_da"])))
        assert log["S_inst"] <= bound * (1 + 1e-12) + 1e-12
        s = s2


@given(st.floats(1e-3, 1e3), st.floats(0, 1))
def test_step_rule_bounds_the_per_step_gain(tau, frac):
    """Twin of Apgi.stepRule_gain_le: dt ≤ τ/10 ⇒ λ = 1 − exp(−dt/τ) ≤ 1/10 (also α_EMA)."""
    dt = frac * tau / 10
    assert R.step_rule(dt, tau)
    assert R.leak_gain(dt, tau) <= 0.1 + 1e-15
    assert R.ema_alpha(dt, tau) <= 0.1 + 1e-15
