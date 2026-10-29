from pathlib import Path
import json,hashlib,subprocess,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/klu-block-reach/2026-10-29'
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=W,text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
need(git('rev-parse','HEAD')=='04c211565976a47cb1e151629c9ed77f5db99618','baseline')
need(git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','master')
need(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'clean index/tracked changes')
need(digest(D/'REVIEW-RESULTS.md')=='9a70b3b7af3029069966f9e11a42575388d73857b012a410d915f4327e76fdeb','accepted result review')
need(digest(D/'REPORT.md')=='984095ce7853f52d1e7e2d929bb6994bdde6c361e1763ede2745c00d2586840b','reviewed report')
raw=tomllib.loads((D/'results-1.toml').read_text());a=json.loads((D/'analysis.json').read_text());fixed=json.loads((D/'fixed-base-analysis.json').read_text());proc=json.loads((D/'reach-1/guard/process.json').read_text());post=json.loads((D/'reach-1/postflight.json').read_text())
need(raw['completed'] and a['accepted'] and (a['verified_profiles'],a['verified_actual_RHS'])==(483,966),'whole graph verification')
need(fixed['accepted'] and fixed['cases']==1449,'fixed-base verification')
need(raw['counts']==dict(factorizations=483,combined_extracts=483,basis_solves=0,identity_probes=483),'literal counts')
need(proc['reason']=='exit0' and proc['returncode']==0 and proc['pins_unchanged'] and not post['conflicts'],'guard')
need('7405   7405' in (D/'reach-1/guard/run.log').read_text(),'regular Test output')
counts={}
for manifest,mapping in [('source-pins.json',{'driver.jl':'driver.before-review.jl','PLAN.md':'PLAN.before-review.md'}),('reviewed-source-pins.json',{}),('launch-pins.json',{})]:
 p=json.loads((D/manifest).read_text());counts[manifest]=len(p['inventory'])
 for path,rec in p['inventory'].items():
  q=D/mapping[Path(path).name] if Path(path).parent==D and Path(path).name in mapping else Path(path)
  need(digest(q)==rec['sha256'],'source binding '+path)
need(counts=={'source-pins.json':43,'reviewed-source-pins.json':51,'launch-pins.json':53},'binding cardinalities')
for witness in raw['witnesses']:need(digest(witness['path'])==witness['sha256'] and Path(witness['path']).stat().st_size==witness['bytes'],'local witness')
need(sum(w['bytes'] for w in raw['witnesses'])==raw['witness_bytes']==265791904,'witness total')
bound=json.loads((D/'boundary-source-bindings.json').read_text())
for name,h in bound['files'].items():need(digest(W/name)==h,'source boundary unchanged')
files=sorted(p for p in D.rglob('*') if p.is_file() and '__pycache__' not in str(p))
closure=dict(scope='structural diagnostic closure; not numerical skip/speedup/production admission',base=git('rev-parse','HEAD'),master=git('rev-parse','master'),tests=7405,verified_graphs=483,actual_RHS=966,fixed_base_scenarios=1449,all_checks=True,numerical_process_attempts=1,basis_solves=0,launch_bindings=53,manifest_reconciliation=counts,original_bindings_map={'source-pins.json/driver.jl':'driver.before-review.jl','source-pins.json/PLAN.md':'PLAN.before-review.md'},postflight_groups=len(post['checked_groups']),result_review_sha256=digest(D/'REVIEW-RESULTS.md'),local_witnesses=raw['witnesses'],bindings={str(p.relative_to(W)):digest(p) for p in files})
(D/'CLOSURE.json').write_text(json.dumps(closure,indent=2)+'\n');files.append(D/'CLOSURE.json')
manifest=D/'STAGED.json';manifest.write_text(json.dumps(dict(scope='exact complete staged set, hashes exclude self only',files={str(p.relative_to(W)):digest(p) for p in files}),indent=2)+'\n');files.append(manifest)
names=sorted(str(p.relative_to(W)) for p in files)
need(all(n.startswith('diagnostics/klu-block-reach/2026-10-29/') for n in names),'only new diagnostics')
git('add','--',*names);need(git('diff','--cached','--name-only').splitlines()==names,'complete staged set')
for n in names:need(hashlib.sha256(subprocess.check_output(['git','show',':'+n],cwd=W)).hexdigest()==digest(W/n),'staged blob '+n)
verbatim=lambda n: '/vendor/' in n or '/native-source/' in n or n.endswith('/inputs.toml')
subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if not verbatim(n)]],cwd=W,check=True)
r=subprocess.run(['git','diff','--cached','--check','--',*[n for n in names if verbatim(n)]],cwd=W,text=True,capture_output=True)
seal=dict(exact_names=names,blobs={n:digest(W/n) for n in names},publication_pass=True,verbatim_whitespace=dict(returncode=r.returncode,diagnostics=r.stdout+r.stderr))
Path('/tmp/klu-reach-20261029/publication-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(dict(publication_pass=True,exact_staged_files=len(names),all_bindings_reconciled=counts,all_witnesses_verified=True,authored_whitespace_pass=True)))
