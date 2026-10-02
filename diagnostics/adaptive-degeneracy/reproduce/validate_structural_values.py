"""Validate structural-retention regression evidence and measured source provenance."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tomllib

root = Path(__file__).resolve().parents[3]
reproduce = Path(__file__).resolve().parent
results = root / 'diagnostics/adaptive-degeneracy/results/structural-values'
metadata = json.loads((results / 'candidate.json').read_text())
context = hashlib.sha256()
files = [Path('Project.toml')] + [p.relative_to(root) for p in (root / 'src').rglob('*.jl')]
for path in sorted(files, key=lambda p: p.as_posix()):
    context.update((path.as_posix() + '\0').encode())
    context.update((root / path).read_bytes())
assert context.hexdigest() == metadata['production_sha256']

checks = (
    ('structural-final-green.log', 'Structural bound-value regressions', 284),
    ('structural-semantics.log', 'Structural retention and simplex semantic regressions', 7160),
    ('structural-compiled.log', 'Compiled structural retention and allocation checks', 1172),
    ('structural-replay.log', 'Earlier mathematical points remain recoverable', 15),
    ('structural-replay.log', 'Captured pivots finish with certified points', 23),
)
for name, label, count in checks:
    log = (results / name).read_text()
    assert re.search(re.escape(label) + rf'\s*\|\s*{count}\s+{count}\s', log), (name, label)
    assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', log), name

read = lambda name: tomllib.loads((results / name).read_text())
replay = read('structural-replay.toml')['records']
assert len(replay) == 9 and all(row['certified'] for row in replay)
pivots = [row for row in replay if row['kind'] == 'one pivot']
assert [row['iteration'] for row in pivots] == [6799, 8464, 14186, 19222]
assert all(row['completed'] and row['same_captured_basis'] for row in pivots)
assert all(row['same_prepoint'] and row['maximum_change'] == 0 for row in pivots[-2:])
for row in replay:
    path = root / '.superpowers/adaptive-degeneracy' / row['snapshot']
    if row['kind'] == 'one pivot':
        path = Path(str(path) + '-before.bin')
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], path

runtime_path = results / 'runtime-structural.toml'
runtime = read(runtime_path.name)
assert runtime['production_sha256'] == metadata['production_sha256']
assert runtime['input_sha256'] == 'd0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
assert runtime['time_limit'] == 900
assert runtime['algorithm'] == 'primal' and runtime['mode'] == 'both'
assert runtime['julia_threads'] == runtime['blas_threads'] == 1
assert runtime['events'].get('precision_boost', 0) == 0
assert runtime['events']['phase_one'] == 1
assert runtime['events']['pivot_rejected'] == 47170
assert runtime['events']['primal_point_preserved'] == 8
assert runtime['events']['pricing_dantzig'] == runtime['events']['pricing_steepest_edge'] == 8
assert runtime['events']['pricing_progress_return'] == 7
assert runtime['events']['pricing_trial_expired'] == 1
for event in ('perturbation', 'primal_projection_attempt', 'primal_point_projected', 'phase_primal'):
    assert runtime['events'].get(event, 0) == 0, event
samples = [row for row in runtime['records'] if row['event'] == 'pivot_completed']
assert len(samples) == 77 and samples[-1]['iteration'] == 77000
assert all(b['objective'] <= a['objective'] for a, b in zip(samples, samples[1:]))
assert all(row['pinf'] == 0 and not row['bound_perturbation_active'] for row in samples)
assert runtime['records'][-1]['observation_kind'] == 'uncertified_after_termination'
for key, value in metadata['runtime'].items():
    assert runtime[key] == value, key
for script in ('validate_phase_one_reports.py', 'validate_intervention_reports.py'):
    subprocess.run(['python3', str(reproduce / script), str(runtime_path)], check=True)

external = read('structural-external.toml')
assert external['production_sha256'] == metadata['production_sha256']
# The established external runner asserts objective and original feasibility
# separately for each of its eighty solves; retain both report and test log.
assert len(external['cases']) == 80
assert external['julia_threads'] == external['blas_threads'] == 1
assert all(row['status'] == 'OPTIMAL' and row['objective_matches'] and
           row['original_primal_certified'] for row in external['cases'])
keys = {(row['id'], row['algorithm'], row['basis_update'], row['backend']) for row in external['cases']}
assert len(keys) == 80
inputs = tomllib.loads((root / 'diagnostics/basis-selective-preparation/reproduce/external-inputs.toml').read_text())['cases']
expected = {(row['id'], algorithm, manager, backend) for row in inputs
            for algorithm in ('primal', 'dual')
            for manager in ('pfi', 'forrest_tomlin', 'suhl_suhl', 'bartels_golub')
            for backend in ('native', 'markowitz')}
assert keys == expected
hashes = {row['id']: row['sha256'] for row in inputs}
assert all(row['input_sha256'] == hashes[row['id']] for row in external['cases'])
assert re.search(r'External LP relaxations: native and Markowitz basis managers\s*\|\s*245\s+245\s',
                 (results / 'structural-external.log').read_text())
assert not re.search(r'Test Failed|Error During Test|(?:\A|\n)ERROR:', (results / 'structural-external.log').read_text())

manifest = json.loads((results / 'local-artifacts.json').read_text())
local = root / manifest['directory']
if local.exists():
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((local / name).read_bytes()).hexdigest() == digest, name
    for name in ('candidate.json', 'structural-replay.toml', 'runtime-structural.toml', 'structural-external.toml'):
        assert (local / name).read_bytes() == (results / name).read_bytes(), name
print('Structural retention: measured source, regressions, snapshots and run provenance validated')
