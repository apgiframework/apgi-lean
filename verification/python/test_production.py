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
import math
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


# ------------------------------------- SSOT v1.2 minimal core (task 53) ----
# Behavioural tests on the full pipeline (pipeline.APGIPipeline), one strict
# xfail per SSOT-P* divergence. Each test is written against the SSOT
# statement, so a production fix turns it into a hard failure (XPASS) until the
# divergence is marked resolved. Inputs are chosen so a test isolates its own
# divergence: fixing SSOT-Pn alone flips the SSOT-Pn tests and no others.
import copy  # noqa: E402
import warnings  # noqa: E402


def _pipe(**over):
    """A fresh production pipeline at the default CONFIG with `over` applied."""
    import pipeline as PP

    cfg = copy.deepcopy(CFG)
    cfg.update(over)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PP.APGIPipeline(cfg)


def _step(p, x_e, x_i):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return p.step(x_e, x_i)


TINY_ETA = 1e-12  # production validates η_θ ∈ (0, 1]; this keeps θ fixed to ~1e-12 AU


def test_pipeline_importable():
    """Guard for the SSOT-P* xfails: an import error inside them would count as an expected
    failure. CI installs structlog and pydantic for this (apgi-implementation requirements)."""
    p = _pipe()
    r = _step(p, 0.1, -0.1)
    assert {"S", "S_inst", "theta", "B", "pi_e", "z_e_norm"} <= set(r)


@divergence("SSOT-P1")
def test_drive_is_sign_symmetric():
    """TC-09 / EQ-DRIVE-1: errors of equal magnitude and opposite sign contribute equally."""
    a = _step(_pipe(beta=0.0), 1.5, 0.0)["S_inst"]
    b = _step(_pipe(beta=0.0), -1.5, 0.0)["S_inst"]
    assert a == pytest.approx(b, rel=1e-9)


@divergence("SSOT-P1")
def test_drive_is_excess_centered():
    """TC-07 / EQ-EXCESS-1: zero error gives S_inst = −m₀·(Πᵉ_rel + Πⁱ_rel) < 0, so the
    stimulus-free mean of S_inst is zero and θ₀ sits on the excess-surprise scale."""
    assert _step(_pipe(beta=0.0), 0.0, 0.0)["S_inst"] < -0.5


@divergence("SSOT-P2")
def test_standardization_does_not_share_the_precision_estimator():
    """EQ-STD-1 / TC-17: z uses separate reference statistics, so changing the precision
    variance estimate must not change z."""
    p, q = _pipe(beta=0.0), _pipe(beta=0.0)
    p.state.sigma2_e = 4.0
    assert _step(p, 1.0, 0.0)["z_e_norm"] == pytest.approx(_step(q, 1.0, 0.0)["z_e_norm"], rel=1e-12)


@divergence("SSOT-P2")
def test_precision_uses_variance_before_current_sample():
    """SSOT §8 step 4: Π(t) = clip(1/(Σ(t) + ε_stab)); ε(t) enters Σ only at step 14."""
    p = _pipe()
    s2 = p.state.sigma2_e
    r = _step(p, 3.0, 0.0)
    assert r["pi_e"] == pytest.approx(R.prec_clamp(CFG["pi_min"], CFG["pi_max"], 1 / (s2 + CFG["eps"])), rel=1e-9)


@divergence("SSOT-P3")
def test_default_accumulator_is_exact_leak():
    """EQ-LEAK-1: without an ignition, S(t+1) = (1 − λ)·S(t) + λ·S_inst(t), deterministic."""
    p = _pipe(beta=0.0, stochastic_ignition=False)  # hard limit, S < θ_eff: no ignition by construction
    p.S = 0.2
    r = _step(p, 1.0, 0.0)
    assert r["B"] == 0
    assert r["S"] == pytest.approx(R.leak_step(0.2, r["S_inst"], CFG["lam"]), rel=1e-9)


@divergence("SSOT-P3")
def test_signal_state_is_signed():
    """S is signed and never overwritten by a compression (log1p is a read-out only, SSOT §5.5/§6.4):
    from S = −0.3 with zero error the state stays negative."""
    p = _pipe(beta=0.0, stochastic_ignition=False)
    p.S = -0.3
    assert _step(p, 0.0, 0.0)["S"] < 0


@divergence("SSOT-P4")
def test_ignition_is_decided_from_existing_S():
    """EQ-PIPE-1 (§8 steps 8-13): the decision compares the existing S(t) with θ_eff(t), before
    reset and accumulation. Hard-threshold limit (EQ-IGN-1) so the test is deterministic."""
    p = _pipe(beta=0.0, stochastic_ignition=False, eta=TINY_ETA)
    p.S = p.theta + 0.01
    assert _step(p, 0.0, 0.0)["B"] == 1


@divergence("SSOT-P4")
def test_reset_increment_inside_allostatic_step():
    """EQ-ALLO-1: δ_reset·B(t) is added inside the allostatic step, before the exact decay,
    and applied exactly once (TC-12): θ(t+1) = θ₀ + (θ + δ − θ₀)·e^(−dt/τ_θ)."""
    p = _pipe(beta=0.0, stochastic_ignition=False, eta=TINY_ETA, delta=0.5)
    th0 = p.theta
    p.S = 5.0
    r = _step(p, 0.0, 0.0)
    assert r["B"] == 1
    expected = R.threshold_step(th0, CFG["theta_base"], 0.0, 0.0, 0.0, 0.5, 1, CFG["dt"], CFG["tau_theta"])
    assert p.theta == pytest.approx(expected, rel=1e-9)


@divergence("SSOT-P5")
def test_ne_factor_is_read_out_only():
    """TC-11 / EQ-THEFF-1: the NE factor scales θ_eff, never θ. With no ignition θ stays at θ₀."""
    p = _pipe(ne_on_threshold=True, gamma_ne=0.2, g_ne=1.0, eta=TINY_ETA, beta=0.0, stochastic_ignition=False)
    for _ in range(100):
        _step(p, 0.0, 0.0)
    assert p.theta == pytest.approx(CFG["theta_base"], abs=1e-6)


@divergence("SSOT-P5")
def test_serotonin_offset_is_read_out_only():
    """TC-11 / EQ-THEFF-1: β_5HT shifts θ_eff, never θ (written back it accumulates ≈ 2000·β_5HT)."""
    p = _pipe(beta_5ht=0.1, eta=TINY_ETA, beta=0.0, stochastic_ignition=False)
    for _ in range(100):
        _step(p, 0.0, 0.0)
    assert p.theta == pytest.approx(CFG["theta_base"], abs=1e-6)


@divergence("SSOT-P6")
def test_ne_clamp_binds_for_negative_coupling():
    """EQ-NE-1, Lean CL-13 (neClamp_bound): |γ_NE|·g_NE ≤ 0.5 for either sign of γ_NE."""
    p = _pipe(ne_on_threshold=True, gamma_ne=-2.0, g_ne=1.0)
    assert abs(p.config["gamma_ne"]) * p.config["g_ne"] <= 0.5 + 1e-12
    assert p.config["g_ne"] == pytest.approx(R.ne_clamp(-2.0, 1.0))


@divergence("SSOT-P6")
def test_gamma_ne_has_no_default_sign():
    """R6: γ_NE has no default sign; the neutral default is 0 (no NE threshold route) or unset."""
    assert CFG.get("gamma_ne") in (None, 0.0)


@divergence("SSOT-P7")
def test_default_theta0_is_canonical():
    """SSOT §4.1: θ₀ = 0.35 AU (registry theta_baseline)."""
    th0 = float(P["theta_baseline"]["value"])
    assert CFG["theta_base"] == th0 and CFG.get("theta_0", th0) == th0


@divergence("SSOT-P7")
def test_default_sampling_is_hazard():
    """EQ-HAZARD-1 is the canonical sampler; the hard threshold is a limit, not the default."""
    assert CFG["stochastic_ignition"] is True


@divergence("SSOT-P7")
def test_manifest_reports_operating_point():
    """R1 / TC-14: every run reports γ_sig·θ₀, σ(−γ_sig·θ₀) and the stimulus-free event rate."""
    m = _pipe().manifest()
    op = R.operating_point(1.0 / CFG["ignite_tau"], CFG["theta_base"], CFG["r_max"])
    flat = {**m, **(m.get("operating_point") or {})}
    for k, v in op.items():
        assert flat.get(k) == pytest.approx(v, rel=1e-9), k


@divergence("SSOT-P8")
def test_ema_weights_follow_reference_windows():
    """EQ-EMA-2: α_EMA = 1 − exp(−dt/T_window), T_window = 5 s (extero), 10 s (intero)."""
    assert CFG["alpha_e"] == pytest.approx(R.ema_alpha(CFG["dt"], float(P["T_window_e"]["value"])), rel=1e-9)
    assert CFG["alpha_i"] == pytest.approx(R.ema_alpha(CFG["dt"], float(P["T_window_i"]["value"])), rel=1e-9)


@divergence("SSOT-P9")
def test_default_dopamine_bias_is_zero():
    """SSOT §4.2: β_DA = 0 by default (registry beta_DA, value verified against SRC-SSOT-V12D; F4)."""
    assert float(P["beta_DA"]["value"]) == 0.0
    assert CFG["beta"] == float(P["beta_DA"]["value"])


# ------------------------------- TC-04: production core == reference core (Phase A) ----
class _FixedDraws:
    """Feeds the production hazard sampler the same uniform draws apgi_ref.core_step receives."""

    def __init__(self, us):
        self._it = iter(us)

    def random(self):
        return next(self._it)


def _ref_params(cfg):
    return dict(dt=cfg["dt"], tau_S=cfg["tau_s"], theta0=cfg["theta_base"], tau_theta=cfg["tau_theta"],
                theta_floor=cfg["theta_clip_min"], eta_theta=cfg["eta"], delta_reset=cfg["delta"],
                rho_retain=cfg["RHO_RETAIN"], gamma_sig=1.0 / cfg["ignite_tau"], r_max=cfg["r_max"],
                c1=cfg["c1"], c2=cfg["c2"], v1=cfg["v1"], v2=cfg["v2"], g_ach=cfg["g_ach"], g_ne=cfg["g_ne"],
                gamma_ne=cfg["gamma_ne"] or 0.0, beta_da=cfg["beta"], beta_5ht=cfg["beta_5ht"],
                tau_ref=cfg["tau_ref"], delta_ref=cfg["delta_ref"], pi_min=cfg["pi_min"], pi_max=cfg["pi_max"],
                pi_bar_e=cfg["pi_bar_e"], pi_bar_i=cfg["pi_bar_i"], eta_pred_e=cfg["eta_pred_e"],
                eta_pred_i=cfg["eta_pred_i"], T_e=cfg["T_window_e"], T_i=cfg["T_window_i"], eps_stab=cfg["eps"])


@pytest.mark.parametrize("over", [{}, {"delta_ref": 0.3, "delta": 0.05}], ids=["CFG-CORE", "CFG-CORE-R"])
def test_production_core_matches_reference_trajectory(over):
    """TC-04 / EQ-PIPE-1: the default production pipeline (model_form "ssot_core") and
    apgi_ref.core_step produce the same S_inst, θ_eff, Bₜ, B(t), S, θ for 400 seeded steps."""
    import numpy as np

    p = _pipe(**over)
    assert p.model_form == "ssot_core"
    rng = np.random.default_rng(10101)
    n = 400
    xe = rng.standard_normal(n) + np.where((np.arange(n) % 100) >= 60, 1.5, 0.0)
    xi = rng.standard_normal(n)
    us = rng.random(n)
    p.rng = _FixedDraws(us)
    ref_p = _ref_params(p.config)
    s = R.core_state(ref_p)
    fired = 0
    for k in range(n):
        r = _step(p, float(xe[k]), float(xi[k]))
        s, log = R.core_step(s, float(xe[k]), float(xi[k]), ref_p, u=float(us[k]))
        assert r["B"] == log["B"], k
        fired += r["B"]
        for a, b in (("S_inst", "S_inst"), ("theta_eff", "theta_eff"), ("B_prop", "B_prop")):
            assert r[a] == pytest.approx(log[b], rel=1e-9, abs=1e-12), (k, a)
        assert r["S"] == pytest.approx(s["S"], rel=1e-9, abs=1e-12), k
        assert r["theta"] == pytest.approx(s["theta"], rel=1e-9, abs=1e-12), k
    assert 0 < fired < n


def test_extensions_are_labelled_legacy():
    """SSOT §9: an enabled extension runs the v1.1 pipeline and says so (model_form and manifest)."""
    p = _pipe(use_hierarchical=True)
    assert p.model_form == "legacy_v1_1" and "hierarchical" in p.extensions_active
    assert p.manifest()["model_form"] == "legacy_v1_1"


# ------------------------------------------------ TC-13 stability (task 68a) ----
def _snapshot(p) -> dict:
    import pickle

    out = {}
    for k, v in vars(p).items():
        try:
            out[k] = pickle.dumps(v)
        except Exception:  # noqa: BLE001 - unpicklable helpers are compared by repr
            out[k] = repr(v)
    return out


def _warm_pipe(seed: int = 7):
    import numpy as np

    p = _pipe()
    p.rng = np.random.default_rng(seed)
    for k in range(20):
        _step(p, 0.1 * k, -0.05 * k)
    return p


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")], ids=["nan", "inf", "-inf"])
def test_production_rejects_non_finite_input_atomically(bad):
    """TC-13: NaN/Inf rejected before any state, statistics, RNG or history change."""
    p = _warm_pipe()
    before = _snapshot(p)
    for args in ((bad, 0.0), (0.0, bad)):
        with pytest.raises(ValueError) as exc:
            _step(p, *args)
        assert type(exc.value).__name__ == "NonFiniteInputError"
        assert _snapshot(p) == before


@divergence("SSOT-P11")
@pytest.mark.parametrize("big", [1e200, -1e200, 1e308])
def test_production_overflow_is_rejected_atomically(big):
    """TC-13: a step that would overflow raises NonFiniteStateError (an OverflowError) and
    leaves the pipeline, its RNG and its history unchanged; the run then continues exactly
    as if the call had not happened."""
    p = _warm_pipe()
    before = _snapshot(p)
    with pytest.raises(OverflowError) as exc:
        _step(p, big, 0.0)
    assert type(exc.value).__name__ == "NonFiniteStateError"
    assert _snapshot(p) == before
    assert _step(p, 0.2, 0.1) == _step(_warm_pipe(), 0.2, 0.1)


@divergence("SSOT-P11")
def test_production_silent_overflow_is_rejected_atomically():
    """TC-13: float64 `*` and `/` overflow to inf without raising. With Π̄ᵉ = 1e-300 the drive
    overflows silently; the step must still be rejected and change nothing."""
    import numpy as np

    p = _pipe(pi_bar_e=1e-300)
    p.rng = np.random.default_rng(7)
    for k in range(20):
        _step(p, 0.1 * k, -0.05 * k)
    before = _snapshot(p)
    with pytest.raises(OverflowError):
        _step(p, 1e10, 0.0)
    assert _snapshot(p) == before


@pytest.mark.parametrize("mag", [1.0, 1e3, 1e50, 1e100, 1e150, 1e154, 1e155, 1e160, 1e200, 1e300])
def test_overflow_classification_matches_reference(mag):
    """TC-13 across implementations: for the same state and input, production and apgi_ref
    either both accept the step (with the same result) or both reject it as an overflow."""
    import numpy as np

    us = [0.5] * 21
    p = _pipe()
    p.rng = _FixedDraws(us)
    ref_p = _ref_params(p.config)
    s = R.core_state(ref_p)
    for k in range(20):
        _step(p, 0.1 * k, -0.05 * k)
        s, _ = R.core_step(s, 0.1 * k, -0.05 * k, ref_p, u=0.5)
    try:
        r = _step(p, mag, 0.0)
        prod = ("ok", r["S"])
    except OverflowError:
        prod = ("overflow", None)
    try:
        s2, _ = R.core_step(s, mag, 0.0, ref_p, u=0.5)
        ref = ("ok", s2["S"])
    except OverflowError:
        ref = ("overflow", None)
    assert prod[0] == ref[0], (mag, prod, ref)
    if prod[0] == "ok":
        assert np.isfinite(prod[1])
        assert prod[1] == pytest.approx(ref[1], rel=1e-9, abs=1e-12)


def test_production_constant_input_has_no_division_by_zero():
    """TC-13: σ_ref → 0 and Σ → 0 under constant input; every denominator stays ≥ ε_stab
    (Lean: Apgi.traj_denoms_pos) and Π_raw is clamped to Π_max, never infinite."""
    p = _pipe()
    for _ in range(3000):
        r = _step(p, 1.0, 1.0)
    for k in ("S", "S_inst", "theta", "theta_eff", "B_prop", "z_e_norm", "z_i_norm", "pi_e", "pi_i"):
        assert math.isfinite(float(r[k])), k
    assert r["pi_e"] == pytest.approx(p.config["pi_max"])


# --------------------------- TC-19 stochastic reproducibility (task 68b) ----
TC19_RUNS = 200
TC19_STEPS = 300


def _tc19_inputs():
    import numpy as np

    g = np.random.default_rng(19)
    xe = g.standard_normal(TC19_STEPS) + np.where((np.arange(TC19_STEPS) % 100) >= 60, 1.5, 0.0)
    xi = g.standard_normal(TC19_STEPS)
    return [float(x) for x in xe], [float(x) for x in xi]


def _ks_statistic(a, b) -> float:
    import numpy as np

    a, b = np.sort(np.asarray(a, float)), np.sort(np.asarray(b, float))
    grid = np.union1d(a, b)
    fa = np.searchsorted(a, grid, side="right") / a.size
    fb = np.searchsorted(b, grid, side="right") / b.size
    return float(np.max(np.abs(fa - fb)))


def test_production_rng_algorithm_is_pcg64_and_seed_reproducible():
    """TC-19: fixed RNG algorithm (numpy PCG64 via default_rng) and seeds. The same seed
    reproduces the same event sequence within one platform; SSOT §23 notes that seeds alone
    do not guarantee cross-platform equality, hence the distributional test below."""
    import numpy as np

    xe, xi = _tc19_inputs()
    runs = []
    for _ in range(2):
        p = _pipe()
        p.rng = np.random.default_rng(np.random.SeedSequence(20261127))
        assert isinstance(p.rng.bit_generator, np.random.PCG64)
        runs.append([_step(p, a, b)["B"] for a, b in zip(xe, xi)])
    assert runs[0] == runs[1]
    assert 0 < sum(runs[0]) < TC19_STEPS


def test_cross_implementation_event_distribution():
    """TC-19 distributional test across implementations. Same deterministic inputs; production
    samples with its own hazard sampler on independent PCG64 streams, apgi_ref with Philox
    streams (a different algorithm on purpose). The per-run ignition counts and first-ignition
    times must agree in distribution: |Welch z| < 4 and the two-sample KS statistic below its
    α = 0.001 critical value. A twin with r_max scaled by 1.5 must fail the same test
    (power check), so the test can detect a real difference."""
    import numpy as np

    xe, xi = _tc19_inputs()
    root = np.random.SeedSequence(20261127)
    prod_seeds, ref_seeds = root.spawn(2)
    p0 = _pipe()
    ref_p = _ref_params(p0.config)

    def prod_runs():
        out = []
        for ss in prod_seeds.spawn(TC19_RUNS):
            p = _pipe()
            p.rng = np.random.Generator(np.random.PCG64(ss))
            B = [_step(p, a, b)["B"] for a, b in zip(xe, xi)]
            out.append(B)
        return out

    def ref_runs(params):
        out = []
        for ss in ref_seeds.spawn(TC19_RUNS):
            g = np.random.Generator(np.random.Philox(ss))
            s, B = R.core_state(params), []
            for a, b in zip(xe, xi):
                s, log = R.core_step(s, a, b, params, u=float(g.random()))
                B.append(log["B"])
            out.append(B)
        return out

    def stats(runs):
        counts = [sum(B) for B in runs]
        first = [B.index(1) if 1 in B else TC19_STEPS for B in runs]
        return np.array(counts, float), np.array(first, float)

    def agree(x, y) -> bool:
        z = (x.mean() - y.mean()) / math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)
        crit = math.sqrt(-math.log(0.001 / 2) / 2) * math.sqrt((x.size + y.size) / (x.size * y.size))
        return abs(z) < 4 and _ks_statistic(x, y) < crit

    pc, pf = stats(prod_runs())
    rc, rf = stats(ref_runs(ref_p))
    assert pc.mean() > 1  # the window is informative: several ignitions per run
    assert agree(pc, rc), (pc.mean(), rc.mean())
    assert agree(pf, rf), (pf.mean(), rf.mean())
    hc, _ = stats(ref_runs({**ref_p, "r_max": 1.5 * ref_p["r_max"]}))
    assert not agree(pc, hc), "power check: a 1.5x hazard rate must be detected"


# ------------------------------------- TC-10 / TC-14 production run report (task 61b) ----
def test_production_run_report_is_current():
    """TC-10, TC-14: verification/reports/production-run-report.json reports, for CFG-CORE and
    CFG-CORE-R at the pinned commit, the clamped-step fractions, the operating point and the
    stimulus-free event rate. Regenerated here and compared field by field."""
    import production_report as PR

    assert PR.REPORT.exists(), "run production_report.py"
    import json

    old = json.loads(PR.REPORT.read_text(encoding="utf-8"))
    new = PR._rounded(PR.build())
    assert old["production_commit"] == KNOWN["production"]["commit"], "report is for another pin"
    assert old == new, "production-run-report.json is stale: rerun production_report.py"


def test_production_run_report_agrees_with_reference():
    """The production figures in the report equal apgi_ref's on the same inputs and draws."""
    import json

    import production_report as PR

    rep = json.loads(PR.REPORT.read_text(encoding="utf-8"))
    assert set(rep["configurations"]) == {"CFG-CORE", "CFG-CORE-R"}
    for name, r in rep["configurations"].items():
        pr, rf = r["production"], r["reference"]
        for k in ("precision_clamped_fraction", "ne_clamped_fraction", "events", "operating_point"):
            assert pr[k] == rf[k], (name, k)
        assert 0.1 <= pr["precision_range"][0] and pr["precision_range"][1] <= 10.0  # [Π_min, Π_max]
        assert r["steps"] == PR.STEPS and pr["events"] > 0


def _clamp_inputs(n=6000):
    """Low-variance input (Σ shrinks until Π binds at Π_max), then N(0, 1): exteroceptive in the
    first half, interoceptive in the middle third, so each channel's clamps bind on part of the run."""
    import numpy as np

    g = np.random.default_rng(1010)
    xe = np.concatenate([0.05 * g.standard_normal(n // 2), g.standard_normal(n - n // 2)])
    k = np.arange(n)
    xi = g.standard_normal(n) * np.where((k >= n // 3) & (k < 2 * n // 3), 0.05, 1.0)
    return xe, xi, g.random(n)


@pytest.mark.parametrize("over", [{}, {"gamma_ne": 2.0, "ne_on_threshold": True}, {"g_ach": 2.0, "g_ne": 2.0}],
                         ids=["precision", "precision+NE", "precision+gains"])
def test_production_clamp_fraction_matches_reference(over):
    """TC-10: when clamps bind, the clamped-step fraction derived from production's outputs equals
    apgi_ref.clamp_report on identical inputs and draws, strictly between 0 and 1 for precision;
    with |γ_NE|·g_NE = 2 > 0.5 the NE clamp binds on every step. Precision stays in
    [Π_min, Π_max] on every step (Lean: Apgi.traj_prec_mem_Icc, Apgi.traj_ne_bound)."""
    import production_report as PR

    xe, xi, us = _clamp_inputs()
    r = PR.run_pair(over, xe, xi, us)
    pr, rf = r["production"], r["reference"]
    assert pr["precision_clamped_fraction"] == rf["precision_clamped_fraction"]
    assert pr["ne_clamped_fraction"] == rf["ne_clamped_fraction"]
    assert pr["events"] == rf["events"]
    assert 0.05 < pr["precision_clamped_fraction"] < 0.95
    assert pr["ne_clamped_fraction"] == (1.0 if "gamma_ne" in over else 0.0)
    lo, hi = pr["precision_range"]
    assert PR.requested_config(over)["pi_min"] <= lo and hi <= PR.requested_config(over)["pi_max"]


def test_production_clamp_flags_detect_bounds():
    """The harness flag is not vacuous: an output at Π_max or Π_min is flagged, one inside is not."""
    import production_report as PR

    cfg = {"pi_min": 0.1, "pi_max": 10.0, "gamma_ne": 0.0, "g_ne": 1.0}
    inside = dict(pi_e=1.0, pi_i=2.0, pi_e_eff=1.0, pi_i_eff=2.0)
    assert PR.production_clamp_flags(inside, cfg) == (False, False)
    assert PR.production_clamp_flags({**inside, "pi_i_eff": 10.0}, cfg)[0]
    assert PR.production_clamp_flags({**inside, "pi_e": 0.1}, cfg)[0]
    assert PR.production_clamp_flags(inside, {**cfg, "gamma_ne": -0.6})[1]


# ------------------------- task 59: legacy extension path (SSOT-P10, SSOT-P12) ----
def _legacy(**over):
    import numpy as np

    p = _pipe(**over)
    assert p.model_form == "legacy_v1_1", p.model_form
    p.rng = np.random.default_rng(3)
    return p


@divergence("SSOT-P10")
def test_hierarchical_precision_ode_is_the_only_precision():
    """SSOT §8 shortcuts / EQ-PREC-ODE-1: the hierarchical precision ODE and the inverse-variance
    precision (EQ-PREC-2) are never combined in one simulation. With the ODE on, a change that
    acts only on the inverse-variance chain (g_ACh scales Πᵉ_eff = g_ACh·Πᵉ) must not change S
    while the ODE precisions are unchanged. Production: S moves, because update_signal_ode is fed
    the inverse-variance Πᵉ_eff, Πⁱ_eff while S_inst aggregates the ODE precisions."""
    import copy

    import numpy as np

    p = _legacy(hierarchical_mode="advanced")
    assert p.hierarchical_network is not None
    for k in range(50):
        _step(p, 0.3 * math.sin(k / 5), 0.1)
    q = copy.deepcopy(p)
    q.config["g_ach"] = 2.0 * p.config["g_ach"]
    rp, rq = _step(p, 1.0, 0.5), _step(q, 1.0, 0.5)
    assert np.array_equal(p.hierarchical_network.pi, q.hierarchical_network.pi)
    assert rp["z_e_norm"] == rq["z_e_norm"]          # the perturbation does not reach z
    assert rp["pi_e_eff"] != rq["pi_e_eff"]          # and does reach the inverse-variance chain
    assert p.S == q.S


@pytest.mark.parametrize("delta", [0.0, 0.2])
def test_resonance_primary_threshold_gets_delta_once(delta):
    """TC-12 in resonance mode: one ignition raises the primary threshold by exactly one δ_reset.
    This refutes the 'double δ' suspected in SSOT-P10 for the threshold that decides ignition:
    resonance.apply_level_ignition raises only the resonance-level copy, which the next
    resonance step recomputes from its baseline."""
    p0 = _legacy(hierarchical_mode="basic", stochastic_ignition=False, delta=0.0, resonance_kappa_down=0.0)
    p1 = _legacy(hierarchical_mode="basic", stochastic_ignition=False, delta=delta, resonance_kappa_down=0.0)
    for k in range(30):
        _step(p0, 0.0, 0.0)
        _step(p1, 0.0, 0.0)
    assert p0.theta == p1.theta
    p0.S = p1.S = 50.0                               # forces one deterministic ignition
    r0, r1 = _step(p0, 0.0, 0.0), _step(p1, 0.0, 0.0)
    assert r0["B"] == r1["B"] == 1
    assert p1.theta - p0.theta == pytest.approx(delta, abs=1e-12)


@divergence("SSOT-P10")
def test_resonance_reset_uses_the_configured_delta():
    """One parameter, one value: the resonance-level threshold reported at an ignition step
    (output resonance_thetas[0]) rises by the configured δ_reset. Production applies the separate
    key DELTA_RESET (0.5, and `or 0.5` makes 0 unreachable), so with δ_reset = 0 the reported
    resonance threshold still jumps by 0.5 AU on the ignition step."""
    p = _legacy(hierarchical_mode="basic", stochastic_ignition=False, delta=0.0, resonance_kappa_down=0.0)
    for k in range(30):
        _step(p, 0.0, 0.0)
    p.S = 50.0
    r = _step(p, 0.0, 0.0)
    assert r["B"] == 1
    assert r["resonance_thetas"][0] == pytest.approx(p.theta, abs=1e-12)


@divergence("SSOT-P12")
def test_pac_threshold_factor_is_normalised():
    """EQ-MS-4: θ₀,ℓ(t) = θ₀,ℓ·[1 + κ_down·(Π_{ℓ+1}/Π_max)·cos φ̄_{ℓ+1}], bounded in [0.5, 1.5]·θ₀,ℓ.
    At Π_{ℓ+1} = Π_max and φ = 0 the factor is 1 + κ_down. Production omits /Π_max, so at the
    default Π_max = 10 and κ_down = 0.1 the factor is 2 (range [0, 2])."""
    import numpy as np

    p = _legacy(hierarchical_mode="basic")
    rs = p.resonance_system
    pi_max = float(p.config["pi_max"])
    rs.pi = np.full(rs.n_levels, pi_max)
    rs.phi = np.zeros(rs.n_levels)
    rs.theta_0 = np.full(rs.n_levels, 1.0)
    th = rs._compute_thresholds()
    assert th[0] == pytest.approx(1.0 + rs.kappa_down, rel=1e-12)


@divergence("SSOT-P12")
def test_pac_modulation_is_read_out_only():
    """TC-11 for EQ-MS-4: the phase-modulated threshold is a read-out of the allostatic state, not
    written back into it. Under stimulus-free N(0, 1) input the carried threshold therefore never
    reaches the numerical guard θ_clip_max (20 AU). Production writes the modulated level-0
    threshold back into θ, so the factor compounds step after step: with κ_down = 0.1 the run
    sits at the guard on about 28 % of steps (κ_down = 0: never; checked below as the control)."""
    import numpy as np

    def at_guard(kd):
        p = _legacy(hierarchical_mode="basic", resonance_kappa_down=kd, stochastic_ignition=False)
        g = np.random.default_rng(5)
        p.rng = np.random.default_rng(5)
        hits = 0
        for _ in range(4000):
            _step(p, float(g.standard_normal()), float(g.standard_normal()))
            hits += p.theta >= p.config["theta_clip_max"]
        return hits

    assert at_guard(0.0) == 0                        # control: without modulation the guard is idle
    assert at_guard(0.1) == 0


@divergence("SSOT-P13")
@pytest.mark.parametrize("gamma_ne", [0.2, -0.3])
def test_nonzero_gamma_ne_runs_both_ne_pathways(gamma_ne):
    """SSOT §11 (NE row: 'Both pathways share one clamped g_NE') and EQ-THEFF-1: with γ_NE ≠ 0 the
    canonical step applies g_NE to Πⁱ_eff and (1 + γ_NE·g_NE) to θ_eff. At production defaults
    (ne_on_threshold = False) the threshold pathway is silently dropped, so θ_eff, and then the
    event train, differ from apgi_ref on identical inputs and draws."""
    import production_report as PR

    xe, xi, us = PR.stimulus_free_inputs(2000)
    req = PR.requested_config({"gamma_ne": gamma_ne})
    p = PR.make_pipe({"gamma_ne": gamma_ne})
    p.rng = PR.FixedDraws(us)
    rp = PR.ref_params(req)
    s = R.core_state(rp)
    for k in range(2000):
        out = _step(p, float(xe[k]), float(xi[k]))
        s, log = R.core_step(s, float(xe[k]), float(xi[k]), rp, u=float(us[k]))
        assert out["theta_eff"] == pytest.approx(log["theta_eff"], rel=1e-9, abs=1e-12), k
        assert out["B"] == log["B"], k
