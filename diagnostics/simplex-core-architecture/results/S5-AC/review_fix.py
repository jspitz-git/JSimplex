"""Exclusive textual RED/GREEN correction; initial evidence remains frozen."""
from pathlib import Path
import hashlib,json
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;P=D/'S5-CLEANUP-ENTRY-REUSE-DECISION.md';before=H/(P.name+'.before-review');text=P.read_text();old='if kernel_timing=true, FTRAN/BTRAN/pricing calls.';new='if kernel_timing=true, FTRAN/BTRAN calls. The direct initial reduced-cost recomputation is not wrapped in the production pricing timer; S5-A counted that pricing request through its separate diagnostic wrapper.'
assert text.count(old)==1
with before.open('xb') as f:f.write(P.read_bytes())
assert 'Verdict: REJECTED' in (H/'review-initial.md').read_text()
source=(R/'src/simplex.jl').read_text();region=source[source.index('function recompute!('):source.index('recompute!(workspace::SimplexWorkspace, refactorize::Bool)')]
red=old in text
P.write_text(text.replace(old,new))
after=P.read_text();c={'RED_wrong_pricing_timing_claim_present':red,'GREEN_exact_single_replacement':after.replace(new,old)==text,'GREEN_two_checked_solve_calls':region.count('_checked_basis_solve!')==2,'GREEN_direct_prices_untimed':'_recompute_reduced_costs!(workspace.reduced_costs, workspace, dual)' in region and ':pricing' not in region,'GREEN_old_pin_maps_before':json.loads((H/'source-check.json').read_text())['sha256'][str(P)]==hashlib.sha256(before.read_bytes()).hexdigest(),'GREEN_rejection_preserved':'Verdict: REJECTED' in (H/'review-initial.md').read_text()}
paths=[P,before,H/'review-initial.md',R/'src/simplex.jl',R/'src/simplex_recovery.jl',Path(__file__)]
with (H/'review-fix.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Single factual work-counter correction; no Julia or old auditor rerun'),f,indent=2);f.write('\n')
print(json.dumps(c));assert all(c.values())
