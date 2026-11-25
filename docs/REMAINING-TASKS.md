# APGI verification: remaining tasks

State as of 2026-11-24 19:45 ET (spec 0.3.1).

- Repository: https://github.com/apgiframework/apgi-lean. Local checkout: `C:\Claude\Projects\apgi-lake`.
- GitHub `main` is at 1c5e03d. Local `main` carries three unpushed commits: 15328d4 (this file), c86d4b5 (spec 0.3.0) and the spec 0.3.1 commit described below.
- Production branch `fix/spec-alignment` in `C:\Claude\Projects\apgi-implementation` is at 7a366db (two commits on a106d98: 7703169, 7a366db). Not pushed. Its worktree is `apgi-lake\Claude outputs\impl-wt`.
- Local results: `lake build --wfail` passes; 41 of 41 theorems pass the axiom audit; check_consistency finds 0 open, 0 unacknowledged, 0 stale; 39 of 39 parameters are verified against their sha256 pins; pytest gives 115 passed, 1 xfailed (PD-LOOP-GAIN), 1 skipped (test_production_validation.py, no checkout). The production suite gives 2830 passed, 11 skipped, 1 failed (the Windows-only cp1252 baseline failure).
- Pilot criteria: 6 of 7 locally. Criterion 6 (report built in GitHub Actions) is met only by a CI run.
- Rating: design 94/100, implementation 93/100 (verification-instructions.txt).

## Done on 2026-11-24 (evening)

- **Task 29, PD-CLIP (floor to 0).** theta_clip_min = 0.0; 20 AU stays as a numerical guard. Resolved.
- **Task 30, PD-KAPPA-RESIDUAL.** Bare κ no longer names a learning rate, decay exponent or R_L; CONFIG kappa_e/kappa_i became eta_pred_e/eta_pred_i. Old names are one-release deprecation aliases, including result keys. Found on the way and fixed: the BOLD calibrator reported the dimensionless R_L as J/bit (E14). Resolved.
- **Task 31, τ_Π.** The v1.2 Math Spec draft §2.6 states the design lower bound τ_Π ≥ 1 s; registered from SRC-MATHSPEC-V12D (re-pinned). KC-PRECOND-TAU-PI resolved.
- **Task 32, α_Π.** α_Π ≥ 0 in the Math Spec and Notation Appendix drafts.
- **Task 19, apgi-validation.** apgi_core counts as production code. Pinned at de06453 under `production_secondary` in known-conflicts.json with four open divergences: PV-THETA-SCALE, PV-CLIP, PV-HAZARD, PV-DT.
- **Task 20 routine.** `production.commit` and the CI `ref:` point at 7a366db.
- test_conflicts.py: the known-conflict check no longer turns into a skip when no conflict is open.

---

## Phase 1: Publish (Owner: Uxod, in this order)

**1. Push the production branch first.** CI checks out `apgi-implementation` at 7a366db, which exists only on your machine.
```powershell
cd C:\Claude\Projects\apgi-implementation
git push origin fix/spec-alignment
```
Then open a PR into `main` and merge it.

**2. Push `main` of apgi-lean** with the apgiframework SSH key:
```powershell
cd C:\Claude\Projects\apgi-lake
git push origin main
```

**3. Optional.** Start ssh-agent once (`Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent; ssh-add $HOME\.ssh\id_ed25519_apgi`) or give `lesoto` write access, so pushes no longer need a manual terminal.

**4. Confirm CI** under Actions → "APGI verification": all jobs green, 115 passed, 1 xfailed, report 7 of 7.

**5. Local cleanup.** `.lake.mac-backup\` (several GB), `build.err`, `build.log`, `cache-get.log`, the duplicate root `REMAINING-TASKS.md`; `Claude outputs\` after task 1 is merged (run `git worktree remove "C:\Claude\Projects\apgi-lake\Claude outputs\impl-wt"` from apgi-implementation first); `%TEMP%\apgi-*`.

## Phase 2: Author decisions and follow-ups (Owner: Uxod)

**33. r_max** = 100 s⁻¹ is a placeholder until fitted.

**35. PD-LOOP-GAIN (open).** (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² < 1 (Notation Appendix p19, p34, proposed) is 2 × 10⁴ at production defaults (τ_Π = 1000, C_down = 0.1, C_up = 0.05, γ_ψ = 2) if tau_pi is in seconds. State tau_pi's unit; then lower C_down, C_up or τ_Π, or record the condition as non-binding. Then resolve PD-LOOP-GAIN and bump the commit.

**36. Run the apgi-validation cross-check once.**
```powershell
git clone https://github.com/apgiframework/apgi-validation "C:\Claude\Projects\apgi-lake\Claude outputs\apgi-validation"
cd "C:\Claude\Projects\apgi-lake\Claude outputs\apgi-validation"; git checkout de06453
cd C:\Claude\Projects\apgi-lake\verification\python
Remove-Item Env:APGI_IMPL_PATH -ErrorAction SilentlyContinue
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-lake\Claude outputs\apgi-validation"
python -m pytest -q -rxs test_production_validation.py
```
Expect 3 passed and 4 xfailed. An XPASS means the static reading was wrong: fix the entry. The PV divergences were found by reading source only. Then fix PV-THETA-SCALE, PV-HAZARD and PV-DT in apgi-validation (they feed protocol outputs), and add a separate CI job for this module.

**37. models/reduced.py** constants are per-trial values frozen at the pre-0.3.0 defaults (dt = 0.5, τ_S = 5). The docstring now says so; decide whether the reduced model keeps them.

## Phase 3: Next Zenodo release (v1.2)

**22.** APGI-Advances p13: restate "Biological overhead ≈ 1.7 × 10³ (κ = 100 ÷ 0.06)" as R_L, or remove it. No v1.2 draft of APGI-Advances is in `apgi-v-1-2`.

**23.** Several v1.1 PDFs are still named "Version 1.0"; drop the duplicate "companion documents" PDF.

**34. Review the v1.2 draft edits** before publishing: γ_sig unit, c_θ = AU (Notation Appendix Table 20), §7.7 cusp, and §2.6 α_Π ≥ 0 and τ_Π ≥ 1 s (also the Notation Appendix rows for α_Π and τ_Π). Originals are in `apgi-v-1-2\_backup\`. Any further Math Spec draft edit changes its sha256: re-pin SRC-MATHSPEC-V12D (`extract_sources.py --hash`) and run the routine.

**25. After publishing:** re-hash every source; re-source EQ-CUSP-1, tau_Pi and alpha_Pi from SRC-MATHSPEC-V12D to the published Math Spec PDF and retire the draft entry; run extraction with `--write` and fix any moved page numbers; confirm the corpus scan of the published PDFs reports 0 defects (3 today, all fixed in the drafts or in task 22).

---

## Routine after any registry edit

```powershell
cd C:\Claude\Projects\apgi-lake
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\apgi-v-1-2 --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-lake\Claude outputs\impl-wt"   # at the commit in known-conflicts.json
python -m pytest -q -rxs
cd ..\..
git add -A
git commit
git push origin main
```

`generate_lean.py` hashes known-conflicts.json too: regenerate and rebuild after changing the production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction.
