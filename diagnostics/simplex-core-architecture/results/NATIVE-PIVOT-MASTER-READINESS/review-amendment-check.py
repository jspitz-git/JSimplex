"""Independent new amendment verifier; no old checker, operational script, or Julia execution."""
from pathlib import Path
import json,hashlib,sys,os,copy,ast,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(D))
import control,oracle
checks={}
def sha(p):
 p=control.path(str(p));h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
m=D/'preparation-pins.json';pins=read(m)['sha256'];required=read(D/'required-paths.json')['paths']
ck('canonical4966',len(pins)==4966 and set(required)==set(pins) and len(required)==len(set(required)))
ck('required_self_bound',str(D/'required-paths.json') in pins)
for n,h in pins.items():ck('canonical:'+n,sha(n)==h)
mappings=read(D/'review-amendment-mappings.json'); mapping={(v['original'],v['sha256']):v['preserved'] for v in mappings}
ck('eight_original_mappings',len(mapping)==8)
for (n,h),before in mapping.items():ck('preserved:'+n,sha(before)==h)
initial=read(D/'review-initial.json');ck('initial_rejection_preserved',initial['accepted'] is False and len(initial['findings'])==1)
for n,h in initial['sha256'].items():ck('initial_evidence:'+n,sha(mapping.get((str(control.path(n)),h),n))==h)
old=read(D/'preparation-pins.json.before-review')['sha256'];ck('membership_only_extended',set(old)<=set(pins))
changed={n for n in old if pins[n]!=old[n]};ck('narrow_original_binding_changes',changed=={str(D/n) for n in ['oracle.py','control.py','audit.py','REPORT.md','required-paths.json']})
a=(D/'audit.py.before-review').read_text();b=(D/'audit.py').read_text();ck('audit_single_loaded_argument',b==a.replace("pure=timeout_only(p,sup,raw,log,inv['elapsed_seconds'],cfg['seconds'])","pure=timeout_only(p,sup,raw,log,inv['elapsed_seconds'],cfg['seconds'],rd(D/'loaded-paths.json'))"))
a=(D/'control.py.before-review').read_text();b=(D/'control.py').read_text();ck('control_single_normalization',b==a.replace("return list(j['sha256'])+[str(m),str(D/'review-final.json')]","return sorted({str(path(n)) for n in j['sha256']}|{str(m),str(D/'review-final.json')})"))
old_ast=ast.parse((D/'oracle.py.before-review').read_text());new_ast=ast.parse((D/'oracle.py').read_text());ck('success_oracle_unchanged',ast.dump(next(n for n in old_ast.body if isinstance(n,ast.FunctionDef) and n.name=='test_results'))==ast.dump(next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name=='test_results')))
loaded=read(D/'loaded-paths.json');node=dict(name='root',**{'pass':0,'fail':0,'error':0,'broken':0,'failures':[],'children':[]});raw=dict(complete=False,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=node);p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);s=dict(returncode=1,hard_timeout=False);log='BEGIN native_pivot_policy_tests.jl\n'
def eligible(v):return oracle.timeout_only(p,s,v,log,295,300,loaded)
ck('missing_raw_permitted',eligible(None));ck('wellformed_empty_partial_permitted',eligible(raw))
partial=copy.deepcopy(raw);child=copy.deepcopy(node);child.update(name='options_and_copy_intent',**{'pass':13});partial['tests']['children']=[child];ck('interrupted_counts_permitted',eligible(partial))
for n,v in [('empty_document',{}),('missing_tests',dict(complete=False,fatal='')),('invalid_complete',dict(complete='true',fatal='',tests={})),('invalid_tree',dict(complete=False,fatal='',tests={}))]:ck('original_finding_fixed:'+n,not eligible(v))
for field in raw:
 v=copy.deepcopy(raw);del v[field];ck('missing_field:'+field,not eligible(v))
for field,value in [('complete',0),('complete','false'),('complete',True),('threads',True),('blas_threads',True),('threads',1.0),('fatal','error'),('loaded',{}),('tests',None)]:
 v=copy.deepcopy(raw);v[field]=value;ck('malformed:'+field+repr(value),not eligible(v))
for field,value in [('name',None),('pass',-1),('pass',True),('fail',1),('error',1),('broken',1),('failures',['failure']),('children',None)]:
 v=copy.deepcopy(partial);v['tests']['children'][0][field]=value;ck('malformed_nested:'+field,not eligible(v))
for v in [[],False,'',0]:ck('malformed_raw_type:'+repr(v),not eligible(v))
for text in ['TEST FAILURE:','BROKEN TEST:','ERROR:','OutOfMemoryError']:ck('log_veto:'+text,not oracle.timeout_only(p,s,raw,log+text,295,300,loaded))
ck('partial_requires_expected_loaded',not oracle.timeout_only(p,s,raw,log,295,300))
f=next(n for n in ast.parse((D/'control.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='preparation');expr=compile(ast.Expression(f.body[-1].value),'independent return-only inspection','eval');cwd=Path.cwd();os.chdir('/tmp')
try:files=eval(expr,dict(j=dict(sha256=pins),m=m,D=D,path=control.path))
finally:os.chdir(cwd)
ck('runtime_seal_files_absolute',all(Path(n).is_absolute() for n in files));ck('runtime_seal_membership_exact',set(files)=={str(control.path(n)) for n in pins}|{str(m),str(D/'review-final.json')})
ck('historical_key_spelling_unchanged',any(not Path(n).is_absolute() for n in pins))
ck('author44pass',read(D/'review-amendment-tests.json')['all_passed'] is True and len(read(D/'review-amendment-tests.json')['checks'])==44)
ck('no_attempt_exists',not (D/'runs').exists())
control.validate_environment();control.validate_production(False);ck('production_unchanged_readonly',True)
host=control.full_host();host['remote']=control.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');host['reviewer_identity']=control.guard.process_identity(os.getpid());host['memory']=control.guard.memory()
ck('fresh220groups_sessions_noJulia',len(host['groups'])==220 and not host['matches']);ck('fresh_refs',host['head']==control.ENTRY and host['master']==control.BASE and control.BASE+'\trefs/heads/master' in host['remote'] and control.ENTRY+'\trefs/heads/codex/simplex-core-architecture' in host['remote']);ck('fresh_resources',not control.guard.pressure(host['memory']))
save(D/'review-amendment-host.json',host)
save(D/'review-amendment-checks.json',dict(all_passed=all(checks.values()),check_count=len(checks),checks=checks,findings=[],pins_sha256=sha(m),sha256={str(p):sha(p) for p in [Path(__file__),m,D/'review-amendment-host.json']},scope='Independent corrected readiness verification only'))
print(len(checks),'independent amendment checks PASS; exact canonical',len(pins),'bindings')
