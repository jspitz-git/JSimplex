"""Independent new offline review. No Julia, launch, seal, reservations or old checkers."""
from pathlib import Path
import json, hashlib, subprocess, sys, os, copy, time
D=Path(__file__).resolve().parent; R=D.parents[3]; Q=D.parent/'NATIVE-PIVOT-PRODUCTION-INTEGRATION-PREPARATION'
sys.path.insert(0,str(D))
import control, oracle
checks={}; findings=[]
def check(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def rejects(n,f):
 try:f()
 except Exception:check(n,True);return
 check(n,False)
m=D/'preparation-pins.json'; pins=read(m)['sha256']; required=read(D/'required-paths.json')['paths']
check('absolute_unique_required_membership',len(required)==len(set(required)) and set(required)==set(pins) and all(Path(n).is_absolute() for n in pins))
check('required_list_self_bound',str(D/'required-paths.json') in pins)
for n,h in pins.items():check('pin:'+n,sha(n)==h)
for n,v in read(D/'copied-sources.json').items():check('copied:'+n,sha(n)==sha(v['source'])==v['sha256'])
for n,v in read(D/'runtime-inputs.json')['inventory'].items():check('resolved:'+n,str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'])
c=read(D/'production-commit.json'); w=Path(c['worktree']); tree=read(D/'production-tree.json')
check('exact_commit',git('rev-parse','HEAD',cwd=w)==c['commit']=='26e2291745999f485a74f643298ca997d65c7205')
check('exact_parent',git('rev-parse','HEAD^',cwd=w)==c['base']==control.BASE)
check('exact_diff_names',git('diff-tree','--no-commit-id','--name-only','-r',c['commit'],cwd=w).splitlines()==c['names'])
entries={}
for line in subprocess.check_output(['git','ls-tree','-rz',c['commit']],cwd=w).split(b'\0'):
 if line:
  meta,name=line.split(b'\t',1);entries[name.decode()]=meta.decode().split()[2]
check('entire_git_tree',entries==tree['git_blobs'] and len(entries)==3533)
check('tracked_membership',set(git('ls-files',cwd=w).splitlines())==set(entries)==set(tree['sha256']))
for n,h in tree['sha256'].items():check('production:'+n,sha(w/n)==h)
manifest=read(Q/'payload-manifest.json')
for x in manifest['files']:
 n=x['destination'];check('payload:'+n,sha(w/n)==x['sha256']==sha(R/x['payload']) and entries[n]==c['blobs'][n])
check('ten_files',len(manifest['files'])==len(c['names'])==10)
control.validate_environment();control.validate_production(False);check('production_readonly_control',True)
rejects('actual_master_gate_refuses_before_ff',lambda:control.validate_production(True))
check('prior_review_accepted',read(Q/'review-final.json')['accepted'] is True and not read(Q/'review-final.json')['findings'])
check('no_attempt_seal_reservation',not (D/'runs').exists())
preview=read(D/'config-preview.json')
for phase,seconds in [('master300',300),('master600',600)]:
 cfg=control.config(phase);check('config:'+phase,cfg==preview[phase] and cfg['seconds']==seconds)
 cmd=control.guard_command(cfg,Path('/tmp/review-unused-pins'),1000.)
 check('inclusive_deadline:'+phase,cmd[cmd.index('--seconds')+1]==str(seconds-8) and float(cmd[cmd.index('--deadline')+1])==1000.+seconds-8)
expected=read(D/'expected-tests.json');loaded=read(D/'loaded-paths.json')
def node(name,n):return dict(name=name,**{'pass':n,'fail':0,'error':0,'broken':0,'failures':[],'children':[]})
root=node('root',0);root['children']=[node(n,v) for n,v in expected['groups']];pub=root['children'][4];pub['pass']=0;pub['children']=[node(n,v) for n,v in expected['public_children']]
raw=dict(complete=True,fatal='',threads=1,blas_threads=1,loaded=loaded,tests=root)
check('exact_tree6956',oracle.test_results(raw,expected,loaded)['assertions']==6956)
mutations={'missing_group':lambda z:z['tests']['children'].pop(),'public_wrong_name':lambda z:z['tests']['children'][4]['children'][0].update(name='pfi default'),'collapsed_public':lambda z:z['tests']['children'][4].update(children=[],**{'pass':48}),'missing_tests':lambda z:z.pop('tests'),'boolean_count':lambda z:z['tests']['children'][0].update(**{'pass':True}),'extra_zero_group':lambda z:z['tests']['children'].append(node('extra',0)),'wrong_loaded':lambda z:z.update(loaded={}), 'wrong_complete':lambda z:z.update(complete='true')}
for field in ['fail','error','broken']:
 mutations[field]=lambda z,k=field:z['tests']['children'][0].update(**{k:1})
for n,fn in mutations.items():
 z=copy.deepcopy(raw);fn(z);rejects('oracle_reject:'+n,lambda:oracle.test_results(z,expected,loaded))
p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);s=dict(returncode=1,hard_timeout=False);log='BEGIN native_pivot_policy_tests.jl\n'
check('missing_final_raw_timeout_allowed',oracle.timeout_only(p,s,None,log,295,300))
for n,pp,ss,rr,ll,elapsed in [('emptylog',p,s,None,'',295),('failed',p,s,None,log+'TEST FAILURE:',295),('error',p,s,None,log+'ERROR:',295),('broken',p,s,None,log+'BROKEN TEST:',295),('raw_complete',p,s,raw,log,295),('raw_fatal',p,s,dict(fatal='failed'),log,295),('resource',dict(p,reason='memory_guard'),s,None,log,295),('integrity',dict(p,pins_unchanged=False),s,None,log,295),('cleanup',p,dict(s,cleanup_error='x'),None,log,295),('hard',p,dict(s,hard_timeout=True),None,log,295),('overrun',p,s,None,log,301),('nan',p,s,None,log,float('nan'))]:check('timeout_refuses:'+n,not oracle.timeout_only(pp,ss,rr,ll,elapsed,300))
malformed={n:oracle.timeout_only(p,s,v,log,295,300) for n,v in [('empty_document',{}),('missing_tests',dict(complete=False,fatal='')),('invalid_complete',dict(complete='true',fatal='',tests={})),('invalid_tree',dict(complete=False,fatal='',tests={}))]}
if any(malformed.values()):findings.append(dict(priority=2,title='Reject malformed raw evidence before granting pure-timeout eligibility',file=str(D/'oracle.py'),start=35,end=39,detail='timeout_only accepts existing empty or schema-invalid raw documents as pure timeouts because missing complete/fatal/tests are defaulted and the test subtree is never schema-validated. Missing final raw is permitted by policy, but present malformed evidence is an unknown outcome and must not qualify a 600-second retry. Validate any present raw against the partial-driver schema before classifying; retain the explicit missing-file exception. Independent fixtures reproduce acceptance for empty TOML {}, missing tests, string complete and an empty tests mapping.'))
host=control.full_host();host['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');host['reviewer_identity']=control.guard.process_identity(os.getpid());host['memory']=control.guard.memory()
check('fresh_host_groups220',len(host['groups'])==220 and not host['matches'])
check('fresh_refs',host['head']==control.ENTRY and host['master']==control.BASE and control.BASE+'\trefs/heads/master' in host['remote'] and control.ENTRY+'\trefs/heads/codex/simplex-core-architecture' in host['remote'])
check('fresh_host_memory',not control.guard.pressure(host['memory']))
save(D/'review-host.json',host)
result=dict(all_checks_passed=all(checks.values()),accepted=not findings,check_count=len(checks),checks=checks,malformed_timeout_acceptance=malformed,findings=findings,sha256={str(p):sha(p) for p in [Path(__file__),m,D/'review-host.json']},scope='Independent new pure Python/read-only readiness review; no numerical execution')
save(D/'review-checks.json',result)
if findings:save(D/'review-initial.json',dict(accepted=False,findings=findings,scope='production commit readiness',pins_sha256=sha(m),sha256={**pins,str(m):sha(m)},evidence_sha256={str(D/'review-checks.json'):sha(D/'review-checks.json'),str(Path(__file__)):sha(__file__)}))
print(json.dumps(dict(checks=len(checks),findings=findings,malformed=malformed)))
