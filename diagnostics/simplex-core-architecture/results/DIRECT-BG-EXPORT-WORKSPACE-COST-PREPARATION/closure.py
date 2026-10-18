"""Fresh cost-result closure; independent reviews required; no numerical rerun."""
from pathlib import Path
import sys,json,hashlib,subprocess
E=Path(__file__).resolve().parent;D=E;sys.path.insert(0,str(D));import control as c
R=c.R;run=D/'runs/cost1-300';checks={}
def ck(v,n):checks[n]=bool(v)
names=c.rd(E/'publication-names.json')['names'];future={str((E/n).relative_to(R)) for n in ('closure.json','publication.json')}
ck(c.rd(run/'audit.json')['all_passed'] and not c.rd(run/'audit.json')['pure_timeout'],'cost_correctness_integrity_audit_accepted')
p=c.rd(E/'postcheck.json');ck(p['all_passed'] and all(p['checks'].values()) and c.bindings(p),'author_postcheck_and_bindings')
files,groups=c.result_review('cost1-300','BG export workspace cost result','result-review.json');ck(True,'independent_exact_result_review');rv=c.rd(run/'result-review.json');ck(bool(rv.get('evidence_sha256')) and c.bindings(rv,'evidence_sha256'),'independent_result_evidence_bindings')
s=c.rd(run/'sealed.json');ad=c.rd(run/'admission.json');c.verify_review(ad,run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG export workspace cost admission','cost1-300');ck(True,'exact_admission_and_evidence_bindings')
c.preparation();c.validate_sources();ck(True,'preparation_runtime_sources_stages')
h=c.full_host(groups);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(E/'host-closure.json',h)
ck(c.host_safe(h) and h['boot_id']==s['boot_id'] and set(groups)<=set(h['groups']),'fresh_full_groups_sessions_closure')
ck(h['head']==s['head']=='6fb6539c07262ae9adc237a4d90488da6fac2c61' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture','refs_unchanged')
ck(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'remote_refs')
ck(not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'no_tracked_changes')
ck(all(line in h['status'].splitlines() for line in c.rd(E/'host.json')['status'].splitlines()),'existing_untracked_preserved')
actual={str(p.relative_to(R)) for root in (E,) for p in root.rglob('*') if p.is_file()}
ck(len(names)==len(set(names)) and actual==set(names)-future,'exact_new_diagnostic_files')
ck(all(n.startswith(str(E.relative_to(R))+'/') for n in names),'only_cost_diagnostics_scope')
ck({x.name for x in (D/'runs').iterdir()}=={'cost1-300'},'one_cost_attempt_only')
from analysis import first_process_viable
ck(not first_process_viable(c.rd(run/'audit.json'),c.rd(D/'inputs.json')['fixtures']) and rv.get('performance_accepted') is False and rv.get('second_process_allowed') is False,'fixed_design_cost_rejected_no_second_process')
ck(c.bindings(c.rd(E/'prepublication-inputs.json')),'final_text_bindings')
out=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Correctness accepted; fixed design cost rejected; no second process or production integration')
c.save(E/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve')
