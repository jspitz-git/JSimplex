"""Compare the numerical state of matching prefixes, excluding wall-clock fields."""
import json
import pathlib
import sys
import tomllib

before = tomllib.loads(pathlib.Path(sys.argv[1]).read_text())
after = tomllib.loads(pathlib.Path(sys.argv[2]).read_text())
assert before["input_sha256"] == after["input_sha256"]
assert before["method"] == after["method"]
assert len(after["samples"]) >= len(before["samples"])
keys = ("iteration", "configured_interval", "effective_interval", "updates",
        "refactorizations", "upper_entries", "history_entries", "working_objective")
for old, new in zip(before["samples"], after["samples"]):
    for key in keys:
        assert old[key] == new[key], (old["iteration"], key, old[key], new[key])
old = before["samples"][-1]
new = after["samples"][len(before["samples"]) - 1]
print(json.dumps(dict(iteration=old["iteration"], matched_samples=len(before["samples"]),
    baseline_seconds=old["seconds"], candidate_seconds=new["seconds"],
    numerical_fields_identical=True), indent=2))
