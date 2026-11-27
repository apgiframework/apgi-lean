"""Full-pipeline recovery study for TC-08d–g (SSOT §17), task 62b.

The canonical pipeline of apgi_ref.core_step (CFG-CORE, η_pred = 0) is rewritten here in a
form vectorized over G parameter sets, so that a likelihood can be evaluated on a whole grid
in one pass. test_recovery_pipeline.py checks that this simulator reproduces apgi_ref.core_step
step for step (same events, same S and θ), so the study runs on the canonical model.

Observation model of the study. The likelihood is that of the every-step event sequence B(t)
under the hazard sampler (EQ-HAZARD-1), with the inputs known. Given B, the paths of S and θ
are deterministic functions of the parameters, so the likelihood is exact. This is an oracle
observation: a hit/report (EQ-OBS-1/2) is a parameter-free function of B plus guess and lapse
noise, so by the data-processing inequality for Fisher information a report-level experiment
carries at most the information measured here (assumed standard result, not proved in Lean).
A parameter that is not identified here is not identified from behavior; one that is
identified here may still fail from behavior.

Everything the study needs that is not a registered value (stimulus, durations, r_max, the
generating ranges of the composite gains, grid sizes, seeds) is in
fixtures/recovery_design.json, marked as a synthetic design choice.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import apgi_ref as R

DESIGN_PATH = Path(__file__).with_name("fixtures") / "recovery_design.json"
REPORT_PATH = Path(__file__).resolve().parents[1] / "reports" / "recovery-pipeline.json"


def load_design() -> dict:
    return json.loads(DESIGN_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- inputs and channels

def make_inputs(rng: np.random.Generator, design: dict, inp: dict) -> tuple[np.ndarray, np.ndarray]:
    """Gaussian input on both channels plus periodic exteroceptive pulses; with `block_s` the
    pulses are present only in alternating on-blocks of that length (a slow design)."""
    n = int(round(design["duration_s"] / design["dt"]))
    t = np.arange(n) * design["dt"]
    x_e = rng.normal(0.0, inp["noise_sd"], n)
    x_i = rng.normal(0.0, inp["noise_sd"], n)
    on = (t % inp["pulse_period_s"]) < inp["pulse_s"]
    if inp.get("block_s"):
        on &= (t // inp["block_s"]) % 2 == 0
    return x_e + inp["pulse_amplitude"] * on, x_i


def channel(x, dt: float, window: float, eps_stab: float, pi_min: float, pi_max: float):
    """Steps 2–4 and 14 of one channel with η_pred = 0 (so ε = x): z from the sliding reference
    window that excludes ε_t (EQ-STD-1), Π from the EMA variance before the update
    (EQ-EMA-1/2, EQ-PREC-2). Returns (z, Π) as arrays over time."""
    x = np.asarray(x, dtype=float)
    n, N = len(x), max(2, round(window / dt))
    a = R.ema_alpha(dt, window)
    z, pi = np.empty(n), np.empty(n)
    mu, s2 = 0.0, 1.0
    for t in range(n):
        w = x[max(0, t - N):t]
        if len(w) < 2:
            m, sd = 0.0, 1.0
        else:
            m = float(w.mean())
            sd = math.sqrt(float(((w - m) ** 2).mean()))
        z[t] = (x[t] - m) / (sd + eps_stab)
        pi[t] = min(pi_max, max(pi_min, 1.0 / (s2 + eps_stab)))
        mu, s2 = (1.0 - a) * mu + a * x[t], (1.0 - a) * s2 + a * (x[t] - mu) ** 2
    return z, pi


def precompute(x_e, x_i, p: dict) -> dict:
    """Parameter-free channel quantities (z, Π) for both channels."""
    p = {**R.CORE_DEFAULTS, **p}
    ze, pe = channel(x_e, p["dt"], p["T_e"], p["eps_stab"], p["pi_min"], p["pi_max"])
    zi, pi = channel(x_i, p["dt"], p["T_i"], p["eps_stab"], p["pi_min"], p["pi_max"])
    return dict(z_e=ze, pi_e=pe, z_i=zi, pi_i=pi)


def _col(v):
    """A parameter as a column (G, 1) for broadcasting against time, or a scalar."""
    v = np.asarray(v, dtype=float)
    return v.reshape(-1, 1) if v.ndim else float(v)


def drive_series(ch: dict, p: dict):
    """Steps 5–6: neuromodulated precision and S_inst (EQ-NE-1, EQ-PREC-ACH-1, EQ-PREC-SM-1 with
    M̂ = 0, EQ-DA-1, EQ-PREC-REL-1, EQ-DRIVE-1). Parameters may be arrays over G sets; the
    result is (G, T) or (T,). Also returns the clamped g_NE and |zⁱ_eff|."""
    q = {**R.CORE_DEFAULTS, **p}
    gamma, g = np.asarray(q["gamma_ne"], float), np.asarray(q["g_ne"], float)
    with np.errstate(divide="ignore"):
        g_cl = np.where((gamma != 0) & (np.abs(gamma) * g > R.NE_BOUND), R.NE_BOUND / np.abs(gamma), g)
    lo, hi = q["pi_min"], q["pi_max"]
    pe_eff = np.clip(q["g_ach"] * ch["pi_e"], lo, hi)
    pi_eff = np.clip(_col(g_cl) * ch["pi_i"], lo, hi)
    zi_eff = ch["z_i"] + q["beta_da"]
    s_inst = (pe_eff / _col(q["pi_bar_e"]) * (np.abs(ch["z_e"]) - R.M0)
              + pi_eff / _col(q["pi_bar_i"]) * (np.abs(zi_eff) - R.M0))
    return s_inst, g_cl, np.abs(zi_eff)


def _sigmoid(k, x):
    """apgi_ref.ignition_prob, vectorized with the same branch formulas."""
    z = k * x
    e = np.exp(-np.abs(z))
    return np.where(z >= 0, 1.0 / (1.0 + e), e / (1.0 + e))


# ---------------------------------------------------------------- steps 7–15

def core_loop(ch: dict, p: dict, B_obs=None, u=None, keep_paths: bool = False) -> dict:
    """Steps 7–15 of apgi_ref.core_step for G parameter sets at once.

    With B_obs (shape (T,) or (G, T)) the observed events drive the state and the exact
    log-likelihood of B_obs is accumulated: log P(B=1) = log(1 − e^{−r_max·Bₜ·dt}),
    log P(B=0) = −r_max·Bₜ·dt. With u (uniform draws, shape (T,) or (G, T)) events are sampled
    as B = 1[u < P], exactly as core_step does. Parameters are scalars or arrays of length G;
    κ_up, β_5HT, u_urg and η_pred are off (CFG-CORE)."""
    q = {**R.CORE_DEFAULTS, **p}
    for k in ("kappa_up", "beta_5ht", "u_urg", "eta_pred_e", "eta_pred_i"):
        if np.any(np.asarray(q[k]) != 0):
            raise ValueError(f"core_loop covers CFG-CORE only; {k} must be 0")
    if np.ndim(q["beta_da"]) or np.ndim(q["dt"]) or np.ndim(q["tau_ref"]) or np.ndim(q["delta_ref"]):
        raise ValueError("beta_da, dt, tau_ref and delta_ref must be scalars")
    s_inst, g_cl, azi = drive_series(ch, q)
    aze, n = np.abs(ch["z_e"]), len(ch["z_e"])
    G = max([np.size(q[k]) for k in q if isinstance(q[k], (np.ndarray, list))] + [1])
    vec = lambda v: np.broadcast_to(np.asarray(v, float).reshape(-1), (G,)) if np.size(v) > 1 else np.full(G, float(np.asarray(v).reshape(-1)[0]))
    th0, eta, c1, c2, v1, v2 = (vec(q[k]) for k in ("theta0", "eta_theta", "c1", "c2", "v1", "v2"))
    ksig, rmax, rho, dlt = (vec(q[k]) for k in ("gamma_sig", "r_max", "rho_retain", "delta_reset"))
    dt = float(q["dt"])
    decay = np.exp(-(dt / vec(q["tau_theta"])))
    lam = -np.expm1(-(dt / vec(q["tau_S"])))
    nef = 1.0 + vec(q["gamma_ne"]) * vec(g_cl)
    rdec, dref = math.exp(-(dt / q["tau_ref"])), float(q["delta_ref"])
    floor = float(q["theta_floor"])
    s_inst = np.broadcast_to(s_inst, (G, n))
    S, th, r, Bp, ll = np.zeros(G), th0.copy(), np.zeros(G), np.zeros(G), np.zeros(G)
    Bs = np.zeros((G, n), dtype=np.int8) if B_obs is None or keep_paths else None
    paths = dict(S=np.empty((G, n)), theta=np.empty((G, n))) if keep_paths else None
    if B_obs is not None:
        B_obs = np.broadcast_to(np.asarray(B_obs), (G, n))
    if u is not None:
        u = np.broadcast_to(np.asarray(u, float), (G, n))
    for t in range(n):
        if keep_paths:
            paths["S"][:, t], paths["theta"][:, t] = S, th
        th_eff = th * nef + r                                            # 7
        x = rmax * _sigmoid(ksig, S - th_eff) * dt                       # 8 (existing S), 9
        if B_obs is not None:
            B = B_obs[:, t].astype(float)
            ll += np.where(B > 0, np.log(-np.expm1(-x)), -x)
        else:
            B = (u[:, t] < -np.expm1(-x)).astype(float)
        if Bs is not None:
            Bs[:, t] = B
        C = c1 * S + c2 * Bp                                             # 10
        V = v1 * aze[t] + v2 * azi[t]
        th = np.maximum(floor, th0 + (th + eta * (C - V) + dlt * B - th0) * decay)
        r = r * rdec + dref * B                                          # 11
        S = np.where(B > 0, rho * S, S)                                  # 12
        S = (1.0 - lam) * S + lam * s_inst[:, t]                         # 13
        Bp = B                                                           # 15
    out = dict(loglik=ll, B=Bs)
    if keep_paths:
        out.update(paths)
    return out


# ---------------------------------------------------------------- grid posterior and diagnostics

def grid_axes(design: dict, block: str) -> dict[str, np.ndarray]:
    return {k: np.linspace(lo, hi, n) for k, (lo, hi, n) in design["blocks"][block]["grid"].items()}


def grid_params(axes: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], tuple[int, ...]]:
    names = list(axes)
    mesh = np.meshgrid(*[axes[k] for k in names], indexing="ij")
    return {k: m.reshape(-1) for k, m in zip(names, mesh)}, mesh[0].shape


def block_params(design: dict, block: str, free: dict) -> dict:
    """The study's fixed parameters, the block's fixed parameters, then the free ones. The composite
    gains k_C = η_θ·c₁ and k_V = η_θ·v₁ are mapped to (η_θ = 1, c₁ = k_C, v₁ = k_V), which is
    exact by the TC-08g scale invariance (Lean: Apgi.traj_scaleAllo)."""
    p = {**design["fixed"], **design["blocks"][block].get("fixed", {})}
    for k, v in free.items():
        if k == "k_C":
            p["eta_theta"], p["c1"] = 1.0, v
        elif k == "k_V":
            p["eta_theta"], p["v1"] = 1.0, v
        elif k == "log_pi_scale":
            p["pi_bar_e"] = p["pi_bar_i"] = np.exp(v)
        else:
            p[k] = v
    return p


def posterior(ll: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    """Grid posterior under the uniform prior on the grid points."""
    w = np.exp(ll - ll.max())
    return (w / w.sum()).reshape(shape)


def summarize(post: np.ndarray, axes: dict[str, np.ndarray]) -> dict:
    """Posterior means, sds, correlations, and normalized profile log-likelihoods per axis."""
    names = list(axes)
    mesh = np.meshgrid(*[axes[k] for k in names], indexing="ij")
    mean = {k: float((post * m).sum()) for k, m in zip(names, mesh)}
    cov = {}
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            cov[a, b] = float((post * (mesh[i] - mean[a]) * (mesh[j] - mean[b])).sum())
    sd = {k: math.sqrt(max(cov[k, k], 0.0)) for k in names}
    corr = {f"{a}~{b}": (cov[a, b] / (sd[a] * sd[b]) if sd[a] > 0 and sd[b] > 0 else float("nan"))
            for i, a in enumerate(names) for b in names[i + 1:]}
    logp = np.log(np.maximum(post, 1e-300))
    prof = {k: (np.max(np.moveaxis(logp, i, 0).reshape(len(axes[k]), -1), axis=1) - logp.max()).tolist()
            for i, k in enumerate(names)}
    return dict(mean=mean, sd=sd, corr=corr, profile=prof)


def mode(post: np.ndarray, axes: dict[str, np.ndarray]) -> dict:
    idx = np.unravel_index(np.argmax(post), post.shape)
    return {k: float(axes[k][i]) for k, i in zip(axes, idx)}


def _logsumexp(a: np.ndarray) -> float:
    m = float(np.max(a))
    return m + math.log(float(np.sum(np.exp(a - m))))


def session(rng, design: dict, spec: dict):
    """Inputs, channel quantities and hazard draws of one synthetic session."""
    x_e, x_i = make_inputs(rng, design, design["inputs"][spec["input"]])
    ch = precompute(x_e, x_i, {**design["fixed"], **spec.get("fixed", {})})
    return ch, rng.random(len(x_e))


def run_block(design: dict, block: str) -> dict:
    """One block of the study: recovery (§17 gate), posterior correlations, profile likelihoods,
    SBC ranks and out-of-sample prediction for the block's free parameters.

    Truths are drawn from the uniform prior on the grid points, so the grid posterior is the
    exact Bayesian posterior and the SBC ranks are uniform exactly when the simulator and the
    likelihood agree (Talts et al. 2018). Posterior means are the point estimates."""
    spec = design["blocks"][block]
    axes = grid_axes(design, block)
    flat, shape = grid_params(axes)
    names, L = list(axes), design["sbc"]["draws"]
    rng = np.random.default_rng(spec["seed"])
    known = spec.get("known", [])  # axes also summarized as known: the posterior slice at the true value
    rows = []
    for i in range(spec["subjects"]):
        truth = {k: float(rng.choice(axes[k])) for k in names}
        ch, u = session(rng, design, spec)
        B = core_loop(ch, block_params(design, block, truth), u=u)["B"][0]
        ll = core_loop(ch, block_params(design, block, flat), B_obs=B)["loglik"]
        post = posterior(ll, shape)
        s = summarize(post, axes)
        draws = rng.choice(post.size, size=L, p=post.reshape(-1))
        rank = {}
        for k in names:
            v = flat[k][draws]
            rank[k] = int(np.sum(v < truth[k]) + rng.integers(0, np.sum(v == truth[k]) + 1))
        row = dict(truth=truth, mean=s["mean"], sd=s["sd"], corr=s["corr"], profile=s["profile"],
                   rank=rank, events=int(B.sum()))
        if known:
            sl, sub = post, dict(axes)
            for ck in known:
                j = int(np.argmin(np.abs(axes[ck] - truth[ck])))
                sl = np.take(sl, j, axis=list(sub).index(ck))
                del sub[ck]
            sc = summarize(sl / sl.sum(), sub)
            row["cond_mean"], row["cond_sd"] = sc["mean"], sc["sd"]
        if i < spec.get("oos_subjects", 0):
            ch2, u2 = session(rng, design, spec)
            B2 = core_loop(ch2, block_params(design, block, truth), u=u2)["B"][0]
            llh = core_loop(ch2, block_params(design, block, flat), B_obs=B2)["loglik"]
            lp = np.log(np.maximum(post.reshape(-1), 1e-300))
            null = core_loop(ch2, block_params(design, block, spec["null"]), B_obs=B2)["loglik"][0]
            at_truth = core_loop(ch2, block_params(design, block, truth), B_obs=B2)["loglik"][0]
            pred = _logsumexp(lp + llh)
            row["oos"] = dict(pred_minus_null=float(pred - null), truth_minus_pred=float(at_truth - pred))
        rows.append(row)
    return summarize_block(block, spec, axes, rows, L, design["sbc"]["bins"])


def _gate(tr: np.ndarray, est: np.ndarray, lo: float, hi: float) -> dict:
    r = float(np.corrcoef(tr, est)[0, 1]) if np.std(est) > 0 and np.std(tr) > 0 else float("nan")
    return dict(pearson_r=r, median_range_scaled_error=float(np.median(np.abs(est - tr)) / (hi - lo)))


def summarize_block(block, spec, axes, rows, L, bins) -> dict:
    names = list(axes)
    out = dict(block=block, tc=spec["tc"], question=spec["question"], input=spec["input"],
               subjects=len(rows), mean_events=float(np.mean([r["events"] for r in rows])),
               grid={k: [float(a[0]), float(a[-1]), len(a)] for k, a in axes.items()}, parameters={})
    known = spec.get("known", [])
    for k in names:
        tr = np.array([r["truth"][k] for r in rows]); est = np.array([r["mean"][k] for r in rows])
        lo, hi = float(axes[k][0]), float(axes[k][-1])
        prior_sd = float(np.std(axes[k]))
        rec = dict(**_gate(tr, est, lo, hi),
                   posterior_sd_over_prior_sd=float(np.mean([r["sd"][k] for r in rows]) / prior_sd),
                   sbc=sbc_test(np.array([r["rank"][k] for r in rows]), L, bins))
        if known and k not in known:
            ce = np.array([r["cond_mean"][k] for r in rows])
            rec["with_" + "_".join(known) + "_known"] = dict(
                **_gate(tr, ce, lo, hi),
                posterior_sd_over_prior_sd=float(np.mean([r["cond_sd"][k] for r in rows]) / prior_sd))
        out["parameters"][k] = rec
    out["posterior_correlation_median"] = {c: float(np.nanmedian([r["corr"][c] for r in rows])) for c in rows[0]["corr"]}
    out["profile_flat_fraction"] = {k: float(np.mean([np.mean(np.array(r["profile"][k]) > -2.0) for r in rows]))
                                    for k in names}
    oos = [r["oos"] for r in rows if "oos" in r]
    if oos:
        out["out_of_sample"] = dict(sessions=len(oos), null=spec["null"],
                                    mean_pred_minus_null_nats=float(np.mean([o["pred_minus_null"] for o in oos])),
                                    mean_truth_minus_pred_nats=float(np.mean([o["truth_minus_pred"] for o in oos])))
    return out


def source_hash() -> str:
    """sha256 of this module, so the committed report can be checked against the code that made it."""
    import hashlib
    return hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def run_study(design: dict | None = None, blocks: dict | None = None) -> dict:
    """The whole study. `blocks` may carry precomputed run_block results (make_recovery_report.py
    runs the blocks in parallel processes); each block depends only on its own seed."""
    design = design or load_design()
    import registry
    P = registry.params()
    return dict(design_status=design["status"], observation=design["observation"],
                design_sha256=design_hash(), source_sha256=source_hash(),
                gate=dict(r_HIGH=float(P["r_HIGH"]["value"]), err_gate=float(P["err_gate"]["value"])),
                blocks={b: (blocks or {}).get(b) or run_block(design, b) for b in design["blocks"]})


def design_hash() -> str:
    import hashlib
    return hashlib.sha256(DESIGN_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sbc_test(ranks: np.ndarray, L: int, bins: int) -> dict:
    """Chi-square uniformity test of SBC ranks in 0..L, pooled into `bins` equal bins.
    Returns the statistic, its degrees of freedom and an upper-tail p-value
    (Wilson–Hilferty approximation; no scipy dependency)."""
    counts = np.bincount((ranks * bins) // (L + 1), minlength=bins)
    expct = len(ranks) / bins
    chi2 = float(((counts - expct) ** 2 / expct).sum())
    k = bins - 1
    zz = ((chi2 / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    pval = 0.5 * math.erfc(zz / math.sqrt(2))
    return dict(chi2=chi2, df=k, p=pval, counts=counts.tolist())
