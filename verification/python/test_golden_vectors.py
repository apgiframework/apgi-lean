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
