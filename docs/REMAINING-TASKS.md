# APGI verification: remaining tasks

State as of 2026-11-27 00:00 ET. Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0** (was 0.5.0); the hash is written by `generate_lean.py` into Apgi/Spec.lean and by `make_release_manifest.py` into verification/reports/release-manifest.json.

- Repositories, all `main` only:
  - apgi-lean: this round is committed locally on top of fb0ad00 and **not pushed** (the github-apgi key is not loaded in this session's shells). fb0ad00 itself is on GitHub.
  - apgi-implementation: 72ad050, pinned in known-conflicts.json and CI (unchanged this round).
  - apgi-validation: f6fec65, pinned in known-conflicts.json and CI (unchanged this round).
- CI on fb0ad00 (GitHub Actions run 45931170311, 2026-11-27 02:55 UTC): **4 of 4 jobs green** (Lean, registry/Python, apgi-validation cross-check, report). B-15 closes on that evidence; the report artifact (7-of-7 criteria) needs GitHub sign-in to read and was not read.
- Local results (this PC, after this round): `lake build --wfail` green (**8 Lean modules** plus the generated Spec); `check_consistency.py` 0 open, 0 unacknowledged, 0 stale; extraction **93 records verified, 0 failed** (85 evidence-bearing parameters plus 8 bridge and observable records; beta_DA now has a value); apgi-lean pytest with APGI_IMPL_PATH **264 passed, 1 skipped** (was 237 / 1); test_production_validation.py 10 passed, 2 skipped. Final numbers are in docs/VERIFICATION-REPORT.md.
- Rating against the SSOT (1–100, nine dimensions): **overall 79 → 85**. Reasons at the end of this file and in docs/VERIFICATION-REPORT.md.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged count): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15; B-15 is now confirmed by CI on fb0ad00. Open: B-07, B-09 (only the derived and label rows of 54b remain), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26 (requirements.json, REQ-TC-*): **17 pass**, **6 partial** (TC-01 approval pending; TC-04; TC-10 production does not report the clamp fraction; TC-13; TC-19; TC-21), **3 not implemented** (TC-08, TC-25, TC-26). Was 16 / 6 / 4.
- Lean: **170 theorems in 8 modules** (was 119 in 5), every one axiom-pinned with `#guard_msgs`; 163 use exactly [propext, Classical.choice, Quot.sound], 7 use a strict subset; no sorry, no admit, no axiom declaration (checked by `check_consistency.axiom_check`, new).
- Equations: 59 of 59 with a Lean-backed statement (unchanged); every equation now carries record_status, status_basis, owner and approval_date.
- Claims: **39** (was 31): 35 proved, 1 assumed (CL-8), 3 unresolved (CL-7 hysteresis in human data, CL-26 coupled Lyapunov conjecture, CL-36 H10 ordering).
- Requirements: **44** in the new requirements.json (18 SSOT requirements plus TC-01…TC-26), each traced to Lean declarations and tests; docs/traceability-matrix.md and docs/assumption-inventory.md are generated from it and CI fails if they are stale.
- Bridges: **4 bridge and 4 observable records** in the new bridges.json, every quote verified against the pinned SSOT.

## Done this round (2026-11-27)

**Task 63: Apgi/Pipeline.lean, the full 15-step pipeline (27 theorems).** `pipeStep` composes steps 2–15 exactly as SSOT §8 and `apgi_ref.core_step`, over an abstract reference estimator, so every theorem holds for any estimator that is a function of past errors.
- Bounded-state invariants along every trajectory, for every input and draw sequence (`traj_inv`): Σ ≥ 0 in both channels, θ ≥ θ_floor, r ≥ 0, B_prev ∈ {0, 1}, and the unconditional lower bound S ≥ −m₀·(Π_max/Π̄ᵉ + Π_max/Π̄ⁱ). Precisions stay in [Π_min, Π_max] and |γ_NE|·g_NE ≤ 0.5 at every step (`traj_prec_mem_Icc`, `traj_ne_bound`).
- The upper bound on S is conditional on a bound on S_inst (`traj_S_le`), because z is unbounded for unbounded input. This is stated as a hypothesis, not hidden.
- The causal one-step lag (`pipeStep_decision_input_independent`): B_t and B(t) at t do not depend on the inputs at t.
- The hazard sampler realizes EQ-HAZARD-1: under a uniform draw on [0, 1], P(B(t) = 1) = 1 − exp(−r_max·B_t·dt) (`pipeLog_ignition_measure`, via Lebesgue measure).
- Full-step versions of TC-11 (`pipeStep_readout_noninterference`), TC-12 (`pipeStep_exactly_once`) and TC-17 (`pipeStep_reference_excludes_current`, `pipeLog_estimators_separate`, `pipeStep_variance_uses_preupdate_mean`).
- Admissibility (`PipeAdmissible`) is a structure of ten explicit hypotheses; `test_cfg_core_is_admissible` checks that CFG-CORE satisfies them.

**Task 64: the 17-step pipeline request.** SSOT §8 states that the proposed 17-step pipeline is **not adopted**, so it was not implemented. Instead it is proved non-equivalent to the canonical order: "ignition after accumulation" makes the decision strictly depend on the current drive (`decideAfterAccumulation_strictMono_drive`, `orders_differ`), and "statistics before standardization" shrinks z by (1 − α) (`standardize_after_update_shrinks`). The third feature, "threshold before ignition", is covered only by the canonical input-independence theorem.

**Task 65: Apgi/Strata.lean, L0–L4 (13 theorems).** Under scope decision (b): strata as definitions plus the SSOT's own statements about them.
- L0 lies outside the ignition model; exactly L1–L4 carry ignition dynamics.
- At τ₀ = 50 ms and k = 133: the SSOT table values, L1 at 6.65 s above its band [0.1, 3] s, L2 at 14.74 min below its integration window [25, 30] min but inside its operational band [1, 30] min. These retained limitations are now theorems.
- The level count is boundary-sensitive: five levels fit 50 ms–6 months at k = 133, not at k = 134.
- τ_Π,ℓ = max(1 s, τ_ℓ/10) meets dt₀ = 10 ms ≤ τ_Π/10 on every level.
- OSF H10 is the hypothesis `H10Ordering`, never proved; only its consequences are, and it constrains nothing at L0–L1.
- The §12.5 Lyapunov bound is proved only at loop gain 0 (`lyapunov_decoupled`). The coupled conjecture stays CL-26.

**Task 66: Apgi/Epistemic.lean and bridges.json (11 theorems).**
- Tier currencies over the unit dimensions. A quantity carrying AU is Tier 3 only. No constant free of AU⁻¹ moves it to Tier 1 or 2, so a Tier-3 bridge needs a registered calibration constant with an AU⁻¹ factor; units.json registers none. This does not decide whether the Tier-3 → Tier-2 bridge exists: it stays unresolved (BR-T3-T2).
- The registered κ calibration rule (OSF Table 13 H7, Table 17) as a decision procedure: one dataset never retires the bridge, the rule is inert without data, straddling intervals never count, and "bridge-consistent" excludes "retired". `apgi_ref.kappa_verdict` is the float twin.
- bridges.json (SSOT §29 "to add"): BR-T3-T2, BR-KAPPA-SYN, BR-LANDAUER, BR-SDT-DV and observables S, θ, B, Πⁱ. Each quotes the SSOT; `extract_sources.py` verifies the quotes; `check_consistency.py` fails on a record changed since extraction. A missing falsifier carries an SSOT-located reason; none is invented.

**Task 61 (TC-01, TC-10), done in part.**
- record_status, status_basis, owner and approval_date on every parameter, equation, claim, bridge and requirement, checked by `record_status_check`. Equation statuses follow the SSOT §9 module table and the CFG-CORE manifest (37 Canonical v1.2, 15 Extension, 5 Canonical v1.1, 1 Deprecated EQ-PREC-1, 1 Proposed EQ-ANT-1). Parameter statuses follow the revision of the cited source. CL-1…16 are Canonical v1.2 (in the SSOT claim register); CL-17…39 are Proposed until D10. **approval_date is null everywhere: the assignments await author approval (61a).**
- The reference reports the clamped-step fraction (`apgi_ref.clamp_report`, `run_core`). Production does not yet (61b).

**Task 62, done in part: TC-20 convergence** (test_convergence.py). Before the first ignition the pipeline is deterministic under deterministic input, so the discrete scheme's P(≥ 1 ignition) is exact; its weak error halves when dt halves (ratios in (1.6, 2.4)), decreases monotonically on the full pipeline, and is dt-invariant under constant propensity. TC-08 and the apgi_core.full_model trajectory test remain (62b).

**Task 67: requirement → proof traceability.** specification/requirements.json (44 records); `make_traceability.py` renders docs/traceability-matrix.md, docs/assumption-inventory.md and verification/reports/traceability.csv; `test_traceability.py` fails on stale output, so CI enforces it.

**54b / F4, done in part:** beta_DA now has value 0 with an SSOT quote verified by extraction, and test_default_dopamine_bias_is_zero reads it from the registry.

**Hygiene:**
- `find_quote.py` pointed at a non-existent apgi-v-1-2 folder; it now uses docs/apgi-v-1-2.
- The Hypothesis `too_slow` health check failed spuriously while lake build loaded the machine; it is suppressed (it measures wall-clock time, not correctness).
- verify_all.ps1 also regenerates the traceability files.
- README layout updated (Coverage, Pipeline, Strata, Epistemic, requirements, bridges); new docs/REPRODUCIBILITY.md and docs/VERIFICATION-REPORT.md.

**Audit evidence (mutation tests, this round).** Seven deliberate faults were each caught: deciding from the post-leak S, dropping the Πⁱ_eff clamp, the post-update mean in the variance, double retention, retiring κ on one dataset, per-step Bernoulli sampling (Python suite), and an edited bridge quote (extraction). An eighth, deciding from the post-leak S in Apgi/Pipeline.lean, made `lake build` fail. Details in docs/VERIFICATION-REPORT.md.

## Findings this round

- **F6 (CI workflow, owner Uxod).** The remote tools here cannot write .github/workflows (protected path). The prepared workflow adds the Python 3.11 / 3.12 matrix that SSOT §28.3 requires and a traceability `--check` step: `.scratch/lean_action_ci.proposed.yml` (git-ignored). Copy it over .github/workflows/lean_action_ci.yml and commit. The traceability check already runs in CI through test_traceability.py.
- **F7 (memory).** This PC had about 180 MB of free memory during the build (7.5 GB total). Pipeline.lean then takes about 95 s; an earlier attempt stalled with the compiler paging. Close other large applications before `lake build`.
- **F8 (17-step loop).** The request to formalize a 17-step loop conflicts with SSOT §8, which rejects it. Recorded as REQ-PIPE-17-REJECTED with the non-equivalence theorems.
- F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F5 (SSOT-P10) are unchanged.

## Remaining tasks

### Next step (one at a time)

**Push apgi-lean** in a shell where the github-apgi key is loaded, then confirm CI green on the new head:
```powershell
cd C:\Claude\Projects\apgi-lake
git push origin main
```

### Phase A remainder
**59.** Put SSOT-P10 under test (hierarchical precision mixing, resonance δ), then fix it in the legacy extension path (apgi-implementation).
**60.** Rerun K7 and the gate results on 72ad050 as a versioned rerun (Phase A changed outputs).
**61a (author).** Approve the derived record statuses (set approval_date) or correct them; review which parameter rows belong to Extension modules.
**61b.** Report the clamped-step fraction from production (`manifest()` or the run log), as apgi_ref.clamp_report does.
**F6 (author).** Install the prepared CI workflow (Python 3.11 / 3.12 matrix).

### Phase B remainder
**54b.** The remaining derived and label parameter rows: α_EMA and β_Σ (EQ-EMA-2), m_Ψ, K_ℓ / K_ℓm, τ_min / τ_max, R_L, α_psy,log, the guess rate g, the protocol seeds, κ_pop / κ_beh.
**62b.** TC-08 parameter recovery (TC-08a–g, the §17 gate) and a TC-04 trajectory test for apgi_core.full_model.
**68 (new).** TC-13: NaN/Inf rejection and overflow handling tests; TC-19: a distributional test across implementations.

### Phase C: author decisions and documents (Owner: Uxod)
**57. SSOT corrections**, all in the SSOT text: D1 author name and email; D2 source registry; D3 section numbers; D4 missing rows; D5 task 44; D6 legacy EQ IDs; D8 B-15 status (now closed on run 45931170311); D10 regenerate the header and §24–§25 from the registry: spec 0.6.0, 170 theorems in 8 modules, CL-1…CL-39, 57 golden vectors in 14 families, 59 equations, requirements.json and bridges.json added.
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

Initial (start of this round, fb0ad00) → final (this round, verified locally):
- Architecture 85 → 90: the whole pipeline is now one Lean function over an abstract estimator, with requirement and bridge registers beside the equation register. Deduction: the Lean pipeline is not executed against the golden vectors (ℝ is not computable); alignment rests on the Python twins.
- Mathematical correctness 90 → 92: 170 theorems, all axiom-pinned, mutation-checked. Deduction: several structural theorems are definitional (rfl) by design; they certify the encoding, not deep mathematics.
- Specification coverage 82 → 88: the pipeline, L0–L4, tiers and the κ rule are covered. Deductions: L3–L4 bands are qualitative in the SSOT; the five-axis classification is in records, not types; CFG-FULL is not defined.
- Implementation 84 → 85: the reference reports clamp fractions; production is unchanged (P10 open, placeholder operating point, no clamp report).
- Proof completeness 78 → 86: trajectory-level invariants and the sampler measure are proved. Deductions: the coupled Lyapunov conjecture and the loop-gain derivation stay open; no theorem links the cusp to the stochastic pipeline.
- Testing 85 → 89: 264 tests, convergence (TC-20), mutation checks. Deductions: TC-08, TC-25, TC-26 missing; TC-13 and TC-19 partial.
- Reproducibility 85 → 87: REPRODUCIBILITY.md, generated docs enforced in CI. Deductions: the 3.11 matrix needs F6; this round is not yet pushed or run in CI.
- Documentation 70 → 86: traceability matrix, assumption inventory, reproducibility guide, final report. Deduction: the SSOT's own header and §24–§25 are stale (D10).
- Publication readiness 63 → 66: unchanged blockers B-07, B-13, B-14, B-16, B-17, B-18 and the missing tag and DOI.
- **Overall 79 → 85.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

---

## Routine after any registry edit

`verification\verify_all.ps1` runs all of it (extraction, generate_lean, lake build, consistency, release manifest, traceability, both pytest runs) and writes .verify.log. Manually:

```powershell
cd C:\Claude\Projects\apgi-lake
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
