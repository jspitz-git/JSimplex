"""Audit the completed serial integration checks without launching Julia."""
import hashlib
import json
import math
from pathlib import Path
import sys
import tomllib

root = Path(__file__).resolve().parents[3]
raw = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
assert json.loads((raw / "current.json").read_text())["state"] == "finished"
pinned = json.loads((raw / "source.json").read_text())["source_sha256"]
h = hashlib.sha256()
for p in sorted([root / "Project.toml", *(root / "src").rglob("*.jl")],
                key=lambda p: str(p.relative_to(root))):
    h.update(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes())
assert h.hexdigest() == pinned
reports = {}
for name in ("targeted", "semantic", "greenbea", "runtime"):
    r = json.loads((raw / (name + "-process.json")).read_text())
    assert r["exit_code"] == 0 and r["source_unchanged"]
    assert r["source_sha256"] == pinned
    r["log_sha256"] = hashlib.sha256((raw / (name + ".log")).read_bytes()).hexdigest()
    reports[name] = r
for text in ("1381   1381", "419    419", "45     45", "5      5"):
    assert text in (raw / "targeted.log").read_text()
assert "15688  15688" in (raw / "semantic.log").read_text()
reference = json.loads((root / "diagnostics/numerical-guard-repair/results/greenbea-reference.json").read_text())["reference"]
for name, path, objective in (
    ("greenbea", raw / "greenbea/result.toml", reference["objective"]),
    ("runtime", raw / "runtime.toml", 51425691.76210442),
):
    r = tomllib.loads(path.read_text())
    assert r["status"] == "OPTIMAL" and r["original_primal_feasible"]
    assert math.isclose(r["objective"], objective, rel_tol=0, abs_tol=1e-4)
    if name == "greenbea":
        assert r["input_sha256"] == reference["sha256"]
    reports[name]["solve"] = {k: r[k] for k in (
        "status", "iterations", "objective", "original_primal_feasible", "seconds", "compile_seconds")}
    reports[name]["report_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"source_sha256": pinned, "targeted_assertions": 1850,
    "semantic_assertions": 15688, "jobs": reports}, indent=2) + "\n")
print("Integration audit passed")
