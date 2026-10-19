"""Independent offline review reproducer; no launch/control entrypoints or Julia."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from contextlib import ExitStack
import ast, hashlib, json, sys, tempfile
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import oracle as o, audit as a, control as c
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(D/'audit.py')=='9c27a6d73204f672c0c5f00fa9cc017f522cc6ea117e3cbf858cf1e6e5108924'
checks=[]
LOADED=dict(JSimplex='/stage/src/JSimplex.jl',Test='/test/Test.jl',LinearAlgebra='/la.jl',TOML='/toml.jl')
# Extract only reviewed fixture/helper definitions. Never execute tests.py's
# top-level test program, output writer, source checker or historical checkers.
names={'check','refuse','metric','fixture','toml_value','toml_doc','full_fixture','full_case','edit_json'}
tree=ast.parse((D/'tests.py').read_text())
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in names:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed-test-helper','exec'))
full_case('valid fixture accepted',success=True)
for bad in [None,True,-1,float('nan'),301]:
 def mutation(run,out,payload,bad=bad):
  v={'available_kib':8*1024**2,'swap_used_kib':0}
  if bad is not None:v['elapsed']=bad
  (out/'resources.jsonl').write_text(json.dumps(v)+'\n')
 full_case('invalid resource elapsed accepted: '+repr(bad),mutation,success=True)
def backwards(run,out,payload):
 mem={'available_kib':8*1024**2,'swap_used_kib':0}
 (out/'resources.jsonl').write_text('\n'.join(json.dumps(dict(mem,elapsed=t)) for t in [.8,.2])+'\n')
full_case('backwards resource timestamps accepted',backwards,success=True)
j=json.loads((D/'preparation-pins.json').read_text());required=json.loads((D/'required-paths.json').read_text())['paths']
assert len(j['sha256'])==74 and set(j['sha256'])==set(required)
assert all(sha(p)==h for p,h in j['sha256'].items())
assert not (D/'runs').exists() and not (D/'outers').exists()
result=dict(scope='Independent synthetic review; fixture host/source/pin boundaries mocked; real JSON/TOML audit; no Julia or entrypoint execution',finding_confirmed=True,checks=checks,preparation_count=74,all_preparation_hashes_match=True,pins_sha256=sha(D/'preparation-pins.json'),sha256={str(D/n):sha(D/n) for n in ['review_initial_tests.py','audit.py','oracle.py','control.py','tests.py','required-paths.json']})
with (D/'review-initial-evidence.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'finding_confirmed':True,'checks':len(checks),'preparation_hashes':74}))
