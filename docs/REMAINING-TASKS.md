# APGI verification: remaining tasks

State as of 2026-11-24 08:30 ET.

- Repository: https://github.com/apgiframework/apgi-lean. Local checkout: `C:\Claude\Projects\apgi-lake`.
- GitHub `main` is at 1c5e03d, which contains the merged registry work. Local `main` has one more commit, the one that adds this file, and it is **not yet pushed**.
- `corpus-v1-registry` was fast-forwarded into `main` and deleted. `main` is the only branch, locally and on GitHub.
- Local results: `lake build --wfail` passes, 14 of 14 theorems pass the axiom audit, pytest gives 81 passed and 5 xfailed, the consistency check finds 1 open item, and 20 of 20 parameters are verified against the pinned PDFs.
- CI run #3 on 1c5e03d: Lean, Python and Report jobs all green.
- Pilot criteria: 6 of 7 expected (confirm in task 4). Criterion 1 is the only one left.

Tasks are listed in the order to do them. Later tasks depend on earlier ones where noted.

---

## Phase 1: Today (publish and confirm)

**1. Push `main` (the commit that adds this file).** Owner: Uxod.
HTTPS uses the stored login `lesoto`, which has no write access to `apgiframework/apgi-lean` (403). Use the apgiframework SSH key and enter its passphrase:
```powershell
cd C:\Claude\Projects\apgi-lake
git push origin main
```
Done when `origin/main` matches local `main`.

**2. Optional: make future pushes work without a manual terminal.** Owner: Uxod. Pick one:
- Start the agent once from an admin PowerShell: `Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent; ssh-add $HOME\.ssh\id_ed25519_apgi`
- Or give the `lesoto` account write access to `apgiframework/apgi-lean`.

**3. Confirm CI.** Owner: either.
Run #3 (1c5e03d) already passed all three jobs on 2026-11-24, including the first CI run of the production cross-check. Your push in task 1 starts run #4 under Actions → "APGI verification"; all three jobs should be green again.
- The Python job now also checks out `apgi-implementation` at a106d98. Expect 81 passed and 5 xfailed. The `-rxs` flag lists the five PD divergences.
- If a job fails, copy its first error line into the next session.

**4. Read the report on the run's Summary tab.** Owner: either.
Expect 6 of 7 criteria. Criterion 1 should fail only on "no sha256 for SRC-INNOV-GDOC".

**5. Local cleanup.** Owner: either. Everything below is git-ignored or temporary, so nothing tracked is affected.
- In `apgi-lake`, delete `Claude outputs\`, `build.err`, `build.log`, `cache-get.log` and `.lake.mac-backup\`. The last one is a full second copy of Mathlib, several GB.
- Delete `%TEMP%\apgi-corpus\` and the `%TEMP%\apgi-*.py` scratch scripts.
- Keep `C:\Claude\Projects\apgi-implementation` (checked out at a106d98) while you still run `test_production.py` locally.

---

## Phase 2: This week (close the pilot, criterion 1)

**6. Find the "APGI Innovations" draft.** Owner: Uxod.
It is the only remaining source for the cusp potential (EQ-CUSP-1). A Drive search for that title on 2026-11-24 found nothing. It may have been renamed or may sit in another account.

**7. Decide what happens to it (A or B).** Owner: Uxod.
- **A. Pin it.** Export it to PDF or DOCX and store the file outside the repo. Run `python verification/python/extract_sources.py --hash <file>`. Paste the sha256 and revision into `SRC-INNOV-GDOC` in `specification/source-manifest.json`. Never commit the file, because the repo is public.
- **B. Publish it.** Move V(x) = x⁴/4 + a·x²/2 + θ·x into the next Zenodo release (Math Spec or Dynamical Formulation). Re-source EQ-CUSP-1 to that document and retire `SRC-INNOV-GDOC`. B is cleaner, because CL-4 and CL-5 would then rest on published text. It waits for the v1.2 release (tasks 21–25).

**8. Scan the draft for the old defects.** Owner: either. Needs task 6.
Run `python verification/python/extract_sources.py <draft file>`. The published corpus is clean of these, so any remaining copies live in the draft:
- Landauer 2.87 × 10⁻²¹ J
- the −θₜ·x cusp sign
- κ in mol ATP/bit
- κ as a spectral radius
- α as an update gain
- λ_θ
- Pred 0.B BF₁₀ ≥ 10

Fix each hit in the draft.

**9. Resolve KC-UNPINNED.** Owner: either. Needs task 7.
Set its status to `resolved` in `specification/known-conflicts.json`, then run the routine at the end of this file. Done when the CI report shows 7 of 7.

**10. Re-rate the pilot.** Owner: either. Needs task 9.
Update "Final assessment" in `verification-instructions.txt` and tick the last open checklist item.

---

## Phase 3: Decision

**11. Decide the scope of further Lean work.** Owner: Uxod.
The evidence is in `verification-instructions.txt`, section 9. Lean found 1 defect on its own; extraction and the production check found 14. The options:
- (a) Stop at the pilot.
- (b) Add targeted theorems only (tasks 26–28).
- (c) Full L0–L4. The defect yield does not support this.

Record the decision and the reason in `verification-instructions.txt`.

---

## Phase 4: Registry completion (C17)

This phase comes before the production fixes, because PD-HAZARD needs r_max registered.

**12. Register the remaining canonical parameters, each with page-cited evidence quotes.** Owner: either.
r_max, δ_reset, ρ_retain ∈ [0, 1], the NE clamp |γ_NE|·g_NE ≤ 0.5, τ_Π, τ_res, α_Π, C_down and C_up, γ⁺ and γ⁻ ∈ [1, 5], β_DA, c_θ, v₁ and v₂, M̂(c,a), Ψ(z), and the Πⁱ_eff = Πⁱ_baseline·exp(β_SM·M̂) form.

**13. Register the missing equations.** Owner: either.
- Leaky integrator, λ = 1 − exp(−dt/τ_S) (Math Spec Eq. 23–24)
- Hazard ignition, 1 − exp(−r_max·Bₜ·dt)
- NE sub-dominance clamp
- Allostatic update (Eq. 26)

**14. Extend the dt precondition to τ_Π and τ_res.** Owner: either. Needs task 12.
The full rule is dt ≤ min(τ)/10. Today it is checked only against τ_S and τ_θ.

---

## Phase 5: Production code (`apgiframework/apgi-implementation`)

Make each fix in `apgi-implementation` first, then do task 20 in `apgi-lean`.

**15. PD-FLOOR.** In `core/allostatic.py`, change the `update_threshold_euler` default `theta_min=0.1` to `0.0`. This is the smallest change and a good first PR.

**16. PD-KAPPA-SYMBOL.** Rename config `kappa` (the per-step decay exponent) and the `threshold_decay(kappa=…)` argument, and deprecate `kappa_meta`. Keep the old names as aliases that raise a `DeprecationWarning` for one release.

**17. PD-DT and PD-TAU-THETA, done together because they are coupled.**
- Set `dt` to 0.01 s (dt₀) and τ_θ to 20 s.
- Compute the decay exponent as dt/τ_θ instead of storing it as a per-step constant.
- Rescale every other per-step quantity: λ through `lam_from_tau_s`, and the per-step η_θ as η_θ·dt.
- Expect behaviour changes. Regenerate any stored reference outputs.

**18. PD-HAZARD.** Needs task 12 (r_max).
Replace the per-step Bernoulli draw with 1 − exp(−r_max·Bₜ·dt). Change `core/ignition.py` `sample_ignition_state` to take `dt` and `r_max`, and update its callers in `pipeline.py` (lines 1045 and 1205).

**19. Decide whether `apgi-validation`'s `apgi_core` (`engine.py`, `equations.py`, `model.py`) also counts as production code.** Owner: Uxod. It has not been checked yet. If it counts, add it to `test_production.py` the same way.

**20. After each production fix, in `apgi-lean`:**
- Set that PD entry to `resolved`.
- Bump the commit in `specification/known-conflicts.json` → `production.commit`.
- Bump the same commit in `.github/workflows/lean_action_ci.yml` (`ref:`).

Until you do this, the strict xfail becomes a hard failure. That is intended.

---

## Phase 6: Next Zenodo release (v1.2), corpus fixes

**21. Math Spec p4.** Change "γ_sig … (dimensionless)" to "1/AU". The reason is on p3: τ_σ carries the units of S, and γ_sig = 1/τ_σ.

**22. APGI-Advances p13.** Restate "Biological overhead ≈ 1.7 × 10³ (κ = 100 ÷ 0.06)" as R_L, or remove it. κ is uncalibrated and measured in ATP/bit.

**23. File names.** Several v1.1 PDFs are still named "Version 1.0". The "companion documents" PDF is byte-identical to the Mathematical Specification; drop the duplicate.

**24. If you chose option B in task 7,** include the cusp potential in this release.

**25. After publishing:**
- Re-hash every source and update `revision` and `sha256` in `source-manifest.json`.
- Run extraction with `--write`. Every evidence page number must still match; fix the ones that moved.
- Confirm the corpus scan reports 0 defects.

---

## Phase 7: Optional Lean (only if task 11 chooses b)

**26. Hazard dt-invariance.** Prove that two steps of dt equal one step of 2·dt: (1 − p_dt)² = 1 − p_2dt. This backs PD-HAZARD directly.

**27. Leaky-integrator gain.** Prove λ = 1 − exp(−dt/τ_S) ∈ (0, 1) for dt > 0. It reuses `decayGain_mem_Icc`.

**28. Cusp converse.** Prove that three distinct equilibria imply 4a³ + 27θ² < 0. That makes the discriminant rule an "if and only if" in Lean, not just the sufficient direction.

---

## Routine after any registry edit

```powershell
cd C:\Claude\Projects\apgi-lake
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"
python -m pytest -q -rxs
cd ..\..
git add -A
git commit
git push origin main
```

If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction. Run the first line again.
