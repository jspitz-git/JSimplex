from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/klu-shared-solves/2026-10-29';BASE='08dfda4b25bb1d014fd9d4c8781b1a83f46c8cd8';MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=W,text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
need(git('rev-parse','HEAD')==BASE,'base')
need(git('rev-parse','master')==git('rev-parse','origin/master')==MASTER,'master')
need(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked work/index unchanged')
a=json.loads((D/'all-unit-analysis.json').read_text());s=json.loads((D/'source-checks.json').read_text());r=json.loads((D/'review-final-bindings.json').read_text())
need(a['accepted'] and (a['unit_RHS_count'],a['all_unit_graphs'],a['small_DAG_checks'],a['actual_BFS_crosschecks'],a['old_selected_unit_crosschecks'])==(172170,9,1024,297,9),'new offline graph gates')
need(s['accepted'] and len(s['checks'])==42,'source gates')
need(r['accepted'],'independent review acceptance')
for name,h in r['files'].items():need(sha(D/name)==h,'final review binding '+name)
for name in ['source-bindings.json','source-bindings-addendum.json']:
 for path,h in json.loads((D/name).read_text())['files'].items():need(sha(path)==h,'source binding '+path)
for path,h in a['original_witness_bindings'].items():need(sha(path)==h,'immutable prior witness '+path)
for entry in json.loads((D/'upstream-provenance.json').read_text()):need(sha(D/entry['path'])==entry['sha256'],'upstream exact bytes')
need('ACCEPTED' in (D/'REVIEW.md').read_text(),'accepted review text')
# Initial analysis file bindings reconciled to explicitly preserved before-review copies if needed.
mapping=r.get('initial_analysis_mapping',{})
for name,h in json.loads((D/'analysis-bindings.json').read_text())['files'].items():need(sha(D/mapping.get(name,name))==h,'analysis binding '+name)
files=sorted(p for p in D.rglob('*')if p.is_file() and '__pycache__' not in str(p))
closure={'all_checks':True,'scope':'source/offline shared KLU graph consumer analysis only; no Julia or new solves','base':BASE,'master':MASTER,'source_gates':42,'all_unit_graphs':9,'unit_RHS_count':172170,'small_DAG_checks':1024,'actual_BFS_crosschecks':297,'old_selected_unit_crosschecks':9,'production_changes':False,'numerical_launch_admission':False,'initial_analysis_mapping':mapping,'bindings':{str(p.relative_to(W)):sha(p)for p in files}}
(D/'CLOSURE.json').write_text(json.dumps(closure,indent=2)+'\n');files.append(D/'CLOSURE.json')
(D/'STAGED.json').write_text(json.dumps({'scope':'exact complete staged set; self only excluded from listed hashes','files':{str(p.relative_to(W)):sha(p)for p in files}},indent=2)+'\n');files.append(D/'STAGED.json');names=sorted(str(p.relative_to(W))for p in files)
need(all(n.startswith('diagnostics/klu-shared-solves/2026-10-29/')for n in names),'only new diagnostics')
git('add','--',*names);need(git('diff','--cached','--name-only').splitlines()==names,'exact complete staged names')
for n in names:need(hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=W)).hexdigest()==sha(W/n),'staged blob '+n)
subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if '/upstream/' not in n]],cwd=W,check=True)
v=subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if '/upstream/' in n]],cwd=W,text=True,capture_output=True)
Path('/tmp/klu-shared-solves-20261029/publication-seal.json').write_text(json.dumps(dict(publication_pass=True,exact_names=names,blobs={n:sha(W/n)for n in names},verbatim_whitespace=dict(returncode=v.returncode,diagnostics=v.stdout+v.stderr)),indent=2)+'\n')
print(json.dumps(dict(publication_pass=True,exact_staged_files=len(names),authored_whitespace_pass=True)))
