"""The generated traceability matrix, assumption inventory and CSV match the current registry (TC-21)."""
from pathlib import Path

import make_traceability as MT


def test_generated_traceability_files_are_current():
    stale = [p for p, t in MT.build().items()
             if not Path(p).exists() or Path(p).read_text(encoding="utf-8").replace("\r\n", "\n") != t]
    assert stale == [], f"run python verification/python/make_traceability.py: {stale}"
