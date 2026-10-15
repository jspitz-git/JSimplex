"""One-shot offline exact audit. Cost gates do not erase a correct slow result."""
from evidence import *
def audit(phase):
 cfg=phase_config(phase);checks={};results=[];error=''
 try:checks,results=phase_checks(phase)
 except Exception as e:error=repr(e);checks=dict(complete=False)
 paths=set(phase_paths(phase,cfg))|{p for p in Path(cfg['output']).rglob('*') if p.is_file()}
 selection=[]
 if phase=='cost2' and all(checks.values()):
  first=rd(D/'cost1-audit.json');req(first['all_passed'],'First process failed')
  for a,b in zip(first['cells'],results):
   req(all(a[k]==b[k] for k in ('fixture','manager','backend')),'Cell mismatch')
   selection.append({**{k:a[k] for k in ('fixture','manager','backend')},'promising':qualify(a['statistics'],b['statistics'])})
  paths.add(D/'cost1-audit.json')
 result=dict(all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,cells=results,selection=selection,
  scope='Instrumented eight-update/two-refactor component cost only; no native-refinement equivalence, peak/native memory, public trajectory or promotion',
  sha256={str(p):sha(p) for p in sorted(paths) if p.is_file()})
 save(D/(phase+'-audit.json'),result);return result
if __name__=='__main__':
 import sys
 req(audit(sys.argv[1])['all_passed'],'Audit rejected; preserve and stop')
