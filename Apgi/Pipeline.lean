module

public import Apgi.Coverage
public import Mathlib.MeasureTheory.Measure.Lebesgue.Basic

/-!
# The canonical 15-step pipeline as one step function (SSOT §8, EQ-PIPE-1)

`coreStep` (Apgi/Core.lean) covers steps 10–13 and takes S_inst, C and V as inputs.
This module composes steps 2–15 into one function, `pipeStep`, with the same order as
SSOT §8 and `apgi_ref.core_step`:

 2 errors against the previous predictions · 3 standardization against reference
 statistics that exclude ε_t · 4 precision from the separate variance estimate, clamped ·
 5 NE clamp, Πᵉ_eff, Πⁱ_eff (somatic marker), β_DA · 6 S_inst · 7 θ_eff (read-out) ·
 8 B_t from the existing S_t · 9 hazard sampling with a uniform draw · 10 C, V, threshold
 step · 11 r · 12 retention · 13 leak · 14 statistics and predictions · 15 B_prev.

The reference estimator is abstract (`RefEstimator`): every theorem holds for any
estimator that is a function of past errors, including the sliding window of
`apgi_ref.core_step`.

What is proved here:
* bounded-state invariants along every trajectory, for every input sequence and every
  sequence of draws (`traj_inv`, `traj_prec_mem_Icc`, `traj_ne_bound`);
* the causal one-step lag: the ignition decision at t does not depend on the inputs at t
  (`pipeStep_decision_input_independent`);
* estimator separation and ordering (TC-17);
* read-out non-interference for the whole step (TC-11);
* the hazard sampler realizes EQ-HAZARD-1 under a uniform draw (`sampler_volume`);
* the rejected 17-step orders (SSOT §8, "not adopted") are not equivalent to the canonical
  order: ignition after accumulation makes the decision depend on the current drive, and
  statistics before standardization shrinks z by (1 − α).

What is NOT proved: anything about real inputs or brains; the upper bound on S is
conditional on a bound on S_inst (`traj_S_le`), because z is unbounded for unbounded input.
-/

@[expose] public section

namespace Apgi

open MeasureTheory

/-! ## State, parameters, log -/

/-- An abstract reference-statistics estimator for standardization (EQ-STD-1). `mean` and
    `sd` read the statistics; `push` adds one error after it has been used. -/
structure RefEstimator (W : Type*) where
  mean : W → ℝ
  sd : W → ℝ
  push : W → ℝ → W

/-- Per-channel state: prediction x̂, EMA mean μ and variance Σ (EQ-EMA-1/2), reference state. -/
structure ChannelState (W : Type*) where
  xhat : ℝ
  mu : ℝ
  s2 : ℝ
  ref : W

/-- Full pipeline state: both channels, the slow core (S, θ, r) and B_prev. -/
structure PipeState (W : Type*) where
  e : ChannelState W
  i : ChannelState W
  core : CoreState
  Bprev : ℝ

/-- Parameters of the minimal core (CFG-CORE, somatic marker optional). -/
structure PipeParams where
  core : CoreParams
  readout : Readout
  epsStab : ℝ
  piMin : ℝ
  piMax : ℝ
  gACh : ℝ
  βSM : ℝ
  marker : ℝ
  βDA : ℝ
  pibarE : ℝ
  pibarI : ℝ
  m₀ : ℝ
  γsig : ℝ
  rmax : ℝ
  c1 : ℝ
  c2 : ℝ
  v1 : ℝ
  v2 : ℝ
  αe : ℝ
  αi : ℝ
  ηe : ℝ
  ηi : ℝ

/-- Everything step 15 logs. -/
structure PipeLog where
  εe : ℝ
  εi : ℝ
  ze : ℝ
  zi : ℝ
  ziEff : ℝ
  prE : ℝ
  prI : ℝ
  prEeff : ℝ
  prIeff : ℝ
  gNE : ℝ
  Sinst : ℝ
  θeff : ℝ
  Bprop : ℝ
  B : ℝ
  C : ℝ
  V : ℝ

/-! ## The step function -/

/-- Steps 2–9: everything computed before the state update. -/
noncomputable def pipeLog {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : PipeLog :=
  let εe := predError xe s.e.xhat
  let εi := predError xi s.i.xhat
  let ze := standardize εe (R.mean s.e.ref) (R.sd s.e.ref) p.epsStab
  let zi := standardize εi (R.mean s.i.ref) (R.sd s.i.ref) p.epsStab
  let prE := precClamp p.piMin p.piMax (1 / (s.e.s2 + p.epsStab))
  let prI := precClamp p.piMin p.piMax (1 / (s.i.s2 + p.epsStab))
  let g := neClamp p.readout.γNE p.readout.gNE
  let prEeff := precClamp p.piMin p.piMax (p.gACh * prE)
  let prIeff := precClamp p.piMin p.piMax (precEff g prI p.βSM p.marker)
  let ziEff := zi + p.βDA
  let Sinst := drive p.m₀ (precRel prEeff p.pibarE) ze (precRel prIeff p.pibarI) ziEff
  let θe := thetaEff p.readout s.core.θ s.core.r
  let Bp := ignitionProb p.γsig s.core.S θe
  let B : ℝ := if u < hazardProb p.rmax Bp p.core.dt then 1 else 0
  { εe := εe, εi := εi, ze := ze, zi := zi, ziEff := ziEff, prE := prE, prI := prI,
    prEeff := prEeff, prIeff := prIeff, gNE := g, Sinst := Sinst, θeff := θe, Bprop := Bp,
    B := B, C := costC p.c1 p.c2 0 s.core.S s.Bprev 0, V := valueV p.v1 p.v2 ze ziEff }

/-- Step 14 for one channel: EMA statistics with the pre-update mean, reference push,
    prediction update x̂ ← x̂ + η·Π·ε (EQ-PRED-1). -/
noncomputable def channelUpdate {W : Type*} (R : RefEstimator W) (c : ChannelState W)
    (ε α η pr : ℝ) : ChannelState W where
  xhat := c.xhat + η * pr * ε
  mu := emaMean c.mu ε α
  s2 := emaVar c.s2 c.mu ε α
  ref := R.push c.ref ε

/-- One full timestep (steps 2–15). Steps 10–13 are `coreStep`. -/
noncomputable def pipeStep {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : PipeState W :=
  let l := pipeLog R p s xe xi u
  { e := channelUpdate R s.e l.εe p.αe p.ηe l.prE
    i := channelUpdate R s.i l.εi p.αi p.ηi l.prI
    core := coreStep p.core s.core l.Sinst l.C l.V l.B
    Bprev := l.B }

/-- A trajectory under input sequences xe, xi and uniform draws u. -/
noncomputable def traj {W : Type*} (R : RefEstimator W) (p : PipeParams) (s₀ : PipeState W)
    (xe xi u : ℕ → ℝ) : ℕ → PipeState W
  | 0 => s₀
  | n + 1 => pipeStep R p (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)

/-- The log at step n of a trajectory. -/
noncomputable def trajLog {W : Type*} (R : RefEstimator W) (p : PipeParams) (s₀ : PipeState W)
    (xe xi u : ℕ → ℝ) (n : ℕ) : PipeLog :=
  pipeLog R p (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)

/-! ## Admissible parameters -/

/-- The registry-level hypotheses the invariants need. Every CFG-CORE default satisfies
    them (`test_pipeline_lean.py::test_cfg_core_is_admissible`). -/
structure PipeAdmissible (p : PipeParams) : Prop where
  piMin_nonneg : 0 ≤ p.piMin
  piMin_le : p.piMin ≤ p.piMax
  pibarE_pos : 0 < p.pibarE
  pibarI_pos : 0 < p.pibarI
  m₀_nonneg : 0 ≤ p.m₀
  αe_mem : p.αe ∈ Set.Icc (0 : ℝ) 1
  αi_mem : p.αi ∈ Set.Icc (0 : ℝ) 1
  ρ_mem : p.core.ρ ∈ Set.Icc (0 : ℝ) 1
  lam_mem : p.core.lam ∈ Set.Icc (0 : ℝ) 1
  δref_nonneg : 0 ≤ p.core.δref

/-- The unconditional lower bound on S_inst: −m₀·(Π_max/Π̄ᵉ + Π_max/Π̄ⁱ). -/
noncomputable def driveLower (p : PipeParams) : ℝ :=
  -(p.m₀ * (p.piMax / p.pibarE + p.piMax / p.pibarI))

/-- The bounded-state invariant. -/
structure PipeInv {W : Type*} (L : ℝ) (s : PipeState W) : Prop where
  s2e : 0 ≤ s.e.s2
  s2i : 0 ≤ s.i.s2
  θ : θ_floor ≤ s.core.θ
  r : 0 ≤ s.core.r
  Bprev : s.Bprev = 0 ∨ s.Bprev = 1
  S : L ≤ s.core.S

/-! ## Single-step facts -/

/-- The sampled event is 0 or 1. -/
theorem pipeLog_B_cases {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : (pipeLog R p s xe xi u).B = 0 ∨ (pipeLog R p s xe xi u).B = 1 := by
  simp only [pipeLog]
  split_ifs <;> simp

/-- EQ-HAZARD-1 / step 9: B(t) = 1 exactly when the draw falls below the hazard. -/
theorem pipeLog_B_eq_one_iff {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : (pipeLog R p s xe xi u).B = 1 ↔
      u < hazardProb p.rmax (ignitionProb p.γsig s.core.S (thetaEff p.readout s.core.θ s.core.r))
        p.core.dt := by
  simp only [pipeLog]
  split_ifs with h <;> simp [h]

/-- TC-10: every precision the step uses lies in [Π_min, Π_max]. -/
theorem pipeLog_prec_mem_Icc {W : Type*} (R : RefEstimator W) {p : PipeParams}
    (h : p.piMin ≤ p.piMax) (s : PipeState W) (xe xi u : ℝ) :
    (pipeLog R p s xe xi u).prE ∈ Set.Icc p.piMin p.piMax ∧
      (pipeLog R p s xe xi u).prI ∈ Set.Icc p.piMin p.piMax ∧
      (pipeLog R p s xe xi u).prEeff ∈ Set.Icc p.piMin p.piMax ∧
      (pipeLog R p s xe xi u).prIeff ∈ Set.Icc p.piMin p.piMax :=
  ⟨precClamp_mem_Icc h _, precClamp_mem_Icc h _, precClamp_mem_Icc h _, precClamp_mem_Icc h _⟩

/-- TC-10: |γ_NE|·g_NE ≤ 0.5 at every step, for either sign of γ_NE. -/
theorem pipeLog_ne_bound {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : |p.readout.γNE| * (pipeLog R p s xe xi u).gNE ≤ ne_bound :=
  neClamp_bound _ _

/-- One channel of the drive is at least −m₀·Π_rel when Π_rel ≥ 0. -/
theorem driveTerm_ge {m₀ q z : ℝ} (hq : 0 ≤ q) : -(m₀ * q) ≤ driveTerm m₀ q z := by
  unfold driveTerm excessMag
  nlinarith [abs_nonneg z]

/-- Unconditional lower bound: S_inst ≥ −m₀·(Π_max/Π̄ᵉ + Π_max/Π̄ⁱ) for every input. -/
theorem pipeLog_Sinst_ge {W : Type*} (R : RefEstimator W) {p : PipeParams} (hp : PipeAdmissible p)
    (s : PipeState W) (xe xi u : ℝ) : driveLower p ≤ (pipeLog R p s xe xi u).Sinst := by
  obtain ⟨_, _, hE, hI⟩ := pipeLog_prec_mem_Icc R hp.piMin_le s xe xi u
  set l := pipeLog R p s xe xi u
  have hEr : 0 ≤ precRel l.prEeff p.pibarE :=
    div_nonneg (le_trans hp.piMin_nonneg hE.1) hp.pibarE_pos.le
  have hIr : 0 ≤ precRel l.prIeff p.pibarI :=
    div_nonneg (le_trans hp.piMin_nonneg hI.1) hp.pibarI_pos.le
  have hEle : precRel l.prEeff p.pibarE ≤ p.piMax / p.pibarE :=
    div_le_div_of_nonneg_right hE.2 hp.pibarE_pos.le
  have hIle : precRel l.prIeff p.pibarI ≤ p.piMax / p.pibarI :=
    div_le_div_of_nonneg_right hI.2 hp.pibarI_pos.le
  have h1 := driveTerm_ge (m₀ := p.m₀) (z := l.ze) hEr
  have h2 := driveTerm_ge (m₀ := p.m₀) (z := l.ziEff) hIr
  have hS : l.Sinst = drive p.m₀ (precRel l.prEeff p.pibarE) l.ze (precRel l.prIeff p.pibarI)
      l.ziEff := rfl
  rw [hS, drive, driveLower]
  have hm := hp.m₀_nonneg
  nlinarith [mul_le_mul_of_nonneg_left hEle hm, mul_le_mul_of_nonneg_left hIle hm]

/-- The lower bound is nonpositive. -/
theorem driveLower_nonpos {p : PipeParams} (hp : PipeAdmissible p) : driveLower p ≤ 0 := by
  have hmax : 0 ≤ p.piMax := le_trans hp.piMin_nonneg hp.piMin_le
  have : 0 ≤ p.piMax / p.pibarE + p.piMax / p.pibarI :=
    add_nonneg (div_nonneg hmax hp.pibarE_pos.le) (div_nonneg hmax hp.pibarI_pos.le)
  unfold driveLower
  nlinarith [mul_nonneg hp.m₀_nonneg this]

/-- Retention then leak keep S above any L ≤ 0 that also bounds the drive. -/
theorem retain_leak_ge {L S Sinst ρ lam B : ℝ} (hL : L ≤ 0) (hS : L ≤ S) (hu : L ≤ Sinst)
    (hρ : ρ ∈ Set.Icc (0 : ℝ) 1) (hl : lam ∈ Set.Icc (0 : ℝ) 1) :
    L ≤ leakStep (if B = 1 then ρ * S else S) Sinst lam := by
  have hS' : L ≤ (if B = 1 then ρ * S else S) := by
    split_ifs
    · nlinarith [hρ.1, hρ.2]
    · exact hS
  unfold leakStep
  nlinarith [hl.1, hl.2]

/-- The invariant is preserved by one step, for every input and every draw. -/
theorem pipeInv_step {W : Type*} (R : RefEstimator W) {p : PipeParams} (hp : PipeAdmissible p)
    {L : ℝ} (hL : L ≤ driveLower p) {s : PipeState W} (hs : PipeInv L s) (xe xi u : ℝ) :
    PipeInv L (pipeStep R p s xe xi u) := by
  have hB := pipeLog_B_cases R p s xe xi u
  have hSinst := pipeLog_Sinst_ge R hp s xe xi u
  have hL0 := le_trans hL (driveLower_nonpos hp)
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact emaVar_nonneg hs.s2e hp.αe_mem.1 hp.αe_mem.2
  · exact emaVar_nonneg hs.s2i hp.αi_mem.1 hp.αi_mem.2
  · exact thresholdStep_floor _ _ _ _ _ _ _ _ _
  · change 0 ≤ s.core.r * Real.exp (-(p.core.dt / p.core.τref)) + p.core.δref * _
    rcases hB with h | h <;> rw [h] <;>
      nlinarith [hs.r, Real.exp_pos (-(p.core.dt / p.core.τref)), hp.δref_nonneg,
        mul_nonneg hs.r (Real.exp_pos (-(p.core.dt / p.core.τref))).le]
  · exact hB
  · exact retain_leak_ge hL0 hs.S (le_trans hL hSinst) hp.ρ_mem hp.lam_mem

/-! ## Trajectory invariants -/

/-- Bounded-state invariant along every trajectory: Σ ≥ 0 in both channels, θ ≥ θ_floor,
    r ≥ 0, B_prev ∈ {0, 1} and S ≥ L, for every input sequence and every draw sequence. -/
theorem traj_inv {W : Type*} (R : RefEstimator W) {p : PipeParams} (hp : PipeAdmissible p)
    {L : ℝ} (hL : L ≤ driveLower p) {s₀ : PipeState W} (h₀ : PipeInv L s₀) (xe xi u : ℕ → ℝ) :
    ∀ n, PipeInv L (traj R p s₀ xe xi u n)
  | 0 => h₀
  | n + 1 => pipeInv_step R hp hL (traj_inv R hp hL h₀ xe xi u n) (xe n) (xi n) (u n)

/-- TC-10 along every trajectory: all four precisions stay in [Π_min, Π_max]. -/
theorem traj_prec_mem_Icc {W : Type*} (R : RefEstimator W) {p : PipeParams}
    (h : p.piMin ≤ p.piMax) (s₀ : PipeState W) (xe xi u : ℕ → ℝ) (n : ℕ) :
    (trajLog R p s₀ xe xi u n).prEeff ∈ Set.Icc p.piMin p.piMax ∧
      (trajLog R p s₀ xe xi u n).prIeff ∈ Set.Icc p.piMin p.piMax :=
  let h4 := pipeLog_prec_mem_Icc R h (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)
  ⟨h4.2.2.1, h4.2.2.2⟩

/-- TC-10 along every trajectory: |γ_NE|·g_NE ≤ 0.5 at every step. -/
theorem traj_ne_bound {W : Type*} (R : RefEstimator W) (p : PipeParams) (s₀ : PipeState W)
    (xe xi u : ℕ → ℝ) (n : ℕ) : |p.readout.γNE| * (trajLog R p s₀ xe xi u n).gNE ≤ ne_bound :=
  pipeLog_ne_bound R p _ _ _ _

/-- Conditional upper bound (explicit assumption): if every drive along the trajectory is at
    most U, with 0 ≤ U and S₀ ≤ U, then S stays at most U. -/
theorem traj_S_le {W : Type*} (R : RefEstimator W) {p : PipeParams} (hp : PipeAdmissible p)
    {U : ℝ} (hU : 0 ≤ U) {s₀ : PipeState W} (h₀ : s₀.core.S ≤ U) (xe xi u : ℕ → ℝ)
    (hdrive : ∀ n, (trajLog R p s₀ xe xi u n).Sinst ≤ U) :
    ∀ n, (traj R p s₀ xe xi u n).core.S ≤ U
  | 0 => h₀
  | n + 1 => by
    have ih := traj_S_le R hp hU h₀ xe xi u hdrive n
    have hd := hdrive n
    change leakStep (if (trajLog R p s₀ xe xi u n).B = 1 then
        p.core.ρ * (traj R p s₀ xe xi u n).core.S else (traj R p s₀ xe xi u n).core.S)
        (trajLog R p s₀ xe xi u n).Sinst p.core.lam ≤ U
    have hS' : (if (trajLog R p s₀ xe xi u n).B = 1 then
        p.core.ρ * (traj R p s₀ xe xi u n).core.S else (traj R p s₀ xe xi u n).core.S) ≤ U := by
      split_ifs
      · rcases le_total 0 (traj R p s₀ xe xi u n).core.S with h | h
        · nlinarith [hp.ρ_mem.1, hp.ρ_mem.2]
        · nlinarith [hp.ρ_mem.1, hp.ρ_mem.2]
      · exact ih
    unfold leakStep
    nlinarith [hp.lam_mem.1, hp.lam_mem.2]

/-! ## Causal order (SSOT §8) -/

/-- The one-step lag: the propensity and the sampled event at t do not depend on the
    inputs at t (they read S_t, which integrates errors up to t − 1). -/
theorem pipeStep_decision_input_independent {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (xe₁ xi₁ xe₂ xi₂ u : ℝ) :
    (pipeLog R p s xe₁ xi₁ u).Bprop = (pipeLog R p s xe₂ xi₂ u).Bprop ∧
      (pipeLog R p s xe₁ xi₁ u).B = (pipeLog R p s xe₂ xi₂ u).B :=
  ⟨rfl, rfl⟩

/-- Steps 10–13 of `pipeStep` are exactly `coreStep`, so the exactly-once theorems of
    Apgi/Core.lean (TC-12) apply to the full step. -/
theorem pipeStep_core {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) : (pipeStep R p s xe xi u).core =
      coreStep p.core s.core (pipeLog R p s xe xi u).Sinst (pipeLog R p s xe xi u).C
        (pipeLog R p s xe xi u).V (pipeLog R p s xe xi u).B :=
  rfl

/-- TC-12 for the full step: one ignition multiplies S by ρ_retain once and adds δ_ref once. -/
theorem pipeStep_exactly_once {W : Type*} (R : RefEstimator W) (p : PipeParams) (s : PipeState W)
    (xe xi u : ℝ) (hB : (pipeLog R p s xe xi u).B = 1) :
    (pipeStep R p s xe xi u).core.S =
        leakStep (p.core.ρ * s.core.S) (pipeLog R p s xe xi u).Sinst p.core.lam ∧
      (pipeStep R p s xe xi u).core.r =
        s.core.r * Real.exp (-(p.core.dt / p.core.τref)) + p.core.δref := by
  rw [pipeStep_core, hB]
  simp [coreStep]

/-- TC-11 for the full step: the purely read-out terms of θ_eff (κ_up, the lower-level
    indicator, β_5HT, u) reach the next state only through B(t). -/
theorem pipeStep_readout_noninterference {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (m : Readout) (hγ : m.γNE = p.readout.γNE) (hg : m.gNE = p.readout.gNE) (s : PipeState W)
    (xe xi u : ℝ)
    (hB : (pipeLog R { p with readout := m } s xe xi u).B = (pipeLog R p s xe xi u).B) :
    pipeStep R { p with readout := m } s xe xi u = pipeStep R p s xe xi u := by
  have hl : ∀ q : PipeParams, pipeStep R q s xe xi u =
      { e := channelUpdate R s.e (pipeLog R q s xe xi u).εe q.αe q.ηe (pipeLog R q s xe xi u).prE
        i := channelUpdate R s.i (pipeLog R q s xe xi u).εi q.αi q.ηi (pipeLog R q s xe xi u).prI
        core := coreStep q.core s.core (pipeLog R q s xe xi u).Sinst (pipeLog R q s xe xi u).C
          (pipeLog R q s xe xi u).V (pipeLog R q s xe xi u).B
        Bprev := (pipeLog R q s xe xi u).B } := fun _ => rfl
  rw [hl, hl, hB]
  simp only [pipeLog, hγ, hg]

/-- The threshold carried to t + 1 is computed from θ_t, never from θ_eff. -/
theorem pipeStep_theta_from_state {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (xe xi u : ℝ) :
    (pipeStep R p s xe xi u).core.θ =
      thresholdStep s.core.θ p.core.θ₀ p.core.η (pipeLog R p s xe xi u).C
        (pipeLog R p s xe xi u).V p.core.δ (pipeLog R p s xe xi u).B p.core.dt p.core.τθ :=
  rfl

/-! ## Estimator ordering and separation (TC-17) -/

/-- z_t is computed against the reference state before ε_t is pushed, and ε_t is pushed
    after use: the reference statistics at t exclude ε_t. -/
theorem pipeStep_reference_excludes_current {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (xe xi u : ℝ) :
    (pipeLog R p s xe xi u).ze =
        standardize (xe - s.e.xhat) (R.mean s.e.ref) (R.sd s.e.ref) p.epsStab ∧
      (pipeStep R p s xe xi u).e.ref = R.push s.e.ref (xe - s.e.xhat) :=
  ⟨rfl, rfl⟩

/-- Standardization and precision use separate estimators: the EMA variance and mean do not
    enter z, and the reference state does not enter Π. -/
theorem pipeLog_estimators_separate {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (μ v : ℝ) (w : W) (xe xi u : ℝ) :
    (pipeLog R p { s with e := { s.e with mu := μ, s2 := v } } xe xi u).ze =
        (pipeLog R p s xe xi u).ze ∧
      (pipeLog R p { s with e := { s.e with ref := w } } xe xi u).prE =
        (pipeLog R p s xe xi u).prE :=
  ⟨rfl, rfl⟩

/-- The EMA variance residual uses the mean before ε_t enters it. -/
theorem pipeStep_variance_uses_preupdate_mean {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (xe xi u : ℝ) :
    (pipeStep R p s xe xi u).e.s2 =
      (1 - p.αe) * s.e.s2 + p.αe * ((xe - s.e.xhat) - s.e.mu) ^ 2 :=
  rfl

/-! ## The hazard sampler realizes EQ-HAZARD-1 -/

/-- For q ≤ 1, the set of uniform draws on [0, 1] that ignite has measure q. -/
theorem sampler_volume {q : ℝ} (h1 : q ≤ 1) :
    volume ({u : ℝ | u < q} ∩ Set.Icc 0 1) = ENNReal.ofReal q := by
  have hset : {u : ℝ | u < q} ∩ Set.Icc 0 1 = Set.Ico 0 q := by
    ext u
    simp only [Set.mem_inter_iff, Set.mem_ofPred_eq, Set.mem_Icc, Set.mem_Ico]
    constructor
    · rintro ⟨hu, h0', _⟩
      exact ⟨h0', hu⟩
    · rintro ⟨h0', hu⟩
      exact ⟨hu, h0', by linarith⟩
  rw [hset, Real.volume_Ico, sub_zero]

/-- Step 9 under a uniform draw: P(B(t) = 1) = 1 − exp(−r_max·B_t·dt). -/
theorem pipeLog_ignition_measure {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (s : PipeState W) (xe xi : ℝ) (hr : 0 ≤ p.rmax) (hdt : 0 ≤ p.core.dt) :
    volume ({u : ℝ | (pipeLog R p s xe xi u).B = 1} ∩ Set.Icc 0 1) =
      ENNReal.ofReal (hazardProb p.rmax
        (ignitionProb p.γsig s.core.S (thetaEff p.readout s.core.θ s.core.r)) p.core.dt) := by
  have hBp : 0 ≤ ignitionProb p.γsig s.core.S (thetaEff p.readout s.core.θ s.core.r) := by
    unfold ignitionProb
    positivity
  have hq := hazardProb_mem_Icc hr hBp hdt
  have hset : {u : ℝ | (pipeLog R p s xe xi u).B = 1} =
      {u : ℝ | u < hazardProb p.rmax
        (ignitionProb p.γsig s.core.S (thetaEff p.readout s.core.θ s.core.r)) p.core.dt} := by
    ext u
    exact pipeLog_B_eq_one_iff R p s xe xi u
  rw [hset]
  exact sampler_volume hq.2

/-! ## The rejected 17-step orders are not equivalent (SSOT §8, "not adopted") -/

/-- The logistic propensity is strictly increasing in S for γ_sig > 0. -/
theorem ignitionProb_strictMono_S {k θ : ℝ} (hk : 0 < k) :
    StrictMono (fun S => ignitionProb k S θ) := by
  intro a b hab
  simp only [ignitionProb]
  apply one_div_lt_one_div_of_lt (by positivity)
  have : -k * (b - θ) < -k * (a - θ) := by nlinarith
  linarith [Real.exp_lt_exp.2 this]

/-- Rejected order "ignition after accumulation": the decision reads the post-leak S. -/
noncomputable def decideAfterAccumulation (k lam S Sinst θe : ℝ) : ℝ :=
  ignitionProb k (leakStep S Sinst lam) θe

/-- Under the rejected order the decision depends strictly on the current drive, whereas the
    canonical decision does not depend on the inputs at t at all
    (`pipeStep_decision_input_independent`). -/
theorem decideAfterAccumulation_strictMono_drive {k lam S θe : ℝ} (hk : 0 < k) (hl : 0 < lam) :
    StrictMono (fun Sinst => decideAfterAccumulation k lam S Sinst θe) := by
  intro a b hab
  apply ignitionProb_strictMono_S hk
  change (1 - lam) * S + lam * a < (1 - lam) * S + lam * b
  nlinarith

/-- The two orders give different propensities whenever the drive moves S (λ > 0,
    S_inst ≠ S, γ_sig > 0). -/
theorem orders_differ {k lam S Sinst θe : ℝ} (hk : 0 < k) (hl : 0 < lam) (h : Sinst ≠ S) :
    ignitionProb k S θe ≠ decideAfterAccumulation k lam S Sinst θe := by
  unfold decideAfterAccumulation
  have hne : S ≠ leakStep S Sinst lam := by
    unfold leakStep
    intro he
    apply h
    have : lam * (Sinst - S) = 0 := by linarith
    rcases mul_eq_zero.1 this with h' | h'
    · exact absurd h' hl.ne'
    · linarith
  exact (ignitionProb_strictMono_S hk).injective.ne hne

/-- Rejected order "statistics before standardization", with the EMA mean as the reference:
    pushing ε_t first shrinks the standardized error by the factor (1 − α). -/
theorem standardize_after_update_shrinks (ε μ σ es α : ℝ) :
    standardize ε (emaMean μ ε α) σ es = (1 - α) * standardize ε μ σ es := by
  unfold standardize emaMean
  ring

end Apgi

end

/-! ## Axiom audit (self-enforcing). -/

/-- info: 'Apgi.pipeLog_B_cases' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_B_cases

/-- info: 'Apgi.pipeLog_B_eq_one_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_B_eq_one_iff

/-- info: 'Apgi.pipeLog_prec_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_prec_mem_Icc

/-- info: 'Apgi.pipeLog_ne_bound' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_ne_bound

/-- info: 'Apgi.driveTerm_ge' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.driveTerm_ge

/-- info: 'Apgi.pipeLog_Sinst_ge' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_Sinst_ge

/-- info: 'Apgi.driveLower_nonpos' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.driveLower_nonpos

/-- info: 'Apgi.retain_leak_ge' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.retain_leak_ge

/-- info: 'Apgi.pipeInv_step' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeInv_step

/-- info: 'Apgi.traj_inv' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_inv

/-- info: 'Apgi.traj_prec_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_prec_mem_Icc

/-- info: 'Apgi.traj_ne_bound' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_ne_bound

/-- info: 'Apgi.traj_S_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_S_le

/-- info: 'Apgi.pipeStep_decision_input_independent' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_decision_input_independent

/-- info: 'Apgi.pipeStep_core' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_core

/-- info: 'Apgi.pipeStep_exactly_once' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_exactly_once

/-- info: 'Apgi.pipeStep_readout_noninterference' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_readout_noninterference

/-- info: 'Apgi.pipeStep_theta_from_state' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_theta_from_state

/-- info: 'Apgi.pipeStep_reference_excludes_current' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_reference_excludes_current

/-- info: 'Apgi.pipeLog_estimators_separate' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_estimators_separate

/-- info: 'Apgi.pipeStep_variance_uses_preupdate_mean' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_variance_uses_preupdate_mean

/-- info: 'Apgi.sampler_volume' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.sampler_volume

/-- info: 'Apgi.pipeLog_ignition_measure' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_ignition_measure

/-- info: 'Apgi.ignitionProb_strictMono_S' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_strictMono_S

/-- info: 'Apgi.decideAfterAccumulation_strictMono_drive' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.decideAfterAccumulation_strictMono_drive

/-- info: 'Apgi.orders_differ' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.orders_differ

/-- info: 'Apgi.standardize_after_update_shrinks' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.standardize_after_update_shrinks
