"""Verify the recorded model reports, including independent reference objectives."""
from pathlib import Path
import hashlib
import json
import math
import tomllib

root = Path(__file__).resolve().parents[3]
folder = root / "diagnostics/dual-core-policy/results"
source_hash = hashlib.sha256((root / "src/dual_simplex.jl").read_bytes()).hexdigest()
reports = {mode: tomllib.loads((folder / f"{mode}.toml").read_text())
           for mode in ("pk1", "medium", "external")}
for report in reports.values():
    assert report["source_sha256"] == source_hash
    assert report["julia_threads"] == report["blas_threads"] == 1
    for case in report["cases"]:
        assert case["maximum_effective_interval"] <= 80
        if case["pricing_requested"] != "dantzig":
            assert "dantzig" not in case["pricing_seen"]
        assert case["last_observed_point"]["row_consistent"]

pk1 = reports["pk1"]["cases"]
assert len(pk1) == 8
for case in pk1:
    if case["pricing_requested"] == "steepest_edge":
        assert case["status"] == "ITERATION_LIMIT" and case["iterations"] == 2000
    else:
        assert case["status"] == "OPTIMAL" and case["original_primal_certified"]
        assert math.isclose(case["objective"], 0, abs_tol=1e-7)

entries = tomllib.loads((root / "diagnostics/basis-selective-preparation/reproduce/external-inputs.toml").read_text())["cases"]
references = {entry["sha256"]: entry for entry in entries}
external = reports["external"]["cases"]
assert len(external) == 16
reference_checks = []
for case in external:
    expected = references[case["sha256"]]
    assert case["status"] == "OPTIMAL" and case["original_primal_certified"]
    assert math.isclose(case["objective"], expected["objective"], rel_tol=1e-8, abs_tol=1e-7)
    reference_checks.append({"id": expected["id"], "manager": case["manager"],
                             "objective_matches": True, "original_primal_certified": True})

medium, = reports["medium"]["cases"]
assert medium["status"] in ("TIME_LIMIT", "OPTIMAL")
assert medium["time_limit"] == 300.0
validation = {"source_sha256": source_hash, "pk1_cases": len(pk1),
              "external_reference_checks": reference_checks,
              "medium_status": medium["status"], "medium_iterations": medium["iterations"],
              "medium_last_point": medium["last_observed_point"],
              "report_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                                  for f in folder.glob("*.toml")}}
(folder / "model-validation.json").write_text(json.dumps(validation, indent=2) + "\n")
print("Verified 8 pk1 reports, 16 external reference optima, and the bounded medium report.")
