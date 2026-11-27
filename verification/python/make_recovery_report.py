"""Run the full-pipeline recovery study (TC-08d–g, task 62b) and write
verification/reports/recovery-pipeline.json. Blocks run in parallel processes; each block
depends only on its own seed in fixtures/recovery_design.json, so the result does not depend
on scheduling. test_recovery_pipeline.py checks the committed report against the design and
the code (sha256) and asserts its conclusions."""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import recovery_pipeline as RP


def _block(name: str) -> tuple[str, dict]:
    return name, RP.run_block(RP.load_design(), name)


def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else round(float(x), 12)
    if isinstance(x, np.integer):
        return int(x)
    return x


def main() -> int:
    t0 = time.time()
    design = RP.load_design()
    with ProcessPoolExecutor(max_workers=len(design["blocks"])) as ex:
        done = dict(ex.map(_block, list(design["blocks"])))
    report = _clean(RP.run_study(design, done))
    report["numpy"] = np.__version__
    RP.REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {RP.REPORT_PATH} in {time.time() - t0:.0f}s")
    for b, r in report["blocks"].items():
        for k, v in r["parameters"].items():
            print(f"{b:12s} {k:13s} r={v['pearson_r']} err={v['median_range_scaled_error']:.3f} "
                  f"sd/prior={v['posterior_sd_over_prior_sd']:.2f} SBC p={v['sbc']['p']:.3f}")
        print(f"{b:12s} corr {r['posterior_correlation_median']} oos {r.get('out_of_sample')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
