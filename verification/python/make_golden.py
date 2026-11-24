"""Regenerate golden_vectors.json with 50-digit mpmath arithmetic.
The vectors are the ground truth that float64 code must match to 1e-9."""
import json
from pathlib import Path

import mpmath as mp

mp.mp.dps = 50
OUT = Path(__file__).with_name("golden_vectors.json")


def s(x):
    return mp.nstr(x, 30)


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
    OUT.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
