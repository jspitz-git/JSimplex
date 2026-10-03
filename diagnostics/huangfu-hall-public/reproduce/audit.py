"""Validate public-manager full solves against previously certified MPF trajectories."""
import hashlib
import json
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parents[3]
local = root / '.superpowers/hh-public'
reference = json.loads((Path(__file__).with_name('reference.json')).read_text())
harness_files = (Path(__file__).with_name('external.jl'), Path(__file__).with_name('reference.json'),
                 root / 'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml')
harness_sha256 = hashlib.sha256(b''.join(p.read_bytes() for p in harness_files)).hexdigest()
exact = ('input', 'input_sha256', 'algorithm', 'pricing', 'partial_pricing',
         'basis_refactorization', 'simplex_strategy', 'refactorization_interval',
         'status', 'objective', 'iterations', 'refactorizations', 'restarts',
         'primal_sha256', 'progress_sha256')
digest = hashlib.sha256()
for rel in sorted(['Project.toml'] + [str(p.relative_to(root)) for p in (root / 'src').rglob('*.jl')]):
    digest.update((rel + '\0').encode()); digest.update((root / rel).read_bytes())
result = {'reference_commit': reference['reference_commit'], 'source_sha256': digest.hexdigest(), 'reports': {}, 'sha256': {}}
for selection, count in (('full', 2), ('external', 10)):
    paths = sorted((local / selection).glob('*.toml'))
    assert len(paths) == count
    reports = [tomllib.loads(p.read_text()) for p in paths]
    refs = {(r['input'], r['algorithm']): r for r in reference['reports'][selection]}
    keys = [(r['input'], r['algorithm']) for r in reports]
    assert len(set(keys)) == len(keys), ('duplicate inputs', selection)
    assert set(keys) == set(refs), ('coverage mismatch', selection)
    for p, report in zip(paths, reports):
        assert report['harness_sha256'] == harness_sha256
        assert report['status'] == 'OPTIMAL' and report['certified'] and report['objective_matches']
        assert report['manager'] == 'huangfu_hall'
        assert report['julia_threads'] == report['blas_threads'] == 1
        assert report['manager_sha256'] == hashlib.sha256((root / 'src/huangfu_hall_factorization.jl').read_bytes()).hexdigest()
        assert report['source_sha256'] == digest.hexdigest()
        old = refs[(report['input'], report['algorithm'])]
        for field in exact:
            assert report[field] == old[field], (report['input'], report['algorithm'], field)
        result['sha256'][str(p.relative_to(local))] = hashlib.sha256(p.read_bytes()).hexdigest()
    result['reports'][selection] = reports
result['exact_comparison_fields'] = exact
cache = tomllib.loads((local / 'cache-g0.toml').read_text())
latency = tomllib.loads((local / 'latency-final.toml').read_text())
assert cache['cached'] and latency['cached_before_load']
assert cache['julia'] == latency['julia']
assert cache['debug_level'] == latency['debug_level'] == 0
assert cache['opt_level'] == latency['opt_level'] == 2
assert latency['source_sha256'] == digest.hexdigest()
for key, name in (('harness_sha256', 'first-solve.jl'), ('cache_builder_sha256', 'build-cache.jl')):
    assert latency[key] == hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
for name, expected in latency['environment_sha256'].items():
    assert expected == hashlib.sha256((local / 'cache-env' / name).read_bytes()).hexdigest()
assert latency['julia_threads'] == 1
assert cache['precompile_workers'] == cache['image_threads'] == '1'
assert latency['precompile_workers'] == latency['image_threads'] == '1'
expected = {(t, a, u, b) for t in ('Float32', 'Float64') for a in ('primal', 'dual')
            for u in ('pfi', 'bartels_golub', 'forrest_tomlin', 'suhl_suhl')
            for b in ('native',)}
expected.update(('Float64', a, 'huangfu_hall', 'native') for a in ('primal', 'dual'))
keys = [(r['type'], r['algorithm'], r['update'], r['backend']) for r in latency['samples']]
assert len(keys) == len(set(keys)) and set(keys) == expected
assert all(abs(r['objective'] - 10) <= 1e-4 for r in latency['samples'])
backend_keys = [(r['type'], r['form']) for r in latency['backend_samples']]
assert len(backend_keys) == len(set(backend_keys)) == 4
assert set(backend_keys) == {(t, f) for t in ('Float32', 'Float64') for f in ('sparse', 'dense')}
assert all(r['verified'] for r in latency['backend_samples'])
result['resources'] = {}
for name in ('cache-g0', 'latency-final', 'targeted-final', 'markowitz-semantic', 'full', 'external'):
    resource = local / (name + '.resources.txt')
    assert 'Exit status: 0' in resource.read_text(), name
    labels = ('User time (seconds)', 'System time (seconds)', 'Elapsed (wall clock) time (h:mm:ss or m:ss)',
              'Maximum resident set size (kbytes)', 'Exit status')
    result['resources'][name] = {label: line.strip()[len(label) + 2:]
        for line in resource.read_text().splitlines() for label in labels if line.strip().startswith(label + ': ')}
    result['sha256'][resource.name] = hashlib.sha256(resource.read_bytes()).hexdigest()
for name in ('cache-g0.toml', 'latency-final.toml'):
    result['sha256'][name] = hashlib.sha256((local / name).read_bytes()).hexdigest()
result['cache'] = cache
result['first_solve'] = latency
result['cache_provenance'] = 'Strict cache build followed by a fresh-process cache check bound to source and environment digests'

result['verification_scripts_sha256'] = {}
for name in ('markowitz-semantic.jl', 'semantic.jl'):
    promoted = Path(__file__).with_name(name)
    assert promoted.read_bytes() == (local / name).read_bytes()
    result['verification_scripts_sha256'][name] = hashlib.sha256(promoted.read_bytes()).hexdigest()
for p in sorted(local.glob('*.log')):
    result['sha256'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
(root / 'diagnostics/huangfu-hall-public/results/external.json').write_text(json.dumps(result, indent=2) + '\n')
print('12 public solves certified; numerical fields match reference exactly')
