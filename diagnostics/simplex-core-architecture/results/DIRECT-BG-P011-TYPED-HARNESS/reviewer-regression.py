"""Fresh bounded R1 re-review. Pure Python saved-data and hash checks only.
Does not execute any previous test/reviewer/preparation script or action entrypoint.
"""
from pathlib import Path
from copy import deepcopy
import ast,hashlib,json,sys,tomllib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-TYPED-HARNESS')
sys.path.insert(0,str(D))
import oracle as o
rows=[]
def check(n,v):
 rows.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reject(f):
 try:f()
 except (ValueError,TypeError,KeyError,RuntimeError):return True
 return False
fix=rd(D/'review-fix-provenance.json');maps=rd(D/'final-mappings.json');pins=rd(D/'preparation-pins.json')
historical=Path(fix['historical_rendering_source']);saved=tomllib.loads(historical.read_text())['records']['failures'][0];detail=saved['detail']
source=str(D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')/'panel-tests.jl')
literal='Test Failed at '+source+':103\n  Expression: $(Expr(:escape, :(#= '+source+':103 =# @allocated(K._bgb_eligibility(f, 1)) == 0)))'
check('historical detail matches independently reconstructed literal',detail==literal==o.RED_FAILURE_DETAIL and len(detail)==439 and saved['site']=='P011' and saved['kind']=='fail')
check('frozen assertion location',Path(source).read_text().splitlines()[102].strip()=='@check "P011" (@allocated K._bgb_eligibility(f,1)) == 0')
check('historical raw bound',str(historical) in pins['sha256'] and sha(historical)==fix['historical_rendering_sha256']==pins['sha256'][str(historical)])
check('no new allocation amount prescribed','208' not in literal and 'Evaluated:' not in literal)
counts={f'P{i:03}':1 for i in range(1,95)}
for i,n in {1:5,13:2,15:4,27:3,66:2}.items():counts[f'P{i:03}']=n
for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
 for i in range(lo,hi+1):counts[f'P{i:03}']=n
names=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
loaded=dict(JSimplex='/stage/src/JSimplex.jl',Test='/test',LinearAlgebra='/la',TOML='/toml',PrecompileTools='/pt')
def fixture(red):
 phase='p011-red300' if red else 'p011-green300';sites=counts.copy()
 if not red:sites.update({f'P{i:03}':1 for i in range(95,103)})
 children=[]
 for i,n in enumerate([23 if red else 31,11619,74,44]):
  f=int(red and i==0);children.append(dict(name=names[i],children=[],**{'pass':n-f,'fail':f,'error':0,'broken':0}))
 u=dict(index=1,name='panel',complete=True,fatal='',tests=dict(name='panel',children=children,**{'pass':0,'fail':0,'error':0,'broken':0}),records=dict(sites=sites,events={},apis={},active='',failure_count=int(red),failures=[dict(site='P011',kind='fail',detail=literal)] if red else []))
 d=dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20)
 p=dict(bytes=0,events=0,consumed_bytes=0,consumed_events=0,warm=deepcopy(d),bytes_decision=deepcopy(d),events_decision=deepcopy(d),values_unchanged=True,owners_unchanged=True)
 raw=dict(schema=1,phase=phase,complete=True,fatal='',qualification='p011_typed_structural',test_source='/frozen/tests',loaded=loaded,threads=1,blas_threads=1,probe=deepcopy(p),unit=deepcopy(u),totals=[11759,1,0,0] if red else [11768,0,0,0])
 costs={n:dict(seconds=.1,bytes=8,events=1,gc_seconds=0.,compile_seconds=.02,recompile_seconds=0.) for n in ['load.toml','panel-load.toml','tests-load.toml','probe-setup.toml','probe-cost.toml','tests-cost.toml']}
 return dict(costs,**{'raw.toml':raw,'unit-1.toml':u,'probe.toml':p})
def validate(p,red=True):return o.validate(p,loaded,'p011-red300' if red else 'p011-green300','/frozen/tests')
for red in (True,False):
 p=fixture(red);phase='p011-red300' if red else 'p011-green300'
 check('valid full '+phase,validate(p,red)['totals']==p['raw.toml']['totals'])
 log='TEST FAILURE: P011 '+literal+'\n' if red else ''
 check('valid log '+phase,not o.warning_log(log,p,phase))
 for bad in ['WARNING: method overwriting','world age warning','ERROR: unexpected','Test Failed at elsewhere:1','TEST FAILURE: P012 bad','Test Error','LoadError','OutOfMemoryError']:
  check(phase+' appended '+bad,o.warning_log(log+bad,p,phase))
  check(phase+' prepended '+bad,o.warning_log(bad+'\n'+log,p,phase))
red=fixture(True)
bad_details=['arbitrary nonempty text','Test Failed at another.jl:1\n  Expression: unrelated() == 0\n   Evaluated: 1 == 0',literal+'\nWARNING: method overwriting',literal.replace('_bgb_eligibility','unrelated'),literal.replace(':103',':104'),literal+'\n',literal+'\n   Evaluated: 208 == 0',literal.replace(' == 0',' == 1'),'WARNING: hidden\n'+literal,literal+'\nTest Failed at another.jl:9',literal+'\nERROR: hidden','',literal[:-1]]
for i,bad in enumerate(bad_details):
 p=deepcopy(red);p['unit-1.toml']['records']['failures'][0]['detail']=bad;p['raw.toml']['unit']=deepcopy(p['unit-1.toml'])
 check('malformed detail full payload '+str(i),reject(lambda:validate(p)))
 check('malformed detail standalone log '+str(i),o.warning_log('TEST FAILURE: P011 '+bad+'\n',p,'p011-red300'))
for label,log in [('missing',''),('duplicate',('TEST FAILURE: P011 '+literal+'\n')*2),('changed prefix','TEST FAILURE: P012 '+literal),('unexpected suffix','TEST FAILURE: P011 '+literal+'\nTest Failed')]:
 check('log '+label,o.warning_log(log,red,'p011-red300'))
# Verify exact revised bindings and explicitly mapped immutable earlier evidence.
required=rd(D/'required-paths.json')['paths']
check('258 exact unique subjects',len(pins['sha256'])==len(required)==len(set(required))==258 and set(required)==set(pins['sha256']))
for n,h in pins['sha256'].items():check('current '+n,Path(n).is_file() and not Path(n).is_symlink() and sha(n)==h)
def mapped(n,h):
 candidates=[n]
 if n in fix['before']:candidates.append(fix['before'][n]['preserved_path'])
 if n in maps['correction_check_maps']:candidates.append(maps['correction_check_maps'][n])
 if n in maps['intermediate_manifest_maps']:candidates.append(maps['intermediate_manifest_maps'][n]['preserved_path'])
 return any(sha(p)==h for p in candidates)
for n in ['preparation-pins.json.before-review','review.json.before-review','source-check.json','review-fix-check.json','preparation-pins.json.before-final-mapping']:
 j=rd(D/n);check('all preserved bindings '+n,all(mapped(p,h) for p,h in j['sha256'].items()))
for n,v in fix['before'].items():check('explicit before mapping '+n,sha(v['preserved_path'])==v['sha256'])
for n,v in maps['intermediate_manifest_maps'].items():check('explicit intermediate mapping '+n,sha(v['preserved_path'])==v['sha256'])
old=rd(D/'review.json.before-review')
check('original rejected receipt preserved',old['accepted'] is False and old['launch_admitted'] is False and len(old['findings'])==1 and old['pins_sha256']==sha(D/'preparation-pins.json.before-review') and all(mapped(n,h) for n,h in old['evidence_sha256'].items()))
check('original reproductions unchanged',sha(D/'reviewer-checks.py')==old['evidence_sha256'][str(D/'reviewer-checks.py')] and sha(D/'reviewer-results.json')==old['evidence_sha256'][str(D/'reviewer-results.json')])
initial=rd(D/'preparation-pins.json.before-review')['sha256']
for n in ['driver.jl','control.py','audit.py','guard.py','supervisor.py','seal.py','launch.py','outer.py','post-return.py','recorder.jl','stages.json','runtime-inputs-complete.json','baseline.json']:
 check('unchanged control/source '+n,sha(D/n)==initial[str(D/n)])
for n,expected in [('tests.json',864),('tests-reviewed.json',894)]:
 j=rd(D/n);check('saved author results '+n,j['all_passed'] is True and j['count']==expected and all(mapped(str(D/p),h) for p,h in j['sha256'].items()))
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
check('current Python sources parse',True)
check('no action directories',not (D/'runs').exists() and not (D/'outers').exists())
result=dict(scope='Fresh bounded offline R1 re-review; prior scripts/tests not rerun; no Julia or action entrypoints',all_passed=True,count=len(rows),checks=rows,pins_sha256=sha(D/'preparation-pins.json'),oracle_sha256=sha(D/'oracle.py'),script_sha256=sha(__file__),prior_receipt_sha256=sha(D/'review.json.before-review'))
with (D/'reviewer-regression-results.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','count','pins_sha256','oracle_sha256']}))
