import sys,json,pathlib,shutil,math
W=pathlib.Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';T=pathlib.Path('/tmp/dual-recovery-devex-task4-green-20261030');D=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
sys.path.insert(0,str(P));import common as C
R=C.RUN/'green';seal=C.read(R/'seal.json');pins=C.read(R/'pins.json');proc=C.read(R/'guard/process.json');done=C.read(R/'completion.json');sup=C.read(R/'supervisor.json');attempt=C.read(R/'attempt.json')
prior=C.read(W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30/postcheck.json')
groups=set(prior['checked_groups']);identities=[attempt['runner'],proc['runner'],proc['child']]
for a in identities:
 if a['boot_id']==seal['preflight']['boot_id']:groups.update((a['pgid'],a['sid']))
host=C.host(groups)
checks={}
checks['head_master_unchanged']=host['refs']['HEAD']==seal['head']=='31415cc1eccc2d6c332ff14863e509f0d805c909' and host['refs']['master']==host['refs']['origin/master']==C.MASTER
checks['tracked_tree_and_index_clean']=not C.git('diff','HEAD','--name-only') and not C.git('diff','--cached','--name-only')
checks['all_launch_pins_and_resolutions']=all(C.sha(n)==v['sha256'] and str(pathlib.Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items())
checks['manifest_pin_and_guard_copy']=C.sha(R/'pins.json')==seal['pins_sha256']==proc['pins_sha256'] and C.read(R/'guard/pins.json')==pins
checks['all_prior_current_groups_and_sessions_closed']=len(host['checked_groups'])==len(groups) and host['conflicts']==[]
checks['shared_time_arithmetic']=done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds'] and done['total_inclusive_seconds']<=1800
samples=[json.loads(s) for s in (R/'guard/resources.jsonl').read_text().splitlines()]
checks['all_resource_samples_and_terminal']=bool(samples) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in [*samples,proc['terminal_memory'],host['memory']])
adpath=pathlib.Path(attempt['admission_path']);ad=C.read(adpath)
checks['admission_report_and_seal_bound']=ad['accepted'] is True and C.sha(adpath)==attempt['admission_sha256'] and C.sha(ad['review_report'])==ad['review_report_sha256'] and ad['seal_sha256']==C.sha(R/'seal.json') and ad['head']==seal['head']
audit=C.read(R/'audit.json') if (R/'audit.json').exists() else None
checks['canonical_audit_if_present_bound']=audit is None or (audit['accepted'] is True and all(C.sha(n)==v for n,v in audit['bindings'].items()))
C.require(all(checks.values()),'postcheck failure '+str(checks))
D.mkdir(parents=True,exist_ok=False);portable={}
for p in sorted(R.rglob('*')):
 if p.is_file():
  dest=D/'green'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);C.require(C.sha(p)==C.sha(dest),'portable mismatch');portable[str(p)]=dict(copy=str(dest),sha256=C.sha(p))
external={}
for p in [T/'preflight.py',T/'preflight.json',T/'admission-check.py',T/'prelaunch-full-host.json',pathlib.Path('/tmp/devex-task4-green-admission.md'),pathlib.Path('/tmp/devex-task4-green-admission.json')]:
 C.require(p.is_file(),'missing external '+str(p));dest=D/p.name;shutil.copyfile(p,dest);C.require(C.sha(p)==C.sha(dest),'external copy mismatch');external[str(p)]=dict(copy=str(dest),sha256=C.sha(p))
for n,digest in ad['bindings'].items():
 p=pathlib.Path(n)
 if p.is_relative_to('/tmp') and str(p) not in external:
  dest=D/'admission-review-artifacts'/p.relative_to('/tmp');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);C.require(C.sha(p)==C.sha(dest)==digest,'admission evidence copy');external[str(p)]=dict(copy=str(dest),sha256=digest)
log=(R/'guard/run.log').read_text(errors='replace');warnings=[s for s in log.splitlines() if s.startswith('WARNING:')]
report=dict(accepted=True,scope='independent postexit integrity/resources/full group closure; numerical acceptance separately follows the original canonical auditor',checks=checks,head=seal['head'],host=host,closed_owner_identities=identities,checked_groups=host['checked_groups'],portable=portable,external_exact_copies=external,process_exit=proc['returncode'],reason=proc['reason'],canonical_audit_accepted=audit is not None and audit['accepted'] is True,test_summary=None if audit is None else audit['test_summary'],elapsed_inclusive_seconds=done['elapsed_inclusive_seconds'],total_inclusive_seconds=done['total_inclusive_seconds'],remaining_seconds=1800-done['total_inclusive_seconds'],resource_samples=len(samples),min_available_kib=min(s['available_kib'] for s in samples),max_swap_used_kib=max(s['swap_used_kib'] for s in samples),warnings=warnings)
C.fresh(D/'postcheck.json',report);shutil.copyfile(__file__,D/'postcheck.py')
print(json.dumps({k:report[k] for k in ('accepted','process_exit','reason','canonical_audit_accepted','test_summary','elapsed_inclusive_seconds','remaining_seconds','resource_samples','min_available_kib','max_swap_used_kib','warnings')}));print('checked_groups',len(groups),'checks',len(checks),'portable',len(portable))
