"""Phase 2 consistency checker for the canonical APGI registry.

Detects: incomplete parameters, unresolved roles, candidate disagreements,
missing derivations, derived-value mismatches, unknown units/sources,
symbol collisions, unverifiable or violated theorem preconditions,
unpinned sources, and broken traceability (Lean/Python/test links).

Exit status
  0  every detected conflict is acknowledged as 'open' in known-conflicts.json
     and every 'open' entry is still detected.
  1  an UNACKNOWLEDGED conflict appeared, or an acknowledged one vanished
     (mark it 'resolved' in known-conflicts.json together with the fix).
Writes verification/reports/conflicts.json.
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from registry import ROOT, load, registry_hash  # noqa: E402

LEAN_DIR = ROOT / "Apgi"
REPORT = ROOT / "verification" / "reports" / "conflicts.json"


# ---------------------------------------------------------------- units ----
def dims(unit: str | None, units: dict) -> dict | None:
    if unit is None or unit not in units["units"]:
        return None
    return {k: v for k, v in units["units"][unit].items() if v}


# ------------------------------------------------------------ detectors ----
def detect(spec_dir: Path | None = None) -> list[dict]:
    if spec_dir is not None:
        import registry
        registry.SPEC = spec_dir
    P = load("parameters.json")["parameters"]
    E = load("equations.json")["equations"]
    U = load("units.json")
    S = load("source-manifest.json")["sources"]
    C = load("epistemic-claims.json")["claims"]
    src_ids = {s["id"]: s for s in S}
    pmap = {p["id"]: p for p in P}
    found: list[dict] = []

    def add(check, params, detail, severity="P1"):
        found.append({"check": check, "params": sorted(params), "detail": detail, "severity": severity})

    # parameter completeness, units, sources
    incomplete = []
    for p in P:
        if p.get("source") not in src_ids:
            add("unknown_source", [p["id"]], f"source {p.get('source')!r} not in source-manifest", "P0")
        if p.get("unit") is not None and dims(p["unit"], U) is None:
            add("unknown_unit", [p["id"]], f"unit {p['unit']!r} not in units.json", "P0")
        if p.get("unit") is None or (p.get("value") is None and p.get("range") is None) or not p.get("version"):
            incomplete.append(p["id"])
    if incomplete:
        add("incomplete_parameter", incomplete, "missing value/range, unit, or version")

    # Lean type contracts: the registry unit must match the Lean quantity type
    lean_types = {"Apgi.Kappa": "dimensionless", "Apgi.Threshold": "AU"}
    for p in P:
        lt = p.get("lean_type")
        if lt and dims(p.get("unit"), U) != dims(lean_types.get(lt), U):
            add("lean_type_mismatch", [p["id"]], f"unit {p.get('unit')!r} contradicts {lt} ({lean_types.get(lt)})", "P0")

    unresolved = [p["id"] for p in P if p.get("role") == "UNRESOLVED"]
    # group θ range bounds together, others separately
    theta = [i for i in unresolved if i.startswith("theta_operating")]
    if theta:
        add("unresolved_role", theta, "role must be 'state_invariant' or 'regime_label'", "P0")
    for i in unresolved:
        if i not in theta:
            add("unresolved_role", [i], "role is UNRESOLVED", "P0")

    for p in P:
        cands = p.get("candidates") or []
        if len({Fraction(c["value"]) for c in cands}) > 1:
            add("candidate_disagreement", [p["id"]],
                "; ".join(f"{c['source']}: {c['value']}" for c in cands), "P0")
        if p.get("approx") and not p.get("derivation"):
            add("missing_derivation", [p["id"]], "approximate value with no registered derivation")

    # symbol collisions
    seen: dict[str, str] = {}
    for p in P:
        sym = p.get("symbol")
        if sym in seen:
            add("symbol_collision", [seen[sym], p["id"]], f"symbol {sym!r} used twice", "P0")
        seen[sym] = p["id"]

    # derived values (exact constants -> high-precision check)
    if "landauer_310K" in pmap:
        L = pmap["landauer_310K"]
        kB, T = float(pmap["k_B"]["value"]), float(pmap["T_body"]["value"])
        truth = kB * T * math.log(2)
        reg = float(L["value"])
        rel = abs(reg - truth) / truth
        if rel > float(L.get("rel_tol", "1e-9")):
            add("derived_mismatch", ["landauer_310K"],
                f"registry {reg:.4e} J vs k_B·T·ln2 = {truth:.4e} J (rel err {rel:.2%})", "P0")

    # preconditions (plan edit C4)
    def bound(pid: str, side: str):
        p = pmap.get(pid)
        if p is None:
            return None
        if p.get("value") is not None:
            return Fraction(p["value"])
        r = p.get("range")
        if r and r.get(side) is not None:
            return Fraction(r[side])
        return None

    for eq in E:
        for pre in eq.get("preconditions", []):
            lhs_hi, lhs_lo = bound(pre["param"], "hi"), bound(pre["param"], "lo")
            if "param_rhs" in pre:
                rhs_lo, rhs_hi = bound(pre["param_rhs"], "lo"), bound(pre["param_rhs"], "hi")
                names = [pre["param"], pre["param_rhs"]]
            else:
                rhs_lo = rhs_hi = Fraction(pre["value"])
                names = [pre["param"]]
            if pre["op"] == "<=":
                if lhs_hi is None or rhs_lo is None:
                    add("precondition_unverifiable", names, f"{eq['id']}: {pre['theorem']} needs {pre['param']} ≤ {pre.get('param_rhs', pre.get('value'))}")
                elif not lhs_hi <= rhs_lo:
                    add("precondition_violated", names, f"{eq['id']}: registry allows {pre['param']}={lhs_hi} > {rhs_lo}", "P0")
            elif pre["op"] == ">=":
                if lhs_lo is None or rhs_hi is None:
                    add("precondition_unverifiable", names, f"{eq['id']}: {pre['theorem']} needs {pre['param']} ≥ {pre.get('value')}")
                elif not lhs_lo >= rhs_hi:
                    add("precondition_violated", names, f"{eq['id']}: registry allows {pre['param']}={lhs_lo} < {rhs_hi}", "P0")

    # dimensional consistency of the ignition exponent k·(S − θ)
    eq = next((e for e in E if e["id"] == "EQ-IGN-2"), None)
    if eq:
        dk, dS, dt = (dims(eq["units"][x], U) for x in ("k", "S", "theta"))
        if dS != dt or dk is None or any((dk.get(b, 0) + dS.get(b, 0)) for b in set(dk) | set(dS)):
            add("dimension_mismatch", ["k_sigmoid"], "k·(S−θ) is not dimensionless", "P0")

    # pinned sources
    used = {p["source"] for p in P} | {e["source"] for e in E}
    unpinned = sorted(s for s in used if s in src_ids and not src_ids[s].get("sha256") and src_ids[s]["kind"] != "external")
    if unpinned:
        add("unpinned_source", [], f"no sha256 for {', '.join(unpinned)}")

    # traceability
    found += traceability(E, C)
    return found


def lean_decls() -> set[str]:
    names = set()
    for f in LEAN_DIR.glob("*.lean"):
        for m in re.finditer(r"^(?:noncomputable\s+)?(?:theorem|def|structure|abbrev)\s+(\S+)", f.read_text(encoding="utf-8"), re.M):
            names.add("Apgi." + m.group(1))
    return names


def lean_theorems() -> set[str]:
    out = set()
    for f in LEAN_DIR.glob("*.lean"):
        out |= {"Apgi." + m for m in re.findall(r"^theorem\s+(\S+)", f.read_text(encoding="utf-8"), re.M)}
    return out


def audited() -> set[str]:
    out = set()
    for f in LEAN_DIR.glob("*.lean"):
        out |= set(re.findall(r"#guard_msgs in\n#print axioms (\S+)", f.read_text(encoding="utf-8")))
    return out


def py_functions(module: str) -> set[str]:
    tree = ast.parse((HERE / f"{module}.py").read_text(encoding="utf-8"))
    return {f"{module}.{n.name}" for n in tree.body if isinstance(n, ast.FunctionDef)}


def traceability(E, C) -> list[dict]:
    out = []
    decls, thms, aud = lean_decls(), lean_theorems(), audited()
    pyf = py_functions("apgi_ref") if (HERE / "apgi_ref.py").exists() else set()
    linked = set()
    for eq in E:
        for n in eq["lean"]:
            linked.add(n)
            if n not in decls:
                out.append({"check": "broken_link", "params": [], "detail": f"{eq['id']}: Lean {n} not found", "severity": "P0"})
        for n in eq["python"]:
            if n not in pyf:
                out.append({"check": "broken_link", "params": [], "detail": f"{eq['id']}: Python {n} not found", "severity": "P0"})
        for t in eq["tests"]:
            file, _, fn = t.partition("::")
            path = HERE / file
            if not path.exists() or (fn and f"def {fn}(" not in path.read_text(encoding="utf-8")):
                out.append({"check": "broken_link", "params": [], "detail": f"{eq['id']}: test {t} not found", "severity": "P0"})
    for t in sorted(thms - linked):
        out.append({"check": "orphan_theorem", "params": [], "detail": f"{t} is linked to no equation", "severity": "P0"})
    for t in sorted(thms - aud):
        out.append({"check": "unaudited_theorem", "params": [], "detail": f"{t} has no #guard_msgs axiom audit", "severity": "P0"})
    for c in C:
        if c["status"] == "proved":
            for ev in c["evidence"]:
                if ev not in thms:
                    out.append({"check": "broken_link", "params": [], "detail": f"{c['id']}: proved-by {ev} is not a Lean theorem", "severity": "P0"})
    return out


# ------------------------------------------------------------- matching ----
def reconcile(found: list[dict], known: list[dict]) -> tuple[list, list, list]:
    """Return (acknowledged, unacknowledged, stale_known)."""
    open_known = [k for k in known if k["status"] == "open"]
    ack, unack, hit = [], [], set()
    for f in found:
        match = next((k for k in open_known if k["check"] == f["check"]
                      and (not k["params"] or set(f["params"]) <= set(k["params"]))), None)
        if match:
            ack.append({**f, "known": match["id"]})
            hit.add(match["id"])
        else:
            unack.append(f)
    stale = [k for k in open_known if k["id"] not in hit]
    return ack, unack, stale


def run(spec_dir: Path | None = None, write: bool = True) -> dict:
    found = detect(spec_dir)
    known = load("known-conflicts.json")["conflicts"]
    ack, unack, stale = reconcile(found, known)
    report = {
        "registry_hash": registry_hash(),
        "acknowledged": ack,
        "unacknowledged": unack,
        "stale_known_conflicts": [k["id"] for k in stale],
        "ok": not unack and not stale,
    }
    if write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    r = run()
    for f in r["acknowledged"]:
        print(f"OPEN   [{f['known']}] {f['check']}: {f['detail']}")
    for f in r["unacknowledged"]:
        print(f"FAIL   {f['check']} {f['params']}: {f['detail']}")
    for k in r["stale_known_conflicts"]:
        print(f"STALE  {k}: no longer detected - mark it 'resolved' in known-conflicts.json")
    print(f"\n{len(r['acknowledged'])} open (acknowledged), {len(r['unacknowledged'])} unacknowledged, "
          f"{len(r['stale_known_conflicts'])} stale -> {'OK' if r['ok'] else 'FAIL'}")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
