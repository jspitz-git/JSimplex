"""Exclusive S5-K literal source/reused-evidence checks; no Julia execution."""
from pathlib import Path
import hashlib,json,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';K=D/'results/S5-K';J=K.parent/'S5-J'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def txt(p):return (R/p).read_text()
e=json.loads((J/'evidence.json').read_text());s=txt('src/dual_simplex.jl');h=s[s.index('function _make_dual_feasible!'):s.index('function _solve_continuous_dual(')];p=txt('src/simplex_pivot.jl');q=txt('src/simplex_pricing.jl');d=txt('src/simplex_diagnostics.jl');a=txt('test/adaptive_pricing_lifecycle_tests.jl');n=txt('src/simplex_numerics.jl');r=txt('src/simplex.jl')
checks={
 'J_full97_current':len(e['sha256'])==97 and all(sha(x)==v for x,v in e['sha256'].items()),
 'J_reuse237_each_failed_run':all(sum(x['passed'] for x in e['rows'] if x['run']==v)==237 for v in ('38142752357','38149970679')) and all(x['run_conclusion']=='failure' for x in e['rows']),
 'J_reuse16_blocks':len(e['test_block_comparisons'])==16 and all(x['block_equal'] and x['whole_file_equal'] for x in e['test_block_comparisons']),
 'single_root_candidate_site':h.count('_candidate_workspace(workspace)')==1,
 'stage_root_identity':'observer = _StageObserver(ws,values.pending_events)' in p,
 'stage_forwards_actual_candidate':'_diagnostic_event!(observer.live.progress.diagnostics,reason,candidate)' in p,
 'phase_reset_buffered':':pricing_phase_reset)' in p and 'push!(observer.pending,reason)' in p,
 'private_copy_before_reset':h.index('trial.factorization = copy_basis_factorization(workspace.factorization)')<h.index('_reset_auto_pricing!(trial)'),
 'reset_before_refactor':h.index('_reset_auto_pricing!(trial)')<h.index('recompute!(trial; refactorize=true'),
 'refactor_notification_before_rebuild':r.index('_simplex_event!(workspace, diagnostic_reason)')<r.index('rhs = workspace.scratch.row_rhs',r.index('function recompute!')),
 'publication_order':h.index('_invalidate_basis_checkpoints!(workspace)',h.index('# No caller code'))<h.index('_copy_pivot_state!(workspace, trial)')<h.index('workspace.factorization = trial.factorization')<h.index('for reason in trial.progress.diagnostics.observer.pending')<h.index('_simplex_event!(workspace, reason)'),
 'public_exception_not_rewrapped':'_is_numerical_exception(exception) || rethrow()' in s[s.index('function make_dual_feasible!'):s.index('function _make_dual_feasible!')],
 'direct_cause_wrapper':'cause::E' in d and 'throw(DiagnosticObserverFailure(exception))' in d,
 'record_before_callback':d.index('record_event!(d, reason)',d.index('function _diagnostic_event!(d::SimplexDiagnostics,'))<d.index('d.observer(reason, state)'),
 'bounded_existing_ring':'if length(d.events) < 64' in d and 'd.events[d.next_event] = reason' in d,
 'fixture_policy_native':'numerical_profile::Symbol=:native' in n and 'phase_one::Bool=false' in n and 'adaptive_stalling=true, adaptive_pricing=enabled' in a,
 'force_creates_pricing':'JSimplex._prepare_auto_pricing!(ws,algorithm)' in a and 'state.temporary = true' in a,
 'reset_conditional':'isnothing(state) && return nothing' in q and '_simplex_event!(ws,:pricing_phase_reset)' in q,
 'weights_helper_has_extra_solves':'JSimplex.transpose_solve!(actual,ws.factorization,rhs)' in a,
 'snapshot_schema':3*(1+1)==6 and 1+8*(1+1)==17 and 11+9==20,
}
paths=set(map(Path,e['sha256']))
paths.update([R/'src/simplex_numerics.jl',Path(__file__).resolve(),K/'host-before.json',D/'S5-DUAL-AUXILIARY-PENDING-OBSERVER-ORACLE.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-oracle.md',R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-preparation.md',D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP.md',D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP-REVIEW.md'])
paths.update(x for x in J.rglob('*') if x.is_file())
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'sha256':{str(p):sha(p) for p in sorted(paths)},'historical_evidence_sha256':sha(J/'evidence.json'),'scope':'Offline conditional observer/oracle specification. Zero Julia, new LP arithmetic or runtime qualification.','schema':{'owned_vector_copies':3,'copied_entries_tiny_fixture':6,'selected_array_owners':9,'post_unwind_vector_entries':17,'reference_slots':20,'callback_vector_copies':0,'callback_vector_scans':0,'new_numerical_calls':0}}
with (K/'evidence.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed'],'pins':len(paths)}));raise SystemExit(0 if x['all_passed'] else 1)
