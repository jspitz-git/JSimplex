from pathlib import Path
import sys,json,hashlib,shutil,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/devex-saved-runtime/2026-10-31-reviewed';sys.path.insert(0,str(D));import common as C
for a,b in (('/tmp/devex-saved-runtime-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-saved-runtime-result-review.json','review-final.json')):shutil.copyfile(a,D/b)
shutil.copyfile(__file__,D/'finish-evidence.py')
r=C.read(D/'review-final.json');checks={}
def check(k,v):checks[k]=bool(v);C.require(bool(v),k)
check('independent_component_result_accepted',r['accepted'] is True and r['scope']=='component_result_only' and r['production_admission'] is False)
check('independent_review_checks',len(r['checks'])==364 and all(v is True for v in r['checks'].values()))
check('independent_review_bindings',all(C.sha(p)==h for p,h in r['bindings'].items()))
check('new_launch_pins',C.pins_ok());old=D.with_name('2026-10-31');check('initial107pins_unchanged',all(C.sha(p)==v['sha256'] for p,v in C.read(old/'pins.json')['inventory'].items()))
check('original_attempt_never_launched',not (old/'run-1').exists());check('actual_audit_accepted',C.read(C.R/'audit.json')['accepted'] is True);check('standalone_full_closure',len(C.read(C.R/'closed.json')['checked_groups'])==748 and not C.read(C.R/'closed.json')['conflicts'])
h=C.host();check('fresh_full748_groups_sessions_noJulia',len(h['checked_groups'])==748 and not h['conflicts']);check('master_unchanged',h['refs']['master']=='9940bdabe149e922afa60b5364227a7e7393bc75');check('diagnostic_before',h['refs']['diagnostic']=='777de74f33f8192a566231c9943eccf02ffe30fc');check('no_staged_user_change',not C.git(W,'diff','--cached','--name-only'))
files=sorted(p for p in (W/'diagnostics/devex-saved-runtime').rglob('*') if p.is_file());check('evidence_scope_no_cache',all('__pycache__' not in str(p) for p in files));check('production_not_edited',not C.git(W,'diff','--name-only','--','src','test','Project.toml','.github'))
C.fresh(D/'closure.json',dict(accepted=True,checks=checks,host=h,bindings={str(p):C.sha(p) for p in files}))
files=sorted(p for p in (W/'diagnostics/devex-saved-runtime').rglob('*') if p.is_file());names=[str(p.relative_to(W)) for p in files];publication_name=str((D/'publication.json').relative_to(W));expected=sorted(names+[publication_name]);C.fresh(D/'publication.json',dict(accepted=True,expected_names=expected,hashes={str(p.relative_to(W)):C.sha(p) for p in files},scope='diagnostic evidence only; master unchanged; actual committed blobs checked separately before push'))
C.require(not C.git(W,'diff','--cached','--name-only'),'index changed');subprocess.run(['git','-C',str(W),'add','--',*expected],check=True)
staged=C.git(W,'diff','--cached','--name-only').splitlines();C.require(staged==expected,'exact staged names mismatch')
for n in expected:
 actual=subprocess.check_output(['git','-C',str(W),'rev-parse',':'+n],text=True).strip();want=C.git(W,'hash-object','--',n);C.require(actual==want,'staged blob mismatch '+n)
subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True)
C.fresh('/tmp/devex-saved-runtime-20261031/staged.json',dict(accepted=True,names=expected,blobs={n:C.git(W,'rev-parse',':'+n) for n in expected},closure_checks=len(checks)))
print(json.dumps(dict(closure_pass=True,closure_checks=len(checks),exact_staged_files=len(expected))))
