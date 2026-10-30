from pathlib import Path
import hashlib,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task2/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task1/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(n,s):
 with (D/n).open('x') as f:f.write(s)
if not (D/'recovery_weight_tests.jl').exists():raise RuntimeError('tests first')
metadata='''# Cold recovery result, with no array or workspace reference.
@enum _RecoveryWeightReason::UInt8 begin
    _weight_complete = 0
    _weight_not_needed
    _weight_finite_inconclusive
    _weight_stopped
    _weight_nonfinite_attempt
    _weight_invalid_norm
    _weight_ineligible
end
struct _RecoveryWeightResult
    ok::Bool
    fallback_ready::Bool
    failed_row::Int
    reason::_RecoveryWeightReason
    refinement_cause::_RefinementCause
end

'''
numerics=(P/'simplex_numerics.jl').read_text();anchor='struct SolveQualityScratch{T,W}\n';assert numerics.count(anchor)==1
fresh('simplex_numerics.jl',numerics.replace(anchor,metadata+anchor))
recovery=(P/'simplex_recovery.jl').read_text();start=recovery.index('function _rebuild_recovery_weights!');end=recovery.index('\nfunction _basis_primal_rhs',start);original=recovery[start:end]
code='''# Explicit caller route and maintained geometry, never options/history alone.
function _recovery_weight_scope(trial::SimplexWorkspace{T},algorithm::Symbol) where T
    state = trial.scratch.pricing
    return algorithm == :dual && (T === Float32 || T === Float64) &&
        _weight_pricing(trial,:dual) == :steepest_edge &&
        (isnothing(state) || state.algorithm == :dual)
end

function _failed_recovery_weight(trial,direction,outcome::_BasisRefinementOutcome,row,algorithm)
    quality,cause = outcome.quality,outcome.cause
    cause == _refine_stopped &&
        return _RecoveryWeightResult(false,false,row,_weight_stopped,cause)
    if outcome.invalid_seen || !quality.finite || cause in (
        _refine_nonfinite_initial_quality,_refine_nonfinite_quality,
        _refine_nonfinite_correction,_refine_nonfinite_trial,_refine_nonfinite_trial_quality)
        return _RecoveryWeightResult(false,false,row,_weight_nonfinite_attempt,cause)
    end
    if !_recovery_weight_scope(trial,algorithm) || quality.reliable ||
       !(cause in (_refine_unchanged,_refine_not_improved,_refine_limit))
        return _RecoveryWeightResult(false,false,row,_weight_ineligible,cause)
    end
    # Same guard as a reliable row: self-dot rejects zero/underflow, overflow,
    # NaN and Inf under the unchanged real IEEE arithmetic. No second scan.
    weight = dot(direction,direction)
    isfinite(weight) && weight > zero(eltype(direction)) ||
        return _RecoveryWeightResult(false,false,row,_weight_invalid_norm,cause)
    return _RecoveryWeightResult(false,true,row,_weight_finite_inconclusive,cause)
end

function _rebuild_recovery_weights_result!(trial::SimplexWorkspace{T},stop;
                                            algorithm::Symbol=:unspecified) where T
    _weight_pricing(trial,:dual) == :steepest_edge ||
        return _RecoveryWeightResult(true,false,0,_weight_not_needed,_refine_not_observed)
    m = length(trial.basis.basic_indices)
    rhs,direction = zeros(T,m),zeros(T,m)
    policy = trial.progress.numerical_policy
    detailed = _recovery_weight_scope(trial,algorithm)
    cause = _refine_not_observed
    for row in 1:m
        stop() && return _RecoveryWeightResult(false,false,row,_weight_stopped,_refine_not_observed)
        fill!(rhs,zero(T))
        rhs[row] = one(T)
        transpose_solve!(direction,trial.factorization,rhs)
        if detailed
            outcome = _refine_basis_solve_outcome!(direction,trial,rhs,policy,stop;transposed=true)
            cause = outcome.cause
            outcome.quality.reliable || return _failed_recovery_weight(trial,direction,outcome,row,algorithm)
        else
            refine_basis_solve!(direction,trial,rhs,policy,stop;transposed=true).reliable ||
                return _RecoveryWeightResult(false,false,row,_weight_ineligible,_refine_not_observed)
        end
        weight = dot(direction,direction)
        isfinite(weight) && weight > zero(T) ||
            return _RecoveryWeightResult(false,false,row,_weight_invalid_norm,cause)
        trial.pricing_weights[trial.basis.basic_indices[row]] = max(_typed_ratio(T,1,10^4),weight)
    end
    return _RecoveryWeightResult(true,false,0,_weight_complete,cause)
end

# All old call sites, including precision transfer, remain strict.
_rebuild_recovery_weights!(trial::SimplexWorkspace,stop)::Bool =
    _rebuild_recovery_weights_result!(trial,stop).ok

# State-only preparation on an owned, core-revalidated recovery trial.
# Task3 owns the post-classification stop/core checks and publication boundary.
function _prepare_recovery_devex!(trial)::Nothing
    trial.scratch.recovery_active || throw(ArgumentError("Devex preparation requires a private recovery trial"))
    _recovery_weight_scope(trial,:dual) || throw(ArgumentError("Ineligible recovery pricing state"))
    state = trial.scratch.pricing
    if isnothing(state) && trial.options.pricing == :auto
        # Auto selection ignores the fixed-mode flag: materialize its existing
        # fixed-size state lazily, with no monitor/vector allocation.
        state = PricingState(eltype(trial.costs))
        state.algorithm = :dual
        trial.scratch.pricing = state
    end
    if !isnothing(state)
        state.rejected_weights += 1
        _unreliable_pricing!(state,trial.progress.numerical_policy)
    end
    trial.options.pricing == :auto || (trial.dual_devex_fallback = true)
    reset_devex!(trial) # recovery_active suppresses the existing reset observer
    _invalidate_pricing_pool!(trial;basis=false,costs=false)
    return nothing
end
'''
fresh('simplex_recovery.jl',recovery[:start]+code+recovery[end:])
ref='module LegacyRecoveryWeights\nusing LinearAlgebra, JSimplex\nconst J=JSimplex\n'+original+'\nend\n'
for name in ['SimplexWorkspace','_weight_pricing','transpose_solve!','refine_basis_solve!','_typed_ratio']:
 import re
 ref=re.sub(r'(?<![\w.])'+re.escape(name)+r'(?!\w)', 'J.'+name,ref)
fresh('legacy_rebuild_reference.jl',ref)
fresh('build.json',json.dumps(dict(tests_first_sha256=sha(D/'recovery_weight_tests.jl'),parent_sources={str(P/n):sha(P/n) for n in ['simplex_numerics.jl','simplex_recovery.jl']},metadata=metadata,original_weight_loop=original,new_weight_loop=code),indent=2)+'\n')
print(json.dumps(dict(candidate_files=2,tests_first=True,production_changed=False,julia_executed=False)))
