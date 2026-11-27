module

public import Apgi.Pilot

/-!
# Epistemic tiers and bridge rules (SSOT §3, §14; EQ-BR-1, EQ-BR-2)

Tier currencies are encoded over the base dimensions of `Apgi.Dim` (the same base
dimensions as specification/units.json). Two kinds of statement are proved:

* **Tier discipline.** A quantity that carries AU is Tier 3 only, and no product with a
  constant free of AU⁻¹ moves it to Tier 1 or Tier 2. A bridge out of Tier 3 therefore
  needs a calibration constant with an AU⁻¹ factor — a registered calibration map, of which
  units.json lists none. This is a statement about the unit algebra; it does not decide
  whether the SSOT's Tier-3 → Tier-2 bridge (surprise in AU → broadcast bits) exists, which
  the SSOT records as unresolved (bridges.json, BR-T3-T2).
* **The registered κ calibration rule** (OSF Table 13 H7, Table 17; SSOT §14.2) as a decision
  procedure: bridge-consistent, retired, or indeterminate. The rule is proved to need two
  independent wholly-outside intervals for retirement, and to return no verdict without data.

Bridges are hypotheses, never theorems: no statement here asserts a calibrated κ.
-/

@[expose] public section

namespace Apgi

/-! ## Tiers -/

/-- The three epistemic tiers of SSOT §3. -/
inductive Tier where
  | T1 | T2 | T3
  deriving DecidableEq, Repr

/-- Product of two dimensions (adds exponents), as in `Qty.mul`. -/
def Dim.mul (d₁ d₂ : Dim) : Dim :=
  ⟨d₁.time + d₂.time, d₁.energy + d₂.energy, d₁.bit + d₂.bit, d₁.au + d₂.au, d₁.atp + d₂.atp⟩

/-- Admissible currencies. Tier 1: J, W, s, ATP counts (no bit, no AU). Tier 2: bits, bits/s
    (no energy, AU or ATP). Tier 3: AU, seconds, probabilities (no energy, bit or ATP). -/
def Tier.admits : Tier → Dim → Prop
  | .T1, d => d.bit = 0 ∧ d.au = 0
  | .T2, d => d.energy = 0 ∧ d.au = 0 ∧ d.atp = 0
  | .T3, d => d.energy = 0 ∧ d.bit = 0 ∧ d.atp = 0

/-- Registered currencies land in the tier the SSOT assigns them. -/
theorem tier_examples :
    Tier.T3.admits auDim ∧ Tier.T3.admits dimensionless ∧ Tier.T2.admits { bit := 1 } ∧
      Tier.T2.admits { bit := 1, time := -1 } ∧ Tier.T1.admits { energy := 1 } ∧
      Tier.T1.admits { atp := 1 } := by
  simp [Tier.admits, auDim, dimensionless]

/-- κ (ATP/bit) and e_bit (J/bit) mix Tier-1 and Tier-2 currencies: they are bridge
    quantities and belong to no single tier. -/
theorem bridge_quantities_cross_tiers :
    (¬ Tier.T1.admits atpPerBit ∧ ¬ Tier.T2.admits atpPerBit ∧ ¬ Tier.T3.admits atpPerBit) ∧
      (¬ Tier.T1.admits joulePerBit ∧ ¬ Tier.T2.admits joulePerBit ∧
        ¬ Tier.T3.admits joulePerBit) := by
  simp [Tier.admits, atpPerBit, joulePerBit]

/-- A quantity that carries AU is admissible in Tier 3 only. -/
theorem au_quantity_tier3_only {d : Dim} (h : d.au ≠ 0) :
    ¬ Tier.T1.admits d ∧ ¬ Tier.T2.admits d := by
  simp only [Tier.admits]
  exact ⟨fun h' => h h'.2, fun h' => h h'.2.1⟩

/-- Multiplying an AU quantity by any constant free of AU⁻¹ leaves it outside Tiers 1 and 2:
    leaving Tier 3 needs a calibration constant that carries AU⁻¹. -/
theorem tier_exit_needs_au_inverse {d c : Dim} (hd : d.au ≠ 0) (hc : c.au = 0) :
    ¬ Tier.T1.admits (d.mul c) ∧ ¬ Tier.T2.admits (d.mul c) := by
  apply au_quantity_tier3_only
  simp [Dim.mul, hc, hd]

/-- From AU to Tier 2 the calibration constant must carry exactly AU⁻¹. -/
theorem calibration_constant_au {c : Dim} (h : Tier.T2.admits (auDim.mul c)) : c.au = -1 := by
  simp [Tier.admits, Dim.mul, auDim] at h
  omega

/-- EQ-BR-2 dimensions: (J/bit) / (J/ATP) = ATP/bit. -/
theorem kappa_dimension : joulePerBit.mul { energy := -1, atp := 1 } = atpPerBit := by
  simp [Dim.mul, joulePerBit, atpPerBit]

/-! ## The registered κ calibration rule (SSOT §14.2) -/

/-- A calibrated 95% interval for κ_syn in ATP/bit, from one independent dataset or paradigm. -/
structure KappaInterval where
  lo : ℝ
  hi : ℝ

/-- The registered band [10, 10⁴] ATP/bit. -/
def kappaBandLo : ℝ := 10
def kappaBandHi : ℝ := 10 ^ 4

/-- Wholly inside the band. -/
def KappaInterval.inside (k : KappaInterval) : Prop := kappaBandLo ≤ k.lo ∧ k.hi ≤ kappaBandHi

/-- Wholly outside the band. -/
def KappaInterval.outside (k : KappaInterval) : Prop := k.hi < kappaBandLo ∨ kappaBandHi < k.lo

noncomputable instance (k : KappaInterval) : Decidable k.outside := Classical.dec _

/-- Retirement: wholly-outside intervals in at least two independent datasets. -/
noncomputable def kappaRetires (ks : List KappaInterval) : Prop :=
  2 ≤ (ks.filter (fun k => decide k.outside)).length

/-- Bridge-consistent: a replicated estimate, i.e. at least two intervals, all wholly inside. -/
def kappaConsistent (ks : List KappaInterval) : Prop := 2 ≤ ks.length ∧ ∀ k ∈ ks, k.inside

/-- A single dataset never retires the bridge, whatever it shows. -/
theorem kappa_single_never_retires (k : KappaInterval) : ¬ kappaRetires [k] := by
  unfold kappaRetires
  have := List.length_filter_le (fun k : KappaInterval => decide k.outside) [k]
  simp only [List.length_singleton] at this
  omega

/-- With no calibrated estimate (the current state: both legs missing) the rule is inert:
    it neither retires nor confirms the bridge. -/
theorem kappa_inert : ¬ kappaRetires [] ∧ ¬ kappaConsistent [] := by
  simp [kappaRetires, kappaConsistent]

/-- An interval cannot be both inside and outside: consistency and retirement exclude each
    other on the same data. -/
theorem kappa_inside_not_outside {k : KappaInterval} (hk : k.lo ≤ k.hi) (h : k.inside) :
    ¬ k.outside := by
  unfold KappaInterval.inside KappaInterval.outside at *
  simp only [not_or, not_lt]
  constructor <;> linarith [h.1, h.2]

/-- Straddling intervals never count toward retirement. -/
theorem kappa_straddle_not_outside {k : KappaInterval} (h1 : k.lo ≤ kappaBandHi)
    (h2 : kappaBandLo ≤ k.hi) : ¬ k.outside := by
  unfold KappaInterval.outside
  simp only [not_or, not_lt]
  exact ⟨h2, h1⟩

/-- Consistent and retired are exclusive on the same well-formed data. -/
theorem kappa_consistent_not_retires {ks : List KappaInterval} (hwf : ∀ k ∈ ks, k.lo ≤ k.hi)
    (h : kappaConsistent ks) : ¬ kappaRetires ks := by
  unfold kappaRetires
  have : ks.filter (fun k => decide k.outside) = [] := by
    rw [List.filter_eq_nil_iff]
    intro k hk
    simpa using kappa_inside_not_outside (hwf k hk) (h.2 k hk)
  rw [this]
  simp

end Apgi

end

/-! ## Axiom audit (self-enforcing). -/

/-- info: 'Apgi.tier_examples' depends on axioms: [propext] -/
#guard_msgs in
#print axioms Apgi.tier_examples

/-- info: 'Apgi.bridge_quantities_cross_tiers' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.bridge_quantities_cross_tiers

/-- info: 'Apgi.au_quantity_tier3_only' does not depend on any axioms -/
#guard_msgs in
#print axioms Apgi.au_quantity_tier3_only

/-- info: 'Apgi.tier_exit_needs_au_inverse' depends on axioms: [propext] -/
#guard_msgs in
#print axioms Apgi.tier_exit_needs_au_inverse

/-- info: 'Apgi.calibration_constant_au' depends on axioms: [propext, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.calibration_constant_au

/-- info: 'Apgi.kappa_dimension' depends on axioms: [propext] -/
#guard_msgs in
#print axioms Apgi.kappa_dimension

/-- info: 'Apgi.kappa_single_never_retires' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_single_never_retires

/-- info: 'Apgi.kappa_inert' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_inert

/-- info: 'Apgi.kappa_inside_not_outside' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_inside_not_outside

/-- info: 'Apgi.kappa_straddle_not_outside' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_straddle_not_outside

/-- info: 'Apgi.kappa_consistent_not_retires' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms Apgi.kappa_consistent_not_retires
