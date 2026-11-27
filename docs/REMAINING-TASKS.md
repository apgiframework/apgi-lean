# APGI verification: remaining tasks

State as of 2026-11-27 10:20 ET (round 72). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0**; the registry hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only:
  - apgi-lean: rounds 68–71 are on origin/main (7aec2c0, pushed by the author 2026-11-27); GitHub Actions "APGI verification" **green on 7aec2c0** (run 46016038433). This round (72) is one local commit on top, not yet pushed.
  - apgi-implementation: main at **d153f6a** (pushed; contains e0e82cf). **New pin d153f6a.** CI on d153f6a: every job green (tests on 3.10–3.13, numerical parity, PyMC parity, reproducibility, K7c, stability, security, performance, wheel, dependency policy) **except "lint & types"**, which has failed since 72ad050 (F13). The fix is prepared as a patch, not yet applied to the author's checkout: `.scratch\0001-CI-restore-the-lint-types-gate-ruff-ruff-format-mypy.patch`.
  - apgi-validation: f6fec65 (unchanged).
- Local results (this PC, `verification\verify_all.ps1 -Impl .scratch\impl-pin`, production at the pin 72ad050, 08:45–09:01 ET): extraction 93 verified, 0 failed; `lake build --wfail` green (7248 jobs, 10 modules plus the generated Spec); consistency 0 open, 0 unacknowledged, 0 stale; recovery study regenerated (152 s, identical to the previous run); apgi-lean pytest **331 passed, 1 skipped, 4 xfailed**; test_production_validation.py 10 passed, 2 skipped.
- Round 72 checks (Linux VM, Python 3.10, production at d153f6a; Lean not rebuilt locally, only Spec.lean's hash line changed, so `lake build` is left to CI): consistency 0 open, 0 unacknowledged, 0 stale; apgi-lean pytest **335 passed, 0 xfailed** across all 16 test files except test_production_validation.py (the four SSOT-P11 strict xfails now pass as ordinary tests); generate_lean, release manifest and traceability regenerated.
- Rating against the SSOT (1–100, nine dimensions): **overall 88 → 89** this round. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (derived and label rows of 54b), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **19 pass** (TC-13 added this round), **5 partial** (TC-01 approval pending; TC-04; TC-08, all four §17 diagnostics, two gate failures awaiting disposition; TC-10 production clamp fraction; TC-21), **2 not implemented** (TC-25, TC-26).
- Lean: **196 theorems in 10 modules** (was 187), every one axiom-pinned with `#guard_msgs`; 189 use exactly [propext, Classical.choice, Quot.sound], 7 a strict subset; no sorry, no admit, no axiom declaration.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: **46** (was 44): 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (34 pass, 5 partial, 3 open, 2 not implemented).

## Done this round (2026-11-27, round 72)

**Pushes confirmed and CI observed.** The author pushed apgi-lean 7aec2c0 and apgi-implementation d153f6a. CI read from the public GitHub API (F10 no longer blocks observation): apgi-lean green on 7aec2c0; apgi-implementation green on every job of d153f6a except "lint & types".

**SSOT-P11 closed; pin moved to d153f6a.** specification/known-conflicts.json: SSOT-P11 `resolved` (fix text moved to `resolution`), production.commit d153f6a152cb…; .github/workflows/lean_action_ci.yml checks out the same commit. REQ-TC-13 `partial` → `pass`; its remaining limitation (overflow is a float64 property, established by tests, not proof) stays on record. Regenerated: Apgi/Spec.lean (registry hash d3afe09c…), verification/reports/{conflicts,release-manifest}.json, traceability.csv, docs/traceability-matrix.md, docs/assumption-inventory.md. Evidence: test_production.py 59 passed, 0 xfailed at d153f6a; full apgi-lean suite 335 passed.

**F13 (apgi-implementation CI): "lint & types" red since 72ad050; fix prepared.** Ruff stopped the job before the format check and mypy ran, so three layers were hidden: ruff I001 (pipeline.py import order) and N812 (test aliases PCFG, PP), 6 files unformatted, and 6 mypy errors (untyped helpers in core/ssot_core.py from e0e82cf; `run_channel(**channel_kwargs: float)` broken by 72ad050's `reference_window: int | None`). Commit "CI: restore the lint & types gate" fixes all three; formatter edits are AST-identical except the moved import; no behaviour change. Verified: ruff 0.16.0 and mypy 1.19.0 clean (105 files); production suite 2840 passed, 12 skipped, 0 failed (per file, Python 3.10). Exported as a patch to .scratch (gitignored) because apgi-implementation is not a connected folder in this session.

## Previous round (2026-11-27, tasks 70–71)

**Task 71 (= 62b): TC-08d–g, the full-pipeline recovery study (TC-08 stays partial).**
- *The exact part of TC-08g, proved* (Apgi/Identifiability.lean, 9 new theorems, CL-45): EQ-ALLO-1 sees η_θ and the weights c₁, c₂, v₁, v₂ only through η_θ·c₁, η_θ·c₂, η_θ·v₁, η_θ·v₂. Scaling η_θ by a ≠ 0 and the weights by 1/a gives the identical trajectory for every input and draw sequence (`pipeStep_scaleAllo`, `traj_scaleAllo`, `scaleAllo_not_injective`); with η_θ = 0 the weights do not enter at all (`traj_weights_eta_zero`). So η_θ, c₁, v₁, v₂ cannot be recovered separately from any data; only the products can.
- *The study* (verification/python/recovery_pipeline.py, make_recovery_report.py, test_recovery_pipeline.py, 19 tests; report verification/reports/recovery-pipeline.json). The canonical pipeline vectorized over a parameter grid; it reproduces apgi_ref.core_step step for step (same events, S and θ to 1e-12, same log-likelihood) with every CFG-CORE term on. Observation: every-step ignition events with known inputs, an exact likelihood. This is an upper bound on what behavior identifies (CL-46, assumed: a report is a parameter-free garbling of the events; data-processing inequality for Fisher information). Truths are drawn from the grid prior, so the grid posterior is the exact posterior and SBC is exact. Design constants are synthetic and listed in fixtures/recovery_design.json; the registered values it uses are checked against the registry; dt = 0.025 s satisfies EQ-STEP-1.
- *Results (30 subjects per block, 300 s sessions; gate r > 0.85 and median range-scaled error < 0.20):*
  - TC-08e/g, fast design (pulses every 3 s): k_V = η_θ·v₁ **passes** (r 0.904, error 0.089); τ_θ **fails** (r 0.753, error 0.139; posterior sd 0.71 of prior); k_C = η_θ·c₁ **fails** (r 0.30, error 0.226; posterior sd 0.99 of prior, flat profile likelihood). Median posterior correlation τ_θ ~ k_V = **−0.79**: the declared adaptation-versus-recovery trade-off.
  - Same, slow block design (40 s on / 40 s off): k_V passes (r 0.917); τ_θ fails worse (r 0.480); k_C fails (r 0.36); τ_θ ~ k_V = −0.79. The block design did not separate adaptation from recovery; that hypothesis was tested and is rejected for this design.
  - TC-08d: γ_NE (r 0.976) and g_NE (r 0.907) **pass** with both NE pathways and the EQ-NE-1 clamp active; posterior correlation +0.20.
  - TC-08f: γ_sig **passes** with the precision scale Π̄ free (r 0.985; 0.988 with Π̄ known); the scale itself passes (r 0.932); correlation +0.18. The scale is identified here only because θ₀ is fixed at its registered value; with θ₀ free, TC-08c makes it exactly degenerate.
  - SBC: every recovered quantity in every block, χ² p > 0.29 (10 bins). Out-of-sample: on held-out sessions the posterior predictive beats the block's null by 69.5, 34.6 and 29.6 nats per session (allo fast, allo blocks, NE), and is within 0.6 nats of the truth.
- *Not covered:* the §17 failed-recovery disposition for τ_θ and η_θ·c₁ (author, 71a); fits to behavioral reports rather than events; η_θ·c₂ and η_θ·v₂ (held at 0 in this design).

**F11 closed in code (apgi-implementation d153f6a, local).** The six production-suite failures were code portability defects, not only environment: `estimation/pymc_models.py` unpacked the deprecated `(outputs, updates)` return of `pytensor.scan`, which `filterwarnings = error` turns into five failures with pytensor 2.38.3 (and which a future pytensor will break outright); it now passes `return_updates=False` where scan accepts it. `tests/test_remaining_coverage_fixes.py` read a UTF-8 file with the platform encoding; it now opens it as UTF-8. Both affected test files: 18 passed on Windows, Python 3.12, without PYTHONUTF8. The full production suite was not rerun after this commit.

**Task 70 (partial).** The design constants of the new study are in one file (fixtures/recovery_design.json), marked as synthetic, and the registered values it uses are checked against the registry by test. test_recovery.py still carries its own constants; registering g and r_max·T_W waits on 54b and B-13.

**Hygiene.** verify_all.ps1 runs make_recovery_report.py (blocks in parallel, about 2.5 min). test_report_is_current fails whenever the design or the study code changes without the report being regenerated (sha256 of both).

**Audit evidence (planted faults, this round; .scratch\r70\mutate.py).** Five faults, planted one at a time and restored, were all caught:
1. core_loop with the two V channels swapped: test_simulator_matches_core_step fails.
2. core_loop propensity against θ instead of θ_eff: test_simulator_matches_core_step fails.
3. Event and non-event log-likelihood swapped: the log-likelihood check fails.
4. `PipeParams.scaleAllo` without scaling η: `pipeStep_scaleAllo` fails (rfl), so the proof uses the scaling.
5. `pipeStep_weights_eta_zero` without the η = 0 hypothesis: the proof fails, so the hypothesis is necessary.
SBC itself is shown not to be vacuous: a likelihood with r_max off by 2× gives p < 0.001 (test_sbc_detects_a_mismatched_likelihood).

**Previous round (68–69), for reference:** TC-13 stability proofs and handling, TC-08a–c, the §17 gate for θ_eff and γ_sig, TC-19, SSOT-P11 (production fix e0e82cf). Details in git history (6167b48).

## Findings this round

- **F12 (identifiability, for the author).** Even with every-step event observation, τ_θ and η_θ·c₁ do not pass the §17 gate in either tested design, and η_θ cannot be separated from c₁, v₁, v₂ at all (proved). §17 requires one disposition per failed parameter before data collection: fixed from external measurement, constrained by a stated informative prior, or redesignated as requiring auxiliary measurement (task 71a).
- **F11** is a code defect, not only an environment issue (above); fixed locally.
- **F10 (permissions)** narrowed: pushes still need the author's key, but CI status is now read from the public GitHub API.
- **F13** (apgi-implementation lint & types gate): fixed in a prepared patch, not yet pushed (above).
- F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F5 (SSOT-P10), F7 (memory), F8 (17-step loop rejected by SSOT §8), are unchanged. F9 / SSOT-P11 is closed (pin d153f6a).

## Remaining tasks

### Next step (one at a time)

**Apply the F13 patch and push both repositories** (github-apgi key loaded):

```powershell
git -C C:\Claude\Projects\apgi-implementation am C:\Claude\Projects\apgi-lake\.scratch\0001-CI-restore-the-lint-types-gate-ruff-ruff-format-mypy.patch
git -C C:\Claude\Projects\apgi-implementation push origin main
git -C C:\Claude\Projects\apgi-lake push origin main
```

Then confirm CI: apgi-implementation fully green (including "lint & types"); apgi-lean green with the new pin d153f6a (`lake build` of the regenerated Spec.lean, SSOT-P11 tests passing). The pin stays at d153f6a: the patch changes no behaviour, and `git am` gives the commit a new hash on the author's machine.

After that: **task 71a** (author decision): the §17 disposition for τ_θ and η_θ·c₁.

### Phase A remainder
**59.** Put SSOT-P10 under test (hierarchical precision mixing, resonance δ), then fix it in the legacy extension path (apgi-implementation).
**60.** Rerun K7 and the gate results on 72ad050 as a versioned rerun (Phase A changed outputs).
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules.
**61b.** Report the clamped-step fraction from production (`manifest()` or the run log), as apgi_ref.clamp_report does.

### Phase B remainder
**54b.** The remaining derived and label parameter rows: α_EMA and β_Σ (EQ-EMA-2), m_Ψ, K_ℓ / K_ℓm, τ_min / τ_max, R_L, α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh.
**62b remainder.** Behavior-level recovery (fits to reports, not events, e.g. by particle filtering), η_θ·c₂ and η_θ·v₂, and a TC-04 trajectory test for apgi_core.full_model.
**70 remainder.** Register the guess rate g (with 54b) and r_max·T_W (once B-13 fixes r_max) so test_recovery.py reads them from the registry.
**71a (author, new).** §17 failed-recovery disposition for τ_θ and η_θ·c₁ (F12), and a statement that η_θ is reported only through its products with c and v (CL-45). TC-08 passes once the dispositions are recorded and REQ-TC-08 cites them.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status (now closed on run 45931170311); D10 regenerate the header and §24–§25 from the registry: spec 0.6.0, 196 theorems in 10 modules, CL-1…CL-46, 57 golden vectors in 14 families, 59 equations, requirements.json and bridges.json added.
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

Initial (start of round 72 = end of round 70–71, 88) → final (this round, verified as stated above):
- Architecture 92 → 92.
- Mathematical correctness 93 → 93: no Lean change except the generated hash line.
- Specification coverage 92 → 93: TC-13 passes end to end (reference and production). Deductions: dispositions (71a), behavior-level recovery, L3–L4 qualitative, CFG-FULL undefined.
- Implementation 87 → 88: the pinned production code carries no open P1 divergence (SSOT-P11 closed); the lint/type gate defects are fixed in a prepared commit. Deductions: that commit is not yet pushed; SSOT-P10 and the clamp report are open.
- Proof completeness 89 → 89.
- Testing 94 → 94: the four strict xfails became passing tests; the production type gate (mypy) was found not to have run and now passes locally. Deductions: TC-25, TC-26; behavior-level recovery.
- Reproducibility 89 → 90: CI observed green on apgi-lean 7aec2c0 and on every behavioural job of apgi-implementation d153f6a. Deduction: the lint gate is red until the patch is pushed; `lake build` for this round's commit is not yet observed.
- Documentation 89 → 89.
- Publication readiness 69 → 69: the blockers B-07, B-13, B-14, B-16, B-17, B-18, the tag and DOI, and decision 71a are unchanged.
- **Overall 88 → 89.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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

`generate_lean.py` hashes all eleven registry files (now including bridges.json and requirements.json), so regenerate and rebuild after changing a production pin. If `test_recovery_pipeline.py::test_report_is_current` fails, the study design or code changed: rerun make_recovery_report.py and review the report diff (and GATE_EXPECTED if a gate outcome flips). If `check_consistency.py` reports `extraction_unverified` or `bridge_unverified`, a registry value or bridge record changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
