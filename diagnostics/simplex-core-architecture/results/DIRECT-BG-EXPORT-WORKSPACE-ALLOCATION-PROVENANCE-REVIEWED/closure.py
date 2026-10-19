"""Fresh offline provenance closure; no Julia or old auditor rerun."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
R=c.R;A=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE');run=D/'runs/profile300';checks={}
def ck(v,n):checks[n]=bool(v)
rv=c.rd(run/'result-review.json');reviewfiles=sorted(str(p) for p in run.rglob('*') if p.is_file() and p.name!='result-review.json')
ck(rv.get('accepted') is True and rv.get('findings')==[] and rv.get('scope')=='BG export allocation provenance result','independent_result_accepted')
ck(set(rv['sha256'])==set(reviewfiles) and c.bindings(rv),'exact_result_review_bindings')
ck(bool(rv.get('evidence_sha256')) and c.bindings(rv,'evidence_sha256'),'independent_evidence_bindings')
ck(rv.get('performance_accepted') is False,'no_performance_promotion')
audit=c.rd(run/'audit.json');ck(audit['all_passed'] and c.bindings(audit),'one_shot_audit_and_bindings')
attr=c.rd(D/'attribution.json');ck(attr['all_passed'] and all(attr['checks'].values()) and c.bindings(attr) and attr['script_sha256']==c.sha(D/'attribution.py'),'exact_stack_attribution')
s=c.rd(run/'sealed.json');c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG export allocation provenance admission','profile300');ck(True,'independent_admission')
c.preparation();c.validate_sources();c.validate_environment();ck(c.guard.pins_match(s) and c.guard.pins_match(c.rd(run/'launch-pins.json')),'frozen_sources_runtime_launch_pins')
ck(not (A/'runs/profile300/reservation.json').exists() and c.rd(A/'review-rejected.json')['accepted'] is False,'initial_rejection_preserved_unattempted')
ck(list((D/'runs').iterdir())==[run] and c.rd(run/'reservation.json')['one_attempt'],'one_new_profile_attempt')
h=c.full_host(c.rd(run/'posthost.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(D/'host-closure.json',h)
ck(c.host_safe(h) and set(c.rd(run/'posthost.json')['groups'])<=set(h['groups']) and h['boot_id']==s['boot_id'],'fresh_groups_sessions_resources')
ck(h['head']==s['head']=='ed3d83e73478b4af00a40dd7e7dc02d5029b159d' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture','refs_unchanged')
ck(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'remote_refs_unchanged')
ck(not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'no_tracked_changes')
ck(all(line in h['status'].splitlines() for line in c.rd(A/'host.json')['status'].splitlines()),'prior_untracked_preserved')
names=c.rd(D/'publication-names.json')['names'];future={str((D/n).relative_to(R)) for n in ['closure.json','publication.json']}
actual={str(p.relative_to(R)) for root in [A,D] for p in root.rglob('*') if p.is_file()}
ck(len(names)==len(set(names)) and actual==set(names)-future,'exact_new_files')
ck(all(any(n.startswith(str(root.relative_to(R))+'/') for root in [A,D]) for n in names),'diagnostic_scope_only')
ck(c.bindings(c.rd(D/'prepublication-inputs.json')),'final_report_review_bindings')
out=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Allocation sites established; frozen candidate and old performance rejection unchanged')
c.save(D/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve')
