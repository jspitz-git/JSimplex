"""Independent bounded review of R1 correction; synthetic data only, no entrypoints."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from contextlib import ExitStack
import ast,hashlib,json,sys,tempfile
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import oracle as o,audit as a,control as c
checks=[]
LOADED=dict(JSimplex='/stage/src/JSimplex.jl',Test='/test/Test.jl',LinearAlgebra='/la.jl',TOML='/toml.jl')
names={'check','refuse','metric','fixture','toml_value','toml_doc','full_fixture','full_case','edit_json'}
for node in ast.parse((D/'tests_reviewed.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed-fixture-helper','exec'))
full_case('valid complete audit',success=True)
for bad in [None,True,False,-1,float('nan'),float('inf'),301,1.1,'0.5']:
 def mutation(run,out,payload,bad=bad):
  v={'available_kib':8*1024**2,'swap_used_kib':0}
  if bad is not None:v['elapsed']=bad
  (out/'resources.jsonl').write_text(json.dumps(v)+'\n')
 full_case('reject elapsed '+repr(bad),mutation)
def samples(times):
 def mutation(run,out,payload):
  (out/'resources.jsonl').write_text('\n'.join(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=t,child_memory=['VmRSS: 1000 kB'])) for t in times)+'\n')
 return mutation
full_case('reject backwards timestamps',samples([.8,.2]))
full_case('valid monotonic boundary timestamps',samples([0,.5,1]),success=True)
full_case('valid equal timestamps',samples([.5,.5]),success=True)
terminal=dict(available_kib=8*1024**2,swap_used_kib=0)
check('exact292 limit valid',a.resource_records([dict(terminal,elapsed=292)],terminal,292))
for duration in [True,-1,293,float('nan')]:refuse('reject duration '+repr(duration),lambda duration=duration:a.resource_records([dict(terminal,elapsed=0)],terminal,duration))
for field,bad in [('available_kib',True),('available_kib',1),('swap_used_kib',1024**2+1)]:
 badmem=dict(terminal,**{field:bad});refuse('reject terminal '+field+repr(bad),lambda badmem=badmem:a.resource_records([dict(terminal,elapsed=0)],badmem,1))
q=fixture()
for name in o.PREPARATION:q[name].update(gc_seconds=.2,compile_seconds=.3,recompile_seconds=.1)
for i in range(1,13):
 for key in ['bytes_wrapper','events_wrapper','consumed_result']:q[f'record-{i}.toml'][key].update(gc_seconds=.2,compile_seconds=.3,recompile_seconds=.1)
 q['raw.toml']['records'][i-1]=deepcopy(q[f'record-{i}.toml'])
r=o.validate(q,LOADED)
check('nonzero costs retained without qualification',r['p011_accepted'] is False and r['red_accepted'] is False and all(not x['clean_wrapper_indices'] for x in r['descriptive_sample_counters'].values()))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
result=dict(all_passed=True,count=len(checks),checks=checks,scope='Independent synthetic correction review; mocked external boundaries, real JSON/TOML and complete audit; no Julia, launch, seal, guard or outer entrypoints',sha256={str(D/n):sha(D/n) for n in ['review_final_tests.py','audit.py','oracle.py','control.py','tests_reviewed.py']})
with (D/'review-final-evidence.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks)}))
