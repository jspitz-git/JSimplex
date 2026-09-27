"""Compare identical replay checkpoints, preserving all residual/storage fields."""
import pathlib
import sys
import tomllib

baseline, candidate = map(pathlib.Path, sys.argv[1:3])
print("start,method,updates,update_before_s,update_after_s,ftran_before_ms,ftran_after_ms,btran_before_ms,btran_after_ms")
count = 0
for path in sorted(candidate.glob("*.toml")):
    before = tomllib.loads((baseline / path.name).read_text())
    after = tomllib.loads(path.read_text())
    assert before["input_sha256"] == after["input_sha256"]
    assert before["source_iteration"] == after["source_iteration"]
    for sample in after["samples"]:
        old = next(row for row in before["samples"]
                   if (row["method"], row["updates"]) == (sample["method"], sample["updates"]))
        for key in sample:
            if "residual" in key or "entries" in key:
                assert old[key] == sample[key], (path.name, sample["method"], sample["updates"], key)
        count += 1
        if sample["updates"] == 320:
            print(",".join(map(str, [after["source_iteration"], sample["method"], sample["updates"],
                old["cumulative_update_seconds"], sample["cumulative_update_seconds"],
                old["forward_seconds"] * 1000, sample["forward_seconds"] * 1000,
                old["transpose_seconds"] * 1000, sample["transpose_seconds"] * 1000])))
assert count > 0, "No replay checkpoints found"
print(f"Verified {count} matching residual/storage checkpoints.", file=sys.stderr)
