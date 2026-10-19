"""Synthetic checks_for wiring. Host/ref/hash/review boundaries and TOML codec mocked; all semantic saved-data gates real. No launcher/Julia."""
from pathlib import Path
import json,copy,tempfile,sys,struct
from unittest.mock import patch
from contextlib import ExitStack
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import audit as a
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def rejected(n,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError):ck(n,True)
 else:ck(n,False)
def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic']*(f+e),children=[])
bt=lambda x:struct.pack('>d',float(x)).hex()
with tempfile.TemporaryDirectory(prefix='bg-gc-full-audit-') as td:
 root=Path(td);run=root/'run';out=run/'output';outer=root/'outer';out.mkdir(parents=True);outer.mkdir()
 cfg=dict(phase='redgc300',mode='red',seconds=300,expected_exit=1,run=str(run),output=str(out),stage='synthetic',command=['synthetic'])
 ident=dict(pid=1,pgid=1,sid=1,start_ticks=1,boot_id='b',command=['synthetic'])
 host=dict(head='h',master='m',boot_id='b',groups=[1],matches=[],unreadable_identity_pids=[])
 fixtures=[];windows={}
 for cell,name in enumerate(('sparse32','dense32','sparse96'),1):
  m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[bt(1)])
  fixtures.append(dict(name=name,n=1,matrices=[copy.deepcopy(m) for _ in range(9)],steps=[dict(j=1,a=[bt(1)],dse=[bt(1)],unit=[bt(1)]) for _ in range(8)]))
  for pair in range(1,11):
   for order in (1,2):
    side=('reference','candidate')[(order-1) if pair%2 else 2-order]
    windows[f'window-{cell}-{2*(pair-1)+order}.toml']=dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=100,events=10 if side=='reference' else 11,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.1]*6,outputs=[[bt(1)] for _ in range(24)])
 preps={f'preparation-{i}.toml':dict(phase='redgc300',fixture=fixtures[i-1]['name'],cell=i,after_pair=3,before_pair=4,requested_full_gc=True,calls=1,cumulative_calls=i,returned=True,seconds=.1,bytes=128,events=2,gc_seconds=.2,compile_seconds=.1,recompile_seconds=0.,gc_pauses=2,full_collections=2) for i in range(1,4)}
 expected=a.rd(P/'expected-tests.json');r=node('root');r['children']=[node(*v) for v in expected['red']['groups']]
 raw=dict(phase='redgc300',complete=True,fatal='',loaded={},threads=1,blas_threads=1,tests=r,preparation_calls=3,preparations_completed=3)
 seal=dict(phase='redgc300',config=cfg,head='h',master='m',boot_id='b',groups=[1],files=[str(outer/'outer-ready.json')],trees=[],inventory={})
 pins=dict(files=seal['files']+[str(run/n) for n in ['sealed.json','admission.json','prehost.json']]+[str(outer/n) for n in ['release.json','outer-invocation.json']],trees=[],inventory={})
 resource=dict(available_kib=7*1024**2,swap_used_kib=0)
 process=dict(runner=ident,child=ident,pins_unchanged=True,command=cfg['command'],pins_sha256='hash',terminal_memory=resource,child_maxrss_kib=100,returncode=1,reason='exit1')
 inv=dict(supervisor=dict(guard_identity=ident,returncode=0,accepted=True,elapsed_seconds=2.),elapsed_seconds=2.,command=cfg['command'],pins_sha256='hash',guard_command=['guard'],monotonic_start=1.,python=sys.executable,reservation_sha256='hash',review_sha256='hash')
 docs={'sealed.json':seal,'config.json':cfg,'admission.json':{},'launch-pins.json':pins,'invocation.json':inv,'host.json':host,'prehost.json':host,'posthost.json':host,'reservation.json':dict(one_attempt=True,phase='redgc300',command=cfg['command'],pins_sha256='hash',review_sha256='hash',max_seconds=300)}
 output=dict(windows,**preps,**{'raw.toml':raw,'pins.json':pins,'current.json':dict(runner=ident,child=ident,command=cfg['command'],pins_sha256='hash'),'process.json':process})
 def restore():
  for p in out.iterdir():p.unlink()
  for n,v in docs.items():(run/n).write_text(json.dumps(v))
  for n,v in output.items():(out/n).write_text(json.dumps(v))
  (out/'resources.jsonl').write_text(json.dumps(resource)+'\n');(out/'run.log').write_text('BEGIN BG specialization driver redgc300\n'+'TEST FAILURE:\n'*3);(run/'launcher.log').write_text('')
 def mutate(n,fn):
  p=out/n;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v))
 realrd=a.rd
 def rd(p):
  if Path(p)==P/'inputs.json':return {'fixtures':fixtures}
  return realrd(p)
 with ExitStack() as stack:
  for name,fn in dict(config=lambda phase:cfg,validate_environment=lambda:None,preparation=lambda:[],validate_sources=lambda:None,predecessor=lambda phase:([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,sha=lambda p:'hash',outer_dir=lambda phase:outer,guard_command=lambda *x:['guard'],loaded_for=lambda cfg:{},rd=rd).items():stack.enter_context(patch.object(a,name,fn))
  stack.enter_context(patch.object(a.guard,'pins_match',lambda p:True));stack.enter_context(patch.object(a.tomllib,'loads',json.loads))
  restore();v=a.checks_for('redgc300');ck('complete_RED_all_three_records',v['all_passed'] and len(v['preparation']['records'])==3 and v['process_elapsed_seconds']==2.)
  mutations={
   'missing_GC':lambda:(out/'preparation-2.toml').unlink(),
   'wrong_phase':lambda:mutate('preparation-1.toml',lambda v:v.update(phase='red300')),
   'wrong_boundary':lambda:mutate('preparation-1.toml',lambda v:v.update(after_pair=2)),
   'incomplete_count':lambda:mutate('raw.toml',lambda v:v.update(preparations_completed=2)),
   'missing_raw_counter':lambda:mutate('raw.toml',lambda v:v.pop('preparation_calls')),
   'compile_in_window':lambda:mutate('window-1-7.toml',lambda v:v.update(compile_seconds=.1)),
   'missing_window':lambda:(out/'window-1-6.toml').unlink(),
   'extra_file':lambda:(out/'extra.toml').write_text('{}'),
   'false_return':lambda:mutate('preparation-3.toml',lambda v:v.update(returned=False)),
   'GC_wall_overflow':lambda:mutate('preparation-1.toml',lambda v:v.update(seconds=3.)),
   'strict_reservation_bool':lambda:(run/'reservation.json').write_text(json.dumps(dict(docs['reservation.json'],one_attempt=1))),
   'bad_GC_metric':lambda:mutate('preparation-1.toml',lambda v:v.update(bytes=-1)),
   'wrong_exit':lambda:mutate('process.json',lambda v:v.update(returncode=0)),
   'pressure':lambda:mutate('process.json',lambda v:v['terminal_memory'].update(available_kib=1)),
   'warning':lambda:(out/'run.log').write_text('Warning: world age'),
   'malformed_GC':lambda:(out/'preparation-1.toml').write_text('{')}
  for n,fn in mutations.items():restore();fn();rejected(n,lambda:a.checks_for('redgc300'))
  # Timeout exactly at first preparation boundary: no GC record is allowed yet.
  restore()
  for p in list(out.iterdir()):
   if p.name.startswith('preparation-') or p.name=='raw.toml' or (p.name.startswith('window-') and p.name not in list(windows)[:6]):p.unlink()
  mutate('process.json',lambda v:v.update(returncode=-15,reason='wall_time'))
  x=json.loads((run/'invocation.json').read_text());x['supervisor'].update(returncode=1,accepted=False,hard_timeout=False);(run/'invocation.json').write_text(json.dumps(x));(out/'run.log').write_text('BEGIN BG specialization driver redgc300')
  v=a.checks_for('redgc300');ck('pure_timeout_before_GC_record',v['pure_timeout'] and not v['all_passed'])
  (out/'preparation-1.toml').write_text('{');rejected('malformed_partial_GC_never_timeout',lambda:a.checks_for('redgc300'))
  # GREEN keeps exact tree/count and all allocation comparisons.
  cfg.update(phase='greengc300',mode='green',expected_exit=0);seal['phase']='greengc300';docs['reservation.json'].update(phase='greengc300')
  process.update(returncode=0,reason='exit0');raw.update(phase='greengc300');raw['tests']['children']=[node(*v) for v in expected['green']['groups']]
  for v in preps.values():v['phase']='greengc300'
  for v in windows.values():
   if v['side']=='candidate':v['events']=9
  restore();(out/'run.log').write_text('BEGIN BG specialization driver greengc300')
  import allocation_oracle
  with patch.object(allocation_oracle,'partial_windows',wraps=allocation_oracle.partial_windows) as partial, patch.object(allocation_oracle,'allocation_results',wraps=allocation_oracle.allocation_results) as full, patch.object(a.tomllib,'loads',wraps=json.loads) as codec:
   v=a.checks_for('greengc300')
   ck('one_full_residual_pass_zero_partial',full.call_count==1 and partial.call_count==0)
   ck('decode_each_TOML_once',codec.call_count==64)
  ck('complete_GREEN_8640',v['all_passed'] and v['result']['assertions']==8640 and v['preparation']['saved_preparations']==3)
with (P/'full-audit-tests-reviewed.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope=__doc__),f,indent=2);f.write('\n')
print('Full auditor synthetic wiring PASS',len(checks))
