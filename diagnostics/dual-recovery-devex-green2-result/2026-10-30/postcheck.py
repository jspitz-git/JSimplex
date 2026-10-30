from pathlib import Path
import sys,json,shutil,tomllib,math
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30';T=Path('/tmp/devex-green2-run-20261030');D=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30'
sys.path.insert(0,str(P));import common as C
R=C.OUT;seal=C.read(R/'seal.json');pins=C.read(R/'pins.json');attempt=C.read(R/'attempt.json');proc=C.read(R/'guard/process.json');sup=C.read(R/'supervisor.json');done=C.read(R/'completion.json');audit=C.read(R/'audit.json')
h=C.host()
owners=[attempt['runner'],proc['runner'],proc['child']]
groups=set(C.read(P/'host.json')['host']['checked_groups'])
for a in owners:
 if a['boot_id']==h['boot_id']:groups.update((a['pgid'],a['sid']))
checks={
'full_prior_and_three_current_groups_sessions_absent':h['conflicts']==[] and not h['still_active_current_launcher'] and set(h['checked_groups'])==groups,
'head_master_unchanged':h['refs']['HEAD']==seal['head']=='4f5e6b9966830955637cfb7bba288b9339c9a494' and h['refs']['master']==h['refs']['origin/master']==C.MASTER,
'tracked_tree_index_unchanged':not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only'),
'all_inventory_hashes_targets_unchanged':all(C.sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),
'guard_inventory_exact':C.read(R/'guard/pins.json')==pins and C.sha(R/'pins.json')==seal['pins_sha256']==proc['pins_sha256'],
'prior_time_and_total_arithmetic':C.prior()[0]==seal['used_seconds']==527.9604928489425 and done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds'] and done['total_inclusive_seconds']<=1800,
'canonical_audit_all_available_bindings':all(C.sha(n)==v for n,v in audit['bindings'].items()),
'auditor_has_explicit_boolean':type(audit['accepted']) is bool and audit['phase']=='green2'}
ad=C.read(attempt['admission_path'])
checks['bound_admission_and_report']=ad['accepted'] is True and C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(ad['review_report'])==ad['review_report_sha256'] and ad['seal_sha256']==C.sha(R/'seal.json')
samples=[json.loads(s) for s in (R/'guard/resources.jsonl').read_text().splitlines()]
checks['all_resource_samples_and_terminal']=bool(samples) and all(type(s['available_kib']) is int and type(s['swap_used_kib']) is int and s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in [*samples,proc['terminal_memory'],h['memory']])
C.require(all(checks.values()),'postcheck integrity/closure failed '+str(checks))
D.mkdir(parents=True,exist_ok=False);portable={};external={}
for p in sorted(R.rglob('*')):
 if p.is_file():
  dst=D/'green2'/p.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst),'portable mismatch');portable[str(p)]=dict(copy=str(dst),sha256=C.sha(p))
for p in [T/'preflight.py',T/'preflight.json',T/'admission-check.py',T/'prelaunch-full-host.json',Path('/tmp/devex-green2-numerical-admission.json'),Path('/tmp/devex-green2-numerical-admission.md')]:
 C.require(p.is_file(),'missing external evidence '+str(p));dst=D/p.name;shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst),'external mismatch');external[str(p)]=dict(copy=str(dst),sha256=C.sha(p))
for n,digest in ad['bindings'].items():
 p=Path(n)
 if p.is_relative_to('/tmp') and str(p) not in external:
  dst=D/'admission-review-artifacts'/p.relative_to('/tmp');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);C.require(C.sha(p)==C.sha(dst)==digest,'review evidence mismatch');external[str(p)]=dict(copy=str(dst),sha256=digest)
log=(R/'guard/run.log').read_text(errors='replace');warnings=[s for s in log.splitlines() if s.startswith('WARNING:')]
report=dict(accepted=True,scope='postexit evidence integrity/full launcher+guard+child group/session closure; numerical outcome remains canonical audit accepted field',checks=checks,host=h,closed_owner_identities=owners,checked_groups=h['checked_groups'],pin_count=len(pins['inventory']),portable=portable,external_exact_copies=external,canonical_audit_accepted=audit['accepted'],test_summary=audit['test_summary'],audit_error=audit['error'],process_reason=proc['reason'],process_exit=proc['returncode'],elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],total_inclusive_seconds=done['total_inclusive_seconds'],remaining_seconds=1800-done['total_inclusive_seconds'],resource_samples=len(samples),min_available_kib=min(s['available_kib'] for s in samples),max_swap_used_kib=max(s['swap_used_kib'] for s in samples),warnings=warnings)
C.fresh(D/'postcheck.json',report);shutil.copyfile(__file__,D/'postcheck.py')
print(json.dumps({k:report[k] for k in ['accepted','pin_count','canonical_audit_accepted','test_summary','audit_error','process_exit','process_reason','elapsed_inclusive_seconds','total_inclusive_seconds','remaining_seconds','resource_samples','min_available_kib','max_swap_used_kib','warnings']}))
print('full_groups_sessions',len(h['checked_groups']),'checks',len(checks),'portable',len(portable))
