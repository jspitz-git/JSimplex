"""One-shot diagnostic closure of failed RED2; no numerical/auditor rerun."""
from pathlib import Path
import sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c
run=H/'runs/red300';outer=c.outer_dir('red300');checks={}
def ck(n,v):c.require(v,n);checks[n]=True
v=c.rd(D/'result-review.json');ck('diagnostic_review_accepted',v.get('accepted') is True and v.get('qualification_accepted') is False and v.get('findings')==[])
ck('result_review_hashes',c.bindings(v));ck('review_evidence',c.bindings(v,'evidence_sha256') if 'evidence_sha256' in v else all(str(D/n) in v['sha256'] for n in ['independent-result.py','independent-result-evidence.json','result-review.md']))
s=c.rd(run/'sealed.json');c.verify_seal(c.config('red300'),s);ck('sealed_inventory_unchanged',c.guard.pins_match(s))
ck('launch_inventory_unchanged',c.guard.pins_match(c.rd(run/'launch-pins.json')))
c.preparation();c.validate_sources();ck('accepted_sources_unchanged',True)
cl=c.rd(run/'outer-closure.json');ck('external_closure',c.validate_result_closure('red300',cl))
a=c.rd(run/'audit.json');p=c.rd(run/'output/process.json');z=c.rd(D/'summary.json')
ck('failed_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Exact exit')" and c.bindings(a))
ck('summary_bound',c.bindings(z) and z['qualification_pass'] is False and z['counts']==[11759,1,0,0] and z['expected_N026_reached'] is False and z['allocated_bytes'] is None)
ck('non_timeout_failure',p['returncode']==2 and p['reason']=='exit2' and p['pins_unchanged'] is True and c.rd(run/'invocation.json')['elapsed_seconds']<=300)
ck('no_accepted_RED_or_GREEN',not (run/'result-review.json').exists() and not (H/'runs/green300').exists())
h=c.full_host(cl['host']['groups']);h['memory']=c.guard.memory();c.save(D/'host-closure.json',h)
ck('fresh_host',c.host_safe(h) and not c.guard.pressure(h['memory']) and len(h['groups'])==274)
ck('same_refs_boot',all(h[k]==s[k] for k in ['head','master','boot_id']))
ck('tracked_index_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';ck('continuation_preserved',ledger.read_bytes()==(D/'progress.md.after-red2-run').read_bytes())
policy=c.rd(D/'publication-policy.json');ck('verbatim_raw_preserved',c.sha(R/policy['raw'])==policy['sha256'])
names=c.rd(D/'publication-names.json')['paths'];actual={str(p.relative_to(R)) for root in [D,run,outer] for p in root.rglob('*') if p.is_file()}
ck('fixed_exact_names',len(names)==len(set(names)) and actual==set(names)-{str((D/n).relative_to(R)) for n in ['closure.json','publication.json']})
c.save(D/'closure.json',dict(all_passed=True,qualification_accepted=False,launch_admitted=False,checks=checks,sha256={n:c.sha(R/n) for n in sorted(actual)},scope=__doc__))
print('Failed RED2 diagnostic closure PASS',len(checks),'checks',len(actual),'bindings')
