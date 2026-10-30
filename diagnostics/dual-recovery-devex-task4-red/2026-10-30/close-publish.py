from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/red'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def req(v,m):
 if not v:raise RuntimeError(m)
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
provenance={}
for a,b in [('/tmp/devex-task4-red-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-task4-red-result-review.json','review-final.json'),('/tmp/devex-task4-red-result-independent-check.py','reviewer-result-check.py'),('/tmp/devex-task4-red-result-independent-checks.json','reviewer-result-checks.json')]:
 fresh(b,Path(a).read_bytes());provenance[str(D/b)]=dict(source=a,sha256=sha(a))
post=json.loads((D/'postcheck.json').read_text());maps={}
for table in (post['portable'],post['external_exact_copies'],json.loads((D/'admission-extra-copies.json').read_text())):
 for old,v in table.items():
  req(sha(old)==v['sha256']==sha(v['copy']),'original/portable drift '+old);maps[old]=v['copy'];provenance[v['copy']]=dict(source=old,sha256=v['sha256'])
for old,new in [('/tmp/devex-task4-red-result-independent-check.py','reviewer-result-check.py'),('/tmp/devex-task4-red-result-independent-checks.json','reviewer-result-checks.json')]:maps[old]=str(D/new)
review=json.loads((D/'review-final.json').read_text());ad=json.loads((D/'red/numerical-admission.json').read_text());audit=json.loads((D/'red/audit.json').read_text());pins=json.loads((D/'red/pins.json').read_text());done=json.loads((D/'red/completion.json').read_text())
def verified(r):return all(sha(maps.get(n,n))==h for n,h in r['bindings'].items())
checks={'result_review_accepted':review['accepted'] and all(review['checks'].values()),'result_review334_bindings':len(review['bindings'])==334 and verified(review),'result_review_report':sha(D/'REVIEW-FINAL.md')==review['review_report_sha256'],'admission_valid_and_bound':ad['accepted'] and ad['scope']=='numerical_admission' and ad['phase']=='red' and verified(ad),'canonical_raw_audit_exact':audit['accepted'] and audit['test_summary']=={'Pass':7,'Fail':1,'Total':8} and verified(audit),'postcheck9_accepted':post['accepted'] and all(post['checks'].values()),'all217_actual_pins':len(pins['inventory'])==217 and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),'shared_budget_exact':done['total_inclusive_seconds']==post['elapsed_inclusive_seconds']==33.35953255696222 and post['remaining_guarded_seconds']==1800-done['total_inclusive_seconds'],'only_one_phase':sorted(p.name for p in R.parent.iterdir() if p.is_dir())==['red'],'guarded_ref':git('rev-parse','HEAD')=='68240e80279b1339fd24c002b91664559acfb1dd','master_unchanged':git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','no_tracked_diff':not git('diff','--name-only','HEAD'),'index_empty':not git('diff','--cached','--name-only')}
req(all(checks.values()),str(checks))
fresh('close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 x=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 if x.stdout or x.stderr:
  v=provenance.get(str(p));req(v is not None and sha(p)==v['sha256']==sha(v['source']),'authored whitespace '+str(p)+' '+x.stdout+x.stderr)
  exempt[str(p.relative_to(W))]=dict(sha256=sha(p),source=v['source'],diagnostics=x.stdout)
fresh('closure.json',(json.dumps(dict(accepted=True,scope='ONE original RED accepted only, expected7PASS1FAIL; no candidate/cost/promotion',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))]);blobs={p:git('hash-object',str(W/p)) for p in names0}
fresh('publication.json',(json.dumps(dict(accepted=True,scope='frozen single-RED raw evidence and independent reviews only',expected_names=names,blobs_excluding_publication=blobs,closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
req(git('diff','--cached','--name-only').splitlines()==names,'staged names')
seal={p:git('rev-parse',':'+p) for p in names};req(all(git('hash-object',str(W/p))==h for p,h in seal.items()),'staged blobs')
Path('/tmp/dual-recovery-devex-task4-red-20261030/exact-staged.json').write_text(json.dumps(dict(names=names,blobs=seal),indent=2)+'\n')
print(json.dumps(dict(accepted=True,closure_checks=len(checks),exact_names=len(names),exact_blobs=len(seal),verbatim_whitespace_exemptions=len(exempt))))
