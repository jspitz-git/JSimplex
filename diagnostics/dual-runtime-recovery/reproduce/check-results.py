"""Independently check recorded endpoints; time limits are not successes."""
from pathlib import Path
import json
import math
import tomllib

root = Path(__file__).resolve().parents[1] / "results"
def read(name):
    with (root / name).open("rb") as stream:
        return tomllib.load(stream)

baseline = read("baseline.toml")
fixed = read("fixed.toml")
replay = read("replay.toml")
external = read("external.toml")
assert baseline["status"] == "NUMERICAL_ERROR"
assert "bounded feasibility recovery exhausted" in baseline["message"]
assert fixed["status"] == "OPTIMAL" and fixed["original_primal_certified"]
assert math.isclose(fixed["objective"], 5.142569176210421e7, rel_tol=1e-10, abs_tol=1e-7)
assert "Restarting simplex on original LP" not in (root / "fixed.log").read_text()
assert replay["status"] == "OPTIMAL"
assert replay["primal_certified"] and replay["optimality_certified"]
assert replay["original_costs"] and replay["original_bounds"]
assert len(external["cases"]) == 56
for case in external["cases"]:
    assert case["status"] == "OPTIMAL" and case["original_primal_certified"]
    assert math.isclose(case["objective"], case["reference_objective"], rel_tol=1e-8, abs_tol=1e-7)
print(json.dumps({"baseline_failure_reproduced": True, "runtime_optimal": True,
                  "runtime_original_primal_certified": True, "runtime_restarted": False,
                  "snapshot_continuation_certified": True, "external_optimal_cases": 56}, indent=2))
