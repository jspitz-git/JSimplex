from pathlib import Path
import hashlib,json
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task1/2026-10-30'
if (D/'simplex_numerics.jl').exists() or (D/'simplex_recovery.jl').exists():raise RuntimeError('fresh candidate required')
read=lambda p:Path(p).read_text()
numeric=read(W/'src/simplex_numerics.jl');recovery=read(W/'src/simplex_recovery.jl')
wrapper=recovery[recovery.index('function refine_basis_solve!'):recovery.index('\n_checkpoint_model')]
kstart=recovery.index('function _refine_basis_solve!(destination::AbstractVector{T},ws,B,rhs,policy,stop,buffers,transposed)')
kend=recovery.index('\n# A clock-only guard',kstart);kernel=recovery[kstart:kend]
metadata='''# Call-local, opt-in status for recovery consumers. No field is added to
# SolveQuality or any workspace/cache. Default refinement constructs no outcome.
@enum _RefinementCause::UInt8 begin
    _refine_reliable = 0
    _refine_nonfinite_initial_quality
    _refine_nonfinite_quality
    _refine_nonfinite_correction
    _refine_nonfinite_trial
    _refine_nonfinite_trial_quality
    _refine_stopped
    _refine_unchanged
    _refine_not_improved
    _refine_limit
    _refine_not_observed
end

struct _BasisRefinementOutcome{T<:Real}
    quality::SolveQuality{T}
    cause::_RefinementCause
    invalid_seen::Bool
end

@inline _refinement_result(::Val{false},quality::SolveQuality,
                           cause::_RefinementCause,invalid_seen::Bool) = quality
@inline _refinement_result(::Val{true},quality::SolveQuality{T},
                           cause::_RefinementCause,invalid_seen::Bool) where T =
    _BasisRefinementOutcome{T}(quality,cause,invalid_seen)

@inline _refinement_finished(::Val{false},quality::SolveQuality,invalid_seen::Bool) = quality
@inline function _refinement_finished(::Val{true},quality::SolveQuality,invalid_seen::Bool)
    cause = quality.reliable ? _refine_reliable :
            !quality.finite ? _refine_nonfinite_quality : _refine_limit
    return _refinement_result(Val(true),quality,cause,invalid_seen || !quality.finite)
end

'''
needle='struct SolveQualityScratch{T,W}'
if numeric.count(needle)!=1:raise RuntimeError('numeric insertion boundary')
newnumeric=numeric.replace(needle,metadata+needle)
entry=wrapper.replace('function refine_basis_solve!', 'function _refine_basis_solve_entry!',1)
entry=entry.replace('policy::NumericalPolicy{T},stop;','policy::NumericalPolicy{T},stop,report::Val;',1)
entry=entry.replace('transposed::Bool=false)::SolveQuality{T} where {T}','transposed::Bool=false) where {T}',1)
entry=entry.replace('_record_refactor_quality!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed))','_record_refinement_result!(ws,_refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed,report))')
api='''function refine_basis_solve!(destination::AbstractVector{T},ws::SimplexWorkspace{T},
                             rhs::AbstractVector{T},policy::NumericalPolicy{T},stop;
                             transposed::Bool=false)::SolveQuality{T} where {T}
    return _refine_basis_solve_entry!(destination,ws,rhs,policy,stop,Val(false);transposed)
end

function _refine_basis_solve_outcome!(destination::AbstractVector{T},ws::SimplexWorkspace{T},
                                    rhs::AbstractVector{T},policy::NumericalPolicy{T},stop;
                                    transposed::Bool=false)::_BasisRefinementOutcome{T} where {T}
    return _refine_basis_solve_entry!(destination,ws,rhs,policy,stop,Val(true);transposed)
end

@inline _record_refinement_result!(ws,quality::SolveQuality) =
    _record_refactor_quality!(ws,quality)
@inline function _record_refinement_result!(ws,result::_BasisRefinementOutcome)
    _record_refactor_quality!(ws,result.quality)
    return result
end

'''
newkernel=kernel.replace('buffers,transposed) where T','buffers,transposed,report::Val{Report}) where {T,Report}',1)
newkernel=newkernel.replace('    quality.finite || return quality','    invalid_seen = false\n    quality.finite || return _refinement_result(report,quality,_refine_nonfinite_initial_quality,true)',1)
newkernel=newkernel.replace('        stop() && return quality','        stop() && return _refinement_result(report,quality,_refine_stopped,invalid_seen)')
newkernel=newkernel.replace('        (quality.reliable || !quality.finite || stop()) && return quality','''        if quality.reliable
            return _refinement_result(report,quality,_refine_reliable,invalid_seen)
        elseif !quality.finite
            return _refinement_result(report,quality,_refine_nonfinite_quality,true)
        elseif stop()
            return _refinement_result(report,quality,_refine_stopped,invalid_seen)
        end''')
replacements={
'all(isfinite,correction) || return quality':'all(isfinite,correction) || return _refinement_result(report,quality,_refine_nonfinite_correction,true)',
'all(isfinite,buffers.trial) || return quality':'all(isfinite,buffers.trial) || return _refinement_result(report,quality,_refine_nonfinite_trial,true)',
'!changed && !policy.solve_refinement && return quality':'!changed && !policy.solve_refinement && return _refinement_result(report,quality,_refine_unchanged,invalid_seen)',
'trial_quality.finite || return quality':'trial_quality.finite || return _refinement_result(report,quality,_refine_nonfinite_trial_quality,true)',
'(trial_quality.reliable || _refinement_error(trial_quality) < _refinement_error(quality)) || return quality':'(trial_quality.reliable || _refinement_error(trial_quality) < _refinement_error(quality)) || return _refinement_result(report,quality,_refine_not_improved,invalid_seen)',
}
for before,after in replacements.items():
 if newkernel.count(before)!=1:raise RuntimeError('kernel selector '+before)
 newkernel=newkernel.replace(before,after)
needle='                cleaned = _refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)\n'
if newkernel.count(needle)!=1:raise RuntimeError('cleanup selector')
newkernel=newkernel.replace(needle,needle+'''                if Report
                    invalid_seen |= !cleaned.finite
                end
''')
needle='                    trial_quality = _refinement_quality!(quality_scratch,B,buffers.trial,saved_rhs,policy,transposed,wide)\n'
if newkernel.count(needle)!=1:raise RuntimeError('restored quality selector')
newkernel=newkernel.replace(needle,needle+'''                    if Report
                        invalid_seen |= !trial_quality.finite
                    end
''')
if not newkernel.endswith('    return quality\nend\n'):raise RuntimeError('final return')
newkernel=newkernel[:-len('    return quality\nend\n')]+'    return _refinement_finished(report,quality,invalid_seen)\nend\n'
compat='''# Preserve the previous private entry as well as the public quality-only API.
_refine_basis_solve!(destination::AbstractVector{T},ws,B,rhs,policy,stop,buffers,transposed) where T =
    _refine_basis_solve!(destination,ws,B,rhs,policy,stop,buffers,transposed,Val(false))

'''
newrecovery=recovery.replace(wrapper,api+entry,1).replace(kernel,compat+newkernel,1)
(D/'simplex_numerics.jl').write_text(newnumeric);(D/'simplex_recovery.jl').write_text(newrecovery)
# A bounded local reference contains only the original wrapper/kernel. Every
# helper other than its own kernel is qualified to the unchanged JSimplex API.
ref=wrapper+'\n'+kernel
import re
names=['SimplexWorkspace','NumericalPolicy','SolveQuality','_pivot_quality_buffers','_basis_matrix!','_stored_quality_bits','_record_refactor_quality!','solve_quality!','_refinement_quality!','_simplex_event!','_timed_simplex','transpose_solve!','_ordinary_forward_solve!','_refinement_error','_clean_homogeneous_terms!','_pipeline_changed!']
for name in sorted(names,key=len,reverse=True):
 ref=re.sub(r'(?<![\w.])'+re.escape(name)+r'(?!\w)',lambda m:'JS.'+m.group(0),ref)
(D/'reference.jl').write_text('module RefinementReference\nusing JSimplex\nconst JS=JSimplex\n'+ref+'end # module\n')
(D/'build-metadata.json').write_text(json.dumps(dict(scope='offline source generation only; no Julia',tests_written_before_candidate=True,baseline={'simplex_numerics.jl':hashlib.sha256(numeric.encode()).hexdigest(),'simplex_recovery.jl':hashlib.sha256(recovery.encode()).hexdigest()},inserted_metadata=metadata,original_wrapper=wrapper,original_kernel=kernel,entry=entry,candidate_kernel=newkernel,api_prefix=api,compatibility_entry=compat,qualified_reference_helpers=names),indent=2)+'\n')
print(json.dumps({'candidate_files':2,'reference_functions':2,'julia_executed':False,'tests_sha256':hashlib.sha256((D/'refinement_outcome_tests.jl').read_bytes()).hexdigest()}))
