# APGI verification: remaining tasks

State as of 2026-11-25 16:45 ET. Measured against **APGI Single Source of Truth (SSOT), framework v1.2, registry 0.3.1, hash 3fc0faa0…** (the hash matches `proof-status.json`).

- Repositories, all `main` only, local = GitHub: apgi-lean ca25d83; apgi-implementation a9b2878 (pinned); apgi-validation 07ca731 (pinned 811aee2, apgi_core identical).
- apgi-lean CI run 45603692681: 4 of 4 jobs green, **7 of 7** pilot criteria. B-15 and task 43 are closed.
- Rating against the SSOT: design 91/100, implementation 60/100, overall release readiness 58/100 (verification-instructions.txt). The earlier 95/96 measured the registry's own scope; the SSOT is a larger yardstick, so the drop is scope, not regression.

## Completion against the SSOT (numerator / denominator)

- Release blockers closed (SSOT §30.1): 7 of 18 (39%): B-01, 02, 03, 04, 06, 08, 15.
- Conformance tests TC-01…TC-26: 7 pass (TC-02, 05, 06, 18, 22, 23, 24), 5 partial (TC-01, 10, 13, 19, 21), 14 fail or not implemented. 27% pass; 37% with partials at half weight.
- SSOT equation IDs in `equations.json`: 10 of 53 (19%). Registered: EQ-IGN-1, IGN-2, HAZARD-1, LEAK-1, NE-1, ALLO-1, PSI-1, PREC-SM-1, CUSP-1, LAND-1.
- SSOT parameter rows in `parameters.json`: 35 of 73 (48%).
- Theorem register: 41 of 41 present, each axiom list pinned to [propext, Classical.choice, Quot.sound] (100%). Claim register: 16 of 16 statuses match (100%).
- Golden vectors: 25 in 6 families, as the SSOT states; required new families (B-10): 0 of 8.
- Prohibited-shortcut checks (SSOT §13), apgi-implementation default configuration: 3 of 7 applicable met (43%). apgi_core: 3 of 7 (43%).
- SSOT worked numbers recomputed: 31 of 31 correct (m₀, λ, null SD 0.110 AU, soft floors, r_max and θ₀ bounds, steepness bridge, ATP and Landauer figures, cusp roots, timescale table, loop-gain bounds).

## Audit findings (2026-11-25)

### Production does not implement the SSOT minimal core

apgi-implementation a9b2878, default `CONFIG`:
- **SSOT-P1, drive (EQ-DRIVE-1, EQ-EXCESS-1, EQ-PREC-REL-1).** `pipeline.step` drives S with the signed valence transform Π·Ψ(z) (`instantaneous_signal_phi`, "negative values suppress ignition"). There is no excess correction |z| − m₀ and no relative gain Π_eff/Π̄ anywhere in the package. The SSOT core uses Π_rel·|z|_ex, and Ψ is an extension that enters as a magnitude |Ψ(z)|_ex. This breaks TC-07 (null mean 0) and TC-09 (sign symmetry).
- **SSOT-P2, shared estimator (EQ-STD-1 vs EQ-EMA-1).** z is standardized with the same EMA mean and variance that give Π = 1/σ². The SSOT prohibits this: Π·|z| then scales as |ε − μ|/σ³. The current sample is correctly excluded, and the two-step EMA ordering is correct. TC-17 fails.
- **SSOT-P3, accumulation (EQ-LEAK-1).** The default is Euler–Maruyama `update_signal_ode` (drift −S/τ_S + ΠΨ, noise 0.01), a form the SSOT does not adopt. Its fixed point is τ_S·S_inst, not S_inst. The exact leak exists but is off (`use_canonical_discrete_mode = False`). `signal_log_nonlinearity = True` overwrites the state each step with log1p(max(0, S)), which forbids S < 0 and compounds. The SSOT allows compression only as a read-out when Ψ is active.
- **SSOT-P4, order (§13 steps 7–13).** S is accumulated before the ignition decision, and the threshold decays before ignition while δ·B(t) is added after it. The SSOT order is: decide from the existing S, then the allostatic step with δ_reset·B(t), then decay, then reset, then accumulate.
- **SSOT-P5, read-out rule (EQ-THEFF-1).** The NE factor, β_5HT, the circadian offset and the hierarchical modulation are applied to `theta_next`, and `self.theta = theta_next` writes them back. They are off by default; once enabled they compound. TC-11 fails.
- **SSOT-P6, NE clamp and sign (EQ-NE-1, R6).** `_enforce_ne_clamp` returns early for γ_NE ≤ 0, so a negative coupling is never clamped (CL-13 requires either sign). The default γ_NE = 0.1 gives a sign; R6 sets none. TC-10 is partial.
- **SSOT-P7, defaults.** θ₀ = 0.55 (SSOT 0.35). `stochastic_ignition = False`, so the default run is the hard-threshold limit, not the canonical hazard (the hazard path is correct when enabled). With ignite_tau = 0.5 the propensity floor is σ(−2·0.55) = 0.25: about 25 events/s at r_max = 100 s⁻¹ (R1, TC-14 not reported).
- Met: hazard sampling when stochastic; strict S > θ in the hard limit; θ floor 0 with a documented 20 AU guard; precision clamp [0.1, 10]; ρ_retain ∈ [0.1, 0.5] applied once on the default path; dt = 10 ms.
- Not checked: whether `use_hierarchical_precision_ode` runs alongside the inverse-variance Π (prohibited); whether the resonance path applies δ twice.

apgi-validation apgi_core (07ca731):
- **SSOT-V1.** `model.py` uses S = ½Πᵉ(zᵉ)² + ½Πⁱ(zⁱ)², recomputed each step with no accumulation. Its z uses the same running statistics as Π, after they absorb the current sample. Ignition is the deterministic `ignite`, and the interoceptive input is a synthetic 0.3·ε.
- **SSOT-V2.** `full_model.py` uses the uncentered Π|ε| and adds input per step without the λ weight, so S scales with 1/(1 − e^(−dt/τ)). The hazard, θ₀ = 0.35, the floor and dt = 10 ms are now correct (PV-*).

The registry cannot catch any of this yet: test_production*.py checks only the PD-*/PV-* items, and EQ-DRIVE-1, EQ-STD-1, EQ-EMA-1, EQ-THEFF-1 and the step order are not registered (B-09).

### Registry and Lean against the SSOT

- **SSOT-R1.** 43 of 53 SSOT equation IDs and 38 of 73 parameter rows are missing (B-09). Missing parameters include m₀, Π_min/Π_max, T_window, ε_stab, η_pred, g_ACh, g_NE, γ_NE, β_5HT, c₁–c₃, τ_ref, δ_ref, γ_ψ, τ₀, k, u₀ and a.
- **SSOT-R2.** `ignites_monotone_precision` (EQ-PREC-1) proves monotonicity for the uncentered Π·|ε|. Under the SSOT drive the term Π_rel·(|z| − m₀) is negative when |z| < m₀, where raising precision makes ignition harder. EQ-DRIVE-1 needs its own theorem: monotone in Π_rel iff |z| ≥ m₀.
- **SSOT-R3.** Registry constraints the SSOT states that the registry lacks: ρ_retain canonical [0.1, 0.5] (registry [0, 1]); C_down·τ_Π ∈ [0.1, 0.5] and C_up·τ_Π ∈ [0.05, 0.2] (registry: support only); τ_Π = max(1 s, τ_ℓ/10) per level.

### Defects in the SSOT document itself

- **SSOT-D1.** The author is "Dimitry Pesochin, dimitry@apgiframework.com"; the repositories and the published corpus use "Dmitry Pesochin, info@apgiframework.com". Pick one form.
- **SSOT-D2.** The source registry lists SRC-MATHSPEC twice and omits SRC-MATHSPEC-V12D, the pinned draft that EQ-CUSP-1, τ_Π and α_Π rest on. SRC-SPEC11, SRC-SSOT-C, SRC-VERIFY and SRC-REG have no sha256 pin in `source-manifest.json`, so the SSOT's own rule reports them UNPINNED, which blocks release.
- **SSOT-D3.** The text cites §5.2, §12, §12.4, §12.5, §13, §15.2, §16–§17, §19.3, §24, §25, §30.1 and §32, but no heading carries a number, and §32 (gate records) does not exist.
- **SSOT-D4.** The parameter section promises rows "flagged add to registry", but no row carries the flag, although 38 rows are absent from the registry.
- **SSOT-D5.** The SSOT defines θ̃ = (θ_eff − S)/u₀ and EQ-CUSP-2 and calls this "task 44 wording". Task 44 is not applied: the Math Spec draft §7.7 and `equations.json` still use θ, and u₀ is not registered.
- **SSOT-D6.** The theorem register cites EQ-PREC-1, EQ-THR-1, EQ-UPD-1, EQ-EULER-1 and EQ-DECAY-1, which the equation sections never define. EQ-PREC-1 is the uncentered form the SSOT prohibits.
- **SSOT-D7.** "Licenses: per repository LICENSE file": apgi-lean and apgi-validation have no LICENSE file (B-11).
- **SSOT-D8.** B-15 is listed as open; it is now closed (CI 7 of 7).

---

## Next step (one at a time)

**53. Make the production gap machine-checked.** Register SSOT-P1…P6 and SSOT-V1, V2 as divergences in known-conflicts.json, each with a strict-xfail test in test_production*.py, after registering the equations they test (EQ-DRIVE-1, EQ-EXCESS-1, EQ-PREC-REL-1, EQ-STD-1, EQ-EMA-1/2, EQ-THEFF-1, EQ-RESET-1, EQ-STEP-1, plus the §13 order as a pipeline rule). This changes no production behavior, turns TC-04/07/09/11/17 into explicit failures, and fixes the work list. About one session.

## Phase A: Align production with the SSOT core (after 53)

**45.** apgi-implementation: Π_rel·|z|_ex as the default drive; Ψ opt-in and used as |Ψ(z)|_ex. Closes SSOT-P1.
**46.** Separate standardization statistics (5 s / 10 s windows that exclude ε_t) from the precision EMA. Closes SSOT-P2.
**47.** Exact leak as the default accumulator; SDE as a declared extension; S never overwritten by log1p. Closes SSOT-P3.
**48.** Reorder `step` to SSOT §13; δ_reset only inside EQ-ALLO-1. Closes SSOT-P4.
**49.** θ_eff as a read-out value; nothing written back to θ. Closes SSOT-P5.
**50.** NE clamp for either sign; γ_NE without a default sign. Closes SSOT-P6.
**51.** Defaults θ₀ = 0.35 and hazard sampling; report γ_sig·θ₀, σ(−γ_sig·θ₀) and the stimulus-free rate (TC-14). Closes SSOT-P7.
**52.** apgi_core: align `model.py` and `full_model.py` with the core, or declare them non-canonical variants (SSOT rank 7: deviations must be identified). Recommendation: align `full_model.py`; label `model.py` as the energy-form variant.

Phase A changes model outputs: expect K7 and gate results to need a versioned rerun (SSOT §13 last paragraph).

## Phase B: Registry completeness (B-09, B-05, B-10)

**54.** Register the remaining 43 equation IDs and 38 parameter rows; add symbols.json, configurations.json (CFG-CORE, CFG-CORE-R, CFG-FULL with counted parameters) and revisions.json (R1–R18). Fixes SSOT-R1, R3.
**55.** Lean: a theorem for EQ-DRIVE-1 (monotone in Π_rel iff |z| ≥ m₀); then the SSOT "next targets" (hard-threshold limit, m₀ identity, read-out non-interference, exactly-once reset, folds of EQ-CUSP-2). Fixes SSOT-R2.
**56.** Golden-vector families hazardProb, leakStep, neClamp, thresholdStep, Ψ, precEff, EMA ordering, and a seeded CFG-CORE / CFG-CORE-R trajectory (B-10).

## Phase C: Author decisions and documents (Owner: Uxod)

**57. SSOT corrections.** D1 author name and email; D2 source registry (remove the duplicate, add SRC-MATHSPEC-V12D, pin the four new sources); D3 number the sections or drop the § references; D4 mark the missing rows; D5 apply task 44 to the Math Spec draft and register u₀, or drop θ̃ from the SSOT; D6 map or retire the five legacy equation IDs; D8 close B-15.
**58. Licenses (B-11).** Add LICENSE files to apgi-lean and apgi-validation and record all three in the release manifest.
**35. PD-LOOP-GAIN (B-12).** τ_Π in [1, 7.07) s at the current couplings, or couplings scaled to the Paper 3 gains.
**33. r_max and the operating point (B-13).** No default in [2, 7.5] reaches a floor ≤ 0.05 at θ₀ = 0.35; fit r_max and declare θ₀ and γ_sig.
**B-14.** OSF Amendment 2 (R4 before P0, R10 before P1 steepness, R8 before P4, recovery readings). **B-07** second-reader check of the hypothesis register. **B-17** independent reviewers. **B-18** add Naccache et al. (2025); Crossref-verify all DOIs.
**2.** ssh-agent, so pushes from this PC work.

## Phase D: Next Zenodo release (v1.2)

**22.** APGI-Advances p13: restate the κ overhead as R_L, or remove it. **23.** v1.1 PDFs still named "Version 1.0"; drop the duplicate companion PDF. **44.** §7.7 θ̃ wording (now also SSOT-D5). **25.** After publishing: re-hash every source, re-source EQ-CUSP-1, tau_Pi and alpha_Pi to the published Math Spec, retire SRC-MATHSPEC-V12D, re-run extraction, confirm 0 corpus defects.

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

`generate_lean.py` hashes known-conflicts.json too: regenerate and rebuild after changing the production pin. If `check_consistency.py` reports `extraction_unverified`, a registry value changed without re-running extraction.
