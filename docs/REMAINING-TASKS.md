# APGI verification: remaining tasks

State as of 2026-11-27 15:40 ET (round 75). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, now sha256 582a09b9…, pinned as SRC-SSOT-V12D; the previous text, 18951b65…, is kept as .scratch/r75/SSOT.pre-D10-D11.md). Registry **spec 0.6.0**, registry hash 4359d611… (Apgi/Spec.lean).

- Repositories, all `main` only:
  - apgi-lean: 680877b is on origin/main. Its CI run 46056666564 **failed** in the two Python jobs at the checkout of apgi-implementation 67a6c3f, which was not yet on GitHub when the run started; Lean and apgi-validation jobs passed. The author pushed 67a6c3f during this round (GitHub main = 67a6c3f), so the next run can check it out. Round 75 is **four local commits, not pushed**: 2a6c96b (task 62c), 3f28c72 (tasks 71a, 54b), fe3dcba (D10, D11), a1a9f4b (statuses and regenerated files), plus the docs commit.
  - apgi-implementation: pin 67a6c3f, **pushed** (GitHub main).
  - apgi-validation: **new pin 604a3d9** (local commit on f6fec65, **not pushed**): apgi_core.full_model aligned with the SSOT core (task 62c).
  - **Push order:** apgi-validation first (the apgi-lean CI checks out 604a3d9), then apgi-lean.
- Round 75 checks (this PC, Windows, Python 3.12.9, numpy 2.1.3; `verify_all.ps1` with -Impl at 67a6c3f): SSOT tables current; extraction **106 verified, 0 failed** (98 parameters, 8 bridge records); `generate_lean.py` wrote Spec.lean; **`lake build --wfail`: Build completed successfully (7248 jobs)**, exit 0; consistency 0 open, 0 unacknowledged, 0 stale; manifest, traceability, recovery and production reports regenerated; apgi-lean pytest with production **360 passed, 1 skipped**; test_production_validation.py at 604a3d9 **15 passed, 2 skipped** (SSOT-V1 declared variant); make_report.py: 196/196 theorems axiom-audited, Spec.lean hash matches the registry. The recovery report regenerated under numpy 2.1.3 differs from the committed one (numpy 2.2.6, the CI pin) only in its numpy field.
- Rating against the SSOT (1–100, nine dimensions): **overall 90 → 92**. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (54b rows now registered; derived-row review with 61a), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **23 pass** (was 20), **1 partial** (TC-01, approval dates, task 61a), **2 not implemented** (TC-25, TC-26).
- Lean: **196 theorems in 10 modules** (unchanged), every one axiom-pinned with `#guard_msgs`; no sorry, no admit, no axiom declaration. No Lean source changed this round; Spec.lean regenerated (new registry hash) and rebuilt.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: 46: 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (38 pass, 1 partial, 3 open, 2 not implemented).
- Parameters: 99 (was 86): 13 rows added under 54b, 11 of them label rows with a stated value rule.
- Production divergences: apgi-implementation **0 open of 22**; apgi-validation **0 open of 7** (SSOT-V3 resolved this round), 1 declared variant (SSOT-V1).

## Done this round (2026-11-27, round 75)

**Initial audit.** HEAD 680877b rebuilt and retested before any change: `lake build --wfail` green (7248 jobs), consistency OK, pytest with production 357 passed, 1 skipped. Lean sources re-scanned: no `sorry`, `admit`, `axiom`, `native_decide` or `implemented_by`; the four `example … : True` in Pilot.lean are unit-type compilation checks, not counted theorems. Found: the apgi-lean CI on 680877b fails because the pin 67a6c3f was not pushed (reported to the author, who pushed it); the committed proof-status.json and verification-report.md were stale (spec 0.3.1, 91 tests) because nothing ran make_report.py locally (F19, fixed).

**Task 62c (author: align). SSOT-V3 resolved in apgi-validation 604a3d9 (TC-04 → pass).** APGIFullDynamicModel.step now follows SSOT §8: the propensity from the existing S(t), θ(t); C(t) = c₁S(t) + c₂B(t−1); V(t) = v₁|zᵉ| + v₂|zⁱ_eff|; EQ-ALLO-1 with δ_reset·B(t), the exact decay and the θ_floor clamp (η_θ ≥ 0, so η_θ = 0 is expressible); the retention reset before the exact leak; φ·I(t−1) removed. New parameters c₁, c₂, v₁, v₂, δ_reset, ρ_retain, θ_floor (SSOT: fitted; neutral placeholder defaults equal to apgi_ref CORE_DEFAULTS). Evidence: the three SSOT-V3 strict xfails XPASSed against the fix before the registry changed; new test_full_model_matches_reference_trajectory_allostatic (every allostatic term on, θ_floor binding, 600 steps) passes. Audit: eight planted faults, one at a time, in a scratch copy (decision from S(t+1); no reset; δ on B(t−1); forward-Euler decay; no floor; cost on B(t); value channels swapped; cost on S(t+1)): **all caught**, five of them only by the new test. apgi-validation's own tests that import apgi_core (19 files): 432 passed, 21 skipped, 4 failed, the same 4 failures at f6fec65 (Windows environment: `resource` module, unmeasured performance gates); ruff, black, isort clean on full_model.py. The full apgi-validation suite cannot run on this PC (main.py's secret-policy check exits without PICKLE_SECRET_KEY / APGI_BACKUP_HMAC_KEY; pytest-timeout and ruff are not installed); its CI runs it.

**Task 71a (author: requires auxiliary measurement). TC-08 → pass.** parameters.json `recovery_dispositions` records one disposition for each quantity that fails §17: τ_θ (RD-TAU-THETA), η_θ·c₁ (RD-K-C1), η_θ·c₂ (RD-K-C2), η_θ·v₂ (RD-K-V2) and the c₂ / δ_reset pair (RD-C2-RESET), with the reporting rule that η_θ is reported only through its products (CL-45); only k_V = η_θ·v₁ passes and may be interpreted. test_failed_recovery_dispositions checks that every failing (block, quantity) of the committed report has exactly one disposition of an allowed kind and that no passing quantity has one. Limitations kept on REQ-TC-08: behavior-level fits are not done (CL-46 bounds them); the 20 % gate and the dispositions are proposed readings pending OSF Amendment 2 (B-14).

**Task 54b. 13 parameter rows, all extraction-verified.** α_EMA and β_Σ (range (0, 1); Notation Appendix p7, Math Spec p2). Label rows, where the SSOT states a rule instead of a value: τ_min, τ_max (participant-estimated), m_Ψ (computed), K_ℓ, K_ℓm (no default or range; Notation Appendix p19), R_L (computed per event, EQ-BR-3; Notation Appendix p22), κ_pop, κ_beh (uncalibrated; a band needs an amendment), α_psy,log (no decision weight), g (catch-trial false-alarm rate; also Math Spec p41), protocol seeds (P1 = 10101 … P7 = 70707, Proposed). No value is invented: check_consistency.py accepts a stated `value_rule` in place of a value or range, and test_label_rows_state_a_value_rule requires one with evidence. Task 70 remainder (g): test_recovery.py now asserts its synthetic guess rate is a known catch-trial rate, as the registered rule requires.

**D10, D11 (author-approved SSOT edits). TC-21 → pass.** New verification/python/make_ssot_tables.py regenerates the SSOT's registry-derived parts between BEGIN/END GENERATED markers: the header registry row, the golden-vector paragraph, the Lean status table, the theorem register (59 equations), the claim register (46 claims) and the open targets, and re-pins SRC-SSOT-V12D. The SSOT no longer quotes a registry hash: it is a pinned registry source, so the hash would be circular. Replaced stale figures: spec 0.3.1 → 0.6.0; 41 → 196 theorems; 25 vectors in six families → 57 in 14; 16 → 46 claims. D11 adds the row c₂ × δ_reset ("the same per-event threshold increment one step apart; declared trade-off; TC-08g") to the §17 degeneracy table. test_ssot_generated_parts_are_current checks the parts and the pin (skipped in CI, where the untracked draft is absent). verify_all.ps1 runs the generator first and now also writes junit and runs make_report.py.

**Task 60 (started, not finished).** `python tools/run_k7.py --out gates --subjects 60` (MCMC, defaults) was started on apgi-implementation 67a6c3f at 14:56 ET on this PC. K7a finished (gates/k7a-results.json, 14:57); K7c (MCMC recovery) was still running at 15:40. Its outputs (k7c-results.json, gate-table.json/.yaml, k7-manifest.json) land in apgi-implementation/gates/, uncommitted. models/reduced.py, which K7 uses, did not change in Phase A or round 74, so the rerun is a versioning step; the result is not yet observed.

## Previous round (2026-11-27, round 74)

**CI confirmed for round 73.** The author pushed 3dd4d68; "APGI verification" green (run 46045899533). The apgi-implementation run the author checked (46029607584) is on 8d8e5bd, the pin. Recorded in f142bcd (pushed).

**Task 59b: SSOT-P10, SSOT-P12, SSOT-P13 fixed in production (apgi-implementation 67a6c3f) and resolved in the registry (a88abba).**
- SSOT-P13: config.py `ne_on_threshold` defaults to True, so γ_NE ≠ 0 runs both NE pathways with one clamped g_NE (SSOT §11, EQ-THEFF-1). core/config_schema.py had two validators that rejected both pathways together and any γ_NE ≥ 0.1 (while accepting −0.3); both contradicted the SSOT and were removed; its `gamma_ne` default was 0.1 with `ge=0` (contradicting R6 / SSOT-P6) and is now 0, unsigned. The clamp |γ_NE|·g_NE ≤ 0.5 stays in the pipeline (rescale, as prescribed).
- SSOT-P12: EQ-MS-4 (Π/Π_max, factor band [0.5, 1.5]) in NestedResonanceSystem and hierarchical_threshold_modulation. In the legacy path every threshold modulation (NE, 5-HT, circadian, hierarchical) is now a read-out of the carried threshold (TC-11); before, all four were written back. With the P13 default an NE write-back would have compounded for γ_NE ≠ 0, so this was fixed with P12.
- SSOT-P10: (a) with the precision ODE on, S is driven by the multiscale S_inst from the ODE precisions, with the noise from the same weighted precision; (b) the resonance-level reset uses the configured δ_reset; DELTA_RESET removed.
- Default ssot_core path unchanged: the prod and dev golden masters are bit-identical and the production run report (TC-10/TC-14) changed only in its commit field. The staging golden master (full hierarchy) moved from final θ 20.0 AU (at the guard) to 1.833 AU.
- **F17 (new, fixed):** stats/maturity_assessment.assess_hierarchical_architecture could return a cascade score above 100 (516 for one seed); the suppression fraction is clipped to [0, 1]. Two apgi-implementation tests compared unseeded runs and failed about 3 in 15 runs at 8d8e5bd (CI runs four Python versions); both are seeded, the maturity test at a seed that fails without the fix.
- Evidence: the six SSOT-P10/P12/P13 strict xfails XPASSed against 67a6c3f before the registry was changed; they now run as ordinary tests. Pin moved in known-conflicts.json and the CI checkout.

Round 74 audit (planted faults in 67a6c3f, seven caught) and task 62b remainder are in git history (680877b).

## Findings this round

- **F19 (fixed):** the committed verification/reports/proof-status.json and verification-report.md described spec 0.3.1 and 91 tests: CI regenerates them as artifacts, but nothing refreshed the committed copies. verify_all.ps1 now runs make_report.py; both are current (196/196 audited, hash match).
- **F20 (closed):** the apgi-lean CI on 680877b failed at the apgi-implementation checkout (pin not pushed). The author pushed 67a6c3f; the next run is expected to pass the checkout.
- **F16 (closed):** SSOT-V3, apgi_core.full_model aligned (604a3d9).
- **F18:** the c₂ / δ_reset confound is now in the SSOT §17 table (D11) and has a disposition (RD-C2-RESET).
- Unchanged: F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F7 (memory), F8 (the 17-step loop is rejected by SSOT §8; the canonical 15-step pipeline is the one formalized, Apgi/Pipeline.lean, with the rejected orders stated as theorems), F10 (pushes need the author's key).

## Remaining tasks

### Next step (one at a time)

**Push apgi-validation, then apgi-lean**, and confirm the apgi-lean CI is green (its production-validation job checks out 604a3d9; its Python jobs check out 67a6c3f, now on GitHub):

```powershell
git -C C:\Claude\Projects\apgi-validation push origin main
git -C C:\Claude\Projects\apgi-lake push origin main
```

After that: **task 60** (finish and commit the K7 rerun).

### Phase A remainder
**60.** Finish the versioned K7 rerun on 67a6c3f (running; see above), review the gate table against TestCommittedGateTable, commit gates/ in apgi-implementation. Gate results from the hierarchical path or with γ_NE ≠ 0 before 67a6c3f also need rerunning if any were cited.
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules. The only remaining partial conformance test (TC-01).
**61b (optional).** Have production count clamped steps itself in `manifest()`; the harness report already satisfies TC-10.

### Phase B remainder
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering). Bounded above by the event-level study (CL-46); the dispositions do not depend on it.
**70 remainder.** Register r_max·T_W once B-13 fixes r_max.
**TC-25.** End-to-end assessment → scoring → storage → analysis with schema and consent checks: belongs to the application layer (apgi-validation / apgi-implementation), not this repository.
**TC-26.** Registered fidelity against the locked OSF record (osf.io/yk29g, Amendment 1): needs the methods, exclusions, thresholds and outcome classifications of SRC-OSF Tables 12, 13 and 15 registered with quotes, then compared field by field; pairs with B-07.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections** remaining: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status. (D10 and D11 done this round.) Also stale in the SSOT, not generated: the "Required before release (B-10)" paragraph lists golden-vector families that now exist (B-10 is closed).
**33 / B-13.** r_max and the operating point (F2).
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, the recovery readings and the 71a dispositions.
**B-07.** Second-reader check of the hypothesis register.
**B-17.** Independent reviewers (scientific, mathematical, implementation, statistical).
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.

### Phase D: next Zenodo release (v1.2)
**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing: re-hash every source; re-source EQ-CUSP-1, the task-53/54/54b rows, τ_Π, α_Π, the SSOT-sourced parameter rows and the bridges.json quotes to the published documents; retire SRC-MATHSPEC-V12D and SRC-SSOT-V12D; re-run extraction; confirm 0 corpus defects; fill the tag and DOI in the release manifest (B-11).

## Rating (1–100) against the SSOT

Initial (start of round 75, re-verified: build and tests green, but CI red on 680877b) → final (this round, verified as stated above):
- Architecture 92 → 93: the registry now generates the SSOT's own counts (the last hand-copied numbers), with a pin check that cannot loop.
- Mathematical correctness 93 → 93: no Lean source change; Spec.lean regenerated and `lake build --wfail` green.
- Specification coverage 95 → 97: TC-04, TC-08, TC-21 pass (23 of 26); 13 more parameter rows; D10, D11. Deductions: TC-25, TC-26, TC-01 approvals, behavior-level recovery.
- Implementation 90 → 93: every registered production divergence in both packages is resolved (22 of 22, 7 of 7 with one declared variant). Deduction: the full apgi-validation suite was not run on this PC (its CI must confirm 604a3d9).
- Proof completeness 89 → 89.
- Testing 96 → 97: eight planted faults in full_model, all caught; dispositions, label rows and the SSOT parts are under test.
- Reproducibility 89 → 90: verify_all now regenerates every committed report; deduction: round 75 not pushed, so its CI is not observed, and the K7 rerun is unfinished.
- Documentation 90 → 92: the SSOT's stale header and §23–§24 counts fixed; proof-status.json current; README and REPRODUCIBILITY updated.
- Publication readiness 70 → 73: decisions 62c and 71a recorded, D10, D11 done; blockers B-07, B-11, B-13, B-14, B-16, B-17, B-18, TC-25, TC-26 and approvals (61a) remain.
- **Overall 90 → 92.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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

`generate_lean.py` hashes all eleven registry files (now including bridges.json and requirements.json), so regenerate and rebuild after changing a production pin. If `test_production.py::test_production_run_report_is_current` fails, production or the pin changed: rerun production_report.py with APGI_IMPL_PATH at the pin and review the diff. If `test_recovery_pipeline.py::test_report_is_current` fails, the study design or code changed: rerun make_recovery_report.py and review the report diff (and GATE_EXPECTED if a gate outcome flips). If `check_consistency.py` reports `extraction_unverified` or `bridge_unverified`, a registry value or bridge record changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
