# Reproducing the APGI verification

This file covers SSOT §28.3 deliverables 2, 9 and 10 for this repository: how to rebuild
every proof, rerun every test and check every pin from a clean clone. It does not cover the
empirical deliverables (recovery data, analysis manifests, consent records), which live with
the protocols, not here.

## 1. Environment

- Lean toolchain: `leanprover/lean4:v4.36.0` (file `lean-toolchain`); Mathlib `v4.36.0`
  (pinned in `lake-manifest.json`). Install with elan; `lake exe cache get` downloads the
  Mathlib build cache. A cold build without the cache takes hours.
- Disk: about 15 GB for `.lake`. Memory: about 4 GB free for the largest module
  (`Apgi/Pipeline.lean`); on a machine with less free memory the build slows down sharply.
- Python: 3.12 for the registry job (`verification/python/requirements.txt` pins pytest,
  hypothesis, numpy, mpmath); 3.11 with `apgi-validation/requirements.lock` for the
  apgi-validation cross-check. The production cross-check also needs
  `structlog`, `pydantic` and `scipy` (see the CI workflow).
- Production repositories, checked out at the commits recorded in
  `specification/known-conflicts.json` (`production.commit`, `production_secondary.commit`).

## 2. From a clean clone

```bash
git clone https://github.com/apgiframework/apgi-lean && cd apgi-lean
lake exe cache get
lake build --wfail                                   # every theorem, every axiom pin

python -m pip install -r verification/python/requirements.txt
python verification/python/generate_lean.py --check  # Spec.lean matches the registry hash
python verification/python/check_consistency.py      # 0 open, 0 unacknowledged, 0 stale
python verification/python/make_traceability.py --check

git clone https://github.com/apgiframework/apgi-implementation ../apgi-implementation
git -C ../apgi-implementation checkout "$(python -c "import json;print(json.load(open('specification/known-conflicts.json'))['production']['commit'])")"
cd verification/python
APGI_IMPL_PATH=../../../apgi-implementation python -m pytest -q -rxs
```

The apgi-validation cross-check runs in a separate interpreter (both production packages ship
a top-level `utils`):

```bash
APGI_VALIDATION_PATH=/path/to/apgi-validation python -m pytest -q -rxs test_production_validation.py
```

On Windows, `verification/verify_all.ps1` runs the whole routine, including source extraction,
and writes `.verify.log`.

## 3. Source pins (needs the corpus)

The v1.1 PDFs and the v1.2 drafts are not in this public repository. `source-manifest.json`
pins each by sha256; `extract_sources.py --corpus DIR --write` locates the files by hash and
re-verifies every evidence quote of `parameters.json` and `bridges.json`, writing
`verification/reports/extraction.json`. `check_consistency.py` then fails on any registry
record that changed after its last verified extraction. Without the corpus, CI trusts the
committed extraction report and checks that it matches the current registry by hash.

## 4. Determinism

- Golden vectors (`verification/python/golden_vectors.json`) are computed at 50 significant
  digits with mpmath by `make_golden.py`; the seeded trajectories store their inputs and
  uniform draws, so they do not depend on any RNG implementation (TC-18, TC-19).
- Hypothesis property tests use the profiles in `conftest.py` and `test_twins.py`;
  the `too_slow` health check is suppressed because it measures wall-clock time only.
- `verification/reports/release-manifest.json` records the sha256 of every registry, Lean and
  golden-vector file, the three repository commits, licenses and the toolchain.

## 5. What a green run means

A green run means: every Lean theorem elaborates with only `propext`, `Classical.choice` and
`Quot.sound`; every registry record is complete, typed and traced; every evidence quote was
found in its pinned source; and the reference and pinned production code satisfy the same
statements numerically. It does not mean that APGI describes the brain (SSOT §32).
