# APGI verification: remaining tasks

State as of 2026-11-26 22:00 ET. Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.5.0**; the hash is written by `generate_lean.py` into Apgi/Spec.lean and by `make_release_manifest.py` into verification/reports/release-manifest.json.

- Repositories, all `main` only. apgi-implementation and apgi-validation are pushed; apgi-lean is pushed up to the history rewrite and needs one force-push (see "Next step"):
  - apgi-lean: bba9f0f "Tasks 52-56 …" on 5fb2487 "Task 53 …" (both rewritten on 2026-11-26 to drop the v1.2 drafts, see F1).
  - apgi-implementation: **72ad050** (was a9b2878), pinned in known-conflicts.json and CI.
  - apgi-validation: **f6fec65** (was 811aee2 / 07ca731), pinned in known-conflicts.json and CI.
- Local results (this PC): `lake build --wfail` green (5 Lean modules plus the generated Spec); `check_consistency.py` 0 open, 0 unacknowledged, 0 stale; extraction 85 of 85 evidence-bearing parameters verified against the pinned sources; apgi-lean pytest with APGI_IMPL_PATH 237 passed, 1 skipped; test_production_validation.py 10 passed, 2 skipped.
- Rating against the SSOT: **design 94/100, implementation 84/100, release readiness 71/100** (was 92 / 60 / 61). Reasons are at the end of this file.

## Push status (task 2, done 2026-11-26)

All three repositories were pushed by Uxod: apgi-implementation 72ad050, apgi-validation f6fec65, apgi-lean 2f4e562 (since rewritten, see F1). The CI run on the new pins is still to be confirmed (B-15).

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18 (56%)**: B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. B-15 must be re-confirmed by the first CI run after the push. B-09 and B-11 are mostly done but stay open (see Phase B and C).
- Conformance tests TC-01…TC-26: **16 pass** (TC-02, 03, 05, 06, 07, 09, 11, 12, 14, 15, 16, 17, 18, 22, 23, 24); **6 partial** (TC-01 the registry records lack the SSOT record-status axis and owner/approval fields; TC-04 production core == reference step for step, but apgi_core.full_model is not trajectory-tested; TC-10 the clamped-step fraction is not reported; TC-13; TC-19; TC-21 the SSOT document text itself is stale, see D10); **4 not implemented** (TC-08 recovery, TC-20 convergence, TC-25 end-to-end, TC-26 registered fidelity). 62% pass; 73% with partials at half weight (was 27% / 50%).
- SSOT equation IDs in `equations.json`: **53 of 53 (100%)** plus 6 legacy IDs (EQ-PREC-1, THR-1, DECAY-1, UPD-1, EULER-1, PIPE-1); 59 in total. **Every registered equation has a Lean-backed statement (59 of 59)**, which is scope decision (b).
- Parameters in `parameters.json`: 86 (was 49). Every SSOT §4 table row is registered except the derived and label entries: α_EMA and β_Σ (EQ-EMA-2), m_Ψ (computed), K_ℓ / K_ℓm, τ_min / τ_max (participant-estimated), R_L (EQ-BR-3), α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh.
- Lean: **119 theorems in 5 modules, 119 of 119 axiom-pinned to [propext, Classical.choice, Quot.sound]**, no sorry (was 41). Claim register: 31 claims, 28 proved, 1 assumed (CL-8), 2 unresolved (CL-7 hysteresis in human data, CL-26 Lyapunov conjecture).
- Golden vectors: **57 in 14 families** (was 25 in 6). All 8 required B-10 families exist, plus seeded CFG-CORE and CFG-CORE-R trajectories (120 steps each, with sha256).
- Prohibited-shortcut checks (SSOT §8): **the apgi-implementation default path meets 7 of 7**; apgi_core.full_model meets the drive and leak checks; apgi_core.model is a declared variant.
- Production divergences: **all of SSOT-P1…P9, PD-LOOP-GAIN and SSOT-V2 are resolved** (the former strict xfails now pass). SSOT-V1 is a declared variant (labelled, checked). **Open: SSOT-P10** (extension path only, not yet under test).
- SSOT worked numbers recomputed: 31 of 31 correct, plus the §12.2 timescale table, the §15 κ_beh example and the §12.5 loop-gain numbers (now tests).

## Done this round (2026-11-26)

**Task 55 (SSOT-R2 and the SSOT "next targets"): Apgi/Core.lean, 19 theorems.**
- EQ-DRIVE-1: `driveTerm_monotone_iff`: the channel drive is monotone in Π_rel **if and only if** |z| ≥ m₀. `driveTerm_strictAnti_of_lt`: below m₀ more precision makes ignition harder. `ignites_drive_monotone_precision` replaces `ignites_monotone_precision` as the statement about the canonical drive. Also sign symmetry (TC-09).
- m₀ identity: `meanAbsStdNormal_eq`: E|z| = √(2/π) (∫|x|e^{−x²/2} = 2).
- Hard-threshold limit: `ignitionProb_at_threshold` (Bₜ = ½ at S = θ_eff for every γ_sig), `ignitionProb_tendsto_one` and `ignitionProb_tendsto_zero` as γ_sig → ∞.
- Read-out non-interference: `coreStep_readout_noninterference`. The state update has no read-out argument, so θ_eff reaches the next state only through B(t). Exactly-once rules for δ_reset (decayed once), δ_ref and ρ_retain.
- EQ-CUSP-2 folds: `cusp_discriminant_iff_fold` (three equilibria iff |θ̃| < 2(−a/3)^{3/2}), monostability past the ignition and extinction folds.

**Task 54 (B-09, B-05, SSOT-R1, SSOT-R3): registry completeness.**
- 31 equation entries (EQ-ERR-1 … EQ-BR-3), each with Python reference functions in apgi_ref.py and tests in test_registry_equations.py.
- 37 parameter rows, sourced to the SSOT tables. There is a new pinned source, SRC-SSOT-V12D, which ranks last; these rows move to the published v1.2 sources at task 25. SSOT-R3 is resolved: C_down·τ_Π ∈ [0.1, 0.5] and C_up·τ_Π ∈ [0.05, 0.2] are registered as dimensionless gains. A new unit, AU/s.
- `symbols.json` (TC-03): 86 parameter symbols, 24 state variables, reserved and retired symbols; uniqueness is tested.
- `configurations.json` (B-05, TC-16): CFG-CORE (11 fitted, 2 measured, 19 fixed, 11 latent states, 2 inputs; hazard sampling, additive channels) and CFG-CORE-R (12 fitted). CFG-FULL is reserved with null counts and a registered reason (extension parameters not frozen). The retired names are CFG-CORE8 and CFG-FULL14.
- `revisions.json`: R1–R18 with status, action and linked test.
- Apgi/Extensions.lean (25 theorems) and Apgi/Coverage.lean (34 theorems): a Lean statement for every remaining equation. Highlights:
  - `pred_contraction`: η_pred·Π < 2.
  - `da_salience_iff`: the dopamine bias raises salience only while zⁱ > −β_DA/2.
  - `loopGain_lt_one_of_paper3`, `loopGain_production_defaults` (2 × 10⁴), `loopGain_scaled_couplings` (0.02).
  - `floor_le_one_percent_iff`: the floor ≤ 0.01 iff γ_sig·θ ≥ log 99.
  - `alloPath_hasDerivAt`: the closed form solves EQ-ALLO-C1.
  - `landauer_310K_within_tolerance`.
  - The normalization budget, the timescale forms, aggregation bounds, the MS-4 band, Kuramoto and the reservoir bounds.

**Task 56 (B-10): golden vectors.** Families hazard_prob, leak_step, ne_clamp, threshold_step, psi, prec_eff and ema_update (estimator ordering). The seeded CFG-CORE and CFG-CORE-R trajectories come from a 50-digit replica of `core_step`. The quantitative TC-15 fixture is `test_core.py::test_tc15_quantitative_signature`: at seed 40404, a θ₀ shift from 0.35 to 0.80 moves c from −0.10 to +1.30 while d′ changes by −0.20; a Πᵉ_rel shift from 0.7 to 1.4 raises d′ from 0.52 to 0.94 with the FA rate held at 0.401 → 0.407.

**Phase A (tasks 45–51) and PD-LOOP-GAIN (task 35, B-12): apgi-implementation 72ad050.**
- New `core/ssot_core.py`: the canonical 15-step pipeline. `APGIPipeline.step()` delegates to it under `model_form="ssot_core"`, the new default.
- Any enabled extension runs the v1.1 pipeline and is labelled `model_form="legacy_v1_1"` in the config and the manifest (`extensions_active`).
- CONFIG: θ₀ = 0.35, hazard sampling, β_DA = 0, γ_NE = 0 (R6), α_EMA from T_window (5 s / 10 s), C_down = 0.1/τ_Π, C_up = 0.05/τ_Π.
- The NE clamp works for either sign. `manifest()` reports the operating point.
- `engine.PrecisionWeightedErrorChannel` gets a `reference_window` option (SSOT order).
- dev.toml and prod.toml: θ₀ = 0.35. Golden master regenerated (deliberate numerical change, stated in the commit).
- apgi-implementation suite: 2833 passed, 8 skipped. The 5 failures are tests/test_estimation_pymc.py on this PC only: the pytensor DeprecationWarning is raised as an error. They are unrelated and unchanged.
- apgi-lean `test_production.py::test_production_core_matches_reference_trajectory` (TC-04) checks the production core against `apgi_ref.core_step`: S_inst, θ_eff, Bₜ, B(t), S and θ for 400 seeded steps, CFG-CORE and CFG-CORE-R, with shared uniform draws.
- **Phase A changes model outputs**: K7 and the gate results need a versioned rerun before citation (SSOT §8, last paragraph).

**Task 52 (SSOT-V1, V2): apgi-validation f6fec65.**
- `full_model.signal_accumulation` uses the excess drive and the exact leak weight (V2 resolved).
- `model.py` carries `MODEL_FORM = "energy_form_variant"`, and its header states that it is not the minimal core. V1 is now `declared_variant`: its core-behaviour tests are skipped, and `test_declared_variants_are_labelled` checks the label.
- apgi_core-related tests: 68 passed, 5 failed. The same 5 fail at 07ca731 on this PC (protocol_lock CRLF digests, `.env.example` missing APGI_LOG_DIR, a zero benchmark timing). The full apgi-validation suite hits a pytest INTERNALERROR during collection on local Python 3.12; CI uses 3.11 with the lock file.

**Task 58 (B-11), licenses:** MIT LICENSE in apgi-lean and apgi-validation, matching apgi-implementation. `make_release_manifest.py` writes verification/reports/release-manifest.json with the three repositories, their commits and licenses, CC BY 4.0 for text and records, the toolchain, and the sha256 of every registry, Lean and golden-vector file. The v1.2 tag and DOI stay null until task 25.

**D9 (SSOT-D9):** the v1.2 Math Spec draft no longer says "γ_NE default > 0" (Table 1, §4.4). The pre-edit copy is .scratch/APGI-Mathematical-Specifications.pre-D9.md (git-ignored). SRC-MATHSPEC-V12D was re-pinned to cd8bde37… and re-extracted.

**Repository hygiene:**
- `verification/verify_all.ps1` runs the whole routine and writes .verify.log.
- The v1.2 drafts (docs/apgi-v-1-2/, docs/APGI-Single-Source-of-Truth.md) were untracked and git-ignored, per the repository's own rule "never commit (public repo)". See finding F1.

## Findings this round

- **F1 (resolved by history rewrite, 2026-11-26).** Task-53 commit 1411665 had pushed the unpublished v1.2 drafts in docs/apgi-v-1-2/ (10 files) to the public repository against .gitignore's rule. Author decision: rewrite and force-push. `git filter-repo --path docs/apgi-v-1-2/ --invert-paths --refs 4f717cd..main` rewrote only the two commits that carried the drafts: 1411665 → 5fb2487 (identical except the 10 drafts) and 2f4e562 → bba9f0f (identical tree). The 12 earlier commits keep their hashes and SSH signatures. Backup: .scratch/apgi-lean-pre-rewrite-2f4e562.bundle (local, git-ignored). After the force-push, GitHub can still serve 1411665 and 2f4e562 by direct SHA until it garbage-collects; ask GitHub Support to purge cached views if that matters, and any existing clone or fork keeps the old commits.
- **F2 (B-13, owner Uxod).** The production operating point is still the placeholder: γ_sig = 2 (τ_σ = 0.5) and r_max = 100 s⁻¹ give a floor of 0.332 and a stimulus-free rate of 33 events/s, which the SSOT calls "not a viable waking operating point". `manifest()` now reports this on every run. Fit r_max and declare θ₀ and γ_sig.
- **F3.** The SSOT's TC-15 Appendix-A numbers (c −0.71 → +0.70, d′ 0.91 → 1.69) cannot be reproduced without the Appendix-A stimulus definition (amplitude, window, trial structure). The SSOT should state it; the fixture here records its own setup.
- **F4.** Registry `beta_DA` has value null, while the SSOT table gives default 0 (production now uses 0). Add the value with an evidence quote at the next extraction.
- **F5 (SSOT-P10).** The extension path still mixes the ODE and inverse-variance precisions under `use_hierarchical_precision_ode`, and resonance mode probably applies δ twice. This is registered as open. The default path is unaffected.

## Remaining tasks

### Next step (one at a time)

**Force-push the rewritten apgi-lean history** (F1), in a shell where the github-apgi key is loaded:
```powershell
cd C:\Claude\Projects\apgi-lake
git push --force-with-lease=main:2f4e562064a7a01de8a622f3a5775c01aa8b7b54 origin main
```
The lease refuses the push if anyone pushed to main after 2f4e562. Then confirm CI green on the new pins (B-15).

### Phase A remainder
**59.** Put SSOT-P10 under test (hierarchical precision mixing, resonance δ), then fix it in the legacy extension path.
**60 (new).** Rerun K7 and the gate results on 72ad050 as a versioned rerun (Phase A changed outputs).
**61 (new).** Record status and owner fields on every registry record (TC-01); report the clamped-step fraction per run (TC-10).

### Phase B remainder
**54b.** The derived and label parameter rows listed above; `beta_DA` value 0 (F4).
**62 (new).** TC-08 parameter recovery (TC-08a–g) and TC-20 timestep-refinement convergence; TC-04 trajectory test for apgi_core.full_model.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text:
- D1: author name and email.
- D2: source registry (remove the duplicate SRC-MATHSPEC row, add SRC-MATHSPEC-V12D and SRC-SSOT-V12D).
- D3: section numbers.
- D4: missing rows.
- D5: task 44.
- D6: legacy EQ IDs; the registry keeps EQ-PREC-1, THR-1, DECAY-1, UPD-1, EULER-1 and PIPE-1.
- D8: B-15 status.
- D10: regenerate the header and §24–§25 from the registry. They should read spec 0.5.0, the new hash, 119 theorems, 57 golden vectors in 14 families, 53 of 53 equations, CL-1…CL-31, and blockers B-05, B-10 and B-12 closed.
- D9 is done in the Math Spec draft.

**33 / B-13.** r_max and the operating point (F2).
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, plus the recovery readings.
**B-07.** Second-reader check of the hypothesis register.
**B-17.** Independent reviewers.
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.

### Phase D: next Zenodo release (v1.2)
**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing:
- re-hash every source;
- re-source EQ-CUSP-1, the task-53 and task-54 equations, τ_Π, α_Π and the 37 SSOT-sourced parameter rows to the published Math Spec and Notation Appendix;
- retire SRC-MATHSPEC-V12D and SRC-SSOT-V12D;
- re-run extraction;
- confirm 0 corpus defects;
- fill the tag and DOI in the release manifest (B-11).

## Rating (1–100) against the SSOT

- **Design 94** (was 92). The specification layer is now complete where the SSOT is complete: 53 of 53 equations, symbols, configurations, revisions and a Lean statement for every equation. Deductions: CFG-FULL cannot be counted until its extension parameters are frozen; the legacy extension path still holds a prohibited shortcut (P10); the operating point is undecided (B-13); the loop-gain condition and the Lyapunov conjecture are design heuristics, not derivations; registry records lack the SSOT record-status axis.
- **Implementation 84** (was 60). The default production path is the SSOT core and equals the reference implementation step for step (TC-04). All nine core divergences, PD-LOOP-GAIN and SSOT-V2 are fixed and guarded by tests; 119 machine-checked theorems; 57 golden vectors. Deductions: extension paths run v1.1 code (P10 open); apgi_core.model is a declared variant, not aligned; placeholder r_max and γ_sig; TC-08, TC-20, TC-25 and TC-26 not implemented; outputs computed before 72ad050 need a versioned rerun.
- **Release readiness 71** (was 61). Ten of 18 blockers are closed and the local verification chain is green. Deductions: CI has not yet run on the new pins and the rewritten history; B-07, B-13, B-14, B-16, B-17 and B-18 are author or external work; the SSOT document's own header and §24–§25 are stale (D10); the release tag and DOI do not exist yet. A perfect specification score would still not be a claim of scientific truth (SSOT §32).

---

## Routine after any registry edit

`verification\verify_all.ps1` runs all of it (extraction, generate_lean, lake build, consistency, release manifest, both pytest runs) and writes .verify.log. Manually:

```powershell
cd C:\Claude\Projects\apgi-lake
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\docs\apgi-v-1-2 --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
python verification\python\make_release_manifest.py
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

`generate_lean.py` hashes all nine registry files, including known-conflicts.json, so regenerate and rebuild after changing a production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM.
