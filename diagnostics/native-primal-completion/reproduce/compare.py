"""Compare numerical trajectories, allowing the corrected completion snapshots."""
import json
from pathlib import Path
import sys
import tomllib

root = Path(__file__).resolve().parents[2]
current = Path(sys.argv[1])
fields = ("input_sha256", "status", "objective", "primal_sha256", "trace_sha256",
          "iterations", "refactorizations", "original_primal_certified", "counts")
report = {}
for name, reference in (("fast0507-primal", "current-fast-primal-trace"),
                        ("runtime-dual", "current-runtime-dual")):
    old = tomllib.loads((root / "simplex-kernel-performance/results" / (reference + ".toml")).read_text())
    new = tomllib.loads((current / (name + ".toml")).read_text())
    checks = {key: old[key] == new[key] for key in fields}
    assert all(checks.values()), (name, checks)
    report[name] = checks
print(json.dumps(report, indent=2))
