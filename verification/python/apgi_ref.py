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


# ------------------------------------- specification 0.4.0: SSOT v1.2 minimal core ----
# Equations of the SSOT minimal core (Math Spec v1.2 draft §1-§6, §13 Table 3).
# core_step() is the canonical single-scale pipeline; the twin tests in
# test_twins.py check its TC-07/09/11/12/17 properties, and test_production.py
# holds the production packages to it (SSOT-P*, SSOT-V*).
M0 = math.sqrt(2.0 / math.pi)  # m₀ = E|z| for z ~ N(0, 1); test_conflicts checks it against the registry
EPS_STAB = 1e-8


def excess(z: float, m: float = M0) -> float:
    """EQ-EXCESS-1: |z|_ex = |z| − m₀ (stimulus-free mean 0 for standard-normal z)."""
    return abs(z) - m


def prec_rel(pi_eff: float, pi_bar: float) -> float:
    """EQ-PREC-REL-1: Π_rel = Π_eff / Π̄ (normalization follows clamping; not re-clamped)."""
    return pi_eff / pi_bar


def drive(pi_rel_e: float, z_e: float, pi_rel_i: float, z_i_eff: float, m: float = M0) -> float:
    """EQ-DRIVE-1: S_inst = Πᵉ_rel·|zᵉ|_ex + Πⁱ_rel·|zⁱ_eff|_ex (signed; sign-symmetric in each z).
    Monotone in Π_rel exactly where |z| ≥ m₀ (task 55, Lean target)."""
    return pi_rel_e * excess(z_e, m) + pi_rel_i * excess(z_i_eff, m)


def standardize(eps: float, mu_ref: float, sigma_ref: float, eps_stab: float = EPS_STAB) -> float:
    """EQ-STD-1: z = (ε − μ_ref)/(σ_ref + ε_stab); the reference statistics exclude ε itself."""
    return (eps - mu_ref) / (sigma_ref + eps_stab)


def ema_alpha(dt: float, window: float) -> float:
    """EQ-EMA-2: α_EMA = 1 − exp(−dt/T_window)."""
    return -math.expm1(-(dt / window))


def ema_update(mu: float, sigma2: float, eps: float, alpha: float) -> tuple[float, float]:
    """EQ-EMA-1/2, two-step EMA: the variance residual uses the mean BEFORE ε enters it."""
    return (1.0 - alpha) * mu + alpha * eps, (1.0 - alpha) * sigma2 + alpha * (eps - mu) ** 2


def theta_eff(theta: float, gamma_ne: float = 0.0, g_ne: float = 1.0, kappa_up: float = 0.0,
              lower_ignited: bool = False, r: float = 0.0, beta_5ht: float = 0.0, u: float = 0.0) -> float:
    """EQ-THEFF-1 (read-out only, never written back to θ):
    θ_eff = θ·(1 + γ_NE·g_NE)·(1 − κ_up·1[lower ignited]) + r(t) + β_5HT − u(t), g_NE after EQ-NE-1."""
    gate = 1.0 - kappa_up * (1.0 if lower_ignited else 0.0)
    return theta * ne_factor(gamma_ne, g_ne) * gate + r + beta_5ht - u


def reset(S: float, B: int, rho: float) -> float:
    """EQ-RESET-1: S ← ρ_retain·S on an ignition, exactly once."""
    return rho * S if B else S


def refractory_step(r: float, B: int, dt: float, tau_ref: float, delta_ref: float) -> float:
    """EQ-REF-1: r(t+1) = r(t)·exp(−dt/τ_ref) + δ_ref·B(t) (no-op when δ_ref = 0 and r = 0)."""
    return r * math.exp(-(dt / tau_ref)) + delta_ref * B


def step_rule(dt: float, *taus: float) -> bool:
    """EQ-STEP-1: dt ≤ min(τ_S, τ_θ, τ_Π[, τ_res])/10."""
    return dt <= min(taus) / 10.0


def sigmoid(x: float) -> float:
    return ignition_prob(1.0, x, 0.0)


# Canonical defaults of the minimal core (SSOT §4; CFG-CORE). Fitted quantities
# carry placeholders chosen only so the loop runs; they are not adopted values.
CORE_DEFAULTS = dict(
    dt=0.01, tau_S=0.3, theta0=0.35, tau_theta=20.0, theta_floor=THETA_FLOOR,
    eta_theta=0.0, delta_reset=0.0, rho_retain=0.3, gamma_sig=5.0, r_max=1.0,
    c1=0.0, c2=0.0, v1=0.0, v2=0.0, g_ach=1.0, g_ne=1.0, gamma_ne=0.0,
    beta_da=0.0, beta_5ht=0.0, kappa_up=0.0, u_urg=0.0,
    tau_ref=0.3, delta_ref=0.0, pi_min=0.1, pi_max=10.0, pi_bar_e=1.0, pi_bar_i=1.0,
    eta_pred_e=0.0, eta_pred_i=0.0, T_e=5.0, T_i=10.0, eps_stab=EPS_STAB,
)


def core_state(p: dict | None = None) -> dict:
    """Initial state: μ(0) = 0, Σ(0) = 1 (EQ-EMA-1/2), θ = θ₀, S = 0, empty reference windows."""
    p = {**CORE_DEFAULTS, **(p or {})}
    return dict(S=0.0, theta=p["theta0"], r=0.0, B_prev=0, xhat_e=0.0, xhat_i=0.0,
                mu_e=0.0, s2_e=1.0, mu_i=0.0, s2_i=1.0, ref_e=[], ref_i=[])


def _ref_stats(window: list) -> tuple[float, float]:
    """Sliding-window reference statistics (Math Spec Eq. 6-7). A separate estimator from the
    precision EMA, as EQ-STD-1 requires. Before two samples exist the reference is N(0, 1)."""
    if len(window) < 2:
        return 0.0, 1.0
    mu = sum(window) / len(window)
    return mu, math.sqrt(sum((w - mu) ** 2 for w in window) / len(window))


def core_step(state: dict, x_e: float, x_i: float, p: dict | None = None, u: float = 1.0) -> tuple[dict, dict]:
    """One timestep of the canonical pipeline, SSOT §13 (Math Spec v1.2 draft §13 Table 3).
    `u` is the uniform draw for the hazard sampler (u = 1 never ignites). Returns (state', log)."""
    p = {**CORE_DEFAULTS, **(p or {})}
    s = {**state, "ref_e": list(state["ref_e"]), "ref_i": list(state["ref_i"])}
    eps_e, eps_i = x_e - s["xhat_e"], x_i - s["xhat_i"]                                   # 2
    (me, se), (mi, si) = _ref_stats(s["ref_e"]), _ref_stats(s["ref_i"])                   # 3
    z_e, z_i = standardize(eps_e, me, se, p["eps_stab"]), standardize(eps_i, mi, si, p["eps_stab"])
    pi_e = prec_clamp(p["pi_min"], p["pi_max"], 1.0 / (s["s2_e"] + p["eps_stab"]))        # 4
    pi_i = prec_clamp(p["pi_min"], p["pi_max"], 1.0 / (s["s2_i"] + p["eps_stab"]))
    g_ne = ne_clamp(p["gamma_ne"], p["g_ne"]) if p["gamma_ne"] else p["g_ne"]             # 5
    pi_e_eff = prec_clamp(p["pi_min"], p["pi_max"], p["g_ach"] * pi_e)
    pi_i_eff = prec_clamp(p["pi_min"], p["pi_max"], g_ne * pi_i)
    z_i_eff = z_i + p["beta_da"]
    s_inst = drive(prec_rel(pi_e_eff, p["pi_bar_e"]), z_e, prec_rel(pi_i_eff, p["pi_bar_i"]), z_i_eff)  # 6
    th_eff = theta_eff(s["theta"], p["gamma_ne"], g_ne, p["kappa_up"], False, s["r"], p["beta_5ht"], p["u_urg"])  # 7
    b_prop = ignition_prob(p["gamma_sig"], s["S"], th_eff)                                # 8 (existing S)
    B = int(u < hazard_prob(p["r_max"], b_prop, p["dt"]))                                 # 9
    C = p["c1"] * s["S"] + p["c2"] * s["B_prev"]                                          # 10
    V = p["v1"] * abs(z_e) + p["v2"] * abs(z_i_eff)
    s["theta"] = threshold_step(s["theta"], p["theta0"], p["eta_theta"], C, V, p["delta_reset"], B,
                                p["dt"], p["tau_theta"], p["theta_floor"])
    s["r"] = refractory_step(s["r"], B, p["dt"], p["tau_ref"], p["delta_ref"])          # 11
    s["S"] = reset(s["S"], B, p["rho_retain"])                                            # 12
    s["S"] = leak_step(s["S"], s_inst, leak_gain(p["dt"], p["tau_S"]))                    # 13
    a_e, a_i = ema_alpha(p["dt"], p["T_e"]), ema_alpha(p["dt"], p["T_i"])                 # 14
    s["mu_e"], s["s2_e"] = ema_update(s["mu_e"], s["s2_e"], eps_e, a_e)
    s["mu_i"], s["s2_i"] = ema_update(s["mu_i"], s["s2_i"], eps_i, a_i)
    for key, eps, T in (("ref_e", eps_e, p["T_e"]), ("ref_i", eps_i, p["T_i"])):
        s[key].append(eps)
        del s[key][:-max(2, round(T / p["dt"]))]
    s["xhat_e"] += p["eta_pred_e"] * pi_e * eps_e
    s["xhat_i"] += p["eta_pred_i"] * pi_i * eps_i
    s["B_prev"] = B                                                                       # 15
    log = dict(eps_e=eps_e, eps_i=eps_i, z_e=z_e, z_i=z_i, z_i_eff=z_i_eff, pi_e=pi_e, pi_i=pi_i,
               pi_e_eff=pi_e_eff, pi_i_eff=pi_i_eff, g_ne=g_ne, S_inst=s_inst, theta_eff=th_eff,
               B_prop=b_prop, B=B, C=C, V=V, S_decided=state["S"], theta_decided=state["theta"])
    return s, log


def operating_point(gamma_sig: float, theta0: float, r_max: float) -> dict:
    """R1 / TC-14 report: γ_sig·θ₀, the soft floor σ(−γ_sig·θ₀) and the stimulus-free hazard
    r_max·σ(−γ_sig·θ₀) (s⁻¹, before noise in S; EQ-FLOOR-1)."""
    floor = sigmoid(-gamma_sig * theta0)
    return {"gamma_sig_theta0": gamma_sig * theta0, "propensity_floor": floor, "baseline_rate": r_max * floor}


# ------------------------------------------------- task 55 twins (Apgi/Core.lean) ----
def drive_term(p: float, z: float, m: float = M0) -> float:
    """EQ-DRIVE-1, one channel: Π_rel·|z|_ex. Lean: Apgi.driveTerm_monotone_iff (monotone in Π_rel iff |z| ≥ m₀)."""
    return p * excess(z, m)


def mean_abs_std_normal() -> float:
    """EQ-EXCESS-1: E|z| for z ~ N(0, 1) by quadrature, (∫|x|e^{−x²/2}dx)/√(2π). Lean: Apgi.meanAbsStdNormal_eq."""
    import mpmath as mp  # pinned in requirements.txt; no SciPy dependency in the base job

    val = mp.quad(lambda x: abs(x) * mp.exp(-x * x / 2), [-mp.inf, 0, mp.inf])
    return float(val / mp.sqrt(2 * mp.pi))


def cusp_fold(a: float) -> float:
    """EQ-CUSP-2: fold distance 2(−a/3)^{3/2} in θ̃ units (a < 0). Lean: Apgi.cusp_discriminant_iff_fold."""
    c = -a / 3.0
    return 2.0 * c * math.sqrt(c)


def cusp_hysteresis_width(a: float, u0: float) -> float:
    """EQ-CUSP-2: hysteresis width 4u₀(−a/3)^{3/2} in AU."""
    return 2.0 * u0 * cusp_fold(a)


# ------------------------------------- task 54: remaining SSOT equations (spec 0.5.0) ----
def prediction_error(x: float, xhat: float) -> float:
    """EQ-ERR-1: ε = x − x̂ (signed)."""
    return x - xhat


def prediction_update(xhat: float, eta_pred: float, pi: float, eps: float) -> float:
    """EQ-PRED-1: x̂ ← x̂ + η_pred·Π·ε (stable while η_pred·Π_max < 2)."""
    return xhat + eta_pred * pi * eps


def prec_ach(g_ach: float, pi_e: float, lo: float = 0.1, hi: float = 10.0) -> float:
    """EQ-PREC-ACH-1: Πᵉ_eff = clip(g_ACh·Πᵉ, Π_min, Π_max)."""
    return prec_clamp(lo, hi, g_ach * pi_e)


def somatic_marker(gamma_v: float, bold: float, gamma_a: float, scr: float) -> float:
    """EQ-SM-1: M̂ = clip(γ_V·BOLD_vmPFC + γ_A^M·SCR, −2, +2)."""
    return max(-2.0, min(2.0, gamma_v * bold + gamma_a * scr))


def da_bias(z_i: float, beta_da: float) -> float:
    """EQ-DA-1: zⁱ_eff = zⁱ + β_DA."""
    return z_i + beta_da


def allostatic_rate(theta, theta0, tau_theta, eta, C, V, delta=0.0, impulses=0.0, xi=0.0):
    """EQ-ALLO-C1: dθ/dt = −(θ − θ₀)/τ_θ + η_θ[C − V] + δ_reset·Σδ_D + ξ_θ (impulse mass given per unit time)."""
    return -(theta - theta0) / tau_theta + eta * (C - V) + delta * impulses + xi


def allostatic_rate_reduced(theta, theta0, tau_theta, gamma_m, s_met, gamma_a, arousal, xi=0.0):
    """EQ-ALLO-R1: dθ/dt = −(θ − θ₀)/τ_θ + γ_M^θ[1 − S_met] + γ_A^θ·A + ξ_θ."""
    return -(theta - theta0) / tau_theta + gamma_m * (1.0 - s_met) + gamma_a * arousal + xi


def anticipated_cost(cost_path, t_index: int, horizon_steps: int) -> float:
    """EQ-ANT-1 (deterministic path): Ĉ(t) = C(t + T_ant); T_ant = 0 recovers EQ-ALLO-1."""
    return cost_path[min(len(cost_path) - 1, t_index + horizon_steps)]


def cost(S: float, B_prev: int, c1: float, c2: float, c3: float = 0.0, action: float = 0.0) -> float:
    """EQ-COST-1: C = c₁·S + c₂·B(t−1) [+ c₃‖a‖]."""
    return c1 * S + c2 * B_prev + c3 * action


def info_value(z_e: float, z_i_eff: float, v1: float, v2: float) -> float:
    """EQ-VAL-1: V = v₁|zᵉ| + v₂|zⁱ_eff|."""
    return v1 * abs(z_e) + v2 * abs(z_i_eff)


def urgency(t_ep: float, u_max: float, tau_u: float) -> float:
    """EQ-URG-1: u(t) = u_max(1 − exp(−t_ep/τ_u)) ≥ 0; u_max = 0 recovers the core."""
    return u_max * -math.expm1(-(t_ep / tau_u))


def p_hit(r_max: float, props, dt: float) -> float:
    """EQ-OBS-1: P(hit) = 1 − exp(−r_max·Σ_W B_t·dt)."""
    return -math.expm1(-(r_max * sum(props) * dt))


def p_report(phit: float, g: float, lapse: float) -> float:
    """EQ-OBS-2: P(report) = g + (1 − g − λ_lapse)·P(hit)."""
    return g + (1.0 - g - lapse) * phit


def cusp_ignites(S: float, theta_eff: float, a: float, u0: float) -> bool:
    """EQ-CUSP-2 ignition fold: S > θ_eff + 2u₀(−a/3)^{3/2}."""
    return S > theta_eff + u0 * cusp_fold(a)


def cusp_extinguishes(S: float, theta_eff: float, a: float, u0: float) -> bool:
    """EQ-CUSP-2 extinction fold: S < θ_eff − 2u₀(−a/3)^{3/2}."""
    return S < theta_eff - u0 * cusp_fold(a)


def norm_gains(pe: float, pi: float) -> tuple[float, float]:
    """EQ-NORM-1: Πᵉ_norm = 2Πᵉ/(Πᵉ + Πⁱ), Πⁱ_norm = 2Πⁱ/(Πᵉ + Πⁱ) (budget 2; equal gains → core)."""
    return 2.0 * pe / (pe + pi), 2.0 * pi / (pe + pi)


def geo_timescale(level: int, tau0: float = 0.05, k: float = 133.0) -> float:
    """EQ-GEO-1: τ_ℓ = τ₀·k^ℓ (analytic sampling points only, R9)."""
    return tau0 * k ** level


def gradient_timescale(h: float, tau_min: float, tau_max: float) -> float:
    """EQ-GRAD-1: log τ(h) = log τ_min + h·log(τ_max/τ_min), h ∈ [0, 1]."""
    return math.exp(math.log(tau_min) + h * math.log(tau_max / tau_min))


def psi_small(z: float, gamma_psi: float) -> float:
    """EQ-PSI-SMALL-1: ψ(z) = tanh(γ_ψ·z)."""
    return math.tanh(gamma_psi * z)


def prec_ode_rate(pi_l, eps_l, pi_up, z_down, tau_pi, alpha_pi, c_down, c_up, gamma_psi):
    """EQ-PREC-ODE-1: dΠ_ℓ/dt = −Π_ℓ/τ_Π + α_Π|ε_ℓ| + C_down(Π_{ℓ+1} − Π_ℓ) + C_up·ψ(z_{ℓ−1})."""
    return -pi_l / tau_pi + alpha_pi * abs(eps_l) + c_down * (pi_up - pi_l) + c_up * psi_small(z_down, gamma_psi)


def loop_gain(c_down: float, c_up: float, tau_pi: float, gamma_psi: float) -> float:
    """EQ-LOOP-1: (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² (design heuristic: < 1)."""
    return (c_down * tau_pi) * (c_up * tau_pi) * gamma_psi ** 2


def psi_excess(z: float, a_plus, a_minus, g_plus, g_minus, m_psi: float) -> float:
    """|Ψ(z)|_ex = |Ψ(z)| − m_Ψ (EQ-MS-1)."""
    return abs(psi(a_plus, a_minus, g_plus, g_minus, z)) - m_psi


def ms_drive(pi_rel: float, psi_ex: float, gamma: float = 1.0) -> float:
    """EQ-MS-1: S_inst,ℓ = Π_rel,ℓ·|Ψ(z_ℓ)|_ex·Γ_ℓ."""
    return pi_rel * psi_ex * gamma


def ms_global(weights, drives, w_res: float = 0.0, s_res: float = 0.0) -> float:
    """EQ-MS-2: S_global = Σ w_ℓ S_inst,ℓ + w_res S_res, weights ≥ 0 summing to 1."""
    tot = sum(weights) + w_res
    if any(w < 0 for w in weights) or w_res < 0 or abs(tot - 1.0) > 1e-9:
        raise ValueError("EQ-MS-2 weights must be non-negative and sum to 1")
    return sum(w * d for w, d in zip(weights, drives)) + w_res * s_res


def ms_integrated(weights, prec, gammas, G, w_res: float = 0.0, s_res: float = 0.0) -> float:
    """EQ-MS-3 (integrate-then-weight): S = Σ w_ℓ·Π_ℓ^eff·Γ_ℓ·G_ℓ + w_res·S_res."""
    return sum(w * p * g * gl for w, p, g, gl in zip(weights, prec, gammas, G)) + w_res * s_res


def ms_threshold_target(theta0_l: float, kappa_down: float, pi_up: float, pi_max: float, phase_up: float) -> float:
    """EQ-MS-4: θ₀,ℓ(t) = θ₀,ℓ[1 + κ_down(Π_{ℓ+1}/Π_max)cos φ̄_{ℓ+1}], bounded in [0.5, 1.5]·θ₀,ℓ."""
    f = 1.0 + kappa_down * (pi_up / pi_max) * math.cos(phase_up)
    return theta0_l * max(0.5, min(1.5, f))


def kuramoto_order(phases) -> tuple[float, float]:
    """EQ-KUR-1: R = |Σ exp(iφ)|/N and Γ = R²."""
    n = len(phases)
    re = sum(math.cos(p) for p in phases) / n
    im = sum(math.sin(p) for p in phases) / n
    R = math.hypot(re, im)
    return R, R * R


def kuramoto_rate(i: int, phases, omega: float, K: float, xi: float = 0.0, inter=()) -> float:
    """EQ-KUR-2: dφ_i/dt = ω_i + (K/N)Σ_j sin(φ_j − φ_i) + Σ_m K_ℓm R_m sin(φ̄_m − φ_i) + ξ.
    `inter` is a sequence of (K_lm, R_m, mean_phase_m)."""
    n = len(phases)
    own = (K / n) * sum(math.sin(pj - phases[i]) for pj in phases)
    cross = sum(k * r * math.sin(ph - phases[i]) for k, r, ph in inter)
    return omega + own + cross + xi


def reservoir_step(x, W_res, W_in, u, xi=None, f=np.tanh):
    """EQ-RES-1: x(t+1) = f(W_res x(t) + W_in u(t) + ξ_t)."""
    pre = np.asarray(W_res) @ np.asarray(x) + np.asarray(W_in) @ np.atleast_1d(u)
    if xi is not None:
        pre = pre + xi
    return f(pre)


def reservoir_readout(W_out, x) -> float:
    """EQ-RES-2: S_res = [W_outᵀ x]₊ (rectified, never subtracts from S)."""
    return max(0.0, float(np.dot(W_out, x)))


def energy_per_bit(E_event: float, N_b: float) -> float:
    """EQ-BR-1: e_bit = E_event/N_b, J/bit."""
    return E_event / N_b


def kappa_atp_per_bit(e_bit: float, dG_atp: float = 8.3e-20) -> float:
    """EQ-BR-2: κ = e_bit/|ΔG_ATP|, ATP molecules per bit (never mol/bit)."""
    return e_bit / abs(dG_atp)


def erasure_ratio(E_event: float, N_erase: float, T: float = 310.0) -> float:
    """EQ-BR-3: R_L = E_event/(N_erase·k_B·T·ln 2), a consistency check only."""
    return E_event / (N_erase * landauer(T))
