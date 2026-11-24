# APGI verification: remaining tasks

State as of 2026-11-24 16:00 ET (spec 0.3.0).

- Repository: https://github.com/apgiframework/apgi-lean. Local checkout: `C:\Claude\Projects\apgi-lake`.
- GitHub `main` is at 1c5e03d. Local `main` carries two unpushed commits: the one that added this file (15328d4) and the spec 0.3.0 commit described below.
- Production fixes live on a new local branch, `fix/spec-alignment` in `C:\Claude\Projects\apgi-implementation`, at 7703169 (one commit on top of a106d98). It is **not pushed**. Its worktree is `apgi-lake\Claude outputs\impl-wt`.
- Local results: `lake build --wfail` passes; 41 of 41 theorems pass the axiom audit (14 pilot, 27 new); pytest gives 112 passed and 1 xfailed (PD-CLIP); the consistency check finds 1 open conflict (KC-PRECOND-TAU-PI); 39 of 39 parameters are verified against their sha256 pins. The production suite gives 2825 passed, 11 skipped, and the same 2 Windows-only failures as a106d98.
- Pilot criteria: 6 of 7 locally. Criterion 1 is now met. Criterion 6 (report built in GitHub Actions) is met only by a CI run.

## Done in this session

- **Task 7, option B.** You chose B. §7.7 of `apgi-v-1-2\APGI-Mathematical-Specifications.md` now states the cusp normal form V(x) = x⁴/4 + a·x²/2 + θ·x, the iff discriminant rule and the fold points. EQ-CUSP-1 is re-sourced to `SRC-MATHSPEC-V12D` (that draft, pinned by sha256). `SRC-INNOV-GDOC` is retired. Tasks 6 and 9 are therefore closed: KC-UNPINNED is `resolved`.
- **Task 8.** The defect scan now reads Markdown correctly (it unescapes `\_`, `\[`). It finds 0 defects in the edited v1.2 drafts. Before the edits it found 2: γ_sig "(dimensionless)" and the new KC-CTHETA-UNIT. The published v1.1 PDFs still show 3 hits (E8, E9, KC-CTHETA-UNIT); task 25 removes them.
- **Task 10.** The pilot is re-rated in `verification-instructions.txt`: design 92/100, implementation 91/100. The last checklist item is ticked.
- **Task 11.** You chose option (b), targeted theorems. The decision and its reason are recorded in `verification-instructions.txt`.
- **Task 12.** 19 parameters are registered with page-cited quotes, all verified against the pins: r_max, δ_reset, ρ_retain, the NE bound (0.5, emitted to `Spec.lean` as `ne_bound`), τ_Π, τ_res, Δt_res, α_Π, C_down, C_up, α⁺, α⁻, γ⁺, γ⁻, β_DA, c_θ, v₁, v₂ and M̂(c,a).
- **Task 13.** These equations are registered: EQ-LEAK-1 (Eq. 23–24), EQ-HAZARD-1 (Eq. 35), EQ-NE-1 (the NE clamp), EQ-ALLO-1 (Eq. 26, then decay, then floor), EQ-PSI-1 (Eq. 21) and EQ-PREC-SM-1 (the Πⁱ_eff form).
- **Task 14.** EQ-EULER-1 now carries the full rule: dt ≤ τ_θ/10, dt ≤ τ_Π/10, and, with the reservoir active, Δt_res ≤ τ_res/10. Only the τ_Π part cannot be checked; see task 31.
- **Tasks 15–18.** The production code is fixed on `fix/spec-alignment`. PD-FLOOR, PD-DT, PD-TAU-THETA, PD-KAPPA-SYMBOL and PD-HAZARD are resolved there, and so is PD-TAU-S, a new finding (τ_S was 5 s). The old names stay as aliases for one release and emit `APGIDeprecationWarning`. Golden trajectories are regenerated.
- **Task 20.** All six PD entries are set to `resolved`. `production.commit` and the CI `ref:` now point at 7703169.
- **Tasks 21 and 24.** Both are applied to the v1.2 drafts. A backup of the originals sits in `apgi-v-1-2\_backup\`. The Notation Appendix table now gives c_θ as AU.
- **Tasks 26–28.** These are proved in `Apgi/Dynamics.lean`: `hazard_two_steps`, `hazard_n_steps`, `leakGain_mem_Ioo`, `leak_two_steps`, `cusp_three_equilibria_converse` and `cusp_three_equilibria_iff`, plus the theorems behind EQ-NE-1, EQ-ALLO-1, EQ-PSI-1 and EQ-PREC-SM-1. Each has a float64 twin test. Claims CL-10 to CL-16 are added and CL-5 is now an equivalence.
- `apgi-v-1-2/` is git-ignored, so the drafts can never be committed to the public repo.

---

## Phase 1: Publish (Owner: Uxod, in this order)

**1. Push the production branch first.** CI checks out `apgi-implementation` at 7703169, and that commit exists only on your machine.
```powershell
cd C:\Claude\Projects\apgi-implementation
git push origin fix/spec-alignment
```
Then open a PR into `main` and merge it. Its own CI runs ruff, mypy and pytest, and all three pass locally.

**2. Push `main` of apgi-lean** with the apgiframework SSH key, as before:
```powershell
cd C:\Claude\Projects\apgi-lake
git push origin main
```
If you push this before task 1, the Python job fails at checkout. That failure is expected; re-run the job after task 1.

**3. Optional: push without a manual terminal.** Either start ssh-agent once from an admin PowerShell (`Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent; ssh-add $HOME\.ssh\id_ed25519_apgi`), or give `lesoto` write access to both repos.

**4. Confirm CI run #4** under Actions → "APGI verification". Expect all three jobs green, 112 passed and 1 xfailed (PD-CLIP), and a report showing 7 of 7 criteria. If a job fails, copy its first error line into the next session.

**5. Local cleanup.** Everything listed here is git-ignored or temporary.
- In `apgi-lake`, delete `.lake.mac-backup\` (several GB), `build.err`, `build.log` and `cache-get.log`.
- Delete `Claude outputs\` once task 1 is merged. It holds the production worktree, so run `git worktree remove "C:\Claude\Projects\apgi-lake\Claude outputs\impl-wt"` from `apgi-implementation` first. It also holds the test venv and text dumps of the pinned PDFs.
- Delete the duplicate `apgi-lake\REMAINING-TASKS.md` in the repo root. The tracked copy is `docs\REMAINING-TASKS.md`.
- Delete `%TEMP%\apgi-corpus\` and the `%TEMP%\apgi-*.py` scratch scripts.

---

## Phase 2: Author decisions (Owner: Uxod)

**19. Decide whether `apgi-validation`'s `apgi_core` counts as production code.** That repo is not checked out on this machine, so it has not been looked at. If it counts, add it to `test_production.py` the way `apgi-implementation` was added.

**29. PD-CLIP (new, open).** The pipeline clips θ to [0.1, 20] AU (`theta_clip_min`), citing "MathSpec §15". The v1.1 Math Spec states no such clip, and its floor default is θ_floor = 0. Either document 0.1 AU as a study-stated floor or set it to 0. Then set PD-CLIP to `resolved` and bump the commit (task 20 routine).

**30. PD-KAPPA-RESIDUAL (new, open).** Bare κ still names other quantities: the learning rate `kappa` in `core/dynamics.py` and `core/preprocessing.py`, the relaxation rate in `engine/somatic.py`, the `KAPPA` decay constant in `engine/latent_state.py` and `estimation/*.py`, `compute_jacobian_discrete(kappa=…)`, and the `*kappa_meta*` names in `energy/bold_calibration.py`. Rename them with the same alias pattern (`core/deprecation.py`). `energy/thermodynamics.py`'s `kappa` is ATP/bit, the correct use, and stays.

**31. KC-PRECOND-TAU-PI (new, open).** The corpus defines τ_Π but gives it no value or range (Math Spec p6, Notation Appendix p16), so the spec's own rule dt ≤ τ_Π/10 cannot be checked. State a τ_Π range or lower bound in v1.2. Production uses τ_Π = 1000 s. Then register the range with an evidence quote and set the conflict to `resolved`.

**32. α_Π sign (minor).** Math Spec p6 says α_Π ≥ 0; p16 says α_Π > 0. Pick one in v1.2.

**33. r_max.** Production now uses r_max = 100 s⁻¹ (= 1/dt₀), a placeholder that matches the old per-step behaviour at dt₀. The corpus says r_max is fitted. Replace it once a fit exists.

---

## Phase 3: Next Zenodo release (v1.2)

**22. APGI-Advances p13.** Restate "Biological overhead ≈ 1.7 × 10³ (κ = 100 ÷ 0.06)" as R_L, or remove it. No v1.2 draft of APGI-Advances is in `apgi-v-1-2`, so this edit is still open.

**23. File names.** Several v1.1 PDFs are still named "Version 1.0". The "companion documents" PDF is byte-identical to the Mathematical Specification; drop it from the release.

**34. Review the edits made in the v1.2 drafts** before you publish. They are: the γ_sig unit (Math Spec glossary), c_θ = AU (Notation Appendix Table 20), and the new §7.7. The originals are in `apgi-v-1-2\_backup\`. Any further edit to the Math Spec draft changes its sha256, so re-pin `SRC-MATHSPEC-V12D` with `extract_sources.py --hash` and run the routine.

**25. After publishing:**
- Re-hash every source and update `revision` and `sha256` in `source-manifest.json`.
- Re-source EQ-CUSP-1 from `SRC-MATHSPEC-V12D` to the published Math Spec PDF and retire the draft entry.
- Run extraction with `--write`. Every evidence page number must still match; fix any that moved.
- Confirm the corpus scan of the published PDFs reports 0 defects. It reports 3 today, all fixed in the drafts or in task 22.

---

## Routine after any registry edit

```powershell
cd C:\Claude\Projects\apgi-lake
python verification\python\extract_sources.py --corpus C:\Claude\Projects\Neuro-Brain\Neuro-Input --corpus C:\Claude\Projects\apgi-lake\apgi-v-1-2 --write
python verification\python\generate_lean.py
lake build --wfail
python verification\python\check_consistency.py
cd verification\python
$env:APGI_IMPL_PATH = "C:\Claude\Projects\apgi-implementation"   # check out the commit in known-conflicts.json first
python -m pytest -q -rxs
cd ..\..
git add -A
git commit
git push origin main
```

`--corpus` can now be repeated. The second directory supplies the v1.2 draft that carries the cusp form.

If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction. Run the first line again.
