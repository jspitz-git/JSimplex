"""Audit preserved medium cleanup reports without launching numerical work."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tomllib

root = Path(__file__).resolve().parents[3]
raw = root / '.superpowers/cleanup-memory'
destination = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'diagnostics/primal-row-memory/results'
destination.mkdir(parents=True, exist_ok=True)
expected_source = 'afdebdb6ede3da184ca8ca27c1ea982936bf5c59b90e1b58b89544423ac72564'
records = []
files = {}

def track(path):
    files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()

for algorithm, start in [('primal', 335046), ('dual', 212280)]:
    report = raw / f'medium-{algorithm}.toml'
    process = raw / f'medium-{algorithm}-process.json'
    memory = raw / f'medium-{algorithm}-memory.csv'
    log = raw / f'medium-{algorithm}.log'
    for path in (report, process, memory, log):
        track(path)
    d = tomllib.loads(report.read_text())
    p = json.loads(process.read_text())
    assert p['exit_code'] == 0 and p['source_unchanged']
    assert p['source_sha256'] == expected_source
    assert d['status'] == 'OPTIMAL' and d['original_primal_feasible']
    assert d['original_objective_evaluable'] and math.isfinite(d['objective'])
    assert d['iterations'] == start + d['additional_iterations']
    assert d['events']['pivot_completed'] == d['additional_iterations']
    assert d['events']['certification'] == 1
    assert d['julia_threads'] == d['blas_threads'] == 1
    assert d['time_limit'] == math.inf and d['iteration_limit'] == 1000000
    handoff = root / f'.superpowers/certificate-repair/medium-{algorithm}-handoff.bin'
    assert hashlib.sha256(handoff.read_bytes()).hexdigest() == d['handoff_sha256']
    with memory.open() as stream:
        samples = list(csv.DictReader(stream))
    rss = max(int(s['rss_kib']) for s in samples)
    vm = max(int(s['vm_kib']) for s in samples)
    assert rss == p['peak_sample_rss_kib'] and vm == p['peak_sample_vm_kib']
    hwm = int(re.search(r'Maximum resident set size \(kbytes\): (\d+)', log.read_text()).group(1))
    assert vm < 8 * 1024**2
    shutil.copyfile(report, destination / report.name)
    shutil.copyfile(process, destination / process.name)
    records.append(dict(algorithm=algorithm, status=d['status'], iterations=d['iterations'],
        additional_iterations=d['additional_iterations'], objective=d['objective'],
        original_primal_feasible=d['original_primal_feasible'], seconds=d['seconds'],
        compile_seconds=d['compile_seconds'], process_hwm_kib=hwm,
        peak_sample_rss_kib=rss, peak_sample_vm_kib=vm, sample_count=len(samples),
        cleanup_algorithm='primal', scope='saved terminal-state handoff continuation'))
assert records[0]['objective'] == records[1]['objective']

# Equality of sampled progress is narrower than a full ordered-pivot trace.
old = root / '.superpowers/certificate-repair/medium-primal-cleanup-gc-final.log'
new = raw / 'medium-primal.log'
track(old)
pattern = re.compile(r'^EVENT pivot_completed iteration=(\d+) pinf=(\S+) dinf=(\S+)$', re.M)
a = {int(i):(p,d) for i,p,d in pattern.findall(old.read_text())}
b = {int(i):(p,d) for i,p,d in pattern.findall(new.read_text())}
shared = sorted(a.keys() & b.keys())
assert shared and all(a[i] == b[i] for i in shared)
summary = dict(source_sha256=expected_source, outcomes=records,
    common_primal_progress=dict(count=len(shared), first=shared[0], last=shared[-1], identical=True,
        limitation='Sampled pinf/dinf only, not complete pivot or state hashes; baseline has GC observer.'),
    incomplete_attempt=dict(path='.superpowers/cleanup-memory/interrupted-before-ftz-fix',
        exit_code=143, reason='Task-owned interruption before final FTZ fix; not a solver result.'),
    file_sha256=files)
(destination / 'medium-cleanup-audit.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k != 'file_sha256'}, indent=2))
