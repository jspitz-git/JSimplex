from pathlib import Path
from fractions import Fraction
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');M=Path('/home/jspitz/JSimplex.jl');D=W/'diagnostics/dual-weight-validity-contract/2026-10-30'
if D.exists():raise RuntimeError('fresh source-only record required')
D.mkdir(parents=True)
checks={};bindings={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def require(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
old=json.loads(Path(W/'diagnostics/klu-homogeneous-cleanup/2026-10-30/verification-1/postflight.json').read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']) if boot==old['boot'] else set();conflicts=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  stat=(p/'stat').read_text();a=stat[stat.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
  pgid,sid,start=int(a[2]),int(a[3]),int(a[19])
  if comm.lower().startswith('julia') or pgid in groups or sid in groups:conflicts.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=start,boot_id=boot,command=cmd))
 except (FileNotFoundError,ProcessLookupError):pass
require('no_Julia_or_prior_group_session',not conflicts)
refs={str(repo):{r:subprocess.check_output(['git','-C',str(repo),'rev-parse',r],text=True).strip() for r in ['HEAD','master','origin/master']} for repo in [W,M]}
require('expected_diagnostic_head',refs[str(W)]['HEAD']=='aad722caf65fbefc09e9a38eca887ab2a1a89581')
require('master_unchanged',all(v=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for k,rows in refs.items() for r,v in rows.items() if not(k==str(W) and r=='HEAD')))
(D/'host.json').write_text(json.dumps(dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,refs=refs),indent=2)+'\n')
recovery=read(W/'src/simplex_recovery.jl');dual=read(W/'src/dual_simplex.jl');pricing=read(W/'src/simplex_pricing.jl');simplex=read(W/'src/simplex.jl');pivot=read(W/'src/simplex_pivot.jl');precision=read(W/'src/simplex_precision.jl')
checks_source={
'strict_rebuild': 'refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable || return false' in recovery,
'weight_scalar_only_from_direction':'weight = dot(direction,direction)' in recovery and 'max(_typed_ratio(T,1,10^4),weight)' in recovery,
'recovery_prechecks_before_weights':recovery.index('_finite_workspace(trial) && _recomputed_basis_reliable(trial)')<recovery.index('_rebuild_recovery_weights!(trial,stop)'),
'precision_shared_consumer':'_rebuild_recovery_weights!(fresh,stop) || throw(_UnreliableBasisSolve())' in precision,
'raw_fixed_score': 'return weighted ? S(violation)^2/S(weight) : S(violation)' in dual,
'eligibility_before_score':dual.index('violation > workspace.options.primal_tolerance || continue')<dual.index('score = _dual_pricing_score(violation,workspace.pricing_weights'),
'raw_score_sentinel':'best_score = S === :scaled ? _primal_dantzig_score(one(T)) : zero(S)' in dual and 'if (S === :scaled && leaving_row == -1) || score > best_score' in dual,
'selected_residual_before_weight_check':dual.index('row_residual_ratio = _dual_row_residual_ratio(workspace, rho, leaving_row)')<dual.index('if !_validate_dual_edge!(workspace,leaving_index,rho)'),
'selected_factor_two_validation':'min(stored, actual) < _typed_ratio(T, 1, 2) * max(stored, actual)' in dual,
'auto_validation_scope':'ws.options.pricing == :auto && _weight_pricing(ws,:dual) == :steepest_edge || return true' in pricing,
'DSE_update_uses_stored_weights':'workspace.pricing_weights[index] + coefficient *' in dual and 'operation=:weight_ftran' in dual,
'existing_devex_switch':'function _switch_dual_pricing_to_devex!' in dual and 'workspace.dual_devex_fallback = true' in dual,
'devex_reset_all_weights':'fill!(workspace.pricing_weights, one(T))' in simplex,
'weight_maintenance_uses_temporary_return_mode':'!isnothing(state) && state.temporary ? state.return_mode' in pricing,
'publication_observers_precede_copy':recovery.index('_recovery_observer!(ws.progress.diagnostics,:checkpoint,trial)')<recovery.index('_copy_pivot_state!(ws,trial)'),
'pricing_flags_copied':'destination.dual_devex_fallback = source.dual_devex_fallback' in pivot,
'final_original_primal_check':'status == OPTIMAL && !_original_primal_feasible(workspace, primal)' in dual,
'final_original_optimality_check':'status == OPTIMAL && !_original_optimality_certified(workspace, primal)' in dual,
'full_component_quality_not_forward_certificate':'A reliable result certifies componentwise backward error, not forward error or' in recovery,
}
for k,v in checks_source.items():require(k,v)
files=['src/simplex_numerics.jl','src/dual_ratio.jl','src/simplex_start.jl','src/simplex_phase_one.jl','src/refactorization_policy.jl','src/solver.jl','src/native_certificate_recovery.jl','src/legacy_dual_correction.jl','src/simplex_diagnostics.jl','test/dual_simplex_tests.jl','test/dual_weight_validation_tests.jl','test/adaptive_pricing_tests.jl','test/adaptive_pricing_lifecycle_tests.jl','test/partial_pricing_edge_tests.jl','AGENTS.md','diagnostics/klu-weight-rejection/2026-10-29/REPORT.md','diagnostics/klu-homogeneous-cleanup/2026-10-30/REPORT.md','diagnostics/klu-weight-btran/2026-10-29/REPORT.md']
for rel in files:
 if (W/rel).exists():read(W/rel)
 else:raise FileNotFoundError(rel)
for p in (W/'src').rglob('*.jl'):
 q=M/p.relative_to(W);require('source_master:'+str(p.relative_to(W)),p.read_bytes()==q.read_bytes())
# Exact analytic example only; no solver/numerical experiment or Julia execution.
epsilon=Fraction(1,2**80);wrong=Fraction(2**20);residual=epsilon*wrong;actual_weight=Fraction(1);proposed_weight=wrong**2+1
require('analytic_residual_small',residual<Fraction(1,2**44))
require('analytic_component_ratio_one',residual/abs(epsilon*wrong)==1)
require('analytic_weight_error_large',proposed_weight/actual_weight>2**40)
analytic=dict(matrix='diag(2^-80,1)',rhs='e2',exact_solution=['0','1'],proposed_solution=['2^20','1'],residual_inf=str(residual),normwise_residual='2^-80 (denominator ||B||inf*||xhat||inf)',exact_weight=str(actual_weight),proposed_weight=str(proposed_weight),componentwise_error='1',scope='analytic rational derivation, no solver fixture/run')
(D/'source-evidence.json').write_text(json.dumps(dict(accepted=True,scope='source/analytic assessment only, no production admission',checks=checks,bindings=bindings,analytic_counterexample=analytic),indent=2)+'\n')
print(json.dumps({'source_checks':len(checks),'readtime_bindings':len(bindings),'groups_sessions':len(groups),'conflicts':conflicts}))
