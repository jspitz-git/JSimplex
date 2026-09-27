"""Summarize elapsed time per actual logged iteration, preserving the source hash."""
import hashlib
import json
import pathlib
import re
import statistics
import sys

source = pathlib.Path(sys.argv[1])
raw = source.read_bytes()
runs = {}
current = None
for line in raw.decode().splitlines():
    if line in ("PFI:", "Suhl_Suhl:", "Forrest-Tomlin:", "Bartels-Golub:"):
        current = line[:-1]
        runs[current] = {"records": [], "windows": [], "stride_changes": []}
    match = re.search(r"iter=(\d+) obj=(\S+) pinf=(\S+) .*?time=([0-9.e+\-]+)s", line)
    if match and current:
        runs[current]["records"].append(dict(iteration=int(match[1]), objective=match[2],
            pinf=match[3], seconds=float(match[4])))
    match = re.search(r"Solve finished: status=(\S+) objective=(\S+) iterations=(\d+) time=(\S+)s", line)
    if match and current:
        runs[current]["final"] = dict(status=match[1], objective=float(match[2]),
            iterations=int(match[3]), seconds=float(match[4]))
for name, run in runs.items():
    samples = [(a, b, b["iteration"]-a["iteration"]) for a, b in zip(run["records"], run["records"][1:])
               if b["iteration"] > a["iteration"]]
    previous = None
    for a, b, stride in samples:
        if stride != previous and a["iteration"] >= 10000:
            run["stride_changes"].append(dict(after_iteration=a["iteration"], previous=previous,
                current=stride, milliseconds_per_iteration=1000*(b["seconds"]-a["seconds"])/stride))
        previous = stride
    for lo, hi in ((10000,15000),(15000,18000),(18000,20000),(20000,22000),
                   (22000,25000),(25000,30000),(30000,40000)):
        costs = [1000*(b["seconds"]-a["seconds"])/stride for a,b,stride in samples
                 if lo <= a["iteration"] and b["iteration"] <= hi]
        if costs:
            run["windows"].append(dict(start=lo,end=hi,samples=len(costs),
                median_milliseconds_per_iteration=statistics.median(costs)))
    print(name, run.get("final"), run["windows"])
report = dict(source=str(source.resolve()), sha256=hashlib.sha256(raw).hexdigest(), runs=runs)
pathlib.Path(sys.argv[2]).write_text(json.dumps(report, indent=2)+"\n")
