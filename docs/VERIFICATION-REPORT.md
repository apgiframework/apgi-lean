# APGI formal verification: final report (round of 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 18951b65…. Production code in apgi-implementation (72ad050) and
apgi-validation (f6fec65) is checked through pinned cross-tests and was not changed this round.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). Every figure below has a numerator and a denominator; none is
an empirical result.

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`, every theorem's axioms are pinned to Lean's three standard axioms, and
every requirement is traced to a proof or a test or marked as assumed, conditional or open.
Release still needs author and external work: 8 of the 18 SSOT release blockers are open
(B-07, B-09 remainder, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-08, TC-25 and TC-26
are not implemented, and this round has not yet run in CI because it is not pushed.

## 2. Evidence (this PC, after the final changes)

- `lake build --wfail`: green, 7244 jobs, 8 APGI modules plus the generated Spec.lean.
- Axiom audit: 170 of 170 theorems pinned with `#guard_msgs`; 163 depend on exactly
  [propext, Classical.choice, Quot.sound] and 7 on a strict subset. No `sorry`, no `admit`, no
  `axiom` declaration (enforced by `check_consistency.axiom_check`).
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale.
- Source extraction: 93 of 93 records verified against the sha256-pinned corpus (85
  evidence-bearing parameters, 8 bridge and observable records).
- pytest (with the pinned apgi-implementation): 264 passed, 1 skipped.
  test_production_validation.py (pinned apgi-validation): 10 passed, 2 skipped (declared variant).
- CI on the previous head fb0ad00 (run 45931170311): 4 of 4 jobs green.

## 3. Proof coverage

- Theorems: 170 in 8 modules (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11). Start of round: 119 in 5.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements (requirements.json): 44; by kind 13 proved, 2 conditional, 27 tested,
  1 assumed, 1 empirical; by status 32 pass, 6 partial, 3 open, 3 not implemented.
- Conformance tests TC-01…TC-26: 17 pass, 6 partial, 3 not implemented (start: 16 / 6 / 4).
- Claims: 39; 35 proved, 1 assumed (CL-8), 3 unresolved (CL-7, CL-26, CL-36).

## 4. What this round proved

1. **The canonical 15-step pipeline as one function** (`Apgi.pipeStep`), over any reference
   estimator, with bounded-state invariants along every trajectory for every input and draw
   sequence: Σ ≥ 0, θ ≥ θ_floor, r ≥ 0, B ∈ {0, 1}, S ≥ −m₀(Π_max/Π̄ᵉ + Π_max/Π̄ⁱ), precisions in
   [Π_min, Π_max], |γ_NE|·g_NE ≤ 0.5.
2. **The causal one-step lag**: the ignition decision at t ignores the inputs at t.
3. **The sampler is the hazard**: under a uniform draw, P(B(t) = 1) = 1 − exp(−r_max·B_t·dt).
4. **The 17-step proposal is not equivalent**: SSOT §8 rejects it; two of its distinguishing
   features are proved to change the decision or the standardized error.
5. **L0–L4**: L0 outside the ignition model; the k = 133 table and its two retained band
   violations; the boundary-sensitive level count; the per-level τ_Π step rule.
6. **Epistemic tiers and the κ rule**: a Tier-3 quantity leaves Tier 3 only through an AU⁻¹
   calibration constant (none is registered); the registered κ retirement rule behaves as
   registered.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- The trajectory theorems assume `PipeAdmissible` (ten explicit parameter hypotheses; CFG-CORE
  satisfies them, checked by test).
- The upper bound on S assumes a bound on S_inst (`traj_S_le`).
- The Lyapunov bound is proved only at loop gain 0; the coupled conjecture (CL-26) is open.
- OSF H10 is a hypothesis (`H10Ordering`), never proved.
- The loop-gain condition is a design heuristic without a closed-loop derivation.
- The Tier-3 → Tier-2 bridge is unresolved; κ has no value and its rule is inert.
- The cusp normal form is an analysis form; no theorem connects it to the stochastic pipeline.

## 6. Independent end-to-end audit

The audit used checks that do not trust the work being audited:

- **Clean rebuild.** The final verification routine re-ran extraction, Spec.lean generation,
  the full Lean build, consistency, the release manifest, the traceability generator and both
  pytest suites on the tree that was then committed.
- **Mutation tests.** Eight faults were planted one at a time and each was caught:
  1. apgi_ref decides from the post-leak S (the rejected order): `test_decision_input_independent` fails.
  2. The Πⁱ_eff clamp removed: `test_traj_inv` fails.
  3. The EMA variance uses the post-update mean: `test_variance_uses_preupdate_mean` fails.
  4. The retention applied twice: the golden-vector trajectory test fails.
  5. κ retired on one dataset: `test_kappa_rule_twin` fails.
  6. Per-step Bernoulli in place of the hazard: `test_sampler_frequency_matches_hazard` fails.
  7. A bridge quote edited: extraction reports the record as failed.
  8. Apgi/Pipeline.lean decides from the post-leak S: `lake build --wfail` fails (unsolved goals
     in `pipeLog_B_eq_one_iff`; `pipeStep_decision_input_independent` no longer holds).
- **Vacuity checks.** Every trajectory theorem's hypothesis structure is satisfied by the
  registry defaults (tested); the invariants are restated as Hypothesis tests on random
  admissible parameters, inputs and draws; the rejected-order theorems carry strict
  inequalities, not equalities.

Limits of this audit: it was run by the same agent that did the work, on one machine; it is
not the independent human review that B-17 and SSOT §32 require.

## 7. Scores (1–100), initial → final

- Architecture 85 → 90
- Mathematical correctness 90 → 92
- Specification coverage 82 → 88
- Implementation 84 → 85
- Proof completeness 78 → 86
- Testing 85 → 89
- Reproducibility 85 → 87
- Documentation 70 → 86
- Publication readiness 63 → 66
- **Overall 79 → 85**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating"). A perfect specification
score would not be a claim of scientific truth (SSOT §32).

## 8. Genuine blockers

- Push: this round is committed locally; the github-apgi SSH key is not loaded in this
  session's shells, so CI has not seen it.
- CI workflow: .github/workflows is write-protected for the remote tools; the Python 3.11/3.12
  matrix is prepared in .scratch/lean_action_ci.proposed.yml (F6).
- Author decisions: record-status approval (61a), operating point (B-13), OSF Amendment 2
  (B-14), SSOT text corrections (D1–D10), bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Out of this repository: SSOT-P10 and the clamp-fraction report in apgi-implementation; the
  K7 rerun; TC-25 end-to-end and TC-26 registered-fidelity checks.
