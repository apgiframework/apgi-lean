"""Registry integrity: schema completeness, units, and traceability."""
import check_consistency as CC
import registry


def test_every_parameter_has_source_version_and_definition():
    src = {s["id"] for s in registry.load("source-manifest.json")["sources"]}
    for p in registry.load("parameters.json")["parameters"]:
        assert p["source"] in src, p["id"]
        assert p["version"] and p["definition"], p["id"]


def test_units_are_declared():
    U = registry.load("units.json")
    for p in registry.load("parameters.json")["parameters"]:
        if p["unit"] is not None:
            assert CC.dims(p["unit"], U) is not None, p["id"]


def test_ignition_exponent_dimensionless():
    U = registry.load("units.json")
    k, S = CC.dims("1/AU", U), CC.dims("AU", U)
    assert all(k.get(b, 0) + S.get(b, 0) == 0 for b in set(k) | set(S))


def test_au_never_equals_a_physical_unit():
    U = registry.load("units.json")
    au = CC.dims("AU", U)
    assert all(CC.dims(u, U) != au for u in U["units"] if u != "AU")


def test_every_lean_theorem_traced_and_audited():
    E = registry.load("equations.json")["equations"]
    C = registry.load("epistemic-claims.json")["claims"]
    problems = CC.traceability(E, C)
    assert problems == [], problems
