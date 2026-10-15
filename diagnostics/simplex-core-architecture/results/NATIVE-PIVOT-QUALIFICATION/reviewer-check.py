"""Independent offline reviewer checks; no Julia or stage/guard/old-script execution."""
from pathlib import Path
import ast, copy, hashlib, json, sys, tomllib
Q=Path(__file__).resolve().parent;R=Q.parents[3];P=Q.parent/'NATIVE-PIVOT-PREPARATION'
sys.path.insert(0,str(Q))
from control import verify_review, config
from oracle import test_results, cost_results
import oracle
from exact import token

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rd(p):return json.loads(Path(p).read_text())
checks={};refusals=[]
def refuses(name,fn):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError):refusals.append(name);return
 raise AssertionError('accepted invalid synthetic evidence: '+name)
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['all_new_python_syntax']=True
pins=rd(Q/'preparation-pins.json');assert len(pins['sha256'])==842
assert all(sha(n)==h for n,h in pins['sha256'].items());checks['all_842_fresh_hashes']=True
for name,z in rd(Q/'test-inverse.json').items():
 text=(Q/name).read_text();assert sha(Q/name)==z['sha256']
 for a,b,c in reversed(z['edits']):assert text.count(b)==c;text=text.replace(b,a)
 assert text.encode()==Path(z['source']).read_bytes() and sha(z['source'])==z['source_sha256']
checks['whole_test_inverse']=True
slices=rd(Q/'neighbor-slices.json');joined='using Test, JSimplex, LinearAlgebra, SparseArrays\n'
assert len(slices)==6 and sum('title' in s for s in slices)==5
for s in slices:
 text=(R/s['source']).read_text()[s['start']:s['end']];assert text==s['text'];joined+=text
assert joined==(Q/'neighbors-original.jl').read_text();checks['five_exact_neighbor_slices']=True
iv=rd(P/'inverse.json')
for name in {e['file'] for e in iv['edits']}:
 text=(P/'candidate'/name).read_text()
 for e in reversed([e for e in iv['edits'] if e['file']==name]):
  assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'])
 assert text==(R/name).read_text()
checks['seven_source_inverse']=True
ol=rd(P/'overlay-manifest.json');assert len(ol['reference'])==73 and len(ol['candidate'])==75
assert all(sha(e['source'])==e['sha256'] for arm in ['reference','candidate'] for e in ol[arm]);checks['all_overlay_inputs']=True
b=rd(Q/'budget.json')
a={'options_and_copy_intent':6*4*2*6*17+2*17+6*2+4,'backend_owned_policy':2*15+4+1,'private_spare_copy_and_failure':8*(61+41+2*47),'precision_and_factory_dispatch':5*4*2*4+4*9+6*8+1,'Parametric factorization backends':4*6+1,'Float64 factorization backend stability':4,'Dimension-changing refactorization resizes solve scratch':2*2,'Owned snapshots survive backend reuse and solve aliases':2*7+4+1,'Triangular identity reset uses current BigFloat precision without changing copies':3*4}
main={'_factorize_basis':2*3+1,'_basis_factorization':8*4+20*3+4+6*3,'UMFPACKBackend':2,'refactorize':8*(7+3+2+3),'copy_basis_factorization':8*3,'replace_column':8*3,'forward_solve':8*(19+3)+40+4+6,'transpose_solve':8*19+40+4+6,'sparse_solve_view':2,'raw_lu':1}
nei={'PFIFactorization':4+1+2+2,'ForrestTomlinFactorization':1,'SuhlSuhlFactorization':1,'BartelsGolubFactorization':1,'_factorize_basis':2+4,'refactorize':1+2+3,'_refactorize_backend':2*3,'copy_basis_factorization':3,'replace_column':3,'forward_solve':4+1+2,'transpose_solve':4+2,'hypersparse_forward_solve':2*4,'hypersparse_transpose_solve':2,'sparse_solve_view':2*2+4+1,'UMFPACKBackend':1,'raw_lu':1}
assert a==b['test_groups'] and sum(a.values())==6858
assert main==b['main'] and nei==b['neighbors'] and sum(main.values())+sum(nei.values())==792
assert 8*19*2+10*2==324 and 8*2*2==32;checks['independently_derived_counts']=True
ins=rd(Q/'inputs.json');old=Q.parent/'NATIVE-ACCURACY-PREPARATION'
assert ins['fixtures']==rd(old/'inputs.json')['fixtures']
assert (Q/'inputs.toml').read_bytes()==(old/'inputs.toml').read_bytes()
assert tomllib.loads((Q/'inputs.toml').read_text())['fixtures']==ins['fixtures']
schedule=[]
for f in ins['fixtures']:
 for r in range(1,12):
  for arm in (('C','P') if r%2 else ('P','C')):schedule.append(dict(id=len(schedule)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
assert schedule==ins['schedule'] and len(schedule)==88
assert 22*sum(f['matrix']['n'] for f in ins['fixtures'])*48*8==2162688
for name,vals in rd(Q/'saved-C.json').items():
 assert len(vals)==11
 for z in vals:assert sha(z['path'])==z['sha256'] and z['outputs']==tomllib.loads(Path(z['path']).read_text())['outputs']
checks['inputs_schedule_saved_C_bindings']=True
assert (Q/'supervisor.py').read_bytes()==(old/'supervisor.py').read_bytes()
g=(old/'guard.py').read_text().replace("if record['reason'] == 'exit0' and pressure", "if record['reason'] == f'exit{args.expected_exit}' and pressure").replace("return 0 if record['reason'] == 'exit0' and record['pins_unchanged'] else 1", "return 0 if record['reason'] == f'exit{args.expected_exit}' and record['pins_unchanged'] else 1").replace("execute.add_argument('--seconds'", "execute.add_argument('--expected-exit', type=int, choices=(0,1), required=True)\n    execute.add_argument('--seconds'")
assert g==(Q/'guard.py').read_text();checks['exact_guard_delta_and_supervisor_copy']=True
for name in ['entry.json','prepare.json']:assert all(sha(n)==h for n,h in rd(Q/name)['sha256'].items())
checks['entry_and_prepare_bindings']=True
# This directly checks source, not a Julia query/parser/import.
testsource=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src')
assert not any('push_testset' in p.read_text() or 'pop_testset' in p.read_text() for p in testsource.glob('*.jl'))
assert 'macro with_testset' in (testsource/'Test.jl').read_text()
driver=(Q/'test-driver.jl').read_text();assert 'Test.push_testset(root)' in driver and 'Test.pop_testset()' in driver
checks['blocking_R1_confirmed_pinned_Test_API']=True
# Pure validation: review must bind exact membership and scope.
required=list(pins['sha256'])+[str(Q/'preparation-pins.json')]
review=dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(Q/'preparation-pins.json'),sha256={**pins['sha256'],str(Q/'preparation-pins.json'):sha(Q/'preparation-pins.json')})
verify_review(review,Q/'preparation-pins.json',required,'offline preparation')
for key,value in [('scope','exact-stage admission'),('accepted',False),('findings',['R1']),('pins_sha256','bad'),('sha256',{})]:
 v=copy.deepcopy(review);v[key]=value;refuses('review '+key,lambda v=v:verify_review(v,Q/'preparation-pins.json',required,'offline preparation'))
# Synthetic GREEN is a schema exercise, not execution of any actual selected test.
groups=[dict(name=n,**{'pass':c,'fail':0,'error':0,'broken':0,'children':[],'failures':[]}) for n,c in a.items()]
total={k:main.get(k,0)+nei.get(k,0) for k in set(main)|set(nei)}
events=[dict(call=k,number=i,exception='') for k,c in total.items() for i in range(1,c+1)]
empty=dict(matrix=dict(n=0,colptr=[1],rowval=[],nzval=[]),rhs=[],output=[],transposed=False)
one=dict(matrix=dict(n=1,colptr=[1,2],rowval=[1],nzval=[token(1)]),rhs=[token(1)],output=[token(1)],transposed=False)
green=dict(complete=True,fatal='',threads=1,blas_threads=1,main_counts=main,counts=total,events=events,observation_limit=2048,equations=[empty]*32+[one]*292,tests=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0,'children':groups}))
assert test_results(green,'green')['assertions']==6858
for key,value in [('complete',False),('equations',green['equations'][:-1]),('events',events[:-1]),('main_counts',{}),('counts',{})]:
 v=copy.deepcopy(green);v[key]=value;refuses('GREEN '+key,lambda v=v:test_results(v,'green'))
v=copy.deepcopy(green);v['tests']['children'][0]['pass']-=1;refuses('GREEN assertion deficit',lambda:test_results(v,'green'))
# Synthetic cost: identity systems only; never replay historical numerical inputs.
fixtures=[dict(name=f['name'],matrix=dict(n=f['matrix']['n'],colptr=list(range(1,f['matrix']['n']+2)),rowval=list(range(1,f['matrix']['n']+1)),nzval=[token(1)]*f['matrix']['n']),rhs={k:[token(1)]*f['matrix']['n'] for k in ['a','dse','unit']}) for f in ins['fixtures']]
base=[token(0)]*20;base[3]=token(.1)
met=dict(seconds=1.,bytes=0,events=0,gctime=0.,compile_time=0.,recompile_time=0.)
windows=[];saved={}
for f in fixtures:saved[f['name']]=[dict(outputs=[[token(1)]*f['matrix']['n'] for k in range(48)],sha256='synthetic') for _ in range(11)]
for s in schedule:
 n=next(f['matrix']['n'] for f in fixtures if f['name']==s['fixture']);ctrl=base.copy();ctrl[3]=token(1 if s['arm']=='P' else .1);info=[token(0)]*90;info[18]=token(1)
 w=dict(schedule=s,no_spare=True,fresh=True,reused=True,owners=['a','b','c','a','b','c'],policy='_NATIVE_PIVOT_ONE' if s['arm']=='P' else '_NATIVE_PIVOT_DEFAULT',control=ctrl,spare_control=ctrl,Wi=n,W=n,info=info,outputs=[[token(1)]*n for _ in range(48)],solve_info=[[token(0)]*4 for _ in range(48)],**{r:met.copy() for r in ['construction','refactor_fresh','refactor_spare','solve','total']})
 if s['round']==11:w['factor']=dict(m=n,n=n,nzd=n,lnz=n,unz=n,graph_bytes=1,spare_W=n,spare_Wi=n)
 windows.append(w)
raw=dict(complete=True,fatal='',inputs_unchanged=True,threads=1,blas_threads=1,windows=88,counts=dict(construction=88,refactor=176,forward=2816,transpose=1408),output_payload_bytes=2162688,info_payload_bytes=135168,diagnostic_graph_bytes=2297856,default_control=base)
oldrd=oracle.rd
def synthetic_rd(path):
 if Path(path)==Q/'inputs.json':return dict(fixtures=fixtures,schedule=schedule)
 if Path(path)==Q/'saved-C.json':return saved
 return oldrd(path)
oracle.rd=synthetic_rd
try:
 result=cost_results(raw,windows);assert result['accuracy']=={'C':True,'P':True} and not result['unexplained_C_mismatch']
 for name,index,key,value in [('compilation',6,'total',dict(met,compile_time=1.)),('control',1,'control',base),('missing outputs',1,'outputs',[]),('lifecycle',0,'fresh',False)]:
  v=copy.deepcopy(windows);v[index][key]=value;refuses('cost '+name,lambda v=v:cost_results(raw,v))
 v=copy.deepcopy(windows);v[1]['outputs'][0][0]=token(2);refuses('cost P residual',lambda:cost_results(raw,v))
 v=copy.deepcopy(windows);v[0]['outputs'][0][0]=token(2);result=cost_results(raw,v)
 assert not result['accuracy']['C'] and result['accuracy']['P'] and result['unexplained_C_mismatch']
finally:oracle.rd=oldrd
checks['synthetic_gates_and_failure_preservation']=True
checks['no_stage_or_run']=not (Q/'runs').exists() and not (R/'.superpowers/native-pivot-qualification').exists()
report=dict(checks=checks,refusals=refusals,assertions=6858,main_calls=722,neighbor_calls=70,equations=324,nonempty_equations=292,cost_windows=88,fresh_native_source=176,private_lu_source=88,cost_solves=4224,numeric_payload_bytes=2297856,blocking_findings=['R1'],review_accepted=False,scope='Offline source/hash/synthetic verification only; no Julia',sha256={str(p):sha(p) for p in [Path(__file__),Q/'preparation-pins.json',Q/'continue.py',Q/'continuation-text.md',Q/'closure.py',Q/'publication.py']})
with (Q/'reviewer-check.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),all_checks_true=all(checks.values()),synthetic_refusals=len(refusals),blocking_findings=['R1'])))
