# APGI Verification Report

- Generated: 2026-11-24T04:39:31+00:00
- Spec version: 0.1.0 · registry hash `020a8b9b1d3fca91…`
- Lean build (`lake build --wfail`): **passed**
- Python test functions: **38 passed, 0 failed** of 38 (parametrised cases collapsed)
- Pilot criteria met: **5 of 7**

> A Lean proof establishes a consequence of a definition. It is not evidence that APGI describes the brain.

## Pilot criteria

- ❌ **Every canonical parameter has a source identifier, unit, version, and documented range** — 5 incomplete parameter(s); sources unpinned
- ✅ **Known discrepancies produce explicit failures** — 7 open conflicts tracked; seeded suite passed
- ✅ **Lean theorems compile without sorry or unapproved axioms** — lake build --wfail: passed; 11/11 theorems axiom-audited via #guard_msgs
- ✅ **Mathematical results are linked to exact specification revisions** — Spec.lean hash matches registry 020a8b9b1d3f
- ✅ **Python tests pass the APGI numerical tolerances (1e-9)** — 5/5 golden-vector tests passed
- ❌ **Continuous integration produces a reproducible verification report** — generated locally (CI run required)
- ✅ **No mathematical proof is described as empirical confirmation of APGI** — no claim cites a Lean theorem as empirical evidence

## Claims by epistemic status

### Proved
- **CL-1** Raising θ cannot make ignition easier at fixed S. — `Apgi.ignites_antitone_threshold` (passed), `Apgi.ignitionProb_antitone_threshold` (passed)
- **CL-2** The clamped update preserves the 0.5 AU floor. — `Apgi.clampedUpdate_floor` (passed)
- **CL-3** [2, 8] AU is not an invariant of the clamped update for unrestricted targets; it is invariant when targets lie in [2, 8] and 0 ≤ g ≤ 1. — `Apgi.operatingRange_not_invariant` (passed), `Apgi.operatingRange_invariant_of_target` (passed)
- **CL-4** a < 0 is necessary for cusp bistability (and hence hysteresis). — `Apgi.cusp_unique_equilibrium` (passed)
- **CL-6** Forward-Euler relaxation stays in bounds when Δt ≤ τ. — `Apgi.euler_step_mem_Icc` (passed)

### Tested
- **CL-5** a < 0 and 4a³ + 27θ² < 0 together are sufficient for three equilibria. — `test_twins.py::test_cusp_discriminant` (passed)

### Assumed
- **CL-8** κ ≈ 1,700 (metabolic overhead relative to Landauer). — no evidence registered

### Unresolved
- **CL-7** APGI's hysteresis prediction (Innovation 4) holds in human data. — no evidence registered

## Theorems

- `Apgi.clampedUpdate_floor` — EQ-THR-1 — axiom audit: pinned
- `Apgi.convex_update_mem_Icc` — EQ-UPD-1 — axiom audit: pinned
- `Apgi.cuspV_hasDerivAt` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_two_equilibria_witness` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.cusp_unique_equilibrium` — EQ-CUSP-1 — axiom audit: pinned
- `Apgi.euler_step_mem_Icc` — EQ-EULER-1 — axiom audit: pinned
- `Apgi.ignites_antitone_threshold` — EQ-IGN-1 — axiom audit: pinned
- `Apgi.ignites_monotone_precision` — EQ-PREC-1 — axiom audit: pinned
- `Apgi.ignitionProb_antitone_threshold` — EQ-IGN-2 — axiom audit: pinned
- `Apgi.operatingRange_invariant_of_target` — EQ-THR-1 — axiom audit: pinned
- `Apgi.operatingRange_not_invariant` — EQ-THR-1 — axiom audit: pinned

## Open specification conflicts

- **KC-INCOMPLETE** (P1) incomplete_parameter: missing value/range, unit, or version
- **KC-THETA-ROLE** (P0) unresolved_role: role must be 'state_invariant' or 'regime_label'
- **KC-LAMBDA** (P0) unresolved_role: role is UNRESOLVED
- **KC-KAPPA-DERIV** (P1) missing_derivation: approximate value with no registered derivation
- **KC-BF10-0B** (P0) candidate_disagreement: SRC-PRED-REG: 100; SRC-OSF: 10
- **KC-PRECOND-EULER** (P1) precondition_unverifiable: EQ-EULER-1: Apgi.euler_step_mem_Icc needs dt ≤ tau_theta
- **KC-UNPINNED** (P1) unpinned_source: no sha256 for SRC-DYN, SRC-INNOV-GDOC, SRC-NOTATION, SRC-OSF, SRC-THERMO

## Traceability

Source → `specification/parameters.json` → `Apgi/Spec.lean` (generated, hash-pinned) → `Apgi/Pilot.lean` theorem → `test_twins.py` twin → `apgi_ref.py` → empirical evidence (`epistemic-claims.json`).
