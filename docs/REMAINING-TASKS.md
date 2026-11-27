# APGI verification: remaining tasks

State as of 2026-11-27 09:05 ET (round 70–71). Measured against **APGI Single Source of Truth (SSOT), framework v1.2** (docs/apgi-v-1-2/APGI-Single-Source-of-Truth.md, sha256 18951b65…, pinned as SRC-SSOT-V12D). Registry **spec 0.6.0**; the registry hash is written by `generate_lean.py` into Apgi/Spec.lean.

- Repositories, all `main` only:
  - apgi-lean: the previous round (6167b48) is on origin/main according to the local tracking ref (pushed outside this session; GitHub itself could not be queried from here, see F10). This round is three local commits on top of it (6d5c0f4 code and registry, 5858625 docs, and a follow-up that fixes the report line endings), **not pushed**: the github-apgi key is not loaded in this session's shells (`ssh -T git@github-apgi`: "Permission denied (publickey)"; the agent has no identities).
  - apgi-implementation: pin **72ad050** (unchanged). Two local commits, **not pushed**: e0e82cf (TC-13 / SSOT-P11 fix, previous round) and **d153f6a** (F11 portability fixes, this round).
  - apgi-validation: f6fec65 (unchanged).
- Local results (this PC, `verification\verify_all.ps1 -Impl .scratch\impl-pin`, production at the pin 72ad050, 08:45–09:01 ET): extraction 93 verified, 0 failed; `lake build --wfail` green (7248 jobs, 10 modules plus the generated Spec); consistency 0 open, 0 unacknowledged, 0 stale; recovery study regenerated (152 s, identical to the previous run); apgi-lean pytest **331 passed, 1 skipped, 4 xfailed**; test_production_validation.py 10 passed, 2 skipped.
- Rating against the SSOT (1–100, nine dimensions): **overall 87 → 88** this round. Reasons at the end of this file.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): **10 of 18** (unchanged): B-01, 02, 03, 04, 05, 06, 08, 10, 12, 15. Open: B-07, B-09 (derived and label rows of 54b), B-11 (tag and DOI), B-13, B-14, B-16, B-17, B-18.
- Conformance tests TC-01…TC-26: **18 pass**, **6 partial** (TC-01 approval pending; TC-04; TC-08, now with all four §17 diagnostics but two gate failures awaiting disposition; TC-10 production clamp fraction; TC-13 production overflow at the pin; TC-21), **2 not implemented** (TC-25, TC-26). Unchanged counts.
- Lean: **196 theorems in 10 modules** (was 187), every one axiom-pinned with `#guard_msgs`; 189 use exactly [propext, Classical.choice, Quot.sound], 7 a strict subset; no sorry, no admit, no axiom declaration.
- Equations: 59 of 59 with a Lean-backed statement.
- Claims: **46** (was 44): 41 proved, 2 assumed (CL-8, CL-46), 3 unresolved (CL-7, CL-26, CL-36).
- Requirements: 44 (33 pass, 6 partial, 3 open, 2 not implemented).

## Done this round (2026-11-27, tasks 70–71)

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
- **F10 (permissions)** unchanged in effect: no push is possible from this session's shells.
- F2 (operating point, B-13), F3 (TC-15 Appendix-A stimulus), F5 (SSOT-P10), F7 (memory), F8 (17-step loop rejected by SSOT §8), F9 / SSOT-P11 (fixed in e0e82cf, not pushed) are unchanged.

## Remaining tasks

### Next step (one at a time)

**Push both repositories** with the github-apgi key loaded (`ssh-add` the key, then `git -C C:\Claude\Projects\apgi-lake push origin main` and `git -C C:\Claude\Projects\apgi-implementation push origin main`), and confirm CI green on both heads; the pinned-production jobs of apgi-lean expect SSOT-P11 as a strict xfail, and apgi-implementation's CI now gets the pytensor fix.

Then **close SSOT-P11**: in apgi-lean set SSOT-P11 to `resolved` (move its `fix` text to `resolution`), set the production pin to d153f6a (it contains e0e82cf) in specification/known-conflicts.json and .github/workflows/lean_action_ci.yml, run `verification\verify_all.ps1` (default -Impl), commit, push, and confirm CI. REQ-TC-13 then passes.

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

Initial (start of this round, measured: 6167b48 with production at 72ad050, verify_all green, 312 passed) → final (this round, verified locally):
- Architecture 91 → 92: one canonical model now serves the Lean pipeline (TC-08g is a statement about `pipeStep`), the scalar reference and the vectorized study simulator, and the simulator is twin-checked against the reference. Deduction: the Lean pipeline is still not executed against the golden vectors.
- Mathematical correctness 93 → 93: 196 theorems, all axiom-pinned; the two new proofs planted-fault checked. Deduction unchanged: several structural theorems remain rfl-level encodings.
- Specification coverage 90 → 92: all four §17 diagnostics for TC-08d–g; TC-08g's exact part. Deductions: dispositions (71a), behavior-level recovery, L3–L4 qualitative, CFG-FULL undefined.
- Implementation 86 → 87: F11 fixed in production code (d153f6a). Deductions: nothing of it is pushed, so the pin still carries SSOT-P11; P10 and the clamp report are still open.
- Proof completeness 88 → 89: the TC-08g degeneracy on whole trajectories. Deductions: coupled Lyapunov conjecture, loop-gain derivation, cusp-to-pipeline link.
- Testing 92 → 94: 19 new tests, exact SBC with a non-vacuity check, out-of-sample prediction, five new planted faults caught. Deductions: TC-25, TC-26; behavior-level recovery.
- Reproducibility 89 → 89: the study is seeded, deterministic (two runs identical) and hash-bound to its design and code. Deduction: neither this round nor the previous one has a CI run observed from this session.
- Documentation 88 → 89: REMAINING-TASKS, VERIFICATION-REPORT, README, regenerated traceability and assumption inventory (CL-46 listed). Deduction: the SSOT's header and §24–§25 are stale (D10).
- Publication readiness 68 → 69: TC-08 now has every diagnostic §17 asks for, and the result is a concrete author decision (71a) rather than a gap. The release blockers B-07, B-13, B-14, B-16, B-17, B-18 and the tag and DOI are unchanged.
- **Overall 87 → 88.** A perfect specification score would still not be a claim of scientific truth (SSOT §32).

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
