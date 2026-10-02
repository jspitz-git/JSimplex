"""Validate replay evidence and reconstruct both experimental source digests."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / "diagnostics/adaptive-degeneracy/results/row-value"
reproduce = Path(__file__).resolve().parent

def read(name):
    return tomllib.loads((results / name).read_text())

def source_digest(directory):
    digest = hashlib.sha256()
    files = [Path("Project.toml")] + [p.relative_to(directory) for p in (directory / "src").rglob("*.jl")]
    for path in sorted(files, key=lambda p: p.as_posix()):
        digest.update((path.as_posix() + "\0").encode())
        digest.update((directory / path).read_bytes())
    return digest.hexdigest()

baseline = read("runtime-ratios.toml")["production_sha256"]
assert source_digest(root) == baseline, "Production source differs from the documented restored baseline"
for name in ("runtime-ratio-replay-before.toml", "runtime-ratio-replay-restored.toml"):
    snapshots = read(name)["snapshots"]
    assert len(snapshots) == 4
    assert all(s["same_ratio"] and s["first_pass_exit"] == "none" for s in snapshots)
after = read("runtime-ratio-replay-final.toml")["snapshots"]
changed = [s for s in after if not s["same_ratio"]]
assert len(changed) == 1
assert (changed[0]["iteration"], changed[0]["replayed_row"], changed[0]["replayed_step"]) == (6695, 16106, 0.0)
assert abs(changed[0]["replayed_pivot"]) > 15

for patch, report, iteration in (
    ("working-row-only.patch", "runtime-row-value.toml", 6799),
    ("working-row-rounded.patch", "runtime-row-rounded.toml", 8464),
):
    evidence = read(report)
    assert evidence["status"] == "NUMERICAL_ERROR" and evidence["iterations"] == iteration
    assert evidence["time_limit"] == 300 and evidence["seconds"] < 300
    assert not evidence["original_retry_enabled"]
    assert evidence["events"].get("precision_boost", 0) == 0
    assert sum(x["count"] for x in evidence["rejection_breakdown"]) == evidence["events"]["pivot_rejected"]
    with tempfile.TemporaryDirectory(prefix="jsimplex-row-evidence-") as temporary:
        directory = Path(temporary)
        shutil.copy2(root / "Project.toml", directory)
        shutil.copytree(root / "src", directory / "src")
        subprocess.run(["git", "apply", "--unidiff-zero", str(reproduce / patch)], cwd=directory, check=True)
        assert source_digest(directory) == evidence["production_sha256"], patch
    print(patch, "matches recorded source; numerical failure at", iteration)
assert read("runtime-row-rounded.toml")["events"]["primal_bound_roundoff_corrected"] == 4
print("Baseline restored; all four ratio decisions reproduce; neither candidate establishes convergence.")
