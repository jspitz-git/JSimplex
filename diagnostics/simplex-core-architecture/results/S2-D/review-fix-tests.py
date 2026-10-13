from pathlib import Path
import ast,json,hashlib,copy
from common_reviewed import allowance_valid,manifest_ok,D,command,OUT
source=(D/'launcher-reviewed.py').read_text();tree=ast.parse(source)
checks={'no_assert_nodes':not any(isinstance(n,ast.Assert) for n in ast.walk(tree))}
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require')
for opt in (0,1,2):
 ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<new gate only>','exec',optimize=opt),ns)
 for value in (False,None,0,[]):
  try:ns['require'](value,'expected refusal')
  except ValueError:ok=True
  else:ok=False
  checks[f'optimized{opt}_reject_{repr(value)}']=ok
 checks[f'optimized{opt}_true']=ns['require'](True,'unused') is None
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require']
checks['eight_unconditional_gates']=len(calls)==8
required=['admission-reviewed.md','driver-reviewed.jl','common_reviewed.py','launcher-reviewed.py','audit-reviewed.py','guard.py','fixtures.toml','budget.json','required-paths-reviewed.json','admission-pins-reviewed.json','final-review.md','final-review-check.json','launch-pins.json']
a={'accepted':True,'numerical_allowance':True,'unresolved_findings':[],'attempts':1,'stage':'S2-D-qualification-1','command':command(),'output':str(OUT),'refs':{'fixture':'only'},'pins_sha256':'hash','sha256':{str(D/n):'hash' for n in required}}
checks['synthetic_valid_allowance']=allowance_valid(a,'hash',{'fixture':'only'},lambda p:'hash')
for key,value in [('accepted',False),('numerical_allowance',False),('attempts',True),('attempts',2),('unresolved_findings',['x']),('stage','other'),('command',[]),('output','other'),('refs',{}),('pins_sha256','wrong'),('sha256',{})]:
 b=copy.deepcopy(a);b[key]=value;checks[f'refuse_{key}_{repr(value)}']=not allowance_valid(b,'hash',{'fixture':'only'},lambda p:'hash')
checks['manifest_empty_rejected']=not manifest_ok({'files':[],'inventory':{},'trees':[],'inputs':[]},{str(D/'driver-reviewed.jl'):'hash'},lambda p:'hash')
checks['original755_preserved']='755' in (D/'driver.jl').read_text()
checks['corrected655_both']='755' not in (D/'driver-reviewed.jl').read_text() and '755' not in (D/'audit-reviewed.py').read_text()
paths=[D/n for n in ['review-fix-tests.py','driver-reviewed.jl','common_reviewed.py','launcher-reviewed.py','audit-reviewed.py','review-fix.json']]
with (D/'review-fix-tests.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'scope':'Only new pure helper functions and extracted require AST executed; no main, guard, launcher, Julia or old script invoked','sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},f,indent=2);f.write('\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
