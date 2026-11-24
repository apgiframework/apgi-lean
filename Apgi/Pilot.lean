module

public import Apgi.Spec
public import Mathlib.Analysis.SpecialFunctions.Exp
public import Mathlib.Analysis.Calculus.Deriv.Add
public import Mathlib.Analysis.Calculus.Deriv.Pow
public import Mathlib.Analysis.Calculus.Deriv.Mul
public import Mathlib.Tactic.LinearCombination
public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Positivity
public import Mathlib.Tactic.NormNum
public import Mathlib.Topology.Order.IntermediateValue
public import Mathlib.Analysis.SpecialFunctions.Pow.Real
public import Mathlib.Tactic

/-!
# APGI Lean pilot

Build with `lake build --wfail`: any `sorry` or warning fails the build.

Constants (`θ_floor`, `θ_lower`, `θ_upper`, …) are NOT defined here. They are
generated into `Apgi/Spec.lean` from `specification/parameters.json`, which
also records `specHash`. When the registry changes, regenerate; proofs that
break are reporting a real change, not a nuisance.

Each theorem is linked to an equation ID in `specification/equations.json`
and has a twin property test in `verification/python/test_twins.py`.
-/

@[expose] public section

namespace Apgi

/-! ## Proof 1 — Ignition monotonicity (EQ-IGN-1, EQ-PREC-1, EQ-IGN-2)
`S` is the precision-weighted prediction error. -/

/-- Deterministic ignition criterion: S exceeds the threshold. -/
def Ignites (S θ : ℝ) : Prop := θ < S

/-- A higher threshold cannot make ignition easier at fixed signal. -/
theorem ignites_antitone_threshold {S θ₁ θ₂ : ℝ}
    (h : θ₁ ≤ θ₂) (hI : Ignites S θ₂) : Ignites S θ₁ :=
  lt_of_le_of_lt h hI

/-- Raising precision cannot block ignition at a fixed |prediction error|.
    (`Π` is reserved notation in Mathlib, hence `prec`.) -/
theorem ignites_monotone_precision {prec₁ prec₂ ε θ : ℝ}
    (h : prec₁ ≤ prec₂) (hI : Ignites (prec₁ * |ε|) θ) :
    Ignites (prec₂ * |ε|) θ :=
  lt_of_lt_of_le hI (mul_le_mul_of_nonneg_right h (abs_nonneg ε))

/-- Probabilistic ignition propensity. `k` is the sigmoid steepness γ_sig = 1/τ_σ
    (`gamma_sig`, unit 1/AU), not the update gain. -/
noncomputable def ignitionProb (k S θ : ℝ) : ℝ :=
  1 / (1 + Real.exp (-k * (S - θ)))

theorem ignitionProb_antitone_threshold {k S θ₁ θ₂ : ℝ}
    (hk : 0 ≤ k) (h : θ₁ ≤ θ₂) :
    ignitionProb k S θ₂ ≤ ignitionProb k S θ₁ := by
  unfold ignitionProb
  have hexp : Real.exp (-k * (S - θ₁)) ≤ Real.exp (-k * (S - θ₂)) :=
    Real.exp_le_exp.mpr (by nlinarith [mul_le_mul_of_nonneg_left h hk])
  have hpos : 0 < 1 + Real.exp (-k * (S - θ₁)) := by positivity
  exact one_div_le_one_div_of_le hpos (by linarith)

/-! ## Proof 2 — Threshold semantics: floor versus operating range (EQ-THR-1)
Two separate types force the specification to say which one is a state
invariant. KC-THETA-ROLE is resolved: the floor is the state invariant and
the θ₀ band is a regime label (Notation Appendix v1.1: θₜ "may leave the band
transiently after δ_reset"). -/

/-- Every reachable threshold state respects the floor. -/
structure ThresholdState where
  value : ℝ
  floor : θ_floor ≤ value

/-- The canonical θ₀ band (a regime label, not a state invariant). -/
structure OperatingThreshold where
  value : ℝ
  lower : θ_lower ≤ value
  upper : value ≤ θ_upper

/-- Consistency lemma: the operating range lies above the floor. -/
def OperatingThreshold.toState (t : OperatingThreshold) : ThresholdState :=
  ⟨t.value, le_trans (by norm_num [θ_floor, θ_lower]) t.lower⟩

/-- Discrete threshold update with the floor enforced by clamping. -/
noncomputable def clampedUpdate (θ target gain : ℝ) : ℝ :=
  max θ_floor (θ + gain * (target - θ))

theorem clampedUpdate_floor (θ target gain : ℝ) :
    θ_floor ≤ clampedUpdate θ target gain :=
  le_max_left _ _

/-- The band is NOT an invariant of the clamped update once the target may
    fall below its lower bound: start at the lower bound and move fully to the
    floor. Stated with the registry constants, so it holds for any band that
    lies strictly above the floor. This is why the band is a regime label
    (see `operatingRange_invariant_of_target` for the restricted case). -/
theorem operatingRange_not_invariant :
    ∃ θ target gain : ℝ, θ_lower ≤ θ ∧ θ ≤ θ_upper ∧ 0 ≤ gain ∧ gain ≤ 1 ∧
      clampedUpdate θ target gain < θ_lower := by
  refine ⟨θ_lower, θ_floor, 1, le_rfl, ?_, ?_, ?_, ?_⟩ <;>
    norm_num [clampedUpdate, θ_floor, θ_lower, θ_upper, max_lt_iff]

/-! ## Proof 3 — Cusp potential, canonical sign convention (+θ·x) (EQ-CUSP-1) -/

noncomputable def cuspV (a θ x : ℝ) : ℝ := x ^ 4 / 4 + a * x ^ 2 / 2 + θ * x

theorem cuspV_hasDerivAt (a θ x : ℝ) :
    HasDerivAt (cuspV a θ) (x ^ 3 + a * x + θ) x := by
  have h := (((hasDerivAt_pow 4 x).div_const 4).add
      (((hasDerivAt_pow 2 x).const_mul a).div_const 2)).add
      ((hasDerivAt_id x).const_mul θ)
  refine h.congr_deriv ?_
  norm_num
  ring

/-- With a non-negative splitting factor the equilibrium is unique.
    So a < 0 is NECESSARY for bistability, and therefore for hysteresis.
    It is not sufficient on its own: see `cusp_three_equilibria`. -/
theorem cusp_unique_equilibrium {a θ x₁ x₂ : ℝ} (ha : 0 ≤ a)
    (h₁ : x₁ ^ 3 + a * x₁ + θ = 0) (h₂ : x₂ ^ 3 + a * x₂ + θ = 0) :
    x₁ = x₂ := by
  have key : (x₁ - x₂) * (x₁ ^ 2 + x₁ * x₂ + x₂ ^ 2 + a) = 0 := by
    linear_combination h₁ - h₂
  rcases mul_eq_zero.1 key with h | h
  · exact sub_eq_zero.1 h
  · have hsq : (x₁ - x₂) * (x₁ - x₂) ≤ 0 := by nlinarith [sq_nonneg (x₁ + x₂)]
    exact sub_eq_zero.1 (mul_self_eq_zero.1 (le_antisymm hsq (mul_self_nonneg _)))

/-- The necessary condition is not vacuous: with a < 0 distinct equilibria
    do occur (a = −1, θ = 0: x = 0 and x = 1). -/
theorem cusp_two_equilibria_witness :
    ∃ a θ x₁ x₂ : ℝ, a < 0 ∧ x₁ ≠ x₂ ∧
      x₁ ^ 3 + a * x₁ + θ = 0 ∧ x₂ ^ 3 + a * x₂ + θ = 0 :=
  ⟨-1, 0, 0, 1, by norm_num, by norm_num, by norm_num, by norm_num⟩

/-- SUFFICIENCY (claim CL-5): a negative splitting factor together with a
    negative discriminant 4a³ + 27θ² < 0 gives three distinct equilibria.
    With c = √(−a/3) the critical points are ±c; the discriminant condition is
    exactly |θ| < 2c³, so dV/dx changes sign on (−M, −c), (−c, c) and (c, M),
    and the intermediate value theorem supplies one root in each. -/
theorem cusp_three_equilibria {a θ : ℝ} (ha : a < 0)
    (hd : 4 * a ^ 3 + 27 * θ ^ 2 < 0) :
    ∃ x₁ x₂ x₃ : ℝ, x₁ < x₂ ∧ x₂ < x₃ ∧
      x₁ ^ 3 + a * x₁ + θ = 0 ∧ x₂ ^ 3 + a * x₂ + θ = 0 ∧
      x₃ ^ 3 + a * x₃ + θ = 0 := by
  set c := Real.sqrt (-a / 3) with hc
  have hc2 : c ^ 2 = -a / 3 := Real.sq_sqrt (by linarith)
  have hcpos : 0 < c := Real.sqrt_pos.2 (by linarith)
  have ha' : a = -3 * c ^ 2 := by linarith
  have h1 : 27 * θ ^ 2 < 108 * c ^ 6 := by
    have h := hd
    rw [ha'] at h
    nlinarith [h]
  have hθ : |θ| < 2 * c ^ 3 :=
    abs_lt_of_sq_lt_sq (by nlinarith [h1]) (by positivity)
  obtain ⟨hθl, hθr⟩ := abs_lt.1 hθ
  set f : ℝ → ℝ := fun x => x ^ 3 + a * x + θ with hf
  have hcont : Continuous f := by fun_prop
  have hfm : 0 < f (-c) := by simp only [hf]; rw [ha']; nlinarith
  have hfp : f c < 0 := by simp only [hf]; rw [ha']; nlinarith
  set M := 2 * c + |θ| + 1 with hM
  have habs : 0 ≤ |θ| := abs_nonneg θ
  have hMc : c < M := by linarith
  have hMsq : 1 ≤ M ^ 2 - 3 * c ^ 2 := by nlinarith
  have hMpos : 0 < M := by linarith
  have hfM : 0 < f M := by
    simp only [hf]; rw [ha']
    have : M ≤ M * (M ^ 2 - 3 * c ^ 2) := by nlinarith
    nlinarith [neg_abs_le θ]
  have hfnM : f (-M) < 0 := by
    simp only [hf]; rw [ha']
    have : M ≤ M * (M ^ 2 - 3 * c ^ 2) := by nlinarith
    nlinarith [le_abs_self θ]
  obtain ⟨x₁, ⟨h1l, h1r⟩, hx₁⟩ :=
    intermediate_value_Ioo (by linarith) hcont.continuousOn ⟨hfnM, hfm⟩
  obtain ⟨x₂, ⟨h2l, h2r⟩, hx₂⟩ :=
    intermediate_value_Ioo' (by linarith) hcont.continuousOn ⟨hfp, hfm⟩
  obtain ⟨x₃, ⟨h3l, h3r⟩, hx₃⟩ :=
    intermediate_value_Ioo hMc.le hcont.continuousOn ⟨hfp, hfM⟩
  exact ⟨x₁, x₂, x₃, by linarith, by linarith, hx₁, hx₂, hx₃⟩

/-! ## Proof 4 — Bounded discrete updates (EQ-UPD-1, EQ-EULER-1)
`gain` replaces the draft's α, which collides with sigmoid steepness. -/

theorem convex_update_mem_Icc {lo hi x u gain : ℝ}
    (hx : x ∈ Set.Icc lo hi) (hu : u ∈ Set.Icc lo hi)
    (hg0 : 0 ≤ gain) (hg1 : gain ≤ 1) :
    x + gain * (u - x) ∈ Set.Icc lo hi := by
  rw [Set.mem_Icc] at hx hu ⊢
  obtain ⟨hx0, hx1⟩ := hx
  obtain ⟨hu0, hu1⟩ := hu
  have h1 : 0 ≤ (1 - gain) * (x - lo) := mul_nonneg (by linarith) (by linarith)
  have h2 : 0 ≤ gain * (u - lo) := mul_nonneg hg0 (by linarith)
  have h3 : 0 ≤ (1 - gain) * (hi - x) := mul_nonneg (by linarith) (by linarith)
  have h4 : 0 ≤ gain * (hi - u) := mul_nonneg hg0 (by linarith)
  constructor <;> nlinarith

/-- Forward-Euler step of dx/dt = (u − x)/τ stays bounded whenever dt ≤ τ.
    This is the precondition the Python integrator must honour. -/
theorem euler_step_mem_Icc {lo hi x u dt τ : ℝ}
    (hx : x ∈ Set.Icc lo hi) (hu : u ∈ Set.Icc lo hi)
    (hτ : 0 < τ) (hdt0 : 0 ≤ dt) (hdt : dt ≤ τ) :
    x + (dt / τ) * (u - x) ∈ Set.Icc lo hi :=
  convex_update_mem_Icc hx hu (div_nonneg hdt0 hτ.le) ((div_le_one hτ).2 hdt)

/-! ### Exact exponential decay (EQ-DECAY-1, Math Spec Eq. 32)
The corpus integrates threshold relaxation exactly rather than by forward
Euler, so its boundedness needs no step-size condition. -/

/-- One exact step of dθ/dt = −(θ − θ₀)/τ. -/
noncomputable def decayStep (θ θ₀ dt τ : ℝ) : ℝ :=
  θ₀ + (θ - θ₀) * Real.exp (-(dt / τ))

/-- The exact-decay gain 1 − e^{−dt/τ} lies in [0, 1] for every dt ≥ 0. -/
theorem decayGain_mem_Icc {dt τ : ℝ} (hτ : 0 < τ) (hdt : 0 ≤ dt) :
    1 - Real.exp (-(dt / τ)) ∈ Set.Icc (0 : ℝ) 1 := by
  have h0 : 0 ≤ dt / τ := div_nonneg hdt hτ.le
  have hle : Real.exp (-(dt / τ)) ≤ 1 := Real.exp_le_one_iff.2 (by linarith)
  have hpos : 0 < Real.exp (-(dt / τ)) := Real.exp_pos _
  rw [Set.mem_Icc]
  constructor <;> linarith

/-- Exact decay toward a θ₀ inside an interval keeps θ inside it, for any
    dt ≥ 0. With the θ₀ band as the interval: between ignition events the
    band is invariant; only δ_reset and the allostatic term can leave it. -/
theorem decay_step_mem_Icc {lo hi θ θ₀ dt τ : ℝ}
    (hθ : θ ∈ Set.Icc lo hi) (h0 : θ₀ ∈ Set.Icc lo hi)
    (hτ : 0 < τ) (hdt : 0 ≤ dt) :
    decayStep θ θ₀ dt τ ∈ Set.Icc lo hi := by
  have hg := decayGain_mem_Icc hτ hdt
  rw [Set.mem_Icc] at hg
  have h := convex_update_mem_Icc hθ h0 hg.1 hg.2
  have e : decayStep θ θ₀ dt τ = θ + (1 - Real.exp (-(dt / τ))) * (θ₀ - θ) := by
    unfold decayStep; ring
  rw [e]
  exact h

/-- Restricting targets to the band (with 0 ≤ gain ≤ 1) makes it invariant:
    the clamp at the floor never binds. The corpus does not adopt this
    restriction (the band is a regime label); the theorem records exactly
    what adopting it would require. -/
theorem operatingRange_invariant_of_target {θ target gain : ℝ}
    (hθ : θ ∈ Set.Icc θ_lower θ_upper) (ht : target ∈ Set.Icc θ_lower θ_upper)
    (hg0 : 0 ≤ gain) (hg1 : gain ≤ 1) :
    clampedUpdate θ target gain ∈ Set.Icc θ_lower θ_upper := by
  have hu := convex_update_mem_Icc hθ ht hg0 hg1
  have hfl : θ_floor ≤ θ + gain * (target - θ) :=
    le_trans (by norm_num [θ_floor, θ_lower]) hu.1
  rw [clampedUpdate, max_eq_right hfl]
  exact hu

/-! ## Proof 5 — Dimensions
AU is its own base dimension, so arbitrary units never mix silently with
physical units. Mirrors `specification/units.json`. -/

structure Dim where
  time : ℤ := 0
  energy : ℤ := 0
  bit : ℤ := 0
  au : ℤ := 0
  /-- Molecule count (ATP). Deliberately not `amount` (mol). -/
  atp : ℤ := 0
deriving DecidableEq, Repr

structure Qty (d : Dim) where
  val : ℝ

noncomputable instance {d : Dim} : Add (Qty d) := ⟨fun x y => ⟨x.val + y.val⟩⟩

noncomputable def Qty.mul {d₁ d₂ : Dim} (x : Qty d₁) (y : Qty d₂) :
    Qty ⟨d₁.time + d₂.time, d₁.energy + d₂.energy, d₁.bit + d₂.bit, d₁.au + d₂.au,
      d₁.atp + d₂.atp⟩ :=
  ⟨x.val * y.val⟩

def dimensionless : Dim := {}
def perSecond : Dim := { time := -1 }
def auDim : Dim := { au := 1 }
def joulePerBit : Dim := { energy := 1, bit := -1 }
def atpPerBit : Dim := { atp := 1, bit := -1 }

/-- κ (`kappa` in parameters.json): ATP per bit of ignition-event information
    (Notation Appendix §11). Uncalibrated: no value lives here or in the registry. -/
abbrev Kappa := Qty atpPerBit
/-- R_L: the dimensionless erasure-overhead ratio against the Landauer floor.
    Formerly (and wrongly) also written κ. -/
abbrev OverheadRatio := Qty dimensionless
abbrev Threshold := Qty auDim

/-! Positive control: same-dimension addition elaborates. -/
example (k₁ k₂ : Kappa) : (k₁ + k₂).val = k₁.val + k₂.val := rfl

/-! Negative cases are tests, not comments: each forbidden mix must FAIL to
elaborate. `fail_if_success` turns an unexpected success into a build error. -/

/-- κ (ATP/bit) + the dimensionless overhead ratio R_L is rejected: the corpus
    keeps the two quantities apart (Notation Appendix §11). -/
example (_k : Kappa) (_r : OverheadRatio) : True := by
  fail_if_success exact (fun _ => trivial) (_k + _r)
  trivial

/-- κ (ATP/bit) + a rate (1/s) is rejected. -/
example (_k : Kappa) (_r : Qty perSecond) : True := by
  fail_if_success exact (fun _ => trivial) (_k + _r)
  trivial

/-- A threshold (AU) + an energy per bit (J/bit) is rejected. -/
example (_θ : Threshold) (_e : Qty joulePerBit) : True := by
  fail_if_success exact (fun _ => trivial) (_θ + _e)
  trivial

/-- A threshold (AU) + κ (ATP/bit) is rejected: AU has no calibration map. -/
example (_θ : Threshold) (_k : Kappa) : True := by
  fail_if_success exact (fun _ => trivial) (_θ + _k)
  trivial

end Apgi

end

/-! ## Axiom audit (self-enforcing)
Each `#guard_msgs` pins the exact axiom list. A `sorry` (`sorryAx`), a custom
`axiom`, or any change to a theorem's dependencies alters the message and
fails the build. -/

/-- info: 'Apgi.ignites_antitone_threshold' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignites_antitone_threshold

/-- info: 'Apgi.ignites_monotone_precision' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignites_monotone_precision

/-- info: 'Apgi.ignitionProb_antitone_threshold' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_antitone_threshold

/-- info: 'Apgi.clampedUpdate_floor' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.clampedUpdate_floor

/-- info: 'Apgi.operatingRange_not_invariant' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.operatingRange_not_invariant

/-- info: 'Apgi.cuspV_hasDerivAt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cuspV_hasDerivAt

/-- info: 'Apgi.cusp_unique_equilibrium' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_unique_equilibrium

/-- info: 'Apgi.cusp_two_equilibria_witness' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_two_equilibria_witness

/-- info: 'Apgi.convex_update_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.convex_update_mem_Icc

/-- info: 'Apgi.euler_step_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.euler_step_mem_Icc

/-- info: 'Apgi.operatingRange_invariant_of_target' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.operatingRange_invariant_of_target

/-- info: 'Apgi.cusp_three_equilibria' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_three_equilibria

/-- info: 'Apgi.decayGain_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.decayGain_mem_Icc

/-- info: 'Apgi.decay_step_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.decay_step_mem_Icc
