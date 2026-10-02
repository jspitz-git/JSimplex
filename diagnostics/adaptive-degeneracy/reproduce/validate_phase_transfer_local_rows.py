"""Validate the experimental local reconstruction and complete boundary export."""
from pathlib import Path
import hashlib
import json
import re
import tomllib

root = Path(__file__).resolve().parents[3]
results = root / 'diagnostics/adaptive-degeneracy/results/phase-transfer-local-rows'
report = tomllib.loads((results / 'runtime-local-export.toml').read_text())
context = hashlib.sha256()
files = [Path('Project.toml')] + [p.relative_to(root) for p in (root / 'src').rglob('*.jl')]
for path in sorted(files, key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == report['production_sha256']
for name, key in (('probe_phase_transfer_residuals.jl', 'residual_helper_sha256'),
                  ('replay_phase_transfer.jl', 'replay_helper_sha256')):
    assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() == report[key]
prior = tomllib.loads((results.parent / 'phase-transfer/runtime-transfer-replay.toml').read_text())
assert report['before_sha256'] == prior['before_sha256']
assert report['scalar_type'] == 'Float64'
assert report['julia_threads'] == report['blas_threads'] == 1
assert report['complete_export_accepted'] and not report['zero_sweep_export_accepted']
assert report['export_pricing'] == 'steepest_edge'
trace = report['local_trace']
assert len(trace) == 2 and [r['bad_before'] for r in trace] == [13, 5]
assert not trace[0]['reliable_after'] and trace[1]['reliable_after']
changes = [c for r in trace for c in r['changes']]
assert len(changes) == len({c['coordinate'] for c in changes}) == 18
assert max(abs(c['new'] - c['old']) for c in changes) < 2e-30 < report['cutoff']
rows = report['records']
assert [r['label'] for r in rows] == ['local row candidate', 'complete local export']
for row in rows:
    assert row['finite'] and row['basis_reliable'] and row['basic_bounds_feasible']
    assert row['point_certified'] and row['original_primal_feasible']
    assert row['pinf'] == 0 and row['pinf_count'] == 0
    for key in ('primal_solve', 'dual_solve', 'primal_residual', 'dual_residual'):
        assert row[key]['reliable'] and row[key]['relative_error'] < 256 * 2**-52
    assert not row['primal_residual']['bad_equations'] and not row['dual_residual']['bad_equations']
assert {k:v for k,v in rows[0].items() if k != 'label'} == {k:v for k,v in rows[1].items() if k != 'label'}
assert report['portable_positive_point'] == [-1e-66, 1e-66]
assert report['portable_rejection_sweeps'] == report['maximum_sweeps'] == 8
assert len(report['portable_rejection_trace']) == 8
assert not any(r['reliable_after'] for r in report['portable_rejection_trace'])
log = (results / 'runtime-local-export.log').read_text()
assert re.search(r'Local phase transfer row reconstruction\s*\|\s*16\s+16\s', log)
assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', log)
manifest = json.loads((results / 'local-artifacts.json').read_text())
assert report['export_variant_sha256'] == manifest['sha256']['runtime-local-export-export-method.jl']
local = root / manifest['directory']
if local.exists():
    for name, digest in manifest['sha256'].items():
        with (local / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
    for name in ('runtime-local-export.toml', 'runtime-local-export.log'):
        assert (local / name).read_bytes() == (results / name).read_bytes(), name
print('Local phase export: unchanged source, two-sweep repair, certificates and rejection controls validated')
