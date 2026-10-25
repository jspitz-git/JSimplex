module GenericScalarBranchesTests
using Test,JSimplex,SparseArrays,LinearAlgebra
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
# Frozen baseline references; candidate calls exercise the actual package.
module Reference
using JSimplex,SparseArrays
using JSimplex: Bound,bound_value,LinearProblem,SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_exact,_is_fixed,_primal_nearest_rounding,_refined_primal_rows_feasible,_unbounded_bound,_dual_pivot_cutoff,_dual_pivot_eligible,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,_primal_direction_magnitude,_record_full_pricing!,_lower_violation,_upper_violation
function _primal_sum_bounds(left::T, right::T) where {T<:Rational}
    value = left + right
    return value, value
end

function _primal_sum_bounds(left::T, right::T) where {T<:AbstractFloat}
    iszero(left) && return right, right
    iszero(right) && return left, left
    isfinite(left) && precision(right) == precision(T) && left == -right &&
        return zero(T), zero(T)
    value = left + right
    # FastTwoSum is exact when intermediate residuals cannot underflow.
    # Other rounding modes and mixed BigFloat precisions use the enclosure.
    if isfinite(value) && _primal_nearest_rounding(T) &&
       precision(left) == precision(right) == precision(T) &&
       min(abs(left), abs(right)) >= ldexp(nextfloat(zero(T)), precision(T))
        large, small = abs(left) >= abs(right) ? (left, right) : (right, left)
        error = (large - value) + small
        if isfinite(error)
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

# Reuse invocation-local magnitudes only inside the original BigFloat guard.
function _primal_sum_bounds(left::BigFloat, right::BigFloat)
    T=BigFloat
    iszero(left) && return right, right
    iszero(right) && return left, left
    isfinite(left) && precision(right) == precision(T) && left == -right &&
        return zero(T), zero(T)
    value = left + right
    # FastTwoSum is exact when intermediate residuals cannot underflow.
    # Other rounding modes and mixed BigFloat precisions use the enclosure.
    if isfinite(value) && _primal_nearest_rounding(T) &&
       precision(left) == precision(right) == precision(T)
        left_magnitude, right_magnitude = abs(left), abs(right)
        if min(left_magnitude, right_magnitude) >= ldexp(nextfloat(zero(T)), precision(T))
            large, small = left_magnitude >= right_magnitude ? (left, right) : (right, left)
            error = (large - value) + small
            if isfinite(error)
                return error < zero(T) ? (prevfloat(value), value) :
                       error > zero(T) ? (value, nextfloat(value)) : (value, value)
            end
        end
    end
    return prevfloat(value), nextfloat(value)
end


_primal_difference_bounds(left::T, right::T) where {T<:Rational} =
    _primal_sum_bounds(left, -right)

function _primal_difference_bounds(left::T, right::T) where {T<:AbstractFloat}
    precision(right) == precision(T) && return _primal_sum_bounds(left, -right)
    # Negating an older, higher-precision tolerance can round before the sum.
    value = left - right
    return prevfloat(value), nextfloat(value)
end

# Integer comparison is exact and avoids temporary multiprecision constants.
_primal_positive_unit(value::T) where T = value == one(T)
_primal_positive_unit(value::BigFloat) = value == 1
_primal_negative_unit(value::T) where T = value == -one(T)
_primal_negative_unit(value::BigFloat) = value == -1

function _primal_product_bounds(left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return zero(T), zero(T)
    _primal_positive_unit(left) && return right, right
    _primal_positive_unit(right) && return left, left
    _primal_negative_unit(left) && precision(right) == precision(T) && return -right, -right
    _primal_negative_unit(right) && precision(left) == precision(T) && return -left, -left
    value = left * right
    if isfinite(value) && _primal_nearest_rounding(T)
        error = fma(left, right, -value)
        # A nonzero fused residual has a conclusive sign. Zero only proves
        # exactness when the product's finest possible bit cannot underflow.
        if isfinite(error) && (!iszero(error) ||
           abs(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
            return error < zero(T) ? (prevfloat(value), value) :
                   error > zero(T) ? (value, nextfloat(value)) : (value, value)
        end
    end
    return prevfloat(value), nextfloat(value)
end

function _primal_product_bounds(left::T, right::T) where {T<:Rational}
    value = left * right
    return value, value
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{true}) where {T<:Rational}
    values = A * primal
    return values, values
end

function _primal_row_bounds(A::SparseMatrixCSC{T,Int}, primal::Vector{T},
                            ::Val{false}) where {T<:AbstractFloat}
    lower, upper = Vector{T}(undef, size(A, 1)), Vector{T}(undef, size(A, 1))
    return _primal_row_bounds!(lower, upper, A, primal)
end

# Keep the allocating and reusable paths in the same arithmetic order.
function _primal_row_bounds!(lower::Vector{T}, upper::Vector{T},
                             A::SparseMatrixCSC{T,Int}, primal::Vector{T}) where {T<:AbstractFloat}
    fill!(lower, zero(T))
    fill!(upper, zero(T))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            product_lower, product_upper = _primal_product_bounds(A.nzval[position], primal[column])
            lower[row], _ = _primal_sum_bounds(lower[row], product_lower)
            _, upper[row] = _primal_sum_bounds(upper[row], product_upper)
        end
    end
    return lower, upper
end

function _primal_interval_within_bounds(value_lower::T, value_upper::T,
                                        lower::Bound{T}, upper::Bound{T},
                                        tolerance::T) where {T}
    isfinite(value_lower) && isfinite(value_upper) || return false
    if isfinite(lower) && value_lower < bound_value(lower)
        _, threshold = _primal_difference_bounds(bound_value(lower), tolerance)
        value_lower >= threshold || return false
    end
    if isfinite(upper) && value_upper > bound_value(upper)
        threshold, _ = _primal_sum_bounds(bound_value(upper), tolerance)
        value_upper <= threshold || return false
    end
    return true
end

function _within_primal_intervals(values_lower::AbstractVector{T}, values_upper::AbstractVector{T},
                                  lower::AbstractVector{Bound{T}}, upper::AbstractVector{Bound{T}},
                                  tolerance::T) where {T}
    for index in eachindex(values_lower)
        _primal_interval_within_bounds(values_lower[index], values_upper[index],
                                       lower[index], upper[index], tolerance) || return false
    end
    return true
end

_within_primal_bounds(values::AbstractVector{T}, lower::AbstractVector{Bound{T}},
                      upper::AbstractVector{Bound{T}}, tolerance::T) where {T} =
    _within_primal_intervals(values, values, lower, upper, tolerance)



function _primal_feasible_with_bounds(problem::LinearProblem{T}, primal::Vector{T},
                                      tolerance::T, column_lower, column_upper,
                                      row_bound_lower, row_bound_upper, row_bounds=nothing, buffers=nothing, share_native::Bool=false) where {T}
    _within_primal_bounds(primal, column_lower, column_upper, tolerance) || return false
    row_lower, row_upper = isnothing(row_bounds) ?
        _primal_row_bounds(problem.A, primal, _is_exact(T)) : row_bounds
    # Certify the entire activity interval in the requested absolute units.
    # Cancellation uncertainty must not enlarge the configured tolerance.
    if isnothing(buffers) || !(T <: Union{Float32,Float64})
        _within_primal_intervals(row_lower, row_upper, row_bound_lower,
                                 row_bound_upper, tolerance) && return true
    end
    # A long floating sum can have a wider enclosure than the absolute
    # tolerance, or overflow before cancellation, even when its exact
    # stored-coefficient activity is feasible. Exact fallback checks finite
    # coefficients independently and does not enlarge the user tolerance.
    T <: Union{Float32,Float64} || return false
    rows = isnothing(buffers) ? Int[] : empty!(buffers.rows)
    for row in eachindex(row_lower)
        _primal_interval_within_bounds(row_lower[row], row_upper[row],
                                       row_bound_lower[row], row_bound_upper[row],
                                       tolerance) || push!(rows, row)
    end
    isempty(rows) && return true
    return _refined_primal_rows_feasible(problem, primal, tolerance, rows,
                                          row_bound_lower, row_bound_upper, buffers, share_native)
end

function _original_primal_feasible(problem::LinearProblem{T}, primal::Vector{T}, tolerance::T) where {T}
    return _primal_feasible_with_bounds(problem, primal, tolerance,
        problem.column_lower, problem.column_upper, problem.row_lower, problem.row_upper)
end

_dual_ratio_tolerance(coefficient,tolerance::T) where T =
    ifelse(coefficient < zero(T), -tolerance, tolerance)
_dual_ratio_tolerance(coefficient::BigFloat,tolerance::BigFloat) =
    coefficient < zero(BigFloat) ? -tolerance : tolerance

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


function _primal_weighted_score(reduced_cost::T,
                                weight::Tuple{I,T}) where {I<:Integer,T<:AbstractFloat}
    cost_mantissa, cost_exponent = frexp(abs(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end

function _primal_weighted_score(reduced_cost::T, weight::T) where {T<:AbstractFloat}
    mantissa, exponent = frexp(weight)
    return _primal_weighted_score(reduced_cost, (exponent, mantissa))
end
_primal_weighted_score(reduced_cost::Rational, weight::Rational) =
    big(reduced_cost)^2 / big(weight)

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

function primal_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.primal_tolerance
    for index in workspace.basis.basic_indices
        value = workspace.primal[index]
        lower_violation = _lower_violation(workspace.lower[index], value)
        upper_violation = _upper_violation(workspace.upper[index], value)
        if lower_violation > tolerance
            infeasibility += lower_violation
            count += 1
        elseif upper_violation > tolerance
            infeasibility += upper_violation
            count += 1
        end
    end
    return infeasibility, count
end


end
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::JSimplex.Bound,b::JSimplex.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
@noinline isum(::Val{:original},a,b)=Reference._primal_sum_bounds(a,b)
@noinline isum(::Val{:candidate},a,b)=JSimplex._primal_sum_bounds(a,b)
@noinline iprod(::Val{:original},a,b)=Reference._primal_product_bounds(a,b)
@noinline iprod(::Val{:candidate},a,b)=JSimplex._primal_product_bounds(a,b)
@noinline feasible(::Val{:original},p,x,t)=Reference._original_primal_feasible(p,x,t)
@noinline feasible(::Val{:candidate},p,x,t)=JSimplex._original_primal_feasible(p,x,t)
@noinline summary(::Val{:original},ws)=Reference.primal_infeasibility_summary(ws)
@noinline summary(::Val{:candidate},ws)=JSimplex.primal_infeasibility_summary(ws)
@noinline ratio(::Val{:original},ws,row,o)=Reference.dual_ratio_test(ws,row,o)
@noinline ratio(::Val{:candidate},ws,row,o)=JSimplex.dual_ratio_test(ws,row,o)
@noinline score(::Val{:original},c,w)=Reference._primal_weighted_score(c,w)
@noinline score(::Val{:candidate},c,w)=JSimplex._primal_weighted_score(c,w)
@noinline primal(::Val{:original},ws)=Reference._primal_entering(ws,ws.options.dual_tolerance)
@noinline primal(::Val{:candidate},ws)=JSimplex._primal_entering(ws,ws.options.dual_tolerance)
@noinline dual(::Val{:original},ws)=Reference.dual_edge_selection(ws)
@noinline dual(::Val{:candidate},ws)=JSimplex.dual_edge_selection(ws)
snap(a)=(a,map(copy,a),deepcopy(a))
intact(a,s)=all(a[k]===s[1][k]&&axes(a[k])==axes(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
parrays(p,x)=(p.A.nzval,p.A.rowval,p.A.colptr,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper,x)
warrays(ws)=(parrays(ws.problem,ws.primal)...,ws.costs,ws.reduced_costs,ws.lower,ws.upper,ws.pricing_weights,ws.basis.basic_indices,ws.basis.states)
function capture(f)
 try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
end
function statefixture(::Type{T},n,m;pricing=:devex) where T
 p=LinearProblem(spzeros(T,m,n),zeros(T,n);row_lower=zeros(T,m),row_upper=fill(T(2),m),column_lower=zeros(T,n),column_upper=fill(T(2),n))
 policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
 JSimplex._initialize_workspace_state(p,SolverOptions(T;algorithm=:dual,pricing,verbose=false);progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
end
function summaryfixture(::Type{T},n,pattern) where T
 ws=statefixture(T,0,n)
 for j in 1:n
  ws.primal[j]=pattern===:lower_bad||pattern===:unbounded ? -T(1//4) : pattern===:upper_bad ? T(9//4) : pattern===:feasible ? one(T) : mod(j,4)<2 ? -T(1//4) : mod(j,4)==2 ? T(9//4) : one(T)
  pattern===:unbounded&&(ws.upper[j]=JSimplex._unbounded_bound(T))
 end
 ws
end
function ratiofixture(::Type{T},n,pattern) where T
 ws=statefixture(T,n,1);fill!(ws.reduced_costs,zero(T));row=T[(pattern===:negative||pattern===:mixed&&isodd(j) ? -1 : 1)*j for j in 1:n]
 for j in 1:n;ws.basis.states[j]=row[j]<0 ? JSimplex.AT_UPPER : JSimplex.AT_LOWER;end
 push!(row,zero(T));ws,row,one(T)
end
function primalfixture(::Type{T},n,pattern) where T
 ws=statefixture(T,n,0)
 for j in 1:n
  x=T(j//16);pattern===:negative||pattern===:mixed&&isodd(j) ? (x=-x) : nothing
  ws.reduced_costs[j]=x;ws.basis.states[j]=x<0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER;ws.pricing_weights[j]=T(2)
 end
 ws
end
function dualfixture(::Type{T},n,pattern) where T
 ws=statefixture(T,0,n;pricing=:auto);JSimplex._prepare_auto_pricing!(ws,:dual)
 for j in 1:n;ws.primal[j]=pattern===:lower_bad ? -T(j//16) : T(2)+T(j//16);ws.pricing_weights[j]=T(4);end
 ws
end
function problemfixture(::Type{T},n,pattern,density) where T
 rows=Int[];cols=Int[];vals=T[];m=8
 for j in 1:n,i in 1:m
  if density===:dense||i==mod1(j,8)
   v=T((5+mod(i+j,7))//8);pattern===:negative ? (v=-v) : pattern===:mixed&&isodd(i+j) ? (v=-v) : nothing
   push!(rows,i);push!(cols,j);push!(vals,v)
  end
 end
 p=LinearProblem(sparse(rows,cols,vals,m,n),zeros(T,n);row_lower=fill(T(-8192),m),row_upper=fill(T(8192),m),column_lower=fill(T(-4),n),column_upper=fill(T(4),n))
 p,fill(T(1//2),n),zero(T)
end
function operands(::Type{T}) where T
 a=T[0,-zero(T),1,-1,T(3//7),T(-7//3),T(1//2),T(-1//2)]
 if T<:AbstractFloat
  append!(a,T[Inf,-Inf,NaN,prevfloat(one(T)),nextfloat(one(T)),nextfloat(zero(T))])
  T===BigFloat&&append!(a,[ldexp(one(T),1000),ldexp(one(T),-1000)])
 end
 a
end
function correctness(::Type{T}) where T
 @testset "Scalar branches values and owners $T" begin
  for stored in (T===BigFloat ? (precision(BigFloat),512) : (0,))
   v=T===BigFloat ? setprecision(()->operands(T),BigFloat,stored) : operands(T)
   for a in v,b in v,f in (isum,iprod)
    saved=deepcopy((a,b));l=capture(()->f(Val(:original),a,b));r=capture(()->f(Val(:candidate),a,b))
    @test same(l,r)
    @test same((a,b),saved)
    if l[1]===:value
     x,y=l[2],r[2];@test (x[1]===a,x[1]===b,x[2]===a,x[2]===b)==(y[1]===a,y[1]===b,y[2]===a,y[2]===b)
    end
   end
   for a in v,w in T[1,2,4]
    @test same(capture(()->score(Val(:original),a,w)),capture(()->score(Val(:candidate),a,w)))
   end
  end
  @test same(score(Val(:candidate),T(3),T(2)),T<:Rational ? T(9//2) : (1,T(3//4)))
  for n in (0,1,8),pattern in (:lower_bad,:upper_bad,:feasible,:mixed,:unbounded)
   ws=summaryfixture(T,n,pattern);saved=snap(warrays(ws))
   @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
   if pattern!==:mixed;@test same(summary(Val(:candidate),ws),pattern===:feasible ? (zero(T),0) : (T(n//4),n));end
   @test intact(warrays(ws),saved)
   n==0&&continue
   ws.upper[1]=JSimplex.Bound(-one(T));ws.primal[1]=-T(1//2)
   @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
   ws.options=SolverOptions(T;verbose=false,primal_tolerance=T(1//2));@test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
  end
  for x in operands(T)
   ws=summaryfixture(T,2,:lower_bad);ws.primal[1]=x;saved=snap(warrays(ws))
   @test same(capture(()->summary(Val(:original),ws)),capture(()->summary(Val(:candidate),ws)))
   @test intact(warrays(ws),saved)
  end
  for pattern in (:positive,:negative,:mixed),n in (1,8)
   ws,row,o=ratiofixture(T,n,pattern);saved=snap((warrays(ws)...,row))
   @test ratio(Val(:original),ws,row,o)==ratio(Val(:candidate),ws,row,o)==n
   @test intact((warrays(ws)...,row),saved)
   for i in (1,n);push!(ws.scratch.rejected_entering,i);@test ratio(Val(:original),ws,row,o)==ratio(Val(:candidate),ws,row,o);empty!(ws.scratch.rejected_entering);end
   for x in operands(T)
    row[1]=x;l=capture(()->ratio(Val(:original),ws,row,o));ca=copy(ws.scratch.candidates);r=capture(()->ratio(Val(:candidate),ws,row,o))
    @test same(l,r)
    @test ca==ws.scratch.candidates
   end
   ws=primalfixture(T,n,pattern);saved=snap(warrays(ws));@test same(primal(Val(:original),ws),primal(Val(:candidate),ws));@test intact(warrays(ws),saved)
   @test primal(Val(:candidate),ws)[1]==n
   for i in 1:n;ws.reduced_costs[i]=pattern===:negative ? -one(T) : one(T);ws.basis.states[i]=pattern===:negative ? JSimplex.AT_LOWER : JSimplex.AT_UPPER;end
   @test primal(Val(:original),ws)==primal(Val(:candidate),ws)
   for pattern2 in (:lower_bad,:upper_bad)
    dw=dualfixture(T,n,pattern2);saved=snap(warrays(dw));@test dual(Val(:original),dw)==dual(Val(:candidate),dw)==n;@test intact(warrays(dw),saved)
    push!(dw.scratch.rejected_rows,n);@test dual(Val(:original),dw)==dual(Val(:candidate),dw)
   end
  end
  for density in (:sparse,:dense),pattern in (:positive,:negative,:mixed)
   p,x,t=problemfixture(T,8,pattern,density);saved=snap(parrays(p,x));@test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===true;@test intact(parrays(p,x),saved)
   x[1]=T(2^20);@test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===false
  end
 end
end
scoresink(v::Tuple)=Int(isfinite(v[2]));scoresink(v)=Int(isfinite(v))
@noinline function batch(method::M,::Val{S},v,calls) where {M,S}
 sink=0
 for _ in 1:calls
  if S===:sum||S===:product
   a,b=v
   for i in eachindex(a);lo,hi=S===:sum ? isum(method,a[i],b[i]) : iprod(method,a[i],b[i]);sink+=Int(isfinite(lo))+Int(isfinite(hi));end
  elseif S===:score
   a,w=v;for i in eachindex(a);sink+=scoresink(score(method,a[i],w[i]));end
  elseif S===:feasible;sink+=Int(feasible(method,v...))
  elseif S===:summary;x,n=summary(method,v);sink+=Int(isfinite(x))+n
  elseif S===:ratio;sink+=ratio(method,v...)
  elseif S===:primal;sink+=first(primal(method,v))
  elseif S===:dual;sink+=dual(method,v)
  end
 end
 sink
end

@noinline function allocation_cost(method::M,scope::S,v::V,sink) where {M,S,V}
 t=@timed sink[]=batch(method,scope,v,2)
 (bytes=t.bytes,events=Base.gc_alloc_count(t.gcstats),compile=t.compile_time,recompile=t.recompile_time)
end
function cost_pair(scope,v)
 sink=Ref(0)
 for _ in 1:3,method in (Val(:original),Val(:candidate));allocation_cost(method,scope,v,sink);end
 before=allocation_cost(Val(:original),scope,v,sink);after=allocation_cost(Val(:candidate),scope,v,sink)
 @test before.compile==before.recompile==after.compile==after.recompile==0
 @test before.events>0 && before.bytes>0
 @test 10*after.events<9*before.events && after.bytes<before.bytes # RED costgate
end
@testset "Generic scalar branches" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat)
    # Current-call context and mutated inputs never reuse a prior tolerance/result.
    ws=summaryfixture(BigFloat,4,:lower_bad)
    ws.primal[1]=setprecision(()->BigFloat(-1)/BigFloat(7),BigFloat,512)
    @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
    saved=snap(warrays(ws));o=ws.options
    raw=ntuple(i->i==1 ? BigFloat(NaN) : getfield(o,i),fieldcount(typeof(o)))
    ws.options=typeof(o)(raw...)
    @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
    @test same(summary(Val(:candidate),ws),(zero(BigFloat),0))
    @test intact(warrays(ws),saved)
    @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
   end
  end
 end
 for T in (Rational{BigInt},Rational{Int64},Float32,Float64);correctness(T);end
 @testset "Ties and partial weighted pricing use current values" begin
  for T in (BigFloat,Rational{BigInt},Float32,Float64)
   dw=dualfixture(T,8,:lower_bad);fill!(dw.primal,-one(T));@test dual(Val(:candidate),dw)==1
   push!(dw.scratch.rejected_rows,1);@test dual(Val(:candidate),dw)==2
   for algorithm in (:primal,:dual)
    ws=algorithm===:primal ? primalfixture(T,129,:positive) : dualfixture(T,129,:lower_bad)
    previous=ws.progress
    policy=JSimplex.NumericalPolicy(T;partial_pricing=true,refactor_timing=false)
    ws.progress=typeof(previous)(previous.start_ns,previous.objective,previous.objective_constant,previous.scaling,previous.iteration_offset,previous.refactorization_offset,previous.diagnostics,policy)
    if algorithm===:primal
     fill!(ws.reduced_costs,zero(T));ws.reduced_costs[129]=T(2);fill!(ws.basis.states,JSimplex.AT_UPPER)
     @test primal(Val(:candidate),ws)[1]==129
     ws.reduced_costs[129]=zero(T);ws.reduced_costs[1]=T(3)
     @test primal(Val(:candidate),ws)[1]==1
     ws.reduced_costs[1]=zero(T);@test primal(Val(:candidate),ws)[1]==0
    else
     fill!(ws.primal,one(T));ws.primal[129]=-T(2)
     @test dual(Val(:candidate),ws)==129
     ws.primal[129]=one(T);ws.primal[1]=-T(3)
     @test dual(Val(:candidate),ws)==1
     ws.primal[1]=one(T);@test dual(Val(:candidate),ws)==-1
    end
   end
  end
 end
 @testset "Warm whole-call allocation savings" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    a=fill(BigFloat(3//2),128);b=fill(BigFloat(5//4),128)
    cost_pair(Val(:sum),(a,b));cost_pair(Val(:product),(a,b))
    cost_pair(Val(:ratio),ratiofixture(BigFloat,128,:positive))
    cost_pair(Val(:score),(a,fill(BigFloat(2),128)))
    cost_pair(Val(:primal),primalfixture(BigFloat,128,:positive))
    cost_pair(Val(:dual),dualfixture(BigFloat,128,:lower_bad))
    cost_pair(Val(:summary),summaryfixture(BigFloat,128,:lower_bad))
   end
  end
  cost_pair(Val(:summary),summaryfixture(Rational{BigInt},128,:lower_bad))
  for T in (Float32,Float64)
   v=summaryfixture(T,128,:lower_bad);sink=Ref(0)
   for _ in 1:3,method in (Val(:original),Val(:candidate));allocation_cost(method,Val(:summary),v,sink);end
   b=allocation_cost(Val(:original),Val(:summary),v,sink);a=allocation_cost(Val(:candidate),Val(:summary),v,sink)
   @test b.bytes==a.bytes==b.events==a.events==0
  end
 end
end
end
