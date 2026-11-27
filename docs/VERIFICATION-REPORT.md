# APGI formal verification: report (round 74, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 18951b65…. Production code is checked through pinned
cross-tests: apgi-implementation at the pin 67a6c3f and apgi-validation at f6fec65.

Round 74 delta (details in docs/REMAINING-TASKS.md): the three open apgi-implementation
divergences (SSOT-P10, P12, P13) are fixed in production (67a6c3f) and resolved in the registry;
a fourth defect class (every legacy-path threshold modulation written back into θ) was fixed
with them; F17 (a score above its range and two flaky tests) fixed; the recovery study now
covers η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair. No Lean source changed.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A recovery result is a property of a model and a design, never
evidence for or against APGI (§17). Every figure below has a numerator and a denominator. The
previous round's report is in git history (3dd4d68).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint, and apgi-implementation now conforms to the SSOT on every registered divergence; the
framework release is not publication-ready.** Every proof builds with `lake build --wfail`;
every theorem's axioms are pinned to Lean's standard axioms; every requirement is traced to a
proof or a test or marked as assumed, conditional or open. The default production core equals
the reference step for step, and the hierarchical extension now follows EQ-MS-4, TC-11 and the
one-precision rule. apgi-validation's full model still diverges after its first ignition
(SSOT-V3, decision 62c). Release needs author and external work: 8 of the 18 SSOT release
blockers are open (B-07, B-09 remainder, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-25
and TC-26 are not implemented, and decisions 71a and 62c are pending. Round 74 is not yet
pushed, so its CI is not observed.

## 2. Evidence

Python, cloud workspace (Python 3.13, numpy 2.5.3; fresh public clones of apgi-lean,
apgi-implementation and apgi-validation, plus the round's commits; the commands of the CI jobs):
- `generate_lean.py --check`, `make_traceability.py --check`, `production_report.py --check`,
  `make_recovery_report.py --check`: current.
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit).
- apgi-lean pytest with production: **357 passed, 1 skipped, 0 xfailed** (start of round: 343
  passed, 6 xfailed); without production: 278 passed, 2 skipped. Same result under the CI pin
  (Python 3.12, numpy 2.2.6).
- test_production_validation.py: 11 passed, 2 skipped, 3 xfailed (SSOT-V3), unchanged.
- apgi-implementation 67a6c3f: ruff and ruff format clean; mypy clean (105 files);
  `pytest -m "not performance"` **2839 passed, 11 skipped**, branch coverage 96.66 %
  (gate 90 %); performance 5 passed; conformance/repeatability 31 passed.

Lean, this PC (Windows, Lean 4.36.0, Mathlib v4.36.0):
- `lake build --wfail` on a88abba: **Build completed successfully (7248 jobs)**, 13:41–13:51 ET.
- `lake build --wfail` on 72a25fa (the final Spec.lean; the docs commit changes no Lean file):
  **Build completed successfully (7248 jobs)**, exit 0, finished 14:06 ET.

CI: "APGI verification" green on apgi-lean 3dd4d68 (run 46045899533); apgi-implementation CI
green on every job at 8d8e5bd (run 46029607584). Round 74 (apgi-lean a88abba, 72a25fa and this
report; apgi-implementation 67a6c3f) is not pushed.

## 3. Proof and test coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19); no Lean source changed.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements (requirements.json): 44; by status 35 pass, 4 partial, 3 open, 2 not implemented.
- Conformance tests TC-01…TC-26: **20 pass, 4 partial, 2 not implemented** (unchanged).
  Partial: TC-01 (approval dates), TC-04 (apgi_core.full_model, SSOT-V3), TC-08 (dispositions;
  behavior-level recovery), TC-21. Not implemented: TC-25, TC-26.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Production divergences: apgi-implementation **0 open of 22** (earlier reports wrote "of 23", a
  miscount), apgi-validation 1 open of 7 (SSOT-V3, a strict xfail) and one declared variant.

## 4. What this round established

1. **SSOT-P13 fixed:** with γ_NE ≠ 0 at the defaults, production now applies both NE pathways
   with one clamped g_NE and matches apgi_ref step for step over 2000 steps (γ_NE = 0.2, −0.3).
   The config schema had rejected exactly the SSOT configuration (both pathways; γ_NE ≥ 0.1) and
   carried a γ_NE default of 0.1 with a sign bound; both corrected.
2. **SSOT-P12 fixed, and a wider defect with it:** EQ-MS-4 with /Π_max and the [0.5, 1.5] band;
   in the legacy path NE, 5-HT, circadian and hierarchical modulation all became read-outs (all
   four had been written back into θ). The staging golden master, which had ended at the 20 AU
   guard, now ends at 1.833 AU; prod and dev are bit-identical.
3. **SSOT-P10 fixed:** one precision definition with the ODE on; one δ_reset value.
4. **F17:** a maturity score reached 516 on a 0–100 scale; two production tests failed about
   one run in five. Fixed and seeded.
5. **Recovery (TC-08g remainder):** η_θ·c₂ (r 0.803, error 0.157) and η_θ·v₂ (r 0.580) fail §17
   at this design; c₂·B(t−1) and δ_reset·B(t) are confounded (correlation −0.59, both fail),
   a degeneracy the SSOT §17 table does not list (proposed correction D11).

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Trajectory theorems assume `PipeAdmissible`; the TC-13 theorems add ε_stab > 0 and a
  nonnegative reference spread; `traj_S_mem_Icc` is conditional on bounded errors.
- Overflow, NaN and Inf are float64 properties; their handling is tested, not proved.
- The production clamp report is derived by apgi-lean from production's per-step outputs;
  production does not count clamped steps itself.
- The recovery study observes events, not reports (CL-46, assumed); its design constants are
  synthetic. At this design τ_θ, η_θ·c₁, η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair fail the §17
  gate and await disposition (71a); of the allostatic quantities only η_θ·v₁ passes.
- Results computed with apgi-implementation's hierarchical path, or with γ_NE ≠ 0 at the old
  defaults, before 67a6c3f are not SSOT-model results and need a versioned rerun (task 60).
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis (CL-36); loop gain a
  design heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem
  connects the cusp normal form to the stochastic pipeline.
- The 17-step processing loop of the proposed SSOT is not adopted by SSOT §8; the canonical
  15-step pipeline is the one formalized (Apgi/Pipeline.lean), and the rejected orders are
  stated there as theorems about their difference.

## 6. Independent end-to-end audit

- **Fresh-clone reproduction.** The Python checks ran on fresh public clones with the CI
  commands and under both numpy pins; the round's commits were moved to the author's PC as git
  bundles, so the local commits carry the same hashes as the tested ones.
- **XPASS before resolve.** The six SSOT-P10/P12/P13 strict xfails were run against the fix and
  XPASSed (failing CI as designed) before the registry was changed.
- **Planted faults** (seven, one at a time, in a scratch copy of 67a6c3f): P13 default off;
  /Π_max removed; band removed; PAC write-back restored; ODE drive off; `or 0.5` restored;
  NE/5-HT write-back. Two (band removed, PAC write-back) **survived** the existing tests; three
  sharper tests were added and all seven are now caught.
- **Regression scope.** The default path was shown unchanged three ways: bit-identical prod and
  dev golden masters, an unchanged production run report, and the unchanged 0.0 / 38 / 253
  event counts. The one changed trajectory (staging) was measured before its digest was
  regenerated.
- **Pre-existing flakiness separated from regressions.** The two intermittent failures were
  reproduced at the base commit 8d8e5bd (3 of 15 runs each) before they were fixed.

Limits of this audit: it was run by the same agent that did the work; it is not the independent
human review that B-17 and SSOT §32 require.

## 7. Scores (1–100), initial → final this round

- Architecture 92 → 92
- Mathematical correctness 93 → 93
- Specification coverage 94 → 95
- Implementation 86 → 90 (every apgi-implementation divergence resolved; SSOT-V3 remains)
- Proof completeness 89 → 89
- Testing 95 → 96
- Reproducibility 91 → 91 (round 74 not pushed, CI not observed)
- Documentation 90 → 90
- Publication readiness 69 → 70
- **Overall 89 → 90**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Pushes: only the author's github-apgi key can push. Pending: apgi-implementation 67a6c3f
  first (the apgi-lean CI checks it out), then apgi-lean.
- SSOT-V3 in apgi-validation: needs decision 62c (align or declare a variant).
- Author decisions: the §17 dispositions (71a: τ_θ, η_θ·c₁, η_θ·c₂, η_θ·v₂, c₂ / δ_reset),
  62c, record-status approval (61a), operating point (B-13), OSF Amendment 2 (B-14), SSOT text
  corrections (D1–D11), bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Registry rows of 54b: need a full extraction run over the v1.1 corpus folder, which is not
  connected to this session; most rows carry no numeric value.
- Outside these repositories: TC-25 (assessment → scoring → storage → analysis) and TC-26 (the
  locked OSF record).
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that can be closed by more work here.
