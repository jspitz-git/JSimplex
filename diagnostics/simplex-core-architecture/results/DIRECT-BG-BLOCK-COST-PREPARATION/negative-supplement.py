from pathlib import Path
import copy,json,tempfile
from unittest.mock import patch
import control as c
from analysis import first_process_viable
checks={}
def check(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
fixtures=c.rd(c.D/'inputs.json')['fixtures']
cells=[dict(fixture=f['name'],manager='BG',backend=b,policy='threshold_one' if b=='native' else 'default',statistics=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,probe_memory_gate=True,faster_pairs=3)) for f in fixtures for b in ['native','markowitz']]
a=dict(all_passed=True,pure_timeout=False,cells=cells)
check('all_eight_first_pass',first_process_viable(a,fixtures))
for i in range(8):
 for field in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate','faster_pairs']:
  b=copy.deepcopy(a);b['cells'][i]['statistics'][field]=2 if field=='faster_pairs' else False
  check(f'reject_cell{i}_{field}',not first_process_viable(b,fixtures))
for key,value in [('all_passed',False),('pure_timeout',True),('cells',cells[:7])]:
 b=copy.deepcopy(a);b[key]=value;check('reject_'+key,not first_process_viable(b,fixtures))
for phase in ['red300','cost3-300','cost1-45','cost1-301']:
 try:c.config(phase)
 except RuntimeError:check('unknown_'+phase,True)
 else:check('unknown_'+phase,False)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);(root/'runs').mkdir();(root/'runs'/'cost1-600').mkdir()
 with patch.object(c,'D',root),patch.object(c,'config',lambda phase:dict(process=1)),patch.object(c,'rd',lambda p:dict(sha256={})),patch.object(c,'bindings',lambda j:True):
  try:c.predecessor('cost1-300')
  except RuntimeError as e:check('reject_prior_extra_attempt','out-of-order' in str(e))
  else:check('reject_prior_extra_attempt',False)
# A warning cannot become a pure timeout admission.
from evidence import timeout_ok
p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);s=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
for marker in ['WARNING:','Warning:','world age','ERROR:']:
 check('mixed_warning_'+marker,not timeout_ok(p,s,'BEGIN matched policy cost '+marker,292,300))
c.save(c.D/'negative-supplement.json',dict(all_passed=True,checks=checks,scope='Synthetic Python only'))
print('Supplement',len(checks),'PASS')
