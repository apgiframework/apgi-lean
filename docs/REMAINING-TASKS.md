# APGI verification: remaining tasks

State as of 2026-11-27 12:00 ET (round 73). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0**; the registry hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only:
  - apgi-lean: round 72 (cfa5b48) is on origin/main; GitHub Actions "APGI verification" **green on cfa5b48** (run 46029638355, read from the public API). This round (73) is local commits on top, not pushed.
  - apgi-implementation: main at **8d8e5bd** (the F13 patch, applied and pushed by the author); CI **green on every job, including "lint & types"**. **New pin 8d8e5bd** (formatting and type annotations over d153f6a; no behaviour change, confirmed by the full apgi-lean suite).
  - apgi-validation: f6fec65 (unchanged).
- Round 73 checks. Python (cloud workspace, Python 3.13, fresh public clones of the three repositories at the pins, the same commands as CI): consistency 0 open, 0 unacknowledged, 0 stale; `generate_lean.py --check`, `make_traceability.py --check`, `production_report.py --check` current; apgi-lean pytest with production **343 passed, 1 skipped, 6 xfailed** (all six strict, SSOT-P10/P12/P13); without production 276 passed, 2 skipped; test_production_validation.py **11 passed, 2 skipped, 3 xfailed** (strict, SSOT-V3). Lean (this PC, `lake build --wfail` on the round-73 Spec.lean, 11:39–11:46 ET): **Build completed successfully (7248 jobs)**.
- Rating against the SSOT (1–100, nine dimensions): **overall 89 → 89** this round (implementation down, coverage, testing and reproducibility up). Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (derived and label rows of 54b), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **20 pass** (TC-10 added this round), **4 partial** (TC-01 approval pending; TC-04, now tested on every implementation, apgi_core.full_model diverges (SSOT-V3); TC-08, dispositions; TC-21), **2 not implemented** (TC-25, TC-26).
- Lean: **196 theorems in 10 modules** (unchanged), every one axiom-pinned with `#guard_msgs`; 189 use exactly [propext, Classical.choice, Quot.sound], 7 a strict subset; no sorry, no admit, no axiom declaration.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: 46: 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (35 pass, 4 partial, 3 open, 2 not implemented).
- Production divergences: apgi-implementation 3 open of 23 (SSOT-P10, SSOT-P12 new, SSOT-P13 new; all strict xfail); apgi-validation 1 open of 7 (SSOT-V3 new, strict xfail), 1 declared variant.

## Done this round (2026-11-27, round 73)

**Pin moved to 8d8e5bd.** The author applied the F13 patch and pushed (8d8e5bd, every CI job green). known-conflicts.json `production.commit` and the CI checkout now name 8d8e5bd. The diff to d153f6a is formatting and annotations; the full suite gives the same results at both commits.

**Task 61b / TC-10 → pass. Production clamp fraction reported.** New verification/python/production_report.py runs the pinned production core for CFG-CORE and CFG-CORE-R on 60 s of seeded stimulus-free N(0, 1) input, runs apgi_ref.core_step on the same inputs and uniform draws, and writes verification/reports/production-run-report.json: clamped-step fractions (precision, NE), the observed precision range, events and event rate, and the TC-14 operating point, production next to reference. Results: both configurations clamp on 0 % of stimulus-free steps; 38 events (0.63 /s, CFG-CORE) and 253 (4.22 /s, CFG-CORE-R), identical in production and reference; γ_sig·θ₀ = 0.7, floor 0.332, nominal baseline 33.2 /s (the F2 / B-13 operating-point question, unchanged). Tests (test_production.py): the report is current and agrees with the reference; with binding clamps (low-variance segments in each channel; gains g_ACh = g_NE = 2; |γ_NE|·g_NE = 2) the production fraction equals the reference's (0.38 for precision, 1.0 for NE) and precision stays in [Π_min, Π_max]; the flag function is checked on bound and interior values. Limitation: the fractions are derived by apgi-lean from production's per-step outputs; production does not count clamped steps itself.

**Task 59: SSOT-P10 under test; one suspicion refuted; two new divergences.** Legacy extension path (model_form legacy_v1_1), experiments first, then tests:
- SSOT-P10 (a) confirmed: with the hierarchical precision ODE on, doubling g_ACh (inverse-variance chain only) changes S while the ODE precisions and z are unchanged: two precisions in one simulation. Strict xfail.
- SSOT-P10 (b) refined: the suspected double δ on the primary threshold is **refuted**: one ignition raises it by exactly one δ_reset (new passing test, δ = 0 and 0.2). The real defect is a second δ value: the resonance-level threshold reported at the ignition step jumps by DELTA_RESET = 0.5 even when δ_reset = 0 (`or 0.5`). Strict xfail.
- **SSOT-P12 (new, P1):** the PAC threshold coupling omits the /Π_max of EQ-MS-4 (factor range [0, 2] instead of [0.5, 1.5]) and writes the modulated threshold back into θ, so it compounds (TC-11): under stimulus-free input with κ_down = 0.1, θ sits at the 20 AU numerical guard on 1117 of 4000 steps; with κ_down = 0, on none. Two strict xfails.
- **SSOT-P13 (new, P1, found while testing TC-10):** any run with γ_NE ≠ 0 at production defaults drops the NE threshold pathway (ne_on_threshold = False), although SSOT §11 states that both NE pathways share one clamped g_NE and EQ-THEFF-1 applies (1 + γ_NE·g_NE). With ne_on_threshold = True production matches the reference step for step. Strict xfail (γ_NE = 0.2 and −0.3).

**Task 62b (TC-04 part): apgi_core.full_model trajectory-tested; SSOT-V3 (new, P1).** Driven by the reference's own Π and z, full_model reproduces S exactly until the first ignition (passing test), then diverges: (a) it decides ignition from S(t+1), θ(t+1), not the existing S(t), θ_eff(t) (SSOT §8 step 8); (b) it has no retention reset (EQ-RESET-1); (c) its threshold step is forward Euler with its own cost, value and facilitation terms, and it cannot express η_θ = 0. Three strict xfails. TC-04 stays partial until full_model is aligned or declared a variant (task 62c, author).

**Audit evidence (planted faults, .scratch/r73 mutate73.py; six faults, one at a time, all caught after one fix):**
1. Production drops the Πⁱ_eff clamp: caught by test_production_clamp_fraction_matches_reference[precision+gains]. In the first run it survived (the interoceptive channel never reached Π_max); the test inputs now give each channel a low-variance segment and the test checks the precision range.
2. The harness never flags a clamp: 4 tests fail.
3. Production fixes SSOT-P13: the strict xfails turn into failures (2), as intended.
4. Production normalizes the PAC factor (part of SSOT-P12): the strict xfail fails.
5. Production changes the r_max default: test_production_run_report_is_current fails (stale report).
6. full_model gains a retention reset (part of SSOT-V3): the strict xfail fails.
Each strict xfail was also run with `--runxfail` to confirm it fails on its stated assertion, not on an import or setup error.

**Not done this round (with reason).** 54b needs a full extraction run, which reads the v1.1 corpus in C:\Claude\Projects\Neuro-Brain, a folder not connected to this session; the rows also carry no values for most symbols (derived, computed, uncalibrated), so they are registry labels rather than verifiable numbers. Production fixes for SSOT-P10/P12/P13 and full_model: the production repositories were not writable from this session (folder access declined); the tests are written so each fix turns its xfail into a failure until the divergence is marked resolved. TC-25 (assessment → scoring → storage → analysis) concerns a data platform outside these three repositories. TC-26 needs the locked OSF record (B-14, Amendment 2 not filed).

## Previous round (2026-11-27, round 72)

**Pushes confirmed and CI observed.** The author pushed apgi-lean 7aec2c0 and apgi-implementation d153f6a. CI read from the public GitHub API (F10 no longer blocks observation): apgi-lean green on 7aec2c0; apgi-implementation green on every job of d153f6a except "lint & types".

**SSOT-P11 closed; pin moved to d153f6a.** specification/known-conflicts.json: SSOT-P11 `resolved` (fix text moved to `resolution`), production.commit d153f6a152cb…; .github/workflows/lean_action_ci.yml checks out the same commit. REQ-TC-13 `partial` → `pass`; its remaining limitation (overflow is a float64 property, established by tests, not proof) stays on record. Regenerated: Apgi/Spec.lean (registry hash d3afe09c…), verification/reports/{conflicts,release-manifest}.json, traceability.csv, docs/traceability-matrix.md, docs/assumption-inventory.md. Evidence: test_production.py 59 passed, 0 xfailed at d153f6a; full apgi-lean suite 335 passed.

**F13 (apgi-implementation CI): "lint & types" red since 72ad050; fix prepared.** Ruff stopped the job before the format check and mypy ran, so three layers were hidden: ruff I001 (pipeline.py import order) and N812 (test aliases PCFG, PP), 6 files unformatted, and 6 mypy errors (untyped helpers in core/ssot_core.py from e0e82cf; `run_channel(**channel_kwargs: float)` broken by 72ad050's `reference_window: int | None`). Commit "CI: restore the lint & types gate" fixes all three; formatter edits are AST-identical except the moved import; no behaviour change. Verified: ruff 0.16.0 and mypy 1.19.0 clean (105 files); production suite 2840 passed, 12 skipped, 0 failed (per file, Python 3.10). Exported as a patch to .scratch (gitignored) because apgi-implementation is not a connected folder in this session.


## Findings this round

- **F14 (new, production, legacy path):** SSOT-P12, PAC threshold coupling unnormalized and written back (θ at the 20 AU guard 28 % of the time with hierarchy on). Any result computed with use_hierarchical = True and κ_down > 0 needs a versioned rerun after the fix.
- **F15 (new, production):** SSOT-P13, γ_NE ≠ 0 silently drops the NE threshold pathway. Any production run with γ_NE ≠ 0 and ne_on_threshold = False is not the SSOT model.
- **F16 (new, validation):** SSOT-V3, apgi_core.full_model is not the SSOT core after the first ignition. It backs Validation/Falsification protocols in apgi-validation, so its outputs should not be cited as minimal-core predictions until aligned or labelled.
- **F12** (identifiability, author decision 71a), F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F7 (memory), F8 (the 17-step loop is rejected by SSOT §8; the canonical 15-step pipeline is the one formalized, Apgi/Pipeline.lean) are unchanged. F5 (SSOT-P10) is now under test. F10 (pushes need the author's key) and F13 (closed: 8d8e5bd green) as before.

## Remaining tasks

### Next step (one at a time)

**Push apgi-lean** (github-apgi key loaded), then confirm CI "APGI verification" is green with the pin 8d8e5bd (it runs the new production tests, the report check and `lake build --wfail`):

```powershell
git -C C:\Claude\Projects\apgi-lake push origin main
```

After that: **task 71a** (author decision): the §17 disposition for τ_θ and η_θ·c₁; then **59b** below.

### Phase A remainder
**59b.** Fix in apgi-implementation, legacy extension path: SSOT-P10 (one precision definition when the precision ODE is on; resonance-level reset uses the configured δ_reset), SSOT-P12 (EQ-MS-4 factor with /Π_max and the [0.5, 1.5] bound; modulation as a read-out, never written back into θ), SSOT-P13 (γ_NE ≠ 0 runs both NE pathways, or the flag is removed). Then mark each resolved and move the pin; the strict xfails will fail until then.
**60.** Rerun K7 and the gate results on 72ad050 as a versioned rerun (Phase A changed outputs).
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules.
**61b (optional).** Have production count clamped steps itself in `manifest()`; the harness report (production_report.py) already satisfies TC-10.

### Phase B remainder
**54b.** The remaining derived and label parameter rows: α_EMA and β_Σ (EQ-EMA-2), m_Ψ, K_ℓ / K_ℓm, τ_min / τ_max, R_L, α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh.
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering), η_θ·c₂ and η_θ·v₂.
**62c (author, new).** SSOT-V3: align apgi_core.full_model with the SSOT core (decision from the existing S, retention reset, EQ-ALLO-1 threshold step) or label it a declared variant with MODEL_FORM, as task 52 did for model.py. TC-04 passes after either.
**70 remainder.** Register the guess rate g (with 54b) and r_max·T_W (once B-13 fixes r_max) so test_recovery.py reads them from the registry.
**71a (author, new).** §17 failed-recovery disposition for τ_θ and η_θ·c₁ (F12), and a statement that η_θ is reported only through its products with c and v (CL-45). TC-08 passes once the dispositions are recorded and REQ-TC-08 cites them.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status (now closed on run 45931170311); D10 regenerate the header and §24–§25 from the registry: spec 0.6.0, 196 theorems in 10 modules, CL-1…CL-46, 26 conformance tests (20 pass), 57 golden vectors in 14 families, 59 equations, requirements.json and bridges.json added.
**33 / B-13.** r_max and the operating point (F2).
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, plus the recovery readings.
**B-07.** Second-reader check of the hypothesis register.
**B-17.** Independent reviewers (scientific, mathematical, implementation, statistical).
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.

### Phase D: next Zenodo release (v1.2)
**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing: re-hash every source; re-source EQ-CUSP-1, the task-53 and task-54 equations, τ_Π, α_Π, the 37 SSOT-sourced parameter rows and the bridges.json quotes to the published documents; retire SRC-MATHSPEC-V12D and SRC-SSOT-V12D; re-run extraction; confirm 0 corpus defects; fill the tag and DOI in the release manifest (B-11).

## Rating (1–100) against the SSOT

Initial (start of round 73, after observing cfa5b48 and 8d8e5bd green) → final (this round, verified as stated above):
- Architecture 92 → 92.
- Mathematical correctness 93 → 93: no Lean source change; the build of the round-73 Spec.lean is green.
- Specification coverage 93 → 94: TC-10 passes for reference and production; TC-04 now covers every implementation; the hierarchical extension (EQ-MS-4, EQ-PREC-ODE-1) and both NE pathways are under test. Deductions: dispositions (71a), behavior-level recovery, TC-25, TC-26, 54b rows.
- Implementation 88 → 86: three new production divergences were found (SSOT-P12, SSOT-P13, SSOT-V3), one of them (P13) on any run with γ_NE ≠ 0; the default core still matches the reference step for step. This is a lower score for better knowledge, not for a regression.
- Proof completeness 89 → 89.
- Testing 94 → 95: 18 new test cases, 9 of them strict xfails each pinned to its stated assertion; six planted faults caught, one only after the test was strengthened.
- Reproducibility 90 → 91: CI observed green on apgi-lean cfa5b48 and on every apgi-implementation job at the new pin; the production run report is regenerated and checked in CI; all checks reproduced from fresh public clones. Deduction: round 73 not yet pushed, so its CI run is not observed.
- Documentation 89 → 90: the report, inventory and traceability carry the new divergences with evidence.
- Publication readiness 69 → 69: blockers B-07, B-13, B-14, B-16, B-17, B-18, tag and DOI, decisions 71a and 62c, and three open production divergences.
- **Overall 89 → 89.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

---

## Routine after any registry edit

`verification\verify_all.ps1` runs all of it (extraction, generate_lean, lake build, consistency, release manifest, traceability, both pytest runs) and writes .verify.log. Manually:

```powershell
cd C:\Claude\Projects\apgi-lake
# or: verification\verify_all.ps1 -Impl <apgi-implementation checkout at the pinned commit>
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

`generate_lean.py` hashes all eleven registry files (now including bridges.json and requirements.json), so regenerate and rebuild after changing a production pin. If `test_production.py::test_production_run_report_is_current` fails, production or the pin changed: rerun production_report.py with APGI_IMPL_PATH at the pin and review the diff. If `test_recovery_pipeline.py::test_report_is_current` fails, the study design or code changed: rerun make_recovery_report.py and review the report diff (and GATE_EXPECTED if a gate outcome flips). If `check_consistency.py` reports `extraction_unverified` or `bridge_unverified`, a registry value or bridge record changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
