# Optional batches live after the unchanged base presolve. Records hold maps,
# scalar proofs and shape only; intermediate matrices are not retained in solve.
struct _RowSparsificationStep{T} <: AbstractPostsolveStep
    rows::Int
    columns::Int
    operations::Vector{_RowSparsification.Operation{T}}
end
struct _OptionalPresolveResult{T}
    problem::LinearProblem{T}
    postsolve_stack::Vector{AbstractPostsolveStep}
    original_column_count::Int
    base_steps::Vector{PostsolveStep{T}}
    tail_steps::Vector{PostsolveStep{T}}
    tail_history::Union{Nothing,_PostsolveHistory{T}}
    row_step::Union{Nothing,_RowSparsificationStep{T}}
    column_step::Union{Nothing,_ColumnPostsolve.Step{T}}
    fixing_steps::Vector{PostsolveStep{T}}
    tolerance::T
end
_optional_presolve_enabled(o)=o.presolve_row_sparsification || o.presolve_column_merging || o.presolve_column_dominance
_release_optional_presolve!(result)=nothing
_release_optional_presolve!(result::_OptionalPresolveResult)=_restore_history_mark!(result.tail_history,0)
@inline function _with_optional_presolve(base,history,options::SolverOptions;stop_requested=()->false,verbose=false)
    # Keep this guard small/inlinable: the disabled branch returns the existing
    # result without allocating optional indices, histories or caches.
    (options.presolve && _optional_presolve_enabled(options)) || return base
    base isa PresolveFailure && return base
    iszero(nnz(base.problem.A)) && return base
    _enabled_optional_presolve(base,history,options;stop_requested,verbose)
end
function _enabled_optional_presolve(base::PresolveResult{T,S},history,options::SolverOptions{T};stop_requested=()->false,verbose=false)::Union{PresolveResult{T,S},_OptionalPresolveResult{T}} where {T,S}
    current=base.problem
    stopped=Ref(false);poll()=stopped[] || (stopped[]=stop_requested())
    poll() && return base
    row_step=nothing;column_step=nothing;fixing_steps=nothing
    if options.presolve_row_sparsification
        batch=_RowSparsification.sparsify(current;stop_requested=poll)
        poll() && return base
        if !isempty(batch.operations)
            operations=T===BigFloat ? deepcopy(batch.operations) : batch.operations
            row_step=_RowSparsificationStep(size(current.A,1),size(current.A,2),operations)
            current=batch.problem
        end
    end
    # Support/proportionality groups are reusable only while the CSC identity
    # is unchanged. Exact scalar conversions remain valid across a merge too.
    exact_state=nothing;groups=nothing
    if options.presolve_column_merging && options.presolve_column_dominance && size(current.A,2)>1
        exact_state=_ColumnMerge.exact_cache(T)
        groups=_ColumnMerge.parallel_groups(current,first(exact_state),Dict{String,Int}())
    end
    if options.presolve_column_merging && size(current.A,2)>1
        poll() && return base
        merged=_ColumnMerge.merge_columns(current;groups,exact_state)
        poll() && return base
        if !isempty(merged.operations)
            column_step=_ColumnPostsolve.record(current,merged)
            current=merged.problem
            groups=nothing # matrix changed: never reuse old support indices
        end
    end
    if options.presolve_column_dominance && size(current.A,2)>1
        poll() && return base
        fixed=_ColumnDominance.capacity_columns(current;groups,exact_state)
        poll() && return base
        # An optional contradiction is never a new original infeasibility proof.
        fixed.result isa PresolveFailure && return base
        if !isempty(fixed.result.postsolve_stack)
            fixing_steps=PostsolveStep{T}[fixed.result.postsolve_stack...]
            T===BigFloat && (fixing_steps=deepcopy(fixing_steps))
            current=fixed.result.problem
        end
    end
    isnothing(row_step)&&isnothing(column_step)&&isnothing(fixing_steps) && return base
    tail_history=current.objective_sense==MIN_SENSE ? _PostsolveHistory(T) : nothing
    # MAX's existing base history has no MIN-normalized dual metadata. Preserve
    # that path; do not invent a multiplier lift through an extra MAX tail.
    tail=if isnothing(tail_history)
        identity_presolve(current)
    else
        _presolve_for_solve(current,options.primal_tolerance;stop_requested=poll,verbose,history=tail_history)
    end
    if tail isa PresolveFailure || poll()
        _restore_history_mark!(tail_history,0)
        return base
    end
    bs=PostsolveStep{T}[base.postsolve_stack...]
    ts=PostsolveStep{T}[tail.postsolve_stack...]
    fs=isnothing(fixing_steps) ? PostsolveStep{T}[] : fixing_steps
    stack=AbstractPostsolveStep[bs...]
    isnothing(row_step) || push!(stack,row_step)
    isnothing(column_step) || push!(stack,column_step)
    append!(stack,fs);append!(stack,ts)
    tolerance=T===BigFloat ? deepcopy(options.primal_tolerance) : options.primal_tolerance
    _OptionalPresolveResult(tail.problem,stack,base.original_column_count,bs,ts,tail_history,row_step,column_step,fs,tolerance)
end
function postsolve_primal(r::_OptionalPresolveResult{T},x::AbstractVector{<:Real}) where T
    point=_postsolve_primal(r.tail_steps,convert.(T,x))
    point=_postsolve_primal(r.fixing_steps,point)
    isnothing(r.column_step) || (point=_ColumnPostsolve.primal(r.column_step,point,r.tolerance))
    # Equivalent row operations leave structural coordinates unchanged.
    _postsolve_primal(r.base_steps,point)
end
function _optional_history_lift(history,steps,b,y,x,options)
    if isnothing(history)
        return _restore_basis(steps,b),y,_postsolve_primal(steps,x)
    end
    length(history.metadata)==length(steps) &&
      all(m.step===s for (m,s) in zip(history.metadata,steps)) || throw(ArgumentError("incomplete optional presolve history"))
    _PropagationHistory.chain(history.metadata,history.propagation,b,y,x,options)
end
function _optional_postsolve(history,r::_OptionalPresolveResult{T},scaling,run,options) where T
    try
        isnothing(run.basis) && throw(ArgumentError("no reduced basis for optional postsolve"))
        isnothing(run.dual) && throw(ArgumentError("no reduced dual for optional postsolve"))
        x=unscale_primal(scaling,run.primal);y=unscale_dual(scaling,run.dual)
        b,y,x=_optional_history_lift(r.tail_history,r.tail_steps,run.basis,y,x,options)
        for step in Iterators.reverse(r.fixing_steps)
            step isa PresolveMap || throw(ArgumentError("unsupported column fixing map"))
            x=postsolve_primal(step,x);b=restore_basis(step,b)
            expanded=zeros(T,step.original_row_count);expanded[step.rows]=y;y=expanded
        end
        isnothing(r.column_step) || ((b,y,x)=_ColumnPostsolve.lift(r.column_step,b,y,x,options))
        if !isnothing(r.row_step)
            step=r.row_step
            hint=_RowSparsification.lift(step.operations,step.rows,step.columns,b,y,x;provisional=true)
            isnothing(hint.basis) && throw(ArgumentError(hint.reason))
            b,y,x=hint.basis,hint.dual,hint.primal
        end
        b,_,x=_optional_history_lift(history,r.base_steps,b,y,x,options)
        # A hint, never an accepted basis/certificate. The unchanged original
        # cleanup installs/refactors/recomputes and certifies before publishing.
        return b,x
    catch e
        e isa ArgumentError || rethrow()
        options.verbose && @info "Optional postsolve hint unavailable; using original LP recovery" reason=sprint(showerror,e)
        return nothing,nothing
    finally
        _restore_history_mark!(history,0)
        _release_optional_presolve!(r)
    end
end
_postsolve_with_dual(h::_PostsolveHistory,r::_OptionalPresolveResult,s,run,o)=_optional_postsolve(h,r,s,run,o)
_postsolve_with_dual(::Nothing,r::_OptionalPresolveResult,s,run,o)=_optional_postsolve(nothing,r,s,run,o)
