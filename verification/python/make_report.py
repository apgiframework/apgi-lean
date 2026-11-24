"""Build verification/reports/{proof-status.json, verification-report.md}.

Inputs (all optional; missing inputs are reported as 'not run', never as pass):
  --junit PATH      pytest --junitxml output
  --lean-log PATH   log of `lake build --wfail`; pass --lean-ok if it exited 0
Every pilot criterion is computed from artefacts, not asserted.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_consistency as CC  # noqa: E402
from registry import ROOT, load, registry_hash  # noqa: E402

REPORTS = ROOT / "verification" / "reports"


def junit(path: str | None) -> dict[str, str]:
    """test id -> 'passed' | 'failed' | 'skipped'."""
    if not path or not Path(path).exists():
        return {}
    out = {}
    for tc in ET.parse(path).iter("testcase"):
        file = tc.get("classname", "").split(".")[-1] + ".py"
        name = re.sub(r"\[.*\]$", "", tc.get("name", ""))
        state = "failed" if tc.find("failure") is not None or tc.find("error") is not None else (
            "skipped" if tc.find("skipped") is not None else "passed")
        key = f"{file}::{name}"
        if out.get(key) != "failed":
            out[key] = state if out.get(key) in (None, "passed") else out[key]
    return out


def spec_lean_hash() -> str | None:
    p = ROOT / "Apgi" / "Spec.lean"
    m = re.search(r'def specHash : String := "([0-9a-f]+)"', p.read_text(encoding="utf-8")) if p.exists() else None
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit")
    ap.add_argument("--lean-log")
    ap.add_argument("--lean-ok", action="store_true")
    a = ap.parse_args()

    tests = junit(a.junit)
    conflicts = CC.run(write=True)
    E = load("equations.json")["equations"]
    C = load("epistemic-claims.json")["claims"]
    P = load("parameters.json")["parameters"]
    thms, aud = sorted(CC.lean_theorems()), CC.audited()
    rhash, lhash = registry_hash(), spec_lean_hash()
    lean_state = "passed" if a.lean_ok else ("failed" if a.lean_log else "not run")

    def tstate(t: str) -> str:
        if not tests:
            return "not run"
        hits = [v for k, v in tests.items() if k == t or ("::" not in t and k.startswith(t + "::"))]
        return "failed" if "failed" in hits else ("passed" if hits else "missing")

    theorems = [{"name": t, "audited": t in aud, "lean": lean_state,
                 "equations": [e["id"] for e in E if t in e["lean"]],
                 "registry_hash": lhash} for t in thms]
    claims = []
    for c in C:
        ev = [{"ref": r, "state": (lean_state if r in thms else tstate(r))} for r in c["evidence"]]
        ok = bool(ev) and all(e["state"] == "passed" for e in ev)
        status = c["status"] if ok or c["status"] in ("assumed", "unresolved") else f"{c['status']} (unconfirmed: evidence {', '.join(e['state'] for e in ev) or 'missing'})"
        claims.append({**c, "evidence_state": ev, "reported_status": status})

    golden = [v for k, v in tests.items() if k.startswith("test_golden_vectors.py")]
    conflict_tests = [v for k, v in tests.items() if k.startswith("test_conflicts.py")]
    incomplete = [f for f in conflicts["acknowledged"] + conflicts["unacknowledged"] if f["check"] == "incomplete_parameter"]
    empirical_from_proof = [c["id"] for c in C if c["status"] == "empirically-supported" and any(r in thms for r in c["evidence"])]

    unpinned = [f for f in conflicts["acknowledged"] + conflicts["unacknowledged"] if f["check"] == "unpinned_source"]
    c1_parts = [f"{len(incomplete[0]['params'])} incomplete parameter(s)" if incomplete else "all parameters complete"]
    if unpinned:
        c1_parts.append(unpinned[0]["detail"])
    criteria = [
        ("Every canonical parameter has a source identifier, unit, version, and documented range",
         not incomplete and not unpinned, "; ".join(c1_parts)),
        ("Known discrepancies produce explicit failures",
         bool(conflict_tests) and all(v == "passed" for v in conflict_tests) and conflicts["ok"],
         f"{len(conflicts['acknowledged'])} open conflicts tracked; seeded suite {'passed' if conflict_tests and all(v == 'passed' for v in conflict_tests) else 'not run/failed'}"),
        ("Lean theorems compile without sorry or unapproved axioms",
         a.lean_ok and all(t["audited"] for t in theorems),
         f"lake build --wfail: {lean_state}; {sum(t['audited'] for t in theorems)}/{len(theorems)} theorems axiom-audited via #guard_msgs"),
        ("Mathematical results are linked to exact specification revisions",
         lhash == rhash and not any(f["check"] in ("orphan_theorem", "broken_link") for f in conflicts["unacknowledged"]),
         f"Spec.lean hash {'matches' if lhash == rhash else 'DOES NOT match'} registry {rhash[:12]}"),
        ("Python tests pass the APGI numerical tolerances (1e-9)",
         bool(golden) and all(v == "passed" for v in golden),
         f"{sum(v == 'passed' for v in golden)}/{len(golden)} golden-vector tests passed" if golden else "not run"),
        ("Continuous integration produces a reproducible verification report",
         os.environ.get("GITHUB_ACTIONS") == "true",
         "generated in GitHub Actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "generated locally (CI run required)"),
        ("No mathematical proof is described as empirical confirmation of APGI",
         not empirical_from_proof,
         "no claim cites a Lean theorem as empirical evidence" if not empirical_from_proof else f"violations: {empirical_from_proof}"),
    ]

    status = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "registry_hash": rhash, "spec_lean_hash": lhash,
        "spec_version": load("parameters.json")["spec_version"],
        "lean_build": lean_state, "python_tests": {"passed": sum(v == "passed" for v in tests.values()),
                                                   "failed": sum(v == "failed" for v in tests.values()),
                                                   "total": len(tests)},
        "theorems": theorems, "claims": claims,
        "pilot_criteria": [{"criterion": c, "met": bool(m), "evidence": e} for c, m, e in criteria],
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "proof-status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    met = sum(c["met"] for c in status["pilot_criteria"])
    L = [
        "# APGI Verification Report", "",
        f"- Generated: {status['generated']}",
        f"- Spec version: {status['spec_version']} · registry hash `{rhash[:16]}…`",
        f"- Lean build (`lake build --wfail`): **{lean_state}**",
        f"- Python test functions: **{status['python_tests']['passed']} passed, {status['python_tests']['failed']} failed** of {status['python_tests']['total']} (parametrised cases collapsed)",
        f"- Pilot criteria met: **{met} of 7**", "",
        "> A Lean proof establishes a consequence of a definition. It is not evidence that APGI describes the brain.", "",
        "## Pilot criteria", "",
    ]
    for c in status["pilot_criteria"]:
        L.append(f"- {'✅' if c['met'] else '❌'} **{c['criterion']}** — {c['evidence']}")
    L += ["", "## Claims by epistemic status", ""]
    for lvl in ("proved", "tested", "assumed", "empirically-supported", "unresolved"):
        group = [c for c in claims if c["status"] == lvl]
        if group:
            L.append(f"### {lvl.capitalize()}")
            for c in group:
                refs = ", ".join(f"`{e['ref']}` ({e['state']})" for e in c["evidence_state"]) or "no evidence registered"
                L.append(f"- **{c['id']}** {c['text']} — {refs}" + ("" if c["reported_status"] == c["status"] else f" — ⚠ {c['reported_status']}"))
            L.append("")
    L += ["## Theorems", ""]
    for t in theorems:
        L.append(f"- `{t['name']}` — {', '.join(t['equations']) or 'UNLINKED'} — axiom audit: {'pinned' if t['audited'] else 'MISSING'}")
    L += ["", "## Open specification conflicts", ""]
    for f in conflicts["acknowledged"]:
        L.append(f"- **{f['known']}** ({f['severity']}) {f['check']}: {f['detail']}")
    for f in conflicts["unacknowledged"]:
        L.append(f"- ❌ **UNACKNOWLEDGED** {f['check']} {f['params']}: {f['detail']}")
    for k in conflicts["stale_known_conflicts"]:
        L.append(f"- ⚠ **{k}** no longer detected — mark resolved")
    L += ["", "## Traceability", "",
          "Source → `specification/parameters.json` → `Apgi/Spec.lean` (generated, hash-pinned) → `Apgi/Pilot.lean` theorem → `test_twins.py` twin → `apgi_ref.py` → empirical evidence (`epistemic-claims.json`).", ""]
    (REPORTS / "verification-report.md").write_text("\n".join(L), encoding="utf-8")
    print(f"pilot criteria met: {met}/7 · report written to verification/reports/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
