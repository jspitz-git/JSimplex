"""Validate the bounded-flip correction and its explicitly unresolved postsolve."""
from pathlib import Path
import hashlib
import json
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / 'diagnostics/adaptive-degeneracy/results/phase-two-small-pivot'
read = lambda name: tomllib.loads((results / name).read_text())
summary = json.loads((results / 'summary.json').read_text())
context = hashlib.sha256()
for path in sorted([Path('Project.toml')] +
                   [p.relative_to(root) for p in (root / 'src').rglob('*.jl')],
                   key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == summary['production_sha256']
old = read('baseline-pass.toml')
prices = [r for r in old['records'] if r['kind'] == 'price']
ratios = [r for r in old['records'] if r['kind'] == 'ratio']
assert old['status'] == 'NUMERICAL_ERROR'
assert old['message'] == 'primal pivot is below the zero tolerance'
assert len(prices) == len(ratios) == 48 and all(r['accepted'] for r in prices)
assert len({r['entering'] for r in ratios}) == 47
assert all(r['step'] == 0 and abs(r['pivot']) < old['zero_tolerance'] for r in ratios)
analysis = read('baseline-ratios.toml')['records']
assert len(analysis) == 48
assert all(r['flip_point_certified'] and r['limiter'] == 0 and 0 < r['flip_step'] == r['limit'] for r in analysis)
assert all(r['flip_max_bound_violation'] <= old['primal_tolerance'] for r in analysis)
fixed = read('corrected-pass.toml')
assert fixed['snapshot_sha256'] == old['snapshot_sha256']
assert fixed['status'] == 'step' and fixed['after_iterations'] == old['before_iterations'] + 1
assert fixed['after_refactorizations'] == fixed['before_refactorizations']
assert fixed['records'][-1]['row'] == 0 and fixed['records'][-1]['step'] == 1e-5
continued = read('continuation.toml')
assert continued['production_sha256'] == summary['production_sha256']
assert continued['continuation_snapshot_sha256'] == old['snapshot_sha256']
assert continued['continuation_start_iterations'] == 128873 and continued['iterations'] == 128920
assert continued['events']['flip_completed'] == 47
assert continued['events'].get('pivot_completed', 0) == 0
assert continued['events']['certification'] == 1
assert continued['status'] == 'NUMERICAL_ERROR' and continued['message'] == 'primal feasibility lost'
assert not continued['original_retry_enabled'] and not continued['weak_pivot_preference']
assert continued['julia_threads'] == continued['blas_threads'] == 1
captured = read('postsolve-capture.toml')
assert captured['production_sha256'] == continued['production_sha256']
assert captured['status'] == continued['status'] and captured['iterations'] == continued['iterations']
assert not captured['postsolve_target_feasible'] and captured['projection_result'] == 'nothing'
assert captured['projection_before_pinf'] == captured['projection_after_pinf']
points = read('original-points.toml')
assert points['reference_precision_bits'] == 256 and points['primal_tolerance'] == 1e-7
for name in ('before_flips', 'after_flips'):
    p = points[name]
    assert not p['certificate']
    assert p['violations_above_tolerance'] == {'column': 21, 'row': 65}
    assert p['maximum_violation'] == {'column': 0.0010642815553997648, 'row': 0.0010642815553997648}
assert points['after_flips']['objective'] == captured['postsolve_target_objective']
external = read('external.toml')['cases']
assert len(external) == 80
assert all(r['status'] == 'OPTIMAL' and r['objective_matches'] and r['original_primal_certified'] for r in external)
manifest = json.loads((results / 'local-artifacts.json').read_text())
for name, digest in manifest['sha256'].items():
    assert hashlib.sha256((root / manifest['directory'] / name).read_bytes()).hexdigest() == digest, name
assert points['target_sha256'] == manifest['sha256']['runtime-small-pivot-postsolve-target.bin']
for name, digest in summary['evidence_sha256'].items():
    assert hashlib.sha256((results / name).read_bytes()).hexdigest() == digest, name
print('Small-pivot correction, continuation, original-point rejection and artifacts verified.')
