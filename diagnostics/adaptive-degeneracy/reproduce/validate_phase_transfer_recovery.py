"""Validate the production transfer evidence, source and retained artifacts."""
from pathlib import Path
import hashlib
import json
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / 'diagnostics/adaptive-degeneracy/results/phase-transfer-recovery'
summary = json.loads((results / 'summary.json').read_text())
report = tomllib.loads((results / 'runtime-phase-recovery.toml').read_text())
replay = tomllib.loads((results / 'phase-transfer-replay.toml').read_text())
context = hashlib.sha256()
for path in sorted([Path('Project.toml')] +
                   [p.relative_to(root) for p in (root / 'src').rglob('*.jl')],
                   key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == report['production_sha256'] == summary['production_sha256']
assert replay['accepted']
for key in ('finite', 'basis_reliable', 'point_certified', 'original_primal_feasible'):
    assert replay['point'][key]
assert replay['point']['primal_solve']['reliable']
assert replay['point']['dual_solve']['reliable']
assert report['algorithm'] == 'primal' and report['mode'] == 'both'
assert not report['original_retry_enabled'] and not report['weak_pivot_preference']
assert report['julia_threads'] == report['blas_threads'] == 1
assert report['input_sha256'] == 'd0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
assert {k for k,v in report['policy'].items() if v} == {
    'adaptive_stalling', 'adaptive_pricing', 'adaptive_primal_perturbation',
    'adaptive_dual_perturbation', 'phase_one'}
prior = tomllib.loads((results.parent / 'phase-transfer/runtime-transfer-capture.toml').read_text())
# Compare mathematical observations, excluding clocks and process object identities.
ignore = {'seconds', 'workspace', 'monitor'}
expected = [r for r in prior['records'] if r['event'] != 'final_observed_workspace']
for actual, old in zip(report['records'], expected, strict=False):
    assert {k:v for k,v in actual.items() if k not in ignore} == {
        k:v for k,v in old.items() if k not in ignore}
assert len(report['records']) >= len(expected)
assert len(expected) == summary['matched_prefix_records']
assert report['status'] == summary['status']
assert report['iterations'] == summary['iterations']
continued = tomllib.loads((results / 'runtime-phase-continuation.toml').read_text())
assert continued['production_sha256'] == report['production_sha256']
assert continued['continuation_start_iterations'] == report['iterations']
assert continued['status'] == 'NUMERICAL_ERROR'
assert continued['message'] == 'primal pivot is below the zero tolerance'
assert continued['iterations'] == 128873
assert continued['policy'] == report['policy']
assert continued['original_retry_enabled'] is False
assert continued['events']['pivot_completed'] + continued['events']['flip_completed'] == 4123
assert continued['iterations'] - continued['continuation_start_iterations'] == 4123
assert continued['julia_threads'] == continued['blas_threads'] == 1
assert any(r['event'] == 'phase_primal' and r['iteration'] == 102446
           and r['pricing'] == 'steepest_edge' for r in report['records'])
manifest = json.loads((results / 'local-artifacts.json').read_text())
assert continued['continuation_snapshot_sha256'] == manifest['sha256']['runtime-phase-recovery-final.bin']
for name, digest in manifest['sha256'].items():
    assert hashlib.sha256((root / manifest['directory'] / name).read_bytes()).hexdigest() == digest, name
for name, digest in summary['evidence_sha256'].items():
    assert hashlib.sha256((results / name).read_bytes()).hexdigest() == digest, name
print('Production transfer evidence, shared prefix, source and artifacts verified.')
