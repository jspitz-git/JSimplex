"""Compare numerical records; timing and allocation counters are not identities."""
import json
import pathlib
import tomllib

root = pathlib.Path(__file__).resolve().parent.parent / "results"
keys = ("input_sha256", "algorithm", "status", "message", "iterations", "refactorizations",
        "objective", "trace_sha256", "checkpoints_sha256", "counts", "primal_sha256",
        "original_primal_certified")

def load(path):
    with path.open("rb") as stream:
        return tomllib.load(stream)


def compare(before, after):
    for key in keys:
        assert before[key] == after[key], (before.get("case", before["input"]), key)
    return len(keys)


baseline = {case["case"]: case for case in load(root / "baseline-corpus.toml")["cases"]}
current = {case["case"]: case for case in load(root / "current-corpus.toml")["cases"]}
assert baseline.keys() == current.keys()
assert len(baseline) == 48
checks = sum(compare(baseline[name], current[name]) for name in baseline)
for algorithm in ("primal", "dual"):
    checks += compare(load(root / f"baseline-fast-{algorithm}-trace.toml"),
                      load(root / f"current-fast-{algorithm}-trace.toml"))
checks += compare(load(root / "baseline-runtime-dual.toml"), load(root / "current-runtime-dual.toml"))
result = {"identical_solve_pairs": len(baseline) + 3, "identity_checks": checks,
          "fields": list(keys)}
(root / "equivalence.json").write_text(json.dumps(result, indent=2) + "\n")
print(result)
