"""Fresh offline preparation review. No Julia or old audit/checker execution."""
from pathlib import Path
import hashlib,json,sys,subprocess,copy
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');E=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN')
sys.path.insert(0,str(D));import control as c
from oracle import test_results,timeout_only
checks={};cache={}
def ck(name,value):checks[name]=bool(value)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def bindings(v,key='sha256'):return all(sha(p)==h for p,h in v[key].items())
def rejected(f):
 try:f();return False
 except (ValueError,RuntimeError,KeyError,FileNotFoundError):return True
m=rd(D/'preparation-pins.json');required=rd(D/'required-paths.json')['paths'];old=rd(O/'preparation-pins.json')
ck('exact_1942_manifest_members',len(m['sha256'])==1942 and len(required)==len(set(required))==1942 and set(required)==set(m['sha256']))
ck('all1942_hashes',bindings(m));ck('all1870_old_inputs_preserved',len(old['sha256'])==1870 and all(m['sha256'].get(p)==h for p,h in old['sha256'].items()))
v=rd(O/'review.json');ck('original_review_exact',v['accepted'] is True and v['findings']==[] and v['scope']=='BG export workspace driver preparation' and v['pins_sha256']==sha(O/'preparation-pins.json') and set(v['sha256'])==set(old['sha256'])|{str(O/'preparation-pins.json')} and bindings(v) and bindings(v,'evidence_sha256'))
inv=rd(D/'inverse.json');a=Path(inv['original']);b=Path(inv['amended']);before=a.read_text();after=b.read_text()
ck('only_one_empty_sum_identity',before.count(inv['before'])==1 and after.count(inv['after'])==1 and after.replace(inv['after'],inv['before'])==before)
ck('unchanged_test_predicates',before.count('@test')==after.count('@test') and after.count('init=0')==1)
ck('inverse_hashes',sha(a)==inv['original_sha256'] and sha(b)==inv['amended_sha256'])
fixture=(b.parent/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve()
ck('canonical_fixture_pinned',fixture==(a.parent/'../../direct-lu-policy-adapters/reproduce/fixtures.jl').resolve() and str(fixture) in m['sha256'])
for n in inv['copied_controls']+['baseline.json','stages.json','environment.json','runtime-inputs-complete.json','loaded-paths.json','expected-tests.json','expected-tests.toml']:
 ck('byteexact_'+n,(D/n).read_bytes()==(O/n).read_bytes())
driver=(O/'driver.jl').read_text()
for x,y in inv['driver_replacements']:driver=driver.replace(x,y)
ck('driver_exact_replacements',(D/'driver.jl').read_text()==driver)
expected=rd(D/'expected-tests.json')['green'];ck('unchanged_7935_eleven_groups',expected['assertions']==sum(g[1] for g in expected['groups'])==7935 and len(expected['groups'])==11 and all(g[2:]==[0,0,0] for g in expected['groups']))
for phase in ['green300','red300','green600','red600','cost1-300','green2-301']:
 ck('refuse_'+phase,rejected(lambda:c.config(phase)))
for phase,seconds in [('green2-300',300),('green2-600',600)]:
 cfg=c.config(phase);ck('bounded_exact_command_'+phase,cfg['mode']=='green' and cfg['seconds']==seconds and cfg['expected_exit']==0 and cfg['stage']==rd(O/'stages.json')['green']['path'] and cfg['command']==['/bin/bash',c.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),cfg['output'],cfg['stage'],phase] and c.guard_command(cfg,'pins',10)[7:11]==[str(seconds-8),'--deadline',str(10+seconds-8),'--expected-exit'])
ck('inherited_lexical_source_paths',c.validate_sources.__globals__['D']==O and c.validate_environment.__globals__['D']==O and c.loaded_for.__globals__['D']==O and c.old.preparation.__globals__['D']==O)
for phase,scope in [('red300','BG export workspace RED result'),('green300','BG export workspace GREEN failed result')]:
 run=O/'runs'/phase;v=rd(run/'result-review.json');files={str(p) for p in run.rglob('*') if p.is_file() and p!=run/'result-review.json'}
 ck('predecessor_exact_'+phase,v['accepted'] is True and v['findings']==[] and v['phase']==phase and v['scope']==scope and set(v['sha256'])==files and bindings(v) and bindings(v,'evidence_sha256'))
 if phase=='green300':ck('original_failure_not_timeout',v['correctness_accepted'] is False and v['cost_predecessor_accepted'] is False and rd(run/'audit.json')['all_passed'] is False and rd(run/'audit.json')['pure_timeout'] is False and v['result']['pass']==7934 and v['result']['error']==1)
 else:ck('RED_expected_six',rd(run/'audit.json')['all_passed'] is True and rd(run/'audit.json')['pure_timeout'] is False)
ck('failed_GREEN_closure',rd(E/'closure.json')['all_passed'] is True and bindings(rd(E/'closure.json')))
source=rd(D/'source-check.json');ck('author31_results_bound',source['all_passed'] is True and len(source['checks'])==31 and all(source['checks'].values()) and bindings(source))
ck('all_new_initial_files_in_manifest',all(str(p) in m['sha256'] or p.name=='preparation-pins.json' for p in D.iterdir() if p.is_file() and p.name!='independent-review-check.py'))
cfg=c.config('green2-300');loaded=c.loaded_for(cfg)
raw=dict(phase='green2-300',complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0},failures=[],children=[dict(name=g[0],**dict(zip(('pass','fail','error','broken'),g[1:])),failures=[],children=[]) for g in expected['groups']]))
ck('synthetic_exact_count',test_results(raw,expected,loaded,'green2-300')['assertions']==7935)
for name,mutate in [('error',lambda x:x['tests']['children'][3].update({'pass':55,'error':1,'failures':['empty']})),('compensating_groups',lambda x:(x['tests']['children'][0].update({'pass':41}),x['tests']['children'][1].update({'pass':7}))),('missing',lambda x:x['tests']['children'].pop()),('wrong_source',lambda x:x['loaded'].update({'JSimplex':'wrong'})),('oldphase',lambda x:x.update(phase='green300')),('incomplete',lambda x:x.update(complete=False))]:
 test=copy.deepcopy(raw);mutate(test);ck('synthetic_reject_'+name,rejected(lambda:test_results(test,expected,loaded,'green2-300')))
cs=(D/'control.py').read_text();ck('preparation_review_exact_scope',"'BG export workspace GREEN2 harness preparation'" in cs and "list(j['sha256'])+[str(m)]" in cs)
ck('timeout_requires_new_review_and_pins',"if phase=='green2-600':" in cs and "result_review('green2-300','pure timeout result','timeout-review.json')" in cs and "a['pure_timeout'] is True" in cs and 'guard.pins_match(s)' in cs)
ck('no_current_run_or_reservation',not (D/'runs').exists())
# Host reads only: all250 historic groups and sessions, no launched workload.
h=c.full_host();h['memory']=c.guard.memory();ck('fresh_host250_scoped',len(h['groups'])==250 and c.host_safe(h));ck('memory_threshold',not c.guard.pressure(h['memory']))
ck('fixed_refs',h['head']=='3c6e5cc7aec51e022da2e1834e8c11779f84b314' and h['master']=='26e2291745999f485a74f643298ca997d65c7205')
c.validate_environment();ck('actual_nonlogin_environment',True)
ck('no_tracked_changes',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
result=dict(all_passed=all(checks.values()),checks=checks,host=h,checked_manifest_files=1942,hashes_read=len(cache),scope='Offline harness preparation only; no Julia, old checker/auditor, seal, reservation, launch or numerical/performance acceptance')
with (D/'independent-review-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[n for n,v in checks.items() if not v],manifest_files=1942,host_groups=len(h['groups']),unreadable_exe=len(h['unreadable_exe_pids']),unreadable_identity=len(h['unreadable_identity_pids']),memory=h['memory'])))
if not result['all_passed']:raise SystemExit(1)
