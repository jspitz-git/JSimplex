"""One-shot offline identity and schedule checks; no numerical auditor run."""
from pathlib import Path
import json,hashlib,ast,tomllib,sys
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(D))
from control import predecessor,config,full_host,sha,rd,save,require,git
m=rd(D/'source-map.json');checks={};files={D/'source-map.json',D/'source-check.py'}
checks['byte_identical']=all((D/n).read_bytes()==Path(p).read_bytes() for n,p in m['byte_identical'].items())
for n,p in m['byte_identical'].items():files|={D/n,Path(p)}
for n,z in m['changed'].items():
 s=(D/n).read_text()
 for e in reversed(z['edits']):
  require(s.count(e['after'])==1,'Inverse uniqueness '+n);s=s.replace(e['after'],e['before'],1)
 checks['inverse_'+n]=s==Path(z['source']).read_text();files|={D/n,Path(z['source'])}
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
inputs=rd(D/'inputs.json');t=tomllib.loads((D/'inputs.toml').read_text())
checks['input_formats']=t['fixtures']==inputs['fixtures']
fs=inputs['fixtures'];schedule=inputs['schedule']
checks['four_fixtures']=len(fs)==4 and sorted(f['matrix']['n'] for f in fs)==[32,32,96,96]
expected=[]
for f in fs:
 for r in range(1,12):
  for arm in ('C','P') if r%2 else ('P','C'):expected.append(dict(id=len(expected)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
checks['88_exact_schedule']=schedule==expected and len(schedule)==88
checks['24_warm_64_measured']=sum(s['warm'] for s in schedule)==24 and sum(not s['warm'] for s in schedule)==64
checks['payload']=sum(f['matrix']['n']*22*48*8 for f in fs)==2162688 and 88*4*48*8==135168
checks['selected_work']=88*2==176 and 88*48==4224 and 88*32==2816 and 88*16==1408
checks['old_cost_unexecuted']=not (D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/cost').exists()
pred,groups=predecessor('cost');files.update(pred)
checks['accepted_predecessor']=len(groups)==214
checks['unchanged_actual_sources']=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce')
checks['new_run_absent']=not (D/'runs').exists() and not Path(config('cost')['stage']).exists()
checks['original_failed_green']=rd(D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False
checks['original_direct_cost_failed']=rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False
h=full_host(groups);save(D/'source-host.json',h);checks['fresh_host']=not h['matches'] and h['head']=='294d4435e888577d90533b50c3c44da6702976e6' and h['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
files|={D/'inputs.json',D/'inputs.toml',D/'source-host.json',D/'offline-tests.py',D/'offline-RED.json',D/'offline-GREEN.json'}
save(D/'source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in sorted(files)},scope='Source identities and schedule arithmetic only; no Julia/parser/import/compile/run or historical auditor replay'))
require(all(checks.values()),'Source check failed: preserve');print(dict(checks=len(checks),bindings=len(files),all_passed=True))
