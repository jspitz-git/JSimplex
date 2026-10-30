from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';T=Path('/tmp/devex-green2-preparation-20261030')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
def fresh(p,b):
 with Path(p).open('xb') as f:f.write(b)
pres=read(D/'preservation.json');maps=read(D/'initial-review-maps.json')|read(D/'review-initial-portable-maps.json');provenance={}
for dest,v in pres['copies'].items():
 need(sha(dest)==sha(v['source'])==v['sha256'],'helper copy changed')
 provenance[dest]=dict(source=v['source'],sha256=v['sha256'])
for n,v in maps.items():
 need(sha(v['copy'])==v['sha256'],'historical copy changed')
 provenance[v['copy']]=dict(source=n,sha256=v['sha256'])
for old,name in [('/tmp/devex-green2-preparation-review-final.md','REVIEW-FINAL.md'),('/tmp/devex-green2-preparation-review-final.json','review-final.json')]:
 dest=D/name;fresh(dest,Path(old).read_bytes());maps[old]=dict(copy=str(dest),sha256=sha(old));provenance[str(dest)]=dict(source=old,sha256=sha(old))
review=read(D/'review-final.json')
table=review.get('bindings')
if table is None:
 table={}
 for sub in ('read_bindings','artifact_bindings'):
  for n,h in review[sub].items():
   need(n not in table or table[n]==h,'conflicting review bindings')
   table[n]=h
for old,h in table.items():
 p=Path(old)
 if p.is_relative_to('/tmp') and old not in maps:
  dest=D/'review-final-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True);fresh(dest,p.read_bytes())
  need(sha(dest)==h,'review temp copy changed')
  maps[old]=dict(copy=str(dest),sha256=h);provenance[str(dest)]=dict(source=old,sha256=h)
def resolve(n,h):
 item=maps.get(n)
 return item['copy'] if item and item['sha256']==h else n
def bindings(table):return all(sha(resolve(n,h))==h for n,h in table.items())
initial=read(D/'review-initial.json');source=read(D/'source-check.json');fix=read(D/'review-fix-check.json');contract=read(D/'contract.json')
report_sha=review.get('review_report_sha256',review.get('report_sha256'))
checks={
'final_source_review_accepted':review['accepted'] is True and review['runtime_qualified'] is False and review['numerical_admission'] is False and all(review['checks'].values()),
'final_review_all_bindings':bindings(table),
'final_review_report':sha(D/'REVIEW-FINAL.md')==report_sha,
'initial_rejection_preserved':initial['accepted'] is False and bindings(initial['bindings']),
'bounded_fix13_and_bindings':fix['accepted'] is True and len(fix['checks'])==13 and all(fix['checks'].values()) and bindings(fix['bindings']),
'initial_source425_unchanged':source['accepted'] is True and len(source['bindings'])==425 and all(source['checks'].values()) and bindings(source['bindings']),
'all402_previous_files_unchanged':len(pres['frozen_publications'])==402 and all(sha(n)==h for n,h in pres['frozen_publications'].items()),
'copied_guards_helpers_exact':all(sha(n)==v['sha256']==sha(v['source']) for n,v in pres['copies'].items()),
'no_runtime_directory_or_seal':not (W/'.superpowers/dual-recovery-devex-task4/green2-1').exists(),
'prior_time1800_charged':contract['used_seconds']==527.9604928489425 and contract['remaining_seconds']==1272.0395071510575 and contract['shared_total_seconds']==1800,
'canonical_launcher_auditor':"import audit_reviewed as audit" in (D/'launch-reviewed.py').read_text() and "(C.D/'audit_reviewed.py').resolve()" in (D/'launch-reviewed.py').read_text(),
'current_refs_unchanged':git('rev-parse','HEAD')=='514e22c1a5e8a056bb81e4d9a63b1e6003040df1' and git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',
'tracked_tree_index_clean':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only')}
need(all(checks.values()),str(checks))
fresh(D/'close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 need(r.returncode in (0,1,2),'whitespace check error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr)
  exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='OFFLINE concrete corrected GREEN2 preparation only',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_hash_conditional_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))])
fresh(D/'publication.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='OFFLINE concrete corrected GREEN2 tools/guards/auditor/tests/reviews',expected_names=names,blobs_excluding_publication={p:git('hash-object',str(W/p)) for p in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'exact staged names')
blobs={p:git('rev-parse',':'+p) for p in names};need(all(git('hash-object',str(W/p))==h for p,h in blobs.items()),'exact staged blobs')
with (T/'exact-staged.json').open('x') as f:json.dump(dict(names=names,blobs=blobs),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_qualified=False,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_whitespace_exemptions=len(exempt))))
