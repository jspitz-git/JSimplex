module GenericDualComparisonsTests
using Test,JSimplex,SparseArrays,LinearAlgebra
module ComparisonReference
using LinearAlgebra
using JSimplex: SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_fixed,_invalidate_pricing_pool!,_primal_direction_magnitude,_primal_weighted_score,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_record_full_pricing!,Bound,_unbounded_bound,_dual_pivot_cutoff,_dual_pivot_eligible,_dual_ratio_tolerance,bound_value,dual_ratio_test,_lower_violation,_upper_violation
function update_duals!(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                      leaving_index::Int, entering_index::Int, dual_step::T)::Nothing where {T}
    changed_costs = false
    for index in eachindex(workspace.reduced_costs)
        state = workspace.basis.states[index]
        (state == BASIC || index == entering_index) && continue
        reduced_cost = workspace.reduced_costs[index] - dual_step * tableau_row[index]
        if !_is_fixed(workspace.lower[index], workspace.upper[index])
            tolerance = workspace.options.dual_tolerance
            violated = ((state == AT_LOWER || state == FREE_NONBASIC) && reduced_cost < -tolerance) ||
                       ((state == AT_UPPER || state == FREE_NONBASIC) && reduced_cost > tolerance)
            if violated
                # Shift to zero to leave room for recomputation roundoff.
                workspace.costs[index] -= reduced_cost
                changed_costs = true
                workspace.perturbed = true
                reduced_cost = zero(T)
            end
        end
        workspace.reduced_costs[index] = reduced_cost
    end
    workspace.reduced_costs[leaving_index] = -dual_step
    workspace.reduced_costs[entering_index] = zero(T)
    changed_costs && _invalidate_pricing_pool!(workspace;basis=false)
    return nothing
end

_primal_dantzig_score(reduced_cost::T) where {T<:AbstractFloat} =
    _primal_weighted_score(reduced_cost, one(T))
_primal_dantzig_score(reduced_cost::Rational) = abs(big(reduced_cost))

# Unit weight needs no arithmetic; retain exceptional tuple conventions and
# ambient rounding of abs, including rounded underflow/overflow.
function _primal_dantzig_score(reduced_cost::BigFloat)
    (!isfinite(reduced_cost) || iszero(reduced_cost)) &&
        return _primal_weighted_score(reduced_cost,one(BigFloat))
    value = abs(reduced_cost)
    (!isfinite(value) || iszero(value)) &&
        return _primal_weighted_score(reduced_cost,one(BigFloat))
    mantissa, exponent = frexp(value)
    return exponent, mantissa
end


function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < zero(T) ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -tolerance) ||
                    (state == AT_UPPER && reduced_cost > tolerance) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T<:Union{BigFloat,Rational{BigInt}}}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < zero(T) ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    negative_tolerance = tolerance
    negative_ready = false
    reuse_negative = pricing === :dantzig || pricing === :devex
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = if state == AT_LOWER
            if reuse_negative
                if !negative_ready
                    negative_tolerance = -tolerance
                    negative_ready = true
                end
                reduced_cost < negative_tolerance
            else
                reduced_cost < -tolerance
            end
        else
            (state == AT_UPPER && reduced_cost > tolerance) ||
            (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        end
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end


function dual_edge_selection(workspace::SimplexWorkspace{T};force_full::Bool=false)::Int where {T}
    _prepare_auto_pricing!(workspace,:dual)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:dual)
        row = _select_workspace_pool!(workspace,:dual;force_full)
        return row == 0 ? -1 : row
    end
    if workspace.options.pricing == :auto && T <: Rational
        return _dual_edge_selection(workspace,Val(Rational{BigInt}))
    elseif workspace.options.pricing == :auto
        return _dual_edge_selection(workspace,Val(:scaled))
    end
    return _dual_edge_selection(workspace,Val(T))
end

function _dual_pricing_score(violation,weight,weighted,::Val{S}) where S
    if S === :scaled
        isfinite(violation) || return (typemax(Int),one(violation))
        # Comparing v/sqrt(w) preserves the order of v^2/w while the existing
        # exponent score avoids overflow and the loss of tiny eligible rows.
        return weighted ? _primal_weighted_score(violation,sqrt(weight)) :
                          _primal_dantzig_score(violation)
    end
    return weighted ? S(violation)^2/S(weight) : S(violation)
end

function _dual_edge_selection(workspace::SimplexWorkspace{T},scoring::Val{S})::Int where {T,S}
    leaving_row = -1
    scored = 0
    best_score = S === :scaled ? _primal_dantzig_score(one(T)) : zero(S)
    weighted = _effective_pricing(workspace,:dual) != :dantzig
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        violation = max(_lower_violation(workspace.lower[index], workspace.primal[index]),
                        _upper_violation(workspace.upper[index], workspace.primal[index]))
        violation > workspace.options.primal_tolerance || continue
        scored += 1
        score = _dual_pricing_score(violation,workspace.pricing_weights[index],weighted,scoring)
        if (S === :scaled && leaving_row == -1) || score > best_score
            leaving_row = row
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.basic_indices),scored)
    return leaving_row
end

@inline function _breakpoint_before(a::Int,b::Int,steps,row)
    left,right = steps[a],steps[b]
    left < right && return true
    right < left && return false
    strength_a,strength_b = abs(row[a]),abs(row[b])
    return strength_a > strength_b || (strength_a == strength_b && a < b)
end

function _sift_breakpoint!(candidates,steps,row,root::Int,count::Int)
    value = candidates[root]
    while root <= count÷2
        child = 2root
        if child < count && _breakpoint_before(candidates[child+1],candidates[child],steps,row)
            child += 1
        end
        _breakpoint_before(candidates[child],value,steps,row) || break
        candidates[root] = candidates[child]
        root = child
    end
    candidates[root] = value
    return nothing
end

function _heapify_breakpoints!(candidates,steps,row)
    for root in length(candidates)÷2:-1:1
        _sift_breakpoint!(candidates,steps,row,root,length(candidates))
    end
    return nothing
end

function _pop_breakpoint!(candidates,steps,row)
    first = candidates[1]
    last = pop!(candidates)
    if !isempty(candidates)
        candidates[1] = last
        _sift_breakpoint!(candidates,steps,row,1,length(candidates))
    end
    return first
end

function _bound_flipping_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                                    orientation::T, violation::T) where {T}
    flips = workspace.scratch.flips
    empty!(flips)
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    # A boxed variable matters only when it can move in this tableau row.
    # Otherwise keep the linear Harris pass and its stronger pivot choice.
    has_boxed = false
    for index in eachindex(workspace.basis.states)
        if isfinite(workspace.lower[index]) && isfinite(workspace.upper[index]) &&
           _dual_pivot_eligible(workspace, index, orientation * tableau_row[index], cutoff)
            has_boxed = true
            break
        end
    end
    has_boxed || return dual_ratio_test(workspace, tableau_row, orientation), flips, false

    candidates = workspace.scratch.candidates
    empty!(candidates)
    steps = workspace.scratch.ratio_steps
    length(steps) < length(tableau_row) && resize!(steps, length(tableau_row))
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        step = workspace.reduced_costs[index] / coefficient
        if !isfinite(step) || step < zero(T)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        steps[index] = step
        push!(candidates, index)
    end
    isempty(candidates) && return -1, flips, false
    # Most pivots consume a small prefix. Building a heap costs linear work
    # and reuses the candidate buffer instead of sorting every breakpoint.
    _heapify_breakpoints!(candidates,steps,tableau_row)
    sort_after = max(32,length(candidates)÷16)
    sorted_tail = false
    tail_position = 1

    remaining = violation
    while sorted_tail ? tail_position <= length(candidates) : !isempty(candidates)
        index = if sorted_tail
            value = candidates[tail_position]
            tail_position += 1
            value
        else
            _pop_breakpoint!(candidates,steps,tableau_row)
        end
        state = workspace.basis.states[index]
        opposite = state == AT_LOWER ? workspace.upper[index] : workspace.lower[index]
        if state == FREE_NONBASIC || !isfinite(opposite)
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        width = bound_value(workspace.upper[index]) - bound_value(workspace.lower[index])
        gain = abs(tableau_row[index]) * width
        if !isfinite(width) || !isfinite(gain)
            empty!(flips)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        if remaining <= gain + workspace.options.primal_tolerance
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        push!(flips, index)
        remaining -= gain
        if !sorted_tail && length(flips) >= sort_after
            # A long flip sequence no longer benefits from extracting a
            # prefix. Finish in-place; the explicit index key restores the
            # same stable ties after heap construction shuffled the tail.
            sort!(candidates;lt=(a,b) -> _breakpoint_before(a,b,steps,tableau_row),alg=QuickSort)
            sorted_tail = true
        end
    end
    return -1, flips, true
end

@inline function _eligible_with_cutoff(workspace::SimplexWorkspace{T},index::Int,
                                      coefficient::T,cutoff::T,
                                      negative::T,ready::Bool) where {T<:Union{BigFloat,Rational{BigInt}}}
    state = workspace.basis.states[index]
    _is_fixed(workspace.lower[index],workspace.upper[index]) && return false,negative,ready
    if state == AT_LOWER
        return coefficient > cutoff,negative,ready
    elseif state == AT_UPPER
        if !ready
            negative = -cutoff
            ready = true
        end
        return coefficient < negative,negative,ready
    elseif state == FREE_NONBASIC
        return abs(coefficient) > cutoff,negative,ready
    end
    return false,negative,ready
end
function _bound_flipping_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                                    orientation::T, violation::T) where {T<:Union{BigFloat,Rational{BigInt}}}
    flips = workspace.scratch.flips
    empty!(flips)
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    # A boxed variable matters only when it can move in this tableau row.
    # Otherwise keep the linear Harris pass and its stronger pivot choice.
    has_boxed = false
    negative_cutoff = cutoff
    negative_ready = false
    for index in eachindex(workspace.basis.states)
        if isfinite(workspace.lower[index]) && isfinite(workspace.upper[index])
            eligible,negative_cutoff,negative_ready = _eligible_with_cutoff(
                workspace,index,orientation * tableau_row[index],cutoff,
                negative_cutoff,negative_ready)
            if eligible
                has_boxed = true
                break
            end
        end
    end
    has_boxed || return dual_ratio_test(workspace, tableau_row, orientation), flips, false

    candidates = workspace.scratch.candidates
    empty!(candidates)
    steps = workspace.scratch.ratio_steps
    length(steps) < length(tableau_row) && resize!(steps, length(tableau_row))
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        eligible,negative_cutoff,negative_ready = _eligible_with_cutoff(
            workspace,index,coefficient,cutoff,negative_cutoff,negative_ready)
        eligible || continue
        step = workspace.reduced_costs[index] / coefficient
        if !isfinite(step) || step < 0
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        steps[index] = step
        push!(candidates, index)
    end
    isempty(candidates) && return -1, flips, false
    # Most pivots consume a small prefix. Building a heap costs linear work
    # and reuses the candidate buffer instead of sorting every breakpoint.
    _heapify_breakpoints!(candidates,steps,tableau_row)
    sort_after = max(32,length(candidates)÷16)
    sorted_tail = false
    tail_position = 1

    remaining = violation
    while sorted_tail ? tail_position <= length(candidates) : !isempty(candidates)
        index = if sorted_tail
            value = candidates[tail_position]
            tail_position += 1
            value
        else
            _pop_breakpoint!(candidates,steps,tableau_row)
        end
        state = workspace.basis.states[index]
        opposite = state == AT_LOWER ? workspace.upper[index] : workspace.lower[index]
        if state == FREE_NONBASIC || !isfinite(opposite)
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        width = bound_value(workspace.upper[index]) - bound_value(workspace.lower[index])
        gain = abs(tableau_row[index]) * width
        if !isfinite(width) || !isfinite(gain)
            empty!(flips)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        if remaining <= gain + workspace.options.primal_tolerance
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        push!(flips, index)
        remaining -= gain
        if !sorted_tail && length(flips) >= sort_after
            # A long flip sequence no longer benefits from extracting a
            # prefix. Finish in-place; the explicit index key restores the
            # same stable ties after heap construction shuffled the tail.
            sort!(candidates;lt=(a,b) -> _breakpoint_before(a,b,steps,tableau_row),alg=QuickSort)
            sorted_tail = true
        end
    end
    return -1, flips, true
end


end

const ComparisonCandidate=JSimplex
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
const METHODS=(:original,:candidate)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
snap(a)=(a,map(copy,a),deepcopy(a))
intact(a,s)=all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
function pricing_state(w)
 s=w.scratch.pricing
 isnothing(s) ? () : tuple((getfield(s,n) for n in fieldnames(typeof(s)))...)
end
function pool_state(w)
 p=w.scratch.pricing_pool
 isnothing(p) ? () : tuple((getfield(p,n) for n in fieldnames(typeof(p)))...)
end
scalar_inputs(v)=(v.step,v.orientation,v.violation,v.w.options.dual_tolerance)
function outputs(w)
 (w.costs,w.reduced_costs,w.primal,w.pricing_weights,w.basis.states,w.scratch.candidates,w.scratch.flips,w.scratch.ratio_steps,w.scratch.ratio_gains,w.perturbed,pricing_state(w),pool_state(w))
end
function immutable_inputs(v)
 w=v.w;A=w.problem.A
 base=(A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights,v.row)
 v.scope===:update ? base : (base...,w.costs,w.reduced_costs)
end
function workspace(::Type{T},n,scope,density,pattern) where T
 m=scope in (:dual,:dual_control) ? n : 4
 columns=scope in (:dual,:dual_control) ? 4 : n
 A=zeros(T,m,columns)
 for j in 1:columns,i in 1:m
  if density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//8);end
 end
 p=LinearProblem(sparse(A),zeros(T,columns);row_lower=zeros(T,m),row_upper=zeros(T,m),column_lower=zeros(T,columns),column_upper=fill(T(4),columns))
 opt=SolverOptions(T;algorithm=scope===:primal ? :primal : :dual,pricing=scope===:dual ? :auto : :dantzig,verbose=false)
 policy=J.NumericalPolicy(T;refactor_timing=false)
 progress=J.SimplexProgressContext(p;numerical_policy=policy)
 w=J._initialize_workspace_state(p,opt;progress)
 fill!(w.pricing_weights,one(T))
 if scope===:dual
  J._prepare_auto_pricing!(w,:dual)
  w.scratch.pricing.active=:dantzig;w.scratch.pricing.return_mode=:dantzig
 end
 if scope in (:dual,:dual_control)
  for (i,index) in enumerate(w.basis.basic_indices)
   magnitude=T((i+1)//8)
   w.primal[index]=pattern===:lower ? -magnitude : pattern===:upper ? magnitude : isodd(i) ? -magnitude : magnitude
  end
 end
 w
end
function fixture(::Type{T},n,scope,density,pattern) where T
 w=workspace(T,n,scope,density,pattern)
 if scope===:update
  pool=J._pricing_pool!(w,:dual);pool.valid=true;pool.full_scan=true;append!(pool.indices,[2,3])
 end
 row=zeros(T,length(w.basis.states));columns=size(w.problem.A,2)
 for i in 1:columns
  active=density===:dense||i%4==0
  magnitude=T((i+1)//8)
  if scope===:primal
   upper=pattern===:positive||pattern===:mixed&&isodd(i)
   w.basis.states[i]=upper ? J.AT_UPPER : J.AT_LOWER
   w.reduced_costs[i]=active ? (upper ? magnitude : -magnitude) : zero(T)
  elseif scope===:update
   state=pattern===:lower ? J.AT_LOWER : pattern===:upper ? J.AT_UPPER : J.FREE_NONBASIC
   w.basis.states[i]=state
   row[i]=active ? T((i%3+1)//8) : zero(T)
   w.reduced_costs[i]=state==J.AT_UPPER ? -T(2) : T(2)
  elseif scope===:bfrt
   negative=pattern===:tied_negative||pattern===:unique_negative||pattern===:tied_mixed&&isodd(i)
   w.basis.states[i]=negative ? J.AT_UPPER : J.AT_LOWER
   w.upper[i]=Bound(one(T))
   row[i]=active ? (negative ? -magnitude : magnitude) : zero(T)
   w.reduced_costs[i]=row[i]*(startswith(String(pattern),"unique") ? T((i+1)//16) : one(T))
  end
 end
 resize!(w.scratch.ratio_steps,length(row));fill!(w.scratch.ratio_steps,T(99))
 resize!(w.scratch.ratio_gains,length(row));fill!(w.scratch.ratio_gains,T(77))
 (w=w,row=row,scope=scope,step=T(1//4),orientation=one(T),violation=T(10^6),leaving=w.basis.basic_indices[1],entering=1,costs=copy(w.costs),prices=copy(w.reduced_costs),perturbed=w.perturbed)
end
function reset_fixture!(v)
 if v.scope===:update
  copyto!(v.w.costs,v.costs);copyto!(v.w.reduced_costs,v.prices);v.w.perturbed=v.perturbed
  p=v.w.scratch.pricing_pool;p.valid=true;p.full_scan=true;empty!(p.indices);append!(p.indices,[2,3]);p.basis_generation=UInt(0);p.cost_generation=UInt(0)
 end
 nothing
end
@noinline function runwhole(::Val{:original},::Val{:update},v)
 ComparisonReference.update_duals!(v.w,v.row,v.leaving,v.entering,v.step)
 Int(isfinite(v.w.reduced_costs[2]))+Int(v.w.perturbed)
end
@noinline function runwhole(::Val{:candidate},::Val{:update},v)
 ComparisonCandidate.update_duals!(v.w,v.row,v.leaving,v.entering,v.step)
 Int(isfinite(v.w.reduced_costs[2]))+Int(v.w.perturbed)
end
@noinline runwhole(::Val{:original},::Val{:primal},v)=first(ComparisonReference._primal_entering(v.w,v.w.options.dual_tolerance))
@noinline runwhole(::Val{:candidate},::Val{:primal},v)=first(ComparisonCandidate._primal_entering(v.w,v.w.options.dual_tolerance))
@noinline runwhole(::Val{:original},::Val{:dual},v)=ComparisonReference.dual_edge_selection(v.w)
@noinline runwhole(::Val{:candidate},::Val{:dual},v)=ComparisonCandidate.dual_edge_selection(v.w)
@noinline runwhole(::Val{:original},::Val{:dual_control},v)=ComparisonReference.dual_edge_selection(v.w)
@noinline runwhole(::Val{:candidate},::Val{:dual_control},v)=ComparisonCandidate.dual_edge_selection(v.w)
@noinline function runwhole(::Val{:original},::Val{:bfrt},v)
 index,flips,exhausted=ComparisonReference._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
 index+length(flips)+Int(exhausted)
end
@noinline function runwhole(::Val{:candidate},::Val{:bfrt},v)
 index,flips,exhausted=ComparisonCandidate._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
 index+length(flips)+Int(exhausted)
end
function timed(method::M,scope::S,v::V) where {M,S,V}
 t=@timed runwhole(method,scope,v);merge(cost(t),Dict("sink"=>t.value))
end
function patterns(scope)
 scope===:update ? (:lower,:upper,:free) : scope===:primal ? (:positive,:negative,:mixed) : scope in (:dual,:dual_control) ? (:lower,:upper) : (:tied_positive,:tied_negative,:tied_mixed,:unique_positive)
end
function scopes(::Type{T}) where T
 T===Rational{BigInt}||T===Rational{Int64} ? (:update,:bfrt) : (:update,:primal,:dual,:dual_control,:bfrt)
end
function scalar_correctness(::Type{T}) where T
 if T===BigFloat
  for stored in (precision(T),512)
   xs=setprecision(()->BigFloat[0,-0.0,1,-1,3//7,-3//7,Inf,-Inf,NaN,floatmax(BigFloat),-floatmax(BigFloat),nextfloat(zero(BigFloat)),-nextfloat(zero(BigFloat))],T,stored)
   for x in xs
    before=deepcopy(x);owner=x
    @test same(capture(()->ComparisonReference._primal_dantzig_score(x)),capture(()->ComparisonCandidate._primal_dantzig_score(x)))
    @test x===owner&&same(x,before)
   end
   steps,row=setprecision(()->(BigFloat[0,-0.0,1,1,2,2],BigFloat[1,-1,Inf,-Inf,3//7,-3//7]),T,stored)
   for a in eachindex(steps),b in eachindex(steps)
    @test ComparisonReference._breakpoint_before(a,b,steps,row)===ComparisonCandidate._breakpoint_before(a,b,steps,row)
   end
  end
 end
end
function correctness(::Type{T}) where T
 @testset "Whole dual comparisons $T" begin
  scalar_correctness(T)
  for scope in scopes(T),density in (:sparse,:dense),pattern in patterns(scope)
   a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern);sa=snap(immutable_inputs(a));sb=snap(immutable_inputs(b));ca=deepcopy(scalar_inputs(a));cb=deepcopy(scalar_inputs(b));sv=Val(scope)
   ra=capture(()->runwhole(Val(:original),sv,a));rb=capture(()->runwhole(Val(:candidate),sv,b))
   @test same(ra,rb)
   @test same(outputs(a.w),outputs(b.w))
   @test intact(immutable_inputs(a),sa)&&intact(immutable_inputs(b),sb)
   @test same(scalar_inputs(a),ca)&&same(scalar_inputs(b),cb)
   if scope===:primal;@test ra[1]===:value&&ra[2]==8;end
   if scope in (:dual,:dual_control);@test ra[1]===:value&&ra[2]==8;end
   # Equal repeated calls, explicit resets and the same counter advancement.
   reset_fixture!(a);reset_fixture!(b)
   @test runwhole(Val(:original),sv,a)==runwhole(Val(:candidate),sv,b)
   @test same(outputs(a.w),outputs(b.w))
   if scope===:bfrt
    x=ComparisonReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation);y=ComparisonCandidate._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation)
    @test same(x,y)&&x[3]&&x[2]===a.w.scratch.flips&&y[2]===b.w.scratch.flips
   end
  end
  # Update perturbation and partial-failure paths, including aliasing RHS.
  for variant in (:perturb,:upper_perturb,:free_perturb,:zero_step,:fixed,:basic,:short_row,:short_bounds,:row_prices,:row_costs)
   a=fixture(T,8,:update,:dense,:lower);b=fixture(T,8,:update,:dense,:lower)
   if variant===:zero_step;a=merge(a,(step=zero(T),));b=merge(b,(step=zero(T),));end
   old_a=copy(a.w.reduced_costs);old_b=copy(b.w.reduced_costs)
   for which in (:a,:b)
    v=which===:a ? a : b
    if variant===:perturb;fill!(v.w.reduced_costs,-one(T))
    elseif variant===:upper_perturb;fill!(v.w.reduced_costs,one(T));v.w.basis.states[2]=J.AT_UPPER
    elseif variant===:free_perturb;fill!(v.w.reduced_costs,one(T));v.w.basis.states[2]=J.FREE_NONBASIC
    elseif variant===:fixed;v.w.upper[2]=Bound(zero(T))
    elseif variant===:basic;v.w.basis.states[2]=J.BASIC
    elseif variant===:short_row
     v=merge(v,(row=v.row[1:4],))
    elseif variant===:short_bounds;resize!(v.w.lower,4)
    elseif variant===:row_prices;v=merge(v,(row=v.w.reduced_costs,))
    elseif variant===:row_costs;v=merge(v,(row=v.w.costs,))
    end
    if which===:a;a=v;else;b=v;end
   end
   ra=capture(()->ComparisonReference.update_duals!(a.w,a.row,a.leaving,a.entering,a.step));rb=capture(()->ComparisonCandidate.update_duals!(b.w,b.row,b.leaving,b.entering,b.step))
   @test same(ra,rb)&&same(outputs(a.w),outputs(b.w))
   if variant in (:short_row,:short_bounds);@test ra[1]===:error&&ra[2]===BoundsError;end
   if variant===:perturb;@test a.w.perturbed&&all(iszero,a.w.reduced_costs[2:8]);end
   if variant in (:perturb,:upper_perturb,:free_perturb)
    pool=a.w.scratch.pricing_pool
    @test a.w.perturbed&&!pool.valid&&!pool.full_scan&&isempty(pool.indices)&&pool.cost_generation==1&&pool.basis_generation==0
   end
   if variant===:zero_step&&(T===BigFloat||T===Rational{BigInt})
    @test a.w.reduced_costs[2]!==old_a[2]&&b.w.reduced_costs[2]!==old_b[2]
   end
  end
  for variant in (:prefix,:flip_pivot,:rejected,:fallback,:short_row,:zero_steps)
   a=fixture(T,8,:bfrt,:dense,:tied_positive);b=fixture(T,8,:bfrt,:dense,:tied_positive)
   if variant===:short_row;a=merge(a,(row=T[],));b=merge(b,(row=T[],));end
   if variant in (:rejected,:prefix);a=merge(a,(violation=T(1//16),));b=merge(b,(violation=T(1//16),));end
   if variant===:flip_pivot;a=merge(a,(violation=T(3//2),));b=merge(b,(violation=T(3//2),));end
   for v in (a,b)
    if variant===:rejected;push!(v.w.scratch.rejected_entering,8)
    elseif variant===:fallback;v.w.reduced_costs[8]=-v.row[8]
    elseif variant===:zero_steps;fill!(v.w.reduced_costs,zero(T))
    end
   end
   x=capture(()->ComparisonReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation));y=capture(()->ComparisonCandidate._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation))
   @test same(x,y)&&same(outputs(a.w),outputs(b.w))
   if variant===:short_row;@test x[1]===:error&&x[2]===BoundsError;end
   if variant===:prefix;@test x[1]===:value&&x[2][1]==8&&isempty(x[2][2])&&!x[2][3];end
   if variant===:flip_pivot;@test x[1]===:value&&x[2][1]==7&&x[2][2]==[8]&&!x[2][3];end
   if variant===:rejected;@test x[1]===:value&&x[2][1]==-1&&isempty(x[2][2])&&!x[2][3];end
   if variant===:fallback;@test x[1]===:value&&x[2][1]==J.dual_ratio_test(a.w,a.row,a.orientation)&&isempty(x[2][2])&&!x[2][3];end
  end
 end
end

function allocation_gate(::Type{T},scope,pattern) where T
 a=fixture(T,128,scope,:dense,pattern);b=fixture(T,128,scope,:dense,pattern);sv=Val(scope)
 for _ in 1:3,method in METHODS
  v=method===:original ? a : b;reset_fixture!(v);timed(Val(method),sv,v)
 end
 before=Tuple{Int,Int}[];after=Tuple{Int,Int}[]
 for round in 1:3
  sinks=Int[]
  for method in (isodd(round) ? METHODS : reverse(METHODS))
   v=method===:original ? a : b;reset_fixture!(v);r=timed(Val(method),sv,v)
   @test r["compile_seconds"]==r["recompile_seconds"]==0
   push!(sinks,r["sink"]);push!(method===:original ? before : after,(Int(r["bytes"]),Int(r["events"])))
  end
  @test sinks[1]==sinks[2]
  @test same(outputs(a.w),outputs(b.w))
 end
 @test all(100*after[i][1]<97*before[i][1]&&100*after[i][2]<97*before[i][2] for i in eachindex(before)) # RED costgate
end
@testset "Generic dual comparisons" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do;setrounding(BigFloat,mode) do;correctness(BigFloat);end;end
 end
 for T in (Rational{BigInt},Float32,Float64,Rational{Int64});correctness(T);end
 @testset "Whole-call allocation gates" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    for T in (BigFloat,Rational{BigInt}),pattern in (:lower,:free);allocation_gate(T,:update,pattern);end
    allocation_gate(BigFloat,:primal,:positive)
    allocation_gate(BigFloat,:dual,:lower)
    allocation_gate(BigFloat,:bfrt,:tied_positive)
   end
  end
 end
 @testset "Unchanged native and fixed-rational costs" begin
  for T in (Float32,Float64,Rational{Int64}),scope in scopes(T)
   pattern=first(patterns(scope));a=fixture(T,32,scope,:dense,pattern);b=fixture(T,32,scope,:dense,pattern);sv=Val(scope)
   for _ in 1:3,method in METHODS
    v=method===:original ? a : b;reset_fixture!(v);timed(Val(method),sv,v)
   end
   reset_fixture!(a);reset_fixture!(b);x=timed(Val(:original),sv,a);y=timed(Val(:candidate),sv,b)
   @test x["compile_seconds"]==x["recompile_seconds"]==y["compile_seconds"]==y["recompile_seconds"]==0
   @test (x["bytes"],x["events"],x["sink"])==(y["bytes"],y["events"],y["sink"])
  end
 end
end
end
