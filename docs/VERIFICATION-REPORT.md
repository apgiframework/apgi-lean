# APGI formal verification: report (round 73, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 18951b65…. Production code is checked through pinned
cross-tests: apgi-implementation at the pin 8d8e5bd (every CI job green) and apgi-validation at
f6fec65.

Round 73 delta (details in docs/REMAINING-TASKS.md): the pin moved to 8d8e5bd; TC-10 passes
(production clamp fraction reported); SSOT-P10 is under test and one of its two suspicions is
refuted; three new production divergences are registered as strict xfails (SSOT-P12, SSOT-P13,
SSOT-V3); TC-04 now covers apgi_core.full_model. No Lean source changed.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A recovery result is a property of a model and a design, never
evidence for or against APGI (§17). Every figure below has a numerator and a denominator. The
previous round's report is in git history (cfa5b48).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready, and the production extension path
is not SSOT-conformant.** Every proof builds with `lake build --wfail`; every theorem's axioms
are pinned to Lean's standard axioms; every requirement is traced to a proof or a test or marked
as assumed, conditional or open. The default production core equals the reference step for
step. The hierarchical extension does not (SSOT-P10, SSOT-P12), a run with γ_NE ≠ 0 drops one NE
pathway (SSOT-P13), and apgi-validation's full model diverges after its first ignition
(SSOT-V3). Release still needs author and external work: 8 of the 18 SSOT release blockers are
open (B-07, B-09 remainder, B-11 tag and DOI, B-13, B-14, B-16, B-17, B-18), TC-25 and TC-26 are
not implemented, and decisions 71a and 62c are pending.

## 2. Evidence

Python, cloud workspace (Python 3.13, numpy 2.5.3; fresh public clones of apgi-lean cfa5b48,
apgi-implementation 8d8e5bd, apgi-validation f6fec65; the commands of the CI job):
- `generate_lean.py --check`: Spec.lean in sync with the registry (hash 65c1640b…).
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit).
- `make_traceability.py --check`, `production_report.py --check`: current.
- pytest with production: **343 passed, 1 skipped, 6 xfailed** (start of round: 335 passed);
  without production: 276 passed, 2 skipped.
- test_production_validation.py: **11 passed, 2 skipped, 3 xfailed** (start: 10 passed, 2 skipped).
- The same production tests and the report check under the CI's pinned numpy 2.2.6: 67 passed,
  6 xfailed; report current.

Lean, this PC (Windows, Lean 4.36.0, Mathlib v4.36.0), round-73 tree:
- `lake build --wfail`: **Build completed successfully (7248 jobs)**, 11:39–11:46 ET.

CI: "APGI verification" green on apgi-lean cfa5b48 (run 46029638355); apgi-implementation CI
green on every job at 8d8e5bd. Round 73 is not pushed, so its CI run is not observed.

## 3. Proof and test coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19); unchanged.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements (requirements.json): 44; by status 35 pass, 4 partial, 3 open, 2 not implemented.
- Conformance tests TC-01…TC-26: **20 pass, 4 partial, 2 not implemented** (TC-10 now passes).
  Partial: TC-01 (approval dates), TC-04 (apgi_core.full_model, SSOT-V3), TC-08 (dispositions;
  behavior-level recovery), TC-21. Not implemented: TC-25, TC-26.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Production divergences: apgi-implementation 3 open of 23, apgi-validation 1 open of 7 and one
  declared variant; every open one is a strict xfail.

## 4. What this round established

1. **TC-10 for production** (verification/reports/production-run-report.json): on 60 s of
   seeded stimulus-free input, CFG-CORE and CFG-CORE-R clamp on 0 % of steps, fire 38 and 253
   events, and report γ_sig·θ₀ = 0.7 and the floor 0.332, identical to apgi_ref on the same
   draws. With binding clamps the production fraction equals the reference's (0.38 precision,
   1.0 NE) and precision stays in [Π_min, Π_max].
2. **SSOT-P10**, the legacy hierarchical path: two precision definitions in one simulation,
   confirmed. The suspected double δ on the primary threshold is refuted (exactly one δ_reset
   per ignition, tested at δ = 0 and 0.2); the actual defect is a second δ value (0.5) on the
   reported resonance-level threshold.
3. **SSOT-P12 (new):** EQ-MS-4 implemented without /Π_max and written back into θ. Under
   stimulus-free input with κ_down = 0.1 the threshold sits at the 20 AU guard on 1117 of 4000
   steps, against none with κ_down = 0.
4. **SSOT-P13 (new):** with γ_NE ≠ 0 at default flags, production drops the NE threshold
   pathway that SSOT §11 and EQ-THEFF-1 require; with the flag set, it matches the reference.
5. **SSOT-V3 (new):** apgi_core.full_model shares the drive and the exact leak (S identical to
   the reference until the first ignition), then diverges: decision from S(t+1), no retention
   reset, a different threshold step.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Trajectory theorems assume `PipeAdmissible`; the TC-13 theorems add ε_stab > 0 and a
  nonnegative reference spread; `traj_S_mem_Icc` is conditional on bounded errors.
- Overflow, NaN and Inf are float64 properties; their handling is tested, not proved.
- The production clamp report is derived by apgi-lean from production's per-step outputs;
  production does not count clamped steps itself.
- The recovery study observes events, not reports (CL-46, assumed); its design constants are
  synthetic; τ_θ and η_θ·c₁ fail the §17 gate and await disposition (71a).
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis (CL-36); loop gain a
  design heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem
  connects the cusp normal form to the stochastic pipeline.
- The 17-step processing loop of the proposed SSOT is not adopted by SSOT §8; the canonical
  15-step pipeline is the one formalized (Apgi/Pipeline.lean), and the rejected orders are
  stated there as theorems about their difference.

## 6. Independent end-to-end audit

- **Fresh-clone reproduction.** The Python checks were run on fresh public clones of all three
  repositories at their pins, with the CI commands, and repeated under the CI's numpy pin.
- **Planted faults** (six, one at a time; .scratch/r73): production without the Πⁱ_eff clamp;
  a harness that never flags a clamp; production fixing SSOT-P13; production normalizing the
  PAC factor; a changed production r_max default; full_model with a retention reset. All six
  were caught. The first fault initially survived because no test input drove the
  interoceptive channel to Π_max; the test inputs were changed and the fault is now caught.
- **Xfail targeting.** Each of the 9 strict xfails was run with `--runxfail` and fails on its
  stated assertion, not on setup.
- **Experiments before tests.** Each new divergence was measured first (scripts in the round
  notes) and the test encodes the measured behavior, including one suspicion that the
  measurement refuted.

Limits of this audit: it was run by the same agent that did the work; it is not the independent
human review that B-17 and SSOT §32 require. The production repositories were read from public
clones but not modified.

## 7. Scores (1–100), initial → final this round

- Architecture 92 → 92
- Mathematical correctness 93 → 93
- Specification coverage 93 → 94
- Implementation 88 → 86 (three new divergences found; lower for better knowledge)
- Proof completeness 89 → 89
- Testing 94 → 95
- Reproducibility 90 → 91
- Documentation 89 → 90
- Publication readiness 69 → 69
- **Overall 89 → 89**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Pushes: only the author's github-apgi key can push. Pending: this round's apgi-lean commits.
- Production fixes (SSOT-P10, P12, P13 in apgi-implementation; SSOT-V3 in apgi-validation):
  those repositories were not writable from this session. The strict xfails will fail CI as
  soon as each fix lands, until the divergence is marked resolved and the pin moved.
- Author decisions: the §17 dispositions for τ_θ and η_θ·c₁ (71a), full_model aligned or
  declared a variant (62c), record-status approval (61a), operating point (B-13), OSF
  Amendment 2 (B-14), SSOT text corrections (D1–D10), bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Registry rows of 54b: need a full extraction run over the v1.1 corpus folder, which was not
  connected to this session; most rows carry no numeric value.
- Outside these repositories: TC-25 (assessment → scoring → storage → analysis) and TC-26 (the
  locked OSF record).
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that can be closed by more work here.
