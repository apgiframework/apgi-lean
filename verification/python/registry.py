"""Shared access to the canonical APGI registry (specification/*.json)."""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "specification"
SPEC_FILES = ("parameters.json", "equations.json", "units.json",
              "epistemic-claims.json", "source-manifest.json", "known-conflicts.json",
              "symbols.json", "configurations.json", "revisions.json",
              "bridges.json", "requirements.json")


def load(name: str) -> dict:
    return json.loads((SPEC / name).read_text(encoding="utf-8"))


def registry_hash() -> str:
    """SHA-256 over the canonical spec files, newline-normalised so that
    Windows and Linux checkouts hash identically."""
    h = hashlib.sha256()
    for name in SPEC_FILES:
        p = SPEC / name
        if p.exists():
            h.update(name.encode())
            h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def params() -> dict[str, dict]:
    return {p["id"]: p for p in load("parameters.json")["parameters"]}


def exact(value: str) -> Fraction:
    """Decimal string -> exact rational (no float rounding)."""
    return Fraction(value)
