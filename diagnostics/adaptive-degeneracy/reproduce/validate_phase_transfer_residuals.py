"""Validate native residual localization and correction evidence."""
from pathlib import Path
import hashlib
import json
import re
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / 'diagnostics/adaptive-degeneracy/results/phase-transfer-residuals'
report = tomllib.loads((results / 'runtime-transfer-residuals.toml').read_text())
context = hashlib.sha256()
files = [Path('Project.toml')] + [p.relative_to(root) for p in (root / 'src').rglob('*.jl')]
for path in sorted(files, key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == report['production_sha256']
prior = tomllib.loads((results.parent / 'phase-transfer/runtime-transfer-replay.toml').read_text())
assert report['before_sha256'] == prior['before_sha256']
helper = Path(__file__).with_name('replay_phase_transfer.jl')
assert hashlib.sha256(helper.read_bytes()).hexdigest() == report['helper_sha256']
assert report['iteration'] == 102446 and report['scalar_type'] == 'Float64'
assert report['julia_threads'] == report['blas_threads'] == 1
assert report['solve_tolerance'] == 256 * 2**-52 and report['primal_tolerance'] == 1e-7
rows = {r['label']: r for r in report['records']}
expected = {'mapped reconstruction': (13, 7), 'primal correction': (13, 7),
            'dual correction': (13, 3), 'both corrections': (13, 3),
            'unaccepted cleanup proposal': (233, 0), 'existing native cleanup': (13, 7)}
assert len(rows) == len(report['records']) == len(expected)
for label, counts in expected.items():
    row = rows[label]
    assert row['point_certified'] and row['original_primal_feasible']
    assert row['basic_bounds_feasible'] and row['finite'] and row['pinf_count'] == 0
    assert not row['basis_reliable']
    for key, count in zip(('primal_residual', 'dual_residual'), counts):
        q = row[key]
        assert q['rows_above_tolerance'] == len(q['bad_equations']) == count
        assert q['reliable'] == (count == 0)
        assert q['largest_bad_absolute_residual'] <= q['absolute_error']
primal = rows['primal correction']['primal_residual']
dual = rows['dual correction']['dual_residual']
assert primal['bad_homogeneous_equations'] == 12 and dual['bad_homogeneous_equations'] == 3
assert primal['largest_bad_absolute_residual'] < 2e-30
assert dual['largest_bad_absolute_residual'] < 2e-29
inhomogeneous = next(r for r in primal['selected_rows'] if r['equation'] == 4933)
assert inhomogeneous['rhs'] != 0 and inhomogeneous['ratio'] > report['solve_tolerance']
cleanup = rows['unaccepted cleanup proposal']
for detail, cleared, protected in zip(cleanup['cleanup_details'], (525, 159), (341, 77)):
    assert len(detail['cleared_indices']) == cleared
    assert len(detail['cleared_with_inhomogeneous_support']) == protected
assert cleanup['primal_residual']['bad_homogeneous_equations'] == 0
before = set(primal['bad_equations'])
after = set(cleanup['primal_residual']['bad_equations'])
assert len(before & after) == 1 and len(after - before) == 232
assert not rows['existing native cleanup']['cleanup_returned_success']
assert rows['existing native cleanup']['maximum_primal_change'] == 0
log = (results / 'runtime-transfer-residuals.log').read_text()
assert re.search(r'Phase transfer native residual diagnosis\s*\|\s*9\s+9\s', log)
assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', log)
manifest = json.loads((results / 'local-artifacts.json').read_text())
local = root / manifest['directory']
if local.exists():
    for name, digest in manifest['sha256'].items():
        with (local / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
    for name in ('runtime-transfer-residuals.toml', 'runtime-transfer-residuals.log'):
        assert (local / name).read_bytes() == (results / name).read_bytes(), name
print('Phase transfer residuals: native corrections, rejected cleanup, unchanged source and provenance validated')
