# APGI formal verification: report (round 76, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 b3ce0052… (round 75's text with regenerated registry-derived
parts). Production code is checked through pinned cross-tests: apgi-implementation at 67a6c3f
and apgi-validation at 604a3d9. The locked OSF pre-registration (v1.1, Amendment 1) is checked
through its sha256-pinned PDF.

Round 76 delta (details in docs/REMAINING-TASKS.md): the Master Prediction Register of the
locked pre-registration (OSF Table 15) is registered verbatim and verified against the PDF
(TC-26 becomes partial); the SSOT's condensed copy of that table is checked against it (B-07,
machine half, Table 15 only); the K7 identifiability and recovery gate table is rerun on a
clean commit and committed in apgi-implementation (task 60), after fixing the run manifest's
git state (F21). No Lean source changed; Spec.lean was regenerated and rebuilt.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A registered prediction is a commitment, not a result; a
recovery result is a property of a model and a design (§17). Every figure below has a numerator
and a denominator. The previous round's report is in git history (dc31ddf).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`; every theorem's axioms are pinned to Lean's standard axioms; every
requirement is traced to a proof or a test or marked as assumed, conditional or open; 23 of 26
conformance tests pass and 2 are partial. Release still needs author and external work: 8 of
the 18 SSOT release blockers are open (B-07, B-09, B-11, B-13, B-14, B-16, B-17, B-18), TC-25 is
not implemented and TC-26 is a first slice, record approvals (61a) are pending, and round 76 is
not pushed, so its CI is not observed.

## 2. Evidence

This PC (Windows, Python 3.12.9, numpy 2.1.3, Lean 4.36.0, Mathlib v4.36.0),
`verification/verify_all.ps1` with apgi-implementation at a worktree of 67a6c3f:
- `make_ssot_tables.py`: both SSOT copies current (re-pinned once this round, to b3ce0052…,
  when TC-26's new status entered the generated parts).
- Extraction: **141 verified, 0 failed** (98 parameters, 8 bridge/observable records,
  34 prediction rows and the OSF Table 15 completeness record). Start of round: 106 verified.
- `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully
  (7248 jobs)**, exit 0 (at the start of the round and on the final tree).
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale (includes the axiom audit and the
  new prediction-register check).
- apgi-lean pytest with production: **369 passed, 1 skipped** (start of round: 360 passed,
  1 skipped; the 9 new tests are the prediction-register suite).
- test_production_validation.py at apgi-validation 604a3d9: **15 passed, 2 skipped** (SSOT-V1,
  declared variant).
- `make_report.py`: 196/196 theorems axiom-audited; Spec.lean hash equals the registry hash
  (e4b80c7b…).
- apgi-implementation 28de9af (pin unchanged at 67a6c3f): tests/test_tools.py 9 passed; mypy
  clean on tools/run_k7.py; ruff format clean. K7 rerun: 3425 s, clean tree.

CI: round 75 (dc31ddf) is green on GitHub (run 46065467794; Lean, Python 3.11 and 3.12,
apgi-validation cross-check, report). Round 76 is not pushed.

## 3. Proof and test coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19); no Lean source changed.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements: 44; 38 pass, 2 partial, 3 open, 1 not implemented.
- Conformance tests TC-01…TC-26: **23 pass, 2 partial, 1 not implemented** (round 75: 23, 1, 2).
  Partial: TC-01 (approval dates), TC-26 (Table 15 only). Not implemented: TC-25.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Parameters: 99. Registered predictions: 34 rows, 42 codes, all verified against the locked PDF.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7**
  and one declared variant.

## 4. What this round established

1. **The registered decision rules are machine-checked against the locked record.** The 34 rows
   of OSF Table 15 (classification standard, severity, HEP dependence, fallback) are in the
   registry verbatim; extraction proves each row is on its page of the pinned PDF and that the
   rows reproduce the table exactly.
2. **The v1.2 drafts have not drifted from the locked register.** The v1.2 OSF draft's Table 15
   equals the locked one cell for cell; the SSOT's condensed copy agrees on every code, tier,
   label and number, with one number (BF₁₀ ≥ 100 for Pred 0.B) traced to p. 69 of the same
   record.
3. **The K7 gate table is versioned.** A clean rerun on 5802bf2 reproduces the round-75 run bit for bit (K7a and K7c digests); desk-exposable: θ_base and the precision-weighted learning composite; α and Π individually non-identifiable, β fails recovery; nothing production-exposable while K7b awaits data.
4. **Run provenance is honest.** K7 manifests no longer report a clean commit as dirty (F21).

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Only Table 15 of the pre-registration is registered. Tables 12, 13, 16, 17 and 19, the
  exclusion and data-admissibility rules and the methods are not, and no analysis code is
  compared against the record (TC-26 remainder, application layer).
- The draft-fidelity and SSOT-condensation checks run only where the untracked drafts exist
  (skipped in CI); extraction runs only where the corpus exists (CI checks the committed
  report by hash).
- The extraction's punctuation handling deletes private-use glyphs except where a per-source
  glyph map is registered (only the OSF Table 15 pages); minus signs are squashed everywhere,
  so a sign is never verified by quote matching alone.
- Trajectory theorems assume `PipeAdmissible`; the TC-13 theorems add ε_stab > 0 and a
  nonnegative reference spread; `traj_S_mem_Icc` is conditional on bounded errors.
- The recovery study observes events, not reports (CL-46, assumed); the dispositions and the
  20 % gate are proposed readings pending OSF Amendment 2. K7 gate decisions stay
  provisional: K7b needs data and the mathematical-contracts file (S1-REG-04) is not qualified,
  so nothing is production-exposable.
- Unchanged: Lyapunov only at loop gain 0 (CL-26 open); H10 a hypothesis (CL-36); loop gain a
  design heuristic; the Tier-3 → Tier-2 bridge unresolved; κ without a value; no theorem
  connects the cusp normal form to the stochastic pipeline.
- The 17-step processing loop of the proposed SSOT is not adopted by SSOT §8; the canonical
  15-step pipeline is the one formalized (Apgi/Pipeline.lean), and the rejected orders are
  stated there as theorems about their difference.

## 6. Independent end-to-end audit

- **Baseline first.** The round started by rebuilding and retesting dc31ddf unchanged with
  verify_all.ps1 (360 passed, 1 skipped; lake green), so every later figure has a "before".
- **Planted faults, three suites.** Register verifier against the real page text: 7 faults,
  all caught. SSOT condensation test against a temporary altered copy: 5 faults, all caught.
  run_k7 git-state test: 1 fault (planted byte-exactly with Python and restored), caught.
- **A fix that broke something was caught by the existing checks.** Applying the glyph map to
  every PDF failed three Math Spec parameter quotes; the map was made per source and the
  extraction returned to 106 + 35 verified, 0 failed.
- **Determinism.** Two K7 runs in separate processes (49 and 57 minutes long; commits 67a6c3f and 5802bf2, identical K7 code) produced identical K7a and K7c results (sha256 630cff21…, 938a6026…); the regenerated reports differed from the committed ones only in timestamps and the numpy field.
- **Full rerun on the final tree.** verify_all.ps1 ran again on the final registry state
  (numbers in §2).
- **Clean clone, CI path.** A fresh clone of 6f97bcf, without the untracked drafts or the
  corpus: Spec.lean in sync, consistency 0/0/0, traceability current, pytest 366 passed,
  4 skipped; the skips are exactly the three draft-dependent checks and the separately run
  validation module, so CI exercises the committed reports, not the local files.

Limits of this audit: it was run by the same agent that did the work, on one PC; round 76's CI
has not run; the second-reader check of B-07 and the independent review of B-17 are human
steps this audit does not replace.

## 7. Scores (1–100), initial → final this round

- Architecture 93 → 94
- Mathematical correctness 93 → 93
- Specification coverage 97 → 98
- Implementation 93 → 94
- Proof completeness 89 → 89
- Testing 97 → 98
- Reproducibility 91 → 92 (initial raised from round 75's 90: its CI is now observed green)
- Documentation 92 → 93
- Publication readiness 73 → 75
- **Overall 92 → 93**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Pushes: only the author's key can push. Pending: apgi-implementation (5802bf2 and the K7
  commit; the pin does not move) and apgi-lean round 76.
- Author decisions: record-status approval (61a), operating point (B-13), OSF Amendment 2
  (B-14), SSOT text corrections D1–D8 and the new D12 (blocker-table statuses), bibliography
  (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Feasible next here: register OSF Tables 12 and 13 the same way (falsifiers, tiers, minimum
  N), which completes the machine half of B-07 and extends TC-26.
- Outside this repository: TC-25 (assessment → scoring → storage → analysis) and the
  analysis-code half of TC-26.
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that more work here can close.
