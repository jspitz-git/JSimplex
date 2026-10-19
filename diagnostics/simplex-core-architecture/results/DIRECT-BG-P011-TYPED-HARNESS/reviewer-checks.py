"""Independent preparation review: Python saved-data/source checks only.
Never executes Julia, old tests, audit(), or seal/outer/launch/guard entrypoints.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import hashlib,json,sys,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-TYPED-HARNESS')
R=D.parents[3]
sys.path.insert(0,str(D))
import oracle as o
import control as c
from audit import resource_records
rows=[]
def check(name,value):rows.append(dict(name=name,passed=bool(value)))
def refused(fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError):return True
 return False
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
# Independent occurrence ledger from manually read source loops, including both
# conditional arms P067-P075. No oracle-produced expectations in the fixture.
counts={f'P{i:03}':1 for i in range(1,95)}
for key,n in {1:5,13:2,15:4,27:3,66:2}.items():counts[f'P{key:03}']=n
for start,end,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
 for i in range(start,end+1):counts[f'P{i:03}']=n
names=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
loaded={'JSimplex':'/stage/src/JSimplex.jl','Test':'/test','LinearAlgebra':'/la','TOML':'/toml','PrecompileTools':'/precompile'}
normal_detail='Test Failed at /frozen/panel-tests.jl:104\n  Expression: #= /frozen/panel-tests.jl:104 =# @allocated(K._bgb_eligibility(f, 1)) == 0\n   Evaluated: 208 == 0'
def fixture(red):
 phase='p011-red300' if red else 'p011-green300';sites=counts.copy()
 if not red:sites.update({f'P{i:03}':1 for i in range(95,103)})
 children=[]
 for i,n in enumerate([23+(0 if red else 8),11619,74,44]):
  fail=int(red and i==0);children.append(dict(name=names[i],children=[],**{'pass':n-fail,'fail':fail,'error':0,'broken':0}))
 root=dict(name='panel',children=children,**{'pass':0,'fail':0,'error':0,'broken':0})
 failures=[dict(site='P011',kind='fail',detail=normal_detail)] if red else []
 u=dict(index=1,name='panel',complete=True,fatal='',tests=root,records=dict(sites=sites,events={},apis={},failures=failures,failure_count=len(failures),active=''))
 d=dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20)
 p=dict(bytes=0,events=0,consumed_bytes=0,consumed_events=0,warm=d,bytes_decision=deepcopy(d),events_decision=deepcopy(d),values_unchanged=True,owners_unchanged=True)
 raw=dict(schema=1,phase=phase,complete=True,fatal='',qualification='p011_typed_structural',test_source='/frozen/tests',loaded=loaded,threads=1,blas_threads=1,probe=deepcopy(p),unit=deepcopy(u),totals=[11759,1,0,0] if red else [11768,0,0,0])
 m=dict(seconds=.01,bytes=1,events=1,gc_seconds=0.,compile_seconds=.001,recompile_seconds=0.)
 return {**{n:deepcopy(m) for n in ('load.toml','panel-load.toml','tests-load.toml','probe-setup.toml','probe-cost.toml','tests-cost.toml')},'probe.toml':p,'unit-1.toml':u,'raw.toml':raw}
def valid(v,red):return o.validate(v,loaded,'p011-red300' if red else 'p011-green300','/frozen/tests')
for red in (True,False):
 phase='p011-red300' if red else 'p011-green300';p=fixture(red)
 check(phase+' independent counts',valid(p,red)['totals']==([11759,1,0,0] if red else [11768,0,0,0]))
 for n in p:
  q=deepcopy(p);del q[n];check(phase+' missing '+n,refused(lambda:valid(q,red)))
 for n in o.PREPARATION:
  for k in ('bytes','events'):
   for bad in [True,-1,2**63,0.5]:
    q=deepcopy(p);q[n][k]=bad;check(phase+' metric '+n+k+repr(bad),refused(lambda:valid(q,red)))
  for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
   for bad in [True,float('nan'),float('inf'),-1,300.1]:
    q=deepcopy(p);q[n][k]=bad;check(phase+' time '+n+k+repr(bad),refused(lambda:valid(q,red)))
 for arm in ('warm','bytes_decision','events_decision'):
  for i in range(20):
   q=deepcopy(p);q['probe.toml'][arm]['counters'][i]=1;q['raw.toml']['probe']=deepcopy(q['probe.toml']);check(phase+' counter '+arm+str(i),refused(lambda:valid(q,red)))
 for key in ('probe','unit'):
  q=deepcopy(p)
  if key=='probe':q['raw.toml'][key]['owners_unchanged']=False
  else:q['raw.toml'][key]['complete']=False
  check(phase+' raw '+key,refused(lambda:valid(q,red)))
 log='TEST FAILURE: P011 '+normal_detail+'\n' if red else ''
 check(phase+' ordinary expected log',not o.warning_log(log,p,phase))
 for warning in ['WARNING: method overwriting','ERROR: unexpected','world age mismatch','TEST FAILURE: P012 nope']:
  check(phase+' distinct warning '+warning,o.warning_log(log+warning,p,phase))
# These are expected-to-reject malformed RED records. The current implementation
# accepts them; retain failing assertions rather than weakening expectations.
for label,detail in [('unrelated_failure','Test Failed at another.jl:1\n  Expression: unrelated() == 0\n   Evaluated: 1 == 0'),('embedded_warning',normal_detail+'\nWARNING: method overwriting'),('arbitrary_detail','arbitrary nonempty text')]:
 p=fixture(True);p['unit-1.toml']['records']['failures'][0]['detail']=detail;p['raw.toml']['unit']=deepcopy(p['unit-1.toml'])
 def all_checks():
  valid(p,True)
  if o.warning_log('TEST FAILURE: P011 '+detail,p,'p011-red300'):raise ValueError('Log refused')
 check('RED expected rendering must reject '+label,refused(all_checks))
# Offline immutable source evidence; no calls to control.validate_sources (which
# also contacts remote Git), author verification scripts, or action entrypoints.
pins=rd(D/'preparation-pins.json');required=rd(D/'required-paths.json')['paths']
check('234 exact manifest subjects',len(pins['sha256'])==len(required)==234 and set(pins['sha256'])==set(required))
for n,h in pins['sha256'].items():check('manifest '+n,sha(n)==h)
check('local source membership',all(str(p) in pins['sha256'] for p in D.iterdir() if p.is_file() and p.name not in ['preparation-pins.json','review.md','review.json','reviewer-checks.py','reviewer-results.json']))
for n,v in rd(D/'copied-files.json').items():check('copied '+n,sha(D/n)==sha(v['source'])==v['sha256'])
for n,v in rd(D/'adapted-files.json').items():check('provenance '+n,sha(D/n)==v['prepared_sha256'] and sha(v['source'])==v['original_sha256'])
for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 baseline=rd(D/'baseline.json')[label];check(label+' baseline all hashes',all(sha(root/n)==h for n,h in baseline.items()))
runtime=rd(D/'runtime-inputs-complete.json')['inventory'];check('609 runtime hashes and resolved paths',len(runtime)==609 and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in runtime.items()))
stage=rd(D/'stages.json')['red'];sr=Path(stage['path']);check('75 stage exact hashes membership no symlinks',len(stage['sha256'])==75 and {str(p.relative_to(sr)) for p in sr.rglob('*') if p.is_file()}==set(stage['sha256']) and not any(p.is_symlink() for p in sr.rglob('*')) and all(sha(sr/n)==h for n,h in stage['sha256'].items()))
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
check('new package Python syntax',True)
T=D.with_name('DIRECT-BG-P011-TYPED-REPAIR');F=D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')
redtext=(F/'panel-tests.jl').read_text();green=(T/'panel-tests.jl').read_text();helper=(T/'helpers.jl').read_text();original=(T/'original-block.txt').read_text();replacement=(T/'replacement.txt').read_text()
check('helper once and only intended replacement',green.count(helper)==1 and green.replace(helper,'',1).replace(replacement,original,1)==redtext)
for phase,code in [('p011-red300',1),('p011-green300',0)]:
 cfg=c.config(phase);check(phase+' same stage exact bound',cfg['stage']==str(sr) and cfg['seconds']==300 and cfg['expected_exit']==code and cfg['command'][-1]==phase)
 check(phase+' child 292 guard argument','--seconds' in c.guard_command(cfg,'/pins',100) and c.guard_command(cfg,'/pins',100)[c.guard_command(cfg,'/pins',100).index('--seconds')+1]=='292')
mem=dict(available_kib=6*1024**2,swap_used_kib=1024**2)
check('resource boundaries',resource_records([dict(mem,elapsed=1)],mem,1))
for samples in [[dict(mem,elapsed=2)],[dict(mem,elapsed=True)],[dict(mem,elapsed=.8),dict(mem,elapsed=.7)],[dict(mem,elapsed=float('nan'))]]:
 check('resource ordering/type '+repr(samples),refused(lambda:resource_records(samples,mem,1)))
with patch.object(c,'rd',lambda p:dict(all_passed=False)):
 check('GREEN missing RED refused',refused(lambda:c.predecessor('p011-green300')))
check('RED no predecessor',c.predecessor('p011-red300')==([],[]))
check('no action artifacts',not (D/'runs').exists() and not (D/'outers').exists())
result=dict(scope='Independent offline Python/source review only; no Julia/action entrypoints/old tests; RED malformed-rendering negative tests expose finding',count=len(rows),passed=sum(r['passed'] for r in rows),all_passed=all(r['passed'] for r in rows),failures=[r['name'] for r in rows if not r['passed']],checks=rows,pins_sha256=sha(D/'preparation-pins.json'),reviewed_sources={n:sha(D/n) for n in ['oracle.py','audit.py','control.py','driver.jl']},script_sha256=sha(__file__))
with (D/'reviewer-results.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['count','passed','all_passed','failures','pins_sha256']}))
