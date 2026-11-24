"""Reference float64 implementations of the canonical APGI equations.

Each function names its equation ID (specification/equations.json) and the
Lean theorem(s) its twin property test checks it against. These are the
reference realisations; the Protocol 1-8 code should be tested against them.
"""
from __future__ import annotations

import math

import numpy as np

THETA_FLOOR = 0.5  # AU, theta_floor; test_conflicts checks this against the registry
K_B = 1.380649e-23  # J/K, exact (SI 2019)


def ignites(S: float, theta: float) -> bool:
    """EQ-IGN-1. Lean: Apgi.Ignites (θ < S)."""
    return theta < S


def signal(prec: float, eps: float) -> float:
    """EQ-PREC-1. S = Π·|ε|."""
    return prec * abs(eps)


def ignition_prob(k: float, S: float, theta: float) -> float:
    """EQ-IGN-2. Numerically stable logistic 1/(1+exp(-k(S-θ)))."""
    z = k * (S - theta)
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def clamped_update(theta: float, target: float, gain: float, floor: float = THETA_FLOOR) -> float:
    """EQ-THR-1. Lean: Apgi.clampedUpdate."""
    return max(floor, theta + gain * (target - theta))


def cusp_V(a: float, theta: float, x: float) -> float:
    """EQ-CUSP-1, canonical +θ·x sign."""
    return x**4 / 4 + a * x**2 / 2 + theta * x


def cusp_dV(a: float, theta: float, x: float) -> float:
    """dV/dx = x³ + a·x + θ. Lean: Apgi.cuspV_hasDerivAt."""
    return x**3 + a * x + theta


def cusp_discriminant(a: float, theta: float) -> float:
    """4a³ + 27θ². Negative ⇔ three distinct real equilibria."""
    return 4 * a**3 + 27 * theta**2


def cusp_equilibria(a: float, theta: float, imag_tol: float = 1e-9) -> list[float]:
    """Real roots of x³ + a x + θ, sorted, duplicates merged."""
    roots = np.roots([1.0, 0.0, a, theta])
    scale = max(1.0, abs(a), abs(theta))
    real = sorted(r.real for r in roots if abs(r.imag) <= imag_tol * scale)
    merged: list[float] = []
    for r in real:
        if not merged or abs(r - merged[-1]) > 1e-7 * scale:
            merged.append(r)
    return merged


def convex_update(x: float, u: float, gain: float) -> float:
    """EQ-UPD-1. Lean: Apgi.convex_update_mem_Icc."""
    return x + gain * (u - x)


def euler_step(x: float, u: float, dt: float, tau: float) -> float:
    """EQ-EULER-1. Lean: Apgi.euler_step_mem_Icc (requires 0 ≤ dt ≤ τ)."""
    return x + (dt / tau) * (u - x)


def landauer(T: float, k_B: float = K_B) -> float:
    """EQ-LAND-1. Minimum erasure energy per bit, J."""
    return k_B * T * math.log(2)
