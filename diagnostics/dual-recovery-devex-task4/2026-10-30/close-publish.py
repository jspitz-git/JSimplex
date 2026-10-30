from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def req(v,m):
 if not v:raise RuntimeError(m)
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
for a,b in [('/tmp/devex-task4-preparation-review-final.md','REVIEW-FINAL.md'),('/tmp/devex-task4-preparation-review-final.json','review-final.json'),('/tmp/devex-task4-final-independent-checks.json','reviewer-final-independent-checks.json')]:fresh(b,Path(a).read_bytes())
oldmap={str(D/'ADMISSION-PREPARATION.md'):str(D/'ADMISSION-PREPARATION.before-review.md'),'/tmp/devex-task4-independent-sourcechecks.json':str(D/'reviewer-initial-sourcechecks.json')}
finalmap={'/tmp/devex-task4-final-independent-checks.json':str(D/'reviewer-final-independent-checks.json')}
def verified(r,m):return all(sha(Path(m.get(n,n)))==h for n,h in r['bindings'].items())
r=json.loads((D/'review-final.json').read_text());initial=json.loads((D/'review-initial.json').read_text());source=json.loads((D/'source-check.json').read_text());fix=json.loads((D/'review-fix.json').read_text());validation=json.loads((D/'fix-validation.json').read_text())
checks={'source_preparation_accepted':source['accepted'] and all(source['checks'].values()),'source_bindings_exact_except_document_snapshot':verified(source,oldmap),'initial_rejection_preserved':initial['accepted'] is False,'initial_review_exact_bindings':verified(initial,oldmap),'canonical_fix_checks':fix['accepted'] and all(fix['checks'].values()),'canonical_fix_bindings':verified(fix,{}),'new_offline_tests_accepted':validation['accepted'] and all(validation['checks'].values()),'new_test_bindings':verified(validation,{}),'final_review_accepted':r['accepted'] and all(r['checks'].values()),'final_review_bindings':verified(r,finalmap),'final_report_bound':sha(D/'REVIEW-FINAL.md')==r['review_report_sha256'],'HEAD_unchanged':git('rev-parse','HEAD')=='99deb2506e4437a56dbb6606f1cad2a3ec5da99f','master_unchanged':git('rev-parse','master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','actual_tracked_files_unchanged':not git('diff','--name-only','HEAD'),'empty_index':not git('diff','--cached','--name-only'),'no_runtime_seal_or_output':not (W/'.superpowers/dual-recovery-devex-task4/qualification-1').exists()}
req(all(checks.values()),str(checks))
fresh('close-publish.py',Path(__file__).read_bytes())
# Verbatim copies are exempt only where Git reports whitespace and their exact
# staged bytes match the already-bound staging source/hash. Never rewrite them.
staging=json.loads((D/'staging.json').read_text())['bindings'];exempt={}
files=sorted(p for p in D.rglob('*') if p.is_file())
for p in files:
 x=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 if x.stdout or x.stderr:
  v=staging.get(str(p));req(v is not None and sha(p)==v['sha256']==sha(Path(v['source'])),'authored whitespace '+str(p)+' '+x.stdout+x.stderr)
  exempt[str(p.relative_to(W))]=dict(sha256=sha(p),source=v['source'],diagnostics=x.stdout)
req(not any('__pycache__' in p.parts or p.suffix=='.pyc' for p in files),'unexpected bytecode')
fresh('closure.json',(json.dumps(dict(accepted=True,scope='Task4 verification PREPARATION ONLY; no Julia, seal, launch or numerical admission',numerical_admission=False,production_admission=False,checks=checks,bindings={str(p):sha(p) for p in files},historical_maps={'source-check.json':oldmap,'review-initial.json':oldmap,'review-final.json':finalmap},verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
paths=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(paths+[str((D/'publication.json').relative_to(W))]);blobs={p:git('hash-object',str(W/p)) for p in paths}
fresh('publication.json',(json.dumps(dict(accepted=True,scope='reviewed offline preparation only',expected_names=names,blobs_excluding_publication=blobs,closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
req(git('diff','--cached','--name-only').splitlines()==names,'staged names');seal={p:git('rev-parse',':'+p) for p in names};req(all(h==git('hash-object',str(W/p)) for p,h in seal.items()),'staged blobs')
Path('/tmp/dual-recovery-devex-task4-20261030/exact-staged.json').write_text(json.dumps(dict(names=names,blobs=seal),indent=2)+'\n')
print(json.dumps(dict(closure_checks=len(checks),exact_staged_names=len(names),exact_staged_blobs=len(seal),verbatim_whitespace_exemptions=len(exempt))))
