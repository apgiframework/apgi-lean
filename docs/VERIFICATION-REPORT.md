# APGI formal verification: report (round 77, 2026-11-27)

Scope: the apgi-lean repository (Lean 4 proofs, the machine-readable registry, the Python
reference implementation and its tests) measured against the APGI Single Source of Truth
(SSOT), framework v1.2, sha256 b3ce0052… (unchanged this round). Production code is checked
through pinned cross-tests: apgi-implementation at 67a6c3f and apgi-validation at 604a3d9. The
locked OSF pre-registration (v1.1, Amendment 1) is checked through its sha256-pinned PDF.

Round 77 delta (details in docs/REMAINING-TASKS.md): Tables 12 (falsifiable hypothesis
register) and 13 (non-falsifiable, conditional or asymmetric commitments) of the locked
pre-registration are registered verbatim and verified against the PDF. One verifier now serves
every registered table. A cross-table check shows that the locked record gives three
prediction codes different severity tiers in Table 12 and Table 15 (F24). The SSOT's and the
v1.2 draft's copies of Tables 12 and 13 are checked against the locked rows (B-07, machine
half). No Lean source changed; Spec.lean was regenerated and rebuilt.

A Lean proof establishes a consequence of a definition. It is never evidence that APGI
describes the brain (SSOT §3.4). A registered hypothesis is a commitment, not a result. Every
figure below has a numerator and a denominator. The previous round's report is in git history
(caa6a83).

## 1. Verdict

**The formal and computational layers are publication-quality for a v1.2 verification
preprint; the framework release is not publication-ready.** Every proof builds with
`lake build --wfail`; every theorem's axioms are pinned to Lean's standard axioms; every
requirement is traced to a proof or a test or marked as assumed, conditional or open; 23 of 26
conformance tests pass and 2 are partial. Release still needs author and external work: 8 of
the 18 SSOT release blockers are open (B-07, B-09, B-11, B-13, B-14, B-16, B-17, B-18), TC-25 is
not implemented, TC-26 is partial, record approvals (61a) are pending, the locked register
has three internal tier conflicts to decide (F24), and round 77 is not pushed, so its CI is
not observed.

## 2. Evidence

This PC (Windows, Python 3.12.9, numpy 2.1.3, Lean 4.36.0, Mathlib v4.36.0),
`verification/verify_all.ps1` with apgi-implementation at a worktree of 67a6c3f, on the final
registry:
- `make_ssot_tables.py`: both SSOT copies current.
- Extraction: **158 verified, 0 failed** (98 parameters, 8 bridge/observable records,
  52 prediction-register records: 34 + 12 + 3 rows and three table completeness records).
  Start of round: 141.
- `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully
  (7248 jobs)**, exit 0.
- `check_consistency.py`: **3 open (acknowledged), 0 unacknowledged, 0 stale**. The three
  open items are the new register tier conflicts (KC-OSF-TIER-1F; KC-OSF-TIER-H5 on 3.C and
  3.D).
- apgi-lean pytest with production: **386 passed, 1 skipped** (start of round: 369 passed,
  1 skipped; the 17 new cases are the Tables 12/13 suite).
- test_production_validation.py at apgi-validation 604a3d9: **15 passed, 2 skipped** (SSOT-V1,
  declared variant).
- `make_report.py`: 196/196 theorems axiom-audited; Spec.lean hash equals the registry hash
  (516242ee…).
- Quotes cited for F24, checked with `find_quote.py --check` against the pinned PDF: "H5 ↔ Pred
  3.A, 3.B, 3.D" (p. 148) and "Pred 1.F is a secondary test (α = 0.05)" (p. 68), both found.

CI: round 76 (caa6a83) is green on GitHub (run 46081343683). Round 77 is not pushed: this
session has no push key.

## 3. Proof and test coverage

- Theorems: **196 in 10 modules** (Pilot 14, Dynamics 27, Core 19, Extensions 25, Coverage 34,
  Pipeline 27, Strata 13, Epistemic 11, Stability 7, Identifiability 19); no Lean source changed.
  189 depend on exactly [propext, Classical.choice, Quot.sound], 7 on a strict subset.
- Registered equations with a Lean-backed statement: 59 of 59.
- Requirements: 44; 38 pass, 2 partial, 3 open, 1 not implemented.
- Conformance tests TC-01…TC-26: **23 pass, 2 partial, 1 not implemented** (unchanged).
  Partial: TC-01 (approval dates), TC-26 (Tables 12, 13 and 15 only). Not implemented: TC-25.
- Claims: 46; 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Parameters: 99. Registered predictions: 34 rows, 42 codes. Registered hypotheses: 12
  falsifiable, 3 non-falsifiable, conditional or asymmetric (H1–H15 exactly once). All verified
  against the locked PDF.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7**
  and one declared variant.

## 4. What this round established

1. **The hypothesis register is machine-checked against the locked record.** The 12 rows of
   Table 12 (hypothesis, evidence tier, benchmark, falsifier, minimum n, severity) and the 3
   rows of Table 13 are in the registry verbatim. Extraction shows each row is on its pages,
   including five rows split across page breaks, and that the rows reproduce both tables
   exactly and in order.
2. **The locked register is internally inconsistent in two places (F24).** Pred 1.F is
   Severity A in Table 12 and B in Table 15, where p. 68 also calls it secondary. H5's range
   3.A–3.D is Severity A in Table 12, while Table 15 tiers 3.C and 3.D as B, and the record's
   own crosswalk maps H5 to 3.A, 3.B and 3.D. The registry records both readings and does not
   pick one.
3. **The v1.2 drafts have not drifted from the locked Tables 12 and 13.** The v1.2 OSF draft's
   copies equal the locked rows cell for cell. The SSOT's condensations name the same
   hypotheses with the same codes and tiers and state no number the locked row lacks; two
   numbers it writes as digits are words in the locked cells.
4. **Registry values are anchored to the locked rows.** The SSOT-sourced α_DFA band and its
   falsifier are the locked H8 row; α_psy = 10 is the H3 benchmark; the registry's citations of
   H7 and H10 name Table 13 entries.

## 5. What is conditional, assumed or open

The full list is generated in docs/assumption-inventory.md. The main items:

- Tables 12, 13 and 15 of the pre-registration are registered. The H↔Pred crosswalk (p. 148),
  Tables 16, 17 and 19, the exclusion and data-admissibility rules and the methods are not, and
  no analysis code is compared against the record (TC-26 remainder, application layer).
- The locked record contradicts itself on three severity tiers (1.F; 3.C and 3.D under H5).
  These are acknowledged open conflicts, not resolved: resolving them is the author's decision
  (erratum or Amendment 2).
- The draft-fidelity and SSOT-condensation checks run only where the untracked drafts exist
  (skipped in CI); extraction runs only where the corpus exists (CI checks the committed
  report by hash).
- The extraction's punctuation handling deletes private-use glyphs except where a per-source
  glyph map is registered (the OSF Table 12, 13 and 15 pages); minus signs are squashed everywhere,
  so a sign is never verified by quote matching alone, and "cell for cell" means equal up to
  whitespace, brackets and dashes.
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

- **Baseline first.** Round 76 (caa6a83) was confirmed on origin/main with CI green before any
  change; the round's start figures (141 verified, 369 passed) are round 76's verified final.
- **Planted faults.** Ten mutations of the registry, each checked against the real page text of
  the pinned PDF: a dropped row, an invented row, a changed falsifier threshold, a changed
  severity, a changed split-row tail, a changed κ band, a missing glyph, a cross-page row swap,
  and two tier mutations aimed at the conflict check (one hides a known conflict, one creates a
  new one). Nine were caught at once. The **cross-page swap was missed**, because page
  reproduction was checked page by page. The table-order check closed that gap, and all ten
  are now caught.
- **Full rerun on the final tree.** verify_all.ps1 ran on the final registry state (numbers in
  §2).
- **Clean clone, CI path.** A fresh clone of 36f137b, without the untracked drafts or the
  corpus: Spec.lean regenerates unchanged, consistency 3 open (acknowledged) / 0 / 0,
  traceability current; pytest with production at the pin **379 passed, 8 skipped** (387 in all,
  as locally). The skips are exactly the seven draft-dependent checks (three from earlier rounds,
  four new) and the separately run validation module. CI therefore exercises the committed
  extraction report and the cross-table checks, not the local files.

Limits of this audit: the same agent did the work and the audit, on one PC; round 77's CI has
not run; the second-reader check of B-07 and the independent review of B-17 are human steps
this audit does not replace. The F24 conflicts are reported from literal readings of verified
cells; whether a row-level tier was meant to cover a range of codes is a reading question for
the author.

## 7. Scores (1–100), initial → final this round

- Architecture 94 → 95
- Mathematical correctness 93 → 93
- Specification coverage 98 → 98
- Implementation 94 → 94
- Proof completeness 89 → 89
- Testing 98 → 98
- Reproducibility 93 → 93 (initial raised from round 76's 92: its CI is now observed green)
- Documentation 93 → 93
- Publication readiness 75 → 75
- **Overall 93 → 93**

Reasons for each score are in docs/REMAINING-TASKS.md ("Rating").

## 8. Genuine blockers

- Push: only the author's key can push. Pending: apgi-lean round 77 (two commits).
- Author decisions: F24 (tiers of 1.F, 3.C, 3.D; erratum or Amendment 2), record-status approval
  (61a), operating point (B-13), OSF Amendment 2 (B-14), SSOT text corrections D1–D8 and D12,
  bibliography (B-18).
- External work: independent reviewers (B-17), the second-reader check (B-07), the Zenodo tag
  and DOI (B-11).
- Feasible next here: register the H↔Pred crosswalk (p. 148) and Tables 16, 17 and 19 the same
  way (TC-26).
- Outside this repository: TC-25 and the analysis-code half of TC-26.
- Open research: the coupled Lyapunov conjecture (CL-26) and the H10 ordering (CL-36) are
  hypotheses, not proof targets that more work here can close.
