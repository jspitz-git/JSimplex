from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-cost-preparation-20261030')
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
pres=read(D/'preservation.json');maps={};provenance={}
for dest,v in pres['copies'].items():
 need(sha(dest)==sha(v['source'])==v['sha256'],'source copy changed');maps[v['source']]=dest;provenance[dest]=dict(source=v['source'],sha256=v['sha256'])
for old,name in [('/tmp/devex-cost-preparation-review.md','REVIEW-FINAL.md'),('/tmp/devex-cost-preparation-review.json','review-final.json')]:
 dest=D/name;fresh(dest,Path(old).read_bytes());maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=sha(old))
review=read(D/'review-final.json');table=review.get('bindings')
if table is None:
 table={}
 for sub in ('read_bindings','artifact_bindings'):
  for n,h in review[sub].items():
   need(n not in table or table[n]==h,'conflicting review binding');table[n]=h
for old,h in table.items():
 p=Path(old)
 if p.is_relative_to('/tmp') and old not in maps:
  dest=D/'review-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True);fresh(dest,p.read_bytes())
  need(sha(dest)==sha(old)==h,'review copy changed');maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=h)
source=read(D/'source-check.json');contract=read(D/'contract.json')
checks={
'final_review_offline_accepted':review['accepted'] is True and review['runtime_qualified'] is False and review['numerical_admission'] is False and all(review['checks'].values()),
'all_review_bindings':all(sha(maps.get(n,n))==h for n,h in table.items()),
'review_report_sha':sha(D/'REVIEW-FINAL.md')==review.get('review_report_sha256',review.get('report_sha256')),
'source19_all546':source['accepted'] is True and len(source['checks'])==19 and all(source['checks'].values()) and len(source['bindings'])==546 and all(sha(maps.get(n,n))==h for n,h in source['bindings'].items()),
'all526_prior_publications_unchanged':len(pres['frozen_publications'])==526 and all(sha(n)==h for n,h in pres['frozen_publications'].items()),
'four_copied_helpers_exact':len(pres['copies'])==4 and all(sha(n)==sha(v['source'])==v['sha256'] for n,v in pres['copies'].items()),
'original_driver_and_reference_bound':sha(contract['driver'])==contract['driver_sha256'] and sha(contract['reference'])==contract['reference_sha256'],
'budget_prior1033_not_reset':contract['base_used_seconds']==1033.6005972509156 and contract['initial_remaining_seconds']==766.3994027490844 and contract['shared_total_seconds']==1800,
'exact_two_sequential_attempts':contract['phases']==['reference-cost','candidate-cost'] and contract['maximum_new_processes']==2 and contract['per_phase_attempts']==1 and contract['sequential'] is True,
'no_numerical_root_seal_admission':not (W/'.superpowers/dual-recovery-devex-task4/cost-1').exists() and contract['runtime_unexecuted'] is True and contract['numerical_admission_created'] is False,
'head_master_unchanged':git('rev-parse','HEAD')=='6251dafd8be8f94ba4409f560692a893ced7d6a0' and git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',
'tracked_tree_index_clean':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only')}
need(all(checks.values()),str(checks))
fresh(D/'close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 need(r.returncode in (0,1,2),'whitespace checker error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr)
  exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='OFFLINE two sequential fixed64 cost tools/guards/auditor only',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))])
fresh(D/'publication.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='OFFLINE reference/candidate cost admission preparation',expected_names=names,blobs_excluding_publication={p:git('hash-object',str(W/p)) for p in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'staged names')
blobs={p:git('rev-parse',':'+p) for p in names};need(all(git('hash-object',str(W/p))==h for p,h in blobs.items()),'staged blobs')
with (T/'exact-staged.json').open('x') as f:json.dump(dict(names=names,blobs=blobs),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_qualified=False,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_whitespace_exemptions=len(exempt))))
