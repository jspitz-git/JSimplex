module GenericPivotScalarsTests
using Test,JSimplex,SparseArrays,LinearAlgebra
module PivotReference
using LinearAlgebra
using JSimplex: SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_fixed,_primal_direction_magnitude,_primal_weighted_score,_primal_dantzig_score,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_record_full_pricing!,Bound,_unbounded_bound,_dual_pivot_cutoff,_dual_pivot_eligible,_dual_ratio_tolerance,bound_value,_heapify_breakpoints!,_pop_breakpoint!,_breakpoint_before
function dual_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                         orientation::T=one(T))::Int where {T}
    candidates = workspace.scratch.candidates
    empty!(candidates)
    maximum_step = _unbounded_bound(T)
    tolerance = workspace.options.dual_tolerance
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        push!(candidates, index)
        relaxed_step = (workspace.reduced_costs[index] +
                        _dual_ratio_tolerance(coefficient,tolerance)) / coefficient
        # An overflowed positive relaxation imposes no finite step limit.
        # The selected pivot's actual step is checked before any update.
        if isfinite(relaxed_step) &&
           (!isfinite(maximum_step) || relaxed_step < bound_value(maximum_step))
            maximum_step = Bound(relaxed_step)
        end
    end

    entering_index = -1
    largest_pivot = zero(T)
    for index in candidates
        index in workspace.scratch.rejected_entering && continue
        coefficient = orientation * tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        within_limit = !isfinite(maximum_step) || step <= bound_value(maximum_step)
        if within_limit && abs(coefficient) > largest_pivot
            entering_index = index
            largest_pivot = abs(coefficient)
        end
    end
    return entering_index
end

# Keep the tested magnitude when a BigFloat pivot becomes the current best.
function dual_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                         orientation::T=one(T))::Int where {T<:BigFloat}
    candidates = workspace.scratch.candidates
    empty!(candidates)
    maximum_step = _unbounded_bound(T)
    tolerance = workspace.options.dual_tolerance
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        push!(candidates, index)
        relaxed_step = (workspace.reduced_costs[index] +
                        _dual_ratio_tolerance(coefficient,tolerance)) / coefficient
        # An overflowed positive relaxation imposes no finite step limit.
        # The selected pivot's actual step is checked before any update.
        if isfinite(relaxed_step) &&
           (!isfinite(maximum_step) || relaxed_step < bound_value(maximum_step))
            maximum_step = Bound(relaxed_step)
        end
    end

    entering_index = -1
    largest_pivot = zero(T)
    for index in candidates
        index in workspace.scratch.rejected_entering && continue
        coefficient = orientation * tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        within_limit = !isfinite(maximum_step) || step <= bound_value(maximum_step)
        if within_limit
            magnitude = abs(coefficient)
            if magnitude > largest_pivot
                entering_index = index
                largest_pivot = magnitude
            end
        end
    end
    return entering_index
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
fields(x)=tuple((getfield(x,n) for n in fieldnames(typeof(x)))...)
pricing_state(w)=isnothing(w.scratch.pricing) ? () : fields(w.scratch.pricing)
pool_state(w)=isnothing(w.scratch.pricing_pool) ? () : fields(w.scratch.pricing_pool)
outputs(w)=(w.scratch.candidates,w.scratch.flips,w.scratch.ratio_steps,w.scratch.ratio_gains,pricing_state(w),pool_state(w))
function inputs(v)
 w=v.w;A=w.problem.A
 (A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights,v.row)
end
scalar_inputs(v)=(v.tol,v.orientation,v.violation,fields(v.w.options),fields(v.w.progress.numerical_policy))
ispartial(scope)=scope in (:partial_hit,:partial_scan)
isprimal(scope)=scope in (:primal,:partial_hit,:partial_scan)
scopes(::Type{T}) where T=(:harris,:primal,:partial_hit,:partial_scan,:bfrt_prefix,:bfrt_exhaust)
patterns(scope)=scope===:harris ? (:lower,:upper,:mixed) : isprimal(scope) ? (:positive,:negative,:mixed,:first_best) : (:positive,:negative,:mixed,:tied_positive)
function fixture(::Type{T},n,scope,density,pattern;diagnostics=false,pivot_validation=false) where T
 m=ispartial(scope) ? 128 : 4
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//8);end
 end
 p=LinearProblem(sparse(A),zeros(T,n);row_lower=zeros(T,m),row_upper=zeros(T,m),column_lower=zeros(T,n),column_upper=fill(T(4),n))
 opt=SolverOptions(T;algorithm=isprimal(scope) ? :primal : :dual,pricing=:dantzig,partial_pricing=ispartial(scope),verbose=false)
 policy=J.NumericalPolicy(T;refactor_timing=false,partial_pricing=ispartial(scope),pivot_validation)
 progress=J.SimplexProgressContext(p;numerical_policy=policy,diagnostics=diagnostics ? J.SimplexDiagnostics() : nothing)
 w=J._initialize_workspace_state(p,opt;progress)
 row=zeros(T,length(w.basis.states));fill!(w.pricing_weights,one(T))
 for i in 1:n
  active=density===:dense||i%4==0;ordinal=density===:dense ? i : i÷4
  magnitude=T((i+1)//8)
  if isprimal(scope)
   positive=pattern in (:positive,:first_best)||pattern===:mixed&&isodd(ordinal)
   w.basis.states[i]=positive ? J.AT_UPPER : J.AT_LOWER
   value=pattern===:first_best ? T((n-i+2)//8) : magnitude
   w.reduced_costs[i]=active ? (positive ? value : -value) : zero(T)
  else
   negative=pattern in (:upper,:negative)||pattern===:mixed&&isodd(ordinal)
   w.basis.states[i]=negative ? J.AT_UPPER : J.AT_LOWER
   w.upper[i]=Bound(one(T))
   row[i]=active ? (negative ? -magnitude : magnitude) : zero(T)
   step=pattern===:tied_positive ? one(T) : T((i+1)//16)
   w.reduced_costs[i]=row[i]*step
  end
 end
 resize!(w.scratch.ratio_steps,length(row));fill!(w.scratch.ratio_steps,T(99))
 resize!(w.scratch.ratio_gains,length(row));fill!(w.scratch.ratio_gains,T(77))
 if ispartial(scope)
  @assert J._partial_pricing_enabled(w,:primal)
  pool=J._pricing_pool!(w,:primal);pool.valid=false
  J._primal_entering(w,w.options.dual_tolerance) # actual complete fullscan history
  @assert pool.valid&&pool.full_scans==1&&!isempty(pool.indices)
 end
 (w=w,row=row,scope=scope,tol=w.options.dual_tolerance,orientation=one(T),violation=scope===:bfrt_prefix ? T(1//16) : T(10^6))
end
reset_fixture!(v)=(v.scope===:partial_scan&&J._invalidate_pricing_pool!(v.w;basis=false);nothing)
@noinline runwhole(::Val{:original},::Val{:harris},v)=PivotReference.dual_ratio_test(v.w,v.row,v.orientation)
@noinline runwhole(::Val{:candidate},::Val{:harris},v)=JSimplex.dual_ratio_test(v.w,v.row,v.orientation)
@inline function direction_sink(entering,direction)
 3entering+(iszero(direction) ? 0 : signbit(direction) ? -1 : 1)
end
for scope in (:primal,:partial_hit,:partial_scan)
 @eval begin
  @noinline function runwhole(::Val{:original},::Val{$(QuoteNode(scope))},v)
   entering,direction=PivotReference._primal_entering(v.w,v.tol);direction_sink(entering,direction)
  end
  @noinline function runwhole(::Val{:candidate},::Val{$(QuoteNode(scope))},v)
   entering,direction=JSimplex._primal_entering(v.w,v.tol);direction_sink(entering,direction)
  end
 end
end
for scope in (:bfrt_prefix,:bfrt_exhaust)
 @eval begin
  @noinline function runwhole(::Val{:original},::Val{$(QuoteNode(scope))},v)
   index,flips,exhausted=PivotReference._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
   1000000index+2length(flips)+Int(exhausted)
  end
  @noinline function runwhole(::Val{:candidate},::Val{$(QuoteNode(scope))},v)
   index,flips,exhausted=JSimplex._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
   1000000index+2length(flips)+Int(exhausted)
  end
 end
end
function timed(method::M,scope::S,v::V) where {M,S,V}
 t=@timed runwhole(method,scope,v);merge(cost(t),Dict("sink"=>t.value))
end
function change_tol!(w,tol)
 opts=w.options;w.options=typeof(opts)((n===:dual_tolerance ? tol : getfield(opts,n) for n in fieldnames(typeof(opts)))...);nothing
end
function extra_correctness(::Type{T}) where T
 for variant in (:free,:ties,:pivot_validation,:overflow)
  a=fixture(T,8,:harris,:dense,:mixed;pivot_validation=variant===:pivot_validation);b=fixture(T,8,:harris,:dense,:mixed;pivot_validation=variant===:pivot_validation)
  for v in (a,b)
   if variant===:free
    v.w.basis.states[1]=J.FREE_NONBASIC;v.w.lower[1]=J._unbounded_bound(T);v.w.upper[1]=J._unbounded_bound(T)
   elseif variant===:ties
    for i in 1:8;v.row[i]=v.row[i]<0 ? -one(T) : one(T);v.w.reduced_costs[i]=v.row[i];end
   elseif variant===:overflow&&T<:AbstractFloat
    change_tol!(v.w,T(Inf))
   end
  end
  @test same(capture(()->PivotReference.dual_ratio_test(a.w,a.row,a.orientation)),capture(()->JSimplex.dual_ratio_test(b.w,b.row,b.orientation)))
  @test same(outputs(a.w),outputs(b.w))
 end
 for variant in (:no_boxed,:free,:unbounded,:wide_row)
  a=fixture(T,8,:bfrt_prefix,:dense,:positive);b=fixture(T,8,:bfrt_prefix,:dense,:positive)
  for v in (a,b)
   if variant===:no_boxed
    for i in 1:8;v.w.upper[i]=J._unbounded_bound(T);end
   elseif variant in (:free,:unbounded)
    v.w.upper[1]=J._unbounded_bound(T)
    if variant===:free;v.w.basis.states[1]=J.FREE_NONBASIC;v.w.lower[1]=J._unbounded_bound(T);end
   elseif T===BigFloat
    v.row[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
   end
  end
  @test same(capture(()->PivotReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation)),capture(()->JSimplex._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation)))
  @test same(outputs(a.w),outputs(b.w))
 end
 for scope in (:primal,:partial_hit,:partial_scan)
  a=fixture(T,8,scope,:dense,:positive;diagnostics=true);b=fixture(T,8,scope,:dense,:positive;diagnostics=true)
  if T===BigFloat
   for v in (a,b);v.w.reduced_costs[8]=setprecision(()->BigFloat(33//7),BigFloat,512);end
  end
  reset_fixture!(a);reset_fixture!(b)
  ra=PivotReference._primal_entering(a.w,a.tol);rb=JSimplex._primal_entering(b.w,b.tol)
  @test same(ra,rb)&&same(fields(a.w.progress.diagnostics),fields(b.w.progress.diagnostics))
  if scope===:primal;@test a.w.progress.diagnostics.counts[:pricing_scanned_entries]==length(a.w.basis.states);end
  if T===BigFloat||T===Rational{BigInt}
   ra2=PivotReference._primal_entering(a.w,a.tol);rb2=JSimplex._primal_entering(b.w,b.tol)
   if T===BigFloat;@test ra[2]!==ra2[2]&&rb[2]!==rb2[2]
   else;@test numerator(ra[2])!==numerator(ra2[2])&&numerator(rb[2])!==numerator(rb2[2]);end
  end
 end
end
function correctness(::Type{T}) where T
 @testset "Pivot scalars correctness $T" begin
  extra_correctness(T)
  for scope in scopes(T),density in (:sparse,:dense),pattern in patterns(scope)
   a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern);sv=Val(scope)
   sa=snap(inputs(a));sb=snap(inputs(b));ca=deepcopy(scalar_inputs(a));cb=deepcopy(scalar_inputs(b))
   reset_fixture!(a);reset_fixture!(b)
   @test runwhole(Val(:original),sv,a)==runwhole(Val(:candidate),sv,b)
   @test same(outputs(a.w),outputs(b.w))
   @test intact(inputs(a),sa)&&intact(inputs(b),sb)
   @test same(scalar_inputs(a),ca)&&same(scalar_inputs(b),cb)
   if isprimal(scope)
    ra=PivotReference._primal_entering(a.w,a.tol);rb=JSimplex._primal_entering(b.w,b.tol)
    @test same(ra,rb)&&ra[1]>0&&abs(ra[2])==1
    if T===BigFloat||T===Rational{BigInt};@test ra[2]!==a.w.reduced_costs[ra[1]]&&rb[2]!==b.w.reduced_costs[rb[1]];end
   elseif scope===:bfrt_prefix
    x=PivotReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation);y=JSimplex._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation)
    @test same(x,y)&&x[1]>0&&isempty(x[2])&&!x[3]
   elseif scope===:bfrt_exhaust
    x=PivotReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation);y=JSimplex._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation)
    @test same(x,y)&&x[1]==-1&&x[3]&&length(x[2])==(density===:dense ? 8 : 2)
   end
  end
  for variant in (:fixed,:basic,:rejected,:none,:short_bounds,:short_states,:short_prices,:nonfinite,:mixed_precision)
   a=fixture(T,8,:harris,:dense,:mixed);b=fixture(T,8,:harris,:dense,:mixed)
   for which in (:a,:b)
    v=which===:a ? a : b
    if variant===:fixed;v.w.upper[2]=Bound(zero(T))
    elseif variant===:basic;v.w.basis.states[2]=J.BASIC
    elseif variant===:rejected;push!(v.w.scratch.rejected_entering,1)
    elseif variant===:none;fill!(v.row,zero(T))
    elseif variant===:short_bounds;resize!(v.w.lower,4)
    elseif variant===:short_states;resize!(v.w.basis.states,4)
    elseif variant===:short_prices
     for i in 1:4;v.w.basis.states[i]=J.AT_LOWER;v.row[i]=T(i);v.w.reduced_costs[i]=T(i);end
     v.w.basis.states[5]=J.AT_UPPER;v.row[5]=-one(T);resize!(v.w.reduced_costs,4)
    elseif variant===:nonfinite&&T<:AbstractFloat;v.row[1]=T(-Inf)
    elseif variant===:mixed_precision&&T===BigFloat
     wide=setprecision(()->BigFloat(3//7),BigFloat,512);change_tol!(v.w,wide);v=merge(v,(tol=wide,))
    end
    if which===:a;a=v;else;b=v;end
   end
   x=capture(()->PivotReference.dual_ratio_test(a.w,a.row,a.orientation));y=capture(()->JSimplex.dual_ratio_test(b.w,b.row,b.orientation))
   @test same(x,y)&&same(outputs(a.w),outputs(b.w))
   if variant in (:short_bounds,:short_states,:short_prices);@test x[1]===:error&&x[2]===BoundsError;end
   if variant===:none;@test x==(:value,-1);end
  end
  for scope in (:primal,:partial_hit,:partial_scan),variant in (:none,:rejected,:zero_negative_tolerance,:nan,:current_pool_mutation)
   a=fixture(T,8,scope,:dense,:positive);b=fixture(T,8,scope,:dense,:positive)
   if variant===:zero_negative_tolerance;a=merge(a,(tol=-one(T),));b=merge(b,(tol=-one(T),));end
   for v in (a,b)
    if variant in (:none,:zero_negative_tolerance,:current_pool_mutation);fill!(v.w.reduced_costs,zero(T));end
    if variant===:zero_negative_tolerance&&T<:AbstractFloat;v.w.reduced_costs[1]=-zero(T);end
    if variant===:rejected;push!(v.w.scratch.rejected_entering,8);end
    if variant===:nan&&T<:AbstractFloat;v.w.reduced_costs[8]=T(NaN);end
   end
   x=capture(()->PivotReference._primal_entering(a.w,a.tol));y=capture(()->JSimplex._primal_entering(b.w,b.tol))
   @test same(x,y)&&same(outputs(a.w),outputs(b.w))
   if variant in (:none,:current_pool_mutation);@test x[1]===:value&&x[2][1]==0&&iszero(x[2][2]);end
   if variant===:zero_negative_tolerance;@test x[1]===:value&&x[2][1]==1&&x[2][2]==-one(T);end
  end
  for scope in (:bfrt_prefix,:bfrt_exhaust),variant in (:rejected,:negative_step,:infinite_gain,:short_row,:flip_then_pivot)
   a=fixture(T,8,scope,:dense,:positive);b=fixture(T,8,scope,:dense,:positive)
   if variant===:short_row;a=merge(a,(row=T[],));b=merge(b,(row=T[],));end
   if variant===:flip_then_pivot;a=merge(a,(violation=T(9//16),));b=merge(b,(violation=T(9//16),));end
   for v in (a,b)
    if variant===:rejected;push!(v.w.scratch.rejected_entering,1)
    elseif variant===:negative_step;v.w.reduced_costs[1]=-v.row[1]
    elseif variant===:infinite_gain&&T<:AbstractFloat;v.row[1]=T(Inf);v.w.reduced_costs[1]=one(T)
    end
   end
   x=capture(()->PivotReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation));y=capture(()->JSimplex._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation))
   @test same(x,y)&&same(outputs(a.w),outputs(b.w))
   if variant===:short_row;@test x[1]===:error&&x[2]===BoundsError;end
   if variant===:flip_then_pivot;@test x[1]===:value&&x[2][1]==2&&x[2][2]==[1]&&!x[2][3];end
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
@testset "Generic pivot scalars" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do;setrounding(BigFloat,mode) do;correctness(BigFloat);end;end
 end
 for T in (Rational{BigInt},Float32,Float64,Rational{Int64});correctness(T);end
 @testset "Whole-call allocation gates" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    allocation_gate(BigFloat,:harris,:upper)
    for T in (BigFloat,Rational{BigInt}),pattern in (:positive,:negative);allocation_gate(T,:primal,pattern);end
    allocation_gate(BigFloat,:bfrt_exhaust,:positive)
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
   @test (x["events"],x["sink"])==(y["events"],y["sink"])
   if T!==Rational{Int64};@test x["bytes"]==y["bytes"];end
  end
 end
end
end
