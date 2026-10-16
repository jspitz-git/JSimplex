"""New pure-Python environment/routing refusal tests; never launch or stage."""
from pathlib import Path
import json,sys,os,copy
D=Path(__file__).resolve().parent;checks={};error=''
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def refuses(fn):
 try:fn();return False
 except Exception:return True
try:
 import control as c
 check('new_control_exists',True)
 check('new_environment_exact',c.validate_environment() is None)
 cfg=c.config('integration');check('new_routing',str(D) in cfg['run'] and 'native-pivot-integration-env1' in cfg['stage'])
 check('original_driver',cfg['command'][-4]==str(c.DRIVER/'driver.jl'))
 check('caps_preserved',cfg['seconds']==60 and c.guard_command(cfg,Path('/tmp/pins'),10)[6:8]==['--seconds','52'])
 check('wrong_phase',refuses(lambda:c.config('cost')))
 baseline=dict(os.environ)
 try:
  for k,v in c.rd(D/'environment.json').items():
   os.environ[k]='__different_environment__'
   check('refuse_'+k,refuses(c.validate_environment))
   os.environ.clear();os.environ.update(baseline)
 finally:os.environ.clear();os.environ.update(baseline)
 old=c.rd(c.DRIVER/'environment.json')
 try:
  for k,v in old.items():
   if v is None:os.environ.pop(k,None)
   else:os.environ[k]=v
  check('refuse_old_environment',refuses(c.validate_environment))
 finally:os.environ.clear();os.environ.update(baseline)
 check('no_stage_runs',not Path(cfg['stage']).exists() and not (D/'runs').exists())
except Exception as x:error=repr(x);checks.setdefault('new_control_exists',False)
name=sys.argv[1]
with (D/name).open('x') as f:json.dump(dict(all_passed=not error and all(checks.values()),checks=checks,error=error,scope='Synthetic Python process-local environment mutations only; no Julia/stage'),f,indent=2);f.write('\n')
print(dict(checks=len(checks),error=error));sys.exit(1 if error else 0)
