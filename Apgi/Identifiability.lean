module

public import Apgi.Pipeline

/-!
# TC-08: structural degeneracies of the likelihood (SSOT §17)

SSOT §17 lists the structural degeneracies a recovery study must handle. Three of them are
exact algebraic facts and are proved here:

* **TC-08a (S, θ_eff).** Only the margin S − θ_eff enters the sigmoid; a common offset b is
  unidentified (`ignitionProb_shift`, `hazardLik_shift`).
* **TC-08c (S, θ, τ_σ).** Joint scale degeneracy: S′ = aS + b, θ′ = aθ + b, γ′ = γ/a preserve
  the propensity path and hence the likelihood of every observed event sequence
  (`ignitionProb_rescale`, `propensity_path_rescale`, `hazardLik_rescale`). Two distinct
  parameter sets therefore have identical likelihood for every data set
  (`hazardLik_not_injective`).
* **TC-08b (g_NE, Πⁱ, exp(β_SM·M̂)).** With γ_NE = 0 (CFG-CORE) the NE gain, the somatic
  marker gain and the marker enter the whole pipeline only through the product
  g_NE·exp(β_SM·M̂): any two settings with the same product give the same trajectory for every
  input and draw sequence (`traj_gain_product`), and such distinct settings exist
  (`gain_product_not_injective`).

The likelihood is the Bernoulli likelihood of the event sequence B(t) under the hazard
sampler (EQ-HAZARD-1). The observation model EQ-OBS-1/2 depends on the data only through the
propensity path, so `propensity_path_rescale` carries over to it.

* **TC-08g (c₁, v₁, v₂, η_θ).** EQ-ALLO-1 sees the cost and value weights only through
  η_θ·c₁, η_θ·c₂, η_θ·v₁, η_θ·v₂: scaling η_θ by a ≠ 0 and the four weights by 1/a leaves
  every trajectory unchanged (`traj_scaleAllo`, `scaleAllo_not_injective`), and with η_θ = 0
  the weights do not enter at all (`traj_weights_eta_zero`). This is an exact degeneracy
  inside the declared TC-08g trade-off; what remains (how well the products are recovered)
  is statistical.

TC-08d–f, and the recovery of the TC-08g products and of τ_θ, are *posterior trade-offs*
(near-degeneracies), not exact invariances; they are statistical properties of a fit, measured
by verification/python/recovery_pipeline.py and reported in
verification/reports/recovery-pipeline.json. The recovery gate itself
(Pearson r > 0.85, median range-scaled error < 20%) is a computational test:
verification/python/test_recovery.py.
-/

@[expose] public section

namespace Apgi

/-! ## TC-08a and TC-08c: the sigmoid -/

/-- TC-08a: a common offset of S and θ_eff leaves the propensity unchanged. -/
theorem ignitionProb_shift (k S θ b : ℝ) :
    ignitionProb k (S + b) (θ + b) = ignitionProb k S θ := by
  unfold ignitionProb
  ring_nf

/-- TC-08c: S′ = aS + b, θ′ = aθ + b, γ′ = γ/a leave the propensity unchanged (a ≠ 0). -/
theorem ignitionProb_rescale {a : ℝ} (ha : a ≠ 0) (k S θ b : ℝ) :
    ignitionProb (k / a) (a * S + b) (a * θ + b) = ignitionProb k S θ := by
  unfold ignitionProb
  congr 3
  field_simp
  ring

/-- TC-08c on whole propensity paths: every functional of the path (the hazard likelihood,
    EQ-OBS-1 P(hit), EQ-OBS-2 P(report)) is invariant. -/
theorem propensity_path_rescale {a : ℝ} (ha : a ≠ 0) (k b : ℝ) (S θ : ℕ → ℝ) :
    (fun t => ignitionProb (k / a) (a * S t + b) (a * θ t + b)) =
      fun t => ignitionProb k (S t) (θ t) :=
  funext fun t => ignitionProb_rescale ha k (S t) (θ t) b

/-! ## The event-sequence likelihood -/

/-- Bernoulli likelihood of one observation B (1 = ignition) with probability q. -/
noncomputable def bernLik (q B : ℝ) : ℝ := if B = 1 then q else 1 - q

/-- Likelihood of the first n observations B under per-step probabilities q. -/
noncomputable def seqLik (q B : ℕ → ℝ) : ℕ → ℝ
  | 0 => 1
  | n + 1 => seqLik q B n * bernLik (q n) (B n)

/-- EQ-HAZARD-1: likelihood of an observed event sequence B given drive and threshold
    paths S, θ, steepness k, r_max and dt. -/
noncomputable def hazardLik (rmax dt k : ℝ) (S θ B : ℕ → ℝ) (n : ℕ) : ℝ :=
  seqLik (fun t => hazardProb rmax (ignitionProb k (S t) (θ t)) dt) B n

/-- TC-08a: the event likelihood is invariant under a common offset of S and θ_eff. -/
theorem hazardLik_shift (rmax dt k b : ℝ) (S θ B : ℕ → ℝ) (n : ℕ) :
    hazardLik rmax dt k (fun t => S t + b) (fun t => θ t + b) B n =
      hazardLik rmax dt k S θ B n := by
  unfold hazardLik
  simp only [ignitionProb_shift]

/-- TC-08c: the event likelihood is invariant under the joint scale transformation. -/
theorem hazardLik_rescale {a : ℝ} (ha : a ≠ 0) (rmax dt k b : ℝ) (S θ B : ℕ → ℝ) (n : ℕ) :
    hazardLik rmax dt (k / a) (fun t => a * S t + b) (fun t => a * θ t + b) B n =
      hazardLik rmax dt k S θ B n := by
  unfold hazardLik
  simp only [ignitionProb_rescale ha]

/-- TC-08c: (k, S, θ) is not identifiable from event data. For k ≠ 0 the distinct parameter
    sets (k, S, θ) and (k/2, 2S, 2θ) give the same likelihood for every data set. -/
theorem hazardLik_not_injective {k : ℝ} (hk : k ≠ 0) (rmax dt : ℝ) :
    k / 2 ≠ k ∧ ∀ (S θ B : ℕ → ℝ) (n : ℕ),
      hazardLik rmax dt (k / 2) (fun t => 2 * S t) (fun t => 2 * θ t) B n =
        hazardLik rmax dt k S θ B n := by
  refine ⟨fun h => hk (by linarith), fun S θ B n => ?_⟩
  have := hazardLik_rescale (a := 2) two_ne_zero rmax dt k 0 S θ B n
  simpa using this

/-! ## TC-08b: the noradrenergic and somatic-marker gains -/

/-- p with the NE gain g_NE, the somatic-marker gain β_SM and the marker M̂ replaced. -/
def PipeParams.withGains (p : PipeParams) (g β M : ℝ) : PipeParams :=
  { p with readout := { p.readout with gNE := g }, βSM := β, marker := M }

/-- With γ_NE = 0 the NE clamp is the identity. -/
theorem neClamp_zero (g : ℝ) : neClamp 0 g = g :=
  neClamp_of_le (by simp [ne_bound])

/-- TC-08b: with γ_NE = 0 one step depends on (g_NE, β_SM, M̂) only through
    g_NE·exp(β_SM·M̂). -/
theorem pipeStep_gain_product {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hγ : p.readout.γNE = 0) {g β M : ℝ}
    (h : g * Real.exp (β * M) = p.readout.gNE * Real.exp (p.βSM * p.marker))
    (s : PipeState W) (xe xi u : ℝ) :
    pipeStep R (p.withGains g β M) s xe xi u = pipeStep R p s xe xi u := by
  have he : ∀ pb, precEff g pb β M = precEff p.readout.gNE pb p.βSM p.marker := by
    intro pb
    unfold precEff
    calc g * pb * Real.exp (β * M) = pb * (g * Real.exp (β * M)) := by ring
      _ = pb * (p.readout.gNE * Real.exp (p.βSM * p.marker)) := by rw [h]
      _ = p.readout.gNE * pb * Real.exp (p.βSM * p.marker) := by ring
  have hl : ∀ q : PipeParams, pipeStep R q s xe xi u =
      { e := channelUpdate R s.e (pipeLog R q s xe xi u).εe q.αe q.ηe (pipeLog R q s xe xi u).prE
        i := channelUpdate R s.i (pipeLog R q s xe xi u).εi q.αi q.ηi (pipeLog R q s xe xi u).prI
        core := coreStep q.core s.core (pipeLog R q s xe xi u).Sinst (pipeLog R q s xe xi u).C
          (pipeLog R q s xe xi u).V (pipeLog R q s xe xi u).B
        Bprev := (pipeLog R q s xe xi u).B } := fun _ => rfl
  rw [hl, hl]
  simp only [pipeLog, PipeParams.withGains, thetaEff, hγ, neClamp_zero, he, zero_mul]

/-- TC-08b along every trajectory, for every input and draw sequence. -/
theorem traj_gain_product {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hγ : p.readout.γNE = 0) {g β M : ℝ}
    (h : g * Real.exp (β * M) = p.readout.gNE * Real.exp (p.βSM * p.marker))
    (s₀ : PipeState W) (xe xi u : ℕ → ℝ) :
    ∀ n, traj R (p.withGains g β M) s₀ xe xi u n = traj R p s₀ xe xi u n
  | 0 => rfl
  | n + 1 => by
    change pipeStep R (p.withGains g β M) (traj R (p.withGains g β M) s₀ xe xi u n) (xe n) (xi n)
        (u n) = pipeStep R p (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)
    rw [traj_gain_product R p hγ h s₀ xe xi u n]
    exact pipeStep_gain_product R p hγ h _ _ _ _

/-- TC-08b: (g_NE, β_SM, M̂) is not identifiable. For β_SM ≠ 0 and g_NE ≠ 0, doubling g_NE and
    lowering M̂ by log 2/β_SM is a different setting with the same trajectory. -/
theorem gain_product_not_injective {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hγ : p.readout.γNE = 0) (hβ : p.βSM ≠ 0) (hg : p.readout.gNE ≠ 0)
    (s₀ : PipeState W) (xe xi u : ℕ → ℝ) :
    2 * p.readout.gNE ≠ p.readout.gNE ∧
      ∀ n, traj R (p.withGains (2 * p.readout.gNE) p.βSM (p.marker - Real.log 2 / p.βSM)) s₀
          xe xi u n = traj R p s₀ xe xi u n := by
  refine ⟨fun h => hg (by linarith), traj_gain_product R p hγ ?_ s₀ xe xi u⟩
  have hx : p.βSM * (p.marker - Real.log 2 / p.βSM) = p.βSM * p.marker - Real.log 2 := by
    field_simp
  rw [hx, Real.exp_sub, Real.exp_log (by norm_num : (0 : ℝ) < 2)]
  field_simp

/-! ## TC-08g: the allostatic gain and the cost and value weights -/

/-- p with η_θ multiplied by a and the cost and value weights c₁, c₂, v₁, v₂ divided by a. -/
noncomputable def PipeParams.scaleAllo (p : PipeParams) (a : ℝ) : PipeParams :=
  { p with core := { p.core with η := a * p.core.η },
           c1 := p.c1 / a, c2 := p.c2 / a, v1 := p.v1 / a, v2 := p.v2 / a }

/-- p with the cost and value weights replaced. -/
def PipeParams.withWeights (p : PipeParams) (c1 c2 v1 v2 : ℝ) : PipeParams :=
  { p with c1 := c1, c2 := c2, v1 := v1, v2 := v2 }

theorem costC_div (a c1 c2 S Bp : ℝ) :
    costC (c1 / a) (c2 / a) 0 S Bp 0 = costC c1 c2 0 S Bp 0 / a := by
  simp only [costC, mul_zero, add_zero, div_mul_eq_mul_div, ← add_div]

theorem valueV_div (a v1 v2 ze zi : ℝ) :
    valueV (v1 / a) (v2 / a) ze zi = valueV v1 v2 ze zi / a := by
  simp only [valueV, div_mul_eq_mul_div, ← add_div]

/-- EQ-ALLO-1 depends on (η_θ, C, V) only through η_θ·(C − V). -/
theorem thresholdStep_scale {a : ℝ} (ha : a ≠ 0) (θ θ₀ η C V δ B dt τ : ℝ) :
    thresholdStep θ θ₀ (a * η) (C / a) (V / a) δ B dt τ = thresholdStep θ θ₀ η C V δ B dt τ := by
  have h : a * η * (C / a - V / a) = η * (C - V) := by
    field_simp
  unfold thresholdStep allostaticStep
  rw [h]

/-- With η_θ = 0 the cost and value drive does not enter EQ-ALLO-1. -/
theorem thresholdStep_eta_zero (θ θ₀ C V δ B dt τ : ℝ) :
    thresholdStep θ θ₀ 0 C V δ B dt τ = max θ_floor (decayStep (θ + δ * B) θ₀ dt τ) := by
  unfold thresholdStep allostaticStep
  simp

/-- TC-08g: one step depends on (η_θ, c₁, c₂, v₁, v₂) only through the products
    η_θ·c₁, η_θ·c₂, η_θ·v₁, η_θ·v₂. -/
theorem pipeStep_scaleAllo {W : Type*} (R : RefEstimator W) (p : PipeParams) {a : ℝ}
    (ha : a ≠ 0) (s : PipeState W) (xe xi u : ℝ) :
    pipeStep R (p.scaleAllo a) s xe xi u = pipeStep R p s xe xi u := by
  simp only [pipeStep, pipeLog, coreStep, PipeParams.scaleAllo, costC_div, valueV_div,
    thresholdStep_scale ha]
  rfl

/-- TC-08g along every trajectory, for every input and draw sequence. -/
theorem traj_scaleAllo {W : Type*} (R : RefEstimator W) (p : PipeParams) {a : ℝ}
    (ha : a ≠ 0) (s₀ : PipeState W) (xe xi u : ℕ → ℝ) :
    ∀ n, traj R (p.scaleAllo a) s₀ xe xi u n = traj R p s₀ xe xi u n
  | 0 => rfl
  | n + 1 => by
    change pipeStep R (p.scaleAllo a) (traj R (p.scaleAllo a) s₀ xe xi u n) (xe n) (xi n) (u n) =
      pipeStep R p (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)
    rw [traj_scaleAllo R p ha s₀ xe xi u n]
    exact pipeStep_scaleAllo R p ha _ _ _ _

/-- TC-08g: η_θ is not identifiable apart from the weights. For η_θ ≠ 0, doubling η_θ and
    halving c₁, c₂, v₁, v₂ is a different setting with the same trajectory. -/
theorem scaleAllo_not_injective {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hη : p.core.η ≠ 0) (s₀ : PipeState W) (xe xi u : ℕ → ℝ) :
    (p.scaleAllo 2).core.η ≠ p.core.η ∧
      ∀ n, traj R (p.scaleAllo 2) s₀ xe xi u n = traj R p s₀ xe xi u n := by
  refine ⟨fun h => hη ?_, traj_scaleAllo R p two_ne_zero s₀ xe xi u⟩
  change 2 * p.core.η = p.core.η at h
  linarith

/-- TC-08g with η_θ = 0 (the CFG-CORE placeholder): the weights c₁, c₂, v₁, v₂ do not enter
    the trajectory at all, so they are unidentified from any data. -/
theorem pipeStep_weights_eta_zero {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hη : p.core.η = 0) (c1 c2 v1 v2 : ℝ) (s : PipeState W) (xe xi u : ℝ) :
    pipeStep R (p.withWeights c1 c2 v1 v2) s xe xi u = pipeStep R p s xe xi u := by
  simp only [pipeStep, pipeLog, coreStep, PipeParams.withWeights, hη, thresholdStep_eta_zero]
  rfl

theorem traj_weights_eta_zero {W : Type*} (R : RefEstimator W) (p : PipeParams)
    (hη : p.core.η = 0) (c1 c2 v1 v2 : ℝ) (s₀ : PipeState W) (xe xi u : ℕ → ℝ) :
    ∀ n, traj R (p.withWeights c1 c2 v1 v2) s₀ xe xi u n = traj R p s₀ xe xi u n
  | 0 => rfl
  | n + 1 => by
    change pipeStep R (p.withWeights c1 c2 v1 v2) (traj R (p.withWeights c1 c2 v1 v2) s₀ xe xi u n)
        (xe n) (xi n) (u n) = pipeStep R p (traj R p s₀ xe xi u n) (xe n) (xi n) (u n)
    rw [traj_weights_eta_zero R p hη c1 c2 v1 v2 s₀ xe xi u n]
    exact pipeStep_weights_eta_zero R p hη c1 c2 v1 v2 _ _ _ _

/-! ## Axiom audit -/

/-- info: 'Apgi.ignitionProb_shift' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_shift

/-- info: 'Apgi.ignitionProb_rescale' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.ignitionProb_rescale

/-- info: 'Apgi.propensity_path_rescale' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.propensity_path_rescale

/-- info: 'Apgi.hazardLik_shift' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazardLik_shift

/-- info: 'Apgi.hazardLik_rescale' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazardLik_rescale

/-- info: 'Apgi.hazardLik_not_injective' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.hazardLik_not_injective

/-- info: 'Apgi.neClamp_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.neClamp_zero

/-- info: 'Apgi.pipeStep_gain_product' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_gain_product

/-- info: 'Apgi.traj_gain_product' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_gain_product

/-- info: 'Apgi.gain_product_not_injective' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.gain_product_not_injective

/-- info: 'Apgi.costC_div' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.costC_div

/-- info: 'Apgi.valueV_div' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.valueV_div

/-- info: 'Apgi.thresholdStep_scale' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_scale

/-- info: 'Apgi.thresholdStep_eta_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.thresholdStep_eta_zero

/-- info: 'Apgi.pipeStep_scaleAllo' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_scaleAllo

/-- info: 'Apgi.traj_scaleAllo' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_scaleAllo

/-- info: 'Apgi.scaleAllo_not_injective' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.scaleAllo_not_injective

/-- info: 'Apgi.pipeStep_weights_eta_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.pipeStep_weights_eta_zero

/-- info: 'Apgi.traj_weights_eta_zero' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.traj_weights_eta_zero

end Apgi
