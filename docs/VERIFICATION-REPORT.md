# APGI formal verification: report (round 68–69, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 18951b65…. Production code is checked through pinned
cross-tests: apgi-implementation at the pin 72ad050 (a fix, e0e82cf, is committed locally and
not pushed) and apgi-validation at f6fec65.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). Every figure below has a numerator and a denominator; none is
an empirical result. The previous round's report is kept in git history (0337730).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`; every theorem's axioms are pinned to Lean's standard axioms; every
requirement is traced to a proof or a test or marked as assumed, conditional or open. Release
still needs author and external work: 8 of the 18 SSOT release blockers are open (B-07, B-09
remainder, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-25 and TC-26 are not
implemented, TC-08d–g are not covered, and the production TC-13 fix is not pushed.

## 2. Evidence (this PC, final tree, production at the pin 72ad050)

`verification\verify_all.ps1 -Impl .scratch\impl-pin`, 2026-11-27 07:10–07:25 ET:
- Source extraction: 93 of 93 records verified against the sha256-pinned corpus.
- `generate_lean.py`: Spec.lean regenerated from the current registry.
- `lake build --wfail`: **Build completed successfully (7248 jobs)**, 10 APGI modules plus the
  generated Spec.lean.
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit: no
  sorry, no admit, no axiom declaration, no non-standard axiom).
- `make_release_manifest.py`, `make_traceability.py`: regenerated.
- pytest with the pinned apgi-implementation: **312 passed, 1 skipped, 4 xfailed** (the four
  strict xfails are SSOT-P11; the skip is the validation module without its path).
- test_production_validation.py (pinned apgi-validation): 10 passed, 2 skipped (declared variant).
- Against apgi-implementation e0e82cf the four SSOT-P11 tests pass (reported as XPASS(strict)).
- apgi-implementation's own suite at e0e82cf: 2842 passed, 8 skipped, 6 failed; the same 6
  fail on a clean 72ad050 on this PC (pytensor deprecation and a cp1252 decode; F11).
- CI on the previous head 4de14fa (run 45988035558): 5 of 5 jobs green. This round has not
  run in CI: the push failed (§8).

## 3. Proof coverage

- Theorems: **187 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 14, Epistemic 11, Stability 7, Identifiability 10). Start of round: 170 in
  8. 180 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements (requirements.json): 44; by kind 13 proved, 2 conditional, 27 tested, 1 assumed,
  1 empirical; by status 33 pass, 6 partial, 3 open, 2 not implemented.
- Conformance tests TC-01…TC-26: **18 pass, 6 partial, 2 not implemented** (start: 17 / 6 / 3).
  Partial: TC-01 (approval dates), TC-04 (apgi_core.full_model), TC-08 (d–g), TC-10 (production
  clamp fraction), TC-13 (production pin), TC-21. Not implemented: TC-25, TC-26.
- Claims: 44; 40 proved, 1 assumed (CL-8), 3 unresolved (CL-7, CL-26, CL-36).

## 4. What this round established

1. **TC-13, division by zero cannot occur** (`traj_denoms_pos`): every denominator of the step
   is positive along every trajectory, for every input and draw sequence.
2. **TC-13, finite amplification** (`pipeLog_Sinst_le`, `traj_S_mem_Icc`): an explicit upper
   bound on the drive in terms of the current errors and 1/ε_stab, and two-sided boundedness of
   S under bounded errors. Before this round the upper bound on S rested on an unexplained
   hypothesis on S_inst; it now rests on a bound on the observable errors.
3. **EQ-STEP-1 bounds every per-step gain by 1/10** (`stepRule_gain_le`).
4. **TC-13, defined handling** (computational, float64): NaN/Inf rejected and overflow rejected
   atomically in the reference; the same in production at e0e82cf; production and reference
   classify inputs up to 10³⁰⁰ identically at the pin.
5. **TC-08a–c, exact degeneracies**: common offset and joint scale leave the event-sequence
   likelihood unchanged (`hazardLik_shift`, `hazardLik_rescale`, `hazardLik_not_injective`); with
   γ_NE = 0 the NE and somatic-marker gains enter the whole trajectory only as a product
   (`traj_gain_product`, `gain_product_not_injective`).
6. **TC-08, the §17 recovery gate** on synthetic data, after the degeneracies are handled:
   θ_eff r = 0.985 and median range-scaled error 0.039; γ_sig r = 0.953 and 0.061 (60 subjects;
   targets r > 0.85, error < 0.20).
7. **TC-19**: PCG64 and seed reproducibility in production; a distributional test of production
   against the reference on independent PCG64 and Philox streams, with a power check.
8. **SSOT-P11** (new production defect): overflow in core/ssot_core.py was not atomic and a
   silent inf could enter the state. Registered, put under strict xfail, fixed in e0e82cf.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Trajectory theorems assume `PipeAdmissible` (ten parameter hypotheses; CFG-CORE satisfies
  them, checked by test); the TC-13 theorems add ε_stab > 0 and a nonnegative reference spread.
- `traj_S_mem_Icc` is conditional on a bound on the errors; z is unbounded for unbounded input.
- Overflow, NaN and Inf are float64 properties and have no Lean counterpart; their handling is
  tested, not proved.
- The recovery gate covers θ_eff and γ_sig only; its design constants are synthetic-study
  choices; the 20% gate is a proposed reading pending amendment; recovery is never evidence for
  APGI (§17).
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis; loop gain a design
  heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem connects the
  cusp normal form to the stochastic pipeline.

## 6. Independent end-to-end audit

- **Clean rebuild.** The final routine re-ran extraction, generation, the full Lean build (every
  APGI module rebuilt because Spec.lean changed), consistency, the manifest, traceability and
  both pytest suites on the committed tree, with production at the pin.
- **Mutation tests this round** (verification of the new checks; `.scratch\r68\mut`): see the
  table in docs/REMAINING-TASKS.md ("Audit evidence"). Faults planted one at a time and restored.
- **Before/after checks of the production fix.** The SSOT-P11 tests fail on 72ad050 for the
  right reasons (wrong exception type, mutated state, a silent inf accepted: "DID NOT RAISE")
  and pass on e0e82cf.
- **Vacuity checks.** The recovery gate fails with 2 trials per level; the TC-19 test rejects a
  1.5× hazard; the TC-08c test shows the joint fit is flat when the scale is free.

Limits of this audit: it was run by the same agent that did the work, on one machine; it is
not the independent human review that B-17 and SSOT §32 require.

## 7. Scores (1–100), initial → final this round

- Architecture 90 → 91
- Mathematical correctness 92 → 93
- Specification coverage 88 → 90
- Implementation 85 → 86
- Proof completeness 86 → 88
- Testing 89 → 92
- Reproducibility 89 → 89
- Documentation 85 → 88
- Publication readiness 66 → 68
- **Overall 85 → 87**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Push of apgi-lean: `git push` failed with "Permission denied (publickey)"; this round has
  therefore not run in CI.
- Push of apgi-implementation e0e82cf (refused from this session; F10), then the SSOT-P11
  closure and pin move.
- Author decisions: record-status approval (61a), operating point (B-13), OSF Amendment 2
  (B-14), SSOT text corrections (D1–D10), bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Out of this repository: SSOT-P10 and the clamp-fraction report in apgi-implementation; the
  K7 rerun; TC-25 end-to-end and TC-26 registered-fidelity checks; TC-08d–g need behavioral
  fitting of the full pipeline.
