"""Offline configuration and gate tests; no outer/seal/launcher or Julia."""
from pathlib import Path
import sys,json,copy
from unittest.mock import patch
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):
 c.require(v,n);checks[n]=True
def reject(n,f):
 try:f()
 except (RuntimeError,KeyError,FileNotFoundError):checks[n]=True
 else:raise RuntimeError('Accepted '+n)
cfg=c.config('red300');m=c.rd(c.REPAIR/'stage.json')
ck('master_stage',cfg['stage']==m['stage'])
ck('new_private_run_root',Path(cfg['run'])==D/'runs/red300' and not Path(cfg['run']).exists())
ck('new_driver',cfg['command'][-4]==str(D/'driver.jl'))
ck('exact_300',cfg['seconds']==300 and cfg['expected_exit']==1 and cfg['mode']=='red')
ck('guard_292',c.guard_command(cfg,D/'pins',10)[c.guard_command(cfg,D/'pins',10).index('--seconds')+1]=='292')
ck('loaded_path',c.loaded_for(cfg)['JSimplex']==str(Path(m['stage'])/'src/JSimplex.jl'))
for phase in ['green300','red600','red','',None]:reject('phase_'+str(phase),lambda:c.config(phase))
ck('predecessor_empty',c.predecessor('red300')==([],[]));reject('no_green_predecessor',lambda:c.predecessor('green300'))
ck('all_old_groups',len(c.rd(D/'host-entry.json')['groups'])==271)
c.validate_stage_binding();checks['stage_binding']=True
real=c.rd
for label,mut in [('old_stage',lambda j:j['red'].update(path=str(c.OLD/'stages.json'))),('changed_hash',lambda j:j['red']['sha256'].update({'src/factorization.jl':'0'*64})),('extra_mode',lambda j:j.update(green=j['red']))]:
 bad=copy.deepcopy(real(D/'stages.json'));mut(bad)
 with patch.object(c,'rd',lambda p:bad if Path(p)==D/'stages.json' else real(p)):reject(label,c.validate_stage_binding)
# Pure receipt validator must reject wrong scope, nonboolean acceptance, omissions and hash drift.
import tempfile
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'pins';p.write_text('fixed');v=dict(accepted=True,findings=[],scope='BG blocked U RED2 preparation',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 c.verify_review(v,p,[str(p)],v['scope']);checks['valid_review']=True
 for label,change in [('wrong_scope',dict(scope='BG blocked U driver preparation')),('nonboolean',dict(accepted=1)),('findings',dict(findings=['x'])),('missing_binding',dict(sha256={})),('bad_pin',dict(pins_sha256='0'*64))]:
  bad=dict(v,**change);reject(label,lambda:c.verify_review(bad,p,[str(p)],v['scope']))
ck('no_run_or_outer',not (D/'runs').exists() and not (D/'outers').exists())
c.save(D/'routing-tests.json',dict(all_passed=True,checks=checks,scope=__doc__))
print('Routing/gates PASS',len(checks))
