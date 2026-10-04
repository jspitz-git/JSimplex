"""Audit final Float64 trajectories and the workload-enabled cache evidence."""
import hashlib
import json
import re
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parents[3]
local = root / '.superpowers/hh-precision'
original = root / 'diagnostics/huangfu-hall-public/reproduce'
reference = json.loads((original / 'reference.json').read_text())
digest = hashlib.sha256()
for rel in sorted(['Project.toml'] + [str(p.relative_to(root)) for p in (root / 'src').rglob('*.jl')]):
    digest.update((rel + '\0').encode())
    digest.update((root / rel).read_bytes())
manager_hash = hashlib.sha256((root / 'src/huangfu_hall_factorization.jl').read_bytes()).hexdigest()
harness_files = (original / 'external.jl', original / 'reference.json',
                 root / 'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml')
harness_hash = hashlib.sha256(b''.join(p.read_bytes() for p in harness_files)).hexdigest()
result = {'source_sha256': digest.hexdigest(), 'manager_sha256': manager_hash,
          'reference_commit': reference['reference_commit'], 'reports': {}, 'sha256': {}}
fields = ('input', 'input_sha256', 'algorithm', 'pricing', 'partial_pricing',
          'basis_refactorization', 'simplex_strategy', 'refactorization_interval',
          'status', 'objective', 'iterations', 'refactorizations', 'restarts',
          'primal_sha256', 'progress_sha256')
for selection, count in (('full', 2), ('external', 10)):
    paths = sorted((local / selection).glob('*.toml'))
    assert len(paths) == count
    reports = [tomllib.loads(p.read_text()) for p in paths]
    refs = {(r['input'], r['algorithm']): r for r in reference['reports'][selection]}
    keys = [(r['input'], r['algorithm']) for r in reports]
    assert len(set(keys)) == count and set(keys) == set(refs)
    for p, report in zip(paths, reports):
        assert report['source_sha256'] == digest.hexdigest()
        assert report['manager_sha256'] == manager_hash
        assert report['harness_sha256'] == harness_hash
        assert report['manager'] == 'huangfu_hall'
        assert report['status'] == 'OPTIMAL' and report['certified'] and report['objective_matches']
        assert report['julia_threads'] == report['blas_threads'] == 1
        for field in fields:
            assert report[field] == refs[(report['input'], report['algorithm'])][field], (p.name, field)
        result['sha256'][str(p.relative_to(local))] = hashlib.sha256(p.read_bytes()).hexdigest()
    result['reports'][selection] = reports
cache = tomllib.loads((local / 'cache.toml').read_text())
latency = tomllib.loads((local / 'latency.toml').read_text())
assert cache['cached'] and latency['cached_before_load']
assert cache['debug_level'] == latency['debug_level'] == 0
assert cache['opt_level'] == latency['opt_level'] == 2
assert latency['source_sha256'] == digest.hexdigest()
for key, name in (('harness_sha256', 'first-solve.jl'), ('cache_builder_sha256', 'build-cache.jl')):
    assert latency[key] == hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
for name, expected in latency['environment_sha256'].items():
    assert expected == hashlib.sha256((local / 'cache-env' / name).read_bytes()).hexdigest()
expected = {(t, a, u, 'native') for t in ('Float32', 'Float64') for a in ('primal', 'dual')
            for u in ('pfi', 'bartels_golub', 'forrest_tomlin', 'suhl_suhl', 'huangfu_hall')}
keys = [(r['type'], r['algorithm'], r['update'], r['backend']) for r in latency['samples']]
assert len(keys) == len(set(keys)) and set(keys) == expected
assert all(abs(r['objective'] - 10) <= 1e-4 for r in latency['samples'])
backend_keys = [(r['type'], r['form']) for r in latency['backend_samples']]
assert len(backend_keys) == len(set(backend_keys)) == 4
assert set(backend_keys) == {(t, form) for t in ('Float32', 'Float64') for form in ('sparse', 'dense')}
assert all(r['verified'] for r in latency['backend_samples'])
assert cache['precompile_workers'] == cache['image_threads'] == '1'
assert latency['julia_threads'] == 1
assert latency['precompile_workers'] == latency['image_threads'] == '1'
result['cache'] = cache
result['first_solve'] = latency
result['exact_comparison_fields'] = fields
result['resources'] = {}
for name in ('cache', 'latency', 'full', 'external', 'targeted-final', 'pipeline'):
    text = (local / (name + '.resources.txt')).read_text()
    assert 'Exit status: 0' in text, name
    labels = ('Elapsed (wall clock) time (h:mm:ss or m:ss)', 'Maximum resident set size (kbytes)', 'Exit status')
    result['resources'][name] = {label: line.strip()[len(label) + 2:]
        for line in text.splitlines() for label in labels if line.strip().startswith(label + ': ')}
# Baseline failures are recorded explicitly rather than reclassified as passes.
failure_pattern = re.compile(r"^(.+?): (Test Failed|Error During Test) at .*?/test/([^:\n]+):(\d+)", re.M)
baseline = (local / 'baseline-primal-tests.log').read_text()
integration = (local / 'integration-primal-tests.log').read_text()
old_failures = failure_pattern.findall(baseline)
new_failures = failure_pattern.findall(integration)
assert old_failures == new_failures and len(old_failures) == 27
assert sum(item[1] == 'Test Failed' for item in old_failures) == 25
assert '313    25      2    340' in baseline and '313    25      2    340' in integration
full_log = (local / 'full-suite.log').read_text()
assert 'wall-time guard; terminating owned process group' in full_log
assert failure_pattern.findall(full_log) == old_failures
assert 'Exit status: 75' in (local / 'full-suite.resources.txt').read_text()
assert re.search(r'Shared pipeline and typed HH policies\s*\|\s*1905\s+1905', (local / 'pipeline.log').read_text())
result['broader_suite'] = {
    'status': 'INCOMPLETE_WITH_BASELINE_FAILURES',
    'wall_guard_seconds': 300,
    'baseline_commit': 'efd7a97329be7391fcedc95a852d8a8713760c7e',
    'baseline_and_integration_passes': 313,
    'baseline_and_integration_failures': 25,
    'baseline_and_integration_errors': 2,
    'matching_failure_locations': old_failures,
    'shared_pipeline_passes': 1905,
}
for p in sorted(local.glob('*')):
    if p.is_file() and p.suffix in ('.log', '.toml', '.txt'):
        result['sha256'][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
(root / 'diagnostics/huangfu-hall-precision/results/final.json').write_text(json.dumps(result, indent=2) + '\n')
print('12 Float64 controls match the certified trajectories; 20 cached configurations verified')
