# APGI verification system

Machine-checked consistency, proofs, and numerical tests for the APGI
(Allostatic Precision-Gated Ignition) specification, measured against the APGI
Single Source of Truth (SSOT), framework v1.2.

A Lean proof establishes a consequence of a definition. It is never evidence
that APGI describes the brain. See `specification/epistemic-claims.json` and
`docs/assumption-inventory.md`.

## What is verified, and how

- **Proved (Lean 4, Mathlib):** bounds, monotonicity, invariance and conditional
  properties of the registered definitions, including bounded-state invariants of
  the full 15-step pipeline along every trajectory. `lake build --wfail` fails on
  any `sorry` or warning; every theorem's axiom list is pinned with `#guard_msgs`.
- **Conditional:** theorems that carry an explicit extra hypothesis (for example the
  upper bound on S needs a bound on S_inst; the Lyapunov bound is proved at loop gain 0).
- **Tested:** float64 twins of every theorem (Hypothesis), golden vectors at 50 digits,
  timestep-refinement convergence, NaN/Inf and overflow handling (TC-13), the §17
  parameter-recovery gate on synthetic data (TC-08), a cross-implementation distributional
  test (TC-19), and cross-checks of the pinned production code.
- **Assumed / empirical:** bridges and registered hypotheses (`specification/bridges.json`,
  CL-* claims). They are stated as hypotheses and never proved.

`docs/traceability-matrix.md` maps every requirement to its Lean theorems and tests;
`docs/assumption-inventory.md` lists every hypothesis those results rest on. Both are
generated from the registry.

## Layout

```
apgi-lean/
├── specification/            canonical registry: the single source of truth
│   ├── parameters.json       values, units, ranges, roles, source IDs, record status
│   ├── equations.json        equation IDs → Lean theorems → Python → tests
│   ├── requirements.json     SSOT requirement → proof/test traceability (REQ-*)
│   ├── bridges.json          bridge and measurement assumptions with falsifiers
│   ├── units.json            base dimensions (AU is its own dimension)
│   ├── epistemic-claims.json proved / tested / assumed / empirical / unresolved
│   ├── symbols.json, configurations.json, revisions.json
│   ├── source-manifest.json  corpus documents and their sha256 pins
│   └── known-conflicts.json  acknowledged open conflicts + corpus defect patterns
├── Apgi/
│   ├── Spec.lean             GENERATED from parameters.json (hash-pinned)
│   ├── Pilot.lean            pilot theorems, unit types, self-enforcing axiom audit
│   ├── Dynamics.lean         hazard, leaky integrator, NE clamp, allostatic step, Ψ, Πⁱ_eff, cusp iff
│   ├── Core.lean             minimal core: excess drive, m₀ = √(2/π), hard-threshold limit,
│   │                         read-out non-interference, exactly-once reset, cusp folds
│   ├── Extensions.lean       extension equations (prediction, DA, urgency, report, strata, loop gain, …)
│   ├── Coverage.lean         a Lean statement for every remaining registered equation
│   ├── Pipeline.lean         the full 15-step pipeline step, trajectory invariants, causal lag,
│   │                         hazard sampler measure, the rejected 17-step orders
│   ├── Strata.lean           L0–L4, geometric spacing and its limitations, τ_Π step rule,
│   │                         H10 as a hypothesis, decoupled Lyapunov bound
│   ├── Epistemic.lean        tier currencies, Tier-3 exit rule, κ calibration rule
│   ├── Stability.lean        TC-13: no division by zero on any trajectory, explicit drive bound,
│   │                         two-sided bound on S, EQ-STEP-1 gain bound
│   └── Identifiability.lean  TC-08a–c: margin, joint-scale and gain-product degeneracies of
│                             the event likelihood and the pipeline
├── docs/                     REMAINING-TASKS.md, REPRODUCIBILITY.md, VERIFICATION-REPORT.md,
│                             traceability-matrix.md, assumption-inventory.md (generated)
└── verification/
    ├── python/               reference implementation, generator, checker, extractor, tests
    ├── reports/              conflicts, extraction, proof status, release manifest, traceability.csv
    └── verify_all.ps1        the full local routine
```

## Run locally

See `docs/REPRODUCIBILITY.md` for the exact environment. In short:

```bash
lake exe cache get && lake build --wfail          # Lean (needs ~15 GB free)

pip install -r verification/python/requirements.txt
python verification/python/generate_lean.py --check
python verification/python/check_consistency.py
python verification/python/make_traceability.py --check
cd verification/python && python -m pytest -q --junitxml=../reports/junit.xml && cd ../..
python verification/python/make_report.py --junit verification/reports/junit.xml --lean-ok
python verification/python/extract_sources.py --corpus path/to/published-pdfs --corpus path/to/apgi-v-1-2 --write
                                                                 # verify evidence against sha256 pins
```

## Changing the specification

1. Edit `specification/*.json` (never the generated `Apgi/Spec.lean` or the generated docs).
2. `python verification/python/generate_lean.py` — proofs that break report a real change.
3. `python verification/python/make_traceability.py` — regenerates the matrix and inventory.
4. Resolving a conflict? Set its entry in `known-conflicts.json` to `"resolved"`;
   the checker fails on stale entries so the record cannot drift.

## License

Code: MIT (`LICENSE`). Registry records and documentation text: CC BY 4.0.
