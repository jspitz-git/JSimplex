"""Synthetic full auditor wiring; only host/ref/hash/review and TOML codec boundaries mocked. No launcher or Julia."""
from pathlib import Path
import json,copy,tempfile,sys
from unittest.mock import patch
from contextlib import ExitStack
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import audit as a
from synthetic import mock,S
checks={}
def ck(n,v):
 if not v:raise RuntimeError(n)
 checks[n]=True
def rejected(n,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError):ck(n,True)
 else:ck(n,False)
with tempfile.TemporaryDirectory(prefix='bg-blocked-full-audit-') as td:
 root=Path(td);run=root/'run';out=run/'output';outer=root/'outer';out.mkdir(parents=True);outer.mkdir()
 cfg=dict(phase='red300',mode='red',seconds=300,expected_exit=1,run=str(run),output=str(out),stage='synthetic',command=['synthetic'])
 ident=dict(pid=1,pgid=1,sid=1,start_ticks=1,boot_id='b',command=['synthetic'])
 host=dict(head='h',master='m',boot_id='b',groups=[1],matches=[],unreadable_identity_pids=[])
 raw,units=mock('red')
 seal=dict(phase='red300',config=cfg,head='h',master='m',boot_id='b',groups=[1],files=[str(outer/'outer-ready.json')],trees=[],inventory={})
 pins=dict(files=seal['files']+[str(run/n) for n in ['sealed.json','admission.json','prehost.json']]+[str(outer/n) for n in ['release.json','outer-invocation.json']],trees=[],inventory={})
 resource=dict(available_kib=7*1024**2,swap_used_kib=0)
 process=dict(runner=ident,child=ident,pins_unchanged=True,command=cfg['command'],pins_sha256='hash',terminal_memory=resource,child_maxrss_kib=100,returncode=1,reason='exit1')
 inv=dict(supervisor=dict(guard_identity=ident,returncode=0,accepted=True,elapsed_seconds=2.),elapsed_seconds=2.,command=cfg['command'],pins_sha256='hash',guard_command=['guard'],monotonic_start=1.,python=sys.executable,reservation_sha256='hash',review_sha256='hash')
 docs={'sealed.json':seal,'config.json':cfg,'admission.json':{},'launch-pins.json':pins,'invocation.json':inv,'host.json':host,'prehost.json':host,'posthost.json':host,'reservation.json':dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256='hash',review_sha256='hash',max_seconds=300)}
 def logfile():return 'BEGIN BG blocked U driver '+cfg['phase']+'\n'+''.join(f'UNIT BEGIN {i} {n}\nUNIT END {i} {n}\n' for i,n in enumerate(S['units'],1))+('TEST FAILURE:\n'*6 if cfg['mode']=='red' else '')
 def restore():
  for p in out.iterdir():p.unlink()
  for n,v in docs.items():(run/n).write_text(json.dumps(v))
  output=dict(units,**{'raw.toml':raw,'pins.json':pins,'current.json':dict(runner=ident,child=ident,command=cfg['command'],pins_sha256='hash'),'process.json':process})
  for n,v in output.items():(out/n).write_text(json.dumps(v))
  (out/'resources.jsonl').write_text(json.dumps(resource)+'\n');(out/'run.log').write_text(logfile());(run/'launcher.log').write_text('')
 def mutate(n,fn,parent=out):
  p=parent/n;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 with ExitStack() as stack:
  for name,fn in dict(config=lambda phase:cfg,validate_environment=lambda:None,preparation=lambda:[],validate_sources=lambda:None,predecessor=lambda phase:([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,sha=lambda p:'hash',outer_dir=lambda phase:outer,guard_command=lambda *x:['guard'],loaded_for=lambda cfg:{}).items():stack.enter_context(patch.object(a,name,fn))
  stack.enter_context(patch.object(a.guard,'pins_match',lambda p:True));stack.enter_context(patch.object(a.tomllib,'loads',json.loads))
  restore();ck('complete_RED',a.checks_for('red300')['all_passed'])
  mutations={
   'missing_unit':lambda:(out/'unit-2.toml').unlink(),
   'malformed_unit':lambda:(out/'unit-1.toml').write_text('{'),
   'missing_raw':lambda:(out/'raw.toml').unlink(),
   'extra_file':lambda:(out/'extra.toml').write_text('{}'),
   'false_complete':lambda:mutate('raw.toml',lambda v:v.update(complete=False)),
   'wrong_named_failure':lambda:mutate('unit-9.toml',lambda v:v['records']['failures'][0].update(site='N005')),
   'strict_reservation_bool':lambda:mutate('reservation.json',lambda v:v.update(one_attempt=1),run),
   'wrong_exit':lambda:mutate('process.json',lambda v:v.update(returncode=0)),
   'wrong_command':lambda:mutate('process.json',lambda v:v.update(command=['wrong'])),
   'changed_pins':lambda:mutate('process.json',lambda v:v.update(pins_unchanged=False)),
   'pressure':lambda:mutate('process.json',lambda v:v['terminal_memory'].update(available_kib=1)),
   'swap':lambda:(out/'resources.jsonl').write_text(json.dumps(dict(resource,swap_used_kib=2*1024**2))),
   'no_samples':lambda:(out/'resources.jsonl').write_text(''),
   'warning':lambda:(out/'run.log').write_text(logfile()+'Warning: world age'),
   'missing_end_log':lambda:(out/'run.log').write_text(logfile().replace('UNIT END 28','MISSING 28')),
   'bad_identity':lambda:mutate('current.json',lambda v:v['child'].update(start_ticks=2)),
   'missing_group':lambda:mutate('posthost.json',lambda v:v.update(groups=[]),run),
   'host_julia':lambda:mutate('posthost.json',lambda v:v.update(matches=[{'pid':4}]),run),
   'wall_overflow':lambda:mutate('invocation.json',lambda v:v.update(elapsed_seconds=301.),run),
   'cleanup_error':lambda:mutate('invocation.json',lambda v:v['supervisor'].update(cleanup_error='not reaped'),run),
   'missing_callback':lambda:mutate('unit-3.toml',lambda v:v['records']['events'].update(event_finish=15)),
   'unexpected_failure_log':lambda:(out/'run.log').write_text(logfile()+'TEST FAILURE:\n'),
   'unit_symlink':lambda:((out/'unit-1.toml').unlink(),(out/'unit-1.toml').symlink_to(out/'unit-2.toml'))}
  for name,fn in mutations.items():restore();fn();rejected(name,lambda:a.checks_for('red300'))
  restore()
  for p in list(out.iterdir()):
   if p.name=='raw.toml' or p.name.startswith('unit-'):p.unlink()
  mutate('process.json',lambda v:v.update(returncode=-15,reason='wall_time'))
  mutate('invocation.json',lambda v:v['supervisor'].update(returncode=1,accepted=False,hard_timeout=False),run)
  (out/'run.log').write_text('BEGIN BG blocked U driver red300\n')
  v=a.checks_for('red300');ck('pure_timeout_is_failed',v['pure_timeout'] and not v['all_passed'])
  (out/'unit-1.toml').write_text('{');rejected('malformed_prefix_not_timeout',lambda:a.checks_for('red300'))
  cfg.update(phase='green300',mode='green',expected_exit=0);seal['phase']='green300';docs['reservation.json'].update(phase='green300');process.update(returncode=0,reason='exit0');raw,units=mock('green')
  restore();ck('complete_GREEN',a.checks_for('green300')['all_passed'])
  # Full audit's outer wrapper remains fail-closed and retains diagnostic hashes.
  restore();mutate('raw.toml',lambda v:v.update(complete=False));record=a.audit('green300');ck('failed_audit_saved',record['all_passed'] is False and (run/'audit.json').exists() and record['sha256'])
with (D/'full-audit-tests.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope=__doc__),f,indent=2)
print('Full auditor synthetic PASS',len(checks))
