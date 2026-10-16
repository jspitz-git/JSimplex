"""New pure-Python acceptance/refusal tests. No Julia/launcher/guard execution."""
from control import *
from oracle import test_results,timeout_only
from copy import deepcopy
import tempfile
checks={}
def check(n,v):
 require(v,n);checks[n]=True
def rejects(n,fn):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError):checks[n]=True;return
 raise RuntimeError('Did not refuse '+n)
e=rd(D/'expected-tests.json');loaded=rd(D/'loaded-paths.json')
def node(name,count):return dict(name=name,**{'pass':count,'fail':0,'error':0,'broken':0,'failures':[],'children':[]})
root=node('root',0);root['children']=[node(n,c) for n,c in e['groups']];pub=root['children'][4];pub['pass']=0;pub['children']=[node(n,c) for n,c in e['public_children']]
raw=dict(complete=True,fatal='',threads=1,blas_threads=1,loaded=loaded,tests=root)
check('valid_exact6956',test_results(raw,e,loaded)['assertions']==6956)
mutations=[('missing_group',lambda z:z['tests']['children'].pop()),('duplicate_group',lambda z:z['tests']['children'].append(deepcopy(z['tests']['children'][0]))),('wrong_public_name',lambda z:z['tests']['children'][4]['children'][0].update(name='other')),('public_collapsed_same_total',lambda z:z['tests']['children'][4].update(children=[],**{'pass':48})),('child_fail',lambda z:z['tests']['children'][4]['children'][0].update(fail=1)),('child_error',lambda z:z['tests']['children'][0].update(error=1)),('child_broken',lambda z:z['tests']['children'][1].update(broken=1)),('boolean_count',lambda z:z['tests']['children'][1].update(**{'pass':True})),('extra_nested',lambda z:z['tests']['children'][0]['children'].append(node('empty',0))),('not_complete',lambda z:z.update(complete=False)),('fatal',lambda z:z.update(fatal='bad')),('threads',lambda z:z.update(threads=2)),('wrong_source',lambda z:z['loaded'].update(JSimplex='/other/src/JSimplex.jl'))]
for n,f in mutations:
 z=deepcopy(raw);f(z);rejects(n,lambda:test_results(z,e,loaded))
p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False);log='BEGIN native_pivot_policy_tests.jl\n'
check('timeout_positive',timeout_only(p,sup,None,log,295,300))
for n,pp,ss,rr,ll,elapsed in [('memory',dict(p,reason='memory_guard'),sup,None,log,295),('source_drift',dict(p,pins_unchanged=False),sup,None,log,295),('launch_error',dict(p,error='launch'),sup,None,log,295),('normal_exit',dict(p,returncode=0),sup,None,log,295),('hard_timeout',p,dict(sup,hard_timeout=True),None,log,295),('cleanup_error',p,dict(sup,cleanup_error='pending'),None,log,295),('test_fail_log',p,sup,None,log+'TEST FAILURE:',295),('broken_log',p,sup,None,log+'BROKEN TEST:',295),('error_log',p,sup,None,log+'ERROR:',295),('fatal_raw',p,sup,dict(fatal='bad'),log,295),('failed_raw',p,sup,dict(tests=dict(fail=1)),log,295),('raw_complete',p,sup,raw,log,295),('empty_log_unknown',p,sup,None,'',295),('inclusive_overrun',p,sup,None,log,301),('nonfinite_elapsed',p,sup,None,log,float('nan'))]:
 check('timeout_refuses_'+n,not timeout_only(pp,ss,rr,ll,elapsed,300))
with tempfile.TemporaryDirectory(prefix='native-pivot-offline-review-') as td:
 f=Path(td)/'pins.json';f.write_text('{}');required=[str(f)];v=dict(accepted=True,findings=[],scope='actual-master exact-stage admission',phase='master300',pins_sha256=sha(f),sha256={str(f):sha(f)})
 verify_review(v,f,required,v['scope'],'master300');checks['valid_exact_review']=True
 for n,changes in [('rejected',dict(accepted=False)),('wrongscope',dict(scope='production commit readiness')),('wrongphase',dict(phase='master600')),('missingbinding',dict(sha256={})),('wrongmanifest',dict(pins_sha256='0'*64)),('finding',dict(findings=['unresolved']))]:rejects('review_'+n,lambda changes=changes:verify_review(dict(v,**changes),f,required,'actual-master exact-stage admission','master300'))
validate_environment();validate_production(False);checks['exact_local_commit_and_untracked_environment']=True
rejects('actual_master_not_yet_integrated',lambda:validate_production(True))
for phase,seconds in [('master300',300),('master600',600)]:
 c=config(phase);check(phase+'_deadline',c['seconds']==seconds and str(seconds-8) in guard_command(c,Path('/tmp/pins'),0))
check('no_run_or_reservation',(not (D/'runs').exists()))
save(D/'offline-tests.json',dict(all_passed=True,checks=checks,scope='Pure Python fixtures and read-only production gates; no launcher, signals, Julia or numerical execution',sha256={str(p):sha(p) for p in [Path(__file__),D/'oracle.py',D/'control.py',D/'expected-tests.json',D/'production-commit.json']}))
print(len(checks),'offline acceptance/refusal checks PASS')
