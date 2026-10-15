"""Independent offline review checks. No Julia, stage, launcher, or auditor execution."""
from pathlib import Path
import ast,copy,hashlib,json,sys,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX';P=D.parent/'NATIVE-PIVOT-PREPARATION'
sys.dont_write_bytecode=True
sys.path.insert(0,str(D))
import control,oracle
checks={};fresh={};bytes_read=0

def rd(p):return json.loads(Path(p).read_text())
def digest(p):
 global bytes_read
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);bytes_read+=len(b)
 return h.hexdigest()
def check(n,v):checks[n]=bool(v)
def rejects(f):
 try:f()
 except Exception:return True
 return False
pins=D/'preparation-pins.json';expected=rd(pins)['sha256'];required=rd(D/'required-paths.json')['paths']
for n in expected:fresh[n]=digest(n)
check('881_fresh_hashes',len(fresh)==881 and fresh==expected)
check('exact_required_membership',len(required)==len(set(required))==881 and set(required)==set(expected))
runtime=rd(Q/'runtime-pins.json')['sha256'];check('679_runtime_bindings',len(runtime)==679 and all(fresh.get(k)==v for k,v in runtime.items()))
source=rd(D/'source-check.json');check('30_source_check_bindings',len(source['sha256'])==30 and all(fresh.get(k)==v for k,v in source['sha256'].items()))
check('15_source_checks',len(source['checks'])==15 and all(source['checks'].values()))
for n,src in rd(D/'source-map.json')['byte_identical'].items():check('identical_'+n,(D/n).read_bytes()==Path(src).read_bytes())
m=rd(P/'overlay-manifest.json');check('candidate75_reference73',len(m['candidate'])==75 and len(m['reference'])==73 and all(fresh[e['source']]==e['sha256'] for a in ['candidate','reference'] for e in m[a]))
s=(D/'test-driver.jl').read_text();old=(F/'test-driver-fixed.jl').read_text()
start=s.index('        raw["regression_counts_before"]');end=s.index('        Test.@with_testset root begin',start)
r=s[:start]+s[end:]
r=r.replace('include(joinpath(@__DIR__,"regression-reviewed.jl"))\n','').replace('\n    regression=RecordedTests.Capture("regression")\n    helper_calls=Ref(0)','').replace('if phase=="green2"','if phase=="red"\n            include(joinpath(@__DIR__,"..","NATIVE-PIVOT-QUALIFICATION","red-contract.jl"))\n        elseif phase=="green"').replace('\n        raw["regression_tests"]=RecordedTests.dictionary(regression)\n        raw["regression_helper_calls"]=helper_calls[]','').replace(' && failed(regression)==0','')
check('whole_driver_exact_inverse',r==old)
check('top_level_module_include',s.index('include(joinpath(@__DIR__,"regression-reviewed.jl"))')<s.index('function main()'))
budget=rd(D/'budget.json');check('original_budget',sum(budget['test_groups'].values())==6858 and len(budget['test_groups'])==9 and sum(budget['main'].values())+sum(budget['neighbors'].values())==792)
check('regression_assertion_derivation',1+12*9+4*2+2==119)
check('regression_helper_derivation',12+4==16)
files,groups=control.predecessor('green2');check('prerequisites_actual_schema_and_bindings',len(groups)==212 and all(str(p) in fresh for p in files))
control.validate_environment();check('fresh_environment',True)
h=control.full_host(groups);check('fresh_host_refs_boot_groups_sessions',not h['matches'] and len(h['groups'])==212 and h['head']==control.HEAD and h['master']==control.MASTER and h['boot_id']==rd(D/'host.json')['boot_id'])
check('tracked_and_index_clean',not subprocess.check_output(['git','diff','--name-only'],cwd=R) and not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R))
cfg=control.config('green2');check('config_preview',cfg==rd(D/'config-preview.json'))
check('no_stage_run_reservation',not Path(cfg['stage']).exists() and not (D/'runs').exists())
check('inclusive60_inner52',cfg['seconds']==60 and '--seconds' in control.guard_command(cfg,D/'hypothetical-pins.json',100.) and control.guard_command(cfg,D/'hypothetical-pins.json',100.)[6:10]==['--seconds','52','--deadline','152.0'])
for phase in ['red','green','cost','../green2','GREEN2',None]:check('reject_phase_'+str(phase),rejects(lambda:control.config(phase)))
for red,green in [({},{}),({'phase':'red','all_passed':False},{'phase':'green','all_passed':False}),({'phase':'red','all_passed':True},{'phase':'green','all_passed':True}),({'phase':'red','all_passed':1},{'phase':'green','all_passed':False})]:check('reject_prereq_'+str(len(checks)),rejects(lambda:control.validate_prerequisites(red,green)))
good_review=dict(accepted=True,findings=[],scope='synthetic',phase='green2',pins_sha256=digest(pins),sha256={str(pins):digest(pins)})
control.verify_review(good_review,pins,[str(pins)],'synthetic','green2')
for k in good_review:
 bad=copy.deepcopy(good_review);del bad[k];check('reject_missing_review_'+k,rejects(lambda:control.verify_review(bad,pins,[str(pins)],'synthetic','green2')))
for k,v in [('accepted',1),('scope','other'),('phase','green'),('findings',['unresolved']),('pins_sha256','0'*64),('sha256',{str(pins):'0'*64})]:
 bad=copy.deepcopy(good_review);bad[k]=v;check('reject_changed_review_'+k,rejects(lambda:control.verify_review(bad,pins,[str(pins)],'synthetic','green2')))
root={'name':'regression','pass':0,'fail':0,'error':0,'broken':0,'failures':[],'children':[{'name':'Dense diagnostic tokens preserve sparse inputs','pass':119,'fail':0,'error':0,'broken':0,'failures':[],'children':[]}]}
good=dict(phase='green2',regression_tests=root,regression_helper_calls=16,regression_counts_before={},regression_counts_after={})
check('synthetic_regression_accept',oracle.regression_results(good)['assertions']==119)
for k in good:
 bad=copy.deepcopy(good);del bad[k];check('reject_missing_regression_'+k,rejects(lambda:oracle.regression_results(bad)))
for level in ['root','child']:
 for k in root:
  bad=copy.deepcopy(good);obj=bad['regression_tests'] if level=='root' else bad['regression_tests']['children'][0];del obj[k]
  check('reject_missing_'+level+'_'+k,rejects(lambda:oracle.regression_results(bad)))
for k,v in [('pass',118),('pass',120),('fail',1),('error',1),('broken',1),('failures',['hidden']),('children',[{}]),('name','wrong')]:
 bad=copy.deepcopy(good);bad['regression_tests']['children'][0][k]=v;check('reject_child_'+k+'_'+str(v),rejects(lambda:oracle.regression_results(bad)))
for k,v in [('regression_helper_calls',15),('regression_helper_calls',17),('regression_counts_before',{'forward_solve':1}),('regression_counts_after',{'forward_solve':1}),('phase','green')]:
 bad=copy.deepcopy(good);bad[k]=v;check('reject_regression_'+k+'_'+str(v),rejects(lambda:oracle.regression_results(bad)))
# Entire oracle receives exclusively fabricated data; never old numerical raw.
groups_data=[dict(name=n,**{'pass':count,'fail':0,'error':0,'broken':0,'failures':[],'children':[]}) for n,count in budget['test_groups'].items()]
total={k:budget['main'].get(k,0)+budget['neighbors'].get(k,0) for k in set(budget['main'])|set(budget['neighbors'])}
raw=copy.deepcopy(good);raw.update(complete=True,fatal='',threads=1,blas_threads=1,tests=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0,'failures':[],'children':groups_data}),main_counts=budget['main'],counts=total,observation_limit=2048,events=[dict(call=k,number=i,exception='') for k,n in total.items() for i in range(1,n+1)],equations=[dict(matrix=dict(n=1,colptr=[1,2],rowval=[1],nzval=['3ff0000000000000']),rhs=['3ff0000000000000'],output=['3ff0000000000000'],transposed=False) for _ in range(324)])
check('fabricated_full_schema_accept',oracle.test_results(raw,'green2')['assertions']==6858)
for k in raw:
 bad=copy.deepcopy(raw);del bad[k];check('reject_missing_full_'+k,rejects(lambda:oracle.test_results(bad,'green2')))
for label,mutation in [('assertions',lambda z:z['tests']['children'][0].update({'pass':4945})),('group_order',lambda z:z['tests']['children'].reverse()),('entries',lambda z:z['events'].pop()),('equations',lambda z:z['equations'].pop()),('residual',lambda z:z['equations'][0].update(output=['4000000000000000'])),('threads',lambda z:z.update(threads=2)),('fatal',lambda z:z.update(fatal='failure')),('incomplete',lambda z:z.update(complete=False))]:
 bad=copy.deepcopy(raw);mutation(bad);check('reject_full_'+label,rejects(lambda:oracle.test_results(bad,'green2')))
check('python_files_ast_parse',all(ast.parse(p.read_text()) for p in D.glob('*.py')))
# Verify absence of all prohibited effects after pure checks.
check('no_stage_run_after_checks',not Path(cfg['stage']).exists() and not (D/'runs').exists())
result=dict(all_passed=all(checks.values()),checks=checks,pins_sha256=digest(pins),fresh_file_count=len(fresh),fresh_bytes=bytes_read,sha256=fresh,host=h,scope='Pure offline reviewer source/hash/schema checks; fabricated oracle data is not numerical qualification')
with (D/'reviewer-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[n for n,v in checks.items() if not v],fresh_files=len(fresh),bytes_read=bytes_read)))
if not result['all_passed']:raise SystemExit(1)
