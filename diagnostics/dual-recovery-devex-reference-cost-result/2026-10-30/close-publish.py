from pathlib import Path
import hashlib,json,subprocess,sys,shutil,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-reference-cost-run-20261030');R=W/'.superpowers/dual-recovery-devex-task4/cost-1/reference-cost'
sys.path.insert(0,str(P));import common as C
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def fresh(p,b):
 Path(p).parent.mkdir(parents=True,exist_ok=True)
 with Path(p).open('xb') as f:f.write(b)
post=read(D/'postcheck.json');maps={};provenance={}
for group in ('portable','external_exact_copies'):
 for src,v in post[group].items():
  need(sha(src)==sha(v['copy'])==v['sha256'],'prior exact copy changed '+src);maps[src]=v['copy'];provenance[v['copy']]=dict(source=src,sha256=v['sha256'])
for src,name in [('/tmp/devex-reference-cost-result-review.md','REVIEW-FINAL.md'),('/tmp/devex-reference-cost-result-review.json','review-final.json'),(str(T/'write-report.py'),'write-report.py')]:
 dst=D/name;fresh(dst,Path(src).read_bytes());maps[src]=str(dst);provenance[str(dst)]=dict(source=src,sha256=sha(src))
review=read(D/'review-final.json');table=review['bindings']
for src,h in table.items():
 need(sha(src)==h,'review original binding '+src)
 if Path(src).is_relative_to('/tmp') and src not in maps:
  dst=D/'result-review-artifacts'/Path(src).relative_to('/tmp');fresh(dst,Path(src).read_bytes());need(sha(dst)==h,'review copy '+src);maps[src]=str(dst);provenance[str(dst)]=dict(source=src,sha256=h)
audit=read(R/'audit.json');closed=read(R/'closed.json');pins=read(R/'pins.json');ad=read(R/'numerical-admission.json');done=read(R/'completion.json');data=tomllib.loads((R/'result.toml').read_text());h=C.host();C.validate_closed('reference-cost')
# All facts are independently read here; this does not rerun any accepted main, auditor or numerical process.
checks={
'result_review_reference_only_accepted':review['accepted'] is True and review['scope']=='reference_cost_result_only' and review['runtime_accepted'] is True and review['cost_qualified'] is False and review['production_admission'] is False and bool(review['checks']) and all(type(v) is bool and v for v in review['checks'].values()),
'all_review_original_and_copy_bindings':all(sha(n)==sha(maps.get(n,n))==v for n,v in table.items()),
'report_binding':sha(D/'REVIEW-FINAL.md')==review.get('review_report_sha256',review.get('report_sha256')),
'canonical_audit272_exit0':audit['accepted'] is True and audit['test_summary']=={'Pass':272,'Total':272} and audit['error'] is None and post['process_exit']==0,
'canonical_audit_bindings':all(sha(n)==v for n,v in audit['bindings'].items()),
'all566_launch_pins_resolved':len(pins['inventory'])==566 and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),
'all801_numerical_admission_bindings':ad['accepted'] is True and len(ad['bindings'])==801 and all(sha(n)==v for n,v in ad['bindings'].items()),
'closed_reference_exact_membership':closed['accepted'] is True,
'postcheck11_and21_runtime_copies':post['accepted'] is True and len(post['checks'])==11 and all(post['checks'].values()) and len(post['portable'])==21,
'prior_time_not_reset':done['elapsed_inclusive_seconds']==37.39421487902291 and done['total_inclusive_seconds']==1033.6005972509156+37.39421487902291==1070.9948121299385 and 1800-done['total_inclusive_seconds']==729.0051878700615,
'all37_resource_samples_passed':post['resource_samples']==37 and post['min_available_kib']==22350896 and post['max_swap_used_kib']==0,
'fresh_full739_groups_and_sessions_noJulia':len(h['checked_groups'])==739 and not h['conflicts'] and not h['still_active_current_launcher'] and set(h['checked_groups'])==C.expected_groups('reference-cost',h['boot_id'],True),
'no_candidate_reservation':not C.out('candidate-cost').exists(),
'head_master_unchanged':git('rev-parse','HEAD')=='d618023b27a42170438c26995c50a036af01c2b4' and git('rev-parse','master')==git('rev-parse','origin/master')==C.MASTER,
'tracked_tree_index_clean':not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only')}
need(all(checks.values()),str(checks));fresh(D/'publication-host.json',(json.dumps(h,indent=2)+'\n').encode());fresh(D/'close-publish.py',Path(__file__).read_bytes())
paths=sorted(p for p in D.rglob('*') if p.is_file());exempt={}
for p in paths:
 r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 need(r.returncode in (0,1,2),'whitespace checker error')
 if r.stdout or r.stderr:
  v=provenance.get(str(p));need(v is not None and sha(p)==sha(v['source'])==v['sha256'],'authored whitespace '+str(p)+' '+r.stdout+r.stderr)
  exempt[str(p.relative_to(W))]=dict(source=v['source'],sha256=sha(p),diagnostics=r.stdout+r.stderr)
fresh(D/'closure.json',(json.dumps(dict(accepted=True,runtime_accepted=True,cost_qualified=False,production_admission=False,scope='reference_cost_result_only',checks=checks,bindings={str(p):sha(p) for p in paths},explicit_exact_copy_maps=maps,verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
names0=sorted(str(p.relative_to(W)) for p in D.rglob('*') if p.is_file());names=sorted(names0+[str((D/'publication.json').relative_to(W))]);fresh(D/'publication.json',(json.dumps(dict(accepted=True,scope='reference_cost_result_only',expected_names=names,blobs_excluding_publication={n:git('hash-object',str(W/n)) for n in names0},closure_sha256=sha(D/'closure.json'),verbatim_whitespace_exemptions=exempt),indent=2)+'\n').encode())
subprocess.run(['git','-C',str(W),'add','-f','--',*names],check=True);need(git('diff','--cached','--name-only').splitlines()==names,'exact staged names');blobs={n:git('rev-parse',':'+n) for n in names};need(all(git('hash-object',str(W/n))==v for n,v in blobs.items()),'exact staged blobs');fresh(T/'exact-staged.json',(json.dumps(dict(names=names,blobs=blobs),indent=2)+'\n').encode());print(json.dumps(dict(accepted=True,closure_checks=len(checks),review_checks=len(review['checks']),review_bindings=len(table),exact_names=len(names),exact_blobs=len(blobs),verbatim_exemptions=len(exempt))))
