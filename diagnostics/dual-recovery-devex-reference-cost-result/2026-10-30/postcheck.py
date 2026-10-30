from pathlib import Path
import sys,json,shutil,tomllib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';T=Path('/tmp/devex-reference-cost-run-20261030');D=W/'diagnostics/dual-recovery-devex-reference-cost-result/2026-10-30'
sys.path.insert(0,str(P));import common as C
phase='reference-cost';r=C.out(phase);seal=C.read(r/'seal.json');pins=C.read(r/'pins.json');attempt=C.read(r/'attempt.json');proc=C.read(r/'guard/process.json');sup=C.read(r/'supervisor.json');done=C.read(r/'completion.json');audit=C.read(r/'audit.json');h=C.host()
owners=[attempt['runner'],proc['runner'],proc['child']]
checks={
'full739groups_and_sessions_noJulia':h['conflicts']==[] and not h['still_active_current_launcher'] and len(h['checked_groups'])==739 and set(h['checked_groups'])==C.expected_groups(phase,h['boot_id'],True),
'head_master_unchanged':h['refs']['HEAD']==seal['head']=='d618023b27a42170438c26995c50a036af01c2b4' and h['refs']['master']==h['refs']['origin/master']==C.MASTER,
'tracked_tree_index_clean':not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only'),
'complete_inventory_hash_targets':all(C.sha(p)==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),
'guard_pin_manifest':C.read(r/'guard/pins.json')==pins and C.sha(r/'pins.json')==seal['pins_sha256']==proc['pins_sha256'],
'original_time_charged':C.prior(phase)[0]==seal['used_seconds']==1033.6005972509156 and done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds']<=1800,
'canonical_audit_bindings_unchanged':all(C.sha(p)==h for p,h in audit['bindings'].items()),
'no_candidate_reservation':not C.out('candidate-cost').exists()}
ad=C.read(attempt['admission_path'])
checks['admission_bound']=ad['accepted'] is True and C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(ad['review_report'])==ad['review_report_sha256']
samples=[json.loads(s) for s in (r/'guard/resources.jsonl').read_text().splitlines()]
checks['all_sample_terminal_current_resources']=bool(samples) and all(type(q['available_kib']) is int and type(q['swap_used_kib']) is int and q['available_kib']>=6*1024**2 and q['swap_used_kib']<=1024**2 for q in [*samples,proc['terminal_memory'],h['memory']])
if audit['accepted']:
 C.validate_closed(phase);checks['canonical_standalone_closed']=True
else:
 checks['no_false_success_closure']=not (r/'closed.json').exists()
C.require(all(checks.values()),'postcheck integrity/closure failure '+str(checks))
D.mkdir(parents=True,exist_ok=False);portable={};external={}
for p in sorted(r.rglob('*')):
 if p.is_file():
  dst=D/'reference-cost'/p.relative_to(r);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst),'portable mismatch');portable[str(p)]=dict(copy=str(dst),sha256=C.sha(p))
for p in [T/'preflight.py',T/'preflight.json',T/'admission-check.py',T/'prelaunch-full-host.json',Path('/tmp/devex-reference-cost-numerical-admission.json'),Path('/tmp/devex-reference-cost-numerical-admission.md')]:
 C.require(p.is_file(),'missing external');dst=D/p.name;shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst),'external mismatch');external[str(p)]=dict(copy=str(dst),sha256=C.sha(p))
for n,digest in ad['bindings'].items():
 p=Path(n)
 if p.is_relative_to('/tmp') and n not in external:
  dst=D/'admission-review-artifacts'/p.relative_to('/tmp');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst)==digest,'review artifact mismatch');external[n]=dict(copy=str(dst),sha256=digest)
log=(r/'guard/run.log').read_text(errors='replace')
result=dict(accepted=True,scope='postexit reference integrity/full launcher-group-session closure only; numerical outcome remains canonical audit',checks=checks,host=h,closed_owner_identities=owners,checked_groups=h['checked_groups'],pin_count=len(pins['inventory']),portable=portable,external_exact_copies=external,canonical_audit_accepted=audit['accepted'],test_summary=audit['test_summary'],audit_error=audit['error'],process_exit=proc['returncode'],process_reason=proc['reason'],elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],total_inclusive_seconds=done['total_inclusive_seconds'],remaining_seconds=1800-done['total_inclusive_seconds'],resource_samples=len(samples),min_available_kib=min(q['available_kib'] for q in samples),max_swap_used_kib=max(q['swap_used_kib'] for q in samples),warnings=[s for s in log.splitlines() if s.startswith('WARNING:')])
C.fresh(D/'postcheck.json',result);shutil.copyfile(__file__,D/'postcheck.py')
print(json.dumps({k:result[k] for k in ['accepted','pin_count','canonical_audit_accepted','test_summary','audit_error','process_exit','elapsed_inclusive_seconds','total_inclusive_seconds','remaining_seconds','resource_samples','min_available_kib','max_swap_used_kib','warnings']}))
print('full_groups',len(h['checked_groups']),'checks',len(checks),'portable',len(portable))
