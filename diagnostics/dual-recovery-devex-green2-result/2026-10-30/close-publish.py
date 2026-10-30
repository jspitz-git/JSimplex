from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/green2-1';T=Path('/tmp/devex-green2-run-20261030')
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
post=read(D/'postcheck.json');maps={};provenance={}
for table in (post['portable'],post['external_exact_copies']):
 for old,v in table.items():
  need(sha(old)==sha(v['copy'])==v['sha256'],'portable drift '+old)
  maps[old]=v['copy'];provenance[v['copy']]=dict(source=old,sha256=v['sha256'])
for old,name in [('/tmp/devex-green2-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-green2-result-review.json','review-final.json')]:
 dest=D/name;fresh(dest,Path(old).read_bytes());maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=sha(old))
review=read(D/'review-final.json')
table=review.get('bindings')
if table is None:
 table={}
 for sub in ('read_bindings','artifact_bindings'):
  for n,h in review[sub].items():
   need(n not in table or table[n]==h,'conflicting review hash');table[n]=h
for old,h in table.items():
 p=Path(old)
 if p.is_relative_to('/tmp') and old not in maps:
  dest=D/'result-review-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True);fresh(dest,p.read_bytes())
  need(sha(dest)==sha(old)==h,'review copy drift')
  maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=h)
def verified(r):return all(sha(maps.get(n,n))==h for n,h in r['bindings'].items())
ad=read(D/'green2/numerical-admission.json');audit=read(D/'green2/audit.json');pins=read(D/'green2/pins.json');done=read(D/'green2/completion.json');sup=read(D/'green2/supervisor.json');proc=read(D/'green2/guard/process.json')
checks={
'independent_result_accepted_scope':review['accepted'] is True and review['runtime_accepted'] is True and review['production_admission'] is False and review['cost_qualified'] is False and all(review['checks'].values()),
'result_review_all_bindings':all(sha(maps.get(n,n))==h for n,h in table.items()),
'result_review_report':sha(D/'REVIEW-FINAL.md')==review.get('review_report_sha256',review.get('report_sha256')),
'concrete_admission635_bound':ad['accepted'] is True and ad['scope']=='numerical_admission' and ad['phase']=='green2' and len(ad['bindings'])==635 and all(ad['checks'].values()) and verified(ad),
'canonical_audit_accepted5774':audit['accepted'] is True and audit['phase']=='green2' and audit['test_summary']==dict(Pass=5774,Total=5774) and audit['error'] is None and audit['production_admission'] is False and verified(audit),
'postcheck10_full736closure':post['accepted'] is True and len(post['checks'])==10 and all(post['checks'].values()) and len(post['checked_groups'])==736 and post['host']['conflicts']==[] and post['host']['still_active_current_launcher']==[],
'all459_pins_resolved_unchanged':len(pins['inventory'])==459 and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),
'natural_exit_no_cleanup':proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','abnormal_cleanup_attempted','child_cleanup_attempted']),
'exact_prior_plus_new_budget':done['elapsed_inclusive_seconds']==505.6401044019731 and done['total_inclusive_seconds']==527.9604928489425+done['elapsed_inclusive_seconds']==1033.6005972509156 and post['remaining_seconds']==1800-done['total_inclusive_seconds']==766.3994027490844,
'no_original_cost_outputs':sorted(p.name for p in (R.parent/'qualification-1').iterdir() if p.is_dir())==['green','red'],
'admitted_head':git('rev-parse','HEAD')=='4f5e6b9966830955637cfb7bba288b9339c9a494',
'master_unchanged':git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',
'tracked_tree_index_clean':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only')}
need(all(checks.values()),str(checks))
fresh(D/'close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 need(r.returncode in (0,1,2),'whitespace check error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr)
  exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,runtime_accepted=True,production_admission=False,cost_qualified=False,scope='ONE corrected-fixture GREEN2 functional stage only; no costs/promotion',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))])
fresh(D/'publication.json',(json.dumps(dict(accepted=True,runtime_accepted=True,production_admission=False,cost_qualified=False,scope='frozen one-GREEN2 results/admission/review',expected_names=names,blobs_excluding_publication={p:git('hash-object',str(W/p)) for p in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'staged names')
blobs={p:git('rev-parse',':'+p) for p in names};need(all(git('hash-object',str(W/p))==h for p,h in blobs.items()),'staged blobs')
with (T/'exact-staged.json').open('x') as f:json.dump(dict(names=names,blobs=blobs),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_accepted=True,cost_qualified=False,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_whitespace_exemptions=len(exempt))))
