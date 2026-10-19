"""Fresh independent offline review. No Julia, run/seal/outer entrypoint or old checker.
Only pure definitions imported. Synthetic files are private temporary fixtures.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import ast, hashlib, importlib.util, json, math, re, sys, tempfile
D=Path(__file__).resolve().parent
P=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS')
R=D.parents[3]
sys.path.insert(0,str(D))
import control as c, audit as a, oracle as o
checks=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def ck(n,b):
 if not b:raise AssertionError(n)
 checks.append(n)
def reject(n,fn):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError,FileNotFoundError):checks.append(n);return
 raise AssertionError('Accepted '+n)
def bound(n,m):
 for p,h in m.items():ck(n+':'+p,Path(p).is_file() and not Path(p).is_symlink() and sha(p)==h)

pins=rd(D/'preparation-pins.json');required=rd(D/'required-paths.json')['paths']
ck('711 exact unique subjects',len(required)==len(set(required))==len(pins['sha256'])==711 and set(required)==set(pins['sha256']))
bound('fresh preparation hash',pins['sha256'])
# Reconstruct membership independently of the required-paths list.
local={str(p) for p in D.iterdir() if p.is_file() and p.name not in {'preparation-pins.json','independent-preparation-check.py'}}
expected=local|set(rd(P/'preparation-pins.json')['sha256'])|set(rd(D/'timeout-bindings.json')['sha256'])
expected|={str(P/'preparation-pins.json'),str(P/'review.json')}|set(rd(P/'review.json')['evidence_sha256'])
expected|={str(R/'AGENTS.md'),str(R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md'),str(R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'),str(P/'MEMORY-WORK.md'),str(D/'required-paths.json')}
ck('independently reconstructed membership',expected==set(required))
cp=rd(D/'copied-files.json');ck('exact22copy roster',len(cp)==22)
for n,v in cp.items():ck('copy '+n,(D/n).read_bytes()==Path(v['source']).read_bytes() and sha(D/n)==v['sha256'])
ck('all Julia text copied',set(p.name for p in D.glob('*.jl'))=={n for n in cp if n.endswith('.jl')})
trans=rd(D/'control-transform.json');ck('six control files only',set(trans)=={'control.py','seal.py','outer.py','launch.py','oracle.py','audit.py'})
for n,v in trans.items():
 s=(D/n).read_text();ck('prepared digest '+n,sha(D/n)==v['prepared_sha256'])
 if 'append' in v:ck('append '+n,s.endswith(v['append']));s=s[:-len(v['append'])]
 for i,e in reversed(list(enumerate(v['edits']))):
  ck('inverse anchor '+n+str(i),s.count(e['new'])==e['count']);s=s.replace(e['new'],e['old'])
 ck('full inverse '+n,s.encode()==Path(v['source']).read_bytes() and sha(v['source'])==v['source_sha256'])
ck('oracle mathematical code identical',(D/'oracle.py').read_text().replace('0<=v[k]<=1800','0<=v[k]<=300')==(P/'oracle.py').read_text())
c.validate_probe();c.validate_typed();c.validate_qualification();c.validate_stage_binding();c.validate_timeout_record();ck('source stage candidate typed fault and diagnostic gates',True)
for n in ('source-check.json','tests.json'):
 j=rd(D/n);ck('saved result '+n,j['all_passed'] is True);bound('saved bindings '+n,j['sha256'])
ck('saved51 source checks',len(rd(D/'source-check.json')['checks'])==51 and all(rd(D/'source-check.json')['checks'].values()))
ck('saved2378 synthetic checks',rd(D/'tests.json')['count']==len(rd(D/'tests.json')['checks'])==2378)
for p in D.glob('*.py'):ast.parse(p.read_text());ck('Python syntax '+p.name,True)
lineage=rd(D/'timeout-bindings.json');bound('timeout lineage',lineage['sha256']);ck('81 prior files',len(lineage['sha256'])==81)
old_audit=rd(lineage['audit']);ck('old RED stays rejected',old_audit['all_passed'] is False and old_audit['pure_timeout'] is False)
old_review=rd(lineage['review']);ck('old review diagnostic only',old_review['accepted'] is True and old_review['qualification_accepted'] is False)
groups=rd(D/'historical-groups.json')['groups'];ck('289 unique groups',len(groups)==len(set(groups))==289 and {209350,210015,210016}<=set(groups))
ck('289 closure groups identical',set(groups)==set(rd(lineage['closure'])['host']['groups']))
oldpayload=Path(lineage['run'])/'payload';ck('old incomplete evidence preserved',not (oldpayload/'raw.toml').exists() and not (oldpayload/'unit-11.toml').exists())
ck('no new execution state',not (D/'runs').exists() and not (D/'outers').exists())
cfg=c.config('red1800');ck('RED config',cfg['seconds']==1800 and cfg['expected_exit']==1 and cfg['mode']=='red')
ck('new run namespace',cfg['run']==str(D/'runs/red1800') and cfg['payload']==str(D/'runs/red1800/payload') and cfg['output']==str(D/'runs/red1800/output') and c.outer_dir('red1800')==D/'outers/red1800')
ck('driver phase mapping',cfg['command'][-4:]==[str(D/'driver.jl'),cfg['payload'],cfg['stage'],'red300'])
ck('unchanged thread and heap flags',cfg['command'][2:7]==['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no'])
for phase in ('red300','green300','green1800','red600','',None):reject('unprepared phase '+str(phase),lambda phase=phase:c.config(phase))
g=c.guard_command(cfg,Path('/tmp/nonexistent-review-pins'),100.)
ck('1792 guard and absolute deadline',g[g.index('--seconds')+1]=='1792' and g[g.index('--deadline')+1]=='1892.0')
ck('full historical predecessor',c.predecessor('red1800')==(sorted(lineage['sha256']),groups))
# Existing numerical sources are read as text, never parsed by Julia.
sites=set()
for n in ('panel-tests.jl','lifecycle-tests.jl','numerical-tests.jl'):sites.update(re.findall(r'@check(?:throws)? "([PLN][0-9]{3})"',(D/n).read_text()))
ck('168 sites',len(sites)==168)
ck('panel11768 and P011 exact zero allocation guards',sum(o.panel_counts().values())==11768 and o.panel_counts()['P011']==1 and '"P011"' in (D/'panel-tests.jl').read_text())
sch=rd(D/'schedule.json');ck('28 units and six RED cases',len(sch['units'])==28 and len(sch['expected_red_units'])==6)
ck('60 payload31 costs',len(o.PAYLOAD)==60 and len(o.PREPARATION)==31)
# Boundary testing of new time bounds, all other metric schemas unchanged.
metric=dict(seconds=1800.,bytes=0,events=0,gc_seconds=1800.,compile_seconds=1800.,recompile_seconds=1800.)
ck('cost1800 inclusive',o.metrics(metric)==metric)
for k in o.METRICS:
 vals=(True,-1,float('inf'),float('nan'),'1',1800.000001) if k not in ('bytes','events') else (True,-1,1.5,2**63)
 for v in vals:
  q=dict(metric);q[k]=v;reject('metric '+k+' '+repr(v),lambda q=q:o.metrics(q))
mem=dict(available_kib=6*1024**2,swap_used_kib=1024**2)
ck('resource1792 inclusive thresholds',a.resource_records([dict(mem,elapsed=1792.)],mem,1792.))
for t in (1792.000001,True,-1,float('nan'),float('inf')):reject('resource elapsed '+repr(t),lambda t=t:a.resource_records([dict(mem,elapsed=0.)],mem,t))
for k,v in [('available_kib',6*1024**2-1),('swap_used_kib',1024**2+1),('available_kib',True)]:
 bad=dict(mem);bad[k]=v;reject('resource limit '+k+repr(v),lambda bad=bad:a.resource_records([dict(bad,elapsed=0.)],mem,1.))
# Real review-binding verifier against temporary synthetic files.
with tempfile.TemporaryDirectory(prefix='red1800-independent-') as tmp:
 t=Path(tmp);p=t/'pins';p.write_text('fixed');f=t/'subject';f.write_text('subject')
 scope='BG blocked typed RED repeat exact-run admission'
 v=dict(accepted=True,findings=[],scope=scope,phase='red1800',pins_sha256=sha(p),sha256={str(f):sha(f)})
 c.verify_review(v,p,[str(f)],scope,'red1800');ck('future exact review accepts valid binding',True)
 for key,bad in [('accepted',1),('findings',['unresolved']),('phase','red300'),('scope','BG blocked typed exact-run admission'),('pins_sha256','bad'),('sha256',{})]:
  q=deepcopy(v);q[key]=bad;reject('future receipt '+key,lambda q=q:c.verify_review(q,p,[str(f)],scope,'red1800'))
 f.write_text('drift');reject('future receipt actual byte drift',lambda:c.verify_review(v,p,[str(f)],scope,'red1800'))
# Test preparation-only receipt enforcement without constructing/launching a run.
virtual=deepcopy(pins);manifest=D/'preparation-pins.json'
receipt=dict(accepted=True,findings=[],scope='BG blocked typed RED repeat preparation',pins_sha256=sha(manifest),sha256={**pins['sha256'],str(manifest):sha(manifest)},launch_admitted=False)
original_rd=c.rd
def virtual_rd(p):return receipt if Path(p)==D/'review.json' else original_rd(p)
with patch.object(c,'rd',virtual_rd):
 prepared=c.preparation();ck('preparation exact712 receipts accepted offline',len(receipt['sha256'])==712 and str(D/'review.json') in prepared)
 for bad in (True,None,0):
  receipt['launch_admitted']=bad;reject('preparation may not admit launch '+repr(bad),c.preparation)
 receipt['launch_admitted']=False
 receipt['sha256'].pop(next(iter(pins['sha256'])));reject('preparation missing one of711 rejected',c.preparation)
# Pure fixture generator; never import or rerun the old or new completed checkers.
spec=importlib.util.spec_from_file_location('independent_fixture',D/'synthetic-data.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
data=fixture.fixture('red300');result=o.validate(data,sch,fixture.LOADED,'red300');ck('full synthetic RED',result['units']==28 and result['expected_failures']==6)
ck('six expected N026 and no unexpected warnings',not o.warning_log(fixture.logfile('red300',data),data,'red300'))
for name in sorted(o.PAYLOAD):
 q=deepcopy(data);q.pop(name);reject('missing payload '+name,lambda q=q:o.validate(q,sch,fixture.LOADED,'red300'))
for phase in ('red1800','green300'):
 q=deepcopy(data);q['raw.toml']['phase']=phase;reject('raw semantic mismatch '+phase,lambda q=q:o.validate(q,sch,fixture.LOADED,'red300'))
for i in (1,9,28):
 q=deepcopy(data);q[f'unit-{i}.toml']['records']['sites'][next(iter(q[f'unit-{i}.toml']['records']['sites']))]+=1
 reject('assertion count drift '+str(i),lambda q=q:o.validate(q,sch,fixture.LOADED,'red300'))
# Independently saved control evidence; scope is source and synthetic checks only.
result=dict(all_passed=True,count=len(checks),checks=checks,subjects_rehashed=711,receipt_subjects=712,copies=22,control_inverses=6,prior_bound_files=81,historical_groups=289,runtime_executed=False,launch_admitted=False,scope='Independent offline preparation review; no Julia or runtime-entrypoint execution',sha256={str(D/n):sha(D/n) for n in ['independent-preparation-check.py','preparation-pins.json','required-paths.json','control-transform.json','copied-files.json','control.py','audit.py','oracle.py']})
with (D/'independent-preparation-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','count','subjects_rehashed','receipt_subjects','runtime_executed','launch_admitted']}))
