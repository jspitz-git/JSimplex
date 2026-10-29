from pathlib import Path
import json,hashlib,subprocess,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/klu-ftran/2026-10-29';MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b';BASE='cd939a1a94549c0242b8f6dc4b65927d06bfe6ce'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
need(git('rev-parse','HEAD')==BASE,'diagnostic base')
need(git('rev-parse','master')==git('rev-parse','origin/master')==MASTER,'unchanged master')
need(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'empty index and tracked working changes')
raw=tomllib.loads((D/'results-2.toml').read_text());a=json.loads((D/'analysis-2.json').read_text());pr=json.loads((D/'comparison-2/guard/process.json').read_text());post=json.loads((D/'comparison-2/postflight.json').read_text());old=json.loads((D/'comparison-1/guard/process.json').read_text())
need(raw['completed'] and a['accepted'] and len(a['checks'])==138 and len(raw['cases'])==12 and a['measured_calls']==58680,'all original results/count gates')
need('5022   5022' in (D/'comparison-2/guard/run.log').read_text(),'ordinary test5022')
need(pr['reason']=='exit0' and pr['returncode']==0 and pr['pins_unchanged'] and not post['conflicts'] and len(post['checked_groups'])==719,'successful run complete groups sessions')
need(old['reason']=='exit1' and old['returncode']==1 and old['pins_unchanged'] and 'ParseError' in (D/'comparison-1/guard/run.log').read_text() and not (D/'results-1.toml').exists(),'original loading failure preserved')
need('ACCEPTED' in (D/'REVIEW-RESULTS-FINAL.md').read_text(),'independent accepted results review')
# Exact report/review bindings supplied by fresh final reviewer before publication.
review=json.loads((D/'final-review-binding.json').read_text())
for n,h in review['files'].items():need(sha(D/n)==h,'final review seal '+n)
need(review['accepted'] is True,'final review seal accepted')
counts={};mapping={'candidate.jl':'candidate.jl.before-review','driver.jl':'driver.jl.before-review','PLAN.md':'PLAN.md.before-review'}
for manifest in ['source-pins.json','reviewed-source-pins.json','launch-pins.json','launch-pins-2.json']:
 inv=json.loads((D/manifest).read_text())['inventory'];counts[manifest]=len(inv)
 for k,v in inv.items():
  p=Path(k);p=D/mapping[p.name] if manifest=='source-pins.json' and p.parent==D and p.name in mapping else p
  need(sha(p)==v['sha256'],'immutable binding '+k)
need(counts=={'source-pins.json':43,'reviewed-source-pins.json':52,'launch-pins.json':58,'launch-pins-2.json':68},'all pin cardinalities')
need(sha(D/'REVIEW-FIX.md.before-tests')=='74764b465fa31cd2080d5078b778ca57a7f29d75da46ad056423a0701d4c2d7a','superseded review original fix binding')
files=sorted(p for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p))
closure={'all_checks':True,'scope':'fixed-base diagnostic only; production withheld','base':BASE,'master':MASTER,'ordinary_tests':5022,'offline_gates':138,'cases':12,'measured_calls':58680,'Julia_process_attempts':2,'completed_numerical_processes':1,'initial_loading_failure_preserved':True,'postflight_groups_and_sessions':719,'manifest_cardinalities':counts,'original43_mapping':mapping,'signed_zero_equivalence':False,'whole_solver_speedup':False,'result_review_sha256':sha(D/'REVIEW-RESULTS-FINAL.md'),'bindings':{str(p.relative_to(W)):sha(p)for p in files}}
(D/'CLOSURE.json').write_text(json.dumps(closure,indent=2)+'\n');files.append(D/'CLOSURE.json')
(D/'STAGED.json').write_text(json.dumps({'scope':'exact complete staged set; hashes exclude self only','files':{str(p.relative_to(W)):sha(p)for p in files}},indent=2)+'\n');files.append(D/'STAGED.json')
names=sorted(str(p.relative_to(W))for p in files)
need(all(n.startswith('diagnostics/klu-ftran/2026-10-29/')for n in names),'new diagnostics only')
git('add','--',*names);need(git('diff','--cached','--name-only').splitlines()==names,'exact staged complete set')
for n in names:need(hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=W)).hexdigest()==sha(W/n),'exact staged blob '+n)
verbatim=lambda n:'/vendor/' in n or n.endswith('/inputs.toml')
subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if not verbatim(n)]],cwd=W,check=True)
v=subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if verbatim(n)]],cwd=W,text=True,capture_output=True)
seal={'publication_pass':True,'exact_names':names,'blobs':{n:sha(W/n)for n in names},'verbatim_whitespace':{'returncode':v.returncode,'diagnostics':v.stdout+v.stderr}}
Path('/tmp/klu-ftran-20261029/publication-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'publication_pass':True,'exact_staged_files':len(names),'all_bindings_reconciled':counts,'authored_whitespace_pass':True}))
