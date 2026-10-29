from pathlib import Path
import json,hashlib,subprocess,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/klu-weight-btran/2026-10-29';BASE='5b9880a8f5ddd2e253300a9c23e531f45d3e31bf';MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=W,text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
need(git('rev-parse','HEAD')==BASE,'diagnostic baseline')
need(git('rev-parse','master')==git('rev-parse','origin/master')==MASTER,'unchanged master')
need(not git('diff','--name-only')and not git('diff','--cached','--name-only'),'no tracked edits/index')
a=json.loads((D/'diagnostic-analysis.json').read_text());r=tomllib.loads((D/'results-2.toml').read_text());p=json.loads((D/'comparison-2/guard/process.json').read_text());post=json.loads((D/'comparison-2/postflight.json').read_text());strict=json.loads((D/'strict-auditor-rejection.json').read_text())
need(a['diagnostic_accepted']is True and a['whole_experiment_accepted']is False,'diagnostic classification only')
need((a['tests_passed'],a['tests_failed'],a['complete_measured_kernel_calls'],a['rejected_whole_windows'],a['rejected_inclusive_windows'])==(13816,217,20160,90,54),'exact preserved outcomes')
need(len(a['checks'])==3574 and r['completed']is True and len(r['cases'])==12,'complete diagnostic records')
need(p['reason']=='exit1'and p['returncode']==1 and p['pins_unchanged']and not post['conflicts']and len(post['checked_groups'])==723,'failed numerical test normal exit/group closure')
need(strict['returncode']==1 and not (D/'results-1.toml').exists(),'strict rejection and first parse failure preserved')
need('ACCEPTED' in (D/'REVIEW-RESULTS.md').read_text(),'independent diagnostic review accepted')
review=json.loads((D/'review-result-bindings.json').read_text());need(review['accepted']is True,'review seal')
for n,h in review['files'].items():need(sha(D/n)==h,'final review binding '+n)
counts={}
for manifest in ['source-pins.json','launch-pins.json','launch-pins-2.json']:
 inv=json.loads((D/manifest).read_text())['inventory'];counts[manifest]=len(inv)
 for path,v in inv.items():need(sha(path)==v['sha256'],'unchanged immutable binding '+path)
need(counts=={'source-pins.json':119,'launch-pins.json':126,'launch-pins-2.json':134},'manifest cardinalities')
need(sha(D/'ftran.jl')==sha(W/'diagnostics/klu-ftran/2026-10-29/candidate-loadfix.jl'),'accepted source copy provenance')
files=sorted(p for p in D.rglob('*')if p.is_file()and '__pycache__'not in str(p))
closure=dict(diagnostic_classification_accepted=True,whole_experiment_accepted=False,production_integration=False,base=BASE,master=MASTER,Julia_process_attempts=2,numerical_runs_completed=1,numerical_exit=1,ordinary_tests_passed=13816,ordinary_tests_failed=217,strict_auditor_exit=1,diagnostic_checks=3574,complete_measured_kernel_calls=20160,excluded_runtime_whole_windows=90,excluded_runtime_inclusive_windows=54,manifest_cardinalities=counts,postflight_groups_and_sessions=723,scope='rejected full weight qualification, preserved kernel/setup diagnostic findings only',bindings={str(p.relative_to(W)):sha(p)for p in files})
(D/'CLOSURE.json').write_text(json.dumps(closure,indent=2)+'\n');files.append(D/'CLOSURE.json')
(D/'STAGED.json').write_text(json.dumps(dict(scope='exact complete staged set; self only excluded from listed hashes',files={str(p.relative_to(W)):sha(p)for p in files}),indent=2)+'\n');files.append(D/'STAGED.json');names=sorted(str(p.relative_to(W))for p in files)
need(all(n.startswith('diagnostics/klu-weight-btran/2026-10-29/')for n in names),'new diagnostic paths only')
git('add','--',*names);need(git('diff','--cached','--name-only').splitlines()==names,'exact complete staged names')
for n in names:need(hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=W)).hexdigest()==sha(W/n),'staged blob '+n)
verbatim=lambda n:'/vendor/'in n or n.endswith('/inputs.toml')
subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if not verbatim(n)]],cwd=W,check=True)
v=subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if verbatim(n)]],cwd=W,text=True,capture_output=True)
Path('/tmp/klu-weight-btran-20261029/publication-seal.json').write_text(json.dumps(dict(publication_pass=True,whole_experiment_accepted=False,exact_names=names,blobs={n:sha(W/n)for n in names},verbatim_whitespace=dict(returncode=v.returncode,diagnostics=v.stdout+v.stderr)),indent=2)+'\n')
print(json.dumps(dict(publication_pass=True,whole_experiment_accepted=False,exact_staged_files=len(names),authored_whitespace_pass=True)))
