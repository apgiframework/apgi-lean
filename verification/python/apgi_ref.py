"""Reference float64 implementations of the canonical APGI equations.

Each function names its equation ID (specification/equations.json) and the
Lean theorem(s) its twin property test checks it against. These are the
reference realisations; the Protocol 1-8 code should be tested against them.
"""
from __future__ import annotations

import math

import numpy as np

THETA_FLOOR = 0.0  # AU, theta_floor (Math Spec §4.5 default); test_conflicts checks this against the registry
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


def decay_step(theta: float, theta0: float, dt: float, tau: float) -> float:
    """EQ-DECAY-1 (Math Spec Eq. 32): exact step of dθ/dt = −(θ − θ₀)/τ.
    Lean: Apgi.decay_step_mem_Icc (bounded for every dt ≥ 0)."""
    return theta0 + (theta - theta0) * math.exp(-(dt / tau))


def landauer(T: float, k_B: float = K_B) -> float:
    """EQ-LAND-1. Minimum erasure energy per bit, J."""
    return k_B * T * math.log(2)


# ------------------------------------------------- specification 0.3.0 ----
NE_BOUND = 0.5  # max |γ_NE|·g_NE (ne_subdominance_bound); test_conflicts checks it against the registry


def leak_gain(dt: float, tau: float) -> float:
    """EQ-LEAK-1 (Math Spec Eq. 23–24): λ = 1 − exp(−dt/τ_S). Lean: Apgi.leakGain_mem_Ioo."""
    return -math.expm1(-(dt / tau))


def leak_step(S: float, s_inst: float, lam: float) -> float:
    """EQ-LEAK-1: S(t+1) = (1 − λ)·S(t) + λ·S_inst(t). Lean: Apgi.leak_step_mem_Icc, Apgi.leak_two_steps."""
    return (1.0 - lam) * S + lam * s_inst


def hazard_prob(r_max: float, B: float, dt: float) -> float:
    """EQ-HAZARD-1 (Math Spec Eq. 35): per-step ignition probability 1 − exp(−r_max·Bₜ·dt).
    Lean: Apgi.hazardProb_mem_Icc, Apgi.hazard_two_steps, Apgi.hazard_n_steps."""
    return -math.expm1(-(r_max * B * dt))


def ne_clamp(gamma_ne: float, g_ne: float, bound: float = NE_BOUND) -> float:
    """EQ-NE-1: rescale g_NE ← bound/|γ_NE| when |γ_NE|·g_NE > bound. Lean: Apgi.neClamp."""
    return g_ne if abs(gamma_ne) * g_ne <= bound else bound / abs(gamma_ne)


def ne_factor(gamma_ne: float, g_ne: float, bound: float = NE_BOUND) -> float:
    """EQ-NE-1: the θ_eff factor 1 + γ_NE·g_NE after the clamp. Lean: Apgi.neFactor_band."""
    return 1.0 + gamma_ne * ne_clamp(gamma_ne, g_ne, bound)


def allostatic_step(theta: float, eta: float, C: float, V: float, delta: float, B: float) -> float:
    """EQ-ALLO-1 (Math Spec Eq. 26): θ + η_θ·(C − V) + δ_reset·B. Lean: Apgi.allostaticStep."""
    return theta + eta * (C - V) + delta * B


def threshold_step(theta, theta0, eta, C, V, delta, B, dt, tau, floor: float = THETA_FLOOR) -> float:
    """EQ-ALLO-1: Eq. 26, then the exact decay of Eq. 32, then the §4.5 floor.
    Lean: Apgi.thresholdStep_floor, Apgi.thresholdStep_monotone_ignition, Apgi.thresholdStep_monotone_drive."""
    return max(floor, decay_step(allostatic_step(theta, eta, C, V, delta, B), theta0, dt, tau))


def psi(a_plus: float, a_minus: float, g_plus: float, g_minus: float, z: float) -> float:
    """EQ-PSI-1 (Math Spec Eq. 21): signed valence transform. Lean: Apgi.psi_abs_lt."""
    return a_plus * math.tanh(g_plus * z) if z >= 0 else a_minus * math.tanh(g_minus * z)


def prec_eff(g_ne: float, pi_base: float, beta_sm: float, m_hat: float) -> float:
    """EQ-PREC-SM-1: g_NE·Πⁱ_baseline·exp(β_SM·M̂) before the clamp. Lean: Apgi.precEff_monotone_marker."""
    return g_ne * pi_base * math.exp(beta_sm * m_hat)


def prec_clamp(lo: float, hi: float, x: float) -> float:
    """EQ-PREC-SM-1: the hard precision clamp [Π_min, Π_max]. Lean: Apgi.precClamp_mem_Icc."""
    return max(lo, min(hi, x))
