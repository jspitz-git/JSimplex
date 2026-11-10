# Stage certified active rows with the original cheap/equality reductions.
# No coefficient dropping, relaxed pivot tests, or extra fill/work budget.
function _stage_inequality_reductions(problem::LinearProblem{T}, certificates;
                                      rounded_costs::Bool, capture::Bool, stop_requested=()->false) where T
    current = _InequalityProofs.activate(problem,certificates)
    origins = collect(1:size(problem.A,1))
    targets = Set(c.row for c in certificates)
    accepted = Set{Int}()
    metadata = _PostsolveLift.Metadata{T}[]
    steps = PostsolveStep{T}[]
    for index in (3,4,1,2)
        stop_requested() && return nothing
        next = index == 3 ? aggregate_singleton_equalities(current) :
               index == 4 ? aggregate_sparse_equalities(current;rounded_costs) :
               index == 1 ? _presolve_basic(current) : reduce_singleton_rows(current)
        next isa PresolveFailure && return nothing
        isempty(next.postsolve_stack) && continue
        step = only(next.postsolve_stack)
        map = _PostsolveLift.mapof(step)
        if step isa Union{SingletonEqualityStep,SparseEqualityStep}
            for record in step.records
                origins[record.row] in targets && push!(accepted,origins[record.row])
            end
        end
        capture && push!(metadata,_PostsolveLift.metadata(current,next,index))
        push!(steps,step)
        origins = origins[map.rows]
        current = next.problem
    end
    return (;problem=current,metadata,steps,accepted)
end

function _augment_inequalities(base, problem::LinearProblem{T}, tolerance,
                               history, stop_requested, verbose; rounded_costs::Bool) where T
    base isa PresolveFailure && return base
    problem.objective_sense == MIN_SENSE && T in (Float32,Float64) &&
        tolerance > zero(T) && is_continuous(problem) &&
        rounding(T) == RoundNearest && !get_zero_subnormals() || return base
    stop_requested() && return base
    root = base.problem
    certificates, _ = _InequalityProofs.infer(root;stop_requested)
    isempty(certificates) && return base
    capture = !isnothing(history)
    staged = _stage_inequality_reductions(root,certificates;rounded_costs,capture,stop_requested)
    while !isnothing(staged) && length(staged.accepted) != length(certificates)
        certificates = filter(c -> c.row in staged.accepted,certificates)
        isempty(certificates) && return base
        stop_requested() && return base
        staged = _stage_inequality_reductions(root,certificates;rounded_costs,capture,stop_requested)
    end
    isnothing(staged) && return base
    @assert staged.accepted == Set(c.row for c in certificates)
    m,n = size(root.A)
    activation = InequalityActivationStep{T}(n,m,[(c.row,c.side==:upper) for c in certificates])
    mark = _history_mark(history)
    try
        if capture
            push!(history.metadata,_PostsolveLift.Metadata{T}(activation,
                _PostsolveLift.SingletonData{T}[],_PostsolveLift.EqualityData{T}[]))
            push!(history.propagation,nothing)
            append!(history.metadata,staged.metadata)
            append!(history.propagation,fill(nothing,length(staged.metadata)))
        end
        continued = _presolve_base_for_solve(staged.problem,tolerance;
            stop_requested,verbose,history,rounded_costs)
        if continued isa PresolveFailure
            # The activated LP's failure is NOT an original-model certificate.
            _restore_history_mark!(history,mark)
            return base
        end
        steps=PostsolveStep{T}[base.postsolve_stack...,activation,staged.steps...,continued.postsolve_stack...]
        return PresolveResult(continued.problem,steps,size(problem.A,2))
    catch
        _restore_history_mark!(history,mark)
        rethrow()
    end
end
