"""Exclusive literal/order evidence for a design rejection, not Julia parsing."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;pins={}
def read(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
s=read(R/'src/simplex.jl');o=read(R/'src/solver.jl');r=read(R/'src/simplex_recovery.jl');p=read(R/'src/simplex_precision_recovery.jl');d=read(R/'src/simplex_diagnostics.jl');n=read(R/'src/simplex_numerics.jl');h=read(R/'src/hypersparse_pipeline.jl')
cl=o[o.index('function cleanup_original('):o.index('function _remaining_options(')];init=s[s.index('function _initialize_workspace_state('):s.index('function primal_infeasibility_summary')]
c={
'constructor_zero_and_unit':all(t in init for t in ['zeros(T, variable_count)','ones(T, variable_count)','SimplexScratch(T, row_count, variable_count)','initial_basis = spdiagm']),
'finish_before_initial_event':init.index('recompute!(workspace)')<init.index('_simplex_event!(workspace, :refactor_initial)'),
'ordinary_assignment_after_initializer_return':'workspace = initialize_workspace(_minimization_problem(problem), options; progress)' in cl and 'workspace = nothing' in cl,
'deadline_after_initialization':cl.index('workspace = initialize_workspace')<cl.index('stop_requested() && return')<cl.index('workspace.basis = Basis'),
'context_policy_override':'isnothing(context.numerical_policy) ? NumericalPolicy(T,options) : context.numerical_policy' in o,
'dual_clock_sources':'_SolveDeadline(context.start_ns, context.time_limit_seconds)' in o and '_BasisSolveClock(ws.progress.start_ns,ws.options.time_limit)' in r,
'refinement_early_return':'policy.solve_refinement || return true' in r,
'policy_overrides':all(t in n for t in ['solve_refinement::Bool=(numerical_profile == :checked)','recovery::Bool=(numerical_profile == :checked)','hypersparse::Bool=false']),
'native_predicate_limited':'!(policy.pivot_validation || policy.recovery || policy.incremental_primal ||\n      policy.incremental_primal_pivots)' in n,
'diagnostics_record_without_observer':d.index('record_event!(d, reason)',d.index('function _diagnostic_event!'))<d.index('if !isnothing(d.observer)'),
'kernel_accounting_finally':'finally\n        diagnostics.kernel_nanoseconds[reason]' in d,
'null_recovery':'_recover_original_failure(::Nothing,run,stop) = run' in p,
'ordinary_recovery_no_dispatch':'!(policy.precision_boosting || policy.lp_refinement)' in p,
'prior_work_on_failure':'isnothing(workspace) ? prior_iterations : workspace.iterations' in cl,
'original_guard_identity':'exception === stop_requested.exception && rethrow()' in cl,
'refactor_log_independent_verbose':'@logmsg workspace.options.log_level "Refactorizing basis"' in s,
'event_precedes_solves':s.index('_simplex_event!(workspace, diagnostic_reason)')<s.index('basic_primal = _checked_basis_solve!'),
'hypersparse_policy_branch':'if !ws.progress.numerical_policy.hypersparse' in h and '_invalidate_prepared_destination!' in h,
'projection_failure_reconstructs':'workspace.basis = Basis(restored_basis.basic_indices, restored_basis.states)\n                recompute!' in cl,
}
for f in ['src/refactorization_policy.jl','src/factorization.jl','src/markowitz_factorization.jl','test/unscaled_cleanup_tests.jl','test/postsolve_cleanup_performance_tests.jl','test/postsolve_hint_tests.jl','test/native_cleanup_recovery_tests.jl'] :read(R/f)
for name in ['S5-ENTRY.md','S5-ENTRY-REVIEW.md','S5-RESTORATION.md','S5-COPIES.md','S5-HANDOFF-COVERAGE-RECONCILIATION.md','S5-CLEANUP-ENTRY-REUSE-DECISION.md']:read(D/name)
for name in ['2026-10-11-simplex-core-architecture.md','2026-10-13-cleanup-entry-reuse-design-decision.md','2026-10-13-test-mps-failure-provenance.md']:read(R/'docs/superpowers/plans'/name)
read(H/'read-selector-failures.md');read(__file__)
with (H/'source-check.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=pins,scope='Literal source/design evidence only; no Julia parsing or execution'),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,hashes=len(pins))));assert all(c.values())
