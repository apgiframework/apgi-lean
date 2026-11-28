# APGI verification: remaining tasks

State as of 2026-11-27 19:10 ET (round 77). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 b3ce0052…, pinned as SRC-SSOT-V12D; unchanged this round). Registry **spec 0.6.0**, twelve files, registry hash now 516242ee… (Apgi/Spec.lean).

- Repositories, all `main` only:
  - apgi-lean: round 76 (caa6a83) is on origin/main and its CI is **green** (run 46081343683). Round 77 is local, **not pushed** (this session has no push key: `git fetch` → Permission denied (publickey)): 36f137b (TC-26 second slice, F24) and the docs commit.
  - apgi-implementation: origin/main at 28de9af (pushed by the author after round 76); pin **67a6c3f** unchanged.
  - apgi-validation: pin 604a3d9, unchanged.
  - **Push:** apgi-lean only (`git -C C:\Claude\Projects\apgi-lake push origin main`); the CI checks out the unchanged pins.
- Round 77 checks (this PC, Windows, Python 3.12.9, numpy 2.1.3; `verify_all.ps1 -Impl C:\Claude\Projects\apgi-impl-pin`, a worktree at 67a6c3f): SSOT tables current; extraction **158 verified, 0 failed** (98 parameters, 8 bridge records, 52 prediction-register records: 34 + 12 + 3 rows and 3 table records); `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully (7248 jobs)**, exit 0; consistency **3 open (acknowledged), 0 unacknowledged, 0 stale** (the three open items are the new tier conflicts in the locked record, F24); manifest, traceability and production reports regenerated; apgi-lean pytest with production **386 passed, 1 skipped** (start: 369 passed, 1 skipped); test_production_validation.py at 604a3d9 **15 passed, 2 skipped**; make_report.py: 196/196 theorems axiom-audited, Spec.lean hash equals the registry hash. The recovery report regenerated under numpy 2.1.3 differs only in its numpy field and was not recommitted. Clean clone of 36f137b without drafts or corpus (the CI path), production at the pin: Spec.lean in sync, consistency 3/0/0, traceability current, pytest **379 passed, 8 skipped** (the seven draft-dependent checks and the validation module).
- Rating against the SSOT (1–100, nine dimensions): **overall 93 → 93**. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07 (machine half done for Tables 12, 13 and 15; the second reader remains, and the record's own tier conflicts F24 need an author decision), B-09, B-11, B-13, B-14, B-16, B-17, B-18. The SSOT's own §30.1 table still lists B-05, B-10, B-12 and B-15 as open (F22).
- Conformance tests TC-01…TC-26: **23 pass**, **2 partial** (TC-01, approval dates; TC-26, Tables 12, 13 and 15 registered), **1 not implemented** (TC-25).
- Lean: **196 theorems in 10 modules** (unchanged), every one axiom-pinned with `#guard_msgs`; no sorry, no admit, no axiom declaration. No Lean source changed; Spec.lean regenerated (new registry hash) and rebuilt.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: 46: 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (38 pass, 2 partial, 3 open, 1 not implemented).
- Parameters: 99. Registered predictions: **34 rows, 42 codes** (OSF Table 15); registered hypotheses: **12 falsifiable** (Table 12) and **3 non-falsifiable, conditional or asymmetric** (Table 13), H1–H15 exactly once; all PDF-verified.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7**, 1 declared variant (SSOT-V1).
- Known conflicts: **2 open entries, 3 detections** (KC-OSF-TIER-1F on 1.F; KC-OSF-TIER-H5 on 3.C and 3.D), all in the locked pre-registration, owner Uxod.

## Done this round (2026-11-27, round 77)

**Initial audit.** HEAD caa6a83 (round 76) is on origin/main and its CI run 46081343683 is green (checked through the GitHub API; the author pushed both repositories after round 76, so the backlog's first step was already done). Lean sources re-scanned on the final tree: no `sorry`, `admit`, `native_decide` or `implemented_by` outside doc comments, and no `axiom` declaration.

**TC-26, second slice: OSF Tables 12 and 13 are in the registry (TC-26 stays partial).** specification/hypotheses.json gains `registers`: the falsifiable hypothesis register (OSF-T12, pp. 43–49, 12 rows, 8 columns: #, Pred-ID, hypothesis, evidence tier, benchmark, falsifier, minimum n, severity) and the non-falsifiable, conditional or asymmetric commitments (OSF-T13, p. 50, 3 rows: H7, H10, H15). Cells are verbatim; `codes` is read from the Pred-ID cell only, `severity_tier` is the first letter of the Severity cell, nothing else is derived. Five rows are split by page breaks (H2, H3, H5, H8, H14) and are registered as head and tail cells that must join to the full cells. The text layer uses the same private-use glyphs as Table 15 plus one more, E0A1 = ± ("∼3.2 Hz crossover (±0.5 octave)", p. 46), fixed by context and stored with the table. extract_sources.py: one verifier, `verify_table`, now serves every registered table (Table 15 through the same function, its record hashes unchanged), and it gained a check that rows are registered in table order (planted fault 8 below found that gap). check_consistency.hypothesis_check() covers every register; the record-status axis (TC-01) covers the new rows. Result against the real PDF: **158 verified, 0 failed**.

**B-07, machine half for Tables 12 and 13; F24.** New check `register_tier_check`: every Table 12 code must be registered in Table 15 (all are) and carry the same severity tier there. The locked record **disagrees with itself** in two places, now detected and acknowledged as open author items, not resolved here: **KC-OSF-TIER-1F**, where H4 / Pred 1.F is Severity A in Table 12 (p. 45) but B in Table 15 (p. 54), and the multiplicity rule calls Pred 1.F "a secondary test (α = 0.05)" (p. 68, quote-verified); and **KC-OSF-TIER-H5**, where H5 is "Pred 3.A–3.D", Severity A, in Table 12, but Table 15 gives 3.C and 3.D Severity B, and the record's H↔Pred crosswalk reads "H5 ↔ Pred 3.A, 3.B, 3.D" (p. 148, quote-verified), a third reading. The SSOT and the v1.2 draft copy both tables unchanged, so they inherit both conflicts.

**Tests (test_hypothesis_register.py, 17 cases).** Extraction coverage and hashes per table; ids and record-status fields; codes against a hand-read oracle; tier as a literal reading; Tables 12 and 13 partition H1–H15 and every Table 12 row states a falsifier; no Table 13 commitment names a Table 15 code; Table 12 codes ⊆ Table 15; the tier disagreements are exactly {1.F, 3.C, 3.D} and all acknowledged; the registry's "OSF Table 13 H7" and "OSF H10" citations name Table 13 entries; the SSOT-sourced α_DFA band [0.85, 0.95] and falsifier < 0.70 are the locked H8 row; α_psy = 10 is the H3 benchmark; the v1.2 draft's Tables 12 and 13 equal the locked rows cell for cell (they do); the SSOT's condensed Tables 12 and 13 name the same hypotheses with the same codes and tiers and state no number the locked row does not (two numbers the SSOT writes as digits, H2's "≥ 2" and H8's "2 datasets", are "Two or more retention criteria" and "Two resting-state datasets" in the locked cells; SSOT section references are ignored). REQ-TC-26 lists the new tests; the traceability matrix lists the registered hypotheses.

**Planted faults** (registry mutated in memory, checked against the real page text of the pinned PDF): row H9 dropped; a Table 13 row invented; H1 falsifier 0.10 → 0.15; H6 severity A → B; split-row tail α 0.048 → 0.05 (H14); H7 κ band 10⁴ → 10⁵; glyph map without ±; rows H11 and H12 swapped across a page break (**missed at first**: page reproduction was checked per page only; fixed by the table-order check, then caught); Table 15 1.F tier changed so the conflict disappears (caught: stale known conflict); Table 12 H11 tier changed (caught: unacknowledged conflict). **10 of 10 caught** after the fix.

## Findings this round

- **F24 (open, author):** two tier conflicts inside the locked pre-registration (KC-OSF-TIER-1F, KC-OSF-TIER-H5; above). Options: an erratum fixing the Table 12 Severity cells, or Amendment 2 (B-14) restating the tiers; for H5 also decide whether 3.C belongs to H5 (Table 12) or not (p. 148). The two 1.F rows also word the estimand differently (Table 12: association beyond Πᵉ with the ±√0.02 interval; Table 15: moderator slope β_std ≥ 0.36); that is for the B-07 second reader, not a mechanical check.
- **F25 (tooling, fixed):** page reproduction did not enforce row order across pages; `verify_table` now requires rows in table order.
- **Limitation (unchanged in kind):** squash() drops whitespace, brackets and dashes, so "cell for cell" means equal up to those characters; a sign is never verified by quote matching alone.
- Unchanged: F22 / D12 (SSOT §30.1 blocker statuses), F23 (Table 15 row order 2.F/2.G in the SSOT), F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F7 (memory), F8 (the 17-step loop is rejected by SSOT §8; the canonical 15-step pipeline is the one formalized, Apgi/Pipeline.lean), F10 (pushes need the author's key). CI note on Node 20 artifact actions unchanged.

## Previous round (2026-11-27, round 76)

TC-26 first slice (OSF Table 15 registered and PDF-verified, 34 rows, 42 codes; dcd0623), B-07 machine half for Table 15 (6f97bcf), task 60 (K7 gate table committed, rerun bit-identical; apgi-implementation 28de9af), F21 (run_k7 git state, apgi-implementation 5802bf2). Details in git history (caa6a83).

## Remaining tasks

### Next step (one at a time)

**Push apgi-lean** and confirm its CI is green (pins unchanged; CI exercises the committed extraction report and skips the four draft-dependent checks):

```powershell
git -C C:\Claude\Projects\apgi-lake push origin main
```

After that: **F24 (author decision)**, the two tier conflicts in the locked record (KC-OSF-TIER-1F, KC-OSF-TIER-H5): erratum or Amendment 2. When decided, record it in the registry and set the two known conflicts to `resolved` with the fix. The next machine step, **TC-26 next slice**, registers the H↔Pred crosswalk (p. 148) and checks it against Tables 12 and 13 (it already shows the H5 discrepancy), then Tables 16, 17 and 19.

### Phase A remainder
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules. Closes TC-01, one of the two partial conformance tests (TC-26 is the other).
**61b (optional).** Have production count clamped steps itself in `manifest()`; the harness report already satisfies TC-10.

### Phase B remainder
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering). Bounded above by the event-level study (CL-46); the dispositions do not depend on it.
**70 remainder.** Register r_max·T_W once B-13 fixes r_max.
**TC-25.** End-to-end assessment → scoring → storage → analysis with schema and consent checks: belongs to the application layer (apgi-validation / apgi-implementation), not this repository.
**TC-26 remainder.** Done: OSF Table 15 (round 76), Tables 12 and 13 (round 77). Next: the H↔Pred crosswalk (p. 148), then Tables 16, 17 and 19, the exclusion and data-admissibility rules (e.g. the EEG trial-rejection gates) and the methods, each quote-verified against SRC-OSF; the comparison with analysis code belongs to apgi-validation (application layer). Pairs with B-07.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections** remaining: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status; **D12 (new, F22)**: the §30.1 table lists B-05, B-10, B-12 and B-15 as open, and the "Required before release (B-10)" paragraph lists golden-vector families that exist. Options: correct by hand, or register the blockers with their closure evidence so make_ssot_tables.py generates the table. Optional: F23 (Table 15 row order 2.F/2.G).
**33 / B-13.** r_max and the operating point (F2).
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, the recovery readings and the 71a dispositions.
**B-07.** Second-reader check of the hypothesis register. Machine half done for Tables 15 (round 76), 12 and 13 (round 77); the record's own tier conflicts (F24) are open.
**F24 (new).** Decide the severity tier of Pred 1.F (Table 12 A vs Table 15 B and p. 68 "secondary") and of H5's codes 3.C and 3.D (Table 12 A vs Table 15 B; p. 148 omits 3.C from H5). Erratum or Amendment 2 (pairs with B-14).
**B-17.** Independent reviewers (scientific, mathematical, implementation, statistical).
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.

### Phase D: next Zenodo release (v1.2)
**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing: re-hash every source; re-source EQ-CUSP-1, the task-53/54/54b rows, τ_Π, α_Π, the SSOT-sourced parameter rows and the bridges.json quotes to the published documents; retire SRC-MATHSPEC-V12D and SRC-SSOT-V12D; re-run extraction; confirm 0 corpus defects; fill the tag and DOI in the release manifest (B-11).

## Rating (1–100) against the SSOT

Initial (start of round 77: caa6a83, its CI observed green) → final (this round, verified as stated above):
- Architecture 94 → 95: one verifier (`verify_table`) now serves every registered table, with per-table columns and glyph maps; Table 15's records and hashes pass through it unchanged.
- Mathematical correctness 93 → 93: no Lean source change; Spec.lean regenerated and `lake build --wfail` green.
- Specification coverage 98 → 98: Tables 12 and 13 registered and the B-07 machine half extended to them. Deductions unchanged in kind: TC-25, the rest of TC-26 (crosswalk, Tables 16, 17, 19, admissibility rules, methods), TC-01 approvals, behavior-level recovery.
- Implementation 94 → 94: no production change.
- Proof completeness 89 → 89.
- Testing 98 → 98: 17 new cases; 10 planted faults, one gap found and fixed (cross-page row order).
- Reproducibility 92 → 93 (initial raised from 92: round 76 CI observed green); round 77 is not pushed, so its CI is not observed.
- Documentation 93 → 93: README, REPRODUCIBILITY, verification report, traceability matrix (registered hypotheses).
- Publication readiness 75 → 75: more of the locked record is machine-checked, and that check found two contradictions inside it (F24), which are new author items. Blockers B-07, B-11, B-13, B-14, B-16, B-17, B-18, TC-25, the rest of TC-26 and approvals (61a) remain.
- **Overall 93 → 93.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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

`generate_lean.py` hashes all twelve registry files (now including bridges.json, requirements.json and hypotheses.json), so regenerate and rebuild after changing a production pin. If `test_production.py::test_production_run_report_is_current` fails, production or the pin changed: rerun production_report.py with APGI_IMPL_PATH at the pin and review the diff. If `test_recovery_pipeline.py::test_report_is_current` fails, the study design or code changed: rerun make_recovery_report.py and review the report diff (and GATE_EXPECTED if a gate outcome flips). If `check_consistency.py` reports `extraction_unverified`, `bridge_unverified`, `prediction_unverified` or `prediction_register_unverified`, a registry value, bridge record or prediction row changed without re-running extraction. If it reports `register_tier_conflict` or `register_code_unregistered`, Table 12 and Table 15 of the locked record disagree: that is an author item to acknowledge in known-conflicts.json, never something to fix by editing a verbatim cell. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New register tables go in hypotheses.json `registers` (table description with `columns`, rows with verbatim cells and page evidence; a page-split row as head and tail `cells`); extraction then verifies them with `verify_table`. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
