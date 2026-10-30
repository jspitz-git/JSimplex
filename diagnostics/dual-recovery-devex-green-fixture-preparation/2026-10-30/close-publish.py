from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30';T=Path('/tmp/dual-recovery-devex-green-fixtures-20261030')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def fresh(p,b):
 with Path(p).open('xb') as f:f.write(b)
stage=read(D/'staging.json');source=read(D/'source-check.json');maps={};provenance={}
fresh(D/'parent-schema-note.json',(T/'parent-schema-note.json').read_bytes())
for dest,v in stage['copies'].items():
 need(sha(dest)==sha(v['source'])==v['sha256'],'staging drift')
 maps[v['source']]=dest;provenance[dest]=dict(source=v['source'],sha256=v['sha256'])
for old,name in [('/tmp/devex-green-fixtures-review.md','REVIEW-FINAL.md'),('/tmp/devex-green-fixtures-review.json','review-final.json')]:
 dest=D/name;fresh(dest,Path(old).read_bytes());maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=sha(old))
review=read(D/'review-final.json')
review_bindings=review['read_bindings']|review['artifact_bindings']
for old,h in review_bindings.items():
 p=Path(old)
 if p.is_relative_to('/tmp') and old not in maps:
  dest=D/'review-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True);fresh(dest,p.read_bytes())
  need(sha(dest)==sha(old)==h,'review copy mismatch');maps[old]=str(dest);provenance[str(dest)]=dict(source=old,sha256=h)
def bindings(r):return all(sha(maps.get(p,p))==h for p,h in r['bindings'].items())
checks={
'offline_review_accepted':review['accepted'] is True and review.get('runtime_qualified') is False and review.get('numerical_admission') is False and all(review['checks'].values()),
'all_review_bindings':all(sha(maps.get(n,n))==h for n,h in review_bindings.items()),
'review_report_sha':sha(D/'REVIEW-FINAL.md')==review['report_sha256'],
'source17_all365_bindings':source['accepted'] and len(source['checks'])==17 and len(source['bindings'])==365 and all(source['checks'].values()) and bindings(source),
'all255_frozen_publications_unchanged':len(stage['frozen_previous_publications'])==255 and all(sha(p)==h for p,h in stage['frozen_previous_publications'].items()),
'whole_prepared91_original_bytes':len([p for p in (D/'prepared').rglob('*') if p.is_file()])==91 and all(sha(dest)==v['sha256'] for dest,v in stage['copies'].items()),
'complete_dependency_audit':read(D/'fixture-check.json')['accepted'] and read(D/'fixture-check.json')['program_count']==15 and read(D/'fixture-check.json')['fixture_count']==2 and read(D/'fixture-check.json')['include_edges']==14,
'original_green_unaccepted':read(W/'.superpowers/dual-recovery-devex-task4/qualification-1/green/completion.json')['supervisor_accepted'] is False and not (W/'.superpowers/dual-recovery-devex-task4/qualification-1/green/audit.json').exists(),
'no_new_runtime_dirs':sorted(p.name for p in (W/'.superpowers/dual-recovery-devex-task4/qualification-1').iterdir() if p.is_dir())==['green','red'],
'head_and_master_unchanged':git('rev-parse','HEAD')=='a2f2415fcc6c9a018ae8209e28f517da1b23b688' and git('rev-parse','master')==git('rev-parse','origin/master')=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b',
'tracked_tree_and_index_clean':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'),
'prior_time_not_reset':stage['consumed_seconds']==source['consumed_guarded_seconds']==527.9604928489425 and stage['unspent_shared_seconds']==source['remaining_shared_seconds']==1272.0395071510575}
need(all(checks.values()),str(checks))
fresh(D/'close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 need(r.returncode in (0,1,2),'whitespace checker error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr)
  exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='OFFLINE fixture preparation correction only; no Julia or launch',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))])
fresh(D/'publication.json',(json.dumps(dict(accepted=True,runtime_qualified=False,numerical_admission=False,scope='isolated exact-source GREEN fixtures, offline tests and review only',expected_names=names,blobs_excluding_publication={p:git('hash-object',str(W/p)) for p in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True)
need(git('diff','--cached','--name-only').splitlines()==names,'exact staged names')
blobs={p:git('rev-parse',':'+p) for p in names};need(all(git('hash-object',str(W/p))==b for p,b in blobs.items()),'exact staged blobs')
with (T/'exact-staged.json').open('x') as f:json.dump(dict(names=names,blobs=blobs),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,runtime_qualified=False,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(review_bindings),exact_names=len(names),exact_blobs=len(blobs),verbatim_whitespace_exemptions=len(exempt))))
