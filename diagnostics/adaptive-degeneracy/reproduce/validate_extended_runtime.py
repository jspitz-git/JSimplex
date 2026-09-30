"""Check the extended run, identical captured trajectory and diagnostic provenance."""
from pathlib import Path
import hashlib
from fractions import Fraction
import json
import subprocess
import tempfile
import tomllib

root=Path(__file__).resolve().parents[3]
reproduce=Path(__file__).resolve().parent
results=root/'diagnostics/adaptive-degeneracy/results/extended-runtime'

def read(name):
    return tomllib.loads((results/name).read_text())

h=hashlib.sha256()
files=[Path('Project.toml')]+[p.relative_to(root) for p in (root/'src').rglob('*.jl')]
for path in sorted(files,key=lambda p:p.as_posix()):
    h.update((path.as_posix()+'\0').encode());h.update((root/path).read_bytes())
assert h.hexdigest()=='1abe1ec7943e8736581d61b5f4b7a04ac5d1c5184148df0f7d7adad4be41d73c'
reports=[results/'runtime-representable-long.toml',results/'runtime-extended-capture.toml']
long,capture=(tomllib.loads(p.read_text()) for p in reports)
for report in (long,capture):
    assert report['production_sha256']==h.hexdigest()
    assert report['input_sha256']=='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
    assert report['status']=='NUMERICAL_ERROR' and report['iterations']==19222
    assert report['message']=='primal point could not be certified'
    assert report['time_limit']==900 and 300<report['seconds']<900
    assert report['refactorizations']==3936
    assert report['events']['primal_projection_attempt']==94
    assert report['events']['primal_point_projected']==93
    assert report['events']['phase_one']==1
    assert report['julia_threads']==report['blas_threads']==1
    assert report['events'].get('precision_boost',0)==0
assert long['events']==capture['events']
assert long['policy']==capture['policy']
keys=('event','iteration','objective','pinf','pinf_count','dinf','dinf_count','pricing',
      'bound_perturbation_active','original_bounds_active','bound_level','cost_level')
assert [[r.get(k) for k in keys] for r in long['records']]==[
    [r.get(k) for k in keys] for r in capture['records']]
for validator in ('validate_phase_one_reports.py','validate_intervention_reports.py'):
    subprocess.run(['python3',str(reproduce/validator),*map(str,reports)],check=True)
with tempfile.TemporaryDirectory(prefix='jsimplex-extended-') as directory:
    output=Path(directory)/'summary.json'
    subprocess.run(['python3',str(reproduce/'analyze_extended_runtime.py'),str(reports[0]),
        str(results.parent/'representable-point/runtime-representable-anchor.toml'),str(output)],
        stdout=subprocess.DEVNULL,check=True)
    assert json.loads(output.read_text())==json.loads((results/'runtime-representable-long-summary.json').read_text())
probe=read('runtime-representable-long-point.toml')
assert not probe['accepted'] and probe['restored']
assert probe['records'][0]['equations']
assert len(probe['records'][0]['bound_failures'])==14
assert not probe['records'][0]['nonbasic_bound_failures']
inspection=read('runtime-extended-inspection.toml')
assert not inspection['accepted'] and inspection['restored']
assert inspection['records'][0]['certified']
assert all(r['nonbasic_unchanged'] for r in inspection['sweeps'])
assert inspection['step']==0 and inspection['pivot']>0.9
assert len(inspection['sweeps'])==8
for sweep in inspection['sweeps'][1:]:
    assert not sweep['certified'] and not sweep['bounds']
    assert len(sweep['rows'])==1 and sweep['rows'][0]['row']==25695
    assert sweep['rows'][0]['equation_ok'] and not sweep['rows'][0]['model_ok']
pair=read('runtime-extended-pair-proof.toml')
assert not pair['witnesses']
proof=pair['contradiction']
q=lambda value: Fraction(value.replace('//','/'))
assert proof['same_basic_coefficients']
assert q(proof['fixed_lower_constant'])==q(proof['fixed_upper_constant'])==0
lower=Fraction(proof['working_lower'])-Fraction(proof['tolerance'])
upper=Fraction(proof['fixed_upper_activity'])+Fraction(proof['tolerance'])
assert lower==q(proof['required_lower_exact'])
assert upper==q(proof['required_upper_exact'])
assert lower-upper==q(proof['gap_exact'])==Fraction(1,4722366482869645213696)
assert pair['transition']['changed_nonbasic_coordinates']==[8504]
assert pair['transition']['retained_prepoint_certified_with_new_basis']
transition=read('runtime-extended-transition.toml')
assert transition['baseline_snap_guard_accepts'] and transition['baseline_status']=='NUMERICAL_ERROR'
assert transition['candidate_pivot_completed'] and transition['candidate_certified']
assert transition['same_captured_basis'] and transition['same_pre_pivot_point']
assert transition['iteration']==19222 and transition['maximum_change']==0
assert transition['leaving_before']==transition['leaving_after']<0
manifest=json.loads((results/'local-artifacts.json').read_text())
local=root/manifest['directory']
if local.exists():
    sha=lambda name: hashlib.sha256((local/name).read_bytes()).hexdigest()
    assert inspection['before_sha256']==transition['before_sha256']==sha('runtime-extended-capture-before.bin')
    assert pair['point_sha256']==sha('runtime-extended-inspection.toml-sweep_8.bin')
    assert pair['context_sha256']==sha('runtime-extended-inspection.toml-context.bin')
    assert transition['method_sha256']==sha('runtime-extended-transition.toml-method.jl')
    assert probe['snapshot_sha256']==sha('runtime-representable-long.bin')
    for name,digest in manifest['sha256'].items():
        assert hashlib.sha256((local/name).read_bytes()).hexdigest()==digest,name
print('Extended run and captured failure match; production sources are unchanged.')
print('Further objective reduction precedes a numerical error at iteration 19222.')
