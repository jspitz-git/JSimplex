from pathlib import Path
import ast
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';D=B/'DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS';F=B/'DIRECT-BG-BLOCKED-UPDATE-HARNESS';P=B/'DIRECT-BG-P011-TYPED-HARNESS'
s=(F/'synthetic-reviewed.py').read_text();s=s[:s.index('\ndef run():')];s=s.replace("children=[node(n,0) for n in names];children[0]['pass']=sum(sites.values())","children=[node(n,k) for n,k in zip(names,[31,11619,74,44])]")
s=s.replace("detail='synthetic coverage'","detail='Test Failed at numerical-tests.jl:163\\n  Expression: sum(o.panels for o in observed) >= f[\"minimum_panels\"]'")
s+='''
def metric():return dict(seconds=.1,bytes=80,events=2,gc_seconds=.01,compile_seconds=.02,recompile_seconds=.0)
LOADED={}
def fixture(phase):
 raw,rows=mock('red' if phase=='red300' else 'green')
 return {**rows,'raw.toml':raw,**{n:metric() for n in o.PREPARATION}}
def logfile(phase,payload):
 out='BEGIN BG blocked U driver '+phase+'\\n'
 for i in range(1,29):
  u=payload[f'unit-{i}.toml'];out+=f"UNIT BEGIN {i} {u['name']}\\n"
  for f in u['records']['failures']:out+='TEST FAILURE: '+f['site']+' '+f['detail']+'\\n'
  out+=f"UNIT END {i} {u['name']}\\n"
 return out
'''
with (D/'synthetic-data.py').open('x') as f:f.write(s)
# Copy only synthetic full auditor exercise, with new fixtures and real TOML codec.
s=(P/'tests-reviewed.py').read_text();a=s.index('def tv(');b=s.index('# Fresh regression cases',a);s=s[a:b]
s=s.replace("int(phase.endswith('red300'))","int(phase=='red300')").replace("log='' if cfg['expected_exit']==0 else 'TEST FAILURE: P011 '+fixture_data['unit-1.toml']['records']['failures'][0]['detail']+'\\n'","log=logfile(phase,fixture_data)")
s=s.replace(",test_source_for=lambda _: '/tests/'+phase",'')
s=s.replace("('p011-red300','p011-green300')","('red300','green300')")
# Real audit reads schedule through rd; create it outside run and patch D only.
s=s.replace("outer=t/'outer'","outer=t/'outer';package=t/'package';package.mkdir();(package/'schedule.json').write_text(json.dumps(S))")
s=s.replace("mocks=dict(config=", "mocks=dict(D=package,config=")
header='''"""New offline synthetic oracle and complete auditor tests. No execution entrypoints."""
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
'''
footer='''
with patch.object(c,'rd',lambda _: {'all_passed':False}):refuse('green_missing_accepted_red',lambda:c.predecessor('green300'))
check('red_no_predecessor',c.predecessor('red300')==([],[]))
with tempfile.TemporaryDirectory() as t:
 p=Path(t)/'pin';p.write_text('fixed');v=dict(accepted=True,findings=[],scope='BG blocked typed exact-run admission',phase='red300',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 c.verify_review(v,p,[str(p)],v['scope'],v['phase']);check('receipt_positive',True)
 for k,bad in [('accepted',1),('findings',['x']),('scope','old'),('phase','green300'),('pins_sha256','bad'),('sha256',{})]:
  q=deepcopy(v);q[k]=bad;refuse('receipt_'+k,lambda q=q:c.verify_review(q,p,[str(p)],v['scope'],v['phase']))
result=dict(all_passed=True,count=len(checks),checks=checks,scope='New Python synthetic payload/process refusal tests; external host/source/review boundaries mocked only in complete auditor fixture. No Julia or launch.',sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('tests.py','synthetic-data.py','oracle.py','audit.py','control.py','driver.jl')})
with (D/'tests.json').open('x') as f:json.dump(result,f,indent=2);f.write('\\n')
print(json.dumps({'all_passed':True,'checks':len(checks),'payload_files':len(o.PAYLOAD),'prospective_RED_failures':6}))
'''
with (D/'tests.py').open('x') as f:f.write(header+s+footer)
print('Saved new synthetic failure tests before execution')
