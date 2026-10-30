from pathlib import Path
import hashlib,json,subprocess,sys,difflib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';T=Path('/tmp/devex-production-preparation-20261030');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
sys.path.insert(0,str(P));import common as C
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def fresh(p,b):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('xb') as f:f.write(b)
m=read(D/'manifest.json');maps={};provenance={}
for src,v in m['exact_copies'].items():
 need(sha(src)==sha(v['copy'])==v['sha256'],'exact copy changed');maps[src]=v['copy'];provenance[v['copy']]=dict(source=src,sha256=v['sha256'])
# Exact before copies map only the four files touched by the future patch.
for rel,v in m['baseline_sha256'].items():
 src=W/rel;dst=D/'baseline'/rel;need(sha(src)==sha(dst)==v,'before copy');maps[str(src)]=str(dst);provenance[str(dst)]=dict(source=str(src),sha256=v)
for src,name in [('/tmp/devex-production-preparation-review.md','REVIEW-FINAL.md'),('/tmp/devex-production-preparation-review.json','review-final.json')]:
 dst=D/name;fresh(dst,Path(src).read_bytes());maps[src]=str(dst);provenance[str(dst)]=dict(source=src,sha256=sha(src))
review=read(D/'review-final.json');table=review.get('bindings')
if table is None:
 table={}
 for field in ('read_bindings','artifact_bindings'):
  for n,v in review[field].items():
   need(n not in table or table[n]==v,'review collision');table[n]=v
for src,v in table.items():
 need(sha(src)==v,'review original binding '+src)
 if Path(src).is_relative_to('/tmp') and src not in maps:
  dst=D/'review-artifacts'/Path(src).relative_to('/tmp');fresh(dst,Path(src).read_bytes());need(sha(dst)==v,'review copy '+src);maps[src]=str(dst);provenance[str(dst)]=dict(source=src,sha256=v)
a=read(D/'source-check.json');b=read(D/'source-check-endpoint.json');h=C.host();C.validate_closed('reference-cost');C.validate_closed('candidate-cost');oldhead='2d226b84e79e8afeff3ec8d8961b15af44b12085'
checks={
'independent_offline_preparation_accepted':review['accepted'] is True and review['scope']=='production_preparation_only' and review['runtime_qualified'] is False and review['numerical_admission'] is False and review['production_admission'] is False and all(type(v) is bool and v for v in review['checks'].values()),
'complete_review_original_and_copy_hashes':all(sha(n)==sha(maps.get(n,n))==v for n,v in table.items()),
'review_report_bound':sha(D/'REVIEW-FINAL.md')==review.get('review_report_sha256',review.get('report_sha256')),
'original_sourcecheck22of23_false_preserved':a['accepted'] is False and len(a['checks'])==23 and [n for n,v in a['checks'].items() if not v]==['endpoint23_assertions_retained_ordered_plus_work'],
'separate_endpoint6checks_accepted':b['accepted'] is True and len(b['checks'])==6 and all(b['checks'].values()) and len(b['original_assertions'])==23 and len(b['prepared_assertions'])==24,
'all353_source_bindings_unchanged':len(a['bindings'])==353 and all(sha(n)==v for n,v in a['bindings'].items()),
'all_endpoint_supplement_hashes':all(sha(n)==v for n,v in b['bindings'].items()),
'exact11_payload_names_and_hashes':len(m['payload'])==11 and sorted(str(p.relative_to(D/'prepared')) for p in (D/'prepared').rglob('*') if p.is_file())==m['payload'] and all(sha(D/'prepared'/n)==v for n,v in m['payload_sha256'].items()),
'exact4_before_maps_and_current_baseline':len(m['baseline_sha256'])==4 and all(sha(W/n)==sha(D/'baseline'/n)==v for n,v in m['baseline_sha256'].items()),
'all264_prior_cost_publication_blobs':len(a['prior_publications'])==264 and all(sha(n)==v and git('hash-object',n)==git('rev-parse','HEAD:'+str(Path(n).relative_to(W))) for n,v in a['prior_publications'].items()),
'no_new_numerical_time':read(C.out('candidate-cost')/'completion.json')['total_inclusive_seconds']==1108.3747013349202 and m['prepared_runtime_unexecuted'] is True,
'fresh_full742_groups_ANDsessions_noJulia':len(h['checked_groups'])==742 and not h['conflicts'] and not h['still_active_current_launcher'] and set(h['checked_groups'])==C.expected_groups('candidate-cost',h['boot_id'],True),
'head_master_baseline_unchanged':git('rev-parse','HEAD')==oldhead and git('rev-parse','master')==git('rev-parse','origin/master')==C.MASTER,
'actual_src_test_env_CI_and_index_unchanged':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github')}
need(all(checks.values()),str(checks));fresh(D/'publication-host.json',(json.dumps(h,indent=2)+'\n').encode());fresh(D/'close-publish.py',Path(__file__).read_bytes());paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True);need(r.returncode in (0,1,2,3),'whitespace checker error')
 if r.stdout or r.stderr:
  if p==D/'production.patch':
   rebuilt=[]
   for rel in m['payload']:
    old=(D/'baseline'/rel).read_text() if (D/'baseline'/rel).exists() else '';new=(D/'prepared'/rel).read_text();rebuilt.append(f'diff --git a/{rel} b/{rel}\n')
    if not (D/'baseline'/rel).exists():rebuilt.append('new file mode 100644\n')
    rebuilt.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+rel if (D/'baseline'/rel).exists() else '/dev/null',tofile='b/'+rel))
   trailing=[line for line in p.read_text().splitlines() if line.rstrip()!=line]
   need(not r.stderr and ''.join(rebuilt)==p.read_text() and len(trailing)==9 and all(line==' ' for line in trailing) and sha(p)==a['bindings'][str(p)],'noncanonical patch whitespace')
   exempt[str(p.relative_to(W))]=dict(scope='exact generated unified-diff formatting only',reason='nine single-space blank context lines; no authored source trailing whitespace',sha256=sha(p),diagnostics=r.stdout)
  else:
   v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr);exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout+r.stderr)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,scope='production_preparation_only',runtime_qualified=False,numerical_admission=False,production_admission=False,checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode());names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))]);fresh(D/'publication.json',(json.dumps(dict(accepted=True,scope='production_preparation_only',expected_names=names,blobs_excluding_publication={n:git('hash-object',str(W/n)) for n in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode());subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True);need(git('diff','--cached','--name-only').splitlines()==names,'exact staged names');blobs={n:git('rev-parse',':'+n) for n in names};need(all(git('hash-object',str(W/n))==v for n,v in blobs.items()),'exact staged blobs');fresh(T/'exact-staged.json',(json.dumps(dict(names=names,blobs=blobs),indent=2)+'\n').encode());print(json.dumps(dict(accepted=True,scope='production_preparation_only',closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_exemptions=len(exempt))))
