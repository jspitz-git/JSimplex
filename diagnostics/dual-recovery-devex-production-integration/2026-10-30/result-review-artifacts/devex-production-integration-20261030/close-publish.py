from pathlib import Path
import sys,json,hashlib,subprocess
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-production-integration/2026-10-30');T=Path('/tmp/devex-production-integration-20261030');sys.path.insert(0,str(D));import common as C
W=C.W;M=C.M

def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return C.sha(p)
def read(p):return C.read(p)
def git(root,*a):return C.git(root,*a)
def fresh(p,b):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('xb') as f:f.write(b)
post=read(D/'postcheck.json');state=read(D/'integration.json');maps={};provenance={}
for group in ('portable','external_exact_copies'):
 for src,v in post[group].items():
  need(sha(src)==sha(v['copy'])==v['sha256'],'exact copy changed '+src);maps[src]=v['copy'];provenance[v['copy']]=dict(source=src,sha256=v['sha256'])
for src,name in [('/tmp/devex-production-master-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-production-master-result-review.json','review-final.json'),(str(T/'write-report.py'),'write-report.py')]:
 dst=D/name;fresh(dst,Path(src).read_bytes());maps[src]=str(dst);provenance[str(dst)]=dict(source=src,sha256=sha(src))
review=read(D/'review-final.json');table=review.get('bindings')
if table is None:
 table={}
 for field in ('read_bindings','artifact_bindings'):
  for n,v in review[field].items():need(n not in table or table[n]==v,'review collision');table[n]=v
for n,v in table.items():
 need(sha(n)==v,'fresh review original binding '+n)
 if Path(n).is_relative_to('/tmp') and n not in maps:
  dst=D/'result-review-artifacts'/Path(n).relative_to('/tmp');fresh(dst,Path(n).read_bytes());need(sha(dst)==v,'result review copy');maps[n]=str(dst);provenance[str(dst)]=dict(source=n,sha256=v)
audit=read(C.R/'audit.json');closed=read(C.R/'closed.json');attempt=read(C.R/'attempt.json');ad=read(attempt['admission_path']);pins=read(C.R/'pins.json');proc=read(C.R/'guard/process.json');done=read(C.R/'completion.json');h=C.host();C.verify_pins(pins);members={str(p) for p in C.R.rglob('*') if p.is_file() and p.name!='closed.json'};members.update((attempt['admission_path'],ad['review_report']));before=read(D/'before.json')
checks={
'actual_master_result_review_accepted':review['accepted'] is True and review['scope']=='production_master_result_only' and review['runtime_accepted'] is True and review['production_admission'] is True and all(v is True for v in review['checks'].values()),
'all_fresh_review_original_and_portable_hashes':all(sha(n)==sha(maps.get(n,n))==v for n,v in table.items()),
'review_report_bound':sha(D/'REVIEW-FINAL.md')==review.get('review_report_sha256',review.get('report_sha256')),
'canonical5776_actual_master_pass':audit['accepted'] is True and audit['test_summary']==dict(Pass=5776,Total=5776) and audit['error'] is None and proc['returncode']==0 and proc['cwd']==str(D),
'complete_canonical_audit_bindings':all(sha(n)==v for n,v in audit['bindings'].items()),
'exact_closed_runtime_membership':closed['accepted'] is True and set(closed['bindings'])==members and all(sha(n)==v for n,v in closed['bindings'].items()),
'all164_specific_pins':len(pins['inventory'])==164,
'complete_numerical_admission':ad['accepted'] is True and all(ad['checks'].values()) and all(sha(n)==v for n,v in ad['bindings'].items()),
'parent_postcheck_all_passed':post['accepted'] is True and all(post['checks'].values()),
'no_budget_reset':C.prior_time()==1108.3747013349202 and done['total_inclusive_seconds']==1108.3747013349202+done['elapsed_inclusive_seconds']<=1800 and post['remaining_seconds']==1800-done['total_inclusive_seconds'],
'fresh_full745_groups_ANDsessions_noJulia':len(h['checked_groups'])==745 and not h['still_active_current_launcher'] and not h['conflicts'] and set(h['checked_groups'])==C.groups(h['boot_id'],True),
'exact11_production_commit_files_blobs':git(W,'diff-tree','--no-commit-id','--name-only','-r',state['production_commit']).splitlines()==read(D/'production-commit.json')['names'] and all(git(W,'rev-parse',state['production_commit']+':'+n)==v for n,v in read(D/'production-commit.json')['blobs'].items()),
'actual_master_DIAG_source_payload_identical':all(sha(root/n)==v for root in (W,M) for n,v in state['payload_sha256'].items()) and not git(W,'diff',state['production_commit'],'HEAD','--','src','test','Project.toml','.github'),
'user_files_and_status_preserved':all(sha(n)==v for n,v in state['user_hashes'].items()) and git(M,'status','--porcelain','-uall')==before['master_status'] and not git(M,'diff','--cached','--name-only'),
'only_exact_historical8_before_maps':len(before['before_maps'])==8 and all(sha(v['copy'])==v['sha256'] for v in before['before_maps'].values()),
'no_premature_remote_master_update':git(W,'rev-parse','origin/master')==state['remote_master_before'],
'diagnostic_head_and_index_unchanged':git(W,'rev-parse','HEAD')==state['diagnostic_head'] and not git(W,'diff','HEAD','--name-only') and not git(W,'diff','--cached','--name-only')}
need(all(checks.values()),str(checks));fresh(D/'publication-host.json',(json.dumps(h,indent=2)+'\n').encode());fresh(D/'close-publish.py',Path(__file__).read_bytes());paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True);need(r.returncode in (0,1,2,3),'diffcheck error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr);exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout+r.stderr)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,scope='production_master_result_only',production_admission=True,production_commit=state['production_commit'],remote_push_unexecuted=True,checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,historical_before_maps=before['before_maps'],verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode());names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))]);fresh(D/'publication.json',(json.dumps(dict(accepted=True,scope='production_master_result_only',production_commit=state['production_commit'],expected_names=names,blobs_excluding_publication={n:git(W,'hash-object',str(W/n)) for n in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode());subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True);need(git(W,'diff','--cached','--name-only').splitlines()==names,'exact staged names');blobs={n:git(W,'rev-parse',':'+n) for n in names};need(all(git(W,'hash-object',str(W/n))==v for n,v in blobs.items()),'exact staged blobs');fresh(T/'exact-staged.json',(json.dumps(dict(names=names,blobs=blobs),indent=2)+'\n').encode());print(json.dumps(dict(accepted=True,production_commit=state['production_commit'],closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_exemptions=len(exempt))))
