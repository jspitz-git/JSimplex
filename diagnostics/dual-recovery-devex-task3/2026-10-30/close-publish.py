from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def req(v,m):
 if not v:raise RuntimeError(m)
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
for a,b in [('/tmp/devex-task3-review-final.md','REVIEW-FINAL.md'),('/tmp/devex-task3-review-final.json','review-final.json')]:fresh(b,Path(a).read_bytes())
temp_map={'/tmp/devex-task3-final-check.py':str(D/'reviewer-final-check.py'),'/tmp/devex-task3-final-check.json':str(D/'reviewer-final-check.json'),'/tmp/devex-task3-review.md':str(D/'REVIEW-INITIAL.md'),'/tmp/devex-task3-independent-check.py':str(D/'reviewer-check.py'),'/tmp/devex-task3-independent-check.json':str(D/'reviewer-check.json'),'/tmp/devex-task3-review-final.md':str(D/'REVIEW-FINAL.md')}
old_map={**temp_map,str(D/'REPORT.md'):str(D/'REPORT.md.before-review')}
def bindings_ok(r,m):return all(sha(Path(m.get(n,n)))==h for n,h in r['bindings'].items())
r=json.loads((D/'review-final.json').read_text());c=json.loads((D/'source-check.json').read_text());initial=json.loads((D/'review-initial.json').read_text());fix=json.loads((D/'review-fix.json').read_text())
checks={'final_review_accepted':r['accepted'] and all(r['checks'].values()),'final_review_bindings':bindings_ok(r,temp_map),'final_review_report':sha(D/'REVIEW-FINAL.md')==r['review_report_sha256'],'original_source_inverse':c['accepted'] and all(c['checks'].values()),'original_source_bindings_with_only_report_map':bindings_ok(c,old_map),'initial_review_rejection_preserved':not initial['accepted'],'initial_review_bindings_with_explicit_maps':bindings_ok(initial,old_map),'fix_source_checks':fix['accepted'] and all(fix['checks'].values()),'fix_bindings':bindings_ok(fix,{}),'diagnostic_baseline':git('rev-parse','HEAD')=='1509f43f9a288bfa5b3ae004e0e9f07b560b5469','master_unchanged':git('rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','no_tracked_changes':not git('diff','--name-only','HEAD'),'empty_index':not git('diff','--cached','--name-only')}
req(all(checks.values()),str(checks))
fresh('close-publish.py',Path(__file__).read_bytes())
fresh('closure.json',(json.dumps(dict(accepted=True,scope='Task3 isolated source preparation only; no Julia or runtime qualification',numerical_admission=False,production_admission=False,checks=checks,bindings={str(p):sha(p) for p in D.iterdir() if p.is_file()},historical_maps={'source-check.json':{str(D/'REPORT.md'):str(D/'REPORT.md.before-review')},'review-initial.json':old_map},temporary_exact_copy_maps=temp_map),indent=2)+'\n').encode())
paths=sorted(str(p.relative_to(W)) for p in D.iterdir() if p.is_file())
for p in paths:
 x=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(W/p)],capture_output=True,text=True);req(not x.stdout and not x.stderr and x.returncode in (0,1),'whitespace '+p+' '+x.stdout+x.stderr)
names=sorted(paths+[str((D/'publication.json').relative_to(W))]);blobs={p:git('hash-object',str(W/p)) for p in paths}
fresh('publication.json',(json.dumps(dict(accepted=True,expected_names=names,blobs_excluding_publication=blobs,closure_sha256=sha(D/'closure.json')),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','--',*names],check=True)
req(git('diff','--cached','--name-only').splitlines()==names,'names');seal={p:git('rev-parse',':'+p) for p in names};req(all(h==git('hash-object',str(W/p)) for p,h in seal.items()),'blobs')
Path('/tmp/dual-recovery-devex-task3-20261030/exact-staged.json').write_text(json.dumps(dict(names=names,blobs=seal),indent=2)+'\n')
print(json.dumps(dict(closure_checks=len(checks),exact_staged_files=len(names),exact_staged_blobs=len(seal))))
