"""Validate actual Phase-I transfer evidence and unchanged production sources."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / 'diagnostics/adaptive-degeneracy/results/phase-transfer'
metadata = json.loads((results / 'candidate.json').read_text())
context = hashlib.sha256()
files = [Path('Project.toml')] + [p.relative_to(root) for p in (root / 'src').rglob('*.jl')]
for path in sorted(files, key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == metadata['production_sha256']
capture_path = results / 'runtime-transfer-capture.toml'
capture = tomllib.loads(capture_path.read_text())
replay = tomllib.loads((results / 'runtime-transfer-replay.toml').read_text())
assert capture['production_sha256'] == metadata['production_sha256']
assert capture['time_limit'] == metadata['solver_seconds'] == 1800
assert capture['status'] == 'NUMERICAL_ERROR' and capture['iterations'] == 102446
assert capture['message'] == 'artificial removal could not be completed'
assert capture['events'].get('phase_primal', 0) == capture['events'].get('precision_boost', 0) == 0
assert replay['auxiliary_optimality_certified']
assert not replay['baseline_transfer_accepted'] and not replay['complete_export_accepted']
assert replay['nonzero_artificials'] == 16
assert replay['maximum_artificial_magnitude'] < 3e-11
changes = replay['changed_nonbasic_values']
assert len(changes) == len(replay['changed_nonbasic_indices']) == 1678
assert [r['index'] for r in changes] == replay['changed_nonbasic_indices']
assert sum(r['structural'] for r in changes) == 448
assert max(abs(r['mapped'] - r['reconstructed']) for r in changes) == replay['maximum_nonbasic_change'] < 1e-7
rows = {r['label']: r for r in replay['records']}
assert len(rows) == len(replay['records']) == 6
assert rows['auxiliary before transfer']['point_certified']
for prefix, expected in (('baseline nonbasic values', False), ('mapped nonbasic values', True)):
    for suffix in ('before completion', 'after completion'):
        row = rows[prefix + ' ' + suffix]
        assert row['point_certified'] == row['original_primal_feasible'] == expected
        assert row['basic_bounds_feasible'] == expected and row['finite']
        assert not row['basis_reliable']
        assert not row['primal_solve']['reliable'] and not row['dual_solve']['reliable']
    assert rows[prefix + ' after completion']['completion_returned_success'] == expected
assert not rows['mapped nonbasic values after completion']['same_mapped_point']
log = (results / 'runtime-transfer-replay.log').read_text()
assert re.search(r'Captured phase transfer replay\s*\|\s*8\s+8\s', log)
assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', log)
with tempfile.TemporaryDirectory(prefix='jsimplex-phase-transfer-') as directory:
    output = Path(directory) / 'summary.json'
    subprocess.run(['python3', str(reproduce / 'analyze_phase_transfer.py'), str(capture_path),
                    str(results.parent / 'structural-continuation/runtime-structural-1800.toml'),
                    str(results / 'runtime-transfer-replay.toml'), str(output)],
                   check=True, stdout=subprocess.DEVNULL)
    assert json.loads(output.read_text()) == json.loads((results / 'summary.json').read_text())
for name in ('validate_phase_one_reports.py', 'validate_intervention_reports.py'):
    subprocess.run(['python3', str(reproduce / name), str(capture_path)], check=True)
manifest = json.loads((results / 'local-artifacts.json').read_text())
assert replay['before_sha256'] == manifest['sha256']['runtime-transfer-capture-before.bin']
assert replay['fresh_sha256'] == manifest['sha256']['runtime-transfer-capture-fresh.bin']
assert capture['transfer_capture_method_sha256'] == manifest['sha256']['runtime-transfer-capture-method.jl']
assert replay['export_variant_sha256'] == manifest['sha256']['runtime-transfer-replay-export-method.jl']
local = root / manifest['directory']
if local.exists():
    for name, digest in manifest['sha256'].items():
        with (local / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
    for name in ('candidate.json', 'runtime-transfer-capture.toml', 'runtime-transfer-replay.toml',
                 'runtime-transfer-replay.log', 'summary.json'):
        assert (local / name).read_bytes() == (results / name).read_bytes(), name
print('Actual phase transfer: source, 137-event agreement, replay outcomes and local provenance validated')
