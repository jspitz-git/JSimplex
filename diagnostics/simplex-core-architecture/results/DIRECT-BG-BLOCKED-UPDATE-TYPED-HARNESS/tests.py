"""New offline synthetic oracle and complete auditor tests. No execution entrypoints."""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import tempfile,json,sys,hashlib,importlib.util
import oracle as o,control as c,audit as a
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('synthetic_data',D/'synthetic-data.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fixture,logfile,LOADED,S=m.fixture,m.logfile,m.LOADED,m.S
checks=[]
def check(n,v):
 if not v:raise RuntimeError(n)
 checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError,FileNotFoundError):checks.append(n);return
 raise RuntimeError('Accepted invalid '+n)
def validate(p,phase):return o.validate(p,S,LOADED,phase)
for phase in ('red300','green300'):
 p=fixture(phase);v=validate(p,phase);check(phase+'_positive',v['expected_failures']==(6 if phase=='red300' else 0))
 for n in o.PAYLOAD:
  q=deepcopy(p);q.pop(n);refuse(phase+'_missing_'+n,lambda q=q:validate(q,phase))
 q=deepcopy(p);q['extra.toml']={};refuse(phase+'_extra',lambda:validate(q,phase))
 for n in o.PREPARATION:
  for k in o.METRICS:
   for bad in (True,-1,float('nan'),float('inf'),'1'):
    q=deepcopy(p);q[n][k]=bad;refuse(phase+n+k+repr(bad),lambda q=q:validate(q,phase))
  for k in ('bytes','events'):
   q=deepcopy(p);q[n][k]=.5;refuse(phase+n+k+'fraction',lambda q=q:validate(q,phase))
 for site in o.panel_counts():
  q=deepcopy(p);q['unit-1.toml']['records']['sites'][site]+=1;refuse(phase+'_site_'+site,lambda q=q:validate(q,phase))
 for i in range(4):
  q=deepcopy(p);q['unit-1.toml']['tests']['children'][i]['pass']+=1;refuse(phase+'_group_'+str(i),lambda q=q:validate(q,phase))
 for index in range(2,29):
  for kind in ['sites','apis','events']:
   for key in p[f'unit-{index}.toml']['records'][kind]:
    q=deepcopy(p);q[f'unit-{index}.toml']['records'][kind][key]+=1
    refuse(phase+str(index)+kind+key,lambda q=q:validate(q,phase))
 for index in range(3,29):
  for key,bad in [('panels',-1),('rejections',2),('growth',float('inf')),('minpivot',0.)]:
   q=deepcopy(p);q[f'unit-{index}.toml']['observations'][0][key]=bad;refuse(phase+str(index)+key,lambda q=q:validate(q,phase))
 for key,bad in [('complete',1),('fatal','error'),('phase','wrong'),('loaded',{'bad':'path'}),('threads',True),('blas_threads',2),('totals',[0,0,0,0])]:
  q=deepcopy(p);q['raw.toml'][key]=bad;refuse(phase+'_raw_'+key,lambda q=q:validate(q,phase))
 log=logfile(phase,p);check(phase+'_clean_log',not o.warning_log(log,p,phase))
 for bad in ['WARNING: world age','Test Failed at other.jl','TEST FAILURE: P011 other','LoadError','ERROR: other','method overwriting','FATAL DRIVER']:
  check(phase+'_badlog_'+bad,o.warning_log(log+bad,p,phase))
 check(phase+'_missing_end',o.warning_log(log.replace('UNIT END 28','ABSENT 28'),p,phase))
 if phase=='red300':
  q=deepcopy(p);q['unit-9.toml']['records']['failures'][0]['site']='P011';refuse('wrong_red_site',lambda:validate(q,phase))
  check('red_missing_failure_log',o.warning_log(log.replace('TEST FAILURE: N026','REMOVED'),p,phase))
 cfg=c.config(phase);check(phase+'_command',cfg['command'][-4:]==[str(D/'driver.jl'),cfg['payload'],cfg['stage'],phase]);check(phase+'_bound',cfg['seconds']==300 and cfg['expected_exit']==int(phase=='red300'))
for bad in ('p011-red300','p011-green300','red600','',None):refuse('unprepared_'+str(bad),lambda bad=bad:c.config(bad))
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
  t=Path(t);run=t/'run';out=run/'output';payload=run/'payload';outer=t/'outer';package=t/'package';package.mkdir();(package/'schedule.json').write_text(json.dumps(S))
  for p in (out,payload,outer):p.mkdir(parents=True)
  cfg=dict(phase=phase,mode='red',seconds=300,expected_exit=int(phase=='red300'),stage='/stage',run=str(run),output=str(out),payload=str(payload),command=['test'])
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
  log=logfile(phase,fixture_data)
  (out/'run.log').write_text(log);(run/'launcher.log').write_text('')
  for n,v in fixture_data.items():(payload/n).write_text(td(v))
  if mutate:mutate(run,out,payload)
  with ExitStack() as stack:
   mocks=dict(D=package,config=lambda _:cfg,validate_environment=lambda:None,preparation=lambda:None,validate_sources=lambda:None,predecessor=lambda _: ([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,outer_dir=lambda _:outer,sha=lambda _: 'sha',host_safe=lambda h:h['matches']==[],guard_command=lambda *x:['guard'],loaded_for=lambda _:LOADED)
   for k,v in mocks.items():stack.enter_context(patch.object(a,k,v))
   stack.enter_context(patch.object(a.guard,'pins_match',lambda _:True))
   if success:check(phase+label,a.checks_for(phase)['all_passed'] is True)
   else:refuse(phase+label,lambda:a.checks_for(phase))
for phase in ('red300','green300'):
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

with patch.object(c,'rd',lambda _: {'all_passed':False}):refuse('green_missing_accepted_red',lambda:c.predecessor('green300'))
check('red_no_predecessor',c.predecessor('red300')==([],[]))
with tempfile.TemporaryDirectory() as t:
 p=Path(t)/'pin';p.write_text('fixed');v=dict(accepted=True,findings=[],scope='BG blocked typed exact-run admission',phase='red300',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 c.verify_review(v,p,[str(p)],v['scope'],v['phase']);check('receipt_positive',True)
 for k,bad in [('accepted',1),('findings',['x']),('scope','old'),('phase','green300'),('pins_sha256','bad'),('sha256',{})]:
  q=deepcopy(v);q[k]=bad;refuse('receipt_'+k,lambda q=q:c.verify_review(q,p,[str(p)],v['scope'],v['phase']))
result=dict(all_passed=True,count=len(checks),checks=checks,scope='New Python synthetic payload/process refusal tests; external host/source/review boundaries mocked only in complete auditor fixture. No Julia or launch.',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('tests.py','synthetic-data.py','oracle.py','audit.py','control.py','driver.jl')})
with (D/'tests.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'payload_files':len(o.PAYLOAD),'prospective_RED_failures':6}))
