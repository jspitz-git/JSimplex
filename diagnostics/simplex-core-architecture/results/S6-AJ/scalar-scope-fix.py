from pathlib import Path
import json,hashlib
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');o=r/'diagnostics/simplex-core-architecture/results/S6-AJ';p=o/'coverage.json';before=p.read_bytes();d=json.loads(before)
inv=json.loads((r/'diagnostics/simplex-core-architecture/results/S6-A/ci-inventory-1.json').read_text()); es={f"{rr['run']}:{e['log_line']}":e for rr in inv['records'] for e in rr['entries']}
rows=[e for rr in d['runs'] for e in rr['rows'] if e['historical_file'].endswith('native_phase_transfer_tests.jl')]
def expected(e):return 'Float32 explicitly printed in this historical inventory entry' if e['historical_line']==211 else 'unknown for historical accepted=false phase entries'
red=[e['id'] for e in rows if e['scalar_scope']!=expected(e)]
assert len(red)==8 and len(rows)==16
assert all('SimplexWorkspace{Float32' in '\n'.join(es[e['id']]['details']) for e in rows if e['historical_line']==211)
with (o/'coverage-before-scalar-scope.json').open('xb') as f:f.write(before)
for e in rows:e['scalar_scope']=expected(e)
assert all(e['scalar_scope']==expected(e) for e in rows)
p.write_text(json.dumps(d,indent=2)+'\n')
with (o/'scalar-scope-fix.json').open('x') as f:json.dump({'author_severity':'Important: exact scalar attribution required by AJ; reviewer called Minor metadata','red_misclassified_ids':red,'red_count':8,'green_checks':16,'line211_explicit_Float32':8,'line164_unknown':8,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'numerical_calls':0,'original_mapper_rerun':False,'note':'reconcile.py is preserved original mapper. This standalone amendment produces the final structured scalar field; counts and all other values unchanged.'},f,indent=2);f.write('\n')
(o/'scalar-scope-fix.py').write_bytes(Path(__file__).read_bytes());print('RED 8 incorrect metadata -> GREEN16/16; original mapper/output preserved, zero numerics')
