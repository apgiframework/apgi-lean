"""TC-10 and TC-14 run report for the pinned production core (task 61b).

SSOT §23 TC-10 requires that "the fraction of clamped steps is reported", and TC-14 that
γ_sig·θ₀, σ(−γ_sig·θ₀) and the stimulus-free event rate are reported for every configuration.
apgi_ref.clamp_report does this for the reference. This module does it for the production
package (apgiframework/apgi-implementation at the commit pinned in known-conflicts.json): it
runs the production pipeline, derives the clamp fractions from the values production returns
at each step, and runs apgi_ref.core_step on the same inputs and uniform draws as a check.

The clamp report is derived by this harness from production's per-step outputs; production
itself does not count clamped steps (stated as the remaining limitation of REQ-TC-10).

Usage: APGI_IMPL_PATH=<checkout> python production_report.py [--check]
Writes verification/reports/production-run-report.json; --check compares instead of writing.
"""
from __future__ import annotations

import copy
import json
import os
import sys
import warnings
from pathlib import Path

import apgi_ref as R
from registry import ROOT, load

REPORT = ROOT / "verification" / "reports" / "production-run-report.json"
SEED = 20261127          # protocol seed of this report (numpy SeedSequence)
STEPS = 6000             # 60 s at the production default dt = 0.01 s
CONFIGS = {              # SSOT §9 reserved configuration names; overrides on production CONFIG
    "CFG-CORE": {},
    "CFG-CORE-R": {"delta_ref": 0.3, "delta": 0.05},
}


def _impl() -> str:
    impl = os.environ.get("APGI_IMPL_PATH")
    if not impl or not (Path(impl) / "core" / "ssot_core.py").exists():
        raise SystemExit("APGI_IMPL_PATH must point at an apgi-implementation checkout")
    if impl not in sys.path:
        sys.path.insert(0, impl)
    return impl


class FixedDraws:
    """Feeds the production hazard sampler a given sequence of uniform draws."""

    def __init__(self, us):
        self._it = iter(us)

    def random(self):
        return next(self._it)


def ref_params(cfg: dict) -> dict:
    """apgi_ref parameters equal to a production CONFIG (same mapping as test_production.py)."""
    return dict(dt=cfg["dt"], tau_S=cfg["tau_s"], theta0=cfg["theta_base"], tau_theta=cfg["tau_theta"],
                theta_floor=cfg["theta_clip_min"], eta_theta=cfg["eta"], delta_reset=cfg["delta"],
                rho_retain=cfg["RHO_RETAIN"], gamma_sig=1.0 / cfg["ignite_tau"], r_max=cfg["r_max"],
                c1=cfg["c1"], c2=cfg["c2"], v1=cfg["v1"], v2=cfg["v2"], g_ach=cfg["g_ach"], g_ne=cfg["g_ne"],
                gamma_ne=cfg["gamma_ne"] or 0.0, beta_da=cfg["beta"], beta_5ht=cfg["beta_5ht"],
                tau_ref=cfg["tau_ref"], delta_ref=cfg["delta_ref"], pi_min=cfg["pi_min"], pi_max=cfg["pi_max"],
                pi_bar_e=cfg["pi_bar_e"], pi_bar_i=cfg["pi_bar_i"], eta_pred_e=cfg["eta_pred_e"],
                eta_pred_i=cfg["eta_pred_i"], T_e=cfg["T_window_e"], T_i=cfg["T_window_i"], eps_stab=cfg["eps"])


def production_clamp_flags(out: dict, cfg: dict) -> tuple[bool, bool]:
    """TC-10 flags for one production step, from the values production returns.

    Precision: production clips each of Πᵉ, Πⁱ, Πᵉ_eff, Πⁱ_eff with clip(Π_min, Π_max, ·), which
    returns the bound itself when it binds, so a returned value equal to a bound marks a binding
    clamp. (apgi_ref flags a raw value strictly outside the bounds; the two differ only when a raw
    value equals a bound exactly.) NE: EQ-NE-1 binds when |γ_NE|·g_NE > 0.5; both are constants
    of the requested configuration, so the flag is the same on every step. Production applies
    EQ-NE-1 once, when APGIPipeline validates the configuration (g_NE ← 0.5/|γ_NE|, with a
    warning), so the clamped gain is the one used on every step; `cfg` must therefore be the
    requested configuration (requested_config), not the validated pipe.config."""
    lo, hi = float(cfg["pi_min"]), float(cfg["pi_max"])
    pi = any(out[k] in (lo, hi) for k in ("pi_e", "pi_i", "pi_e_eff", "pi_i_eff"))
    g = float(cfg.get("gamma_ne") or 0.0)
    ne = bool(g) and abs(g) * float(cfg["g_ne"]) > R.NE_BOUND
    return pi, ne


def requested_config(over: dict) -> dict:
    """Production's default CONFIG with `over` applied, before APGIPipeline validates it."""
    _impl()
    import config as PCFG

    cfg = copy.deepcopy(PCFG.CONFIG)
    cfg.update(over)
    return cfg


def make_pipe(over: dict):
    """A fresh production pipeline at the default CONFIG with `over` applied."""
    import pipeline as PP

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PP.APGIPipeline(requested_config(over))


def run_pair(over: dict, xe, xi, us) -> dict:
    """Run production and apgi_ref on the same inputs and draws; return both reports."""
    req = requested_config(over)
    p = make_pipe(over)
    assert p.model_form == "ssot_core", p.model_form
    p.rng = FixedDraws(us)
    rp = ref_params(req)       # the reference applies EQ-NE-1 itself, step by step
    s, logs = R.core_state(rp), []
    flags, events = [], 0
    pis = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for a, b, u in zip(xe, xi, us):
            out = p.step(float(a), float(b))
            flags.append(production_clamp_flags(out, req))
            pis += [out[k] for k in ("pi_e", "pi_i", "pi_e_eff", "pi_i_eff")]
            events += int(out["B"])
            s, log = R.core_step(s, float(a), float(b), rp, u=float(u))
            logs.append(log)
    n = len(flags)
    dt = float(p.config["dt"])
    ref = R.clamp_report(logs)
    m = p.manifest()
    op = {**m, **(m.get("operating_point") or {})}
    return {
        "steps": n,
        "dt_s": dt,
        "production": {
            "precision_clamped_fraction": sum(f[0] for f in flags) / n,
            "ne_clamped_fraction": sum(f[1] for f in flags) / n,
            "events": events,
            "event_rate_per_s": events / (n * dt),
            "precision_range": [min(pis), max(pis)],
            "operating_point": {k: op.get(k) for k in ("gamma_sig_theta0", "propensity_floor", "baseline_rate")},
        },
        "reference": {
            "precision_clamped_fraction": ref["precision_clamped_fraction"],
            "ne_clamped_fraction": ref["ne_clamped_fraction"],
            "events": sum(l["B"] for l in logs),
            "operating_point": R.operating_point(rp["gamma_sig"], rp["theta0"], rp["r_max"]),
        },
    }


def stimulus_free_inputs(steps: int = STEPS, seed: int = SEED):
    """TC-07/TC-14 stimulus-free input: independent N(0, 1) samples per channel, plus uniform draws."""
    import numpy as np

    g = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))
    return g.standard_normal(steps), g.standard_normal(steps), g.random(steps)


def build() -> dict:
    _impl()
    kc = load("known-conflicts.json")["production"]
    xe, xi, us = stimulus_free_inputs()
    return {
        "schema": "apgi-production-run-report/1",
        "purpose": "SSOT §23 TC-10 (clamped-step fraction) and TC-14 (operating point, stimulus-free "
                   "event rate) for the pinned production core; apgi_ref on identical inputs and draws.",
        "production_commit": kc["commit"],
        "input": {"kind": "stimulus-free N(0,1) per channel", "seed": SEED, "steps": STEPS,
                  "rng": "numpy PCG64(SeedSequence(seed)): x_e, x_i, then uniform draws"},
        "configurations": {name: run_pair(over, xe, xi, us) for name, over in CONFIGS.items()},
        "limitation": "Clamp flags are derived by apgi-lean from production's per-step outputs; "
                      "production does not count clamped steps itself.",
    }


def _rounded(x, nd: int = 9):
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, dict):
        return {k: _rounded(v, nd) for k, v in x.items()}
    if isinstance(x, list):
        return [_rounded(v, nd) for v in x]
    return x


def main(argv: list[str]) -> int:
    rep = _rounded(build())
    text = json.dumps(rep, indent=2, ensure_ascii=False) + "\n"
    if "--check" in argv:
        old = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else None
        if old != rep:
            print(f"{REPORT.relative_to(ROOT)} is stale: rerun production_report.py")
            return 1
        print(f"{REPORT.relative_to(ROOT)} is current")
        return 0
    REPORT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {REPORT.relative_to(ROOT)}")
    for name, r in rep["configurations"].items():
        pr = r["production"]
        print(f"  {name}: clamped {pr['precision_clamped_fraction']}, NE {pr['ne_clamped_fraction']}, "
              f"{pr['events']} events ({pr['event_rate_per_s']} /s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
