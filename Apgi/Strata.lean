module

public import Apgi.Extensions

/-!
# Temporal strata L0–L4 (SSOT §12; EQ-GEO-1, EQ-GRAD-1, EQ-STEP-1, EQ-PREC-ODE-1)

Scope decision (b): the strata are formalized as definitions plus the facts the SSOT
states about them, not as a full multiscale dynamical model. The SSOT itself says formal
verification cannot establish full L0–L4 stability without explicit assumptions
(§24.4); the two such claims below are therefore stated as explicit hypotheses:

* `H10Ordering` — the registered ordering τ_int > τ_ign > τ_θ for ℓ ≥ 2 (OSF H10). It is an
  empirical hypothesis, never proved; only its consequences are.
* `lyapunov_decoupled` proves the §12.5 Lyapunov bound **only in the zero-coupling,
  zero-forcing limit** (loop gain 0). The coupled conjecture stays unresolved (CL-26).

Proved facts: L0 lies outside the ignition model; geometric spacing at k = 133 reproduces
the SSOT table; its two known band violations (L1 at 6.65 s, L2 at 14.74 min) are
theorems, not opinions; the five-level count holds at k = 133 and fails at k = 134; the
per-level τ_Π = max(1 s, τ_ℓ/10) meets the step rule at dt₀ = 10 ms on every level.
-/

@[expose] public section

namespace Apgi

/-! ## Levels -/

/-- The five analytical strata. They are sampling points on a continuous gradient
    (EQ-GRAD-1), not compartments. -/
inductive Level where
  | L0 | L1 | L2 | L3 | L4
  deriving DecidableEq, Repr

/-- The level index ℓ. -/
def Level.idx : Level → ℕ
  | .L0 => 0
  | .L1 => 1
  | .L2 => 2
  | .L3 => 3
  | .L4 => 4

/-- Ignition dynamics are defined for ℓ ≥ 1; Level 0 is reflexive processing outside the
    access-ignition model. -/
def Level.inIgnitionModel (ℓ : Level) : Prop := 1 ≤ ℓ.idx

/-- Exactly L1–L4 carry ignition dynamics; L0 does not. -/
theorem ignition_levels (ℓ : Level) : ℓ.inIgnitionModel ↔ ℓ ≠ .L0 := by
  cases ℓ <;> simp [Level.inIgnitionModel, Level.idx]

theorem L0_outside_ignition_model : ¬ Level.L0.inIgnitionModel := by
  simp [Level.inIgnitionModel, Level.idx]

theorem idx_injective : Function.Injective Level.idx := by
  intro a b h
  cases a <;> cases b <;> simp_all [Level.idx]

/-! ## Geometric spacing at the retained v1.1 ratio (EQ-GEO-1, τ₀ = 50 ms, k = 133) -/

/-- The point timescale of a level in seconds. -/
noncomputable def levelTau (ℓ : Level) : ℝ := geoTau (1 / 20) 133 ℓ.idx

/-- Geometric spacing is strictly increasing along the levels. -/
theorem levelTau_strictMono {ℓ₁ ℓ₂ : Level} (h : ℓ₁.idx < ℓ₂.idx) : levelTau ℓ₁ < levelTau ℓ₂ := by
  unfold levelTau geoTau
  have : (133 : ℝ) ^ ℓ₁.idx < 133 ^ ℓ₂.idx := pow_lt_pow_right₀ (by norm_num) h
  linarith

/-- The SSOT §12.2 table, column k = 133, in seconds. -/
theorem levelTau_values :
    levelTau .L0 = 1 / 20 ∧ levelTau .L1 = 133 / 20 ∧ levelTau .L2 = 17689 / 20 ∧
      levelTau .L3 = 2352637 / 20 ∧ levelTau .L4 = 312900721 / 20 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num [levelTau, geoTau, Level.idx]

/-- Known limitation 1 (retained): the L1 point value 6.65 s lies above the L1 integration
    band [100 ms, 3 s]. -/
theorem L1_point_outside_band : 3 < levelTau .L1 := by
  rw [levelTau_values.2.1]; norm_num

/-- Known limitation 2 (retained): the L2 point value 14.74 min lies below the L2 integration
    window [25, 30] min, but inside the L2 operational band [1, 30] min. -/
theorem L2_point_vs_bands :
    levelTau .L2 < 25 * 60 ∧ 1 * 60 ≤ levelTau .L2 ∧ levelTau .L2 ≤ 30 * 60 := by
  rw [levelTau_values.2.2.1]; norm_num

/-- The five-level count is boundary-sensitive: with τ_min = 50 ms and τ_max ≈ 6 months
    (1.58 × 10¹⁰ ms), k = 133 keeps L4 inside the span and k = 134 pushes it out. -/
theorem five_levels_boundary :
    geoTau (1 / 20) 133 4 ≤ 158 * 10 ^ 5 ∧ 158 * 10 ^ 5 < geoTau (1 / 20) 134 4 := by
  constructor <;> norm_num [geoTau]

/-! ## Per-level precision timescale and the step rule (SSOT §12.5, EQ-STEP-1) -/

/-- v1.2 design rule: τ_Π,ℓ = max(1 s, τ_ℓ/10). -/
noncomputable def tauPiLevel (τℓ : ℝ) : ℝ := max 1 (τℓ / 10)

/-- τ_Π ≥ 1 s on every level (the v1.2 design lower bound). -/
theorem tauPiLevel_ge_one (τℓ : ℝ) : 1 ≤ tauPiLevel τℓ := le_max_left _ _

/-- dt₀ = 10 ms meets dt ≤ τ_Π/10 at every level, for every τ_ℓ. -/
theorem tauPiLevel_step_rule (τℓ : ℝ) : (1 / 100 : ℝ) ≤ tauPiLevel τℓ / 10 := by
  have := tauPiLevel_ge_one τℓ
  linarith

/-! ## Registered hypotheses, stated as hypotheses -/

/-- OSF H10 (registered, Severity per OSF Table 13): τ_int,ℓ > τ_ign,ℓ > τ_θ,ℓ for ℓ ≥ 2.
    An empirical hypothesis; APGI cannot prove it. -/
def H10Ordering (τint τign τθ : Level → ℝ) : Prop :=
  ∀ ℓ : Level, 2 ≤ ℓ.idx → τign ℓ < τint ℓ ∧ τθ ℓ < τign ℓ

/-- Conditional consequence: under H10, recovery is faster than integration at L2–L4. -/
theorem H10Ordering.recovery_lt_integration {τint τign τθ : Level → ℝ}
    (h : H10Ordering τint τign τθ) {ℓ : Level} (hℓ : 2 ≤ ℓ.idx) : τθ ℓ < τint ℓ :=
  lt_trans (h ℓ hℓ).2 (h ℓ hℓ).1

/-- H10 says nothing at L1 (the falsifiability asymmetry): any timescales whatsoever at L0–L1
    are compatible with it. -/
theorem H10Ordering.silent_below_two {τint τign τθ : Level → ℝ} (h : H10Ordering τint τign τθ)
    (f g k : ℝ) :
    H10Ordering (Function.update (Function.update τint .L1 f) .L0 f)
      (Function.update (Function.update τign .L1 g) .L0 g)
      (Function.update (Function.update τθ .L1 k) .L0 k) := by
  intro ℓ hℓ
  have h1 : ℓ ≠ .L1 := by rintro rfl; simp [Level.idx] at hℓ
  have h0 : ℓ ≠ .L0 := by rintro rfl; simp [Level.idx] at hℓ
  simp only [Function.update_of_ne h0, Function.update_of_ne h1]
  exact h ℓ hℓ

/-! ## The §12.5 Lyapunov conjecture in its decoupled limit -/

/-- V = Σ_ℓ [(Π_ℓ − Π*_ℓ)² + (θ_ℓ − θ*_ℓ)²]. -/
noncomputable def lyapV {n : ℕ} (P Ps θ θs : Fin n → ℝ) : ℝ :=
  ∑ l, ((P l - Ps l) ^ 2 + (θ l - θs l) ^ 2)

/-- dV/dt along the decoupled relaxation dΠ/dt = −(Π − Π*)/τ_Π, dθ/dt = −(θ − θ*)/τ_θ
    (zero coupling, zero forcing: loop gain 0). -/
noncomputable def lyapVdotDecoupled {n : ℕ} (τP τθ : ℝ) (P Ps θ θs : Fin n → ℝ) : ℝ :=
  ∑ l, (2 * (P l - Ps l) * (-(P l - Ps l) / τP) + 2 * (θ l - θs l) * (-(θ l - θs l) / τθ))

/-- The conjectured bound V̇ ≤ −λV with λ = min(1/τ_Π, 1/τ_θ)·(1 − loop gain) holds at loop
    gain 0 (indeed with a factor 2 to spare). This is the decoupled limit only; the coupled
    conjecture is CL-26, unresolved. -/
theorem lyapunov_decoupled {n : ℕ} {τP τθ : ℝ} (hP : 0 < τP) (hθ : 0 < τθ)
    (P Ps θ θs : Fin n → ℝ) :
    lyapVdotDecoupled τP τθ P Ps θ θs ≤ -(min (1 / τP) (1 / τθ) * (1 - 0)) * lyapV P Ps θ θs := by
  unfold lyapVdotDecoupled lyapV
  rw [sub_zero, mul_one, neg_mul, Finset.mul_sum, ← Finset.sum_neg_distrib]
  apply Finset.sum_le_sum
  intro l _
  set m := min (1 / τP) (1 / τθ)
  have hm1 : m ≤ 1 / τP := min_le_left _ _
  have hm2 : m ≤ 1 / τθ := min_le_right _ _
  have e1 : 2 * (P l - Ps l) * (-(P l - Ps l) / τP) = -(2 * (1 / τP)) * (P l - Ps l) ^ 2 := by
    field_simp
  have e2 : 2 * (θ l - θs l) * (-(θ l - θs l) / τθ) = -(2 * (1 / τθ)) * (θ l - θs l) ^ 2 := by
    field_simp
  rw [e1, e2]
  have hp1 : 0 < 1 / τP := by positivity
  have hp2 : 0 < 1 / τθ := by positivity
  have hm0 : 0 < m := lt_min hp1 hp2
  nlinarith [sq_nonneg (P l - Ps l), sq_nonneg (θ l - θs l),
    mul_le_mul_of_nonneg_right hm1 (sq_nonneg (P l - Ps l)),
    mul_le_mul_of_nonneg_right hm2 (sq_nonneg (θ l - θs l))]

end Apgi

end

/-! ## Axiom audit (self-enforcing). -/

/-- info: 'Apgi.ignition_levels' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignition_levels

/-- info: 'Apgi.L0_outside_ignition_model' depends on axioms: [propext] -/
#guard_msgs in
#print axioms Apgi.L0_outside_ignition_model

/-- info: 'Apgi.idx_injective' depends on axioms: [propext] -/
#guard_msgs in
#print axioms Apgi.idx_injective

/-- info: 'Apgi.levelTau_strictMono' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.levelTau_strictMono

/-- info: 'Apgi.levelTau_values' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.levelTau_values

/-- info: 'Apgi.L1_point_outside_band' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.L1_point_outside_band

/-- info: 'Apgi.L2_point_vs_bands' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.L2_point_vs_bands

/-- info: 'Apgi.five_levels_boundary' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.five_levels_boundary

/-- info: 'Apgi.tauPiLevel_ge_one' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.tauPiLevel_ge_one

/-- info: 'Apgi.tauPiLevel_step_rule' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.tauPiLevel_step_rule

/-- info: 'Apgi.H10Ordering.recovery_lt_integration' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.H10Ordering.recovery_lt_integration

/-- info: 'Apgi.H10Ordering.silent_below_two' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.H10Ordering.silent_below_two

/-- info: 'Apgi.lyapunov_decoupled' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.lyapunov_decoupled
