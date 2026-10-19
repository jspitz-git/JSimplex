"""Separate publication closure for one admitted first Task3 cost process; no numerical/auditor rerun."""
from pathlib import Path
import sys,json
Q=Path(__file__).resolve().parent;P=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-COST');R=Q.parents[3];sys.path.insert(0,str(P));import control as c
run=P/'runs/cost1-300';outer=P/'outers/cost1-300';checks={}
def ck(n,v):checks[n]=bool(v)
v=c.rd(run/'result-review.json');a=c.rd(run/'audit.json');post=c.rd(Q/'postcheck.json');s=c.rd(run/'sealed.json');oc=c.rd(run/'outer-closure.json')
files={str(p) for p in run.rglob('*') if p.is_file() and p!=run/'result-review.json'}
ck('result_review_exact_membership',set(v['sha256'])==files and c.bindings(v) and v.get('findings')==[] and v.get('phase')=='cost1-300')
if 'evidence_sha256' in v:ck('result_review_evidence',c.bindings(v,'evidence_sha256'))
ck('diagnostic_or_successful_acceptance',v.get('accepted') is True or v.get('diagnostic_review_accepted') is True)
ck('exact_cost_result_scope',v.get('scope')=='BG specialized export cost result')
ck('author_postcheck_passed',post.get('all_passed') is True and all(post['checks'].values()))
ck('first_process_gate_agreement',v.get('first_process_viable') is post['first_process_viable'])
ck('expected_result_agreement',v.get('accepted') is bool(a['all_passed']) and post['audit_all_passed'] is a['all_passed'])
c.verify_review(c.rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG specialized export cost admission','cost1-300');ck('exact_admission',True)
ck('seal_and_launch_pins',c.guard.pins_match(s) and c.guard.pins_match(c.rd(run/'launch-pins.json')))
ck('saved_audit_hashes',c.bindings(a));ck('saved_postcheck_hashes',c.bindings(post))
c.validate_result_closure('cost1-300',oc);ck('exact_external_outer_closure',True)
ck('old_preparation_publication_preserved',c.bindings(c.rd(P/'publication.json')) and c.bindings(c.rd(P/'closure.json')))
c.validate_environment();c.validate_sources();ck('sources_environment_runtime',True)
h=c.full_host(oc['host']['groups']);h.update(memory=c.guard.memory(),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(Q/'host-closure.json',h)
e=c.rd(Q/'host-entry.json');ck('fresh_groups_sessions_noJulia',c.host_safe(h) and set(oc['host']['groups'])<=set(h['groups']) and h['boot_id']==e['boot_id'])
ck('refs_remote',h['head']==e['head']=='e149671cd2c9560ae2a91b80614d36799b845240' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture' and h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('accepted_GREEN_predecessor_preserved',bool(c.predecessor('cost1-300')[0]))
names=c.rd(Q/'publication-names.json')['names'];future={str((Q/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for root in [Q,run,outer] for p in root.rglob('*') if p.is_file()}
ck('exact_publication_names',len(names)==len(set(names)) and actual==set(names)-future)
ck('preserved_prior_untracked',all(x in h['status'].splitlines() for x in e['status'].splitlines()))
record=dict(all_passed=all(checks.values()),checks=checks,first_process_viable=post['first_process_viable'],sha256={n:c.sha(R/n) for n in names if n not in future},scope='Diagnostic integrity/closure of one Task3 cost process; ALL8 cost gates separate, whole two-process qualification not established')
c.save(Q/'closure.json',record);print(json.dumps(dict(all_passed=record['all_passed'],first_process_viable=record['first_process_viable'],checks=len(checks),bindings=len(record['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(record['all_passed'],'Closure failed; preserve and stop')
