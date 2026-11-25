# APGI verification: remaining tasks

State as of 2026-11-25 06:30 ET (spec 0.3.1, tasks 36–39 round).

- apgi-lean: https://github.com/apgiframework/apgi-lean, local `C:\Claude\Projects\apgi-lake`. `main` is the only branch.
- apgi-implementation: `main` = a9b2878 (pinned), local `C:\Claude\Projects\apgi-implementation`. `main` is the only branch.
- apgi-validation: `main` = 07ca731, local `C:\Claude\Projects\apgi-validation`. `main` is the only branch. Pinned at 811aee2; 07ca731 only rebuilds the `release/` manifest (its own gate XC-CI-05.3 hashes apgi_core), so apgi_core is identical.
- Local results: extraction 39 of 39 verified; `lake build --wfail` passes; 41 of 41 theorems pass the axiom audit; check_consistency 0 open, 0 unacknowledged, 0 stale; pytest 116 passed, 1 xfailed (PD-LOOP-GAIN), 1 skipped; test_production_validation.py 7 passed; apgi-implementation suite at a9b2878 2826 passed, 11 skipped; make_report 6 of 7 locally (the seventh needs a CI run).
- Rating: design 95/100, implementation 96/100, overall readiness 95/100 (verification-instructions.txt).
- Pushing: this PC's SSH key needs its passphrase and the HTTPS login (lesoto) has no write access to apgiframework, so this round was pushed through the Claude session's GitHub access. To push locally, see task 2.

## Done on 2026-11-25 (tasks 36–39 round)

- **Task 1.** `claude/awesome-hypatia-2q329f` is gone; every repository has `main` only.
- **Task 3, cleanup.** Deleted `.lake.mac-backup\` (481 MB), `build.err`, `build.log`, `cache-get.log`, the duplicate root `REMAINING-TASKS.md`, `Claude outputs\venv` (432 MB), the PDF text dumps, old logs and scripts, and `%TEMP%\apgi-*`. Kept `Claude outputs\apgi-pending-files.zip` and `parameters.orig.json`.
- **Task 36.** test_production_validation.py at de06453: 3 passed, 4 xfailed, as the static reading predicted. All four PV divergences fixed in apgi-validation 628f5b1 and merged to `main` as 811aee2: θ₀ = 0.35 AU (validated to [0.25, 0.85]), θ floor 0, ignition through 1 − exp(−r_max·Bₜ·dt) with r_max = 100 s⁻¹, Δt = 10 ms. Pin moved to 811aee2; PV-* resolved; 7 passed. New CI job `production-validation`; `test_ci_checks_out_the_pinned_production_commits` ties both CI refs to the pins.
- **Task 34, review of the v1.2 drafts.** γ_sig 1/AU, c_θ AU, α_Π ≥ 0 and the §7.7 cusp mathematics are correct. The review found E20 and E21 (below), registered as corpus patterns KC-LOOPGAIN-NO-TAU and KC-TAU-PI-LEVEL with seeded and clean fixtures.
- **Task 38 (E20), loop-gain form.** Canonical: (C_down·τ_Π)·(C_up·τ_Π)·γ_ψ² < 1, the only dimensionless form. Paper 2 v1.2 draft (γ_ψ row) and Paper 3 v1.2 draft (§2.5 summary, Appendix B.5) rewritten: C_down, C_up in s⁻¹; Paper 3's ranges restated as the dimensionless gains C_down·τ_Π ∈ [0.1, 0.5] and C_up·τ_Π ∈ [0.05, 0.2], which keeps γ_ψ < 3.16, so γ_ψ ∈ [1, 3] stands; Lyapunov rate uses the τ_Π form.
- **Task 39 (E21), τ_Π per level.** Paper 3 v1.2 draft: τ_Π = max(1 s, τ_ℓ/10) at level ℓ, so the Math Spec bound τ_Π ≥ 1 s holds at every level and dt₀ = 10 ms meets dt ≤ τ_Π/10. The Math Spec draft is unchanged, so SRC-MATHSPEC-V12D keeps its pin. The v1.2 drafts now scan clean (0 hits); both patterns stay active for the published v1.1 PDFs.
- **Task 37, reduced model.** apgi-implementation a9b2878: constants unchanged (same floats); the docstring states λ = 1 − e^(−0.1) as a per-trial constant and drops the dt = 0.5 s, τ_S = 5 s derivation.
- **Task 35, first half.** a9b2878 documents tau_pi in s, and validate_dt_stability now uses the configured tau_pi instead of a hard-coded 1000. Production pin moved to a9b2878.

---

## Phase 1: Owner actions (Uxod)

**2. Local pushes.** Start ssh-agent once in an elevated PowerShell (`Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent`), then `ssh-add $HOME\.ssh\id_ed25519_apgi` and type the passphrase. Until then, local `git fetch`/`git push` over `github-apgi` fail; read-only fetches over HTTPS still work.

**43. CI.** The production-validation job now installs apgi-validation with Python 3.11 and its `requirements.lock`, as apgi-validation's own CI does. Confirm the run on apgi-lean `main` shows 4 jobs green and 7 of 7.

## Phase 2: Author decisions (Owner: Uxod)

**35. PD-LOOP-GAIN, second half.** Production defaults (τ_Π = 1000 s, C_down = 0.1 s⁻¹, C_up = 0.05 s⁻¹, γ_ψ = 2) give 2 × 10⁴ under the canonical form. Either set τ_Π in [1, 7) s at the current couplings (for example 5 s, gain 0.5), or keep τ_Π and scale the couplings to the Paper 3 gains (C_down = 0.1/τ_Π, C_up = 0.05/τ_Π, gain 0.02). Then resolve PD-LOOP-GAIN, move `production.commit` and the CI ref.

**33. r_max** = 100 s⁻¹ is a placeholder until fitted (both production packages).

## Phase 3: Next Zenodo release (v1.2)

**22.** APGI-Advances p13: restate "Biological overhead ≈ 1.7 × 10³ (κ = 100 ÷ 0.06)" as R_L, or remove it. No v1.2 draft of APGI-Advances is in `apgi-v-1-2`.

**23.** Several v1.1 PDFs are still named "Version 1.0"; drop the duplicate "companion documents" PDF.

**44. Optional wording, Math Spec §7.7.** θ there is dimensionless ("the effective threshold on the reduced scale") while θₜ elsewhere is in AU; consider θ̃ or "rescaled threshold". Any Math Spec draft edit changes its sha256: re-pin SRC-MATHSPEC-V12D (`extract_sources.py --hash`) and run the routine. Originals of all drafts are in `apgi-v-1-2\_backup\`.

**25. After publishing:** re-hash every source; re-source EQ-CUSP-1, tau_Pi and alpha_Pi from SRC-MATHSPEC-V12D to the published Math Spec PDF and retire the draft entry; run extraction with `--write` and fix any moved page numbers; confirm the corpus scan of the published PDFs reports 0 defects (the v1.2 drafts already scan clean).

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

`generate_lean.py` hashes known-conflicts.json too: regenerate and rebuild after changing the production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction.
