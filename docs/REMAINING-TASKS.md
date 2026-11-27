# APGI verification: remaining tasks

State as of 2026-11-27 07:30 ET (round 68–69). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0**; the registry hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only:
  - apgi-lean: the previous round (4de14fa, including the Python 3.11 / 3.12 CI matrix, F6) **is on GitHub**; CI run 45988035558 is green on all 5 jobs. This round is three local commits on top of it (a1a7562 code and registry, 0dbd85c verify_all.ps1, and the docs commit) and is **not pushed**: `git push` failed with "Permission denied (publickey)" (the github-apgi key is not loaded in this session's shells).
  - apgi-implementation: pin **72ad050** (unchanged). The TC-13 fix **e0e82cf is committed locally and not pushed**: the push was not permitted from this session (F10). SSOT-P11 stays open, as a strict xfail against the pin.
  - apgi-validation: f6fec65 (unchanged).
- Local results (this PC, `verification\verify_all.ps1 -Impl .scratch\impl-pin`, production at the pin 72ad050): extraction 93 verified, 0 failed; `lake build --wfail` green (**10 Lean modules** plus the generated Spec); consistency 0 open, 0 unacknowledged, 0 stale; apgi-lean pytest **see docs/VERIFICATION-REPORT.md §2**; test_production_validation.py 10 passed, 2 skipped. Against apgi-implementation e0e82cf the four SSOT-P11 tests pass (XPASS(strict)), which is the evidence for the fix.
- Rating against the SSOT (1–100, nine dimensions): **overall 85 → 87** this round. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (derived and label rows of 54b), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **18 pass**, **6 partial** (TC-01 approval pending; TC-04; TC-08; TC-10 production clamp fraction; TC-13 production overflow at the pin; TC-21), **2 not implemented** (TC-25, TC-26). Was 17 / 6 / 3: TC-19 now passes, TC-08 moved from not implemented to partial.
- Lean: **187 theorems in 10 modules** (was 170 in 8), every one axiom-pinned with `#guard_msgs`; 180 use exactly [propext, Classical.choice, Quot.sound], 7 a strict subset; no sorry, no admit, no axiom declaration.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: **44** (was 39): 40 proved, 1 assumed (CL-8), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (33 pass, 6 partial, 3 open, 2 not implemented).

## Done this round (2026-11-27, tasks 68–69)

**Task 68a: TC-13 stability (partial → still partial, only the production pin is missing).**
- *Division by zero is excluded by proof* (Apgi/Stability.lean): along every trajectory, σ_ref + ε_stab and Σ + ε_stab are positive in both channels (`traj_denoms_pos`, CL-40), given ε_stab > 0 and a nonnegative reference spread (`RefEstimator.SdNonneg`).
- *Finite amplification, quantified*: |z| ≤ |ε − μ_ref|/ε_stab (`standardize_abs_le`), 1/(Σ + ε_stab) ≤ 1/ε_stab (`precRaw_le`), and the explicit drive bound S_inst ≤ Π_max/Π̄ᵉ·|εᵉ − μᵉ_ref|/ε_stab + Π_max/Π̄ⁱ·(|εⁱ − μⁱ_ref|/ε_stab + |β_DA|) (`pipeLog_Sinst_le`); with the unconditional floor, S ∈ [L, U] on every trajectory whose errors keep the bound at most U (`traj_S_mem_Icc`, CL-41). The factor Π_max/(Π̄·ε_stab) = 10⁹ at CFG-CORE is why float64 overflow is reachable.
- *EQ-STEP-1 bounds every per-step gain*: dt ≤ τ/10 ⇒ 1 − exp(−dt/τ) ≤ 1/10, for λ and α_EMA (`stepRule_gain_le`, CL-42).
- *Defined handling in the reference* (apgi_ref.core_step): NaN/Inf/non-numeric inputs raise NonFiniteInputError before any computation; a step that would overflow, by `**` (raises) or silently by `*`, `/` (inf), raises NonFiniteStateError (an OverflowError); the input state is never mutated. test_stability.py (25 tests, including a Hypothesis twin of the drive bound).
- *Production*: NaN/Inf were already rejected atomically. **New finding SSOT-P11**: at 72ad050 an overflowing input raised OverflowError after mutating μₑ, the RNG draw and r/t_ep (non-atomic), and a silent inf was accepted into the state. Fixed in apgi-implementation **e0e82cf** (local): `core/ssot_core.step` computes steps 2–15 into locals, commits only a finite state, and restores the RNG on rejection; `core.finite.NonFiniteStateError`; tests/test_ssot_core_stability.py (10 tests; the overflow tests fail on 72ad050 and pass on e0e82cf). The production suite at e0e82cf: 2842 passed, 8 skipped, 6 failed, and the same 6 fail on a clean 72ad050 (F11).
- Cross-implementation: production and apgi_ref classify inputs from 1 to 10³⁰⁰ identically (accept with equal S, or reject as overflow) at the pin.

**Task 69: TC-08 identifiability and the §17 recovery gate (not implemented → partial).**
- Apgi/Identifiability.lean (10 theorems): TC-08a common offset (`ignitionProb_shift`, `hazardLik_shift`); TC-08c joint scale S′ = aS + b, θ′ = aθ + b, γ′ = γ/a on the propensity path and on the Bernoulli likelihood of any event sequence (`propensity_path_rescale`, `hazardLik_rescale`), with non-injectivity stated (`hazardLik_not_injective`, CL-43); TC-08b with γ_NE = 0, g_NE, β_SM, M̂ enter the **whole pipeline** only through g_NE·exp(β_SM·M̂) (`pipeStep_gain_product`, `traj_gain_product`, `gain_product_not_injective`, CL-44).
- test_recovery.py: the §17 gate on synthetic data for θ_eff and γ_sig of EQ-IGN-2 → EQ-HAZARD-1 → EQ-OBS-1/2, S anchored, scale fixed, truths drawn from the registered ranges (θ₀ [0.25, 0.85] AU, γ_sig [2, 7.5]), 60 synthetic subjects, 16 levels × 60 trials: **θ_eff r = 0.985, median range-scaled error 0.039; γ_sig r = 0.953, error 0.061** (targets r > 0.85 from r_HIGH, error < 0.20 from err_gate). The gate is shown not to be vacuous (it fails with 2 trials per level) and the scale anchor is shown necessary (a free scale leaves the likelihood flat). Float64 twins of TC-08a–c.
- Not covered: TC-08d–g (declared posterior trade-offs) and recovery of η_θ, τ_θ, c₁, v₁, v₂ from behavior (task 62b). The design constants (levels, trials, r_max·T_W = 3, guess 0.02, lapse 0.02) are synthetic-study choices, not registered values.

**Task 68b: TC-19 stochastic reproducibility (partial → pass).** Production samples from numpy PCG64 (`default_rng`), seeded runs reproduce exactly; the distributional test compares 200 production runs (PCG64 streams) with 200 reference runs (Philox streams), both spawned from one SeedSequence, on ignition counts and first-ignition times (Welch |z| < 4, two-sample KS at α = 0.001), with a built-in power check: a 1.5× hazard rate is detected. apgi_core is a declared variant (SSOT-V1) and is not compared; cross-platform equality is not claimed.

**Hygiene.** verify_all.ps1 takes `-Impl` (a checkout at the pin; .scratch\impl-pin is a git worktree of apgi-implementation at 72ad050) and logs the production commit it tested. README lists the two new modules. The previous report's "170 theorems" is confirmed (187 now).

**Audit evidence (mutation tests, this round; .scratch\r68\mut\mutate.py).** Six faults, planted one at a time and restored, were all caught:
1. apgi_ref.core_step without the input finiteness check: 12 of 25 test_stability.py tests fail.
2. apgi_ref.core_step without the post-step finiteness check: `test_silent_float_overflow_is_rejected` fails (DID NOT RAISE). The `**` path alone would have hidden this; the silent `*`/`/` test was added for it.
3. The recovery design cut to 2 trials per level: both gate tests fail (γ_sig r = 0.248, error 0.562), so the gate is not vacuous.
4. The observation model without the hazard (P(hit) = Bₜ): `test_vectorized_model_matches_reference` fails.
5. Apgi/Identifiability.lean with γ′ = γ·a instead of γ/a: the proof fails and every dependent axiom pin reports sorryAx.
6. Apgi/Stability.lean with ε_stab ≥ 0 instead of > 0: `traj_denoms_pos` fails (linarith), so the hypothesis is necessary.
The SSOT-P11 tests were also run against both production commits: they fail on 72ad050 (wrong exception type, mutated state, a silent inf accepted) and pass on e0e82cf.

## Findings this round

- **F9 / SSOT-P11 (production, P1).** Overflow was not atomic in core/ssot_core.py (above). Fixed in e0e82cf, not yet pushed.
- **F10 (permissions).** Pushing apgi-implementation from this session was refused by the tool permission layer. Owner Uxod: push e0e82cf (`git -C C:\Claude\Projects\apgi-implementation push origin main`), then close SSOT-P11 (next step below).
- **F11 (production test environment).** On this PC the apgi-implementation suite has 6 failures that also occur on a clean 72ad050: 5 in tests/test_estimation_pymc.py (pytensor DeprecationWarning raised as an error) and test_examples_16_figures_import_smoke (cp1252 decode; passes with PYTHONUTF8=1). They are environment issues, not regressions; owner Uxod to pin pytensor or set PYTHONUTF8 in that repository's CI.
- F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F5 (SSOT-P10), F7 (memory), F8 (17-step loop rejected by SSOT §8) are unchanged. F6 is closed (4de14fa).

## Remaining tasks

### Next step (one at a time)

**Push apgi-lean** (`git -C C:\Claude\Projects\apgi-lake push origin main` with the github-apgi key loaded) and confirm CI green on the new head; the pinned-production jobs expect SSOT-P11 as a strict xfail.

Then **close SSOT-P11**: push apgi-implementation e0e82cf; then in apgi-lean set SSOT-P11 to `resolved` (move its `fix` text to `resolution`), set the production pin to e0e82cf in specification/known-conflicts.json and .github/workflows/lean_action_ci.yml, run `verification\verify_all.ps1` (default -Impl), commit, push, and confirm CI. REQ-TC-13 then passes.

### Phase A remainder
**59.** Put SSOT-P10 under test (hierarchical precision mixing, resonance δ), then fix it in the legacy extension path (apgi-implementation).
**60.** Rerun K7 and the gate results on 72ad050 as a versioned rerun (Phase A changed outputs).
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules.
**61b.** Report the clamped-step fraction from production (`manifest()` or the run log), as apgi_ref.clamp_report does.

### Phase B remainder
**54b.** The remaining derived and label parameter rows: α_EMA and β_Σ (EQ-EMA-2), m_Ψ, K_ℓ / K_ℓm, τ_min / τ_max, R_L, α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh.
**62b.** TC-08d–g (posterior correlations, profile likelihood, simulation-based calibration, out-of-sample prediction) and recovery of η_θ, τ_θ, c₁, v₁, v₂ from full-pipeline fits; a TC-04 trajectory test for apgi_core.full_model.
**70 (new).** Register the recovery-study design constants (guess rate g with 54b, r_max·T_W once B-13 fixes r_max) so test_recovery.py reads them from the registry.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status (now closed on run 45931170311); D10 regenerate the header and §24–§25 from the registry: spec 0.6.0, 187 theorems in 10 modules, CL-1…CL-44, 57 golden vectors in 14 families, 59 equations, requirements.json and bridges.json added.
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

Initial (start of this round, 4de14fa) → final (this round, verified locally):
- Architecture 90 → 91: TC-13 and TC-08 are separate modules over the same `pipeStep`; reference and production now share one atomic-step contract (compute, check, commit). Deduction: the Lean pipeline is still not executed against the golden vectors.
- Mathematical correctness 92 → 93: 187 theorems, all axiom-pinned, two new ones planted-fault checked. TC-08b is a whole-trajectory statement, not a definitional unfolding. Deduction: several structural theorems remain rfl-level encodings.
- Specification coverage 88 → 90: TC-08a–c, division by zero, the drive bound, the step-rule gain, TC-19. Deductions: TC-08d–g; L3–L4 qualitative; CFG-FULL undefined.
- Implementation 85 → 86: reference TC-13 handling; production fix written and tested (e0e82cf) but not pushed, so the pin still carries SSOT-P11. P10 and the clamp report are still open.
- Proof completeness 86 → 88: no-division-by-zero and two-sided boundedness on every trajectory; the likelihood degeneracies. Deductions: coupled Lyapunov conjecture, loop-gain derivation, cusp-to-pipeline link.
- Testing 89 → 92: §17 recovery gate with a non-vacuity check, TC-13 for both implementations including silent overflow, TC-19 with a power check; 6 new planted faults caught. Deductions: TC-25, TC-26; TC-08d–g.
- Reproducibility 89 → 89: verify_all.ps1 -Impl makes the pinned-production run explicit. Deduction: this round's CI run is pending the push.
- Documentation 85 → 88: REMAINING-TASKS, VERIFICATION-REPORT, README, regenerated traceability and assumption inventory. Deduction: the SSOT's header and §24–§25 are stale (D10).
- Publication readiness 66 → 68: TC-19 passes and TC-08 is partly met; the release blockers B-07, B-13, B-14, B-16, B-17, B-18 and the tag and DOI are unchanged.
- **Overall 85 → 87.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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

`generate_lean.py` hashes all eleven registry files (now including bridges.json and requirements.json), so regenerate and rebuild after changing a production pin. If `check_consistency.py` reports `extraction_unverified` or `bridge_unverified`, a registry value or bridge record changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`. A `declared_variant` divergence needs `module` and `model_form` fields, and the module must export that MODEL_FORM. New Lean theorems need an equation link in equations.json and a `#guard_msgs` axiom pin; `axiom_check` rejects any axiom outside [propext, Classical.choice, Quot.sound].
