"""Close a preserved FAILED RED qualification; does not accept it for GREEN."""
from pathlib import Path
import sys,json
Q=Path(__file__).resolve().parent;D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');R=Q.parents[3];RUN=D/'runs/red300'
sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):checks[n]=bool(v)
a=c.rd(RUN/'audit.json');rv=c.rd(RUN/'result-review.json');s=c.rd(RUN/'sealed.json')
ck('qualification_rejected',rv.get('accepted') is False and rv.get('qualification_accepted') is False and a['all_passed'] is False and a['pure_timeout'] is False)
ck('diagnostic_review_accepted',rv.get('diagnostic_review_accepted') is True and rv.get('findings')==[] and rv.get('scope')=='BG specialization RED failed-attempt diagnostic review' and rv.get('phase')=='red300')
files={str(p) for p in RUN.rglob('*') if p.is_file() and p!=RUN/'result-review.json'}
ck('exact_result_review_membership',set(rv.get('sha256',{}))==files)
ck('result_review_bindings',bool(rv.get('sha256')) and c.bindings(rv) and c.bindings(rv,'evidence_sha256'))
c.verify_review(c.rd(RUN/'admission.json'),RUN/'sealed.json',s['files']+[str(RUN/'sealed.json')],'BG specialization exact-stage admission','red300');ck('exact_admission',True)
ck('sealed_and_launch_inputs_unchanged',c.guard.pins_match(s) and c.guard.pins_match(c.rd(RUN/'launch-pins.json')))
c.preparation();c.validate_sources();ck('frozen_preparation_source_stage_runtime',True)
ck('old_publication_unchanged',c.bindings(c.rd(D/'publication.json')))
outer=c.rd(Q/'outer-closure.json');ck('outer_closure',outer['all_passed'] and c.host_safe(outer['host']) and c.bindings(outer))
ck('no_other_phase',{p.name for p in (D/'runs').iterdir()}=={'red300'})
ck('original_false_audit_unchanged',c.bindings(a) and 'Measured compilation' in a['error'])
ck('process_exit2_not_timeout',c.rd(RUN/'output/process.json')['returncode']==2 and c.rd(RUN/'output/process.json')['reason']=='exit2')
for phase in ['green300','red600']:
 try:c.predecessor(phase);rejected=False
 except (RuntimeError,FileNotFoundError):rejected=True
 ck('predecessor_rejects_'+phase,rejected)
h=c.full_host(outer['host']['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'),memory=c.guard.memory());c.save(Q/'host-closure.json',h)
ck('full259groups_sessions_noJulia',c.host_safe(h) and set(outer['host']['groups'])==set(h['groups']) and len(h['groups'])==259 and h['boot_id']==outer['host']['boot_id'])
ck('refs',h['head']=='e780e6158ea5365adf5cde36dceaa8032a34fe9c' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture')
ck('remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_unchanged',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
names=c.rd(Q/'publication-names.json')['names'];future={str((Q/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for root in [Q,RUN] for p in root.rglob('*') if p.is_file()}
ck('exact_files',len(names)==len(set(names)) and actual==set(names)-future)
ck('diagnostic_scope',all(n.startswith(str(Q.relative_to(R))+'/') or n.startswith(str(RUN.relative_to(R))+'/') for n in names))
out=dict(all_passed=all(checks.values()),checks=checks,qualification_accepted=False,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Diagnostic preservation/closure PASS only. RED qualification rejected; no GREEN or retry admission.')
c.save(Q/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve')
