"""Recover the comparable printed prefix when a final report could not be saved."""
import json
import pathlib
import re
import sys
import tomllib

baseline = tomllib.loads(pathlib.Path(sys.argv[1]).read_text())
old = {sample["iteration"]: sample for sample in baseline["samples"]}
keys = ("iteration", "configured_interval", "effective_interval", "updates",
        "refactorizations", "upper_entries", "history_entries", "working_objective")
matched = []
for line in pathlib.Path(sys.argv[2]).read_text().splitlines():
    if not line.startswith('Dict{String, Any}("iteration"'):
        continue
    sample = {key: float(re.search('"' + key + '" => ([0-9.e+\\-]+)', line)[1])
              for key in (*keys, "seconds")}
    iteration = int(sample["iteration"])
    if iteration not in old:
        continue
    for key in keys:
        assert sample[key] == old[iteration][key], (iteration, key)
    matched.append(sample)
assert matched, "No matching printed samples"
last = matched[-1]
print(json.dumps(dict(source=pathlib.Path(sys.argv[2]).name,
    final_status="unavailable_due_to_export_error", matched_logged_samples=len(matched),
    iteration=last["iteration"], baseline_seconds=old[int(last["iteration"])]["seconds"],
    candidate_seconds=last["seconds"], numerical_fields_identical=True), indent=2))
