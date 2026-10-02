"""Validate postsolve evidence without running another numerical process."""
from pathlib import Path
import hashlib
import json
import math
import re
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / 'diagnostics/adaptive-degeneracy/results/postsolve-hints'
read = lambda name: tomllib.loads((results / name).read_text())
summary = json.loads((results / 'summary.json').read_text())
hash_context = hashlib.sha256()
for path in sorted([Path('Project.toml')] +
                   [p.relative_to(root) for p in (root / 'src').rglob('*.jl')],
                   key=lambda p: p.as_posix()):
    hash_context.update((path.as_posix() + '\0').encode())
    hash_context.update((root / path).read_bytes())
assert hash_context.hexdigest() == summary['production_sha256']
units = read('units.toml')
assert units['scaled']['violations_above_tolerance'] == {'column': 0, 'row': 0}
assert units['unscaled']['violations_above_tolerance'] == {'column': 18, 'row': 65}
for label in ('original_before_flips', 'original_after_flips'):
    assert units[label]['violations_above_tolerance'] == {'column': 21, 'row': 65}
    assert not units[label]['certificate']
assert units['clipped']['violations_above_tolerance'] == {'column': 0, 'row': 95}
assert not units['clipped']['certificate']
assert set(units['eliminated_violations']) == {'C8651', 'C8652', 'C8653'}
scaled_columns = [r for r in units['column_trace'] if r['stage'] == 'scaled']
assert {r['name'] for r in scaled_columns} == {'C6569', 'C6570', 'C6571'}
for row in scaled_columns:
    assert row['factor'] == 2 ** -14
    assert row['unscaled_value'] == row['value'] / row['factor']
    assert row['unscaled_value'] == -0.0010642815553997648
basis = read('basis-hint.toml')
assert basis['result'] == '342' and basis['after_pinf'] == 0 and basis['certificate']
assert basis['before_pinf'] == 3436849.0446019256
run = read('production.toml')
assert run['production_sha256'] == summary['production_sha256']
assert run['status'] == 'OPTIMAL' and run['original_primal_feasible']
assert math.isclose(run['objective'], 51425691.762103125, rel_tol=3e-14, abs_tol=0)
assert run['iterations'] == 130052 and run['refactorizations'] == 39075
assert run['events']['flip_completed'] == 47 and run['events']['pivot_completed'] == 1132
assert run['events']['certification'] == 2 and run['events']['phase_cleanup'] == 1
assert run['continuation_snapshot_sha256'] == units['workspace_sha256']
assert run['julia_threads'] == run['blas_threads'] == 1
assert not run['original_retry_enabled'] and not run['weak_pivot_preference']
assert {k for k,v in run['policy'].items() if v} == {
    'adaptive_pricing', 'adaptive_stalling', 'adaptive_primal_perturbation',
    'adaptive_dual_perturbation', 'phase_one'}
external = read('external.toml')['cases']
assert len(external) == 80
assert all(r['status'] == 'OPTIMAL' and r['objective_matches'] and r['original_primal_certified'] for r in external)
for name, label, count in (
    ('semantics.log', 'Postsolve hints and simplex semantic regressions', 9074),
    ('compiled.log', 'Compiled postsolve and allocation regressions', 2120),
    ('external.log', 'External LP relaxations: native and Markowitz basis managers', 245),
):
    assert re.search(re.escape(label) + rf'\s+\|\s+{count}\s+{count}\s',
                     (results / name).read_text()), name
manifest = json.loads((results / 'local-artifacts.json').read_text())
for name, digest in manifest['sha256'].items():
    assert hashlib.sha256((root / manifest['directory'] / name).read_bytes()).hexdigest() == digest, name
for name, digest in manifest['dependencies'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for name, digest in summary['evidence_sha256'].items():
    assert hashlib.sha256((results / name).read_bytes()).hexdigest() == digest, name
print('Coordinate trace, certified runtime continuation, external results and artifact hashes verified.')
