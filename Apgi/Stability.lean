module

public import Apgi.Pipeline

/-!
# TC-13: numerical stability of the canonical pipeline (SSOT §23)

SSOT §23 TC-13: "dt obeys EQ-STEP-1; overflow, NaN and division-by-zero have defined
handling; NaN/Inf rejected."

What is proved here, over ℝ:
* **Division by zero cannot occur.** Along every trajectory from an invariant state, every
  denominator of the step is positive: σ_ref + ε_stab and Σ + ε_stab in both channels
  (`traj_denoms_pos`), given ε_stab > 0 and an estimator whose spread is nonnegative.
* **Finite amplification.** The standardized error is at most |ε − μ_ref|/ε_stab
  (`standardize_abs_le`), the raw precision at most 1/ε_stab (`precRaw_le`), and the drive
  obeys an explicit upper bound in the current errors (`pipeLog_Sinst_le`). With the
  unconditional lower bound of `pipeLog_Sinst_ge`, S is two-sided bounded on every
  trajectory whose errors are bounded (`traj_S_mem_Icc`). The amplification factor
  Π_max/(Π̄·ε_stab) (10⁹ at CFG-CORE) is the reason float64 overflow is reachable at all.
* **EQ-STEP-1 bounds the per-step gain**: dt ≤ τ/10 ⇒ 1 − exp(−dt/τ) ≤ 1/10, for the leak λ
  and for α_EMA alike (`stepRule_gain_le`).

What is NOT proved here: overflow, NaN and Inf are properties of float64, not of ℝ. Their
defined handling (rejection, atomicity) is a computational requirement, tested in
verification/python/test_stability.py (reference) and test_production.py (production).
-/

@[expose] public section

namespace Apgi

/-- The reference estimator never reports a negative spread (true of any standard deviation,
    in particular the sliding-window σ of `apgi_ref._ref_stats`). -/
def RefEstimator.SdNonneg {W : Type*} (R : RefEstimator W) : Prop := ∀ w, 0 ≤ R.sd w

/-! ## Division by zero -/

/-- TC-13: along every trajectory every denominator of the step is positive. -/
theorem traj_denoms_pos {W : Type*} (R : RefEstimator W) {p : PipeParams}
    (hp : PipeAdmissible p) (hsd : R.SdNonneg) (hes : 0 < p.epsStab) {L : ℝ}
    (hL : L ≤ driveLower p) {s₀ : PipeState W} (h₀ : PipeInv L s₀) (xe xi u : ℕ → ℝ) (n : ℕ) :
    0 < R.sd (traj R p s₀ xe xi u n).e.ref + p.epsStab ∧
      0 < R.sd (traj R p s₀ xe xi u n).i.ref + p.epsStab ∧
      0 < (traj R p s₀ xe xi u n).e.s2 + p.epsStab ∧
      0 < (traj R p s₀ xe xi u n).i.s2 + p.epsStab := by
  have hi := traj_inv R hp hL h₀ xe xi u n
  refine ⟨?_, ?_, ?_, ?_⟩
  · linarith [hsd (traj R p s₀ xe xi u n).e.ref]
  · linarith [hsd (traj R p s₀ xe xi u n).i.ref]
  · linarith [hi.s2e]
  · linarith [hi.s2i]

/-! ## Finite amplification -/

/-- EQ-STD-1: |z| ≤ |ε − μ_ref|/ε_stab whenever σ_ref ≥ 0. -/
theorem standardize_abs_le {ε μ σ es : ℝ} (hσ : 0 ≤ σ) (hes : 0 < es) :
    |standardize ε μ σ es| ≤ |ε - μ| / es := by
  unfold standardize
  rw [abs_div, abs_of_pos (by linarith : 0 < σ + es)]
  exact div_le_div_of_nonneg_left (abs_nonneg _) hes (by linarith)

/-- EQ-PREC-2: the raw precision 1/(Σ + ε_stab) is at most 1/ε_stab for Σ ≥ 0. -/
theorem precRaw_le {s2 es : ℝ} (hs : 0 ≤ s2) (hes : 0 < es) : 1 / (s2 + es) ≤ 1 / es :=
  one_div_le_one_div_of_le hes (by linarith)

/-- One channel of the drive is at most Q·Z when 0 ≤ Π_rel ≤ Q and |z| ≤ Z. -/
theorem driveTerm_le {m₀ q Q z Z : ℝ} (hm : 0 ≤ m₀) (hq : 0 ≤ q) (hqQ : q ≤ Q) (hz : |z| ≤ Z) :
    driveTerm m₀ q z ≤ Q * Z := by
  unfold driveTerm excessMag
  have hQ : 0 ≤ Q := le_trans hq hqQ
  nlinarith [abs_nonneg z, mul_le_mul hqQ hz (abs_nonneg z) hQ, mul_nonneg hq hm]

/-- The explicit upper bound on the drive in terms of the current errors:
    S_inst ≤ Π_max/Π̄ᵉ·|εᵉ − μᵉ_ref|/ε_stab + Π_max/Π̄ⁱ·(|εⁱ − μⁱ_ref|/ε_stab + |β_DA|). -/
theorem pipeLog_Sinst_le {W : Type*} (R : RefEstimator W) {p : PipeParams}
    (hp : PipeAdmissible p) (hsd : R.SdNonneg) (hes : 0 < p.epsStab) (s : PipeState W)
    (xe xi u : ℝ) :
    (pipeLog R p s xe xi u).Sinst ≤
      p.piMax / p.pibarE * (|predError xe s.e.xhat - R.mean s.e.ref| / p.epsStab) +
      p.piMax / p.pibarI *
        (|predError xi s.i.xhat - R.mean s.i.ref| / p.epsStab + |p.βDA|) := by
  obtain ⟨_, _, hE, hI⟩ := pipeLog_prec_mem_Icc R hp.piMin_le s xe xi u
  have hEr : 0 ≤ precRel (pipeLog R p s xe xi u).prEeff p.pibarE :=
    div_nonneg (le_trans hp.piMin_nonneg hE.1) hp.pibarE_pos.le
  have hIr : 0 ≤ precRel (pipeLog R p s xe xi u).prIeff p.pibarI :=
    div_nonneg (le_trans hp.piMin_nonneg hI.1) hp.pibarI_pos.le
  have hEle : precRel (pipeLog R p s xe xi u).prEeff p.pibarE ≤ p.piMax / p.pibarE :=
    div_le_div_of_nonneg_right hE.2 hp.pibarE_pos.le
  have hIle : precRel (pipeLog R p s xe xi u).prIeff p.pibarI ≤ p.piMax / p.pibarI :=
    div_le_div_of_nonneg_right hI.2 hp.pibarI_pos.le
  have hze : |(pipeLog R p s xe xi u).ze| ≤
      |predError xe s.e.xhat - R.mean s.e.ref| / p.epsStab :=
    standardize_abs_le (hsd _) hes
  have hzi0 : |(pipeLog R p s xe xi u).zi| ≤
      |predError xi s.i.xhat - R.mean s.i.ref| / p.epsStab :=
    standardize_abs_le (hsd _) hes
  have hzi : |(pipeLog R p s xe xi u).ziEff| ≤
      |predError xi s.i.xhat - R.mean s.i.ref| / p.epsStab + |p.βDA| := by
    have h : (pipeLog R p s xe xi u).ziEff = (pipeLog R p s xe xi u).zi + p.βDA := rfl
    rw [h]
    exact le_trans (abs_add_le _ _) (add_le_add hzi0 le_rfl)
  have hS : (pipeLog R p s xe xi u).Sinst =
      drive p.m₀ (precRel (pipeLog R p s xe xi u).prEeff p.pibarE) (pipeLog R p s xe xi u).ze
        (precRel (pipeLog R p s xe xi u).prIeff p.pibarI) (pipeLog R p s xe xi u).ziEff := rfl
  rw [hS, drive]
  exact add_le_add (driveTerm_le hp.m₀_nonneg hEr hEle hze) (driveTerm_le hp.m₀_nonneg hIr hIle hzi)

/-- Two-sided boundedness of S on every trajectory whose error bound stays at most U
    (with 0 ≤ U, L ≤ S₀ ≤ U and L ≤ the unconditional drive floor). -/
theorem traj_S_mem_Icc {W : Type*} (R : RefEstimator W) {p : PipeParams} (hp : PipeAdmissible p)
    (hsd : R.SdNonneg) (hes : 0 < p.epsStab) {L U : ℝ} (hL : L ≤ driveLower p) (hU : 0 ≤ U)
    {s₀ : PipeState W} (h₀ : PipeInv L s₀) (hS₀ : s₀.core.S ≤ U) (xe xi u : ℕ → ℝ)
    (herr : ∀ n,
      p.piMax / p.pibarE *
          (|predError (xe n) (traj R p s₀ xe xi u n).e.xhat -
            R.mean (traj R p s₀ xe xi u n).e.ref| / p.epsStab) +
        p.piMax / p.pibarI *
          (|predError (xi n) (traj R p s₀ xe xi u n).i.xhat -
            R.mean (traj R p s₀ xe xi u n).i.ref| / p.epsStab + |p.βDA|) ≤ U) (n : ℕ) :
    (traj R p s₀ xe xi u n).core.S ∈ Set.Icc L U :=
  ⟨(traj_inv R hp hL h₀ xe xi u n).S,
    traj_S_le R hp hU hS₀ xe xi u
      (fun k => le_trans (pipeLog_Sinst_le R hp hsd hes _ _ _ _) (herr k)) n⟩

/-! ## EQ-STEP-1 -/

/-- EQ-STEP-1: dt ≤ τ/10 ⇒ the per-step gain 1 − exp(−dt/τ) is at most 1/10. The same form
    is the leak λ (EQ-LEAK-1) and α_EMA (EQ-EMA-2). -/
theorem stepRule_gain_le {dt τ : ℝ} (hτ : 0 < τ) (hrule : dt ≤ τ / 10) :
    leakGain dt τ ≤ 1 / 10 := by
  unfold leakGain
  have h1 : dt / τ ≤ 1 / 10 := by
    rw [div_le_iff₀ hτ]
    linarith
  have h2 := Real.add_one_le_exp (-(dt / τ))
  linarith

/-! ## Axiom audit -/

/-- info: 'Apgi.traj_denoms_pos' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_denoms_pos

/-- info: 'Apgi.standardize_abs_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.standardize_abs_le

/-- info: 'Apgi.precRaw_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.precRaw_le

/-- info: 'Apgi.driveTerm_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.driveTerm_le

/-- info: 'Apgi.pipeLog_Sinst_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeLog_Sinst_le

/-- info: 'Apgi.traj_S_mem_Icc' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_S_mem_Icc

/-- info: 'Apgi.stepRule_gain_le' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.stepRule_gain_le

end Apgi
