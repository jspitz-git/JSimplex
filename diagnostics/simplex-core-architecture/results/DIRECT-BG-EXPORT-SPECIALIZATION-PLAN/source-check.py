"""New offline plan check; does not execute any old auditor or Julia."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED');sys.path.insert(0,str(P));import control as c
spec=R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md';plan=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md'
s=spec.read_text();p=plan.read_text();checks={}
def ck(v,n):checks[n]=bool(v)
ck(c.guard.pins_match(c.rd(P/'runs/profile300/launch-pins.json')),'previous_profile_launch_files_unchanged')
ck(c.bindings(c.rd(P/'runs/profile300/result-review.json')) and c.bindings(c.rd(P/'runs/profile300/result-review.json'),'evidence_sha256'),'previous_independent_result_bindings')
ck(c.rd(P/'runs/profile300/result-review.json')['accepted'] and not c.rd(P/'runs/profile300/result-review.json')['performance_accepted'],'diagnostic_acceptance_not_performance')
ck(c.bindings(c.rd(P/'publication.json')),'previous_exact_publication_hashes')
ck('Planning-only' in s and 'Planning only now' in p,'planning_only')
ck('No new retained fields' in s and 'No new full scans' in s,'work_memory_zero_source_increment')
ck('min(1048576,fld(P0,16))' in s and 'min(1048576,fld(P0,16))' in p,'unchanged_cache_budget')
ck('same tuple result' in p and 'same tuple' in s,'unchanged_import_result_contract')
ck('Core.Box' in s and 'Fourteen' in s and '+41' in s,'attribution_limits_preserved')
ck(all(x in p for x in ['Task1','Task2','Task3','boundary_request_equivalence','boundary_hook_order','boundary_hot_and_hook_agree']),'tasks_and_specific_tests')
ck(p.count('| `_bgxs_')==7,'seven_explicit_core_interfaces')
ck('@inline' in s and 'No duplicated numeric bodies' in p,'bounded_inlining_single_body')
ck('actual accepted GREEN2 lifecycle test source' in p and 'init=0' in p,'corrected_test_lineage')
ck('300/292' in p and '600/592' in p and 'standing' in p,'short_run_authorization_and_timeout_policy')
ck('0.95' in p and '1.10' in p and '3/7' in p and '10/14' in p,'old_performance_gates_not_relaxed')
ck(160+16+24+4==204 and 320+32+48+12==412 and 1280+192==1472 and 2560+384==2944,'copied_cost_budget_arithmetic')
ck('No third timed arm' in p and 'no automatic Profile.Allocs' in p.lower().replace('profile.allocs','Profile.Allocs'),'bounded_cost_route')
ck(not (R/'diagnostics/direct-bg-export-specialized').exists(),'no_candidate_created')
ck(not c.git('diff','--name-only','HEAD') and not c.git('diff','--cached','--name-only'),'no_tracked_changes')
files={spec,plan,Path(__file__),D/'host.json',R/'AGENTS.md'}
for dirname in ['DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED','DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION','DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION']:
 root=D.with_name(dirname)
 files.update(q for q in root.iterdir() if q.is_file() and q.suffix in ['.md','.json'])
 for q in root.glob('runs/*/result-review.json'):files.add(q)
files.update((R/'diagnostics/direct-bg-export-workspace/reproduce').glob('*.jl'))
files.update([R/'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md',R/'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'])
stage=Path(c.rd(P/'stages.json')['green']['path']);files.update(q for q in stage.rglob('*') if q.is_file())
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(q):c.sha(q) for q in sorted(files)},scope='Read-time planning bindings, not launch pins; no Julia')
c.save(D/'source-check.json',out)
print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(files),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Plan check failed; preserve')
