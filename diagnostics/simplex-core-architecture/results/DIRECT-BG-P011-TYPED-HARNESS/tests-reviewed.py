"""Fresh offline synthetic tests. Never invoke seal/outer/guard/launch entrypoints."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import tempfile,json,sys,hashlib
import oracle as o, control as c, audit as a
D=Path(__file__).resolve().parent;checks=[]
def check(n,v):
 if not v:raise RuntimeError(n)
 checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):checks.append(n);return
 raise RuntimeError('Accepted invalid '+n)
def metric():return dict(seconds=.1,bytes=80,events=2,gc_seconds=.01,compile_seconds=.02,recompile_seconds=.0)
LOADED=dict(JSimplex='/stage/src/JSimplex.jl',Test='/Test.jl',LinearAlgebra='/LA.jl',TOML='/TOML.jl',PrecompileTools='/PT.jl')
def fixture(phase):
 counts=o.panel_counts(phase);red=phase=='p011-red300'
 def node(name,n=0,fail=0):return dict(name=name,**{'pass':n-fail,'fail':fail,'error':0,'broken':0,'children':[]})
 root=node('panel');ranges=[(1,15),(16,33),(34,65),(66,94)]
 for i,(name,(lo,hi)) in enumerate(zip(o.NAMES,ranges)):
  n=sum(counts[f'P{k:03d}'] for k in range(lo,hi+1))+(8 if i==0 and not red else 0)
  root['children'].append(node(name,n,int(red and i==0)))
 failures=[dict(site='P011',kind='fail',detail=o.RED_FAILURE_DETAIL)] if red else []
 unit=dict(index=1,name='panel',complete=True,fatal='',tests=root,records=dict(sites=counts,events={},apis={},failures=failures,failure_count=len(failures),active=''))
 dec=dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20)
 probe=dict(bytes=0,events=0,consumed_bytes=0,consumed_events=0,warm=dec,bytes_decision=deepcopy(dec),events_decision=deepcopy(dec),values_unchanged=True,owners_unchanged=True)
 totals=[sum(x[k] for x in root['children']) for k in ('pass','fail','error','broken')]
 raw=dict(schema=1,phase=phase,complete=True,fatal='',qualification='p011_typed_structural',test_source='/tests/'+phase,loaded=LOADED.copy(),threads=1,blas_threads=1,probe=deepcopy(probe),unit=deepcopy(unit),totals=totals)
 return {**{n:metric() for n in o.PREPARATION},'probe.toml':probe,'unit-1.toml':unit,'raw.toml':raw}
def validate(p,phase):return o.validate(p,LOADED,phase,'/tests/'+phase)
for phase in ('p011-red300','p011-green300'):
 p=fixture(phase);v=validate(p,phase);check(phase+'_positive',v['totals']==([11759,1,0,0] if phase=='p011-red300' else [11768,0,0,0]))
 for n in o.PAYLOAD:
  q=deepcopy(p);del q[n];refuse(phase+'_missing_'+n,lambda q=q:validate(q,phase))
 q=deepcopy(p);q['extra.toml']={};refuse(phase+'_extra',lambda:validate(q,phase))
 for n in o.PREPARATION:
  for k in o.METRICS:
   for bad in (True,-1,float('nan'),float('inf'),'1'):
    q=deepcopy(p);q[n][k]=bad;refuse(phase+'_prep_'+n+k+repr(bad),lambda q=q:validate(q,phase))
  for k in ('bytes','events'):
   q=deepcopy(p);q[n][k]=.5;refuse(phase+'_prep_fraction'+n+k,lambda q=q:validate(q,phase))
 for k in ('bytes','events','consumed_bytes','consumed_events','values_unchanged','owners_unchanged'):
  for bad in (False,1,'0') if k.endswith('unchanged') else (True,1,-1,.0):
   q=deepcopy(p);q['probe.toml'][k]=bad;q['raw.toml']['probe']=deepcopy(q['probe.toml']);refuse(phase+'_probe_'+k+repr(bad),lambda q=q:validate(q,phase))
 for arm in ('warm','bytes_decision','events_decision'):
  for k,bad in [('start',0),('start',True),('count',1),('accepted',0),('reason','uninitialized'),('finite',1),('counters',[0]*19),('counters',[False]*20)]:
   q=deepcopy(p);q['probe.toml'][arm][k]=bad;q['raw.toml']['probe']=deepcopy(q['probe.toml']);refuse(phase+'_decision_'+arm+k,lambda q=q:validate(q,phase))
 for site in o.panel_counts(phase):
  q=deepcopy(p);q['unit-1.toml']['records']['sites'][site]+=1;q['raw.toml']['unit']=deepcopy(q['unit-1.toml']);refuse(phase+'_site_'+site,lambda q=q:validate(q,phase))
 for i in range(4):
  for k in ('pass','fail','error','broken'):
   q=deepcopy(p);q['unit-1.toml']['tests']['children'][i][k]+=1;q['raw.toml']['unit']=deepcopy(q['unit-1.toml']);refuse(phase+'_tree_'+str(i)+k,lambda q=q:validate(q,phase))
 for key,bad in [('complete',1),('schema',True),('fatal','error'),('phase','wrong'),('test_source','other'),('loaded',{}),('threads',True),('blas_threads',2),('totals',[0,0,0,0])]:
  q=deepcopy(p);q['raw.toml'][key]=bad;refuse(phase+'_raw_'+key,lambda q=q:validate(q,phase))
 q=deepcopy(p);q['raw.toml']['probe']['bytes']=4;refuse(phase+'_raw_probe_mismatch',lambda:validate(q,phase))
 expected_log='' if phase.endswith('green300') else 'TEST FAILURE: P011 '+p['unit-1.toml']['records']['failures'][0]['detail']+'\n'
 check(phase+'_expected_log',not o.warning_log(expected_log,p,phase))
 for s in ['WARNING: world age','Test Failed at other.jl','TEST FAILURE: P095 fail','LoadError','ERROR: other','method overwriting']:
  check(phase+'_badlog_'+s,o.warning_log(expected_log+s,p,phase))
 if phase.endswith('red300'):
  check('red_missing_failure_log',o.warning_log('',p,phase));check('red_duplicate_log',o.warning_log(expected_log*2,p,phase))
  for k,bad in [('site','P095'),('kind','error'),('detail','')]:
   q=deepcopy(p);q['unit-1.toml']['records']['failures'][0][k]=bad;q['raw.toml']['unit']=deepcopy(q['unit-1.toml']);refuse('wrong_red_'+k,lambda q=q:validate(q,phase))
 cfg=c.config(phase);check(phase+'_command',cfg['command'][-4:]==[str(D/'driver.jl'),cfg['payload'],cfg['stage'],phase]);check(phase+'_bound',cfg['seconds']==300 and cfg['expected_exit']==int(phase.endswith('red300')))
for phase in ('zero-counts-300','red300','green300','p011-red600','',None):refuse('unprepared_'+str(phase),lambda phase=phase:c.config(phase))
with tempfile.TemporaryDirectory() as t:
 p=Path(t)/'pins';p.write_text('fixed');v=dict(accepted=True,findings=[],scope='P011 typed exact-run admission',phase='p011-red300',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 c.verify_review(v,p,[str(p)],v['scope'],v['phase']);check('receipt_positive',True)
 for k,bad in [('accepted',1),('findings',['x']),('scope','old'),('phase','p011-green300'),('pins_sha256','bad'),('sha256',{})]:
  q=deepcopy(v);q[k]=bad;refuse('receipt_'+k,lambda q=q:c.verify_review(q,p,[str(p)],v['scope'],v['phase']))
# Exercise the real auditor on temporary JSON/TOML. External source/host/admission
# boundaries are mocked, not counted as launch-safety proof.
def tv(v):
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) is str:return json.dumps(v)
 if type(v) in (int,float):return repr(v)
 if type(v) is list:return '['+','.join(tv(x) for x in v)+']'
 if type(v) is dict:return '{'+','.join(json.dumps(k)+'='+tv(x) for k,x in v.items())+'}'
 raise TypeError(type(v))
def td(v):return '\n'.join(json.dumps(k)+'='+tv(x) for k,x in v.items())+'\n'
def edit(p,k,v):
 d=json.loads(p.read_text());d[k]=v;p.write_text(json.dumps(d))
def full_case(phase,label,mutate=None,success=False):
 with tempfile.TemporaryDirectory() as t:
  t=Path(t);run=t/'run';out=run/'output';payload=run/'payload';outer=t/'outer'
  for p in (out,payload,outer):p.mkdir(parents=True)
  cfg=dict(phase=phase,mode='red',seconds=300,expected_exit=int(phase.endswith('red300')),stage='/stage',run=str(run),output=str(out),payload=str(payload),command=['test'])
  ident=lambda n:dict(pid=n,pgid=n,sid=n,boot_id='boot',start_ticks=1,command='cmd')
  runner,child=ident(10),ident(11);host=dict(head='head',master='master',boot_id='boot',groups=[1,10,11],matches=[])
  sp=run/'sealed.json';rp=run/'admission.json';pp=run/'launch-pins.json'
  seal=dict(phase=phase,config=cfg,files=[str(outer/'outer-ready.json')],trees=[],inventory={},groups=[1],head='head',master='master',boot_id='boot')
  pins=dict(files=seal['files']+[str(x) for x in (sp,rp,run/'prehost.json',outer/'release.json',outer/'outer-invocation.json')],trees=[],inventory={})
  sup=dict(guard_identity=runner,elapsed_seconds=1.,returncode=0,accepted=True,**{k:False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')})
  mem=dict(available_kib=8*1024**2,swap_used_kib=0)
  proc=dict(runner=runner,child=child,pins_unchanged=True,command=cfg['command'],pins_sha256='sha',terminal_memory=mem,child_maxrss_kib=1000,elapsed_including_launch=1.,cwd=str(c.R),returncode=cfg['expected_exit'],reason='exit'+str(cfg['expected_exit']))
  inv=dict(supervisor=sup,elapsed_seconds=1.,command=cfg['command'],pins_sha256='sha',guard_command=['guard'],python=sys.executable,monotonic_start=1,reservation_sha256='sha',review_sha256='sha')
  res=dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256='sha',review_sha256='sha',max_seconds=300)
  data={sp:seal,rp:{},pp:pins,out/'pins.json':pins,run/'invocation.json':inv,out/'process.json':proc,out/'current.json':deepcopy(proc),run/'prehost.json':host,run/'host.json':host,run/'posthost.json':host,run/'config.json':cfg,run/'reservation.json':res}
  for p,v in data.items():p.write_text(json.dumps(v))
  (out/'resources.jsonl').write_text(json.dumps(dict(mem,elapsed=.5))+'\n');fixture_data=fixture(phase)
  log='' if cfg['expected_exit']==0 else 'TEST FAILURE: P011 '+fixture_data['unit-1.toml']['records']['failures'][0]['detail']+'\n'
  (out/'run.log').write_text(log);(run/'launcher.log').write_text('')
  for n,v in fixture_data.items():(payload/n).write_text(td(v))
  if mutate:mutate(run,out,payload)
  with ExitStack() as stack:
   mocks=dict(config=lambda _:cfg,validate_environment=lambda:None,preparation=lambda:None,validate_sources=lambda:None,predecessor=lambda _: ([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,outer_dir=lambda _:outer,sha=lambda _: 'sha',host_safe=lambda h:h['matches']==[],guard_command=lambda *x:['guard'],loaded_for=lambda _:LOADED,test_source_for=lambda _: '/tests/'+phase)
   for k,v in mocks.items():stack.enter_context(patch.object(a,k,v))
   stack.enter_context(patch.object(a.guard,'pins_match',lambda _:True))
   if success:check(phase+label,a.checks_for(phase)['all_passed'] is True)
   else:refuse(phase+label,lambda:a.checks_for(phase))
for phase in ('p011-red300','p011-green300'):
 full_case(phase,'full_positive',success=True)
 for k,v in [('returncode',2),('returncode',False),('reason','wall_time'),('pins_unchanged',False),('cwd','wrong'),('elapsed_including_launch',293),('error','bad'),('child_maxrss_kib',float('nan')),('terminal_memory',dict(available_kib=1,swap_used_kib=0))]:
  full_case(phase,'process_'+k,lambda run,out,payload,k=k,v=v:edit(out/'process.json',k,v))
 for k,v in [('elapsed_seconds',301),('review_sha256','bad'),('reservation_sha256','bad'),('guard_command',['wrong'])]:
  full_case(phase,'invocation_'+k,lambda run,out,payload,k=k,v=v:edit(run/'invocation.json',k,v))
 for flag in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill'):
  def mutation(run,out,payload,flag=flag):
   p=run/'invocation.json';v=json.loads(p.read_text());v['supervisor'][flag]=True;p.write_text(json.dumps(v))
  full_case(phase,flag,mutation)
 for name in o.PAYLOAD:full_case(phase,'missing_'+name,lambda run,out,payload,name=name:(payload/name).unlink())
 full_case(phase,'malformed',lambda run,out,payload:(payload/'raw.toml').write_text('not toml'))
 full_case(phase,'extra_payload',lambda run,out,payload:(payload/'extra').write_text(''))
 full_case(phase,'extra_guard',lambda run,out,payload:(out/'extra').write_text(''))
 full_case(phase,'empty_resources',lambda run,out,payload:(out/'resources.jsonl').write_text(''))
 full_case(phase,'reservation_bool',lambda run,out,payload:edit(run/'reservation.json','one_attempt',1))
 full_case(phase,'posthost',lambda run,out,payload:edit(run/'posthost.json','matches',[11]))
 def symlink(run,out,payload):
  p=payload/'load.toml';dest=run/'moved';p.rename(dest);p.symlink_to(dest)
 full_case(phase,'symlink',symlink)
 for value in (True,-1,float('nan'),float('inf'),1.1):
  full_case(phase,'resource_elapsed'+repr(value),lambda run,out,payload,value=value:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=value))))
# Fresh regression cases for the rejected overly broad failure-detail exception.
phase='p011-red300';p=fixture(phase)
for index,bad in enumerate([
 'arbitrary failure',o.RED_FAILURE_DETAIL.replace('_bgb_eligibility','unrelated_assertion'),
 o.RED_FAILURE_DETAIL.replace(':103',':104'),o.RED_FAILURE_DETAIL+'WARNING: method overwriting',
 o.RED_FAILURE_DETAIL+'\nTest Failed at another.jl',o.RED_FAILURE_DETAIL+'\nERROR: hidden',
 o.RED_FAILURE_DETAIL.replace(' == 0',' == 1'),o.RED_FAILURE_DETAIL.replace('P011','P095')+'extra',
 o.RED_FAILURE_DETAIL+'\n   Evaluated: 208 == 0',o.RED_FAILURE_DETAIL+'\n',
]):
 q=deepcopy(p);q['unit-1.toml']['records']['failures'][0]['detail']=bad;q['raw.toml']['unit']=deepcopy(q['unit-1.toml'])
 refuse('strict_failure_detail_'+str(index),lambda q=q:validate(q,phase))
 check('log_standalone_rejects_detail_'+str(index),o.warning_log('TEST FAILURE: P011 '+bad+'\n',q,phase))
 def mutate(run,out,payload,q=q,bad=bad):
  for name in ('unit-1.toml','raw.toml'):(payload/name).write_text(td(q[name]))
  (out/'run.log').write_text('TEST FAILURE: P011 '+bad+'\n')
 full_case(phase,'strict_failure_full_'+str(index),mutate)
# GREEN must stop at missing RED acceptance, even before a result-review lookup.
with patch.object(c,'rd',lambda _: {'all_passed':False}):refuse('green_missing_red',lambda:c.predecessor('p011-green300'))
check('red_no_predecessor',c.predecessor('p011-red300')==([],[]))
result=dict(all_passed=True,count=len(checks),checks=checks,scope='Fresh synthetic Python only; full-auditor external boundaries mocked; no Julia or process launch',sha256={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('tests-reviewed.py','oracle.py','audit.py','control.py','driver.jl')})
with (D/'tests-reviewed.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'red_totals':fixture('p011-red300')['raw.toml']['totals'],'green_totals':fixture('p011-green300')['raw.toml']['totals']}))
