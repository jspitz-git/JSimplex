from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/qualification-1/green';T=Path('/tmp/dual-recovery-devex-task4-green-20261030')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for a in iter(lambda:f.read(1024*1024),b''):h.update(a)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def req(v,m):
 if not v:raise RuntimeError(m)
def fresh(n,b):
 with (D/n).open('xb') as f:f.write(b)
def load(p):return json.loads(Path(p).read_text())
post=load(D/'postcheck.json');maps={};provenance={}
for table in (post['portable'],post['external_exact_copies']):
 for old,v in table.items():
  req(sha(old)==v['sha256']==sha(v['copy']),'original/portable drift '+old)
  maps[old]=v['copy'];provenance[v['copy']]=dict(source=old,sha256=v['sha256'])
for old,name in [('/tmp/devex-task4-green-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-task4-green-result-review.json','review-final.json')]:
 fresh(name,Path(old).read_bytes());maps[old]=str(D/name);provenance[str(D/name)]=dict(source=old,sha256=sha(old))
review=load(D/'review-final.json')
for old,h in review['bindings'].items():
 p=Path(old)
 if p.is_relative_to('/tmp') and old not in maps:
  dest=D/'result-review-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(p.read_bytes())
  req(sha(dest)==sha(old)==h,'result reviewer copy mismatch')
  maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=h)
def verified(r):return all(sha(maps.get(n,n))==h for n,h in r['bindings'].items())
ad=load(D/'green/numerical-admission.json');pins=load(D/'green/pins.json');done=load(D/'green/completion.json');sup=load(D/'green/supervisor.json');proc=load(D/'green/guard/process.json');cause=load(D/'cause-check.json')
checks={
'result_review_diagnostic_accepted':review['accepted'] is True and review.get('runtime_accepted') is False and review.get('candidate_accepted') is False and all(review['checks'].values()),
'result_review_all_bindings':verified(review),
'result_review_report':sha(D/'REVIEW-FINAL.md')==review['review_report_sha256'],
'admission_valid_and_bound':ad['accepted'] is True and ad['phase']=='green' and ad['scope']=='numerical_admission' and len(ad['bindings'])==371 and verified(ad),
'failed_exit_and_no_timeout_preserved':proc['returncode']==1 and proc['reason']=='exit1' and sup['accepted'] is False and done['supervisor_accepted'] is False and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']),
'no_canonical_audit_invented':not (R/'audit.json').exists() and not (D/'green/audit.json').exists() and post['canonical_audit_accepted'] is False,
'exact_failed_ordinary_result_and_cause':cause['accepted'] is True and all(cause['checks'].values()) and verified(cause) and cause['ordinary_summary']==dict(Pass=5772,Fail=0,Error=1,Broken=0,Total=5773),
'postcheck9_integrity_only':post['accepted'] is True and len(post['checks'])==9 and all(post['checks'].values()) and len(post['checked_groups'])==733 and post['host']['conflicts']==[],
'all217_actual_pins':len(pins['inventory'])==217 and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),
'shared_budget_exact':done['elapsed_inclusive_seconds']==494.6009602919803 and done['total_inclusive_seconds']==527.9604928489425 and post['remaining_seconds']==1800-done['total_inclusive_seconds']==1272.0395071510575,
'only_red_and_consumed_green':sorted(p.name for p in R.parent.iterdir() if p.is_dir())==['green','red'],
'guarded_head':git('rev-parse','HEAD')=='31415cc1eccc2d6c332ff14863e509f0d805c909',
'master_unchanged':git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',
'no_tracked_diff':not git('diff','HEAD','--name-only'),
'index_empty':not git('diff','--cached','--name-only')}
req(all(checks.values()),str(checks))
fresh('close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 x=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 req(x.returncode in (0,1,2),'unexpected whitespace checker status')
 if x.stdout or x.stderr:
  v=provenance.get(str(p));req(v is not None and sha(p)==v['sha256']==sha(v['source']),'authored whitespace '+str(p)+' '+x.stdout+x.stderr)
  exempt[str(p.relative_to(W))]=dict(sha256=sha(p),source=v['source'],diagnostics=x.stdout)
fresh('closure.json',(json.dumps(dict(accepted=True,runtime_accepted=False,scope='diagnostic closure of FAILED first GREEN only; no retry, cost or promotion',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))]);blobs={p:git('hash-object',str(W/p)) for p in names0}
fresh('publication.json',(json.dumps(dict(accepted=True,runtime_accepted=False,scope='frozen failed-GREEN evidence, diagnosis and independent reviews only',expected_names=names,blobs_excluding_publication=blobs,closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
req(git('diff','--cached','--name-only').splitlines()==names,'exact staged names')
blobs={p:git('rev-parse',':'+p) for p in names}
req(all(git('hash-object',str(W/p))==v for p,v in blobs.items()),'exact staged blobs')
with (T/'exact-staged.json').open('x') as f:json.dump(dict(names=names,blobs=blobs),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_accepted=False,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(review['bindings']),exact_names=len(names),exact_blobs=len(blobs),verbatim_whitespace_exemptions=len(exempt))))
