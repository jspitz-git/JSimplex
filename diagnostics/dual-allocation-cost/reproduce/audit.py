"""Audit archived diagnostic results without starting Julia."""
from pathlib import Path
import json, subprocess, tomllib
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'diagnostics/dual-allocation-cost/results'
def read(name):
    with (OUT / name).open('rb') as stream:
        return tomllib.load(stream)
reference = tomllib.loads((ROOT / 'diagnostics/simplex-data-movement/results/runtime-final.toml').read_text())
for name in ('cost-runtime.toml', 'cost-runtime-repeat.toml'):
    report = read(name)
    assert report['status'] == 'OPTIMAL' and report['original_feasible']
    assert report['iterations'] == 54591 and report['refactorizations'] == 194
    for key in ('events_hash', 'states_hash'):
        assert report[key] == reference[key]
    repairs = [r for r in report['stats'] if r['kernel'] == 'small_pivot_recovery']
    assert sum(r['calls'] for r in repairs) == 4
    assert 59_146_790 <= sum(r['allocations_inclusive'] for r in repairs) <= 59_146_810
    for kernel in ('leaving_pricing', 'tableau_pricing', 'harris', 'flips_nonempty', 'weight_maintenance'):
        assert sum(r['allocations_inclusive'] for r in report['stats'] if r['kernel'] == kernel) == 0
medium = read('cost-medium.toml')
assert medium['status'] == 'ITERATION_LIMIT' and medium['iterations'] == 4000
replay = read('selection-replay.toml')['cases']
assert len(replay) == 12
for row in replay:
    for key in ('batch_bytes', 'batch_allocations', 'compile_seconds'):
        assert len(row[key]) == 9 and all(value == 0 for value in row[key])
for path in OUT.glob('*-process.json'):
    record = json.loads(path.read_text())
    assert record['sources_unchanged']
    failed = path.name in ('runtime-allocations-process.json', 'selection-replay-process.json')
    assert record['returncode'] == (1 if failed else 0)
assert not subprocess.check_output(['git', 'diff', '9c67ab2', '--', 'src', 'test', 'Project.toml'], cwd=ROOT).strip()
print('PASS: runtime fingerprints, repair counts, allocation-free kernels, medium prefix, 108 selector batches, process outcomes, unchanged production source')
