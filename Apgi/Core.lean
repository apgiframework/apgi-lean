module

public import Apgi.Dynamics
public import Mathlib.Analysis.SpecialFunctions.Gaussian.GaussianIntegral
public import Mathlib.MeasureTheory.Measure.Lebesgue.Integral

/-!
# APGI minimal core: excess drive, hard-threshold limit, m₀, read-out discipline, cusp folds

Task 55 (SSOT §24 "next targets" and SSOT-R2). Each theorem is linked to an
equation ID in `specification/equations.json` and has a float64 twin in
`verification/python/test_twins.py`.

* EQ-DRIVE-1 / EQ-EXCESS-1: the centered drive Π_rel·(|z| − m₀) is monotone in
  Π_rel **exactly** when |z| ≥ m₀; below m₀ more precision makes ignition harder.
  This replaces `ignites_monotone_precision` (uncentered Π·|ε|) as the statement
  about the canonical drive.
* EQ-IGN-2 → EQ-IGN-1: the logistic propensity tends to the strict hard
  threshold as γ_sig → ∞, and equals 1/2 at S = θ_eff for every γ_sig.
* EQ-EXCESS-1: m₀ = E|z| = √(2/π) for z ~ N(0, 1).
* EQ-PIPE-1 / EQ-THEFF-1: the state update has no read-out argument, so θ_eff
  can enter the next state only through the sampled event B(t); one ignition
  applies δ_reset, δ_ref and ρ_retain exactly once.
* EQ-CUSP-2: three equilibria ⇔ |θ̃| < 2(−a/3)^{3/2}; past either fold the
  system is monostable.
-/

@[expose] public section

namespace Apgi

open Filter Topology MeasureTheory

/-! ## Excess drive (EQ-EXCESS-1, EQ-DRIVE-1) -/

/-- |z|_ex = |z| − m₀. -/
noncomputable def excessMag (m₀ z : ℝ) : ℝ := |z| - m₀

/-- One channel of EQ-DRIVE-1: Π_rel·|z|_ex. (`Π` is reserved in Mathlib, hence `p`.) -/
noncomputable def driveTerm (m₀ p z : ℝ) : ℝ := p * excessMag m₀ z

/-- EQ-DRIVE-1: S_inst = Πᵉ_rel·|zᵉ|_ex + Πⁱ_rel·|zⁱ_eff|_ex. -/
noncomputable def drive (m₀ pe ze pi zi : ℝ) : ℝ := driveTerm m₀ pe ze + driveTerm m₀ pi zi

/-- SSOT-R2: the channel drive is monotone in Π_rel if and only if |z| ≥ m₀. -/
theorem driveTerm_monotone_iff (m₀ z : ℝ) :
    Monotone (fun p => driveTerm m₀ p z) ↔ m₀ ≤ |z| := by
  constructor
  · intro h
    have h01 := h (zero_le_one : (0 : ℝ) ≤ 1)
    simp only [driveTerm, excessMag, zero_mul, one_mul] at h01
    linarith
  · intro h a b hab
    exact mul_le_mul_of_nonneg_right hab (sub_nonneg.2 h)

/-- Below m₀ the channel drive is strictly decreasing in Π_rel: raising precision
    on a smaller-than-expected error makes ignition harder. -/
theorem driveTerm_strictAnti_of_lt {m₀ z : ℝ} (h : |z| < m₀) :
    StrictAnti (fun p => driveTerm m₀ p z) := by
  intro a b hab
  exact mul_lt_mul_of_neg_right hab (sub_neg.2 h)

/-- The canonical replacement for `ignites_monotone_precision`: at fixed errors,
    raising Πᵉ_rel cannot block ignition when |zᵉ| ≥ m₀. -/
theorem ignites_drive_monotone_precision {m₀ pe₁ pe₂ ze pi zi θ : ℝ}
    (hz : m₀ ≤ |ze|) (hp : pe₁ ≤ pe₂) (hI : Ignites (drive m₀ pe₁ ze pi zi) θ) :
    Ignites (drive m₀ pe₂ ze pi zi) θ := by
  have h := (driveTerm_monotone_iff m₀ ze).2 hz hp
  unfold Ignites drive at *
  simp only at h
  linarith

/-- TC-09: equal-magnitude errors of opposite sign contribute equally. -/
theorem drive_sign_symmetric (m₀ pe ze pi zi : ℝ) :
    drive m₀ pe (-ze) pi (-zi) = drive m₀ pe ze pi zi := by
  simp [drive, driveTerm, excessMag, abs_neg]

/-- With unit gains and |z| = m₀ in both channels the drive is exactly zero
    (the excess-surprise scale is centered). -/
theorem drive_zero_at_m0 {m₀ ze zi : ℝ} (he : |ze| = m₀) (hi : |zi| = m₀) :
    drive m₀ 1 ze 1 zi = 0 := by
  simp [drive, driveTerm, excessMag, he, hi]

/-! ## m₀ = E|z| = √(2/π) for z ~ N(0, 1) (EQ-EXCESS-1) -/

/-- ∫₀^∞ x·e^{−x²/2} dx = 1. -/
theorem integral_Ioi_mul_exp_neg_half_sq :
    ∫ x in Set.Ioi (0 : ℝ), x * Real.exp (-(1 / 2) * x ^ 2) = 1 := by
  have A : ∀ x : ℝ, HasDerivAt (fun x => -Real.exp (-(1 / 2) * x ^ 2))
      (x * Real.exp (-(1 / 2) * x ^ 2)) x := by
    intro x
    have := (((hasDerivAt_pow 2 x).const_mul (-(1 / 2 : ℝ))).exp).neg
    convert this using 1
    push_cast
    ring
  have B : Tendsto (fun x : ℝ => -Real.exp (-(1 / 2) * x ^ 2)) atTop (𝓝 (-0)) :=
    (Real.tendsto_exp_atBot.comp
      ((tendsto_pow_atTop two_ne_zero).const_mul_atTop_of_neg (by norm_num))).neg
  have h := integral_Ioi_of_hasDerivAt_of_tendsto' (a := (0 : ℝ)) (fun x _ => A x)
    (integrable_mul_exp_neg_mul_sq (b := 1 / 2) (by norm_num)).integrableOn B
  rw [h]
  simp

/-- ∫ |x|·e^{−x²/2} dx = 2 over ℝ. -/
theorem integral_abs_mul_exp_neg_half_sq :
    ∫ x : ℝ, |x| * Real.exp (-(1 / 2) * x ^ 2) = 2 := by
  have h := integral_comp_abs (f := fun y : ℝ => y * Real.exp (-(1 / 2) * y ^ 2))
  simp only [sq_abs] at h
  rw [h, integral_Ioi_mul_exp_neg_half_sq]
  norm_num

/-- E|z| for a standard normal z, written against the density e^{−x²/2}/√(2π). -/
noncomputable def meanAbsStdNormal : ℝ :=
  (∫ x : ℝ, |x| * Real.exp (-(1 / 2) * x ^ 2)) / √(2 * Real.pi)

/-- EQ-EXCESS-1: m₀ = E|z| = √(2/π). -/
theorem meanAbsStdNormal_eq : meanAbsStdNormal = √(2 / Real.pi) := by
  unfold meanAbsStdNormal
  rw [integral_abs_mul_exp_neg_half_sq]
  have hπ : 0 < Real.pi := Real.pi_pos
  have h2π : 0 < √(2 * Real.pi) := Real.sqrt_pos.2 (by positivity)
  rw [← pow_left_inj₀ (by positivity) (Real.sqrt_nonneg _) two_ne_zero, div_pow,
    Real.sq_sqrt (by positivity), Real.sq_sqrt (by positivity)]
  field_simp

/-! ## Hard-threshold limit (EQ-IGN-2 → EQ-IGN-1, TC-05) -/

/-- Bₜ = 1/2 at the effective threshold, for every steepness. -/
theorem ignitionProb_at_threshold (k θ : ℝ) : ignitionProb k θ θ = 1 / 2 := by
  simp [ignitionProb]
  norm_num

/-- Above threshold the propensity tends to 1 as γ_sig → ∞. -/
theorem ignitionProb_tendsto_one {S θ : ℝ} (h : θ < S) :
    Tendsto (fun k => ignitionProb k S θ) atTop (𝓝 1) := by
  have h1 : Tendsto (fun k : ℝ => -k * (S - θ)) atTop atBot := by
    have := (tendsto_id (α := ℝ)).const_mul_atTop_of_neg (show -(S - θ) < 0 by linarith)
    refine this.congr (fun k => ?_)
    simp only [id]
    ring
  have h2 := (tendsto_const_nhds (x := (1 : ℝ))).add (Real.tendsto_exp_atBot.comp h1)
  have h3 := h2.inv₀ (by norm_num)
  simp only [add_zero, inv_one] at h3
  refine h3.congr (fun k => ?_)
  simp [ignitionProb, Function.comp]

/-- Below threshold the propensity tends to 0 as γ_sig → ∞. -/
theorem ignitionProb_tendsto_zero {S θ : ℝ} (h : S < θ) :
    Tendsto (fun k => ignitionProb k S θ) atTop (𝓝 0) := by
  have h1 : Tendsto (fun k : ℝ => -k * (S - θ)) atTop atTop := by
    have := (tendsto_id (α := ℝ)).const_mul_atTop (show 0 < -(S - θ) by linarith)
    refine this.congr (fun k => ?_)
    simp only [id]
    ring
  have h2 : Tendsto (fun k : ℝ => 1 + Real.exp (-k * (S - θ))) atTop atTop :=
    tendsto_atTop_add_const_left _ _ (Real.tendsto_exp_atTop.comp h1)
  refine (tendsto_inv_atTop_zero.comp h2).congr (fun k => ?_)
  simp [ignitionProb, Function.comp]

/-! ## Read-out discipline and exactly-once reset (EQ-PIPE-1, EQ-THEFF-1, EQ-RESET-1, EQ-REF-1) -/

/-- Parameters of the deterministic part of one canonical step (SSOT §8 steps 10–13). -/
structure CoreParams where
  θ₀ : ℝ
  η : ℝ
  δ : ℝ
  dt : ℝ
  τθ : ℝ
  τref : ℝ
  δref : ℝ
  ρ : ℝ
  lam : ℝ

/-- The slow state carried between steps. -/
structure CoreState where
  S : ℝ
  θ : ℝ
  r : ℝ

/-- Read-out modulators of EQ-THEFF-1. -/
structure Readout where
  γNE : ℝ
  gNE : ℝ
  κup : ℝ
  lower : ℝ
  β5HT : ℝ
  u : ℝ

/-- EQ-THEFF-1, with the NE clamp of EQ-NE-1 applied to g_NE. -/
noncomputable def thetaEff (m : Readout) (θ r : ℝ) : ℝ :=
  θ * (1 + m.γNE * neClamp m.γNE m.gNE) * (1 - m.κup * m.lower) + r + m.β5HT - m.u

/-- Step 8: the propensity compares the existing S with θ_eff. -/
noncomputable def corePropensity (k : ℝ) (m : Readout) (s : CoreState) : ℝ :=
  ignitionProb k s.S (thetaEff m s.θ s.r)

/-- Steps 10–13 given the sampled event `B`: allostatic step with δ_reset·B,
    exact decay, floor; refractory update; retention once; leak.
    The type has no `Readout` argument: θ_eff is never written back. -/
noncomputable def coreStep (p : CoreParams) (s : CoreState) (Sinst C V B : ℝ) : CoreState where
  S := leakStep (if B = 1 then p.ρ * s.S else s.S) Sinst p.lam
  θ := thresholdStep s.θ p.θ₀ p.η C V p.δ B p.dt p.τθ
  r := s.r * Real.exp (-(p.dt / p.τref)) + p.δref * B

/-- One full step: the read-out sets the propensity, a sampler turns it into B(t),
    and the state update consumes only B(t). -/
noncomputable def coreStepSampled (p : CoreParams) (k : ℝ) (m : Readout) (sample : ℝ → ℝ)
    (s : CoreState) (Sinst C V : ℝ) : CoreState :=
  coreStep p s Sinst C V (sample (corePropensity k m s))

/-- TC-11 read-out non-interference: two read-out settings that yield the same
    sampled event give the same successor state (θ, S and r). -/
theorem coreStep_readout_noninterference {p : CoreParams} {k : ℝ} {m₁ m₂ : Readout}
    {sample : ℝ → ℝ} {s : CoreState} {Sinst C V : ℝ}
    (hB : sample (corePropensity k m₁ s) = sample (corePropensity k m₂ s)) :
    coreStepSampled p k m₁ sample s Sinst C V = coreStepSampled p k m₂ sample s Sinst C V := by
  unfold coreStepSampled
  rw [hB]

/-- The successor threshold is computed from the state θ, never from θ_eff. -/
theorem coreStep_theta_from_state (p : CoreParams) (s : CoreState) (Sinst C V B : ℝ) :
    (coreStep p s Sinst C V B).θ = thresholdStep s.θ p.θ₀ p.η C V p.δ B p.dt p.τθ := rfl

/-- TC-12, threshold: an ignition adds exactly one δ_reset, decayed once. -/
theorem decay_allostatic_exactly_once (θ θ₀ η C V δ dt τ : ℝ) :
    decayStep (allostaticStep θ η C V δ 1) θ₀ dt τ =
      decayStep (allostaticStep θ η C V δ 0) θ₀ dt τ + δ * Real.exp (-(dt / τ)) := by
  unfold decayStep allostaticStep
  ring

/-- TC-12, refractory: an ignition adds exactly one δ_ref. -/
theorem coreStep_refractory_exactly_once (p : CoreParams) (s : CoreState) (Sinst C V : ℝ) :
    (coreStep p s Sinst C V 1).r = (coreStep p s Sinst C V 0).r + p.δref := by
  simp [coreStep]

/-- TC-12, retention: an ignition multiplies S by ρ_retain exactly once before the leak. -/
theorem coreStep_retention_exactly_once (p : CoreParams) (s : CoreState) (Sinst C V : ℝ) :
    (coreStep p s Sinst C V 1).S = leakStep (p.ρ * s.S) Sinst p.lam ∧
      (coreStep p s Sinst C V 0).S = leakStep s.S Sinst p.lam := by
  simp [coreStep]

/-! ## Cusp folds (EQ-CUSP-2) -/

/-- Three equilibria exist exactly inside the folds |θ̃| < 2(−a/3)^{3/2}
    (written as 2·(−a/3)·√(−a/3)). -/
theorem cusp_discriminant_iff_fold {a θ : ℝ} (ha : a < 0) :
    4 * a ^ 3 + 27 * θ ^ 2 < 0 ↔ |θ| < 2 * (-a / 3) * √(-a / 3) := by
  have hc : 0 < -a / 3 := by linarith
  have hs := Real.sq_sqrt hc.le
  have hR : 0 ≤ 2 * (-a / 3) * √(-a / 3) := by positivity
  have hR2 : (2 * (-a / 3) * √(-a / 3)) ^ 2 = -(4 * a ^ 3) / 27 := by
    rw [mul_pow, hs]
    ring
  rw [← abs_of_nonneg hR, ← sq_lt_sq, hR2]
  constructor <;> intro h <;> linarith

/-- Three distinct cusp equilibria. -/
def CuspBistable (a θ : ℝ) : Prop :=
  ∃ x₁ x₂ x₃ : ℝ, x₁ < x₂ ∧ x₂ < x₃ ∧
    x₁ ^ 3 + a * x₁ + θ = 0 ∧ x₂ ^ 3 + a * x₂ + θ = 0 ∧ x₃ ^ 3 + a * x₃ + θ = 0

/-- EQ-CUSP-2 (ignition fold): with θ̃ = (θ_eff − S)/u₀, once
    S > θ_eff + 2u₀(−a/3)^{3/2} the unignited well has vanished. -/
theorem cusp_monostable_of_ignition {a u₀ S θe : ℝ} (ha : a < 0) (hu : 0 < u₀)
    (h : θe + 2 * u₀ * ((-a / 3) * √(-a / 3)) < S) :
    ¬ CuspBistable a ((θe - S) / u₀) := by
  intro hb
  have h3 := (cusp_three_equilibria_iff a _).1 hb
  rw [cusp_discriminant_iff_fold ha] at h3
  have hlt : (θe - S) / u₀ < -(2 * (-a / 3) * √(-a / 3)) := by
    rw [div_lt_iff₀ hu]
    nlinarith
  have := neg_abs_le ((θe - S) / u₀)
  linarith

/-- EQ-CUSP-2 (extinction fold): once S < θ_eff − 2u₀(−a/3)^{3/2} the ignited
    well has vanished. -/
theorem cusp_monostable_of_extinction {a u₀ S θe : ℝ} (ha : a < 0) (hu : 0 < u₀)
    (h : S < θe - 2 * u₀ * ((-a / 3) * √(-a / 3))) :
    ¬ CuspBistable a ((θe - S) / u₀) := by
  intro hb
  have h3 := (cusp_three_equilibria_iff a _).1 hb
  rw [cusp_discriminant_iff_fold ha] at h3
  have hgt : 2 * (-a / 3) * √(-a / 3) < (θe - S) / u₀ := by
    rw [lt_div_iff₀ hu]
    nlinarith
  have := le_abs_self ((θe - S) / u₀)
  linarith

end Apgi

end

/-! ## Axiom audit (self-enforcing), as in `Apgi/Pilot.lean`. -/

/-- info: 'Apgi.driveTerm_monotone_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.driveTerm_monotone_iff

/-- info: 'Apgi.driveTerm_strictAnti_of_lt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.driveTerm_strictAnti_of_lt

/-- info: 'Apgi.ignites_drive_monotone_precision' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignites_drive_monotone_precision

/-- info: 'Apgi.drive_sign_symmetric' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.drive_sign_symmetric

/-- info: 'Apgi.drive_zero_at_m0' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.drive_zero_at_m0

/-- info: 'Apgi.integral_Ioi_mul_exp_neg_half_sq' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.integral_Ioi_mul_exp_neg_half_sq

/-- info: 'Apgi.integral_abs_mul_exp_neg_half_sq' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.integral_abs_mul_exp_neg_half_sq

/-- info: 'Apgi.meanAbsStdNormal_eq' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.meanAbsStdNormal_eq

/-- info: 'Apgi.ignitionProb_at_threshold' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_at_threshold

/-- info: 'Apgi.ignitionProb_tendsto_one' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_tendsto_one

/-- info: 'Apgi.ignitionProb_tendsto_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_tendsto_zero

/-- info: 'Apgi.coreStep_readout_noninterference' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.coreStep_readout_noninterference

/-- info: 'Apgi.coreStep_theta_from_state' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.coreStep_theta_from_state

/-- info: 'Apgi.decay_allostatic_exactly_once' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.decay_allostatic_exactly_once

/-- info: 'Apgi.coreStep_refractory_exactly_once' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.coreStep_refractory_exactly_once

/-- info: 'Apgi.coreStep_retention_exactly_once' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.coreStep_retention_exactly_once

/-- info: 'Apgi.cusp_discriminant_iff_fold' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_discriminant_iff_fold

/-- info: 'Apgi.cusp_monostable_of_ignition' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_monostable_of_ignition

/-- info: 'Apgi.cusp_monostable_of_extinction' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_monostable_of_extinction
