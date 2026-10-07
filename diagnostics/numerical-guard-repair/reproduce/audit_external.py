"""Audit the completed external validation without starting a numerical process."""
import json
import sys
import tomllib
from pathlib import Path

raw = Path(sys.argv[1])
output = Path(sys.argv[2])
report = tomllib.loads((raw / "external.toml").read_text())
cases = report["cases"]
keys = {(c["id"], c["backend"], c["algorithm"], c["basis_update"]) for c in cases}
assert len(cases) == len(keys) == 100
assert all(c["status"] == "OPTIMAL" and c["original_primal_certified"] and
           c["objective_matches"] for c in cases)
processes = {name: json.loads((raw / (name + "-process.json")).read_text())
             for name in ("semantic", "external")}
assert all(p["exit_code"] == 0 and p["source_unchanged"] for p in processes.values())
assert len({p["source_sha256"] for p in processes.values()}) == 1
output.write_text(json.dumps({"cases": len(cases), "unique_combinations": len(keys),
    "all_optimal": True, "all_original_primal_certified": True,
    "all_reference_objectives_matched": True, "processes": processes}, indent=2) + "\n")
print("Audited 100 unique optimal, feasible, reference-matching external solves")
