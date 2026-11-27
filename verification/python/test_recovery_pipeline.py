"""TC-08d–g: full-pipeline recovery and identifiability (SSOT §17, task 62b).

What is tested here, and how.

1. The study's simulator is the canonical pipeline. recovery_pipeline.core_loop (vectorized over
   parameter sets) reproduces apgi_ref.core_step step for step: the same events, S and θ paths,
   and the same event log-likelihood (test_simulator_matches_core_step).
2. TC-08g has an exact part, proved in Apgi/Identifiability.lean: η_θ and the weights c₁, c₂, v₁,
   v₂ enter only as the products η_θ·c₁, η_θ·c₂, η_θ·v₁, η_θ·v₂ (Apgi.traj_scaleAllo), and with
   η_θ = 0 the weights do not enter (Apgi.traj_weights_eta_zero). Float64 twins below.
3. The statistical part is the study in recovery_pipeline.run_study, written by
   make_recovery_report.py to verification/reports/recovery-pipeline.json (about 3 minutes with
   the four blocks in parallel). The tests check that the committed report was produced by the
   current design and code (sha256), and assert its conclusions: SBC calibration of every block,
   the §17 gate outcome of every recovered quantity, the declared trade-offs, and out-of-sample
   prediction. A fast smoke run exercises the same code path end to end.

Scope limits. The observation is every-step events with known inputs (an oracle, an upper bound
on what behavior identifies); the design constants are synthetic choices
(fixtures/recovery_design.json); behavior-level fits are not done. Passing or failing recovery
says nothing about whether APGI is true (§17).
"""
from __future__ import annotations

import copy
import json
import math

import numpy as np
import pytest

import apgi_ref as R
import recovery_pipeline as RP
import registry

P = registry.params()
DESIGN = RP.load_design()
R_HIGH = float(P["r_HIGH"]["value"])
ERR_GATE = float(P["err_gate"]["value"])

# §17 gate outcome of every recovered quantity in the committed report (True = passes both
# Pearson r > r_HIGH and median range-scaled error < err_gate). A change in the study that flips
# one of these must be a deliberate, reviewed change of this table.
GATE_EXPECTED = {
    ("allo_fast", "tau_theta"): False,
    ("allo_fast", "k_C"): False,
    ("allo_fast", "k_V"): True,
    ("allo_blocks", "tau_theta"): False,
    ("allo_blocks", "k_C"): False,
    ("allo_blocks", "k_V"): True,
    ("ne", "gamma_ne"): True,
    ("ne", "g_ne"): True,
    ("sig", "gamma_sig"): True,
    ("sig", "log_pi_scale"): True,
    # Round 74 (task 62b remainder): η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair. All fail §17 at
    # this design; dispositions go with task 71a.
    ("allo_c2v2", "tau_theta"): False,
    ("allo_c2v2", "k_C2"): False,
    ("allo_c2v2", "k_V2"): False,
    ("c2_reset", "k_C2"): False,
    ("c2_reset", "delta_reset"): False,
}


def _inputs(n, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 0.01
    return rng.normal(0, 1, n) + 2.5 * ((t % 3) < 0.5), rng.normal(0, 1, n), rng.random(n)


FULL = dict(eta_theta=0.002, c1=0.3, c2=0.05, v1=0.2, v2=0.1, gamma_ne=0.45, g_ne=1.2,
            delta_reset=0.02, r_max=5.0, gamma_sig=5.0, theta0=0.35, tau_theta=20.0,
            delta_ref=0.1, beta_da=0.1, g_ach=1.3, pi_bar_e=0.8, pi_bar_i=1.25)


# ---------------------------------------------------------------- 1. simulator twin

@pytest.mark.parametrize("seed", [1, 2])
def test_simulator_matches_core_step(seed):
    """core_loop = apgi_ref.core_step, with every CFG-CORE term active (including the NE clamp:
    |γ_NE|·g_NE = 0.54 > 0.5, δ_reset, δ_ref, c₂, v₂, β_DA, g_ACh, Π̄ ≠ 1)."""
    x_e, x_i, u = _inputs(1500, seed)
    _, logs, _ = R.run_core(x_e, x_i, u, FULL)
    ch = RP.precompute(x_e, x_i, FULL)
    out = RP.core_loop(ch, FULL, u=u, keep_paths=True)
    B = np.array([l["B"] for l in logs])
    assert B.sum() > 5
    assert np.array_equal(out["B"][0], B)
    assert np.allclose(out["S"][0], [l["S_decided"] for l in logs], rtol=0, atol=1e-12)
    assert np.allclose(out["theta"][0], [l["theta_decided"] for l in logs], rtol=0, atol=1e-12)
    ll = sum(math.log(R.hazard_prob(FULL["r_max"], l["B_prop"], 0.01)) if l["B"]
             else math.log1p(-R.hazard_prob(FULL["r_max"], l["B_prop"], 0.01)) for l in logs)
    assert RP.core_loop(ch, FULL, B_obs=B)["loglik"][0] == pytest.approx(ll, rel=1e-9)


def test_grid_evaluation_equals_one_at_a_time():
    """A vectorized grid pass gives each parameter set the likelihood it gets alone."""
    x_e, x_i, u = _inputs(800, 3)
    ch = RP.precompute(x_e, x_i, FULL)
    B = RP.core_loop(ch, FULL, u=u)["B"][0]
    taus, etas = np.array([10.0, 20.0, 30.0]), np.array([0.0, 0.002, 0.004])
    grid = RP.core_loop(ch, {**FULL, "tau_theta": taus, "eta_theta": etas}, B_obs=B)["loglik"]
    for k in range(3):
        one = RP.core_loop(ch, {**FULL, "tau_theta": taus[k], "eta_theta": etas[k]}, B_obs=B)["loglik"][0]
        assert grid[k] == pytest.approx(one, rel=1e-12)


def test_core_loop_rejects_terms_outside_cfg_core():
    ch = RP.precompute(*_inputs(50, 4)[:2], FULL)
    with pytest.raises(ValueError):
        RP.core_loop(ch, {**FULL, "kappa_up": 0.1}, u=np.ones(50))


# ---------------------------------------------------------------- 2. TC-08g exact part

def _run(p, seed=5, n=1500):
    x_e, x_i, u = _inputs(n, seed)
    _, logs, _ = R.run_core(x_e, x_i, u, p)
    return [(l["B"], l["S_decided"], l["theta_decided"]) for l in logs]


@pytest.mark.parametrize("a", [2.0, 0.5, 4.0])
def test_tc08g_scale_twin(a):
    """Twin of Apgi.traj_scaleAllo: (η_θ, c₁, c₂, v₁, v₂) → (a·η_θ, c/a, v/a) gives the same
    trajectory. Powers of two keep the float64 products exact, so the equality is exact."""
    q = {**FULL, "eta_theta": a * FULL["eta_theta"], **{k: FULL[k] / a for k in ("c1", "c2", "v1", "v2")}}
    assert _run(q) == _run(FULL)


def test_tc08g_weights_irrelevant_at_eta_zero():
    """Twin of Apgi.traj_weights_eta_zero."""
    base = {**FULL, "eta_theta": 0.0}
    other = {**base, "c1": -3.0, "c2": 7.0, "v1": 0.0, "v2": 11.0}
    assert _run(other) == _run(base)


def test_tc08g_composites_are_what_the_study_fits():
    """The study maps k_C, k_V to (η_θ = 1, c₁ = k_C, v₁ = k_V); by TC-08g any (η_θ, c₁ = k_C/η_θ,
    v₁ = k_V/η_θ) is the same model."""
    p = RP.block_params(DESIGN, "allo_fast", {"tau_theta": 20.0, "k_C": 2e-4, "k_V": 1e-4})
    assert (p["eta_theta"], p["c1"], p["v1"]) == (1.0, 2e-4, 1e-4)
    x_e, x_i, u = _inputs(600, 6)
    ch = RP.precompute(x_e, x_i, p)
    q = {**p, "eta_theta": 4e-4, "c1": 0.5, "v1": 0.25}
    assert np.array_equal(RP.core_loop(ch, p, u=u)["B"], RP.core_loop(ch, q, u=u)["B"])


def test_tc08g_second_weights_are_what_the_study_fits():
    """The same mapping for the round-74 composites: k_C2 → (η_θ = 1, c₂ = k_C2) and
    k_V2 → (η_θ = 1, v₂ = k_V2); any (η_θ, c₂ = k_C2/η_θ, v₂ = k_V2/η_θ) gives the same events."""
    p = RP.block_params(DESIGN, "allo_c2v2", {"tau_theta": 20.0, "k_C2": 3e-3, "k_V2": 1e-4})
    assert (p["eta_theta"], p["c2"], p["v2"], p["c1"], p["v1"]) == (1.0, 3e-3, 1e-4, 0.0, 0.0)
    x_e, x_i, u = _inputs(600, 7)
    ch = RP.precompute(x_e, x_i, p)
    q = {**p, "eta_theta": 2e-3, "c2": 1.5, "v2": 0.05}
    assert np.array_equal(RP.core_loop(ch, p, u=u)["B"], RP.core_loop(ch, q, u=u)["B"])


# ---------------------------------------------------------------- design

def test_design_uses_registered_values():
    reg = DESIGN["registered_values_used"]
    assert float(P["theta_baseline"]["value"]) == reg["theta_baseline"] == DESIGN["fixed"]["theta0"]
    assert float(P["tau_S"]["value"]) == reg["tau_S"] == DESIGN["fixed"]["tau_S"]
    assert [float(P["tau_theta"]["range"][k]) for k in ("lo", "hi")] == reg["tau_theta_range"]
    assert [float(P["gamma_sig"]["range"][k]) for k in ("lo", "hi")] == reg["gamma_sig_range"]
    assert float(P["T_window_e"]["value"]) == reg["T_window_e"] == DESIGN["fixed"]["T_e"]
    assert float(P["T_window_i"]["value"]) == reg["T_window_i"] == DESIGN["fixed"]["T_i"]
    assert float(P["pi_min"]["value"]) == reg["pi_min"] == R.CORE_DEFAULTS["pi_min"]
    assert float(P["pi_max"]["value"]) == reg["pi_max"] == R.CORE_DEFAULTS["pi_max"]
    assert float(P["theta_floor"]["value"]) == reg["theta_floor"] == R.THETA_FLOOR
    tau = DESIGN["blocks"]["allo_fast"]["grid"]["tau_theta"]
    assert tau[:2] == reg["tau_theta_range"]
    assert DESIGN["blocks"]["sig"]["grid"]["gamma_sig"][:2] == reg["gamma_sig_range"]
    # EQ-STEP-1 holds for the design dt on every grid point (τ_S and the smallest τ_θ).
    assert R.step_rule(DESIGN["dt"], DESIGN["fixed"]["tau_S"], tau[0])
    assert DESIGN["fixed"]["dt"] == DESIGN["dt"]


# ---------------------------------------------------------------- 3. the committed study

@pytest.fixture(scope="module")
def report():
    return json.loads(RP.REPORT_PATH.read_text(encoding="utf-8"))


def test_report_is_current(report):
    """The committed report was made from this design and this code. If this fails, rerun
    `python make_recovery_report.py` (verify_all.ps1 does) and review the diff."""
    assert report["design_sha256"] == RP.design_hash()
    assert report["source_sha256"] == RP.source_hash()
    assert set(report["blocks"]) == set(DESIGN["blocks"])
    assert report["gate"] == {"r_HIGH": R_HIGH, "err_gate": ERR_GATE}
    for b, r in report["blocks"].items():
        assert r["subjects"] == DESIGN["blocks"][b]["subjects"]


def test_sbc_calibrated(report):
    """Simulation-based calibration: with truths drawn from the grid prior, the rank of the truth
    among 99 posterior draws is uniform when simulator and likelihood agree. Every recovered
    quantity of every block passes a 10-bin χ² test at α = 0.001."""
    for b, r in report["blocks"].items():
        for k, v in r["parameters"].items():
            assert v["sbc"]["p"] > 0.001, (b, k, v["sbc"])
            assert sum(v["sbc"]["counts"]) == r["subjects"]


def test_gate_outcomes(report):
    """§17 gate per recovered quantity, against GATE_EXPECTED (the reviewed record)."""
    seen = {}
    for b, r in report["blocks"].items():
        for k, v in r["parameters"].items():
            seen[b, k] = bool(v["pearson_r"] is not None and v["pearson_r"] > R_HIGH
                              and v["median_range_scaled_error"] < ERR_GATE)
            print(f"TC-08 {b:12s} {k:13s} r = {v['pearson_r']:.3f}, error = "
                  f"{v['median_range_scaled_error']:.3f}, posterior sd/prior sd = "
                  f"{v['posterior_sd_over_prior_sd']:.2f} -> {'pass' if seen[b, k] else 'FAIL'}")
    assert seen == GATE_EXPECTED


def test_tc08e_tradeoff_present(report):
    """TC-08e: adaptation (k_V) and recovery (τ_θ) trade off: the median posterior correlation
    is strongly negative in both designs, and τ_θ is barely narrowed by the data."""
    for b in ("allo_fast", "allo_blocks"):
        r = report["blocks"][b]
        assert r["posterior_correlation_median"]["tau_theta~k_V"] < -0.5
        assert r["parameters"]["tau_theta"]["posterior_sd_over_prior_sd"] > 0.6


def test_tc08g_cost_weight_unidentified(report):
    """TC-08g: k_C = η_θ·c₁ is not narrowed by the data at all (posterior sd ≈ prior sd), and its
    profile likelihood is flat (within 2 log units) over the whole grid."""
    for b in ("allo_fast", "allo_blocks"):
        r = report["blocks"][b]
        assert r["parameters"]["k_C"]["posterior_sd_over_prior_sd"] > 0.95
        assert r["profile_flat_fraction"]["k_C"] > 0.95


def test_tc08g_second_weights_trade_off(report):
    """Round 74. allo_c2v2: k_C2 (raises θ after each event) and k_V2 (lowers θ with |z_i|) are
    positively correlated a posteriori: the events mainly constrain their net effect on θ.
    c2_reset: k_C2·B(t−1) and δ_reset·B(t) are the same per-event increment one step apart; they
    are negatively correlated, though not fully degenerate (median correlation about −0.6)."""
    assert report["blocks"]["allo_c2v2"]["posterior_correlation_median"]["k_C2~k_V2"] > 0.5
    c = report["blocks"]["c2_reset"]["posterior_correlation_median"]["k_C2~delta_reset"]
    assert -0.9 < c < -0.3
    for k in ("k_C2", "delta_reset"):
        assert report["blocks"]["c2_reset"]["parameters"][k]["posterior_sd_over_prior_sd"] > 0.6


def test_tc08f_free_scale_costs_little_here(report):
    """TC-08f: with the precision scale Π̄ free, γ_sig is still recovered, and knowing Π̄ narrows
    it further. The scale is identifiable here only because θ₀ is fixed at its registered value;
    with θ₀ free too, TC-08c makes (S scale, θ, γ_sig) exactly degenerate (Apgi.hazardLik_rescale)."""
    g = report["blocks"]["sig"]["parameters"]["gamma_sig"]
    known = g["with_log_pi_scale_known"]
    assert known["posterior_sd_over_prior_sd"] < g["posterior_sd_over_prior_sd"]


def test_out_of_sample_prediction(report):
    """Held-out sessions at the same truth: the posterior predictive beats the block's null model
    (no allostatic drive, or no NE coupling) in every block that has one, and is within 1 nat
    per session of the truth on average."""
    for b, r in report["blocks"].items():
        o = r.get("out_of_sample")
        if o is None:
            continue
        assert o["mean_pred_minus_null_nats"] > 0, b
        assert o["mean_truth_minus_pred_nats"] < 1.0, b


def test_smoke_run_block_deterministic():
    """The study code path end to end, small and fast, and deterministic for a fixed seed."""
    d = copy.deepcopy(DESIGN)
    d["duration_s"] = 30.0
    d["blocks"] = {"ne": dict(DESIGN["blocks"]["ne"], subjects=3, oos_subjects=1,
                              grid={"gamma_ne": [-0.4, 0.4, 3], "g_ne": [0.5, 1.5, 3]})}
    a, b = RP.run_block(d, "ne"), RP.run_block(d, "ne")
    assert a == b
    assert set(a["parameters"]) == {"gamma_ne", "g_ne"}
    assert a["out_of_sample"]["sessions"] == 1


def test_sbc_detects_a_mismatched_likelihood():
    """SBC is not vacuous: when the likelihood uses the wrong r_max (2× the simulator's), the ranks
    of γ_sig are far from uniform."""
    d = copy.deepcopy(DESIGN)
    d["duration_s"] = 60.0
    spec = dict(tc="test", question="test", input="fast", grid={"gamma_sig": [2.0, 7.5, 12]},
                subjects=40, seed=7)
    d["blocks"] = {"g": spec}
    axes = RP.grid_axes(d, "g")
    flat, shape = RP.grid_params(axes)
    rng = np.random.default_rng(spec["seed"])
    ranks = []
    for _ in range(spec["subjects"]):
        truth = {"gamma_sig": float(rng.choice(axes["gamma_sig"]))}
        ch, u = RP.session(rng, d, spec)
        B = RP.core_loop(ch, RP.block_params(d, "g", truth), u=u)["B"][0]
        wrong = {**RP.block_params(d, "g", flat), "r_max": 2 * d["fixed"]["r_max"]}
        post = RP.posterior(RP.core_loop(ch, wrong, B_obs=B)["loglik"], shape)
        v = flat["gamma_sig"][rng.choice(post.size, size=99, p=post.reshape(-1))]
        ranks.append(int(np.sum(v < truth["gamma_sig"]) + rng.integers(0, np.sum(v == truth["gamma_sig"]) + 1)))
    assert RP.sbc_test(np.array(ranks), 99, 10)["p"] < 0.001
