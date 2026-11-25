# APGI verification: remaining tasks

State as of 2026-11-25 17:45 ET. Measured against **APGI Single Source of Truth (SSOT), framework v1.2**. The registry is now **spec 0.4.0** (was 0.3.1, hash 3fc0faa0…); the new hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only: apgi-lean 4f717cd + **task-53 working tree, not yet committed** (see "Task 53" below); apgi-implementation a9b2878 (pinned); apgi-validation 07ca731 (pinned 811aee2).
- apgi-lean CI run 45603692681 at 4f717cd: 4 of 4 jobs green, 7 of 7 pilot criteria.
- Rating against the SSOT: design 92/100, implementation 60/100, overall release readiness 61/100 (was 91 / 60 / 58). Production code is unchanged, so the implementation score stays put. The verification layer can now see the whole production gap, which accounts for the gain.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): 7 of 18 (39%): B-01, 02, 03, 04, 06, 08, 15. B-09 has progressed but is still open.
- Conformance tests TC-01…TC-26: 7 pass (TC-02, 05, 06, 18, 22, 23, 24), 12 partial (TC-01, 10, 13, 19, 21; TC-07, 09, 11, 12, 17 pass on the reference loop but are strict xfails in production; TC-14, 15 pass on the reference loop only), 7 fail or not implemented (TC-03, 04, 08, 16, 20, 25, 26). 27% pass; 50% with partials at half weight (was 37%).
- SSOT equation IDs in `equations.json`: 22 of 53 (42%; was 10). New: EQ-EXCESS-1, PREC-REL-1, DRIVE-1, STD-1, EMA-1, EMA-2, PREC-2, THEFF-1, RESET-1, REF-1, FLOOR-1, STEP-1. The §13 order is registered as the pipeline rule EQ-PIPE-1 (`apgi_ref.core_step`).
- SSOT parameter rows in `parameters.json`: 42 of 73 (58%; was 35). New: m₀, Π_min/Π_max, ε_stab, T_window (5 s / 10 s), g_NE, γ_NE (no default sign), β_5HT. Extraction: 48 of 48 verified against the pinned sources.
- Theorem register: 41 of 41, axioms pinned (100%). Claim register: 16 of 16 (100%). No new Lean theorems yet; the EQ-DRIVE-1 theorem is task 55.
- Golden vectors: 25 in 6 families; required new families (B-10): 0 of 8.
- Prohibited-shortcut checks (SSOT §13): apgi-implementation 3 of 7 met, apgi_core 3 of 7. The unmet 4 are now strict xfails rather than findings in prose.
- Production divergences under strict xfail: 9 in apgi-implementation (SSOT-P1…P9, 18 tests) and 2 in apgi_core (SSOT-V1, V2, 4 tests). PD-LOOP-GAIN is still open.
- SSOT worked numbers recomputed: 31 of 31 correct. The soft floors are now also fixtures (test_core.py).

## Task 53: done in the working tree, verification pending

The connection to the PC dropped during `lake build --wfail`. All of the following is saved on disk in C:\Claude\Projects\apgi-lake but is **not committed or pushed**.

- `apgi_ref.py`: reference functions for the SSOT minimal core (excess, prec_rel, drive, standardize, ema_alpha/ema_update, theta_eff, reset, refractory_step, step_rule, operating_point) and `core_step`/`core_state`, the canonical 15-step pipeline. The reference windows (sliding window) and the precision EMA are separate estimators, as EQ-STD-1 requires.
- `test_core.py` (new, 23 tests): TC-07 null operating point, TC-09 sign symmetry, drive monotone in Π_rel exactly where |z| ≥ m₀, TC-11 read-out, TC-12 exactly once, TC-17 estimator ordering, the decision taken from the existing S, the hazard, R1 soft-floor values, and CORE_DEFAULTS checked against the registry.
- `equations.json`: 13 new entries. The dt ≤ min(τ)/10 preconditions moved from EQ-EULER-1 to EQ-STEP-1.
- `parameters.json`: 9 new parameters; spec_version 0.4.0.
- `known-conflicts.json`: SSOT-P1…P9 and SSOT-V1, V2 as open divergences, each with its tests and the task that closes it. There is also a new corpus pattern, KC-GAMMA-NE-SIGN, with seeded and clean fixtures.
- `test_production.py`: `test_pipeline_importable` (a hard guard, so an import error cannot pass as an xfail) plus 18 behavioural strict xfails on `pipeline.APGIPipeline`. Each test isolates its own divergence: fixing SSOT-Pn alone flips only the SSOT-Pn tests.
- `test_production_validation.py`: 4 strict xfails (SSOT-V1, V2).
- CI: the python job installs structlog, pydantic and scipy so the pipeline imports.
- `find_quote.py` (new helper): locates and checks evidence quotes in a pinned source.

Local results before the drop:
- `check_consistency.py`: 0 open, 0 unacknowledged, 0 stale.
- `test_core`, `test_equations`, `test_conflicts`, `test_twins` and `test_golden_vectors`: 123 passed. test_conflicts ran before the KC-GAMMA-NE-SIGN fixture lines were added, so rerun it.
- `test_production.py` (APGI_IMPL_PATH): 18 passed, 18 xfailed.
- `test_production_validation.py` (APGI_VALIDATION_PATH): 7 passed, 4 xfailed.
- Not yet run: `lake build --wfail` on the regenerated Spec.lean, the full pytest, commit and push.

To finish 53 (one sitting):
```powershell
cd C:\Claude\Projects\apgi-lake
lake build --wfail
python verification\python\check_consistency.py
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"; python -m pytest -q -rxs; Remove-Item Env:APGI_IMPL_PATH
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-validation"; python -m pytest -q -rxs test_production_validation.py; Remove-Item Env:APGI_VALIDATION_PATH
cd ..\..
git add -A; git commit -m "Task 53: register the SSOT minimal core and the production gap (SSOT-P1..P9, V1, V2)"; git push origin main
```
Locally, `pip install "structlog>=24.1.0,<26.0"` is already done on this PC.

## New findings (task-53 audit)

- **SSOT-P8.** Production uses α_EMA = 0.05 at dt = 10 ms, a 0.195 s horizon. EQ-EMA-2 with the 5 s / 10 s windows gives 0.0020 and 0.0010.
- **SSOT-P9.** Production defaults β_DA to 1.15; the SSOT default is 0.
- **SSOT-P2, sharper.** Besides sharing one estimator, production computes Π from the variance after ε(t) has entered it. SSOT step 4 uses Σ(t).
- **SSOT-P10 (read, not yet under test).** With `use_hierarchical_precision_ode`, the aggregate S_inst uses the ODE precisions, but `update_signal_ode` integrates S with the inverse-variance Πᵉ_eff and Πⁱ_eff. That puts two precision definitions in one simulation, which the SSOT prohibits. Resonance mode applies δ on the resonance θ and again through `apply_refractory_boost`; double application is likely but not yet confirmed.
- **SSOT-D9.** The v1.2 Math Spec draft still says "γ_NE … default > 0" (Table 1) and "In the default parameterization (γ_NE > 0)" (§4.4). SSOT R6 sets no default sign. Corpus pattern KC-GAMMA-NE-SIGN now flags both lines.
- **SSOT-D10.** The SSOT header cites "specification 0.3.1 · registry hash 3fc0faa0…". After task 53 the registry is 0.4.0 with a new hash, so the header must be regenerated from the registry (SSOT §29 generation flow).

## Audit findings carried forward (2026-11-25)

### Production does not implement the SSOT minimal core
SSOT-P1…P7, V1 and V2 as audited. They are now registered as divergences with strict xfails (see known-conflicts.json for where each lives and its test names). "Met" is unchanged: hazard sampling when stochastic; strict S > θ in the hard limit; θ floor 0; precision clamp [0.1, 10]; ρ_retain applied once on the default path; dt = 10 ms.

### Registry and Lean against the SSOT
- **SSOT-R1 (partly fixed).** 31 SSOT equation IDs and 31 parameter rows are still missing. Still missing: g_ACh, η_pred, c₁–c₃, τ_ref, δ_ref, γ_ψ, τ₀, k, u₀, a, κ_up, κ_down and others.
- **SSOT-R2.** `ignites_monotone_precision` (EQ-PREC-1) covers only the uncentered drive. EQ-DRIVE-1 now carries that note and a Python twin of the target statement. The Lean theorem is task 55.
- **SSOT-R3.** ρ_retain canonical [0.1, 0.5]; C_down·τ_Π and C_up·τ_Π gains; τ_Π = max(1 s, τ_ℓ/10) per level. Still not in the registry.

### Defects in the SSOT document itself
D1–D8 as before. D9 and D10 are new (see above). D8 (B-15 status) is still open in the SSOT text.

---

## Next step (one at a time)

**53-close.** Run the five commands above, then commit and push. No production behavior changes. About 15 minutes.

## Phase A: Align production with the SSOT core (after 53)

Each task closes its SSOT-P* xfails. When one flips to XPASS, mark that divergence resolved in the same commit.

**45.** Π_rel·|z|_ex as the default drive; Ψ opt-in as |Ψ(z)|_ex. Closes SSOT-P1.
**46.** Separate reference statistics (5 s / 10 s windows that exclude ε_t) from the precision EMA; Π from Σ(t); α_EMA from T_window. Closes SSOT-P2 and P8.
**47.** Exact leak as the default accumulator; SDE as a declared extension; S never overwritten by log1p. Closes SSOT-P3.
**48.** Reorder `step` to SSOT §13; δ_reset only inside EQ-ALLO-1. Closes SSOT-P4.
**49.** θ_eff as a read-out value; nothing written back to θ. Closes SSOT-P5.
**50.** NE clamp for either sign; γ_NE default 0. Closes SSOT-P6.
**51.** Defaults θ₀ = 0.35, hazard sampling, β_DA = 0; `manifest()` reports `gamma_sig_theta0`, `propensity_floor` and `baseline_rate`. Closes SSOT-P7 and P9.
**52.** apgi_core: align `full_model.py` (closes SSOT-V2); label `model.py` the energy-form variant and resolve SSOT-V1 as "declared variant".
**59 (new).** Put SSOT-P10 under test (hierarchical precision mixing, resonance δ), then fix it.

Phase A changes model outputs: K7 and gate results need a versioned rerun (SSOT §13, last paragraph).

## Phase B: Registry completeness (B-09, B-05, B-10)

**54.** Register the remaining 31 equation IDs and 31 parameter rows; add symbols.json, configurations.json (CFG-CORE, CFG-CORE-R, CFG-FULL with counted parameters; `apgi_ref.CORE_DEFAULTS` is the CFG-CORE seed) and revisions.json (R1–R18). Fixes SSOT-R1, R3.
**55.** Lean: EQ-DRIVE-1 is monotone in Π_rel iff |z| ≥ m₀ (the twin test already exists). Then the SSOT "next targets": the hard-threshold limit, the m₀ identity, read-out non-interference, the exactly-once reset, and the folds of EQ-CUSP-2. Fixes SSOT-R2.
**56.** Golden-vector families: hazardProb, leakStep, neClamp, thresholdStep, Ψ, precEff, EMA ordering, plus seeded CFG-CORE and CFG-CORE-R trajectories from `core_step`. Add a quantitative TC-15 d′/c fixture (B-10).

## Phase C: Author decisions and documents (Owner: Uxod)

**57. SSOT corrections.** D1–D10:
- D1: author name and email.
- D2: source registry (remove the duplicate entry, add SRC-MATHSPEC-V12D, pin the four new sources).
- D3: number the sections or drop the § references.
- D4: mark the missing rows.
- D5: task 44.
- D6: map or retire the five legacy EQ IDs.
- D8: close B-15.
- D9: remove "default > 0" for γ_NE from the v1.2 Math Spec draft. Then re-hash SRC-MATHSPEC-V12D and re-run extraction.
- D10: regenerate the header after 53 is committed.

**58. Licenses (B-11).** Add LICENSE files to apgi-lean and apgi-validation; record all three in the release manifest.
**35. PD-LOOP-GAIN (B-12).** Either τ_Π in [1, 7.07) s at the current couplings, or couplings scaled to the Paper 3 gains.
**33. r_max and the operating point (B-13).** No default in [2, 7.5] reaches a floor ≤ 0.05 at θ₀ = 0.35. Fit r_max and declare θ₀ and γ_sig.
**B-14.** OSF Amendment 2: R4 before P0, R10 before P1 steepness, R8 before P4, plus the recovery readings.
**B-07.** Second-reader check of the hypothesis register.
**B-17.** Independent reviewers.
**B-18.** Add Naccache et al. (2025); Crossref-verify all DOIs.
**2.** ssh-agent, so pushes from this PC work.

## Phase D: Next Zenodo release (v1.2)

**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it.
**23.** The v1.1 PDFs are still named "Version 1.0"; drop the duplicate companion PDF.
**44.** §7.7 θ̃ wording (also SSOT-D5).
**25.** After publishing: re-hash every source; re-source EQ-CUSP-1, the task-53 equations, τ_Π and α_Π to the published Math Spec; retire SRC-MATHSPEC-V12D; re-run extraction; confirm 0 corpus defects.

## Done before this audit (2026-11-24 / 25)

Tasks 1, 3, 34, 36–39, 43; first half of 35. PV-* resolved and merged (apgi-validation 811aee2); production pin a9b2878; loop-gain form canonical and τ_Π = max(1 s, τ_ℓ/10) in the v1.2 Paper 2/3 drafts; CI 7 of 7. Details in the git history of this file.

---

## Routine after any registry edit

```powershell
cd C:\Claude\Projects\apgi-lake
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\apgi-v-1-2 --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"   # main contains the pinned commit; check it out exactly if main moves on
python -m pytest -q -rxs
Remove-Item Env:APGI_IMPL_PATH   # the validation module refuses to run with both packages on sys.path
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-validation"   # main contains the pinned commit; check it out exactly if main moves on
python -m pytest -q -rxs test_production_validation.py
Remove-Item Env:APGI_VALIDATION_PATH
cd ..\..
git add -A
git commit
git push origin main
```

`generate_lean.py` also hashes known-conflicts.json, so regenerate and rebuild after changing the production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction. To find an evidence quote, run `python verification\python\find_quote.py SRC-ID "regex"`; to check one, run `python verification\python\find_quote.py SRC-ID --check "quote" PAGE`.
