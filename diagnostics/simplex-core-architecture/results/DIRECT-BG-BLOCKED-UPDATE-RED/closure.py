"""Close the failed RED diagnostic record only; never rerun numerical controls."""
from pathlib import Path
import sys,json,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');sys.path.insert(0,str(H));import control as c
run=H/'runs/red300';outer=H/'outers/red300';checks={}
def ck(n,v):
 checks[n]=bool(v);c.require(v,n)
s=c.rd(run/'sealed.json');rv=c.rd(D/'result-review.json')
ck('independent_diagnostic_acceptance',rv.get('accepted') is True and rv.get('qualification_accepted') is False and rv.get('findings')==[])
ck('independent_bindings',c.bindings(rv))
if 'evidence_sha256' in rv:ck('independent_evidence',c.bindings(rv,'evidence_sha256'))
ck('no_false_accepted_predecessor',not (run/'result-review.json').exists())
ck('frozen_seal',c.guard.pins_match(s));c.validate_sources();ck('production_and_stage_unchanged',True)
cl=c.rd(run/'outer-closure.json');ck('external_closure',c.validate_result_closure('red300',cl))
h=c.full_host(cl['host']['groups']);h['memory']=c.guard.memory();c.save(D/'host-closure.json',h)
ck('fresh_host',c.host_safe(h) and not c.guard.pressure(h['memory']))
ck('same_refs_boot',all(h[k]==s[k] for k in ['head','master','boot_id']))
ck('clean_tracked_and_index',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
a=c.rd(run/'audit.json');p=c.rd(run/'output/process.json');summary=c.rd(D/'summary.json')
ck('failed_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and 'Missing raw/units' in a['error'] and c.bindings(a))
ck('one_non_timeout_attempt',p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True and p['elapsed_including_launch']<300 and not (H/'runs/green300').exists())
ck('no_assertion_coverage',summary['units_saved']==0 and summary['raw'] is None and summary['qualification_pass'] is False)
ck('summary_bindings',c.bindings(summary))
ck('source_diagnosis',c.rd(D/'source-diagnosis.json')['all_passed'] is True and c.bindings(c.rd(D/'source-diagnosis.json')))
ck('outer_failed_closed',c.rd(outer/'outer-outcome.json')['returncode']==2)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
ck('continuation_snapshot',ledger.read_bytes()==(D/'progress.md.after-red').read_bytes() and (D/'progress.md.before-red').is_file())
names=c.rd(D/'publication-names.json')['paths'];actual={str(p.relative_to(R)) for root in [D,run,outer] for p in root.rglob('*') if p.is_file()}
expected=set(names)-{str((D/n).relative_to(R)) for n in ['closure.json','publication.json']}
ck('exact_package',actual==expected and len(names)==len(set(names)))
c.save(D/'closure.json',dict(all_passed=True,qualification_accepted=False,checks=checks,sha256={n:c.sha(R/n) for n in sorted(actual)},scope=__doc__))
print('Diagnostic closure PASS',len(checks),'checks',len(actual),'bindings')
