from pathlib import Path
import json,hashlib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task2/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(n,s):
 with (D/n).open('x') as f:f.write(s)
require_tests=sha(D/'recovery_devex_fallback_tests.jl')
s=(P/'simplex_recovery.jl').read_text();changes=[]
def change(a,b):
 global s
 if s.count(a)!=1:raise RuntimeError(('unique anchor',a,s.count(a)))
 s=s.replace(a,b);changes.append((a,b))
old='function _recovery_trial(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop) where T\n'
new='''# Cold, call-local pending publication; no copies or new persistent fields.
struct _RecoveryTrialResult{W}
    workspace::W
    devex_fallback::Bool
    failed_weight_row::Int
end

_validate_recovery_algorithm(algorithm::Symbol) =
    algorithm in (:unspecified,:primal,:dual) ? nothing :
    throw(ArgumentError("Unknown recovery algorithm"))
_build_recovery_factor(B,options) = _basis_factorization(B,options)

# Strict compatibility, including all existing direct/precision callers.
function _recovery_trial(ws::SimplexWorkspace,c::BasisCheckpoint,stop)
    result = _recovery_trial_with_pricing(ws,c,stop)
    return isnothing(result) ? nothing : result.workspace
end

function _recovery_trial_with_pricing(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop;
                                     algorithm::Symbol=:unspecified,
                                     build_factor::F=_build_recovery_factor) where {T,F}
    _validate_recovery_algorithm(algorithm)
'''
change(old,new)
change('                _basis_factorization(B,ws.options)\n','                build_factor(B,ws.options)\n')
change('''    _rebuild_recovery_weights!(trial,stop) || return nothing
    stop() && return nothing
    return trial
''','''    weights = _rebuild_recovery_weights_result!(trial,stop;algorithm)
    if !weights.ok
        weights.fallback_ready || return nothing
        # One corresponding post-weight stop, before any state preparation.
        stop() && return nothing
        # Refined weight buffers are independent of rho; callbacks may have
        # invalidated core values since recompute. No additional solve/factor.
        _finite_workspace(trial) && _recomputed_basis_reliable(trial) || return nothing
        _prepare_recovery_devex!(trial)
        return _RecoveryTrialResult(trial,true,weights.failed_row)
    end
    stop() && return nothing
    return _RecoveryTrialResult(trial,false,0)
''')
change('function _publish_recovery!(ws,trial,reason,stop)\n','''function _publish_recovery!(ws,result::_RecoveryTrialResult,reason,stop)
    return _publish_recovery!(ws,result.workspace,reason,stop;
        weight_fallback=result.devex_fallback,failed_weight_row=result.failed_weight_row)
end

function _publish_recovery!(ws,trial,reason,stop;
                            weight_fallback::Bool=false,failed_weight_row::Int=0)
''')
change('''    _store_basis_checkpoint!(ws,checkpoint)
    pricing_reset && _record_recovery!(ws.progress.diagnostics,:pricing_reset)
''','''    _store_basis_checkpoint!(ws,checkpoint)
    if weight_fallback
        # Commit-only records, never observer/logger calls. Pending mode was
        # already visible to the unchanged prepublication recovery observers.
        _record_recovery!(ws.progress.diagnostics,:pricing_weight_rejected)
        _record_recovery!(ws.progress.diagnostics,:pricing_devex)
    end
    pricing_reset && _record_recovery!(ws.progress.diagnostics,:pricing_reset)
''')
change('function restore_checkpoint!(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop)::Bool where T\n','''function restore_checkpoint!(ws::SimplexWorkspace{T},c::BasisCheckpoint{T},stop;
                             algorithm::Symbol=:unspecified)::Bool where T
    _validate_recovery_algorithm(algorithm)
''')
change('trial = _recovery_trial(ws,c,guard)','trial = _recovery_trial_with_pricing(ws,c,guard;algorithm)')
change('function repair_basis!(ws::SimplexWorkspace{T},policy::NumericalPolicy{T},stop)::Bool where T\n','''function repair_basis!(ws::SimplexWorkspace{T},policy::NumericalPolicy{T},stop;
                       algorithm::Symbol=:unspecified)::Bool where T
    _validate_recovery_algorithm(algorithm)
''')
change('_repair_basis!(ws,policy,guard,original)\n    end','_repair_basis!(ws,policy,guard,original;algorithm)\n    end')
change('function _repair_basis!(ws,policy,guard,original)\n','''function _repair_basis!(ws,policy,guard,original;algorithm::Symbol=:unspecified)
    _validate_recovery_algorithm(algorithm)
''')
change('trial = _recovery_trial(ws,candidate,guard)','trial = _recovery_trial_with_pricing(ws,candidate,guard;algorithm)')
change('if restore_checkpoint!(ws,checkpoint,guard)','if restore_checkpoint!(ws,checkpoint,guard;algorithm)')
fresh('simplex_recovery.jl',s)
fresh('simplex_numerics.jl',(P/'simplex_numerics.jl').read_text())
pivot=(W/'src/simplex_pivot.jl').read_text();a='repaired = repair_basis!(ws,policy,stop_requested)';b='repaired = repair_basis!(ws,policy,stop_requested;algorithm)'
if pivot.count(a)!=1:raise RuntimeError('pivot unique')
fresh('simplex_pivot.jl',pivot.replace(a,b))
fresh('build.json',json.dumps(dict(tests_first_sha256=require_tests,parent_sources={str(P/n):sha(P/n) for n in ('simplex_numerics.jl','simplex_recovery.jl')},recovery_changes=changes,pivot_change=(a,b)),indent=2)+'\n')
print(json.dumps(dict(candidate_files=3,source_changes=len(changes)+1,julia_executed=False)))
