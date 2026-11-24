# APGI Verification Report

- Generated: 2026-11-24T06:15:57+00:00
- Spec version: 0.2.0 · registry hash `e37ebd033e84155e…`
- Lean build (`lake build --wfail`): **passed**
- Python test functions: **56 passed, 0 failed** of 61 (parametrised cases collapsed)
- Pilot criteria met: **5 of 7**

> A Lean proof establishes a consequence of a definition. It is not evidence that APGI describes the brain.

## Pilot criteria

- ❌ **Every canonical parameter has a source identifier, unit, version, and documented range** — all parameters complete; no sha256 for SRC-INNOV-GDOC
- ✅ **Known discrepancies produce explicit failures** — 1 open conflicts tracked; seeded suite passed
- ✅ **Lean theorems compile without sorry or unapproved axioms** — lake build --wfail: passed; 14/14 theorems axiom-audited via #guard_msgs
- ✅ **Mathematical results are linked to exact specification revisions** — Spec.lean hash matches registry e37ebd033e84
- ✅ **Python tests pass the APGI numerical tolerances (1e-9)** — 6/6 golden-vector tests passed
- ❌ **Continuous integration produces a reproducible verification report** — generated locally (CI run required)
- ✅ **No mathematical proof is described as empirical confirmation of APGI** — no claim cites a Lean theorem as empirical evidence

## Claims by epistemic status

### Proved
- **CL-1** Raising θ cannot make ignition easier at fixed S. — `Apgi.ignites_antitone_threshold` (passed), `Apgi.ignitionProb_antitone_threshold` (passed)
- **CL-2** The clamped update preserves the positivity floor θ_floor (0 AU by default). — `Apgi.clampedUpdate_floor` (passed)
- **CL-3** The θ₀ band [0.25, 0.85] AU is not an invariant of the clamped update for unrestricted targets; it is invariant when targets lie in the band and 0 ≤ g ≤ 1. Consistent with the Notation Appendix: θₜ may leave the band transiently. — `Apgi.operatingRange_not_invariant` (passed), `Apgi.operatingRange_invariant_of_target` (passed)
- **CL-4** a < 0 is necessary for cusp bistability (and hence hysteresis). — `Apgi.cusp_unique_equilibrium` (passed)
- **CL-5** a < 0 and 4a³ + 27θ² < 0 together are sufficient for three distinct equilibria. — `Apgi.cusp_three_equilibria` (passed)
- **CL-6** Forward-Euler relaxation stays in bounds when Δt ≤ τ. — `Apgi.euler_step_mem_Icc` (passed)
- **CL-9** The exact exponential decay (Math Spec Eq. 32) keeps θ inside any interval that contains θ and θ₀, for every step dt ≥ 0, with no step-size condition. — `Apgi.decayGain_mem_Icc` (passed), `Apgi.decay_step_mem_Icc` (passed)

### Assumed
- **CL-8** κ (ATP per bit of ignition-event information) has no canonical value; published sensitivity calculations span 3 × 10³ to 10⁹ ATP/bit. — no evidence registered

### Unresolved
- **CL-7** APGI's hysteresis prediction (Innovation 4) holds in human data. — no evidence registered

## Theorems

- `Apgi.clampedUpdate_floor` — EQ-THR-1 — axiom audit: pinned
- `Apgi.convex_update_mem_Icc` — EQ-UPD-1 — axiom audit: pinned
- `Apgi.cuspV_hasDerivAt` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_three_equilibria` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_two_equilibria_witness` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_unique_equilibrium` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.decayGain_mem_Icc` — EQ-DECAY-1 — axiom audit: pinned
- `Apgi.decay_step_mem_Icc` — EQ-DECAY-1 — axiom audit: pinned
- `Apgi.euler_step_mem_Icc` — EQ-EULER-1 — axiom audit: pinned
- `Apgi.ignites_antitone_threshold` — EQ-IGN-1 — axiom audit: pinned
- `Apgi.ignites_monotone_precision` — EQ-PREC-1 — axiom audit: pinned
- `Apgi.ignitionProb_antitone_threshold` — EQ-IGN-2 — axiom audit: pinned
- `Apgi.operatingRange_invariant_of_target` — EQ-THR-1 — axiom audit: pinned
- `Apgi.operatingRange_not_invariant` — EQ-THR-1 — axiom audit: pinned

## Open specification conflicts

- **KC-UNPINNED** (P1) unpinned_source: no sha256 for SRC-INNOV-GDOC

## Traceability

Source → `specification/parameters.json` → `Apgi/Spec.lean` (generated, hash-pinned) → `Apgi/Pilot.lean` theorem → `test_twins.py` twin → `apgi_ref.py` → empirical evidence (`epistemic-claims.json`).
