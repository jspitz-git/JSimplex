"""Check diagnostic provenance, complementary certificates and candidate results."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / "diagnostics/adaptive-degeneracy/results/coupled-point"

def read(name):
    return tomllib.loads((results / name).read_text())

def source_digest(directory):
    digest = hashlib.sha256()
    files = [Path("Project.toml")] + [p.relative_to(directory) for p in (directory / "src").rglob("*.jl")]
    for path in sorted(files, key=lambda p: p.as_posix()):
        digest.update((path.as_posix() + "\0").encode())
        digest.update((directory / path).read_bytes())
    return digest.hexdigest()

assert source_digest(root) == "c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc"
capture = read("runtime-coupled.toml")
assert capture["iterations"] == 8464 and capture["status"] == "NUMERICAL_ERROR"
assert capture["refactorizations"] == 1791
inspection = read("runtime-coupled-inspection.toml")
expected = {"before": (0, 0, 0), "reconstructed": (3, 2, 0),
            "prediction": (0, 1, 0), "balanced": (0, 1, 0),
            "correction": (3, 1, 0), "rounded": (0, 1, 0)}
for point in inspection["records"]:
    counts = (len(point["bounds"]), sum(not row["model_ok"] for row in point["rows"]),
              sum(not row["equation_ok"] for row in point["rows"]))
    assert counts == expected.pop(point["tag"])
assert not expected
assert "ROUNDING_REPLAY completed=true same_point=true" in (results / "runtime-coupled-inspection.log").read_text()
probes = read("runtime-coupled-probes.toml")["records"]
assert all(p["nonbasic_unchanged"] for p in probes)
blend = {p["prediction_fraction"]: p["certified"] for p in probes if p["tag"] == "blend"}
assert blend == {0.0: False, 0.25: False, 0.5: True, 0.75: True, 1.0: False}
assert next(p for p in probes if p["tag"] == "adjacent_basic_9126")["certified"]
assert all(not p["accepted"] for p in probes if p["tag"].startswith("correct_"))
candidate = json.loads((results / "candidate.json").read_text())
assert hashlib.sha256((reproduce / candidate["patch"]).read_bytes()).hexdigest() == candidate["patch_sha256"]
for patch, expected_digest in (("working-row-rounded.patch", capture["production_sha256"]),
                                (candidate["patch"], candidate["production_sha256"])):
    with tempfile.TemporaryDirectory(prefix="jsimplex-coupled-evidence-") as temporary:
        directory = Path(temporary)
        shutil.copy2(root / "Project.toml", directory)
        shutil.copytree(root / "src", directory / "src")
        subprocess.run(["git", "apply", "--unidiff-zero", str(reproduce / patch)], cwd=directory, check=True)
        assert source_digest(directory) == expected_digest
run = read("runtime-coupled-candidate.toml")
assert run["production_sha256"] == candidate["production_sha256"]
assert run["status"] == "NUMERICAL_ERROR" and run["iterations"] == 8589
assert run["refactorizations"] == 1793 and run["seconds"] < 300
assert run["events"].get("primal_correction_balanced", 0) == 1
assert run["events"]["primal_bound_roundoff_corrected"] == 5
for report in (capture, run):
    assert report["time_limit"] == 300
    assert report["julia_threads"] == report["blas_threads"] == 1
    assert not report["original_retry_enabled"]
    assert report["events"].get("precision_boost", 0) == 0
    assert not report["weak_pivot_preference"]
    enabled = {name for name, value in report["policy"].items() if value}
    assert enabled == {"phase_one", "adaptive_stalling", "adaptive_pricing",
                       "adaptive_primal_perturbation", "adaptive_dual_perturbation"}
local = json.loads((results / "local-artifacts.json").read_text())
if (root / local["directory"]).exists():
    for name, digest in local["sha256"].items():
        assert hashlib.sha256((root / local["directory"] / name).read_bytes()).hexdigest() == digest
print("Baseline restored; captured and candidate patches match their measured source digests.")
print("Complementary certificate failures verified; candidate:", run["status"], run["iterations"], "iterations.")
