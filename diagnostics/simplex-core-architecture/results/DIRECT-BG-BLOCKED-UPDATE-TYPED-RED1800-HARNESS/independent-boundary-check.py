"""Additional fresh independent Python-only boundary fixtures. No runtime entrypoints."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import sys,json,tempfile,importlib.util,hashlib
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import control as c,audit as a,oracle as o
checks=[]
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def reject(n,f):
 try:f()
 except (RuntimeError,ValueError,KeyError,TypeError,FileNotFoundError):checks.append(n);return
 raise AssertionError('Accepted '+n)
# Fresh source bytes and resolved runtime identities, without Git or Julia calls.
for label,root in [('diagnostic',c.R),('production',c.W)]:
 for name,h in c.rd(D/'baseline.json')[label].items():ck(label+':'+name,c.sha(root/name)==h)
inv=c.rd(D/'runtime-inputs-complete.json')['inventory'];ck('609 current runtime resolved paths and hashes',len(inv)==609 and c.guard.inventory(list(inv),[])==inv)
stages=c.rd(D/'stages.json')
for mode,v in stages.items():
 root=Path(v['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck('exact stage '+mode,actual==set(v['sha256']) and not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
 for n,h in v['sha256'].items():ck('stage:'+n,c.sha(root/n)==h)
ck('relocated common source path',(D/'../../../direct-bg-blocked-update/reproduce').resolve()==c.C.resolve())
ck('fixtures present and preparation-pinned',str(c.C/'fixtures.toml') in c.rd(D/'preparation-pins.json')['sha256'])
# A complete saved-output auditor fixture: only external host/source/receipt/pin
# authenticity are mocked. Output schemas, phase, commands, all time bounds,
# process linkage, resources, oracle and log checks remain real.
spec=importlib.util.spec_from_file_location('independent_boundary_fixture',D/'synthetic-data.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def toml(v):
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) is str:return json.dumps(v)
 if type(v) in (int,float):return repr(v)
 if type(v) is list:return '['+','.join(toml(x) for x in v)+']'
 if type(v) is dict:return '{'+','.join(json.dumps(k)+'='+toml(x) for k,x in v.items())+'}'
 raise TypeError(type(v))
def dump(p,v):p.write_text(json.dumps(v))
def case(label,change=None,passes=False):
 with tempfile.TemporaryDirectory(prefix='red1800-boundary-') as tmp:
  root=Path(tmp);run=root/'run';out=run/'output';payload=run/'payload';outer=root/'outer';package=root/'package'
  for p in (out,payload,outer,package):p.mkdir(parents=True)
  dump(package/'schedule.json',f.S)
  cfg=c.config('red1800');cfg.update(run=str(run),output=str(out),payload=str(payload));cfg['command']=list(cfg['command']);cfg['command'][-3]=str(payload)
  identity=lambda pid:dict(pid=pid,pgid=pid,sid=pid,boot_id='fixture-boot',start_ticks=11,command='fixture command')
  runner,child=identity(101),identity(102)
  host=dict(head='fixture-head',master='fixture-master',boot_id='fixture-boot',groups=[100,101,102],matches=[])
  seal=dict(phase='red1800',config=cfg,files=[str(outer/'outer-ready.json')],trees=[],inventory={},groups=[100],head=host['head'],master=host['master'],boot_id=host['boot_id'])
  sp=run/'sealed.json';rp=run/'admission.json';pp=run/'launch-pins.json'
  pins=dict(files=seal['files']+[str(p) for p in (sp,rp,run/'prehost.json',outer/'release.json',outer/'outer-invocation.json')],trees=[],inventory={})
  mem=dict(available_kib=6*1024**2,swap_used_kib=1024**2)
  proc=dict(runner=runner,child=child,pins_unchanged=True,command=cfg['command'],pins_sha256='synthetic-hash',terminal_memory=mem,child_maxrss_kib=100,elapsed_including_launch=1792.,cwd=str(c.R),returncode=1,reason='exit1')
  sup=dict(guard_identity=runner,elapsed_seconds=1800.,returncode=0,accepted=True,**dict.fromkeys(['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill'],False))
  invocation=dict(supervisor=sup,elapsed_seconds=1800.,command=cfg['command'],pins_sha256='synthetic-hash',guard_command=['synthetic-guard'],python=sys.executable,monotonic_start=1,reservation_sha256='synthetic-hash',review_sha256='synthetic-hash')
  reservation=dict(one_attempt=True,phase='red1800',command=cfg['command'],pins_sha256='synthetic-hash',review_sha256='synthetic-hash',max_seconds=1800)
  objects={sp:seal,rp:{},pp:pins,out/'pins.json':pins,run/'config.json':cfg,run/'invocation.json':invocation,out/'process.json':proc,out/'current.json':deepcopy(proc),run/'reservation.json':reservation,run/'host.json':host,run/'prehost.json':host,run/'posthost.json':host}
  payload_data=f.fixture('red300');log=f.logfile('red300',payload_data)
  if change:change(objects,run,out,payload_data)
  for p,v in objects.items():dump(p,v)
  (out/'resources.jsonl').write_text(json.dumps(dict(mem,elapsed=1792.))+'\n');(out/'run.log').write_text(log);(run/'launcher.log').write_text('')
  for n,v in payload_data.items():(payload/n).write_text('\n'.join(json.dumps(k)+'='+toml(x) for k,x in v.items())+'\n')
  with ExitStack() as stack:
   for k,v in dict(D=package,config=lambda _:cfg,validate_environment=lambda:None,preparation=lambda:None,validate_sources=lambda:None,predecessor=lambda _:None,verify_seal=lambda *args:None,verify_outer_invocation=lambda *args:None,verify_review=lambda *args:None,outer_dir=lambda _:outer,sha=lambda _:'synthetic-hash',host_safe=lambda h:h['matches']==[],guard_command=lambda *args:['synthetic-guard'],loaded_for=lambda _:f.LOADED).items():stack.enter_context(patch.object(a,k,v))
   stack.enter_context(patch.object(a.guard,'pins_match',lambda _:True))
   if passes:ck(label,a.checks_for('red1800')['all_passed'] is True)
   else:reject(label,lambda:a.checks_for('red1800'))
case('full auditor exact1792/1800 positive',passes=True)
for key,value in [('elapsed_including_launch',1792.000001),('returncode',False),('reason','wall_time'),('pins_unchanged',False),('cwd','other'),('remaining_session',[102])]:
 case('process '+key,lambda d,r,out,p,key=key,value=value:d[out/'process.json'].__setitem__(key,value))
for key,value in [('elapsed_seconds',1800.000001),('review_sha256','wrong'),('reservation_sha256','wrong'),('guard_command',['wrong'])]:
 case('invocation '+key,lambda d,r,out,p,key=key,value=value:d[r/'invocation.json'].__setitem__(key,value))
for key,value in [('elapsed_seconds',1800.000001),('soft_timeout',True),('hard_timeout',True),('child_kill',True),('guard_term',True),('guard_kill',True),('cleanup_error','error')]:
 case('supervisor '+key,lambda d,r,out,p,key=key,value=value:d[r/'invocation.json']['supervisor'].__setitem__(key,value))
for key,value in [('one_attempt',1),('phase','red300'),('max_seconds',300)]:
 case('reservation '+key,lambda d,r,out,p,key=key,value=value:d[r/'reservation.json'].__setitem__(key,value))
case('raw must retain red300 semantic phase',lambda d,r,out,p:p['raw.toml'].__setitem__('phase','red1800'))
case('final raw mandatory',lambda d,r,out,p:p.pop('raw.toml'))
case('last cost mandatory',lambda d,r,out,p:p.pop('cost-28.toml'))
case('all28 units mandatory',lambda d,r,out,p:p.pop('unit-28.toml'))
case('cost bound1800',lambda d,r,out,p:p['cost-28.toml'].__setitem__('seconds',1800.000001))
case('posthost descendant refusal',lambda d,r,out,p:d[r/'posthost.json'].__setitem__('matches',[102]))
result=dict(all_passed=True,count=len(checks),checks=checks,scope='Fresh baseline bytes, resolved runtime inventory, stage/source paths and complete synthetic auditor. External host/source/review/pin authenticity mocked only in synthetic auditor; actual offline receipt gates tested separately. No runtime execution.',runtime_executed=False,sha256={str(D/n):c.sha(D/n) for n in ['independent-boundary-check.py','audit.py','control.py','oracle.py','synthetic-data.py','baseline.json','runtime-inputs-complete.json','stages.json']})
with (D/'independent-boundary-check.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(dict(all_passed=True,count=len(checks),runtime_executed=False)))
