from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl/diagnostics/dual-recovery-devex-production-integration/2026-10-30');T=Path('/tmp/devex-production-integration-20261030');sys.path.insert(0,str(D));import common as C
h=C.host();pins=C.read(C.R/'pins.json');audit=C.read(C.R/'audit.json');done=C.read(C.R/'completion.json');attempt=C.read(C.R/'attempt.json');proc=C.read(C.R/'guard/process.json');ad=C.read(attempt['admission_path']);owners=[attempt['runner'],proc['runner'],proc['child']];C.verify_pins(pins)
checks=dict(all_pins_unchanged=True,full745_groups_and_sessions_noJulia=len(h['checked_groups'])==745 and not h['still_active_current_launcher'] and not h['conflicts'] and set(h['checked_groups'])==C.groups(h['boot_id'],True),all_audit_bindings=all(C.sha(p)==v for p,v in audit['bindings'].items()),admission_bound=C.sha(attempt['admission_path'])==attempt['admission_sha256'] and C.sha(ad['review_report'])==ad['review_report_sha256'],actual_prior_time_not_reset=C.prior_time()==1108.3747013349202 and done['total_inclusive_seconds']==C.prior_time()+done['elapsed_inclusive_seconds']<=1800,production_commit_and_user_files=h['refs']['master']==C.read(D/'integration.json')['production_commit'])
if audit['accepted']:
 q=C.read(C.R/'closed.json');expected={str(p) for p in C.R.rglob('*') if p.is_file() and p.name!='closed.json'};expected.update((attempt['admission_path'],ad['review_report']));checks['exact_closed_membership']=q['accepted'] is True and set(q['bindings'])==expected and all(C.sha(p)==v for p,v in q['bindings'].items())
else:checks['no_false_success_closed']=not (C.R/'closed.json').exists()
samples=[json.loads(s) for s in (C.R/'guard/resources.jsonl').read_text().splitlines()];checks['all_sample_terminal_current_resources']=bool(samples) and all(type(s['available_kib']) is int and s['available_kib']>=6*1024**2 and type(s['swap_used_kib']) is int and s['swap_used_kib']<=1024**2 for s in [*samples,proc['terminal_memory'],h['memory']]);C.require(all(checks.values()),str(checks));portable={};external={}
for p in sorted(C.R.rglob('*')):
 if p.is_file():
  dst=D/'master-1'/p.relative_to(C.R);dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(p.read_bytes())
  C.require(C.sha(p)==C.sha(dst),'runtime copy');portable[str(p)]=dict(copy=str(dst),sha256=C.sha(p))
for p in [T/'PLAN.md',T/'preparation-path-note.json',T/'admission-check.py',T/'prelaunch-host.json',Path(attempt['admission_path']),Path(ad['review_report'])]:
 dst=D/'external'/p.relative_to('/tmp');dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(p.read_bytes())
 external[str(p)]=dict(copy=str(dst),sha256=C.sha(p));C.require(C.sha(dst)==C.sha(p),'external copy')
for n,v in ad['bindings'].items():
 p=Path(n)
 if p.is_relative_to('/tmp') and n not in external:
  dst=D/'admission-review-artifacts'/p.relative_to('/tmp');dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(p.read_bytes())
  C.require(C.sha(dst)==C.sha(p)==v,'review copy');external[n]=dict(copy=str(dst),sha256=v)
result=dict(accepted=True,scope='postexit integrity/full closure, numerical acceptance is separately canonical audit',checks=checks,host=h,closed_owner_identities=owners,portable=portable,external_exact_copies=external,pin_count=len(pins['inventory']),canonical_audit_accepted=audit['accepted'],test_summary=audit['test_summary'],audit_error=audit['error'],process_exit=proc['returncode'],elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],total_inclusive_seconds=done['total_inclusive_seconds'],remaining_seconds=1800-done['total_inclusive_seconds'],resource_samples=len(samples),min_available_kib=min(s['available_kib'] for s in samples),max_swap_used_kib=max(s['swap_used_kib'] for s in samples),child_maxrss_kib=proc['child_maxrss_kib'],warnings=[s for s in (C.R/'guard/run.log').read_text().splitlines() if s.startswith('WARNING:')]);C.fresh(D/'postcheck.json',result);shutil.copyfile(__file__,D/'postcheck.py');print(json.dumps({k:result[k] for k in ('accepted','pin_count','canonical_audit_accepted','test_summary','audit_error','process_exit','elapsed_inclusive_seconds','total_inclusive_seconds','remaining_seconds','resource_samples','min_available_kib','max_swap_used_kib','child_maxrss_kib')}));print('checks',len(checks),'runtime',len(portable),'external',len(external))
