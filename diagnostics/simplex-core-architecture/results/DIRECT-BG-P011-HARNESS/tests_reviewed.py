"""Offline synthetic rejection tests. No launcher/guard/outer entry point is called."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from contextlib import ExitStack
import tempfile,json,math,sys,hashlib
import oracle as o
import audit as a
import control as c
D=Path(__file__).resolve().parent
checks=[]
def check(name,condition):
 if not condition:raise RuntimeError(name)
 checks.append(name)
def refuse(name,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,FileNotFoundError):checks.append(name);return
 raise RuntimeError('Accepted invalid '+name)
def metric():return dict(seconds=0.1,bytes=80,events=2,gc_seconds=0.0,compile_seconds=0.0,recompile_seconds=0.0)
LOADED=dict(JSimplex='/stage/src/JSimplex.jl',Test='/test/Test.jl',LinearAlgebra='/la.jl',TOML='/toml.jl')
def fixture():
 rows=[]
 for i,(phase,pair,arm) in enumerate(o.SCHEDULE,1):
  rows.append(dict(index=i,phase=phase,pair=pair,arm=arm,inner_bytes=16 if arm=='original' else 0,inner_events=1 if arm=='original' else 0,assignment_ok=True,decision_ok=True,bytes_wrapper=metric(),events_wrapper=metric(),consumed_result=metric()))
 p={name:metric() for name in o.PREPARATION}
 p.update({f'record-{i}.toml':deepcopy(v) for i,v in enumerate(rows,1)})
 p['raw.toml']=dict(schema=1,complete=True,fatal='',qualification='diagnostic_only',records=rows,loaded=LOADED.copy(),input_unchanged=True,replacement_unchanged=True)
 return p
p=fixture();v=o.validate(p,LOADED);check('valid_nonzero_allocations',v['p011_accepted'] is False)
q=deepcopy(p);q['load.toml']['compile_seconds']=0.25;check('preparation_compile_retained',o.validate(q,LOADED)['preparation']['load.toml']['compile_seconds']==.25)
for file in o.PAYLOAD:
 q=deepcopy(p);del q[file];refuse('missing_'+file,lambda q=q:o.validate(q,LOADED))
q=deepcopy(p);q['extra.toml']={};refuse('extra_file',lambda:o.validate(q,LOADED))
for file in o.PREPARATION:
 for field in o.METRICS:
  for bad in (True,-1,float('nan'),float('inf'),'1'):
   q=deepcopy(p);q[file][field]=bad;refuse('prep_'+file+'_'+field+'_'+repr(bad),lambda q=q:o.validate(q,LOADED))
 for field in ('bytes','events'):
  q=deepcopy(p);q[file][field]=1.5;refuse('fractional_'+file+field,lambda q=q:o.validate(q,LOADED))
 q=deepcopy(p);q[file]['extra']=0;refuse('extra_metric_'+file,lambda q=q:o.validate(q,LOADED))
for i in range(1,13):
 for key,bad in [('index',True),('index',i+1),('pair',True),('phase','sample-wrong'),('arm','bad'),('assignment_ok',1),('decision_ok',False),('inner_bytes',False),('inner_bytes',-1),('inner_events',1.5)]:
  q=deepcopy(p);q[f'record-{i}.toml'][key]=bad;refuse(f'row{i}_{key}_{bad}',lambda q=q:o.validate(q,LOADED))
 for field in ('bytes_wrapper','events_wrapper','consumed_result'):
  q=deepcopy(p);q[f'record-{i}.toml'][field]['compile_seconds']=float('nan');refuse(f'row{i}_{field}_nan',lambda q=q:o.validate(q,LOADED))
 q=deepcopy(p);q['raw.toml']['records'][i-1]['inner_bytes']+=1;refuse(f'raw_mismatch{i}',lambda q=q:o.validate(q,LOADED))
for key,bad in [('complete',1),('schema',True),('schema',2),('fatal','failure'),('qualification','red'),('input_unchanged',False),('replacement_unchanged',1),('loaded',{}),('records',[])]:
 q=deepcopy(p);q['raw.toml'][key]=bad;refuse('raw_'+key,lambda q=q:o.validate(q,LOADED))
q=deepcopy(p);q['record-5.toml']['bytes_wrapper']['compile_seconds']=.01;q['raw.toml']['records'][4]=deepcopy(q['record-5.toml']);v=o.validate(q,LOADED);check('nonzero_compile_excluded_not_rejected',5 not in v['descriptive_sample_counters']['original']['clean_wrapper_indices'])
for text in ['WARNING: world age','method overwriting','LoadError','ERROR: test','Test Failed','OutOfMemoryError']:check('log_'+text,o.warning_log(text))
check('empty_log',not o.warning_log(''))
# Actual config and receipt pure checks; fake filesystem pins only in temporary directory.
cfg=c.config('p011-300');check('two_driver_arguments',cfg['command'][-3:]==[str(c.PROBE/'driver.jl'),cfg['payload'],cfg['stage']]);check('separate_outputs',cfg['payload']!=cfg['output']);check('300_exit0',cfg['seconds']==300 and cfg['expected_exit']==0)
for phase in ('red300','green300','p011-600','',None):refuse('phase_'+str(phase),lambda phase=phase:c.config(phase))
with tempfile.TemporaryDirectory() as t:
 t=Path(t);pin=t/'pin';pin.write_text('pin');required=[str(pin)];v=dict(accepted=True,findings=[],scope='P011 diagnostic exact-run admission',phase='p011-300',pins_sha256=c.sha(pin),sha256={str(pin):c.sha(pin)})
 c.verify_review(v,pin,required,v['scope'],'p011-300');check('receipt_positive',True)
 for key,bad in [('accepted',1),('findings',['x']),('scope','BG blocked U RED2 exact-stage admission'),('phase','red300'),('pins_sha256','bad'),('sha256',{})]:
  q=deepcopy(v);q[key]=bad;refuse('receipt_'+key,lambda q=q:c.verify_review(q,pin,required,v['scope'],'p011-300'))
# Full checks_for path: real JSON/TOML/files and schema validation. Mock only external
# host/source/immutable-review checks, tested separately above or fixed source contracts.
def toml_value(v):
 if type(v) is bool:return 'true' if v else 'false'
 if type(v) is str:return json.dumps(v)
 if type(v) in (int,float):return repr(v)
 if type(v) is list:return '['+','.join(toml_value(x) for x in v)+']'
 if type(v) is dict:return '{'+','.join(json.dumps(k)+'='+toml_value(x) for k,x in v.items())+'}'
 raise TypeError(type(v))
def toml_doc(v):return '\n'.join(json.dumps(k)+'='+toml_value(x) for k,x in v.items())+'\n'
def full_fixture(t):
 run=t/'run';out=run/'output';payload=run/'payload';outer=t/'outer'
 for d in (out,payload,outer):d.mkdir(parents=True)
 cfg=dict(phase='p011-300',mode='red',seconds=300,expected_exit=0,stage='/stage',run=str(run),output=str(out),payload=str(payload),command=['test-command'])
 identity=lambda pid:dict(pid=pid,pgid=pid,sid=pid,boot_id='boot',start_ticks=1,command='command')
 guard,child=identity(10),identity(11);host=dict(head='head',master='master',boot_id='boot',groups=[1,10,11],matches=[])
 seal=dict(phase='p011-300',config=cfg,files=[str(outer/'outer-ready.json')],trees=[],inventory={},groups=[1],head='head',master='master',boot_id='boot')
 pp=run/'launch-pins.json';sp=run/'sealed.json';rp=run/'admission.json'
 pins=dict(files=seal['files']+[str(x) for x in (sp,rp,run/'prehost.json',outer/'release.json',outer/'outer-invocation.json')],trees=[],inventory={})
 sup=dict(guard_identity=guard,elapsed_seconds=1.0,returncode=0,accepted=True,**{k:False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']})
 mem=dict(available_kib=8*1024**2,swap_used_kib=0)
 proc=dict(runner=guard,child=child,pins_unchanged=True,command=cfg['command'],pins_sha256='sha',terminal_memory=mem,child_maxrss_kib=1000,elapsed_including_launch=1.0,cwd=str(c.R),returncode=0,reason='exit0')
 inv=dict(supervisor=sup,elapsed_seconds=1.0,command=cfg['command'],pins_sha256='sha',guard_command=['guard'],python=sys.executable,monotonic_start=1,reservation_sha256='sha',review_sha256='sha')
 res=dict(one_attempt=True,phase='p011-300',command=cfg['command'],pins_sha256='sha',review_sha256='sha',max_seconds=300)
 data={run/'sealed.json':seal,run/'admission.json':{},pp:pins,out/'pins.json':pins,run/'invocation.json':inv,out/'process.json':proc,out/'current.json':deepcopy(proc),run/'prehost.json':host,run/'host.json':host,run/'posthost.json':host,run/'config.json':cfg,run/'reservation.json':res}
 for path,value in data.items():path.write_text(json.dumps(value))
 (out/'resources.jsonl').write_text(json.dumps(dict(mem,elapsed=.5))+'\n');(out/'run.log').write_text('');(run/'launcher.log').write_text('')
 for name,value in fixture().items():(payload/name).write_text(toml_doc(value))
 return cfg,data

def full_case(name,mutation=None,success=False):
 with tempfile.TemporaryDirectory() as t:
  cfg,data=full_fixture(Path(t));run=Path(cfg['run']);out=Path(cfg['output']);payload=Path(cfg['payload'])
  if mutation:mutation(run,out,payload)
  with ExitStack() as stack:
   replacements=dict(config=lambda phase:cfg,validate_environment=lambda:None,preparation=lambda:None,validate_sources=lambda:None,predecessor=lambda phase:([],[]),verify_seal=lambda *x:None,verify_outer_invocation=lambda *x:None,verify_review=lambda *x:None,outer_dir=lambda phase:Path(t)/'outer',sha=lambda p:'sha',host_safe=lambda h:h['matches']==[],guard_command=lambda *x:['guard'],loaded_for=lambda cfg:LOADED)
   for k,v in replacements.items():stack.enter_context(patch.object(a,k,v))
   stack.enter_context(patch.object(a.guard,'pins_match',lambda p:True))
   if success:check(name,a.checks_for('p011-300')['all_passed'] is True)
   else:refuse(name,lambda:a.checks_for('p011-300'))
def edit_json(file,key,value):
 x=json.loads(file.read_text());x[key]=value;file.write_text(json.dumps(x))
full_case('full_positive',success=True)
for key,value in [('returncode',2),('returncode',False),('reason','wall_time'),('pins_unchanged',False),('cwd','/wrong'),('elapsed_including_launch',293),('error','bad'),('terminal_memory',dict(available_kib=1,swap_used_kib=0)),('child_maxrss_kib',float('nan'))]:
 full_case('process_'+key,lambda run,out,payload,key=key,value=value:edit_json(out/'process.json',key,value))
for key,value in [('elapsed_seconds',301),('pins_sha256','bad'),('review_sha256','bad'),('reservation_sha256','bad'),('guard_command',['bad'])]:
 full_case('invocation_'+key,lambda run,out,payload,key=key,value=value:edit_json(run/'invocation.json',key,value))
for flag in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill'):
 def mutate(run,out,payload,flag=flag):
  p=run/'invocation.json';x=json.loads(p.read_text());x['supervisor'][flag]=True;p.write_text(json.dumps(x))
 full_case('supervisor_'+flag,mutate)
full_case('payload_missing',lambda run,out,payload:(payload/'load.toml').unlink())
full_case('payload_extra',lambda run,out,payload:(payload/'extra').write_text(''))
full_case('payload_invalid_toml',lambda run,out,payload:(payload/'setup.toml').write_text('not toml'))
full_case('guard_extra',lambda run,out,payload:(out/'extra').write_text(''))
full_case('warning_log',lambda run,out,payload:(out/'run.log').write_text('WARNING: world age'))
full_case('empty_resources',lambda run,out,payload:(out/'resources.jsonl').write_text(''))
full_case('resource_boolean',lambda run,out,payload:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=True,swap_used_kib=0))))
full_case('bad_posthost',lambda run,out,payload:edit_json(run/'posthost.json','matches',[{'pid':11}]))
full_case('reservation_boolean',lambda run,out,payload:edit_json(run/'reservation.json','one_attempt',1))
def symlink_payload(run,out,payload):
 p=payload/'load.toml';target=run/'load-copy';p.rename(target);p.symlink_to(target)
full_case('payload_symlink',symlink_payload)
for value in (True,-1,float('nan'),float('inf'),301,1.1):
 full_case('resource_elapsed_'+repr(value),lambda run,out,payload,value=value:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=value))))
full_case('resource_elapsed_missing',lambda run,out,payload:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0))))
def reversed_resources(run,out,payload):
 (out/'resources.jsonl').write_text('\n'.join(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=t)) for t in (.8,.5)))
full_case('resource_elapsed_reversed',reversed_resources)
full_case('resource_unknown_field',lambda run,out,payload:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=.5,unknown=0))))
full_case('resource_child_memory_type',lambda run,out,payload:(out/'resources.jsonl').write_text(json.dumps(dict(available_kib=8*1024**2,swap_used_kib=0,elapsed=.5,child_memory=1))))
# Fresh one-shot check output, not an auditor against actual evidence.
result=dict(all_passed=True,count=len(checks),checks=checks,scope='Synthetic Python; external host/pin boundaries mocked in full-case tests; no Julia/guard/outer/launch',sha256={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('tests_reviewed.py','oracle.py','audit.py','control.py')})
with (D/'tests-reviewed.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks))))
