# APGI formal verification: report (round 75, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, now sha256 582a09b9… (the round-74 text, 18951b65…, plus the
generated parts of D10 and the D11 row). Production code is checked through pinned
cross-tests: apgi-implementation at 67a6c3f and apgi-validation at 604a3d9.

Round 75 delta (details in docs/REMAINING-TASKS.md): apgi-validation's full model is aligned
with the SSOT core (task 62c, SSOT-V3 resolved, TC-04 passes); the §17 dispositions are
recorded (task 71a, TC-08 passes); 13 parameter rows are registered (task 54b), 11 as label
rows that state the SSOT's value rule instead of an invented value; the SSOT's
registry-derived parts are generated from the registry (D10, TC-21 passes) and its §17 table
gains the c₂ × δ_reset row (D11). No Lean source changed; Spec.lean was regenerated and
rebuilt.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A recovery result is a property of a model and a design, never
evidence for or against APGI (§17). Every figure below has a numerator and a denominator. The
previous round's report is in git history (680877b).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint, and both production packages now conform to the SSOT on every registered
divergence; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`; every theorem's axioms are pinned to Lean's standard axioms; every
requirement is traced to a proof or a test or marked as assumed, conditional or open; 23 of 26
conformance tests pass. Release still needs author and external work: 8 of the 18 SSOT release
blockers are open (B-07, B-09 review, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-25 and
TC-26 are not implemented, record approvals (61a, TC-01) are pending, and round 75 is not
pushed, so its CI is not observed.

## 2. Evidence

This PC (Windows, Python 3.12.9, numpy 2.1.3, Lean 4.36.0, Mathlib v4.36.0),
`verification/verify_all.ps1` with apgi-implementation at 67a6c3f, 15:14–15:33 ET:
- `make_ssot_tables.py`: both SSOT copies current; SRC-SSOT-V12D re-pinned.
- Extraction: **106 verified, 0 failed** (98 parameters, 8 bridge/observable records).
- `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully
  (7248 jobs)**, exit 0.
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit).
- apgi-lean pytest with production: **360 passed, 1 skipped** (start of round: 357 passed,
  1 skipped). Repeated with junit at 15:34–15:37: 360 passed, 1 skipped.
- test_production_validation.py at apgi-validation 604a3d9: **15 passed, 2 skipped** (SSOT-V1,
  declared variant). At the start of the round: 11 passed, 2 skipped, 3 xfailed.
- `make_report.py`: 196/196 theorems axiom-audited; Spec.lean hash equals the registry hash;
  6 of 7 pilot criteria (the seventh needs a CI run).
- apgi-validation, tests importing apgi_core (19 files): 432 passed, 21 skipped, 4 failed; the
  same 4 fail at f6fec65 (environment). ruff, black, isort clean on full_model.py.

CI: apgi-lean 680877b (run 46056666564) failed in its Python jobs at the checkout of
apgi-implementation 67a6c3f, which was pushed only during this round; its Lean and
apgi-validation jobs passed. Round 75 (apgi-lean 2a6c96b, 3f28c72, fe3dcba, a1a9f4b and this
report; apgi-validation 604a3d9) is not pushed.

## 3. Proof and test coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19); no Lean source changed.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements: 44; 38 pass, 1 partial, 3 open, 2 not implemented.
- Conformance tests TC-01…TC-26: **23 pass, 1 partial, 2 not implemented** (round 74: 20, 4, 2).
  Partial: TC-01 (approval dates). Not implemented: TC-25, TC-26.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Parameters: 99, all with a value, a range or a stated value rule, all extraction-verified
  except computed constants.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7**
  and one declared variant.

## 4. What this round established

1. **TC-04 for both production packages.** apgi_core.full_model equals apgi_ref.core_step in
   S, θ, Bₜ and B(t) for 600 seeded steps, with the default (minimal) settings and with every
   allostatic term on and the θ floor binding.
2. **§17 is closed procedurally.** Every quantity that fails the recovery gate has exactly one
   author-recorded disposition (requires auxiliary measurement), checked against the committed
   recovery report.
3. **No invented values.** The 11 label rows carry the SSOT's own value rule (computed,
   participant-estimated, catch-trial rate, uncalibrated, no decision weight); the checker
   accepts a rule in place of a value only when evidence is attached.
4. **The SSOT no longer drifts from the registry.** Its header and verification sections are
   generated; the stale figures were spec 0.3.1, 41 theorems, 25 golden vectors, 16 claims.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Trajectory theorems assume `PipeAdmissible`; the TC-13 theorems add ε_stab > 0 and a
  nonnegative reference spread; `traj_S_mem_Icc` is conditional on bounded errors.
- Overflow, NaN and Inf are float64 properties; their handling is tested, not proved.
- full_model's comparison covers θ_eff = θ: it has no NE, 5-HT, refractory or urgency term.
- The recovery study observes events, not reports (CL-46, assumed); its design constants are
  synthetic; the dispositions and the 20 % gate are proposed readings pending OSF Amendment 2.
- The SSOT generation check runs only where the untracked v1.2 draft exists (skipped in CI).
- K7 rerun on 67a6c3f (task 60) started, not finished.
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis (CL-36); loop gain a
  design heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem
  connects the cusp normal form to the stochastic pipeline.
- The 17-step processing loop of the proposed SSOT is not adopted by SSOT §8; the canonical
  15-step pipeline is the one formalized (Apgi/Pipeline.lean), and the rejected orders are
  stated there as theorems about their difference.

## 6. Independent end-to-end audit

- **Baseline first.** The round started by rebuilding and retesting 680877b unchanged, so every
  later figure has a measured "before".
- **XPASS before resolve.** The three SSOT-V3 strict xfails were run against the aligned
  full_model and XPASSed before the registry entry was changed.
- **Planted faults** (eight, one at a time, in a scratch copy of the aligned full_model): all
  caught; five were caught only by the new all-terms-on trajectory test, which is why it was
  added.
- **Regression scope.** apgi-validation's apgi_core tests were run before and after the change
  (git stash); the result is identical (432 passed, 4 environment failures both times).
- **Quotes verified twice.** Every 54b evidence quote was checked against the pinned page with
  extract_sources' own matching before it entered the registry, then by the full extraction run.
- **Reproducibility of the study.** The recovery report regenerated under numpy 2.1.3 matched
  the committed one (numpy 2.2.6) in everything but the numpy field.

Limits of this audit: it was run by the same agent that did the work, on one PC; the full
apgi-validation suite and the round-75 CI have not run; it is not the independent human review
that B-17 and SSOT §32 require.

## 7. Scores (1–100), initial → final this round

- Architecture 92 → 93
- Mathematical correctness 93 → 93
- Specification coverage 95 → 97
- Implementation 90 → 93
- Proof completeness 89 → 89
- Testing 96 → 97
- Reproducibility 89 → 90 (initial lowered from 91: CI red on 680877b; round 75 not pushed)
- Documentation 90 → 92
- Publication readiness 70 → 73
- **Overall 90 → 92**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Pushes: only the author's key can push. Pending: apgi-validation 604a3d9 first (the
  apgi-lean CI checks it out), then apgi-lean.
- Author decisions: record-status approval (61a, the last partial TC), operating point (B-13),
  OSF Amendment 2 (B-14), SSOT text corrections D1–D8, bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Outside this repository: TC-25 (assessment → scoring → storage → analysis); TC-26 needs the
  locked OSF record's methods, exclusions and outcome classifications registered.
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that more work here can close.
