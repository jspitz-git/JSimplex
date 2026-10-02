"""Compare the repair corpus while recording the changed coverage instrumentation."""
import json
from pathlib import Path
import sys
import tomllib

base_path,candidate_path,output_path=map(Path,sys.argv[1:])
base=tomllib.loads(base_path.read_text())
candidate=tomllib.loads(candidate_path.read_text())
for field in ('julia','jump','julia_threads','blas_threads','policy',
              'original_retry_enabled','weak_pivot_preference'):
    assert base[field]==candidate[field],field

def key(row):
    return tuple(row[k] for k in ('id','reader','algorithm','manager','seed'))

a={key(r):r for r in base['records']}
b={key(r):r for r in candidate['records']}
assert len(a)==len(base['records']) and len(b)==len(candidate['records'])
assert a.keys()==b.keys()
changes=[]
fields=('status','iterations','refactorizations','objective','phases','events',
        'pivot_observations','zero_primal_steps')
for k,after in b.items():
    before=a[k]
    assert before['input_sha256']==after['input_sha256']
    assert after['exact_model_match']
    assert after['passed'] and after['status']=='OPTIMAL'
    assert all(after[x] for x in ('reader_primal_feasible','original_primal_feasible','objective_matches'))
    differing={f:{'before':before.get(f),'after':after.get(f)} for f in fields if before.get(f)!=after.get(f)}
    if differing:
        changes.append({'case':k,'changes':differing})
report={'cases':len(b),'all_verified':True,'trajectory_fields':fields,
        'identical_cases':len(b)-len(changes),'changes':changes,
        'base_production_sha256':base['production_sha256'],
        'candidate_production_sha256':candidate['production_sha256'],
        'base_diagnostic_sha256':base['diagnostic_sha256'],
        'candidate_diagnostic_sha256':candidate['diagnostic_sha256'],
        'instrumentation_note':'Phase coverage now handles the coupled fallback; diagnostic hashes are recorded, not asserted equal.',
        'coupled_attempts':sum(r['coverage'].get('coupled_attempts',0) for r in b.values()),
        'coupled_certified':sum(r['coverage'].get('coupled_certified',0) for r in b.values())}
output_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('changes','base_diagnostic_sha256','candidate_diagnostic_sha256')},indent=2))
