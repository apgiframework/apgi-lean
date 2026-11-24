module

public import Apgi.Pilot

/-!
# APGI dynamics: hazard, leaky integrator, NE clamp, allostatic step, Ψ, Πⁱ_eff

Targeted theorems chosen under decision (b) of `docs/REMAINING-TASKS.md`
(task 11): one Lean-backed statement for every equation registered in
specification 0.3.0, plus the cusp converse.

Each theorem is linked to an equation ID in `specification/equations.json` and
has a float64 twin in `verification/python/test_twins.py`. The registry constant
`ne_bound` (0.5) comes from the generated `Apgi/Spec.lean`.
-/

@[expose] public section

namespace Apgi

/-! ## Hazard ignition (EQ-HAZARD-1, Math Spec Eq. 35)
Bₜ is a propensity, not a per-step probability. Events follow the hazard
r_max·Bₜ, so the per-step probability is 1 − exp(−r_max·Bₜ·dt). -/

/-- Per-step ignition probability under the dt-invariant hazard. -/
noncomputable def hazardProb (r B dt : ℝ) : ℝ := 1 - Real.exp (-(r * B * dt))

/-- With r_max, Bₜ, dt ≥ 0 the hazard is a probability. -/
theorem hazardProb_mem_Icc {r B dt : ℝ} (hr : 0 ≤ r) (hB : 0 ≤ B) (hdt : 0 ≤ dt) :
    hazardProb r B dt ∈ Set.Icc (0 : ℝ) 1 := by
  have h0 : 0 ≤ r * B * dt := by positivity
  have hle : Real.exp (-(r * B * dt)) ≤ 1 := Real.exp_le_one_iff.2 (by linarith)
  have hpos : 0 < Real.exp (-(r * B * dt)) := Real.exp_pos _
  unfold hazardProb
  rw [Set.mem_Icc]
  constructor <;> linarith

/-- Survival probabilities of consecutive steps multiply into the survival
    probability of the combined step. -/
theorem hazard_survival_add (r B dt₁ dt₂ : ℝ) :
    (1 - hazardProb r B dt₁) * (1 - hazardProb r B dt₂) =
      1 - hazardProb r B (dt₁ + dt₂) := by
  unfold hazardProb
  rw [sub_sub_cancel, sub_sub_cancel, sub_sub_cancel, ← Real.exp_add]
  congr 1
  ring

/-- Task 26 (backs PD-HAZARD): two steps of dt equal one step of 2·dt,
    (1 − p_dt)² = 1 − p_2dt. -/
theorem hazard_two_steps (r B dt : ℝ) :
    (1 - hazardProb r B dt) ^ 2 = 1 - hazardProb r B (2 * dt) := by
  rw [sq, hazard_survival_add, two_mul]

/-- dt-invariance in general: n steps of dt equal one step of n·dt. -/
theorem hazard_n_steps (r B dt : ℝ) (n : ℕ) :
    (1 - hazardProb r B dt) ^ n = 1 - hazardProb r B (n * dt) := by
  induction n with
  | zero => simp [hazardProb]
  | succ k ih =>
    rw [pow_succ, ih, hazard_survival_add,
      show ((k + 1 : ℕ) : ℝ) * dt = (k : ℝ) * dt + dt by push_cast; ring]

/-- A higher propensity cannot lower the per-step ignition probability. -/
theorem hazardProb_monotone_propensity {r dt B₁ B₂ : ℝ} (hr : 0 ≤ r) (hdt : 0 ≤ dt)
    (h : B₁ ≤ B₂) : hazardProb r B₁ dt ≤ hazardProb r B₂ dt := by
  unfold hazardProb
  have h1 : r * B₁ * dt ≤ r * B₂ * dt :=
    mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left h hr) hdt
  have h2 := Real.exp_le_exp.2 (neg_le_neg h1)
  linarith

/-- CL-1 carried through the hazard: with the logistic propensity
    Bₜ = σ(γ_sig·(S − θ)), raising θ cannot raise the per-step ignition
    probability. -/
theorem hazard_antitone_threshold {k r dt S θ₁ θ₂ : ℝ} (hk : 0 ≤ k) (hr : 0 ≤ r)
    (hdt : 0 ≤ dt) (h : θ₁ ≤ θ₂) :
    hazardProb r (ignitionProb k S θ₂) dt ≤ hazardProb r (ignitionProb k S θ₁) dt :=
  hazardProb_monotone_propensity hr hdt (ignitionProb_antitone_threshold hk h)

/-! ## Leaky integrator (EQ-LEAK-1, Math Spec Eq. 23–24)
S(t+1) = (1 − λ)·S(t) + λ·S_inst(t) with λ = 1 − exp(−dt/τ_S). -/

/-- Exact leaky-integrator gain λ = 1 − exp(−dt/τ_S). -/
noncomputable def leakGain (dt τ : ℝ) : ℝ := 1 - Real.exp (-(dt / τ))

/-- One leaky-integrator step with gain `lam`. -/
noncomputable def leakStep (S Sinst lam : ℝ) : ℝ := (1 - lam) * S + lam * Sinst

/-- Task 27: λ ∈ (0, 1) for every dt > 0, as Math Spec p18 requires. -/
theorem leakGain_mem_Ioo {dt τ : ℝ} (hτ : 0 < τ) (hdt : 0 < dt) :
    leakGain dt τ ∈ Set.Ioo (0 : ℝ) 1 := by
  have h0 : 0 < dt / τ := div_pos hdt hτ
  have hlt : Real.exp (-(dt / τ)) < 1 := by
    rw [← Real.exp_zero]
    exact Real.exp_lt_exp.2 (by linarith)
  have hpos : 0 < Real.exp (-(dt / τ)) := Real.exp_pos _
  unfold leakGain
  rw [Set.mem_Ioo]
  constructor <;> linarith

/-- The accumulated signal stays inside any interval containing S and S_inst,
    for every dt ≥ 0 (reuses `decayGain_mem_Icc`). -/
theorem leak_step_mem_Icc {lo hi S Sinst dt τ : ℝ} (hS : S ∈ Set.Icc lo hi)
    (hu : Sinst ∈ Set.Icc lo hi) (hτ : 0 < τ) (hdt : 0 ≤ dt) :
    leakStep S Sinst (leakGain dt τ) ∈ Set.Icc lo hi := by
  have hg := decayGain_mem_Icc hτ hdt
  rw [Set.mem_Icc] at hg
  have h := convex_update_mem_Icc hS hu hg.1 hg.2
  have e : leakStep S Sinst (leakGain dt τ) =
      S + (1 - Real.exp (-(dt / τ))) * (Sinst - S) := by
    unfold leakStep leakGain
    ring
  rw [e]
  exact h

/-- With S_inst held over the step, two steps of dt equal one step of 2·dt:
    the exact gain makes the integrator dt-invariant (Math Spec p18). -/
theorem leak_two_steps (S u dt τ : ℝ) :
    leakStep (leakStep S u (leakGain dt τ)) u (leakGain dt τ) =
      leakStep S u (leakGain (2 * dt) τ) := by
  have h : Real.exp (-(2 * dt / τ)) = Real.exp (-(dt / τ)) * Real.exp (-(dt / τ)) := by
    rw [← Real.exp_add]
    congr 1
    ring
  unfold leakStep leakGain
  rw [h]
  ring

/-! ## NE sub-dominance clamp (EQ-NE-1, Math Spec §4.4)
If |γ_NE|·g_NE > 0.5, rescale g_NE ← 0.5/|γ_NE| before θ_eff is computed. -/

/-- The hard clamp on the noradrenergic gain. `ne_bound` = 0.5 (registry). -/
noncomputable def neClamp (γ g : ℝ) : ℝ := if |γ| * g ≤ ne_bound then g else ne_bound / |γ|

theorem neClamp_nonneg {γ g : ℝ} (hg : 0 ≤ g) : 0 ≤ neClamp γ g := by
  unfold neClamp
  split_ifs
  · exact hg
  · exact div_nonneg (by norm_num [ne_bound]) (abs_nonneg γ)

/-- After the clamp, |γ_NE|·g_NE ≤ 0.5 holds for either sign of γ_NE. -/
theorem neClamp_bound (γ g : ℝ) : |γ| * neClamp γ g ≤ ne_bound := by
  unfold neClamp
  split_ifs with h
  · exact h
  · have hγ : 0 < |γ| := by
      rcases (abs_nonneg γ).lt_or_eq with h' | h'
      · exact h'
      · exfalso
        apply h
        rw [← h', zero_mul]
        norm_num [ne_bound]
    have e : |γ| * (ne_bound / |γ|) = ne_bound := by field_simp
    exact le_of_eq e

/-- The clamp is the identity on gains that already respect the bound. -/
theorem neClamp_of_le {γ g : ℝ} (h : |γ| * g ≤ ne_bound) : neClamp γ g = g := by
  simp [neClamp, h]

/-- The NE factor of θ_eff stays in [1 − 0.5, 1 + 0.5]. -/
theorem neFactor_mem_Icc {γ g : ℝ} (hg : 0 ≤ g) :
    1 + γ * neClamp γ g ∈ Set.Icc (1 - ne_bound) (1 + ne_bound) := by
  have hb := neClamp_bound γ g
  have hn := neClamp_nonneg (γ := γ) hg
  have habs : |γ * neClamp γ g| ≤ ne_bound := by
    rw [abs_mul, abs_of_nonneg hn]
    exact hb
  obtain ⟨h1, h2⟩ := abs_le.1 habs
  rw [Set.mem_Icc]
  constructor <;> linarith

/-- With the registry value, 1 + γ_NE·g_NE ∈ [0.5, 1.5] (Notation Appendix p9). -/
theorem neFactor_band {γ g : ℝ} (hg : 0 ≤ g) :
    1 / 2 ≤ 1 + γ * neClamp γ g ∧ 1 + γ * neClamp γ g ≤ 3 / 2 := by
  have h := neFactor_mem_Icc (γ := γ) hg
  rw [Set.mem_Icc] at h
  have hb : ne_bound = 1 / 2 := rfl
  rw [hb] at h
  constructor <;> linarith [h.1, h.2]

/-- NE modulation never drives a positive threshold to zero or below. -/
theorem neThreshold_pos {θ γ g : ℝ} (hθ : 0 < θ) (hg : 0 ≤ g) :
    0 < θ * (1 + γ * neClamp γ g) :=
  mul_pos hθ (by linarith [(neFactor_band (γ := γ) hg).1])

/-! ## Allostatic threshold step (EQ-ALLO-1, Math Spec Eq. 26 → Eq. 32 → §4.5)
θₜ₊₁ = θₜ + η_θ·[C − V] + δ_reset·Bₜ, then exact decay toward θ₀, then the
floor clamp. -/

/-- Math Spec Eq. 26, the canonical allostatic update. -/
noncomputable def allostaticStep (θ η C V δ B : ℝ) : ℝ := θ + η * (C - V) + δ * B

/-- One full threshold step: Eq. 26, then the exact decay of Eq. 32, then the floor. -/
noncomputable def thresholdStep (θ θ₀ η C V δ B dt τ : ℝ) : ℝ :=
  max θ_floor (decayStep (allostaticStep θ η C V δ B) θ₀ dt τ)

/-- Exact decay is monotone in the pre-decay threshold. -/
theorem decayStep_monotone {θ₁ θ₂ : ℝ} (θ₀ dt τ : ℝ) (h : θ₁ ≤ θ₂) :
    decayStep θ₁ θ₀ dt τ ≤ decayStep θ₂ θ₀ dt τ := by
  unfold decayStep
  have hpos := Real.exp_pos (-(dt / τ))
  have := mul_le_mul_of_nonneg_right (sub_le_sub_right h θ₀) hpos.le
  linarith

/-- The full step respects the positivity floor for every input. -/
theorem thresholdStep_floor (θ θ₀ η C V δ B dt τ : ℝ) :
    θ_floor ≤ thresholdStep θ θ₀ η C V δ B dt τ :=
  le_max_left _ _

/-- With δ_reset ≥ 0, an ignition event never lowers the next threshold. -/
theorem thresholdStep_monotone_ignition {θ θ₀ η C V δ B₁ B₂ dt τ : ℝ} (hδ : 0 ≤ δ)
    (hB : B₁ ≤ B₂) :
    thresholdStep θ θ₀ η C V δ B₁ dt τ ≤ thresholdStep θ θ₀ η C V δ B₂ dt τ := by
  unfold thresholdStep
  apply max_le_max (le_refl _)
  apply decayStep_monotone
  unfold allostaticStep
  have := mul_le_mul_of_nonneg_left hB hδ
  linarith

/-- With η_θ ≥ 0, a larger cost-minus-value drive never lowers the next threshold. -/
theorem thresholdStep_monotone_drive {θ θ₀ η C₁ V₁ C₂ V₂ δ B dt τ : ℝ} (hη : 0 ≤ η)
    (h : C₁ - V₁ ≤ C₂ - V₂) :
    thresholdStep θ θ₀ η C₁ V₁ δ B dt τ ≤ thresholdStep θ θ₀ η C₂ V₂ δ B dt τ := by
  unfold thresholdStep
  apply max_le_max (le_refl _)
  apply decayStep_monotone
  unfold allostaticStep
  have := mul_le_mul_of_nonneg_left h hη
  linarith

/-! ## Signed valence transform Ψ(z) (EQ-PSI-1, Math Spec Eq. 21) -/

/-- Ψ(z) = α⁺·tanh(γ⁺·z) for z ≥ 0 and α⁻·tanh(γ⁻·z) for z < 0. -/
noncomputable def psi (αp αm γp γm z : ℝ) : ℝ :=
  if 0 ≤ z then αp * Real.tanh (γp * z) else αm * Real.tanh (γm * z)

/-- Ψ is bounded by the larger amplitude gain: saturation is strict. -/
theorem psi_abs_lt {αp αm γp γm : ℝ} (hp : 0 < αp) (hm : 0 < αm) (z : ℝ) :
    |psi αp αm γp γm z| < max αp αm := by
  unfold psi
  split_ifs
  · rw [abs_mul, abs_of_pos hp]
    calc αp * |Real.tanh (γp * z)| < αp * 1 :=
          mul_lt_mul_of_pos_left (Real.abs_tanh_lt_one _) hp
      _ = αp := mul_one _
      _ ≤ max αp αm := le_max_left _ _
  · rw [abs_mul, abs_of_pos hm]
    calc αm * |Real.tanh (γm * z)| < αm * 1 :=
          mul_lt_mul_of_pos_left (Real.abs_tanh_lt_one _) hm
      _ = αm := mul_one _
      _ ≤ max αp αm := le_max_right _ _

/-- With α⁺ = α⁻ and γ⁺ = γ⁻ the symmetric form α·tanh(γ·z) is recovered. -/
theorem psi_symmetric (α γ z : ℝ) : psi α α γ γ z = α * Real.tanh (γ * z) := by
  unfold psi
  split_ifs <;> rfl

/-- The symmetric form is odd in z (Math Spec p17: the signed transform is odd,
    so opposite-signed channels can cancel). -/
theorem psi_odd_of_symmetric (α γ z : ℝ) : psi α α γ γ (-z) = -psi α α γ γ z := by
  rw [psi_symmetric, psi_symmetric, mul_neg, Real.tanh_neg, mul_neg]

/-! ## Somatic-marker precision (EQ-PREC-SM-1)
Πⁱ_eff = g_NE·Πⁱ_baseline·exp(β_SM·M̂(c,a)), clamped to [Π_min, Π_max].
(`Π` is reserved notation in Mathlib, hence `pb`.) -/

/-- Effective interoceptive precision before the clamp. -/
noncomputable def precEff (gNE pb βSM M : ℝ) : ℝ := gNE * pb * Real.exp (βSM * M)

/-- The hard precision clamp. -/
noncomputable def precClamp (lo hi x : ℝ) : ℝ := max lo (min hi x)

theorem precEff_nonneg {gNE pb : ℝ} (hg : 0 ≤ gNE) (hp : 0 ≤ pb) (βSM M : ℝ) :
    0 ≤ precEff gNE pb βSM M := by
  unfold precEff
  positivity

/-- With β_SM ≥ 0, a higher somatic-marker value never lowers precision. -/
theorem precEff_monotone_marker {gNE pb βSM M₁ M₂ : ℝ} (hg : 0 ≤ gNE) (hp : 0 ≤ pb)
    (hβ : 0 ≤ βSM) (h : M₁ ≤ M₂) : precEff gNE pb βSM M₁ ≤ precEff gNE pb βSM M₂ := by
  unfold precEff
  apply mul_le_mul_of_nonneg_left _ (mul_nonneg hg hp)
  exact Real.exp_le_exp.2 (mul_le_mul_of_nonneg_left h hβ)

/-- The clamp lands in [Π_min, Π_max] whenever Π_min ≤ Π_max. -/
theorem precClamp_mem_Icc {lo hi : ℝ} (h : lo ≤ hi) (x : ℝ) :
    precClamp lo hi x ∈ Set.Icc lo hi := by
  unfold precClamp
  rw [Set.mem_Icc]
  exact ⟨le_max_left _ _, max_le h (min_le_left _ _)⟩

/-! ## Cusp converse (EQ-CUSP-1, task 28)
Three distinct equilibria force 4a³ + 27θ² < 0, so the discriminant rule is an
"if and only if". -/

/-- Three distinct equilibria imply a negative discriminant. By Vieta the roots
    sum to zero, and 4a³ + 27θ² = −((x₁ − x₂)(x₁ − x₃)(x₂ − x₃))². -/
theorem cusp_three_equilibria_converse {a θ x₁ x₂ x₃ : ℝ} (h12 : x₁ < x₂) (h23 : x₂ < x₃)
    (h₁ : x₁ ^ 3 + a * x₁ + θ = 0) (h₂ : x₂ ^ 3 + a * x₂ + θ = 0)
    (h₃ : x₃ ^ 3 + a * x₃ + θ = 0) :
    4 * a ^ 3 + 27 * θ ^ 2 < 0 := by
  have hq : ∀ {u v : ℝ}, u ≠ v → u ^ 3 + a * u + θ = 0 → v ^ 3 + a * v + θ = 0 →
      u ^ 2 + u * v + v ^ 2 + a = 0 := by
    intro u v huv hu hv
    have key : (u - v) * (u ^ 2 + u * v + v ^ 2 + a) = 0 := by linear_combination hu - hv
    rcases mul_eq_zero.1 key with h | h
    · exact absurd (sub_eq_zero.1 h) huv
    · exact h
  have e12 := hq h12.ne h₁ h₂
  have e13 := hq (h12.trans h23).ne h₁ h₃
  have hs : x₁ + x₂ + x₃ = 0 := by
    have key : (x₂ - x₃) * (x₁ + x₂ + x₃) = 0 := by linear_combination e12 - e13
    rcases mul_eq_zero.1 key with h | h
    · exact absurd (sub_eq_zero.1 h) h23.ne
    · exact h
  have hx3 : x₃ = -x₁ - x₂ := by linarith
  have ha : a = -(x₁ ^ 2 + x₁ * x₂ + x₂ ^ 2) := by linarith
  have hθ : θ = -(x₁ ^ 3 + a * x₁) := by linarith
  have hD : 4 * a ^ 3 + 27 * θ ^ 2 = -((x₁ - x₂) * (x₁ - x₃) * (x₂ - x₃)) ^ 2 := by
    rw [hθ, ha, hx3]
    ring
  have hne : (x₁ - x₂) * (x₁ - x₃) * (x₂ - x₃) ≠ 0 :=
    mul_ne_zero (mul_ne_zero (sub_ne_zero.2 h12.ne) (sub_ne_zero.2 (h12.trans h23).ne))
      (sub_ne_zero.2 h23.ne)
  have hpos : 0 < ((x₁ - x₂) * (x₁ - x₃) * (x₂ - x₃)) ^ 2 :=
    lt_of_le_of_ne (sq_nonneg _) (Ne.symm (pow_ne_zero 2 hne))
  linarith

/-- The discriminant rule as an equivalence (claim CL-5 strengthened). The
    condition 4a³ + 27θ² < 0 already forces a < 0. -/
theorem cusp_three_equilibria_iff (a θ : ℝ) :
    (∃ x₁ x₂ x₃ : ℝ, x₁ < x₂ ∧ x₂ < x₃ ∧
      x₁ ^ 3 + a * x₁ + θ = 0 ∧ x₂ ^ 3 + a * x₂ + θ = 0 ∧ x₃ ^ 3 + a * x₃ + θ = 0) ↔
      4 * a ^ 3 + 27 * θ ^ 2 < 0 := by
  constructor
  · rintro ⟨x₁, x₂, x₃, h12, h23, h₁, h₂, h₃⟩
    exact cusp_three_equilibria_converse h12 h23 h₁ h₂ h₃
  · intro hd
    have ha : a < 0 := by
      by_contra h
      have h' : 0 ≤ a := not_lt.1 h
      nlinarith [pow_nonneg h' 3, sq_nonneg θ]
    exact cusp_three_equilibria ha hd

end Apgi

end

/-! ## Axiom audit (self-enforcing), as in `Apgi/Pilot.lean`. -/

/-- info: 'Apgi.hazardProb_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazardProb_mem_Icc

/-- info: 'Apgi.hazard_survival_add' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazard_survival_add

/-- info: 'Apgi.hazard_two_steps' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazard_two_steps

/-- info: 'Apgi.hazard_n_steps' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazard_n_steps

/-- info: 'Apgi.hazardProb_monotone_propensity' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazardProb_monotone_propensity

/-- info: 'Apgi.hazard_antitone_threshold' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazard_antitone_threshold

/-- info: 'Apgi.leakGain_mem_Ioo' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.leakGain_mem_Ioo

/-- info: 'Apgi.leak_step_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.leak_step_mem_Icc

/-- info: 'Apgi.leak_two_steps' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.leak_two_steps

/-- info: 'Apgi.neClamp_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neClamp_nonneg

/-- info: 'Apgi.neClamp_bound' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neClamp_bound

/-- info: 'Apgi.neClamp_of_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neClamp_of_le

/-- info: 'Apgi.neFactor_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neFactor_mem_Icc

/-- info: 'Apgi.neFactor_band' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neFactor_band

/-- info: 'Apgi.neThreshold_pos' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neThreshold_pos

/-- info: 'Apgi.decayStep_monotone' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.decayStep_monotone

/-- info: 'Apgi.thresholdStep_floor' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_floor

/-- info: 'Apgi.thresholdStep_monotone_ignition' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_monotone_ignition

/-- info: 'Apgi.thresholdStep_monotone_drive' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_monotone_drive

/-- info: 'Apgi.psi_abs_lt' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psi_abs_lt

/-- info: 'Apgi.psi_symmetric' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psi_symmetric

/-- info: 'Apgi.psi_odd_of_symmetric' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.psi_odd_of_symmetric

/-- info: 'Apgi.precEff_nonneg' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precEff_nonneg

/-- info: 'Apgi.precEff_monotone_marker' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precEff_monotone_marker

/-- info: 'Apgi.precClamp_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precClamp_mem_Icc

/-- info: 'Apgi.cusp_three_equilibria_converse' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_three_equilibria_converse

/-- info: 'Apgi.cusp_three_equilibria_iff' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.cusp_three_equilibria_iff
