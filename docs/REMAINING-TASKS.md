# APGI verification: remaining tasks

State as of 2026-11-27 17:55 ET (round 76). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, now sha256 b3ce0052…, pinned as SRC-SSOT-V12D; only its generated parts changed this round). Registry **spec 0.6.0**, now twelve files with specification/hypotheses.json, registry hash e4b80c7b… (Apgi/Spec.lean).

- Repositories, all `main` only:
  - apgi-lean: round 75 (dc31ddf) is on origin/main and its CI is **green** (run 46065467794: Lean, both Python jobs, apgi-validation cross-check, report). Round 76 is local, **not pushed**: dcd0623 (TC-26 first slice), 6f97bcf (SSOT condensation check), the docs commit (docs).
  - apgi-implementation: pin **67a6c3f** unchanged (the apgi-lean CI checks it out). Local main is two commits ahead, **not pushed**: 5802bf2 (F21, run_k7 git state) and 28de9af (task 60, K7 gate table). Neither touches the core, so the pin stays.
  - apgi-validation: pin 604a3d9, pushed by the author in round 75; unchanged.
  - **Push order:** apgi-implementation, then apgi-lean (either order works: the apgi-lean CI checks out the unchanged pin 67a6c3f).
- Round 76 checks (this PC, Windows, Python 3.12.9, numpy 2.1.3; `verify_all.ps1` with -Impl at a worktree of 67a6c3f): SSOT tables current (SRC-SSOT-V12D re-pinned once, to b3ce0052…, when TC-26's status entered the generated parts); extraction **141 verified, 0 failed** (98 parameters, 8 bridge records, 35 prediction-register records); `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully (7248 jobs)**, exit 0; consistency 0 open, 0 unacknowledged, 0 stale; manifest, traceability and production reports regenerated; apgi-lean pytest with production **369 passed, 1 skipped** (start of round: 360 passed, 1 skipped); test_production_validation.py at 604a3d9 **15 passed, 2 skipped**; make_report.py: 196/196 theorems axiom-audited, Spec.lean hash equals the registry hash. The recovery report regenerated under numpy 2.1.3 differs from the committed one (numpy 2.2.6, the CI pin) only in its numpy field and was not recommitted. Clean clone of 6f97bcf without drafts or corpus (the CI path): Spec.lean in sync, consistency 0/0/0, traceability current, pytest 366 passed, 4 skipped (the three draft-dependent checks and the validation module).
- Rating against the SSOT (1–100, nine dimensions): **overall 92 → 93**. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07 (machine half done for Table 15 only; Tables 12 and 13 and the second reader remain), B-09, B-11, B-13, B-14, B-16, B-17, B-18. The SSOT's own §30.1 table still lists B-05, B-10, B-12 and B-15 as open (F22).
- Conformance tests TC-01…TC-26: **23 pass**, **2 partial** (TC-01, approval dates; TC-26, first slice), **1 not implemented** (TC-25).
- Lean: **196 theorems in 10 modules** (unchanged), every one axiom-pinned with `#guard_msgs`; no sorry, no admit, no axiom declaration. No Lean source changed; Spec.lean regenerated (new registry hash) and rebuilt.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: 46: 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (38 pass, 2 partial, 3 open, 1 not implemented).
- Parameters: 99. Registered predictions: **34 rows, 42 codes** (OSF Table 15), all PDF-verified.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7**, 1 declared variant (SSOT-V1).

## Done this round (2026-11-27, round 76)

**Initial audit.** HEAD dc31ddf rebuilt and retested before any change with `verify_all.ps1`: SSOT tables current; extraction 106 verified, 0 failed; `lake build --wfail` green (7248 jobs); consistency 0/0/0; pytest with production 360 passed, 1 skipped; validation 15 passed, 2 skipped; the regenerated reports differed from the committed ones only in timestamps and the numpy field. Lean sources re-scanned: no `sorry`, `admit`, `axiom`, `native_decide` or `implemented_by`. CI on dc31ddf green (the author pushed round 75 at 15:42 ET).

**TC-26, first slice: the locked Master Prediction Register is in the registry (dcd0623; TC-26 → partial).** specification/hypotheses.json holds OSF Table 15 of the locked pre-registration (SRC-OSF, v1.1 Amendment 1, sha256-pinned PDF): 34 rows, 42 prediction codes, cells verbatim. Tier and label are literal readings of the Severity cell; no other classification is derived. `extract_sources.py --corpus` verifies (a) every row cell for cell, in column order, on its stated page; (b) the one row split by a page break (7.G, pp. 57–58) as head and tail cells that must join to the full cells; (c) that the rows reproduce the table on each of pp. 53–58 exactly, so nothing is dropped or invented. Result against the real PDF: **141 verified, 0 failed** (98 parameters, 8 bridge records, 34 rows + the table record). The PDF's table font emits private-use code points for ( ) [ ] - – : + − ↔; the glyph map, each entry fixed by context on those pages, is stored with the table record and applied to that source only: applied to every PDF it broke three Math Spec quotes (α⁺, γ⁺, M̂), whose font uses the same code points for other glyphs. check_consistency.hypothesis_check() requires a current, verified extraction of the table and of every record (P1); hypotheses.json joins the registry hash and the TC-01 status axis (record status Registered, approval pending 61a). test_prediction_register.py: extraction coverage and hashes; codes expanded from the Pred-ID cell; literal tier and label; every "Pred X.Y" cited elsewhere in the registry is registered; α_psy = 10 is the Pred 1.E threshold; and, where the untracked v1.2 draft exists, the draft's Table 15 equals the locked record row for row (it does). Planted faults against the real page text, one at a time (row dropped, row invented, α 0.0125 → 0.025, "+15%" → "15%", severity B → A, HEP Yes → No, 7.G threshold 0.048 → 0.05): **all caught**; without the glyph map the table fails. The traceability matrix lists the registered predictions.

**B-07, machine half for Table 15 (6f97bcf).** The SSOT's own copy of Table 15 is a condensation, not a verbatim copy, so test_ssot_condensed_table_agrees_with_the_locked_record checks what can be checked mechanically: the same 34 codes, the same tier and label in every row, and no number the locked row does not state. Result: **agreement in every row**; one number, "BF₁₀ ≥ 100 for 0.B", is not in the Table 15 cell but is the locked record's Pred 0.B criterion (p. 69, registered and extraction-verified as bf10_threshold_pred_0B), and the test names that support explicitly. Rows 2.F and 2.G are in swapped order in the SSOT (F23, cosmetic; order is not tested). Planted faults in a temporary copy of the SSOT (1.C 0.30 → 0.35, 6.D tier B → A, 7.E label Exploratory → B, row 5.D dropped, 0.B BF 100 → 10): **all caught**. B-07 stays open: Tables 12 and 13 (falsifiers, tiers, minimum N) are not registered, and the second-reader sign-off is a human step.

**Task 60: K7 rerun, versioned (28de9af in apgi-implementation).** `python tools/run_k7.py --out gates --subjects 60` (MCMC defaults, seed 20261116) ran on a clean 5802bf2 in 3425 s (`"dirty": false`). It reproduces the round-75 run on 67a6c3f **bit for bit**: K7a sha256 630cff21…, K7c 938a6026…; the gate tables are identical apart from git_commit. Gate decisions (K7b PENDING_DATA, so no parameter is production-exposable and the allow list is empty): desk-exposable θ_base (r 0.8985, coverage 0.917) and the precision-weighted learning composite (r 0.998, 0.95); α and Π FALSIFIED in K7a and K7c (the registered α–Π degeneracy); β CONFIRMED in K7a, FALSIFIED in K7c. Same outcomes as the archived 27 October run, now under the current gate rules. TestCommittedGateTable now runs (6 tests) instead of skipping: tests/test_tools.py 9 passed. gates/README.md records the command, commit, determinism check and reading; the table stays labelled provisional (S1-REG-04 contracts not qualified). The K7 model (models/reduced.py) did not change since 27 October, so no earlier gate result is invalidated; hierarchical-path or γ_NE ≠ 0 results before 67a6c3f were not cited anywhere in this repository.

**F21 (fixed, apgi-implementation 5802bf2).** run_k7 read the git state only at the end, after writing k7a-results.json into the repository's gates/; `git status --porcelain` counts that untracked file, so every K7 run into the repository recorded "dirty": true (the 14:56 run on a clean 67a6c3f did). The state is now read before any output exists and passed to the manifest; the gate table's git_commit comes from the same record. New test test_run_k7_records_git_state_before_writing_outputs; planted fault (read moved after the K7a output): caught. tests/test_tools.py 9 passed; mypy clean; ruff format clean (ruff check flags only an import-order rule on unchanged lines when linted outside the repository, where ruff cannot see the first-party packages).

## Findings this round

- **F21 (fixed):** run_k7 manifests marked dirty by their own outputs (above).
- **F22 (open, author):** the SSOT §30.1 release-blocker table lists B-05, B-10, B-12 and B-15 as open, and the B-10 "Required before release" paragraph lists golden-vector families that exist; the closure evidence is in this file and git history, not in the registry, so nothing checks the table. Proposed correction **D12**: either correct the four statuses and drop the paragraph by hand, or register the blockers (closure evidence per blocker) so make_ssot_tables.py generates the table. Not edited here: D8 (B-15 status) is already an author item.
- **F23 (cosmetic):** SSOT Table 15 orders 2.F before 2.G; the locked record has 2.G first.
- **Tooling note:** `extract_sources.squash` deletes the whole private-use range, so an existing evidence quote that spans PDF punctuation encoded as private-use glyphs is matched with that punctuation removed. All 106 earlier quotes still verify; they are not strengthened by the glyph map, which is per source.
- **CI note:** GitHub annotates the artifact actions (upload-artifact@v4, download-artifact@v4) as Node 20 and runs them on Node 24; the jobs pass. Not bumped: upload-artifact@v6 / download-artifact@v7 would remove the warning, but the download step is `continue-on-error`, so a breakage would be silent, and no CI run can be observed before a push.
- Unchanged: F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F7 (memory), F8 (the 17-step loop is rejected by SSOT §8; the canonical 15-step pipeline is the one formalized, Apgi/Pipeline.lean, with the rejected orders stated as theorems), F10 (pushes need the author's key).

## Previous round (2026-11-27, round 75)

Task 62c (apgi_core.full_model aligned with the SSOT core in apgi-validation 604a3d9; SSOT-V3 resolved; TC-04 pass), task 71a (§17 recovery dispositions; TC-08 pass), task 54b (13 parameter rows, 11 label rows with a stated value rule), D10 and D11 (registry-derived SSOT parts generated; c₂ × δ_reset row; TC-21 pass), F19 (committed reports refreshed by verify_all). Details in git history (dc31ddf).

## Remaining tasks

### Next step (one at a time)

**Push apgi-implementation, then apgi-lean**, and confirm the apgi-lean CI is green (the pin 67a6c3f does not move, so the CI checks out the same production commit as round 75):

```powershell
git -C C:\Claude\Projects\apgi-implementation push origin main
git -C C:\Claude\Projects\apgi-lake push origin main
```

After that: **TC-26 / B-07, next slice** (register OSF Tables 12 and 13 the same way: falsifier, tier, minimum N per row, verified against the locked PDF; then compare the SSOT's H-register condensation against them).

### Phase A remainder
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules. Closes TC-01, one of the two partial conformance tests (TC-26 is the other).
**61b (optional).** Have production count clamped steps itself in `manifest()`; the harness report already satisfies TC-10.

### Phase B remainder
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering). Bounded above by the event-level study (CL-46); the dispositions do not depend on it.
**70 remainder.** Register r_max·T_W once B-13 fixes r_max.
**TC-25.** End-to-end assessment → scoring → storage → analysis with schema and consent checks: belongs to the application layer (apgi-validation / apgi-implementation), not this repository.
**TC-26 remainder.** Done: OSF Table 15 (round 76). Next: Tables 12 and 13 (falsifiable register; non-falsifiable, conditional and asymmetric commitments), then 16, 17 and 19, the exclusion and data-admissibility rules (e.g. the EEG trial-rejection gates) and the methods, each quote-verified against SRC-OSF; the comparison with analysis code belongs to apgi-validation (application layer). Pairs with B-07.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections** remaining: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status; **D12 (new, F22)**: the §30.1 table lists B-05, B-10, B-12 and B-15 as open, and the "Required before release (B-10)" paragraph lists golden-vector families that exist. Options: correct by hand, or register the blockers with their closure evidence so make_ssot_tables.py generates the table. Optional: F23 (Table 15 row order 2.F/2.G).
**33 / B-13.** r_max and the operating point (F2).
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, the recovery readings and the 71a dispositions.
**B-07.** Second-reader check of the hypothesis register. Machine half done for Table 15 (round 76); Tables 12 and 13 next (see TC-26 remainder).
**B-17.** Independent reviewers (scientific, mathematical, implementation, statistical).
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.

### Phase D: next Zenodo release (v1.2)
**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing: re-hash every source; re-source EQ-CUSP-1, the task-53/54/54b rows, τ_Π, α_Π, the SSOT-sourced parameter rows and the bridges.json quotes to the published documents; retire SRC-MATHSPEC-V12D and SRC-SSOT-V12D; re-run extraction; confirm 0 corpus defects; fill the tag and DOI in the release manifest (B-11).

## Rating (1–100) against the SSOT

Initial (start of round 76: dc31ddf rebuilt and retested green; its CI green) → final (this round, verified as stated above):
- Architecture 93 → 94: the pre-registration's decision rules are now registry records on the same footing as parameters and bridges (extraction, hash-checked report, consistency check, status axis), with a per-source glyph map instead of a global text hack.
- Mathematical correctness 93 → 93: no Lean source change; Spec.lean regenerated and `lake build --wfail` green.
- Specification coverage 97 → 98: TC-26 first slice (34 rows, 42 codes) and the Table 15 half of B-07. Deductions: TC-25, the rest of TC-26, TC-01 approvals, behavior-level recovery.
- Implementation 93 → 94: F21 fixed; the K7 gate table is committed and its tests run. Deduction: the full apgi-validation suite still runs only in its own CI.
- Proof completeness 89 → 89.
- Testing 97 → 98: 9 new apgi-lean tests and 1 apgi-implementation test, 13 planted faults across three suites, all caught; the six committed-gate-table tests no longer skip.
- Reproducibility 91 → 92 (initial raised from 90: round 75 CI observed green): K7 shown bit-reproducible across two runs; manifests no longer misreport a clean tree. Deduction: round 76 not pushed, so its CI is not observed.
- Documentation 92 → 93: README, REPRODUCIBILITY, traceability matrix (registered predictions), gates/README.
- Publication readiness 73 → 75: registered fidelity is now checked for the main register; blockers B-07, B-11, B-13, B-14, B-16, B-17, B-18, TC-25, the rest of TC-26 and approvals (61a) remain.
- **Overall 92 → 93.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

---

## Routine after any registry edit

`verification\verify_all.ps1` runs all of it (SSOT tables, extraction, generate_lean, lake build, consistency, release manifest, traceability, recovery and production reports, both pytest runs, make_report) and writes .verify.log. Manually:

```powershell
cd C:\Claude\Projects\apgi-lake
# or: verification\verify_all.ps1 -Impl <apgi-implementation checkout at the pinned commit>
python verification\python\make_ssot_tables.py   # D10: SSOT registry-derived parts; re-pins SRC-SSOT-V12D
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\docs\apgi-v-1-2 --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
python verification\python\make_release_manifest.py
python verification\python\make_traceability.py
python verification\python\make_recovery_report.py   # TC-08d–g study, about 2.5 min
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"; python verification\python\production_report.py; Remove-Item Env:APGI_IMPL_PATH   # TC-10/TC-14 report (task 61b)
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"   # main must contain the pinned commit
python -m pytest -q -rxs
Remove-Item Env:APGI_IMPL_PATH   # the validation module refuses to run with both packages on sys.path
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-validation"
python -m pytest -q -rxs test_production_validation.py
Remove-Item Env:APGI_VALIDATION_PATH
cd ..\..
git add -A
git commit
git push origin main
```

`generate_lean.py` hashes all twelve registry files (now including bridges.json, requirements.json and hypotheses.json), so regenerate and rebuild after changing a production pin. If `test_production.py::test_production_run_report_is_current` fails, production or the pin changed: rerun production_report.py with APGI_IMPL_PATH at the pin and review the diff. If `test_recovery_pipeline.py::test_report_is_current` fails, the study design or code changed: rerun make_recovery_report.py and review the report diff (and GATE_EXPECTED if a gate outcome flips). If `check_consistency.py` reports `extraction_unverified`, `bridge_unverified`, `prediction_unverified` or `prediction_register_unverified`, a registry value, bridge record or prediction row changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
