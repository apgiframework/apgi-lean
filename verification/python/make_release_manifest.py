"""Write verification/reports/release-manifest.json (SSOT §24 deliverables 2 and 10; B-11).

Records the three repositories with their pinned commits and licenses, the text/record license,
and SHA-256 of every registry file, Lean module and golden-vector file in this repository.
The v1.2 DOI and the release tag are filled in when the Zenodo release is minted (task 25)."""
import hashlib
import json
from pathlib import Path

from registry import ROOT, SPEC_FILES, load, registry_hash


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    kc = load("known-conflicts.json")
    params = load("parameters.json")
    files = [ROOT / "specification" / n for n in SPEC_FILES]
    files += sorted((ROOT / "Apgi").glob("*.lean")) + [ROOT / "Apgi.lean", ROOT / "verification" / "python" / "golden_vectors.json"]
    m = {
        "schema": "apgi-release-manifest/1",
        "framework_version": "APGI v1.2 (working draft)",
        "spec_version": params["spec_version"],
        "registry_hash": registry_hash(),
        "release": {"tag": None, "doi": None, "note": "Filled in when the v1.2 Zenodo release is minted (task 25, B-11)."},
        "licenses": {"text_and_records": "CC-BY-4.0", "data": "consent-compatible access terms (per dataset)"},
        "repositories": [
            {"name": "apgiframework/apgi-lean", "commit": "HEAD of main at release", "license": "MIT", "license_file": "LICENSE"},
            {"name": kc["production"]["repository"], "commit": kc["production"]["commit"], "license": "MIT", "license_file": "LICENSE"},
            {"name": kc["production_secondary"]["repository"], "commit": kc["production_secondary"]["commit"], "license": "MIT", "license_file": "LICENSE"},
        ],
        "toolchain": (ROOT / "lean-toolchain").read_text(encoding="utf-8").strip(),
        "files": {str(f.relative_to(ROOT)).replace("\\", "/"): sha(f) for f in files if f.exists()},
    }
    out = ROOT / "verification" / "reports" / "release-manifest.json"
    out.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
