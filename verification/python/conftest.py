import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Hypothesis: the `too_slow` health check measures wall-clock input generation, which fails
# spuriously on a loaded machine (seen 2026-11-26 while lake build ran). It does not affect
# what is tested, so it is suppressed for every profile; deadlines stay off as before.
from hypothesis import HealthCheck, settings  # noqa: E402

settings.register_profile("apgi", deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("apgi")
