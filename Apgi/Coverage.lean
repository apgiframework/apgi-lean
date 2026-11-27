module

public import Apgi.Core
public import Apgi.Extensions
public import Mathlib.Analysis.Complex.ExponentialBounds

/-!
# Lean statements for the remaining registered equations (scope decision (b))

Every equation in `specification/equations.json` carries at least one Lean-backed
statement. This module covers the 22 that had none after task 55: the error and
standardization rules, the EMA estimator, relative precision, the soft floor, the
step rule, the continuous and reduced threshold forms, anticipation, cost and value,
the precision ODE, level salience, aggregation, Kuramoto, the reservoir and the
thermodynamic bridges. Each theorem has a float64 twin in `test_registry_equations.py`.
-/

@[expose] public section

namespace Apgi

/-! ## EQ-ERR-1 and EQ-STD-1 -/

noncomputable def predError (x xh : ℝ) : ℝ := x - xh

theorem predError_self (x : ℝ) : predError x x = 0 := sub_self x

theorem predError_antisymm (x xh : ℝ) : predError x xh = -predError xh x := by
  unfold predError
  ring

/-- z = (ε − μ_ref)/(σ_ref + ε_stab). -/
noncomputable def standardize (ε μ σ es : ℝ) : ℝ := (ε - μ) / (σ + es)

theorem standardize_at_mean (μ σ es : ℝ) : standardize μ μ σ es = 0 := by
  simp [standardize]

/-- Errors equidistant from the reference mean standardize to opposite values. -/
theorem standardize_odd (μ σ es d : ℝ) :
    standardize (μ + d) μ σ es = -standardize (μ - d) μ σ es := by
  unfold standardize
  rw [← neg_div]
  congr 1
  ring

theorem standardize_monotone {μ σ es ε₁ ε₂ : ℝ} (hs : 0 < σ + es) (h : ε₁ ≤ ε₂) :
    standardize ε₁ μ σ es ≤ standardize ε₂ μ σ es := by
  unfold standardize
  exact div_le_div_of_nonneg_right (by linarith) hs.le

/-! ## EQ-EMA-1, EQ-EMA-2 (two-step EMA) -/

/-- α_EMA = 1 − exp(−dt/T_window). -/
noncomputable def emaAlpha (dt T : ℝ) : ℝ := 1 - Real.exp (-(dt / T))

theorem emaAlpha_mem_Ioo {dt T : ℝ} (hT : 0 < T) (hdt : 0 < dt) :
    emaAlpha dt T ∈ Set.Ioo (0 : ℝ) 1 :=
  leakGain_mem_Ioo hT hdt

noncomputable def emaMean (μ ε α : ℝ) : ℝ := (1 - α) * μ + α * ε

/-- The variance residual uses the mean μ BEFORE ε enters it. -/
noncomputable def emaVar (v μ ε α : ℝ) : ℝ := (1 - α) * v + α * (ε - μ) ^ 2

theorem emaMean_mem_Icc {lo hi μ ε α : ℝ} (hμ : μ ∈ Set.Icc lo hi) (hε : ε ∈ Set.Icc lo hi)
    (h0 : 0 ≤ α) (h1 : α ≤ 1) : emaMean μ ε α ∈ Set.Icc lo hi := by
  have h := convex_update_mem_Icc hμ hε h0 h1
  have e : emaMean μ ε α = μ + α * (ε - μ) := by
    unfold emaMean
    ring
  rw [e]
  exact h

theorem emaVar_nonneg {v μ ε α : ℝ} (hv : 0 ≤ v) (h0 : 0 ≤ α) (h1 : α ≤ 1) :
    0 ≤ emaVar v μ ε α := by
  unfold emaVar
  exact add_nonneg (mul_nonneg (by linarith) hv) (mul_nonneg h0 (sq_nonneg _))

/-- A sample at the running mean only shrinks the variance: mean-centred, not E[ε²]. -/
theorem emaVar_at_mean (v μ α : ℝ) : emaVar v μ μ α = (1 - α) * v := by
  simp [emaVar]

/-! ## EQ-PREC-REL-1 -/

noncomputable def precRel (pe pbar : ℝ) : ℝ := pe / pbar

theorem precRel_self {pbar : ℝ} (h : pbar ≠ 0) : precRel pbar pbar = 1 := div_self h

theorem precRel_mem_Icc {lo hi pe pbar : ℝ} (hb : 0 < pbar) (h : pe ∈ Set.Icc lo hi) :
    precRel pe pbar ∈ Set.Icc (lo / pbar) (hi / pbar) := by
  unfold precRel
  rw [Set.mem_Icc] at h ⊢
  exact ⟨div_le_div_of_nonneg_right h.1 hb.le, div_le_div_of_nonneg_right h.2 hb.le⟩

/-! ## EQ-FLOOR-1: the soft-threshold floor σ(−γ_sig·θ_eff) -/

/-- The floor is at most ε exactly when γ_sig·θ_eff ≥ log(1/ε − 1). -/
theorem floor_le_iff {k θ ε : ℝ} (hε0 : 0 < ε) (hε1 : ε < 1) :
    ignitionProb k 0 θ ≤ ε ↔ Real.log (1 / ε - 1) ≤ k * θ := by
  have he : -k * (0 - θ) = k * θ := by ring
  unfold ignitionProb
  rw [he]
  have hpos : 0 < 1 + Real.exp (k * θ) := by positivity
  have hq : 0 < 1 / ε - 1 := by
    rw [sub_pos, lt_div_iff₀ hε0]
    linarith
  rw [Real.log_le_iff_le_exp hq, div_le_iff₀ hpos, div_sub_one hε0.ne', div_le_iff₀ hε0]
  constructor <;> intro h <;> nlinarith

/-- R1 worked value: a floor ≤ 0.01 needs γ_sig·θ_eff ≥ log 99 ≈ 4.60. -/
theorem floor_le_one_percent_iff (k θ : ℝ) :
    ignitionProb k 0 θ ≤ 1 / 100 ↔ Real.log 99 ≤ k * θ := by
  have h := floor_le_iff (k := k) (θ := θ) (ε := 1 / 100) (by norm_num) (by norm_num)
  norm_num at h ⊢
  exact h

/-! ## EQ-STEP-1 -/

/-- The step rule dt ≤ τ/10 implies the forward-Euler precondition dt ≤ τ. -/
theorem euler_step_mem_Icc_of_stepRule {lo hi x u dt τ : ℝ} (hx : x ∈ Set.Icc lo hi)
    (hu : u ∈ Set.Icc lo hi) (hτ : 0 < τ) (hdt0 : 0 ≤ dt) (hrule : dt ≤ τ / 10) :
    x + (dt / τ) * (u - x) ∈ Set.Icc lo hi :=
  euler_step_mem_Icc hx hu hτ hdt0 (by linarith)

/-! ## EQ-ALLO-C1, EQ-ALLO-R1: continuous threshold dynamics between events -/

/-- Closed-form path between ignitions with constant drive D = η_θ[C − V]:
    θ(t) = θ* + (θ(0) − θ*)·e^{−t/τ}, θ* = θ₀ + τ·D. -/
noncomputable def alloPath (θ₀ τ D θi t : ℝ) : ℝ :=
  (θ₀ + τ * D) + (θi - (θ₀ + τ * D)) * Real.exp (-(t / τ))

/-- The closed form solves dθ/dt = −(θ − θ₀)/τ + D (EQ-ALLO-C1 with ξ_θ = 0, no event). -/
theorem alloPath_hasDerivAt {θ₀ τ D θi : ℝ} (hτ : τ ≠ 0) (t : ℝ) :
    HasDerivAt (alloPath θ₀ τ D θi) (-(alloPath θ₀ τ D θi t - θ₀) / τ + D) t := by
  have h1 : HasDerivAt (fun t : ℝ => -(t / τ)) (-(1 / τ)) t :=
    ((hasDerivAt_id t).div_const τ).neg
  have h3 := (h1.exp.const_mul (θi - (θ₀ + τ * D))).const_add (θ₀ + τ * D)
  have hf : alloPath θ₀ τ D θi =
      fun x => θ₀ + τ * D + (θi - (θ₀ + τ * D)) * Real.exp (-(x / τ)) := by
    funext x
    rfl
  rw [hf]
  refine h3.congr_deriv ?_
  beta_reduce
  field_simp
  ring

/-- EQ-ALLO-R1 is the same dynamics with D = γ_M^θ[1 − S_met] + γ_A^θ·A. -/
theorem alloReduced_hasDerivAt {θ₀ τ γM Sm γA A θi : ℝ} (hτ : τ ≠ 0) (t : ℝ) :
    HasDerivAt (alloPath θ₀ τ (γM * (1 - Sm) + γA * A) θi)
      (-(alloPath θ₀ τ (γM * (1 - Sm) + γA * A) θi t - θ₀) / τ + (γM * (1 - Sm) + γA * A)) t :=
  alloPath_hasDerivAt hτ t

/-! ## EQ-ANT-1 -/

/-- Deterministic anticipation: Ĉ(t) = C(t + T_ant). -/
noncomputable def anticipated (C : ℝ → ℝ) (Tant t : ℝ) : ℝ := C (t + Tant)

/-- T_ant = 0 recovers the reactive cost of EQ-ALLO-1. -/
theorem anticipated_zero (C : ℝ → ℝ) (t : ℝ) : anticipated C 0 t = C t := by
  simp [anticipated]

/-! ## EQ-COST-1, EQ-VAL-1 -/

noncomputable def costC (c1 c2 c3 S Bp a : ℝ) : ℝ := c1 * S + c2 * Bp + c3 * a

noncomputable def valueV (v1 v2 ze zi : ℝ) : ℝ := v1 * |ze| + v2 * |zi|

theorem valueV_nonneg {v1 v2 : ℝ} (h1 : 0 ≤ v1) (h2 : 0 ≤ v2) (ze zi : ℝ) :
    0 ≤ valueV v1 v2 ze zi := by
  unfold valueV
  positivity

/-- With c₂ ≥ 0 the previous ignition never lowers the cost. -/
theorem costC_monotone_ignition {c1 c2 c3 S a B₁ B₂ : ℝ} (hc : 0 ≤ c2) (h : B₁ ≤ B₂) :
    costC c1 c2 c3 S B₁ a ≤ costC c1 c2 c3 S B₂ a := by
  unfold costC
  nlinarith [mul_le_mul_of_nonneg_left h hc]

/-- Greater information value never raises the next threshold (η_θ ≥ 0). -/
theorem thresholdStep_antitone_value {θ θ₀ η C V₁ V₂ δ B dt τ : ℝ} (hη : 0 ≤ η) (h : V₁ ≤ V₂) :
    thresholdStep θ θ₀ η C V₂ δ B dt τ ≤ thresholdStep θ θ₀ η C V₁ δ B dt τ :=
  thresholdStep_monotone_drive hη (by linarith)

/-! ## EQ-PREC-ODE-1 -/

/-- dΠ_ℓ/dt = −Π_ℓ/τ_Π + α_Π|ε_ℓ| + C_down(Π_{ℓ+1} − Π_ℓ) + C_up·ψ(z_{ℓ−1}). -/
noncomputable def precOdeRate (p eps pup zdown τ α cd cu γ : ℝ) : ℝ :=
  -p / τ + α * |eps| + cd * (pup - p) + cu * psiSmall γ zdown

/-- The rate is strictly decreasing in Π_ℓ (τ_Π > 0, C_down ≥ 0): one equilibrium per input. -/
theorem precOdeRate_strictAnti {eps pup zdown τ α cd cu γ : ℝ} (hτ : 0 < τ) (hcd : 0 ≤ cd) :
    StrictAnti (fun p => precOdeRate p eps pup zdown τ α cd cu γ) := by
  intro a b hab
  have e : ∀ p : ℝ, -p / τ = -(p * τ⁻¹) := fun p => by ring
  have hi : 0 < τ⁻¹ := inv_pos.2 hτ
  simp only [precOdeRate, e]
  nlinarith [mul_lt_mul_of_pos_right hab hi, mul_le_mul_of_nonneg_left hab.le hcd]

/-- With α_Π = 0, equal neighbours and zero lower-level error, the ODE is pure decay. -/
theorem precOdeRate_pure_decay (p eps τ cd cu γ : ℝ) :
    precOdeRate p eps p 0 τ 0 cd cu γ = -p / τ := by
  simp [precOdeRate, psiSmall]

/-! ## EQ-MS-1 (EQ-MS-3 shares the convex bounds msGlobal_le / msGlobal_ge) -/

/-- S_inst,ℓ = Π_rel,ℓ·|Ψ(z_ℓ)|_ex·Γ_ℓ. -/
noncomputable def msDrive (prel psiEx gate : ℝ) : ℝ := prel * psiEx * gate

/-- Magnitude, not direction, drives ignition: opposite-signed errors give the same level
    salience under the symmetric Ψ. -/
theorem msDrive_sign_symmetric (prel α γ m gate z : ℝ) :
    msDrive prel (|psi α α γ γ (-z)| - m) gate = msDrive prel (|psi α α γ γ z| - m) gate := by
  rw [psi_odd_of_symmetric, abs_neg]

/-- Γ = 1 recovers salience without synchrony gating. -/
theorem msDrive_gate_one (prel x : ℝ) : msDrive prel x 1 = prel * x := by
  simp [msDrive]

theorem msDrive_gate_monotone {prel x g₁ g₂ : ℝ} (hp : 0 ≤ prel) (hx : 0 ≤ x) (h : g₁ ≤ g₂) :
    msDrive prel x g₁ ≤ msDrive prel x g₂ := by
  unfold msDrive
  exact mul_le_mul_of_nonneg_left h (mul_nonneg hp hx)

/-! ## EQ-KUR-2 -/

/-- Within-level Kuramoto rate ω + (K/N)·Σ_j sin(φ_j − φ_i). -/
noncomputable def kurRate {n : ℕ} (φ : Fin n → ℝ) (ω K : ℝ) (i : Fin n) : ℝ :=
  ω + K / n * ∑ j, Real.sin (φ j - φ i)

/-- A synchronized level drifts at its natural frequency: the coupling term vanishes. -/
theorem kurRate_synchronized {n : ℕ} (c ω K : ℝ) (i : Fin n) :
    kurRate (fun _ => c) ω K i = ω := by
  simp [kurRate]

/-! ## EQ-RES-1, EQ-RES-2 -/

noncomputable def resStep {n m : ℕ} (W : Fin n → Fin n → ℝ) (Win : Fin n → Fin m → ℝ)
    (u : Fin m → ℝ) (x : Fin n → ℝ) (i : Fin n) : ℝ :=
  Real.tanh (∑ j, W i j * x j + ∑ k, Win i k * u k)

/-- The tanh reservoir state is bounded in (−1, 1) componentwise for any weights and input. -/
theorem resStep_abs_lt {n m : ℕ} (W : Fin n → Fin n → ℝ) (Win : Fin n → Fin m → ℝ)
    (u : Fin m → ℝ) (x : Fin n → ℝ) (i : Fin n) : |resStep W Win u x i| < 1 :=
  Real.abs_tanh_lt_one _

/-- S_res = [W_outᵀx]₊. -/
noncomputable def resReadout {n : ℕ} (w x : Fin n → ℝ) : ℝ := max 0 (∑ i, w i * x i)

/-- Rectification keeps the reservoir from subtracting from S. -/
theorem resReadout_nonneg {n : ℕ} (w x : Fin n → ℝ) : 0 ≤ resReadout w x := le_max_left _ _

/-! ## EQ-LAND-1, EQ-BR-1, EQ-BR-2, EQ-BR-3 -/

/-- E_L = k_B·T·ln 2. -/
noncomputable def landauerE (kB T : ℝ) : ℝ := kB * T * Real.log 2

theorem landauerE_pos {kB T : ℝ} (hk : 0 < kB) (hT : 0 < T) : 0 < landauerE kB T := by
  unfold landauerE
  have := Real.log_pos (by norm_num : (1 : ℝ) < 2)
  positivity

/-- The registry value 2.97 × 10⁻²¹ J at 310 K holds within its relative tolerance 0.005. -/
theorem landauer_310K_within_tolerance :
    |landauerE 1.380649e-23 310 - 2.97e-21| ≤ 0.005 * 2.97e-21 := by
  unfold landauerE
  have h1 := Real.log_two_gt_d9
  have h2 := Real.log_two_lt_d9
  rw [abs_le]
  constructor <;> nlinarith

/-- KC-LANDAUER-287: 2.87 × 10⁻²¹ J is the 300 K value, below 2.88 × 10⁻²¹ J. -/
theorem landauer_300K_below : landauerE 1.380649e-23 300 < 2.88e-21 := by
  unfold landauerE
  have h2 := Real.log_two_lt_d9
  nlinarith

/-- e_bit = E_event/N_b. -/
noncomputable def energyPerBit (E Nb : ℝ) : ℝ := E / Nb

/-- κ = e_bit/|ΔG_ATP|, a molecule count per bit. -/
noncomputable def kappaATP (ebit dG : ℝ) : ℝ := ebit / |dG|

theorem kappaATP_nonneg {ebit : ℝ} (h : 0 ≤ ebit) (dG : ℝ) : 0 ≤ kappaATP ebit dG :=
  div_nonneg h (abs_nonneg dG)

theorem kappa_of_energy (E Nb dG : ℝ) : kappaATP (energyPerBit E Nb) dG = E / (Nb * |dG|) := by
  unfold kappaATP energyPerBit
  rw [div_div]

/-- R_L = E_event/(N_erase·E_L). -/
noncomputable def erasureRatio (E N EL : ℝ) : ℝ := E / (N * EL)

/-- R_L ≥ 1 exactly when the event energy meets the Landauer bound for N_erase erasures. -/
theorem erasureRatio_ge_one_iff {E N EL : ℝ} (hN : 0 < N) (hL : 0 < EL) :
    1 ≤ erasureRatio E N EL ↔ N * EL ≤ E := by
  unfold erasureRatio
  exact one_le_div (mul_pos hN hL)

end Apgi

end

/-! ## Axiom audit (self-enforcing). -/

/-- info: 'Apgi.predError_self' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.predError_self

/-- info: 'Apgi.predError_antisymm' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.predError_antisymm

/-- info: 'Apgi.standardize_at_mean' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.standardize_at_mean

/-- info: 'Apgi.standardize_odd' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.standardize_odd

/-- info: 'Apgi.standardize_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.standardize_monotone

/-- info: 'Apgi.emaAlpha_mem_Ioo' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.emaAlpha_mem_Ioo

/-- info: 'Apgi.emaMean_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.emaMean_mem_Icc

/-- info: 'Apgi.emaVar_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.emaVar_nonneg

/-- info: 'Apgi.emaVar_at_mean' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.emaVar_at_mean

/-- info: 'Apgi.precRel_self' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precRel_self

/-- info: 'Apgi.precRel_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precRel_mem_Icc

/-- info: 'Apgi.floor_le_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.floor_le_iff

/-- info: 'Apgi.floor_le_one_percent_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.floor_le_one_percent_iff

/-- info: 'Apgi.euler_step_mem_Icc_of_stepRule' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.euler_step_mem_Icc_of_stepRule

/-- info: 'Apgi.alloPath_hasDerivAt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.alloPath_hasDerivAt

/-- info: 'Apgi.alloReduced_hasDerivAt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.alloReduced_hasDerivAt

/-- info: 'Apgi.anticipated_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.anticipated_zero

/-- info: 'Apgi.valueV_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.valueV_nonneg

/-- info: 'Apgi.costC_monotone_ignition' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.costC_monotone_ignition

/-- info: 'Apgi.thresholdStep_antitone_value' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_antitone_value

/-- info: 'Apgi.precOdeRate_strictAnti' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precOdeRate_strictAnti

/-- info: 'Apgi.precOdeRate_pure_decay' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precOdeRate_pure_decay

/-- info: 'Apgi.msDrive_sign_symmetric' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msDrive_sign_symmetric

/-- info: 'Apgi.msDrive_gate_one' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msDrive_gate_one

/-- info: 'Apgi.msDrive_gate_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.msDrive_gate_monotone

/-- info: 'Apgi.kurRate_synchronized' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kurRate_synchronized

/-- info: 'Apgi.resStep_abs_lt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.resStep_abs_lt

/-- info: 'Apgi.resReadout_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.resReadout_nonneg

/-- info: 'Apgi.landauerE_pos' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.landauerE_pos

/-- info: 'Apgi.landauer_310K_within_tolerance' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.landauer_310K_within_tolerance

/-- info: 'Apgi.landauer_300K_below' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.landauer_300K_below

/-- info: 'Apgi.kappaATP_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappaATP_nonneg

/-- info: 'Apgi.kappa_of_energy' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_of_energy

/-- info: 'Apgi.erasureRatio_ge_one_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.erasureRatio_ge_one_iff
