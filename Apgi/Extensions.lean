module

public import Apgi.Dynamics

/-!
# APGI equations registered in specification 0.5.0 (task 54)

Lean-backed statements for the SSOT equations added to the registry in task 54:
learning-rule contraction (EQ-PRED-1), the dopamine non-monotonicity (EQ-DA-1),
urgency (EQ-URG-1), the observation model (EQ-OBS-2), cross-channel
normalization (EQ-NORM-1), the timescale forms (EQ-GEO-1, EQ-GRAD-1), the
small cross-level transform (EQ-PSI-SMALL-1), the loop-gain heuristic
(EQ-LOOP-1, including the PD-LOOP-GAIN numbers), the synchrony gate
(EQ-KUR-1), the weighted aggregation (EQ-MS-2) and the bounded hierarchical
target (EQ-MS-4). Each theorem has a float64 twin in `test_twins.py`.
-/

@[expose] public section

namespace Apgi

/-! ## EQ-PRED-1: the learning rule contracts the error for 0 < η·Π < 2 -/

/-- With fixed input x, one update x̂ ← x̂ + η·Π·(x − x̂) multiplies the error by 1 − η·Π. -/
theorem pred_error_update (x xh η p : ℝ) :
    x - (xh + η * p * (x - xh)) = (1 - η * p) * (x - xh) := by ring

/-- The SSOT stability condition η_pred·Π < 2 (with η_pred·Π > 0) makes the
    error factor a strict contraction. -/
theorem pred_contraction {η p : ℝ} (h0 : 0 < η * p) (h2 : η * p < 2) : |1 - η * p| < 1 := by
  rw [abs_lt]
  constructor <;> linarith

/-! ## EQ-DA-1: the dopamine bias is non-monotonic in salience -/

/-- For β_DA > 0, |zⁱ + β_DA| > |zⁱ| exactly while zⁱ > −β_DA/2 (SSOT §5.4). -/
theorem da_salience_iff {z β : ℝ} (hβ : 0 < β) : |z| < |z + β| ↔ -β / 2 < z := by
  rw [← sq_lt_sq]
  constructor <;> intro h <;> nlinarith

/-! ## EQ-URG-1: urgency -/

/-- u(t) = u_max·(1 − exp(−t_ep/τ_u)). -/
noncomputable def urgency (umax τu t : ℝ) : ℝ := umax * (1 - Real.exp (-(t / τu)))

theorem urgency_nonneg {umax τu t : ℝ} (hu : 0 ≤ umax) (hτ : 0 < τu) (ht : 0 ≤ t) :
    0 ≤ urgency umax τu t := by
  unfold urgency
  have hd := div_nonneg ht hτ.le
  have : Real.exp (-(t / τu)) ≤ 1 := Real.exp_le_one_iff.2 (by linarith)
  exact mul_nonneg hu (by linarith)

/-- u_max = 0 recovers the canonical model. -/
theorem urgency_off (τu t : ℝ) : urgency 0 τu t = 0 := by simp [urgency]

/-- Urgency never falls within an episode. -/
theorem urgency_monotone {umax τu t₁ t₂ : ℝ} (hu : 0 ≤ umax) (hτ : 0 < τu) (h : t₁ ≤ t₂) :
    urgency umax τu t₁ ≤ urgency umax τu t₂ := by
  unfold urgency
  apply mul_le_mul_of_nonneg_left _ hu
  have : -(t₂ / τu) ≤ -(t₁ / τu) := neg_le_neg (div_le_div_of_nonneg_right h hτ.le)
  have := Real.exp_le_exp.2 this
  linarith

/-! ## EQ-OBS-2: observation model -/

/-- P(report) = g + (1 − g − λ_lapse)·P(hit). -/
noncomputable def pReport (g lapse ph : ℝ) : ℝ := g + (1 - g - lapse) * ph

/-- With P(hit) ∈ [0, 1] and g + λ ≤ 1, the report probability lies in [g, 1 − λ]. -/
theorem pReport_mem_Icc {g lapse ph : ℝ} (hgl : g + lapse ≤ 1) (h0 : 0 ≤ ph) (h1 : ph ≤ 1) :
    pReport g lapse ph ∈ Set.Icc g (1 - lapse) := by
  unfold pReport
  rw [Set.mem_Icc]
  constructor <;> nlinarith

/-- A larger latent hit probability never lowers the report probability. -/
theorem pReport_monotone {g lapse ph₁ ph₂ : ℝ} (hgl : g + lapse ≤ 1) (h : ph₁ ≤ ph₂) :
    pReport g lapse ph₁ ≤ pReport g lapse ph₂ := by
  unfold pReport
  nlinarith

/-! ## EQ-NORM-1: divisive cross-channel normalization -/

/-- Πᵉ_norm = 2Πᵉ/(Πᵉ + Πⁱ). -/
noncomputable def normGain (p q : ℝ) : ℝ := 2 * p / (p + q)

/-- The two normalized gains share a fixed budget of 2. -/
theorem normGain_budget {p q : ℝ} (h : p + q ≠ 0) : normGain p q + normGain q p = 2 := by
  unfold normGain
  rw [add_comm q p, ← add_div]
  field_simp

/-- Equal gains reduce to the additive core (gain 1). -/
theorem normGain_equal {p : ℝ} (hp : p ≠ 0) : normGain p p = 1 := by
  unfold normGain
  field_simp
  ring

/-- Under the budget, more interoceptive gain lowers exteroceptive gain (R3). -/
theorem normGain_antitone_other {p q₁ q₂ : ℝ} (hp : 0 < p) (hq : 0 ≤ q₁) (h : q₁ ≤ q₂) :
    normGain p q₂ ≤ normGain p q₁ := by
  unfold normGain
  rw [div_le_div_iff₀ (by linarith) (by linarith)]
  nlinarith

/-! ## EQ-GEO-1 and EQ-GRAD-1: timescales -/

/-- τ_ℓ = τ₀·k^ℓ. -/
noncomputable def geoTau (τ₀ k : ℝ) (ℓ : ℕ) : ℝ := τ₀ * k ^ ℓ

/-- Adjacent levels differ by exactly the coarse-graining ratio k. -/
theorem geoTau_succ (τ₀ k : ℝ) (ℓ : ℕ) : geoTau τ₀ k (ℓ + 1) = k * geoTau τ₀ k ℓ := by
  unfold geoTau
  ring

/-- log τ(h) = log τ_min + h·log(τ_max/τ_min). -/
noncomputable def gradTau (τmin τmax h : ℝ) : ℝ :=
  Real.exp (Real.log τmin + h * Real.log (τmax / τmin))

theorem gradTau_zero {τmin τmax : ℝ} (hmin : 0 < τmin) : gradTau τmin τmax 0 = τmin := by
  simp [gradTau, Real.exp_log hmin]

theorem gradTau_one {τmin τmax : ℝ} (hmin : 0 < τmin) (hmax : 0 < τmax) :
    gradTau τmin τmax 1 = τmax := by
  have e : τmin * (τmax / τmin) = τmax := by field_simp
  unfold gradTau
  rw [one_mul, ← Real.log_mul hmin.ne' (div_pos hmax hmin).ne', e, Real.exp_log hmax]

/-- With τ_min ≤ τ_max the gradient is monotone in the hierarchy coordinate h. -/
theorem gradTau_monotone {τmin τmax h₁ h₂ : ℝ} (hmin : 0 < τmin) (hle : τmin ≤ τmax)
    (h : h₁ ≤ h₂) : gradTau τmin τmax h₁ ≤ gradTau τmin τmax h₂ := by
  unfold gradTau
  apply Real.exp_le_exp.2
  have hl : 0 ≤ Real.log (τmax / τmin) :=
    Real.log_nonneg ((one_le_div hmin).2 hle)
  nlinarith [mul_le_mul_of_nonneg_right h hl]

/-! ## EQ-PSI-SMALL-1: ψ(z) = tanh(γ_ψ·z) -/

noncomputable def psiSmall (γ z : ℝ) : ℝ := Real.tanh (γ * z)

theorem psiSmall_zero (γ : ℝ) : psiSmall γ 0 = 0 := by simp [psiSmall]

theorem psiSmall_abs_lt (γ z : ℝ) : |psiSmall γ z| < 1 := Real.abs_tanh_lt_one _

theorem psiSmall_odd (γ z : ℝ) : psiSmall γ (-z) = -psiSmall γ z := by
  simp [psiSmall, Real.tanh_neg]

/-! ## EQ-LOOP-1: cross-level loop gain (design heuristic) and PD-LOOP-GAIN -/

/-- (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ². -/
noncomputable def loopGain (cd cu τ γ : ℝ) : ℝ := (cd * τ) * (cu * τ) * γ ^ 2

/-- Inside the Paper 3 dimensionless ranges C_down·τ_Π ≤ 0.5, C_up·τ_Π ≤ 0.2 and
    γ_ψ ∈ [0, 3], the loop gain is below 1 (at most 0.9). -/
theorem loopGain_lt_one_of_paper3 {cd cu τ γ : ℝ} (hd0 : 0 ≤ cd * τ) (hd : cd * τ ≤ 1 / 2)
    (hu0 : 0 ≤ cu * τ) (hu : cu * τ ≤ 1 / 5) (hγ0 : 0 ≤ γ) (hγ : γ ≤ 3) :
    loopGain cd cu τ γ < 1 := by
  unfold loopGain
  have hxy : (cd * τ) * (cu * τ) ≤ 1 / 10 := by nlinarith
  have hxy0 : 0 ≤ (cd * τ) * (cu * τ) := mul_nonneg hd0 hu0
  have hg : γ ^ 2 ≤ 9 := by nlinarith
  nlinarith [mul_le_mul hxy hg (sq_nonneg γ) (by norm_num : (0 : ℝ) ≤ 1 / 10)]

/-- PD-LOOP-GAIN, before: τ_Π = 1000 s, C_down = 0.1 s⁻¹, C_up = 0.05 s⁻¹, γ_ψ = 2. -/
theorem loopGain_production_defaults : loopGain (1 / 10) (1 / 20) 1000 2 = 20000 := by
  norm_num [loopGain]

/-- PD-LOOP-GAIN, after (author decision 2026-11-25): couplings scaled to the
    Paper 3 gains, C_down = 0.1/τ_Π and C_up = 0.05/τ_Π, give 0.02 for every τ_Π > 0. -/
theorem loopGain_scaled_couplings {τ : ℝ} (hτ : τ ≠ 0) :
    loopGain (1 / 10 / τ) (1 / 20 / τ) τ 2 = 1 / 50 := by
  unfold loopGain
  field_simp
  norm_num

/-! ## EQ-KUR-1: synchrony gate Γ = R² -/

theorem kuramotoGate_mem_Icc {R : ℝ} (h0 : 0 ≤ R) (h1 : R ≤ 1) :
    R ^ 2 ∈ Set.Icc (0 : ℝ) 1 ∧ R ^ 2 ≤ R := by
  refine ⟨⟨sq_nonneg R, by nlinarith⟩, by nlinarith⟩

/-! ## EQ-MS-2: convex aggregation across levels -/

/-- With non-negative weights summing to 1, the aggregate drive never exceeds the
    largest level drive. -/
theorem msGlobal_le {n : ℕ} (w s : Fin n → ℝ) (M : ℝ) (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i, w i = 1) (hM : ∀ i, s i ≤ M) : ∑ i, w i * s i ≤ M :=
  calc ∑ i, w i * s i ≤ ∑ i, w i * M :=
        Finset.sum_le_sum (fun i _ => mul_le_mul_of_nonneg_left (hM i) (hw i))
    _ = M := by rw [← Finset.sum_mul, hsum, one_mul]

/-- …and never falls below the smallest level drive. -/
theorem msGlobal_ge {n : ℕ} (w s : Fin n → ℝ) (m : ℝ) (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i, w i = 1) (hm : ∀ i, m ≤ s i) : m ≤ ∑ i, w i * s i :=
  calc m = ∑ i, w i * m := by rw [← Finset.sum_mul, hsum, one_mul]
    _ ≤ ∑ i, w i * s i :=
        Finset.sum_le_sum (fun i _ => mul_le_mul_of_nonneg_left (hm i) (hw i))

/-! ## EQ-MS-4: bounded hierarchical relaxation target -/

/-- θ₀,ℓ(t) = θ₀,ℓ·clip(1 + κ_down·(Π_{ℓ+1}/Π_max)·cos φ̄, 0.5, 1.5). -/
noncomputable def msTarget (θ₀ κ ρ φ : ℝ) : ℝ :=
  θ₀ * max (1 / 2) (min (3 / 2) (1 + κ * ρ * Real.cos φ))

theorem msTarget_band {θ₀ : ℝ} (hθ : 0 ≤ θ₀) (κ ρ φ : ℝ) :
    θ₀ / 2 ≤ msTarget θ₀ κ ρ φ ∧ msTarget θ₀ κ ρ φ ≤ 3 * θ₀ / 2 := by
  unfold msTarget
  have h1 : (1 / 2 : ℝ) ≤ max (1 / 2) (min (3 / 2) (1 + κ * ρ * Real.cos φ)) := le_max_left _ _
  have h2 : max (1 / 2) (min (3 / 2) (1 + κ * ρ * Real.cos φ)) ≤ 3 / 2 :=
    max_le (by norm_num) (min_le_left _ _)
  constructor <;> nlinarith

end Apgi

end

/-! ## Axiom audit (self-enforcing). -/

/-- info: 'Apgi.pred_error_update' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pred_error_update

/-- info: 'Apgi.pred_contraction' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pred_contraction

/-- info: 'Apgi.da_salience_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.da_salience_iff

/-- info: 'Apgi.urgency_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.urgency_nonneg

/-- info: 'Apgi.urgency_off' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.urgency_off

/-- info: 'Apgi.urgency_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.urgency_monotone

/-- info: 'Apgi.pReport_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pReport_mem_Icc

/-- info: 'Apgi.pReport_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pReport_monotone

/-- info: 'Apgi.normGain_budget' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.normGain_budget

/-- info: 'Apgi.normGain_equal' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.normGain_equal

/-- info: 'Apgi.normGain_antitone_other' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.normGain_antitone_other

/-- info: 'Apgi.geoTau_succ' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.geoTau_succ

/-- info: 'Apgi.gradTau_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.gradTau_zero

/-- info: 'Apgi.gradTau_one' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.gradTau_one

/-- info: 'Apgi.gradTau_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.gradTau_monotone

/-- info: 'Apgi.psiSmall_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psiSmall_zero

/-- info: 'Apgi.psiSmall_abs_lt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psiSmall_abs_lt

/-- info: 'Apgi.psiSmall_odd' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psiSmall_odd

/-- info: 'Apgi.loopGain_lt_one_of_paper3' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.loopGain_lt_one_of_paper3

/-- info: 'Apgi.loopGain_production_defaults' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.loopGain_production_defaults

/-- info: 'Apgi.loopGain_scaled_couplings' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.loopGain_scaled_couplings

/-- info: 'Apgi.kuramotoGate_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kuramotoGate_mem_Icc

/-- info: 'Apgi.msGlobal_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msGlobal_le

/-- info: 'Apgi.msGlobal_ge' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msGlobal_ge

/-- info: 'Apgi.msTarget_band' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msTarget_band
