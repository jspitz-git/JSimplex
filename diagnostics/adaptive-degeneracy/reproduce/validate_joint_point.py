"""Validate rejected joint-point candidates, source provenance and local evidence."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / "diagnostics/adaptive-degeneracy/results/joint-point"


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
metadata = json.loads((results / "candidate.json").read_text())
for patch, key, hash_key in (("joint-quarter.patch", "production_sha256", "quarter_patch_sha256"),
                             ("joint-native.patch", "native_production_sha256", "native_patch_sha256")):
    assert hashlib.sha256((reproduce / patch).read_bytes()).hexdigest() == metadata[hash_key]
    with tempfile.TemporaryDirectory(prefix="jsimplex-joint-evidence-") as temporary:
        directory = Path(temporary)
        shutil.copy2(root / "Project.toml", directory)
        shutil.copytree(root / "src", directory / "src")
        subprocess.run(["git", "apply", "--unidiff-zero", str(reproduce / patch)], cwd=directory, check=True)
        assert source_digest(directory) == metadata[key]

for name, iteration, refs, attempts, accepted, key in (
    ("runtime-joint.toml", 9391, 1805, 7, 6, "production_sha256"),
    ("runtime-joint-native.toml", 9612, 1985, 8, 7, "native_production_sha256"),
):
    report = read(name)
    assert report["status"] == "NUMERICAL_ERROR" and report["iterations"] == iteration
    assert report["refactorizations"] == refs and report["seconds"] < 300
    assert report["events"]["primal_projection_attempt"] == attempts
    assert report["events"]["primal_point_projected"] == accepted
    assert report["production_sha256"] == metadata[key]

for name in ("runtime-joint.toml", "runtime-joint-native.toml", "medium-joint-native.toml"):
    report = read(name)
    assert report["time_limit"] == 300
    assert report["julia_threads"] == report["blas_threads"] == 1
    assert not report["original_retry_enabled"] and not report["weak_pivot_preference"]
    assert report["events"].get("precision_boost", 0) == 0
    enabled = {name for name, value in report["policy"].items() if value}
    assert enabled == {"phase_one", "adaptive_stalling", "adaptive_pricing",
                       "adaptive_primal_perturbation", "adaptive_dual_perturbation"}

medium = read("medium-joint-native.toml")
assert medium["status"] == "TIME_LIMIT" and medium["iterations"] == 2875
assert medium["refactorizations"] == 36 and medium["seconds"] >= 300
assert medium["production_sha256"] == metadata["native_production_sha256"]
assert medium["events"].get("primal_projection_attempt", 0) == 0

margin = read("joint-margin.toml")["records"]
assert [(r["tag"], r["certified"]) for r in margin] == [
    ("quarter_tolerance", False), ("zero_margin", True), ("native_roundoff", True)]
clipping = read("joint-clipping.toml")["records"]
assert all(not r["accepted"] and not r["certified"] for r in clipping)
for name in ("joint-native-failure.toml", "joint-redistributed-failure.toml"):
    trace = read(name)
    assert not trace["accepted"] and trace["restored"]
    sweeps = [r for r in trace["records"] if r["tag"].startswith("sweep_")]
    assert len(sweeps) == 8 and all(not r["equations"] for r in sweeps)
last = read("joint-redistributed-failure-constraints.toml")["records"][-1]
assert [r["row"] for r in last["rows"]] == [3608]
assert 0 < last["rows"][0]["exact_bound_excess"] < 1e-20
replay = read("joint-native-replay.toml")["records"]
assert len(replay) == 6
assert all(r["accepted"] and r["certified"] and r["nonbasic_unchanged"] for r in replay)

assert hashlib.sha256((reproduce / "joint_point_candidate_tests.jl").read_bytes()).hexdigest() == metadata["native_candidate_tests_sha256"]
for name, count in (("joint-native-semantics.log", 6728), ("joint-native-compiled.log", 740)):
    assert re.search(r"\|\s+" + str(count) + r"\s+" + str(count) + r"\s+", (results / name).read_text())

local = json.loads((results / "local-artifacts.json").read_text())
if (root / local["directory"]).exists():
    for name, digest in local["sha256"].items():
        assert hashlib.sha256((root / local["directory"] / name).read_bytes()).hexdigest() == digest
print("Baseline restored; both rejected patches match their measured source digests.")
print("Joint recovery, margin and clipping evidence verified; runtime still fails.")
