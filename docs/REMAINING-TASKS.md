# APGI verification: remaining tasks

State as of 2026-11-27 14:30 ET (round 74). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0**; the registry hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only:
  - apgi-lean: round 73 (3dd4d68) and f142bcd are on origin/main; CI "APGI verification" **green on 3dd4d68** (run 46045899533). Round 74 is three local commits on top, **not pushed**: a88abba (task 59b), 72a25fa (task 62b remainder), and the docs commit.
  - apgi-implementation: **new pin 67a6c3f** (local commit on top of 8d8e5bd, **not pushed**): the legacy extension path aligned with the SSOT (SSOT-P10, P12, P13) plus F17. 8d8e5bd remains green on every CI job (run 46029607584).
  - apgi-validation: f6fec65 (unchanged).
  - **Push order matters:** apgi-implementation first (the apgi-lean CI checks out 67a6c3f from GitHub), then apgi-lean.
- Round 74 checks. Python, cloud workspace (Python 3.13, numpy 2.5.3; and again under the CI pin Python 3.12, numpy 2.2.6): consistency 0 open, 0 unacknowledged, 0 stale; `generate_lean.py`, `make_traceability.py`, `production_report.py`, `make_recovery_report.py` `--check` current; apgi-lean pytest with production **357 passed, 1 skipped, 0 xfailed** (both numpy versions); without production 278 passed, 2 skipped; test_production_validation.py 11 passed, 2 skipped, 3 xfailed (SSOT-V3, unchanged). apgi-implementation at 67a6c3f, the CI commands: ruff 0.16.0 and ruff format clean, mypy 1.19.0 clean (105 files), `pytest -m "not performance"` **2839 passed, 11 skipped, coverage 96.66 %**, performance 5 passed, conformance/repeatability 31 passed. Lean (this PC, Windows): `lake build --wfail` on a88abba **Build completed successfully (7248 jobs)**, 13:41–13:51 ET; on 72a25fa (final Spec.lean) **Build completed successfully (7248 jobs)**, exit 0, 14:06 ET.
- Rating against the SSOT (1–100, nine dimensions): **overall 89 → 90**. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (derived and label rows of 54b), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **20 pass**, **4 partial** (TC-01 approval pending; TC-04, apgi_core.full_model (SSOT-V3, decision 62c); TC-08, dispositions 71a and behavior-level recovery; TC-21), **2 not implemented** (TC-25, TC-26).
- Lean: **196 theorems in 10 modules** (unchanged), every one axiom-pinned with `#guard_msgs`; 189 use exactly [propext, Classical.choice, Quot.sound], 7 a strict subset; no sorry, no admit, no axiom declaration.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: 46: 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (35 pass, 4 partial, 3 open, 2 not implemented).
- Production divergences: apgi-implementation **0 open of 22** (SSOT-P10, P12, P13 resolved this round; earlier rounds wrote "of 23", a miscount: the registry holds 22); apgi-validation 1 open of 7 (SSOT-V3), 1 declared variant.

## Done this round (2026-11-27, round 74)

**CI confirmed for round 73.** The author pushed 3dd4d68; "APGI verification" green (run 46045899533). The apgi-implementation run the author checked (46029607584) is on 8d8e5bd, the pin. Recorded in f142bcd (pushed).

**Task 59b: SSOT-P10, SSOT-P12, SSOT-P13 fixed in production (apgi-implementation 67a6c3f) and resolved in the registry (a88abba).**
- SSOT-P13: config.py `ne_on_threshold` defaults to True, so γ_NE ≠ 0 runs both NE pathways with one clamped g_NE (SSOT §11, EQ-THEFF-1). core/config_schema.py had two validators that rejected both pathways together and any γ_NE ≥ 0.1 (while accepting −0.3); both contradicted the SSOT and were removed; its `gamma_ne` default was 0.1 with `ge=0` (contradicting R6 / SSOT-P6) and is now 0, unsigned. The clamp |γ_NE|·g_NE ≤ 0.5 stays in the pipeline (rescale, as prescribed).
- SSOT-P12: EQ-MS-4 (Π/Π_max, factor band [0.5, 1.5]) in NestedResonanceSystem and hierarchical_threshold_modulation. In the legacy path every threshold modulation (NE, 5-HT, circadian, hierarchical) is now a read-out of the carried threshold (TC-11); before, all four were written back. With the P13 default an NE write-back would have compounded for γ_NE ≠ 0, so this was fixed with P12.
- SSOT-P10: (a) with the precision ODE on, S is driven by the multiscale S_inst from the ODE precisions, with the noise from the same weighted precision; (b) the resonance-level reset uses the configured δ_reset; DELTA_RESET removed.
- Default ssot_core path unchanged: the prod and dev golden masters are bit-identical and the production run report (TC-10/TC-14) changed only in its commit field. The staging golden master (full hierarchy) moved from final θ 20.0 AU (at the guard) to 1.833 AU.
- **F17 (new, fixed):** stats/maturity_assessment.assess_hierarchical_architecture could return a cascade score above 100 (516 for one seed); the suppression fraction is clipped to [0, 1]. Two apgi-implementation tests compared unseeded runs and failed about 3 in 15 runs at 8d8e5bd (CI runs four Python versions); both are seeded, the maturity test at a seed that fails without the fix.
- Evidence: the six SSOT-P10/P12/P13 strict xfails XPASSed against 67a6c3f before the registry was changed; they now run as ordinary tests. Pin moved in known-conflicts.json and the CI checkout.

**Round-74 audit (planted faults in a scratch copy of 67a6c3f, mutate script, one fault at a time):** P13 default off (2 tests fail); P12 /Π_max removed (1); P10 a ODE drive off (1); P10 b `or 0.5` restored (1); **P12 band removed: survived**; **P12 write-back restored: survived** (with the normalized factor θ never reaches the guard the test watched). Added test_pac_threshold_factor_band (κ_down = 1, factor 1.5 / 0.5), test_pac_modulation_leaves_carried_threshold_unchanged (carried θ bitwise independent of κ_down, decision threshold not), test_legacy_neuromodulator_offsets_are_read_out_only (NE+, NE−, 5-HT). After that, all seven faults (the six above plus an NE/5-HT write-back) are caught.

**Task 62b remainder: η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair (72a25fa).** Two blocks added to the synthetic design (30 subjects × 300 s, oracle event observation, CL-46): allo_c2v2 (τ_θ, k_C2, k_V2 free; δ_reset known) and c2_reset (k_C2, δ_reset free). Against the §17 gate (r > 0.85, error < 0.2): k_C2 r 0.803 / error 0.157, k_V2 r 0.580, τ_θ r 0.592, all FAIL; posterior correlation k_C2~k_V2 +0.69 (the events constrain mainly their net effect). c2_reset: k_C2 r 0.570, δ_reset r 0.793, both FAIL, correlation −0.59. SBC calibrated in every block (min p 0.25); the posterior predictive beats the null in both blocks. The four existing blocks reproduce bit for bit.

## Previous round (2026-11-27, round 73)

**Pin moved to 8d8e5bd.** The author applied the F13 patch and pushed (8d8e5bd, every CI job green). known-conflicts.json `production.commit` and the CI checkout now name 8d8e5bd. The diff to d153f6a is formatting and annotations; the full suite gives the same results at both commits.

**Task 61b / TC-10 → pass. Production clamp fraction reported.** New verification/python/production_report.py runs the pinned production core for CFG-CORE and CFG-CORE-R on 60 s of seeded stimulus-free N(0, 1) input, runs apgi_ref.core_step on the same inputs and uniform draws, and writes verification/reports/production-run-report.json: clamped-step fractions (precision, NE), the observed precision range, events and event rate, and the TC-14 operating point, production next to reference. Results: both configurations clamp on 0 % of stimulus-free steps; 38 events (0.63 /s, CFG-CORE) and 253 (4.22 /s, CFG-CORE-R), identical in production and reference; γ_sig·θ₀ = 0.7, floor 0.332, nominal baseline 33.2 /s (the F2 / B-13 operating-point question, unchanged). Tests (test_production.py): the report is current and agrees with the reference; with binding clamps (low-variance segments in each channel; gains g_ACh = g_NE = 2; |γ_NE|·g_NE = 2) the production fraction equals the reference's (0.38 for precision, 1.0 for NE) and precision stays in [Π_min, Π_max]; the flag function is checked on bound and interior values. Limitation: the fractions are derived by apgi-lean from production's per-step outputs; production does not count clamped steps itself.

**Task 59: SSOT-P10 under test; one suspicion refuted; two new divergences.** Legacy extension path (model_form legacy_v1_1), experiments first, then tests:
- SSOT-P10 (a) confirmed: with the hierarchical precision ODE on, doubling g_ACh (inverse-variance chain only) changes S while the ODE precisions and z are unchanged: two precisions in one simulation. Strict xfail.
- SSOT-P10 (b) refined: the suspected double δ on the primary threshold is **refuted**: one ignition raises it by exactly one δ_reset (new passing test, δ = 0 and 0.2). The real defect is a second δ value: the resonance-level threshold reported at the ignition step jumps by DELTA_RESET = 0.5 even when δ_reset = 0 (`or 0.5`). Strict xfail.
- **SSOT-P12 (new, P1):** the PAC threshold coupling omits the /Π_max of EQ-MS-4 (factor range [0, 2] instead of [0.5, 1.5]) and writes the modulated threshold back into θ, so it compounds (TC-11): under stimulus-free input with κ_down = 0.1, θ sits at the 20 AU numerical guard on 1117 of 4000 steps; with κ_down = 0, on none. Two strict xfails.
- **SSOT-P13 (new, P1, found while testing TC-10):** any run with γ_NE ≠ 0 at production defaults drops the NE threshold pathway (ne_on_threshold = False), although SSOT §11 states that both NE pathways share one clamped g_NE and EQ-THEFF-1 applies (1 + γ_NE·g_NE). With ne_on_threshold = True production matches the reference step for step. Strict xfail (γ_NE = 0.2 and −0.3).

**Task 62b (TC-04 part): apgi_core.full_model trajectory-tested; SSOT-V3 (new, P1).** Driven by the reference's own Π and z, full_model reproduces S exactly until the first ignition (passing test), then diverges: (a) it decides ignition from S(t+1), θ(t+1), not the existing S(t), θ_eff(t) (SSOT §8 step 8); (b) it has no retention reset (EQ-RESET-1); (c) its threshold step is forward Euler with its own cost, value and facilitation terms, and it cannot express η_θ = 0. Three strict xfails. TC-04 stays partial until full_model is aligned or declared a variant (task 62c, author).

Round 73 audit (six planted faults, all caught) and the "not done" list are in git history (3dd4d68).

## Findings this round

- **F18 (new, identifiability):** c₂·B(t−1) (EQ-COST-1) and δ_reset·B(t) (EQ-ALLO-1) are the same per-event threshold increment one step apart, so they are confounded in recovery (correlation −0.59; neither passes §17). The SSOT §17 degeneracy table names c₁, v₁, v₂, η_θ but not c₂ or this pair: a proposed SSOT correction (D11 under task 57). Together with F12: of the allostatic quantities only k_V = η_θ·v₁ passes §17 at the current design.
- **F17 (closed):** maturity score above 100 and two unseeded apgi-implementation tests; fixed in 67a6c3f.
- **F14, F15 (closed):** SSOT-P12, SSOT-P13 fixed in 67a6c3f. Results computed earlier with use_hierarchical = True and κ_down > 0, or with γ_NE ≠ 0 at the old defaults, are not SSOT-model results and need a versioned rerun (task 60).
- **F16 (open):** SSOT-V3, apgi_core.full_model diverges after the first ignition (decision 62c).
- F12 (identifiability, decision 71a, now wider), F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F7 (memory), F8 (the 17-step loop is rejected by SSOT §8; the canonical 15-step pipeline is the one formalized, Apgi/Pipeline.lean) unchanged. F10: pushes need the author's key.

## Remaining tasks

### Next step (one at a time)

**Push apgi-implementation, then apgi-lean**, and confirm both CIs are green (the apgi-lean run checks out 67a6c3f):

```powershell
git -C C:\Claude\Projects\apgi-implementation push origin main
git -C C:\Claude\Projects\apgi-lake push origin main
```

After that: **task 71a** (author decision), now covering τ_θ, η_θ·c₁, η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair.

### Phase A remainder
**60.** Versioned rerun of K7 and the gate results on the current pin (Phase A and round 74 changed outputs; any result from the hierarchical path or with γ_NE ≠ 0 before 67a6c3f is affected).
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules.
**61b (optional).** Have production count clamped steps itself in `manifest()`; the harness report (production_report.py) already satisfies TC-10.

### Phase B remainder
**54b.** The remaining derived and label parameter rows: α_EMA and β_Σ (EQ-EMA-2), m_Ψ, K_ℓ / K_ℓm, τ_min / τ_max, R_L, α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh. Needs the v1.1 corpus folder (C:\Claude\Projects\Neuro-Brain) connected.
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering). η_θ·c₂ and η_θ·v₂ done this round.
**62c (author).** SSOT-V3: align apgi_core.full_model with the SSOT core (decision from the existing S, retention reset, EQ-ALLO-1 threshold step) or label it a declared variant with MODEL_FORM. TC-04 passes after either.
**70 remainder.** Register the guess rate g (with 54b) and r_max·T_W (once B-13 fixes r_max) so test_recovery.py reads them from the registry.
**71a (author).** §17 failed-recovery disposition (SSOT §17: exactly one of fixed from external measurement, constrained by a stated informative prior, or redesignated as requiring auxiliary measurement; never freely fitted) for τ_θ, η_θ·c₁ (F12), η_θ·c₂, η_θ·v₂ and the c₂ / δ_reset pair (F18), and a statement that η_θ is reported only through its products with c and v (CL-45). TC-08 passes once recorded and REQ-TC-08 cites them (behavior-level recovery remains as its limitation).

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status (closed on run 45931170311); D10 regenerate the header and §24–§25 from the registry: spec 0.6.0, 196 theorems in 10 modules, CL-1…CL-46, 26 conformance tests (20 pass), 57 golden vectors in 14 families, 59 equations, requirements.json and bridges.json added; **D11 (new)** add "c₂ × δ_reset: per-event increments one step apart; declared trade-off; TC-08g" to the §17 degeneracy table (F18).
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

Initial (start of round 74 = end of round 73) → final (this round, verified as stated above):
- Architecture 92 → 92.
- Mathematical correctness 93 → 93: no Lean source change; `lake build --wfail` green.
- Specification coverage 94 → 95: TC-08g now covers every allostatic weight (c₁, c₂, v₁, v₂) and the c₂ / δ_reset pair; the legacy path's threshold read-outs are under test. Deductions: dispositions (71a), behavior-level recovery, TC-25, TC-26, 54b rows.
- Implementation 86 → 90: all 22 apgi-implementation divergences resolved; the schema no longer contradicts the SSOT on NE; F17 fixed. Deductions: SSOT-V3 in apgi-validation; legacy-path results before 67a6c3f need a rerun (task 60).
- Proof completeness 89 → 89.
- Testing 95 → 96: two planted faults survived the existing tests and were closed with sharper ones (seven caught); two flaky production tests fixed; every changed module rerun under both numpy pins.
- Reproducibility 91 → 91: everything reproduced from fresh public clones plus bundles with identical commit hashes; deduction: round 74 is not pushed, so its CI is not observed.
- Documentation 90 → 90.
- Publication readiness 69 → 70: no open production divergence in apgi-implementation; blockers B-07, B-13, B-14, B-16, B-17, B-18, tag and DOI, decisions 71a and 62c remain.
- **Overall 89 → 90.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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
