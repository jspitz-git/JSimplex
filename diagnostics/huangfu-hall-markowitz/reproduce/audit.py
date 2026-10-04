"""Audit pinned external results, scalar controls and split regression checks."""
import hashlib
import json
from pathlib import Path
import re
import tomllib

root = Path(__file__).resolve().parents[3]
local = root / '.superpowers/hh-markowitz'
digest = hashlib.sha256()
for rel in sorted(['Project.toml'] + [str(p.relative_to(root)) for p in (root / 'src').rglob('*.jl')]):
    digest.update((rel + '\0').encode())
    digest.update((root / rel).read_bytes())
source = digest.hexdigest()
result = {'source_sha256': source, 'reports': {}, 'resources': {}, 'sha256': {}}
harness = Path(__file__).with_name('external.jl')
for selection, count, backend in (('small', 10, 'markowitz'), ('runtime-long', 1, 'markowitz'), ('native', 10, 'native')):
    paths = sorted((local / selection).glob('*.toml'))
    assert len(paths) == count, selection
    reports = [tomllib.loads(p.read_text()) for p in paths]
    assert len({(r['input'], r['algorithm']) for r in reports}) == count
    for r in reports:
        assert r['source_sha256'] == source
        assert r['harness_sha256'] in (hashlib.sha256(harness.read_bytes()).hexdigest(),
            '00ec80db022a8b1ffbf495cd3ea3ee29d04cba52aa646c0fd4d44fa3e69619b8')
        assert r['status'] == 'OPTIMAL' and r['certified'] and r['objective_matches']
        assert r['basis_refactorization'] == backend
        assert r['julia_threads'] == r['blas_threads'] == 1
    result['reports'][selection] = reports
initial = tomllib.loads((local / 'runtime/mps-runtime-dual.toml').read_text())
assert initial['status'] == 'TIME_LIMIT' and initial['source_sha256'] == source
assert initial['iterations'] == 60732 and initial['restarts'] == 0
assert 'Exit status: 1' in (local / 'runtime.resources.txt').read_text()
result['initial_runtime_limit'] = initial
result['initial_runtime_profile_peek'] = 'One SIGUSR1 sample; not a performance comparison'
reference = json.loads((root / 'diagnostics/huangfu-hall-public/reproduce/reference.json').read_text())
refs = {(r['input'], r['algorithm']): r for r in reference['reports']['external']}
fields = ('input_sha256', 'status', 'objective', 'iterations', 'refactorizations',
          'restarts', 'primal_sha256', 'progress_sha256')
for r in result['reports']['native']:
    old = refs[(r['input'], r['algorithm'])]
    for key in fields:
        assert r[key] == old[key], (r['input'], r['algorithm'], key)
result['native_reference_commit'] = reference['reference_commit']
result['native_exact_comparison_fields'] = fields
scalars = tomllib.loads((local / 'scalars.toml').read_text())['records']
assert len(scalars) == 10
assert all(r['status'] == 'OPTIMAL' and r['certified'] and r['objective_matches'] for r in scalars)
assert len({(r['type'], r['input'], r['algorithm']) for r in scalars}) == 10
result['scalar_controls'] = scalars
for name, count in (('semantic', 2516), ('compiled', 1833)):
    log = (local / (name + '.log')).read_text()
    assert re.search(r'HH Markowitz ' + name + r'\s*\|\s*' + str(count) + r'\s+' + str(count), log)
result['targeted_passes'] = {'semantic': 2516, 'compiled': 1833}
for name in ('small', 'runtime-long', 'native', 'scalars', 'semantic', 'compiled'):
    data = (local / (name + '.resources.txt')).read_text()
    assert 'Exit status: 0' in data, name
    labels = ('Elapsed (wall clock) time (h:mm:ss or m:ss)', 'Maximum resident set size (kbytes)', 'Exit status')
    result['resources'][name] = {label: line.strip()[len(label) + 2:]
        for line in data.splitlines() for label in labels if line.strip().startswith(label + ': ')}
for p in sorted(local.rglob('*')):
    if p.is_file() and p.suffix in ('.log', '.toml', '.txt'):
        result['sha256'][str(p.relative_to(local))] = hashlib.sha256(p.read_bytes()).hexdigest()
for p in (harness, Path(__file__).with_name('scalars.jl'), Path(__file__).with_name('targeted.jl'),
          root / 'diagnostics/huangfu-hall-public/reproduce/external.jl'):
    result['sha256'][str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
output = root / 'diagnostics/huangfu-hall-markowitz/results/final.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n')
print('All 21 external solves, 10 scalar controls and split checks passed; native trajectories match exactly')
