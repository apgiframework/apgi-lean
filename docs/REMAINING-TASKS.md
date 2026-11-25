# APGI verification: remaining tasks

State as of 2026-11-25 05:15 ET (spec 0.3.1, task 36 round).

- Repository: https://github.com/apgiframework/apgi-lean. Local checkout: `C:\Claude\Projects\apgi-lake`. Local `main` is one commit ahead of GitHub (this round, not pushed).
- Production: https://github.com/apgiframework/apgi-implementation `main` = 736c296 (contains the pinned 7a366db). `main` is the only branch on GitHub; `claude/awesome-hypatia-2q329f` is gone.
- Second production package: https://github.com/apgiframework/apgi-validation, pinned at de06453. Local clone `Claude outputs\apgi-validation` on branch `fix/spec-alignment-v12` (628f5b1, not pushed); worktree `Claude outputs\apgi-validation-pin` at de06453 for the pinned run.
- Local results: extraction 39 of 39 verified; `lake build --wfail` passes; 41 of 41 theorems pass the axiom audit; check_consistency 0 open, 0 unacknowledged, 0 stale; pytest 116 passed, 1 xfailed (PD-LOOP-GAIN), 1 skipped (test_production_validation.py, run separately); test_production_validation.py 3 passed, 4 xfailed at de06453; make_report 6 of 7 locally (the seventh needs a CI run).
- Rating: design 93/100, implementation 95/100, overall readiness 94/100 (verification-instructions.txt).

## Done on 2026-11-25 (task 36 round)

- **Task 1.** The old branch `claude/awesome-hypatia-2q329f` is no longer on GitHub (checked with `git ls-remote`).
- **Task 3, local cleanup.** Deleted `.lake.mac-backup\` (481 MB), `build.err`, `build.log`, `cache-get.log`, the duplicate root `REMAINING-TASKS.md`, `Claude outputs\venv` (432 MB), `Claude outputs\corpus-text` and the old logs and scripts there, and `%TEMP%\apgi-*`. Kept: `Claude outputs\apgi-pending-files.zip`, `parameters.orig.json`, and this round's clones and logs.
- **Task 36, first half.** test_production_validation.py ran against de06453: 3 passed, 4 xfailed, exactly as the static reading predicted, so no PV entry needed correcting.
- **Task 36, second half.** All four PV divergences fixed in apgi-validation on `fix/spec-alignment-v12` (628f5b1): PV-THETA-SCALE (θ₀ = 0.35 AU, validated to [0.25, 0.85]; APGISettings.theta0 = 0.35), PV-CLIP (θ floor 0, per task 29), PV-HAZARD (hazard 1 − exp(−r_max·Bₜ·dt), r_max = 100 s⁻¹, in full_model and the equations.py engine), PV-DT (Δt = 10 ms, warning when Δt > τ/10). Against 628f5b1 the four strict xfails XPASS. apgi-validation's affected tests: 420 passed, 21 skipped, 4 failed; the same 4 fail at de06453 on Windows (no `resource` module; CRLF checkout breaks the protocol manifest checksums).
- **Task 36, CI.** New job `production-validation` runs the module at the pinned commit; the report job now needs it. New test `test_ci_checks_out_the_pinned_production_commits` ties both CI `ref:` values to known-conflicts.json.
- **Task 34, review of the v1.2 draft edits.** γ_sig in 1/AU, c_θ in AU, α_Π ≥ 0 and the §7.7 cusp mathematics are correct and consistent (unique equilibrium for a ≥ 0; three equilibria iff 4a³ + 27θ² < 0; fold points ±2·(−a/3)^{3/2}; matches the Lean theorems). The corpus scan of the v1.2 drafts finds none of the old defects. Two new cross-document conflicts, registered as corpus patterns (seeded and clean fixtures extended):
  - **E20, KC-LOOPGAIN-NO-TAU.** Paper 2 (parameter table) and Paper 3 (Appendix B.5) write the loop gain as γ_ψ² < 1/(C_down·C_up); the Notation Appendix and Specifications write (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² < 1. With C in s⁻¹ only the second is dimensionless. Paper 3's γ_ψ ∈ [1, 3] rests on the first.
  - **E21, KC-TAU-PI-LEVEL.** Paper 3 sets τ_Π = τ_ℓ/10: 5 ms at ℓ = 0, 0.66 s at ℓ = 1. That breaks the v1.2 bound τ_Π ≥ 1 s, and 5 ms breaks dt ≤ τ_Π/10 at dt₀ = 10 ms.
  - Minor, optional: §7.7 calls θ dimensionless and "the effective threshold on the reduced scale", while θₜ elsewhere is in AU. Consider θ̃ or the phrase "rescaled threshold". Any edit changes the draft's sha256, so re-pin SRC-MATHSPEC-V12D afterwards.
- **Task 35, analysis.** tau_pi is in seconds in effect: `core/config_schema.py` validate_dt_stability compares it with tau_s in s, and the precision ODE runs with dt in s. Recorded as a note on PD-LOOP-GAIN. Under the τ_Π form the current couplings need τ_Π < 1/(γ_ψ·√(C_down·C_up)) ≈ 7.07 s; under the τ_Π-free form the defaults give 0.02 < 1. The decision waits on task 38.

---

## Phase 1: Publish this round (Owner: Uxod)

**40. Push apgi-lean `main`.** One local commit (CI job, corpus patterns, registry notes, reports, this file). From `C:\Claude\Projects\apgi-lake`: `git push origin main`. Expect CI 3 + 1 jobs green and 7 of 7.

**41. Publish the apgi-validation fixes.**
```powershell
cd "C:\Claude\Projects\apgi-lake\Claude outputs\apgi-validation"
git push -u origin fix/spec-alignment-v12
```
Open and merge the PR (merge commit, so 628f5b1 stays reachable). Then in apgi-lean: set `production_secondary.commit` to the merged commit that contains 628f5b1 (or 628f5b1 itself), set PV-THETA-SCALE, PV-CLIP, PV-HAZARD and PV-DT to `resolved` (move each `fix_pending_merge` text into `resolution`), set the CI `ref:` of the production-validation job to the same commit, and run the routine. Expect 7 passed.

**2. Optional.** Start ssh-agent once (`Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent; ssh-add $HOME\.ssh\id_ed25519_apgi`), so pushes stop asking for the passphrase.

**42. Optional cleanup.** `Claude outputs\apgi-validation-pin` is a worktree of the clone: remove it with `git -C "Claude outputs\apgi-validation" worktree remove ..\apgi-validation-pin` once the pin moves.

## Phase 2: Author decisions (Owner: Uxod)

**38. Canonical loop-gain form (E20).** Choose (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² < 1 (dimensionless; Notation Appendix, Specifications) or γ_ψ² < 1/(C_down·C_up) (Paper 2, Paper 3). Recommendation: the τ_Π form, since it is the only dimensionless one; then rewrite the Paper 2 table row and the Paper 3 Appendix B.5 sentences, including the γ_ψ ∈ [1, 3] justification and the Lyapunov rate.

**39. τ_Π bound versus Paper 3 (E21).** Either scope τ_Π ≥ 1 s to the single-scale model in Math Spec §2.6 and the Notation Appendix row, or change Paper 3's τ_Π = τ_ℓ/10 (for example τ_Π,ℓ = max(1 s, τ_ℓ/10)). Either choice changes a v1.2 draft: re-pin SRC-MATHSPEC-V12D if the Math Spec changes.

**35. PD-LOOP-GAIN.** After task 38: with the τ_Π form, choose τ_Π ∈ [1, 7) s at the current couplings (for example 5 s, loop gain 0.5), or lower C_down·C_up; state the unit "s" in apgi-implementation's tau_pi description and validator. Then resolve PD-LOOP-GAIN, bump `production.commit` and the CI ref.

**37. models/reduced.py.** Recommendation: keep the constants. The model is per trial, not per integration step, so the dt ≤ τ/10 rule does not apply, and the K7 identifiability results and gate table depend on these values. Drop the derivation "λ = 1 − exp(−dt/τ_S) with dt = 0.5, τ_S = 5" from the docstring (τ_S = 5 s lies outside the registered [0.2, 0.5] s) and state λ ≈ 0.095 as a per-trial retention constant.

**33. r_max** = 100 s⁻¹ is a placeholder until fitted (now in both production packages).

## Phase 3: Next Zenodo release (v1.2)

**22.** APGI-Advances p13: restate "Biological overhead ≈ 1.7 × 10³ (κ = 100 ÷ 0.06)" as R_L, or remove it. No v1.2 draft of APGI-Advances is in `apgi-v-1-2`.

**23.** Several v1.1 PDFs are still named "Version 1.0"; drop the duplicate "companion documents" PDF.

**34. Done (review), see above.** Apply the outcomes of tasks 38 and 39 and the optional §7.7 wording before publishing. Originals are in `apgi-v-1-2\_backup\`.

**25. After publishing:** re-hash every source; re-source EQ-CUSP-1, tau_Pi and alpha_Pi from SRC-MATHSPEC-V12D to the published Math Spec PDF and retire the draft entry; run extraction with `--write` and fix any moved page numbers; confirm the corpus scan of the published PDFs reports 0 defects (today the v1.2 drafts show 4 hits, all E20 and E21).

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
$env:APGI_VALIDATION_PATH = "C:\Claude\Projects\apgi-lake\Claude outputs\apgi-validation-pin"   # checkout of production_secondary.commit
python -m pytest -q -rxs test_production_validation.py
Remove-Item Env:APGI_VALIDATION_PATH
cd ..\..
git add -A
git commit
git push origin main
```

`generate_lean.py` hashes known-conflicts.json too: regenerate and rebuild after changing the production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction.
