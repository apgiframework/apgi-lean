"""Golden vectors (50-digit mpmath) vs float64 reference code at 1e-9."""
import json
from pathlib import Path

import pytest

import apgi_ref as R

G = json.loads(Path(__file__).with_name("golden_vectors.json").read_text(encoding="utf-8"))
REL, ABS = G["_meta"]["rel_tol"], G["_meta"]["abs_tol"]


def close(got, want):
    return got == pytest.approx(float(want), rel=REL, abs=ABS)


@pytest.mark.parametrize("v", G["ignition_prob"])
def test_ignition_prob(v):
    assert close(R.ignition_prob(v["k"], v["S"], v["theta"]), v["expected"])


@pytest.mark.parametrize("v", G["cusp_V"])
def test_cusp_V(v):
    assert close(R.cusp_V(v["a"], v["theta"], v["x"]), v["expected"])


@pytest.mark.parametrize("v", G["cusp_equilibria"])
def test_cusp_equilibria(v):
    got = R.cusp_equilibria(v["a"], v["theta"])
    assert len(got) == len(v["expected"])
    for g, w in zip(got, v["expected"]):
        assert close(g, w)


@pytest.mark.parametrize("v", G["landauer"])
def test_landauer(v):
    assert R.landauer(v["T"]) == pytest.approx(float(v["expected"]), rel=REL, abs=0)


@pytest.mark.parametrize("v", G["euler_step"])
def test_euler_step(v):
    assert close(R.euler_step(v["x"], v["u"], v["dt"], v["tau"]), v["expected"])


@pytest.mark.parametrize("v", G["decay_step"])
def test_decay_step(v):
    assert close(R.decay_step(v["theta"], v["theta0"], v["dt"], v["tau"]), v["expected"])


# ---- B-10 families (task 56) ----
import hashlib  # noqa: E402

import registry  # noqa: E402


@pytest.mark.parametrize("v", G["hazard_prob"])
def test_hazard_prob(v):
    assert close(R.hazard_prob(v["r_max"], v["B"], v["dt"]), v["expected"])


@pytest.mark.parametrize("v", G["leak_step"])
def test_leak_step(v):
    assert close(R.leak_step(v["S"], v["S_inst"], R.leak_gain(v["dt"], v["tau"])), v["expected"])


@pytest.mark.parametrize("v", G["ne_clamp"])
def test_ne_clamp(v):
    assert close(R.ne_clamp(v["gamma_ne"], v["g_ne"]), v["expected"])
    assert close(R.ne_factor(v["gamma_ne"], v["g_ne"]), v["factor"])


@pytest.mark.parametrize("v", G["threshold_step"])
def test_threshold_step(v):
    got = R.threshold_step(v["theta"], v["theta0"], v["eta"], v["C"], v["V"], v["delta"], v["B"], v["dt"], v["tau"])
    assert close(got, v["expected"])


@pytest.mark.parametrize("v", G["psi"])
def test_psi(v):
    assert close(R.psi(v["a_plus"], v["a_minus"], v["g_plus"], v["g_minus"], v["z"]), v["expected"])


@pytest.mark.parametrize("v", G["prec_eff"])
def test_prec_eff(v):
    raw = R.prec_eff(v["g_ne"], v["pi_base"], v["beta_sm"], v["m_hat"])
    assert close(raw, v["expected"])
    assert close(R.prec_clamp(0.1, 10.0, raw), v["clamped"])


@pytest.mark.parametrize("v", G["ema_update"])
def test_ema_update_ordering(v):
    a = R.ema_alpha(v["dt"], v["T_window"])
    assert close(a, v["alpha"])
    mu, s2 = R.ema_update(v["mu"], v["sigma2"], v["eps"], a)
    assert close(mu, v["mu_next"]) and close(s2, v["sigma2_next"])


@pytest.mark.parametrize("v", G["trajectory"], ids=lambda v: v["config"])
def test_seeded_trajectory(v):
    """TC-18 full-pipeline vectors: apgi_ref.core_step against the 50-digit replica, step by step."""
    rows = v["steps"]
    assert hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest() == v["sha256"]
    p = {k: val for k, val in v["params"].items()}
    s = R.core_state(p)
    for k, row in enumerate(rows):
        s, log = R.core_step(s, v["x_e"][k], v["x_i"][k], p, u=v["u"][k])
        assert log["B"] == row["B"], f"step {k}"
        assert close(log["B_prop"], row["B_prop"]), f"step {k}"
        for key in ("S", "theta", "r"):
            assert s[key] == pytest.approx(float(row[key]), rel=1e-9, abs=1e-12), f"step {k} {key}"


def test_trajectories_fire_and_cover_both_configs():
    names = {v["config"]: v for v in G["trajectory"]}
    assert set(names) == {"CFG-CORE", "CFG-CORE-R"}
    for v in names.values():
        assert 0 < sum(r["B"] for r in v["steps"]) < len(v["steps"])
    assert any(float(r["r"]) > 0 for r in names["CFG-CORE-R"]["steps"])
