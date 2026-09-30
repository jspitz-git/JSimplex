"""Validate the longer runtime experiment against measured production sources."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / 'diagnostics/adaptive-degeneracy/results/structural-continuation'
metadata = json.loads((results / 'candidate.json').read_text())
context = hashlib.sha256()
files = [Path('Project.toml')] + [p.relative_to(root) for p in (root / 'src').rglob('*.jl')]
for path in sorted(files, key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == metadata['production_sha256']
report_path = results / 'runtime-structural-1800.toml'
report = tomllib.loads(report_path.read_text())
assert report['production_sha256'] == metadata['production_sha256']
assert report['time_limit'] == metadata['solver_seconds'] == 1800
assert report['input_sha256'] == 'd0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
assert report['algorithm'] == 'primal' and report['mode'] == 'both'
assert report['julia_threads'] == report['blas_threads'] == 1
assert report['events'].get('precision_boost', 0) == 0
for key, expected in metadata['result'].items():
    assert report[key] == expected, key
for script in ('validate_phase_one_reports.py', 'validate_intervention_reports.py'):
    subprocess.run(['python3', str(reproduce / script), str(report_path)], check=True)
with tempfile.TemporaryDirectory(prefix='jsimplex-structural-long-') as directory:
    output = Path(directory) / 'summary.json'
    subprocess.run(['python3', str(reproduce / 'analyze_structural_continuation.py'),
                    str(report_path), str(results.parent / 'structural-values/runtime-structural.toml'),
                    str(output)], check=True, stdout=subprocess.DEVNULL)
    assert json.loads(output.read_text()) == json.loads((results / 'summary.json').read_text())
assert report['status'] == 'NUMERICAL_ERROR' and report['iterations'] == 102446
assert report['events'].get('artificial_removed', 0) == 0
assert report['events'].get('phase_primal', 0) == 0
assert report['events'].get('perturbation', 0) == 0
assert report['events'].get('primal_projection_attempt', 0) == 0
final = report['records'][-1]
assert final['columns'] == 31615 and final['pinf_count'] == 10 and final['pinf'] > 1e-5
assert final['observation_kind'] == 'uncertified_after_termination'
probe = tomllib.loads((results / 'structural-phase-transfer.toml').read_text())
fixture = root / 'test/legacy_primal_structural_value_tests.jl'
assert hashlib.sha256(fixture.read_bytes()).hexdigest() == probe['fixture_sha256']
assert len(probe['records']) == 16
expected = {(precision, sign, manager) for precision in ('Float32', 'Float64')
            for sign in (-1, 1) for manager in ('pfi', 'forrest_tomlin', 'suhl_suhl', 'bartels_golub')}
assert {(r['precision'], r['sign'], r['basis_update']) for r in probe['records']} == expected
for row in probe['records']:
    assert not row['baseline_transfer_accepted'] and not row['mapped_nonbasic_only_feasible']
    assert row['mapped_point_completion_accepted'] and row['same_mapped_point']
    assert row['original_primal_certified'] and row['artificial_value'] == 0
log = (results / 'structural-phase-transfer.log').read_text()
assert re.search(r'Portable structural point transfer control\s*\|\s*192\s+192\s', log)
assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', log)
manifest = json.loads((results / 'local-artifacts.json').read_text())
local = root / manifest['directory']
if local.exists():
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((local / name).read_bytes()).hexdigest() == digest, name
    for name in ('candidate.json', 'runtime-structural-1800.toml', 'summary.json', 'structural-phase-transfer.toml', 'structural-phase-transfer.log'):
        assert (local / name).read_bytes() == (results / name).read_bytes(), name
print('Longer runtime: source, common trajectory, adaptive ordering and local provenance validated')
