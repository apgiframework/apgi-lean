# APGI Verification Report

- Generated: 2026-11-25T00:02:30+00:00
- Spec version: 0.3.1 · registry hash `5330b3bd64ae87fb…`
- Lean build (`lake build --wfail`): **passed**
- Python test functions: **90 passed, 0 failed** of 92 (parametrised cases collapsed)
- Pilot criteria met: **6 of 7**

> A Lean proof establishes a consequence of a definition. It is not evidence that APGI describes the brain.

## Pilot criteria

- ✅ **Every canonical parameter has a source identifier, unit, version, and documented range** — all parameters complete
- ✅ **Known discrepancies produce explicit failures** — 0 open conflicts tracked; seeded suite passed
- ✅ **Lean theorems compile without sorry or unapproved axioms** — lake build --wfail: passed; 41/41 theorems axiom-audited via #guard_msgs
- ✅ **Mathematical results are linked to exact specification revisions** — Spec.lean hash matches registry 5330b3bd64ae
- ✅ **Python tests pass the APGI numerical tolerances (1e-9)** — 6/6 golden-vector tests passed
- ❌ **Continuous integration produces a reproducible verification report** — generated locally (CI run required)
- ✅ **No mathematical proof is described as empirical confirmation of APGI** — no claim cites a Lean theorem as empirical evidence

## Claims by epistemic status

### Proved
- **CL-1** Raising θ cannot make ignition easier at fixed S. — `Apgi.ignites_antitone_threshold` (passed), `Apgi.ignitionProb_antitone_threshold` (passed)
- **CL-2** The clamped update preserves the positivity floor θ_floor (0 AU by default). — `Apgi.clampedUpdate_floor` (passed)
- **CL-3** The θ₀ band [0.25, 0.85] AU is not an invariant of the clamped update for unrestricted targets; it is invariant when targets lie in the band and 0 ≤ g ≤ 1. Consistent with the Notation Appendix: θₜ may leave the band transiently. — `Apgi.operatingRange_not_invariant` (passed), `Apgi.operatingRange_invariant_of_target` (passed)
- **CL-4** a < 0 is necessary for cusp bistability (and hence hysteresis). — `Apgi.cusp_unique_equilibrium` (passed)
- **CL-5** Three distinct cusp equilibria exist if and only if 4a³ + 27θ² < 0 (which forces a < 0). — `Apgi.cusp_three_equilibria` (passed), `Apgi.cusp_three_equilibria_converse` (passed), `Apgi.cusp_three_equilibria_iff` (passed)
- **CL-6** Forward-Euler relaxation stays in bounds when Δt ≤ τ. — `Apgi.euler_step_mem_Icc` (passed)
- **CL-9** The exact exponential decay (Math Spec Eq. 32) keeps θ inside any interval that contains θ and θ₀, for every step dt ≥ 0, with no step-size condition. — `Apgi.decayGain_mem_Icc` (passed), `Apgi.decay_step_mem_Icc` (passed)
- **CL-10** The hazard sampler is dt-invariant: n steps of dt have the same survival probability as one step of n·dt, and the per-step probability lies in [0, 1] and rises with the propensity Bₜ. — `Apgi.hazardProb_mem_Icc` (passed), `Apgi.hazard_two_steps` (passed), `Apgi.hazard_n_steps` (passed), `Apgi.hazardProb_monotone_propensity` (passed)
- **CL-11** Raising θ cannot raise the per-step ignition probability under the hazard with logistic propensity. — `Apgi.hazard_antitone_threshold` (passed)
- **CL-12** The exact leaky-integrator gain λ = 1 − exp(−dt/τ_S) lies in (0, 1) for dt > 0; the integrator stays inside any interval containing S and S_inst and is dt-invariant under constant input. — `Apgi.leakGain_mem_Ioo` (passed), `Apgi.leak_step_mem_Icc` (passed), `Apgi.leak_two_steps` (passed)
- **CL-13** The NE clamp enforces |γ_NE|·g_NE ≤ 0.5 for either sign of γ_NE, keeps 1 + γ_NE·g_NE in [0.5, 1.5], and so never drives a positive threshold to zero. — `Apgi.neClamp_bound` (passed), `Apgi.neFactor_band` (passed), `Apgi.neThreshold_pos` (passed)
- **CL-14** The canonical threshold step (Eq. 26, exact decay, floor) respects θ_floor; with δ_reset ≥ 0 an ignition never lowers the next threshold, and with η_θ ≥ 0 a larger C − V never lowers it. — `Apgi.thresholdStep_floor` (passed), `Apgi.thresholdStep_monotone_ignition` (passed), `Apgi.thresholdStep_monotone_drive` (passed)
- **CL-15** Ψ(z) is strictly bounded by max(α⁺, α⁻); with α⁺ = α⁻ and γ⁺ = γ⁻ it reduces to α·tanh(γ·z), which is odd. — `Apgi.psi_abs_lt` (passed), `Apgi.psi_symmetric` (passed), `Apgi.psi_odd_of_symmetric` (passed)
- **CL-16** With β_SM ≥ 0, Πⁱ_eff is non-negative and non-decreasing in M̂(c,a); the hard clamp keeps it in [Π_min, Π_max]. — `Apgi.precEff_nonneg` (passed), `Apgi.precEff_monotone_marker` (passed), `Apgi.precClamp_mem_Icc` (passed)

### Assumed
- **CL-8** κ (ATP per bit of ignition-event information) has no canonical value; published sensitivity calculations span 3 × 10³ to 10⁹ ATP/bit. — no evidence registered

### Unresolved
- **CL-7** APGI's hysteresis prediction (Innovation 4) holds in human data. — no evidence registered

## Theorems

- `Apgi.clampedUpdate_floor` — EQ-THR-1 — axiom audit: pinned
- `Apgi.convex_update_mem_Icc` — EQ-UPD-1 — axiom audit: pinned
- `Apgi.cuspV_hasDerivAt` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_three_equilibria` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_three_equilibria_converse` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_three_equilibria_iff` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_two_equilibria_witness` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_unique_equilibrium` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.decayGain_mem_Icc` — EQ-DECAY-1 — axiom audit: pinned
- `Apgi.decayStep_monotone` — EQ-ALLO-1 — axiom audit: pinned
- `Apgi.decay_step_mem_Icc` — EQ-DECAY-1 — axiom audit: pinned
- `Apgi.euler_step_mem_Icc` — EQ-EULER-1 — axiom audit: pinned
- `Apgi.hazardProb_mem_Icc` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.hazardProb_monotone_propensity` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.hazard_antitone_threshold` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.hazard_n_steps` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.hazard_survival_add` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.hazard_two_steps` — EQ-HAZARD-1 — axiom audit: pinned
- `Apgi.ignites_antitone_threshold` — EQ-IGN-1 — axiom audit: pinned
- `Apgi.ignites_monotone_precision` — EQ-PREC-1 — axiom audit: pinned
- `Apgi.ignitionProb_antitone_threshold` — EQ-IGN-2 — axiom audit: pinned
- `Apgi.leakGain_mem_Ioo` — EQ-LEAK-1 — axiom audit: pinned
- `Apgi.leak_step_mem_Icc` — EQ-LEAK-1 — axiom audit: pinned
- `Apgi.leak_two_steps` — EQ-LEAK-1 — axiom audit: pinned
- `Apgi.neClamp_bound` — EQ-NE-1 — axiom audit: pinned
- `Apgi.neClamp_nonneg` — EQ-NE-1 — axiom audit: pinned
- `Apgi.neClamp_of_le` — EQ-NE-1 — axiom audit: pinned
- `Apgi.neFactor_band` — EQ-NE-1 — axiom audit: pinned
- `Apgi.neFactor_mem_Icc` — EQ-NE-1 — axiom audit: pinned
- `Apgi.neThreshold_pos` — EQ-NE-1 — axiom audit: pinned
- `Apgi.operatingRange_invariant_of_target` — EQ-THR-1 — axiom audit: pinned
- `Apgi.operatingRange_not_invariant` — EQ-THR-1 — axiom audit: pinned
- `Apgi.precClamp_mem_Icc` — EQ-PREC-SM-1 — axiom audit: pinned
- `Apgi.precEff_monotone_marker` — EQ-PREC-SM-1 — axiom audit: pinned
- `Apgi.precEff_nonneg` — EQ-PREC-SM-1 — axiom audit: pinned
- `Apgi.psi_abs_lt` — EQ-PSI-1 — axiom audit: pinned
- `Apgi.psi_odd_of_symmetric` — EQ-PSI-1 — axiom audit: pinned
- `Apgi.psi_symmetric` — EQ-PSI-1 — axiom audit: pinned
- `Apgi.thresholdStep_floor` — EQ-ALLO-1 — axiom audit: pinned
- `Apgi.thresholdStep_monotone_drive` — EQ-ALLO-1 — axiom audit: pinned
- `Apgi.thresholdStep_monotone_ignition` — EQ-ALLO-1 — axiom audit: pinned

## Open specification conflicts


## Traceability

Source → `specification/parameters.json` → `Apgi/Spec.lean` (generated, hash-pinned) → `Apgi/Pilot.lean` theorem → `test_twins.py` twin → `apgi_ref.py` → empirical evidence (`epistemic-claims.json`).
