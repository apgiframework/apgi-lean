"""The generated traceability matrix, assumption inventory and CSV match the current registry (TC-21)."""
from pathlib import Path

import make_traceability as MT


def test_generated_traceability_files_are_current():
    stale = [p for p, t in MT.build().items()
             if not Path(p).exists() or Path(p).read_text(encoding="utf-8").replace("\r\n", "\n") != t]
    assert stale == [], f"run python verification/python/make_traceability.py: {stale}"


def test_ssot_generated_parts_are_current():
    """TC-21 / D10: the registry-derived parts of the SSOT (header registry row, golden-vector
    paragraph, Lean status table, theorem and claim registers, open targets) match the registry.
    The v1.2 SSOT draft is not under version control, so this runs only where a copy exists."""
    import pytest

    import make_ssot_tables as MS

    copies = [p for p in MS.SSOT_PATHS if p.exists()]
    if not copies:
        pytest.skip("no SSOT copy present (docs/apgi-v-1-2/ is not under version control)")
    F = MS.facts()
    for p in copies:
        text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        assert set(MS.BLOCKS) <= MS.markers_present(text), f"{p}: generated-block markers missing"
        assert MS.render(text, F) == text, f"{p} is stale: run python verification/python/make_ssot_tables.py"
    if MS.SSOT_PATHS[0].exists():
        assert MS.pin_current(MS.SSOT_PATHS[0]), "SRC-SSOT-V12D pin is stale: run make_ssot_tables.py"
