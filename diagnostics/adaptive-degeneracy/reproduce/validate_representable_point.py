"""Validate bounded native recovery results and measured source provenance."""
from pathlib import Path
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / 'diagnostics/adaptive-degeneracy/results/representable-point'
metadata = json.loads((results / 'candidate.json').read_text())


def read(name):
    return tomllib.loads((results / name).read_text())


def source_digest(directory):
    digest = hashlib.sha256()
    files = [Path('Project.toml')] + [p.relative_to(directory) for p in (directory / 'src').rglob('*.jl')]
    for path in sorted(files, key=lambda p: p.as_posix()):
        digest.update((path.as_posix() + '\0').encode())
        digest.update((directory / path).read_bytes())
    return digest.hexdigest()


assert source_digest(root) == metadata['prediction_anchor_production_sha256']
patch = reproduce / metadata['reconstruction_patch']
assert hashlib.sha256(patch.read_bytes()).hexdigest() == metadata['reconstruction_patch_sha256']
archive = subprocess.check_output(['git', 'archive', metadata['baseline_commit'], 'src', 'Project.toml'], cwd=root)
with tempfile.TemporaryDirectory(prefix='jsimplex-representable-') as temporary:
    directory = Path(temporary)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(directory, filter='data')
    assert source_digest(directory) == 'c72ebe2862aa66194cd238ab35d93a19dc56ae59e2f80948c9e9d3a447ff48bc'
    subprocess.run(['git', 'apply', '--unidiff-zero', str(patch)], cwd=directory, check=True)
    assert source_digest(directory) == metadata['production_sha256']

reports = []
for name, status, iteration, refs, attempts, key in (
    ('runtime-representable.toml', 'NUMERICAL_ERROR', 14186, 3182, 46, 'production_sha256'),
    ('runtime-representable-capture.toml', 'NUMERICAL_ERROR', 14186, 3182, 46, 'production_sha256'),
    ('runtime-representable-anchor.toml', 'TIME_LIMIT', 14845, 3209, 50, 'prediction_anchor_production_sha256'),
):
    report = read(name)
    assert report['status'] == status and report['iterations'] == iteration
    assert report['refactorizations'] == refs
    assert report['production_sha256'] == metadata[key]
    assert report['time_limit'] == 300
    assert report['julia_threads'] == report['blas_threads'] == 1
    assert not report['original_retry_enabled'] and not report['weak_pivot_preference']
    assert report['events']['primal_projection_attempt'] == attempts
    assert report['events']['primal_point_projected'] == attempts
    assert report['events'].get('precision_boost', 0) == 0
    assert (report['seconds'] >= 300) == (status == 'TIME_LIMIT')
    reports.append(str(results / name))
final = read('runtime-representable-anchor.toml')
terminal = [r for r in final['records'] if r['event'] == 'final_observed_workspace']
assert len(terminal) == 1 and terminal[0]['pinf'] > 0
assert 'uncertified_after_termination' in terminal[0].values()
assert final['events']['phase_one'] == 1 and final['events'].get('phase_two', 0) == 0
for validator in ('validate_phase_one_reports.py', 'validate_intervention_reports.py'):
    subprocess.run(['python3', str(reproduce / validator), *reports], check=True)

budget = read('representable-budget.toml')['records']
assert len(budget) == 18 and all(r['basic'] for r in budget)
assert sum(r['empty_local_interval'] for r in budget) == 8
pivot = read('representable-pivot.toml')
assert pivot['step'] == 0 and pivot['pivot'] > 1
assert pivot['records'][0]['certified']
anchors = read('representable-anchor.toml')['records']
assert len(anchors) == 4
assert all(r['accepted'] == r['certified'] == (r['tag'] == 'prediction') for r in anchors)
prediction = next(r for r in anchors if r['tag'] == 'prediction')
assert prediction['maximum_change_from_anchor'] < 1e-7
assert prediction['maximum_change_from_reconstruction'] > 8e-7
replay = read('representable-anchored-replay.toml')['records']
assert len(replay) == 8
assert all(r['accepted'] and r['certified'] and r['nonbasic_unchanged'] for r in replay)
assert replay[-1]['iteration'] == 14186

for name, count in (('representable-expanded.log', 378), ('representable-semantics.log', 6876),
                    ('representable-compiled.log', 888)):
    assert re.search(r'\|\s+' + str(count) + r'\s+' + str(count) + r'\s+', (results / name).read_text())
assert (root / 'test/legacy_primal_joint_point_tests.jl').read_text() == (
    (reproduce / 'joint_point_candidate_tests.jl').read_text() + '\n' +
    (reproduce / 'representable_point_tests.jl').read_text())
assert (root / 'test/legacy_primal_working_row_scope_tests.jl').read_bytes() == (
    reproduce / 'working_row_candidate_tests.jl').read_bytes()
for name in ('legacy_primal_joint_point_tests.jl', 'legacy_primal_working_row_scope_tests.jl'):
    assert f'include("{name}")' in (root / 'test/runtests.jl').read_text()
external = read('representable-external.toml')
assert external['production_sha256'] == metadata['prediction_anchor_production_sha256']
assert external['julia_threads'] == external['blas_threads'] == 1
assert len(external['cases']) == 80
assert len({(r['id'], r['algorithm'], r['basis_update'], r['backend']) for r in external['cases']}) == 80
assert all(r['status'] == 'OPTIMAL' and r['original_primal_certified'] and r['objective_matches']
           for r in external['cases'])
assert re.search(r'\|\s+245\s+245\s+', (results / 'representable-external.log').read_text())
local = json.loads((results / 'local-artifacts.json').read_text())
if (root / local['directory']).exists():
    for name, digest in local['sha256'].items():
        assert hashlib.sha256((root / local['directory'] / name).read_bytes()).hexdigest() == digest, name
print('Measured source, bounded recovery, regression and external evidence verified.')
print('Runtime reaches TIME_LIMIT in Phase I; convergence remains unresolved.')
