# APGI verification system

Machine-checked consistency, proofs, and numerical tests for the APGI
(Allostatic Precision-Gated Ignition) specification.

A Lean proof establishes a consequence of a definition. It is never evidence
that APGI describes the brain. See `specification/epistemic-claims.json`.

## Layout

```
apgi/                         Lean project root (lakefile.toml, lean-toolchain)
├── specification/            canonical registry: the single source of truth
│   ├── parameters.json       values, units, ranges, roles, source IDs
│   ├── equations.json        equation IDs → Lean theorems → Python → tests
│   ├── units.json            base dimensions (AU is its own dimension)
│   ├── epistemic-claims.json proved / tested / assumed / empirical / unresolved
│   ├── source-manifest.json  corpus documents and their sha256 pins
│   └── known-conflicts.json  acknowledged open conflicts + corpus defect patterns
├── Apgi/
│   ├── Spec.lean             GENERATED from parameters.json (hash-pinned)
│   └── Pilot.lean            theorems, unit types, self-enforcing axiom audit
└── verification/
    ├── python/               generator, checker, extractor, tests, report
    └── reports/              conflicts.json, proof-status.json, verification-report.md
```

## Run locally

```bash
lake exe cache get && lake build --wfail          # Lean (needs ~15 GB free)

pip install -r verification/python/requirements.txt
python verification/python/generate_lean.py --check
python verification/python/check_consistency.py
cd verification/python && python -m pytest -q --junitxml=../reports/junit.xml && cd ../..
python verification/python/make_report.py --junit verification/reports/junit.xml --lean-ok
python verification/python/extract_sources.py path/to/corpus/   # scan documents
```

## Changing the specification

1. Edit `specification/*.json` (never the generated `Apgi/Spec.lean`).
2. `python verification/python/generate_lean.py` — proofs that break report a real change.
3. Resolving a conflict? Set its entry in `known-conflicts.json` to `"resolved"`;
   the checker fails on stale entries so the record cannot drift.
