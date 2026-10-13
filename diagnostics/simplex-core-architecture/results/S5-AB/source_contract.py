"""Exclusive literal/source bindings supplementary to reconciliation-2."""
from pathlib import Path
import json,hashlib,re
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;pins={}
def read(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def js(p):return json.loads(read(p))
s={f:read(R/'src'/f) for f in ['solver.jl','transformations.jl','simplex_phase_one.jl','primal_simplex.jl','simplex_precision.jl','dual_simplex.jl','simplex_driver.jl','simplex_perturbation.jl']};c={}
c['identity_presolve_can_share']='PresolveResult(problem, (), size(problem.A, 2))' in s['transformations.jl']
c['original_feasibility_separate']='_original_primal_feasible(continuous_problem, primal, typed_options.primal_tolerance)' in s['solver.jl']
c['missing_basis_retries_original']='if isnothing(run.basis)\n            run = _retry_original' in s['solver.jl']
c['primal_options_restored']='finally\n        workspace.options = original_options' in s['solver.jl']
a=s['simplex_phase_one.jl'];c['export_checks_before_adoption']=a.index('_original_primal_feasible(fresh,')<a.index('_adopt_phase_basis!(original,fresh)') and a.index('reset_devex!(fresh)')<a.index('_adopt_phase_basis!(original,fresh)')
c['mapped_basis_and_fresh_scratch']='indices = map.phase_to_original[phase.basis.basic_indices]' in a and 'ws.factorization=fresh.factorization;ws.scratch=fresh.scratch' in a
c['legacy_normalization_and_objective']='workspace.problem.objective[1:column_count] .= original.problem.objective' in s['primal_simplex.jl'] and 'policy.feasibility_recovery || recompute!(workspace; caller_guard=stop_requested)' in s['primal_simplex.jl']
a=s['simplex_precision.jl'];c['precision_owner_and_final_stop']='_copy_precision_journal!(fresh,ws.scratch.perturbations)' in a and '_simplex_event!(fresh,:refactor_other)\n    stop() && return nothing' in a
c['precision_failed_factor_work']='ws.refactorizations += 1\n        _sync_run_budget!(budget,ws)' in a
a=s['dual_simplex.jl'];c['dual_private_factor']='trial.factorization = copy_basis_factorization(workspace.factorization)' in a and 'trial.scratch.refactorization = deepcopy(workspace.scratch.refactorization)' in a
c['dual_publication_before_pending']=a.index('workspace.factorization = trial.factorization')<a.index('for reason in trial.progress.diagnostics.observer.pending')
c['original_terminal_same_budget']='for cleanup in 0:2' in s['simplex_driver.jl'] and '_run_basis_terminal!(ws,budget,policy,stop,allow_auxiliary,' in s['simplex_driver.jl']
for st,base in [('S5-A','census-1'),('S5-B','census-2')]:
 a=js(H.parent/st/(base+'-audit.json'));read(H.parent/st/(base+'-run.log'));read(H.parent/st/(base+'-reference.toml'));c[st+'_accepted_audit']=a['accepted'] is True and all(v is True for v in a['checks'].values())
for base in ['work-green-1','focused-1','trajectories-1','master-1']:
 a=js(H.parent/'S5-C'/(base+'-audit.json'));read(H.parent/'S5-C'/(base+'-run.log'));c['C_'+base]=all(v is True for v in a['checks'].values())
 if 'source' in a:
  compared={k:hashlib.sha256((R/k).read_bytes()).hexdigest()==v['sha256'] for k,v in a['source'].items() if k.startswith('src/')}
  c['C_'+base+'_production_match']=bool(compared) and all(compared.values())
# Bind all accepted-report review texts and current source/test manifest from reconciliation.
z=js(H/'reconciliation-2.json');c['reconciliation10']=z['all_passed'] is True and len(z['checks'])==10
for k,v in z['sha256'].items():read(k);assert pins[k]==v
for f in ['S5-HANDOFF-COVERAGE-RECONCILIATION.md','S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION-REVIEW.md','S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION-REVIEW.md','S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION-REVIEW.md','S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION-REVIEW.md','S6-PHASE-RECONSTRUCTION-FIXTURE-REVIEW.md','S6-RELIABLE-EXCHANGE-FIXTURE-REVIEW.md','S6-NATIVE-CLEANUP-ENTRY-COVERAGE-REVIEW.md']:read(D/f)
read(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md');read(R/'docs/superpowers/plans/2026-10-13-handoff-coverage-reconciliation.md');read(R/'docs/superpowers/plans/2026-10-13-cleanup-entry-reuse-design-decision.md');read(H/'entry.json');read(H/'entry.py');read(H/'reconcile.py');read(H/'reconcile-failure.json');read(H/'reconcile-2.py');read(H/'source_contract.py')
with (H/'source-contract.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256=pins),f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,pins=len(pins))));assert all(c.values())
