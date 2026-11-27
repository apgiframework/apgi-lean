# APGI formal verification: report (round 72, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 18951b65…. Production code is checked through pinned
cross-tests: apgi-implementation at the pin d153f6a (pushed; contains the SSOT-P11 fix
e0e82cf) and apgi-validation at f6fec65.

Round 72 delta (details in docs/REMAINING-TASKS.md): SSOT-P11 resolved and the pin moved to
d153f6a; TC-13 / REQ-TC-13 pass; apgi-lean pytest 335 passed, 0 xfailed (Linux VM, production at
d153f6a); CI observed green on apgi-lean 7aec2c0 and on every apgi-implementation job at d153f6a
except "lint & types" (F13, red since 72ad050; fix prepared as a patch, ruff and mypy clean,
production suite 2840 passed, 0 failed). Sections 2–6 below are the round 70–71 evidence; only
the counts in section 3 and the scores in section 7 are updated.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A recovery result is a property of a model and a design, never
evidence for or against APGI (§17). Every figure below has a numerator and a denominator. The
previous round's report is in git history (6167b48).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`; every theorem's axioms are pinned to Lean's standard axioms; every
requirement is traced to a proof or a test or marked as assumed, conditional or open. TC-08 now
has all four diagnostics §17 requires, and they show that τ_θ and η_θ·c₁ are not recovered even
from every-step event data. That calls for an author disposition (task 71a). Release still
needs author and external work: 8 of the 18 SSOT release blockers are open (B-07, B-09
remainder, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-25 and TC-26 are not
implemented, and nothing from this round or the production fixes is pushed.

## 2. Evidence (this PC, final tree, production at the pin 72ad050)

`verification\verify_all.ps1 -Impl .scratch\impl-pin`, 2026-11-27 08:45–09:01 ET:
- Source extraction: 93 of 93 records verified against the sha256-pinned corpus.
- `generate_lean.py`: Spec.lean regenerated from the current registry.
- `lake build --wfail`: **Build completed successfully (7248 jobs)**, 10 APGI modules plus the
  generated Spec.lean, all rebuilt because Spec.lean changed.
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit: no
  sorry, no admit, no axiom declaration, no non-standard axiom; no orphan or unaudited theorem).
- `make_release_manifest.py`, `make_traceability.py`: regenerated.
- `make_recovery_report.py`: the TC-08d–g study, 152 s; identical to the run 25 minutes earlier.
- pytest with the pinned apgi-implementation: **331 passed, 1 skipped, 4 xfailed** (start of
  round: 312 passed; the four strict xfails are SSOT-P11; the skip is the validation module
  without its path).
- test_production_validation.py (pinned apgi-validation): 10 passed, 2 skipped (declared variant).
- apgi-implementation d153f6a: tests/test_estimation_pymc.py and
  tests/test_remaining_coverage_fixes.py, 18 passed (previously 6 of them failed); the full
  production suite was not rerun after this commit.
- CI: not observed from this session for this round or the previous one (no push possible, §8).

## 3. Proof coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19). Start of round: 187.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements (requirements.json): 44; by status 34 pass, 5 partial, 3 open, 2 not implemented.
- Conformance tests TC-01…TC-26: **19 pass, 5 partial, 2 not implemented** (TC-13 now passes).
  Partial: TC-01 (approval dates), TC-04 (apgi_core.full_model), TC-08 (dispositions for two
  failed parameters; behavior-level recovery), TC-10 (production clamp fraction), TC-21. Not implemented: TC-25, TC-26.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).

## 4. What this round established

1. **TC-08g, exact part** (`traj_scaleAllo`, `scaleAllo_not_injective`, `traj_weights_eta_zero`):
   η_θ and the weights c₁, c₂, v₁, v₂ enter every trajectory only as η_θ·c₁, η_θ·c₂, η_θ·v₁,
   η_θ·v₂; with η_θ = 0 the weights do not enter. η_θ is unidentifiable apart from the weights
   from any data.
2. **TC-08d–g, the statistical part**, on the canonical pipeline (twin-checked against the
   reference to 1e-12), with every-step event observation (an upper bound on behavior, CL-46),
   30 synthetic subjects per block, exact grid posteriors:
   - passes the §17 gate: k_V = η_θ·v₁ (r 0.904 / 0.917 in two designs), γ_NE (0.976), g_NE
     (0.907), γ_sig with the precision scale free (0.985), the precision scale (0.932);
   - fails: τ_θ (r 0.753 / 0.480) and k_C = η_θ·c₁ (r 0.30 / 0.36, flat profile likelihood);
   - declared trade-offs measured: τ_θ ~ k_V −0.79 (TC-08e), γ_NE ~ g_NE +0.20 (TC-08d),
     γ_sig ~ Π̄ scale +0.18 (TC-08f), k_C ~ k_V −0.04 (TC-08g);
   - SBC p > 0.29 for every quantity; out-of-sample, the posterior predictive beats the null
     in every block and lies within 0.6 nats of the truth.
   A slow block design was tested as a way to separate adaptation from recovery and did not.
3. **F11 is a code defect, fixed** in apgi-implementation d153f6a: a deprecated pytensor API
   (which `filterwarnings = error` turned into five failures) and a platform-encoding read.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Trajectory theorems assume `PipeAdmissible`; the TC-13 theorems add ε_stab > 0 and a
  nonnegative reference spread; `traj_S_mem_Icc` is conditional on bounded errors.
- Overflow, NaN and Inf are float64 properties; their handling is tested, not proved.
- The recovery study observes events, not reports; its upper-bound reading rests on CL-46
  (assumed, standard, not formalized). Its design constants (inputs, durations, r_max = 5/s,
  composite-gain ranges, grids, seeds) are synthetic; the 20% gate is a proposed reading
  pending amendment. η_θ·c₂ and η_θ·v₂ are held at 0.
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis (CL-36); loop gain a
  design heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem
  connects the cusp normal form to the stochastic pipeline; SSOT-P10 open in production.

## 6. Independent end-to-end audit

- **Clean rebuild.** The final routine re-ran extraction, generation, the full Lean build,
  consistency, the manifest, traceability, the recovery study and both pytest suites on the
  final tree, with production at the pin.
- **Planted faults** (`.scratch\r70\mutate.py`): five faults, one at a time, all caught: V
  channels swapped and θ used for θ_eff in the study simulator (twin test), event and non-event
  log-likelihood swapped (likelihood check), `scaleAllo` without scaling η and the weights
  theorem without η = 0 (both proofs fail).
- **Vacuity checks.** SBC rejects a likelihood with r_max off by 2× (p < 0.001); the k_C
  profile is shown flat, not assumed flat; the TC-08g twins hold exactly in float64 for
  power-of-two scalings.
- **Determinism.** Two runs of the study 25 minutes apart gave identical reports.

Limits of this audit: it was run by the same agent that did the work, on one machine; it is
not the independent human review that B-17 and SSOT §32 require.

## 7. Scores (1–100), initial → final this round

- Architecture 92 → 92
- Mathematical correctness 93 → 93
- Specification coverage 92 → 93
- Implementation 87 → 88
- Proof completeness 89 → 89
- Testing 94 → 94
- Reproducibility 89 → 90
- Documentation 89 → 89
- Publication readiness 69 → 69
- **Overall 88 → 89**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Pushes: only the author's github-apgi key can push. Pending: this round's apgi-lean commit
  and the F13 patch for apgi-implementation (`git am`, then push). CI is now observable.
- Author decisions: the §17 dispositions for τ_θ and η_θ·c₁ (71a), record-status approval
  (61a), operating point (B-13), OSF Amendment 2 (B-14), SSOT text corrections (D1–D10),
  bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Out of this repository: SSOT-P10 and the clamp-fraction report in apgi-implementation; the
  K7 rerun; TC-25 end-to-end and TC-26 registered-fidelity checks.
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that can be closed by more work here.
