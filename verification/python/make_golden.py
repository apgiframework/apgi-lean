"""Regenerate golden_vectors.json with 50-digit mpmath arithmetic.
The vectors are the ground truth that float64 code must match to 1e-9."""
import hashlib
import json
from pathlib import Path

import mpmath as mp
import numpy as np

mp.mp.dps = 50
OUT = Path(__file__).with_name("golden_vectors.json")


def s(x):
    return mp.nstr(x, 30)


# ---- 50-digit replica of apgi_ref.core_step (SSOT §8 order), for seeded trajectories ----
TRAJ_BASE = dict(dt="0.01", tau_S="0.3", theta0="0.35", tau_theta="20", eta_theta="0", delta_reset="0",
                 rho_retain="0.3", gamma_sig="5", r_max="100", c1="0", c2="0", v1="0", v2="0", tau_ref="0.3",
                 delta_ref="0", pi_min="0.1", pi_max="10", T_e="5", T_i="10", eps_stab="1e-8")
TRAJ_STEPS, TRAJ_SEED = 120, 10101


def _ref(window):
    if len(window) < 2:
        return mp.mpf(0), mp.mpf(1)
    mu = mp.fsum(window) / len(window)
    return mu, mp.sqrt(mp.fsum((w - mu) ** 2 for w in window) / len(window))


def trajectory(name, over):
    """Seeded CFG-CORE / CFG-CORE-R run: x_e carries a 1.5-AU pulse in steps 30-59 on top of N(0,1) noise.
    Inputs and uniform draws are stored, so the vector does not depend on any RNG implementation."""
    p = {k: mp.mpf(str(v)) for k, v in {**TRAJ_BASE, **over}.items()}
    rng = np.random.default_rng(TRAJ_SEED)
    xe = [float(rng.standard_normal()) + (1.5 if 30 <= k < 60 else 0.0) for k in range(TRAJ_STEPS)]
    xi = [float(rng.standard_normal()) for _ in range(TRAJ_STEPS)]
    us = [float(rng.random()) for _ in range(TRAJ_STEPS)]
    m0 = mp.sqrt(2 / mp.pi)
    S, th, r, Bp = mp.mpf(0), p["theta0"], mp.mpf(0), 0
    mu = {"e": mp.mpf(0), "i": mp.mpf(0)}
    s2 = {"e": mp.mpf(1), "i": mp.mpf(1)}
    ref = {"e": [], "i": []}
    lam = 1 - mp.exp(-p["dt"] / p["tau_S"])
    a = {"e": 1 - mp.exp(-p["dt"] / p["T_e"]), "i": 1 - mp.exp(-p["dt"] / p["T_i"])}
    keep = {"e": int(round(float(p["T_e"] / p["dt"]))), "i": int(round(float(p["T_i"] / p["dt"])))}
    rows = []
    for k in range(TRAJ_STEPS):
        eps = {"e": mp.mpf(xe[k]), "i": mp.mpf(xi[k])}
        z, pe = {}, {}
        for c in "ei":
            m, sd = _ref(ref[c])
            z[c] = (eps[c] - m) / (sd + p["eps_stab"])
            pe[c] = max(p["pi_min"], min(p["pi_max"], 1 / (s2[c] + p["eps_stab"])))
        s_inst = pe["e"] * (abs(z["e"]) - m0) + pe["i"] * (abs(z["i"]) - m0)
        th_eff = th + r
        bprop = 1 / (1 + mp.exp(-p["gamma_sig"] * (S - th_eff)))
        haz = 1 - mp.exp(-p["r_max"] * bprop * p["dt"])
        B = int(mp.mpf(us[k]) < haz)
        C = p["c1"] * S + p["c2"] * Bp
        V = p["v1"] * abs(z["e"]) + p["v2"] * abs(z["i"])
        pre = th + p["eta_theta"] * (C - V) + p["delta_reset"] * B
        th = max(mp.mpf(0), p["theta0"] + (pre - p["theta0"]) * mp.exp(-p["dt"] / p["tau_theta"]))
        r = r * mp.exp(-p["dt"] / p["tau_ref"]) + p["delta_ref"] * B
        if B:
            S = p["rho_retain"] * S
        S = (1 - lam) * S + lam * s_inst
        for c in "ei":
            mu_old = mu[c]
            mu[c] = (1 - a[c]) * mu_old + a[c] * eps[c]
            s2[c] = (1 - a[c]) * s2[c] + a[c] * (eps[c] - mu_old) ** 2
            ref[c] = (ref[c] + [eps[c]])[-max(2, keep[c]):]
        Bp = B
        rows.append({"B_prop": s(bprop), "B": B, "S": s(S), "theta": s(th), "r": s(r)})
    params = {k: float(v) for k, v in {**TRAJ_BASE, **over}.items()}
    payload = {"config": name, "params": params, "seed": TRAJ_SEED, "x_e": xe, "x_i": xi, "u": us, "steps": rows}
    payload["sha256"] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return payload


def main():
    v = {"_meta": {"generator": "make_golden.py", "mp_dps": 50, "rel_tol": 1e-9, "abs_tol": 1e-12}}
    v["ignition_prob"] = [
        {"k": k, "S": S, "theta": th, "expected": s(1 / (1 + mp.exp(-mp.mpf(k) * (mp.mpf(S) - mp.mpf(th)))))}
        for k, S, th in [(1, 3, 2), (2.5, 2, 2), (4, 1.2, 6.5), (0.3, 7.9, 2.1), (10, 2.05, 2), (50, 1, 8)]
    ]
    v["cusp_V"] = [
        {"a": a, "theta": th, "x": x, "expected": s(mp.mpf(x)**4 / 4 + mp.mpf(a) * mp.mpf(x)**2 / 2 + mp.mpf(th) * mp.mpf(x))}
        for a, th, x in [(-1, 0, 1), (-3, 0.5, -1.7), (2, -1, 0.3), (-0.5, 0.1, 2.2)]
    ]
    v["cusp_equilibria"] = []
    for a, th in [(-1, 0), (-3, 1), (-3, 3), (1, 1), (-2, 0.5)]:
        r = sorted(mp.re(z) for z in mp.polyroots([1, 0, a, th], maxsteps=200, extraprec=200) if abs(mp.im(z)) < mp.mpf("1e-30"))
        v["cusp_equilibria"].append({"a": a, "theta": th, "expected": [s(x) for x in r]})
    kB = mp.mpf("1.380649e-23")
    v["landauer"] = [{"T": T, "expected": s(kB * T * mp.log(2))} for T in (300, 310, 310.15)]
    v["euler_step"] = [
        {"x": x, "u": u, "dt": dt, "tau": tau, "expected": s(mp.mpf(x) + (mp.mpf(dt) / tau) * (mp.mpf(u) - x))}
        for x, u, dt, tau in [(2, 8, 0.01, 0.2), (7.5, 2, 0.2, 0.2), (0.5, 3, 0.001, 1.5)]
    ]
    v["decay_step"] = [
        {"theta": th, "theta0": t0, "dt": dt, "tau": tau,
         "expected": s(mp.mpf(t0) + (mp.mpf(th) - t0) * mp.exp(-mp.mpf(dt) / tau))}
        for th, t0, dt, tau in [(0.85, 0.35, 0.01, 20), (0.25, 0.35, 0.01, 10), (0.6, 0.35, 3.0, 1.0), (0.3, 0.55, 0.5, 30)]
    ]

    # ---- B-10 families (task 56) ----
    v["hazard_prob"] = [
        {"r_max": r, "B": B, "dt": dt, "expected": s(1 - mp.exp(-mp.mpf(r) * mp.mpf(B) * mp.mpf(dt)))}
        for r, B, dt in [(100, 0.332, 0.01), (10, 0.5, 0.01), (1.5, 0.0017, 0.01), (20, 0.38, 0.5), (1, 1, 1)]
    ]
    v["leak_step"] = [
        {"S": S, "S_inst": u, "dt": dt, "tau": tau,
         "expected": s(mp.exp(-mp.mpf(dt) / tau) * S + (1 - mp.exp(-mp.mpf(dt) / tau)) * u)}
        for S, u, dt, tau in [(0, 1, 0.01, 0.3), (0.5, -0.2, 0.01, 0.3), (-0.3, 2.4, 0.001, 0.2), (1.2, 0, 0.3, 0.3)]
    ]
    v["ne_clamp"] = []
    for gm, g in [(0.3, 1.0), (0.8, 1.0), (-0.8, 1.0), (-2.0, 0.6), (0.0, 3.0), (0.5, 1.0)]:
        gm_, g_ = mp.mpf(gm), mp.mpf(g)
        gc = g_ if abs(gm_) * g_ <= mp.mpf("0.5") else mp.mpf("0.5") / abs(gm_)
        v["ne_clamp"].append({"gamma_ne": gm, "g_ne": g, "expected": s(gc), "factor": s(1 + gm_ * gc)})
    v["threshold_step"] = []
    for th, t0, eta, C, V, d, B, dt, tau in [(0.35, 0.35, 0.01, 0.4, 0.1, 0.05, 1, 0.01, 20),
                                             (0.85, 0.35, 0.0, 0, 0, 0.0, 0, 0.01, 20),
                                             (0.02, 0.35, 0.5, 0, 1.0, 0.0, 0, 0.01, 20),
                                             (0.5, 0.35, 0.02, 1.2, 0.3, 0.1, 1, 0.5, 10)]:
        pre = mp.mpf(th) + mp.mpf(eta) * (mp.mpf(C) - V) + mp.mpf(d) * B
        dec = mp.mpf(t0) + (pre - t0) * mp.exp(-mp.mpf(dt) / tau)
        v["threshold_step"].append({"theta": th, "theta0": t0, "eta": eta, "C": C, "V": V, "delta": d, "B": B,
                                    "dt": dt, "tau": tau, "expected": s(max(mp.mpf(0), dec))})
    v["psi"] = []
    for ap, am, gp, gm, z in [(1, 1, 2, 2, 0.3), (1.5, 0.8, 1.0, 3.0, -0.7), (2.0, 0.5, 5.0, 1.0, 2.5), (1, 1, 1, 1, 0)]:
        z_ = mp.mpf(z)
        val = mp.mpf(ap) * mp.tanh(gp * z_) if z_ >= 0 else mp.mpf(am) * mp.tanh(gm * z_)
        v["psi"].append({"a_plus": ap, "a_minus": am, "g_plus": gp, "g_minus": gm, "z": z, "expected": s(val)})
    v["prec_eff"] = []
    for gne, pb, bsm, M in [(1, 1, 1.2, 2), (1, 0.5, 0.3, -2), (0.5, 3, 0.8, 1.1), (1.2, 2, 0, 1.7)]:
        raw = mp.mpf(gne) * pb * mp.exp(mp.mpf(bsm) * M)
        v["prec_eff"].append({"g_ne": gne, "pi_base": pb, "beta_sm": bsm, "m_hat": M,
                              "expected": s(raw), "clamped": s(max(mp.mpf("0.1"), min(mp.mpf(10), raw)))})
    v["ema_update"] = []
    for mu, s2, eps, dt, T in [(0, 1, 0.7, 0.01, 5), (0.2, 0.5, -1.3, 0.01, 10), (1.0, 2.0, 3.0, 0.1, 5)]:
        a = 1 - mp.exp(-mp.mpf(dt) / T)
        v["ema_update"].append({"mu": mu, "sigma2": s2, "eps": eps, "dt": dt, "T_window": T, "alpha": s(a),
                                "mu_next": s((1 - a) * mu + a * eps),
                                "sigma2_next": s((1 - a) * s2 + a * (mp.mpf(eps) - mu) ** 2)})
    v["trajectory"] = [trajectory("CFG-CORE", {}), trajectory("CFG-CORE-R", {"delta_ref": 0.3, "delta_reset": 0.05,
                                                                          "eta_theta": 0.01, "c2": 0.2, "v1": 0.05})]
    OUT.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
