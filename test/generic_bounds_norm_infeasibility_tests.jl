module GenericBoundsNormInfeasibilityTests
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
module BNIReference
import JSimplex
using JSimplex: SimplexWorkspace,Bound,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_can_preserve_primal_bound_value,_primal_relaxed_step,_legacy_primal_row_validation_enabled,_primal_direction_magnitude,_pipeline_column_rhs!,_checked_basis_solve!,_primal_cacheable_weight,_primal_unit_basis,_add_product_bounds,_infeasibility_bound_allowance
function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}, entering::Int,
                                    direction::T, column::Vector{T}, leaving_row::Int) where {T}
    leaving = workspace.basis.basic_indices[leaving_row]
    movement = -direction * column[leaving_row]
    bound = movement > zero(T) ? workspace.upper[leaving] : workspace.lower[leaving]
    step = (bound_value(bound) - workspace.primal[leaving]) / movement
    step >= zero(T) && return true
    state = movement > zero(T) ? AT_UPPER : AT_LOWER
    _can_preserve_primal_bound_value(workspace, leaving, state, bound) && return true
    # A tolerated bound violation has a negative ratio. Clipping it to zero
    # does not eliminate the movement imposed by fixing the leaving variable
    # exactly at its bound during the subsequent basis recomputation.
    value = workspace.primal[entering] + direction * step
    isfinite(value) || return false
    tolerance = workspace.options.primal_tolerance
    violation = max(zero(T), _lower_violation(workspace.lower[entering], value),
                    _upper_violation(workspace.upper[entering], value))
    violation <= tolerance || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row == leaving_row && continue
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        bound_violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                              _upper_violation(workspace.upper[index], value))
        # Use the same per-bound feasibility criterion as legacy Harris pricing
        # and recomputation, including the movement imposed by this bound snap.
        violation = max(violation, bound_violation)
        violation <= tolerance || return false
    end
    return true
end

function _primal_bound_snap_feasible(workspace::SimplexWorkspace{BigFloat}, entering::Int,
                                    direction::BigFloat, column::Vector{BigFloat}, leaving_row::Int)
    T = BigFloat
    leaving = workspace.basis.basic_indices[leaving_row]
    movement = -direction * column[leaving_row]
    bound = movement > 0 ? workspace.upper[leaving] : workspace.lower[leaving]
    step = (bound_value(bound) - workspace.primal[leaving]) / movement
    step >= 0 && return true
    state = movement > 0 ? AT_UPPER : AT_LOWER
    _can_preserve_primal_bound_value(workspace, leaving, state, bound) && return true
    # A tolerated bound violation has a negative ratio. Clipping it to zero
    # does not eliminate the movement imposed by fixing the leaving variable
    # exactly at its bound during the subsequent basis recomputation.
    value = workspace.primal[entering] + direction * step
    isfinite(value) || return false
    tolerance = workspace.options.primal_tolerance
    violation = max(zero(T), _lower_violation(workspace.lower[entering], value),
                    _upper_violation(workspace.upper[entering], value))
    violation <= tolerance || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row == leaving_row && continue
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        bound_violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                              _upper_violation(workspace.upper[index], value))
        # Use the same per-bound feasibility criterion as legacy Harris pricing
        # and recomputation, including the movement imposed by this bound snap.
        violation = max(violation, bound_violation)
        violation <= tolerance || return false
    end
    return true
end


function _primal_step_bounds_feasible(workspace::SimplexWorkspace{T}, direction::T,
                                      column::Vector{T}, step::T) where {T}
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                        _upper_violation(workspace.upper[index], value))
        violation <= tolerance || return false
    end
    return true
end

function _primal_ratio(workspace::SimplexWorkspace{T}, entering::Int, direction::T,
                       tableau_column::Vector{T}) where {T}
    opposite = direction > zero(T) ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < zero(T)
            violation = movement > zero(T) ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = max(zero(T), relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    strict_safe = !(strict_row in workspace.scratch.rejected_rows) &&
        _primal_bound_snap_feasible(
            workspace, entering, direction, tableau_column, strict_row)
    fallback = strict_safe ? (strict_step, strict_row, strict_state) : (nothing, -1, BASIC)
    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = max(zero(T),
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = abs(tableau_column[row])
        if pivot > largest_pivot
            !_primal_bound_snap_feasible(
                workspace, entering, direction, tableau_column, row) && continue
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    # Tolerated initial bound violations can create zero ratios on coefficients
    # too small to pivot on. A finite entering bound remains a valid Harris move
    # when the entire predicted step respects the same per-bound tolerance.
    if _legacy_primal_row_validation_enabled(workspace) &&
       largest_pivot <= workspace.options.zero_tolerance && isfinite(opposite) &&
       isfinite(entering_step) && entering_step > zero(T) && entering_step <= relaxed_limit &&
       _primal_step_bounds_feasible(workspace, direction, tableau_column, entering_step)
        return entering_step, 0, BASIC
    end
    if leaving_row == 0
        return fallback
    end
    _primal_step_bounds_feasible(workspace, direction, tableau_column, leaving_step) ||
        return fallback
    return leaving_step, leaving_row, leaving_state
end

# Keep a fresh zero, NaN handling and signed-zero selection on the fallback path.
_primal_nonnegative_step(value::BigFloat) = value > 0 ? value : max(zero(BigFloat),value)

function _primal_ratio(workspace::SimplexWorkspace{BigFloat}, entering::Int, direction::BigFloat,
                       tableau_column::Vector{BigFloat})
    T = BigFloat
    opposite = direction > 0 ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > 0 ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < 0
            violation = movement > 0 ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = _primal_nonnegative_step(raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > 0 ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = _primal_nonnegative_step(relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    strict_safe = !(strict_row in workspace.scratch.rejected_rows) &&
        _primal_bound_snap_feasible(
            workspace, entering, direction, tableau_column, strict_row)
    fallback = strict_safe ? (strict_step, strict_row, strict_state) : (nothing, -1, BASIC)
    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > 0 ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = _primal_nonnegative_step(
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = _primal_direction_magnitude(tableau_column[row])
        if pivot > largest_pivot
            !_primal_bound_snap_feasible(
                workspace, entering, direction, tableau_column, row) && continue
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > 0 ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    # Tolerated initial bound violations can create zero ratios on coefficients
    # too small to pivot on. A finite entering bound remains a valid Harris move
    # when the entire predicted step respects the same per-bound tolerance.
    if _legacy_primal_row_validation_enabled(workspace) &&
       largest_pivot <= workspace.options.zero_tolerance && isfinite(opposite) &&
       isfinite(entering_step) && entering_step > 0 && entering_step <= relaxed_limit &&
       _primal_step_bounds_feasible(workspace, direction, tableau_column, entering_step)
        return entering_step, 0, BASIC
    end
    if leaving_row == 0
        return fallback
    end
    _primal_step_bounds_feasible(workspace, direction, tableau_column, leaving_step) ||
        return fallback
    return leaving_step, leaving_row, leaving_state
end


function _primal_direction_weight(direction::AbstractVector{T}) where {T<:AbstractFloat}
    scale = one(T)
    for coefficient in direction
        scale = max(scale, _primal_direction_magnitude(coefficient))
    end
    scaled_square = abs2(inv(scale))
    for coefficient in direction
        scaled_square += abs2(coefficient / scale)
    end
    factor = sqrt(scaled_square)
    scale_mantissa, scale_exponent = frexp(scale)
    factor_mantissa, factor_exponent = frexp(factor)
    mantissa, correction = frexp(scale_mantissa * factor_mantissa)
    # Keep the exponent separately: a finite column can have a norm above floatmax(T).
    scaled_weight = (scale_exponent + factor_exponent + correction, mantissa)
    stored_weight = min(floatmax(T), scale * factor)
    return scaled_weight, stored_weight
end

function _primal_direction_weight(direction::AbstractVector{T}) where {T<:Rational}
    weight = one(Rational{BigInt})
    for coefficient in direction
        weight += abs2(big(coefficient))
    end
    stored_weight = T === Rational{BigInt} ? weight : one(T)
    return weight, stored_weight
end

function _primal_steepest_weight!(workspace::SimplexWorkspace{T}, index::Int) where {T}
    column = _pipeline_column_rhs!(workspace,index)
    direction = _checked_basis_solve!(workspace.scratch.row_solution,workspace,column;
                                      operation=:weight_ftran)
    scaled_weight, stored_weight = _primal_direction_weight(direction)
    workspace.pricing_weights[index] = stored_weight
    workspace.scratch.steepest_valid[index] = _primal_cacheable_weight(stored_weight)
    return scaled_weight
end

function _primal_initialize_steepest!(workspace::SimplexWorkspace{T}) where {T}
    scratch = workspace.scratch
    scratch.steepest_initialized && return nothing
    scratch.steepest_initialized = true
    T <: Rational && T !== Rational{BigInt} && return nothing
    _primal_unit_basis(workspace) || return nothing
    A = workspace.problem.A
    row_count, column_count = size(A)
    for index in 1:column_count
        direction = @view A.nzval[A.colptr[index]:(A.colptr[index + 1] - 1)]
        _, weight = _primal_direction_weight(direction)
        workspace.pricing_weights[index] = weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(weight)
    end
    _, row_weight = _primal_direction_weight(T[one(T)])
    for index in (column_count + 1):(column_count + row_count)
        workspace.pricing_weights[index] = row_weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(row_weight)
    end
    return nothing
end


function _primal_initialize_steepest!(workspace::SimplexWorkspace{BigFloat})
    T = BigFloat
    scratch = workspace.scratch
    scratch.steepest_initialized && return nothing
    scratch.steepest_initialized = true
    T <: Rational && T !== Rational{BigInt} && return nothing
    _primal_unit_basis(workspace) || return nothing
    A = workspace.problem.A
    row_count, column_count = size(A)
    for index in 1:column_count
        direction = @view A.nzval[A.colptr[index]:(A.colptr[index + 1] - 1)]
        _, weight = _primal_direction_weight(direction)
        workspace.pricing_weights[index] = weight
        scratch.steepest_valid[index] = _primal_cacheable_weight(weight)
    end
    _, row_weight = _primal_direction_weight(T[one(T)])
    row_cacheable = false
    row_ready = false
    for index in (column_count + 1):(column_count + row_count)
        workspace.pricing_weights[index] = row_weight
        if !row_ready
            row_cacheable = _primal_cacheable_weight(row_weight)
            row_ready = true
        end
        scratch.steepest_valid[index] = row_cacheable
    end
    return nothing
end

function _floating_infeasibility_certified(workspace::SimplexWorkspace{T},
                                          rho::Vector{T}, below::Bool) where {T<:AbstractFloat}
    # Every feasible working vector satisfies [A -I] * x == 0. A row
    # combination must stay positive over the tolerance envelope of the bounds.
    # This does not rely on the computed basic primal values.
    A = workspace.problem.A
    column_count = size(A, 2)
    orientation = below ? one(T) : -one(T)
    minimum_value = zero(T)
    for index in eachindex(workspace.lower)
        coefficient_lower = coefficient_upper = zero(T)
        if index <= column_count
            for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                coefficient_lower, coefficient_upper = _add_product_bounds(
                    coefficient_lower, coefficient_upper,
                    orientation * rho[A.rowval[position]], A.nzval[position],
                )
            end
        else
            coefficient_lower = coefficient_upper = -orientation * rho[index - column_count]
        end
        isfinite(coefficient_lower) && isfinite(coefficient_upper) || return false
        iszero(coefficient_lower) && iszero(coefficient_upper) && continue

        lower, upper = workspace.lower[index], workspace.upper[index]
        !isfinite(lower) && coefficient_upper > zero(T) && return false
        !isfinite(upper) && coefficient_lower < zero(T) && return false
        isfinite(lower) || isfinite(upper) || return false
        endpoint = isfinite(lower) ? bound_value(lower) : bound_value(upper)
        term = min(coefficient_lower * endpoint, coefficient_upper * endpoint)
        if isfinite(lower) && isfinite(upper)
            endpoint = bound_value(upper)
            term = min(term, coefficient_lower * endpoint, coefficient_upper * endpoint)
        end
        isfinite(term) || return false
        contribution = prevfloat(term)
        allowance = _infeasibility_bound_allowance(workspace,index)
        if !iszero(allowance)
            magnitude = nextfloat(max(abs(coefficient_lower),abs(coefficient_upper)))
            penalty = nextfloat(magnitude*allowance)
            isfinite(penalty) || return false
            contribution = prevfloat(contribution-penalty)
        end
        total = minimum_value + contribution
        isfinite(total) || return false
        minimum_value = prevfloat(total)
    end
    return minimum_value > zero(T)
end

_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:AbstractFloat} = _floating_infeasibility_certified(w,rho,below)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:Rational} = JSimplex._infeasibility_certified(w,rho,below)

end

const BNIA=JSimplex
const BNIB=JSimplex
const BNIC=JSimplex
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
modof(::Val{:original})=BNIReference
modof(::Val{:A})=BNIA
modof(::Val{:B})=BNIB
modof(::Val{:C})=BNIC
isresidual(scope)=scope in (:direction_residual,:row_residual)
function ratio_fixture(::Type{T},n,scope,density,pattern) where T
 m=scope===:harris ? 4 : n;columns=isresidual(scope) ? n : scope===:harris ? n : 1
 A=zeros(T,m,columns)
 for j in 1:columns,i in 1:m
  if isresidual(scope)
   if i==j;A[i,j]=T(2)
   elseif i>1&&j>1&&(density===:dense||(i+j)%8==0);A[i,j]=T(1//32);end
  elseif density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//8)
  end
 end
 p=LinearProblem(sparse(A),zeros(T,columns);row_lower=fill(-T(8),m),row_upper=fill(T(8),m),column_lower=fill(-T(8),columns),column_upper=fill(T(8),columns))
 opt=SolverOptions(T;algorithm=scope===:primal_ratio ? :primal : :dual,pricing=:dantzig,verbose=false)
 policy=J.NumericalPolicy(T;refactor_timing=false)
 w=J._initialize_workspace_state(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=policy))
 vector=zeros(T,scope===:harris ? length(w.basis.states) : m);rhs=zeros(T,m)
 if isresidual(scope)
  for i in 1:m;w.basis.basic_indices[i]=isodd(i) ? i : columns+i;end
  if scope===:row_residual
   if m>0;vector[1]=T(1//2);end
   if m>0&&pattern===:perturbed;vector[end]=T(1//1024);end
  else
   for i in 1:m;vector[i]=T((isodd(i) ? 1 : -1)//8);end
   for (j,k) in enumerate(w.basis.basic_indices)
    if k<=columns
     for q in w.problem.A.colptr[k]:w.problem.A.colptr[k+1]-1;rhs[w.problem.A.rowval[q]]+=w.problem.A.nzval[q]*vector[j];end
    else;rhs[k-columns]-=vector[j];end
   end
   if pattern===:perturbed;rhs[end]+=T(1//1024);end
  end
 elseif scope===:primal_ratio
  for i in 1:m
   active=density===:dense||i%4==0;ordinal=density===:dense ? i : i÷4
   negative=pattern===:negative||pattern===:mixed&&isodd(ordinal)
   vector[i]=active ? (negative ? -T((i+1)//8) : T((i+1)//8)) : zero(T)
   magnitude=T((i+1)//8);step=pattern===:unique ? T((i+64)//64) : one(T)
   w.lower[columns+i]=Bound(-magnitude*step);w.upper[columns+i]=Bound(magnitude*step)
  end
 else
  for i in 1:columns
   active=density===:dense||i%4==0;negative=pattern===:negative||pattern===:mixed&&isodd(i÷(density===:dense ? 1 : 4))
   w.basis.states[i]=negative ? J.AT_UPPER : J.AT_LOWER
   vector[i]=active ? (negative ? -T((i+1)//8) : T((i+1)//8)) : zero(T)
   step=pattern===:unique ? T((i+64)//64) : pattern===:ties ? zero(T) : one(T)
   w.reduced_costs[i]=vector[i]*step
  end
 end
 if scope===:direction_residual;J._hypersparse_workspace!(w);end
 (w=w,vector=vector,rhs=rhs,scope=scope,orientation=one(T),pivot=one(T))
end


function fixture(::Type{T},n,density,shape,scope;below=true,mode=:finite) where T
 if scope in (:snap,:step,:ratio)
  v=ratio_fixture(T,n,:primal_ratio,density,shape)
  if scope===:snap
   v.vector[1]=-one(T);v.w.upper[2]=J.Bound(one(T));v.w.primal[2]=T(17//16)
   v.w.lower[1]=J.Bound(zero(T));opts=v.w.options
   v.w.options=typeof(opts)((k===:primal_tolerance ? T(1//8) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  if scope!==:ratio
   for i in 2:n
    if i%3==0;v.w.lower[1+i]=J._unbounded_bound(T);v.w.upper[1+i]=J._unbounded_bound(T);end
   end
  end
  return merge(v,(scope=scope,step=T(1//32)))
 elseif scope===:norm
  vector=T[(density===:dense||i%4==0) ? (shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*((i%7+1)//16) : 0 for i in 1:n]
  return (scope=scope,vector=vector)
 end
 m=min(8,n÷2);A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  (density===:dense||(i+j)%5==0)&&(A[i,j]=T((shape===:negative||shape===:mixed&&isodd(i+j) ? -1 : 1)*((i+j)%7+1)//16))
 end
 p=LinearProblem(sparse(A),zeros(T,n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),m),row_upper=fill(T(8),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,verbose=false)
 pol=J.NumericalPolicy(T;refactor_timing=false,solve_refinement=false,recovery=false)
 progress=J.SimplexProgressContext(p;numerical_policy=pol)
 w=scope===:solve ? J.initialize_workspace(p,opt;progress) : J._initialize_workspace_state(p,opt;progress)
 if scope===:cert
  rho=fill(T(1//8),m);orientation=below ? one(T) : -one(T)
  for j in 1:n
   coefficient=sum((orientation*rho[i]*A[i,j] for i in 1:m);init=zero(T));value=coefficient<0 ? -T(2) : T(2)
   w.lower[j]=J.Bound(value);w.upper[j]=J.Bound(value)
   if mode===:one_sided&&!iszero(coefficient)
    if coefficient>0;w.upper[j]=J._unbounded_bound(T);else;w.lower[j]=J._unbounded_bound(T);end
   end
  end
  for j in n+1:n+m;w.lower[j]=J.Bound(zero(T));w.upper[j]=J.Bound(zero(T));end
  if mode===:zero_tol
   opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? zero(T) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  return (scope=scope,w=w,rho=rho,below=below)
 end
 (scope=scope,w=w,weights=copy(w.pricing_weights),valid=copy(w.scratch.steepest_valid))
end
function reset!(v)
 if v.scope in (:init,:solve)
  copyto!(v.w.pricing_weights,v.weights);copyto!(v.w.scratch.steepest_valid,v.valid);v.w.scratch.steepest_initialized=false
 end
 nothing
end
@noinline function whole(a::A,v::V) where {A,V}
 mod=modof(a)
 if v.scope===:snap;return mod._primal_bound_snap_feasible(v.w,1,v.orientation,v.vector,1)
 elseif v.scope===:step;return mod._primal_step_bounds_feasible(v.w,v.orientation,v.vector,v.step)
 elseif v.scope===:ratio;return mod._primal_ratio(v.w,1,v.orientation,v.vector)
 elseif v.scope===:norm;return mod._primal_direction_weight(v.vector)
 elseif v.scope===:init;return mod._primal_initialize_steepest!(v.w)
 elseif v.scope===:solve;return mod._primal_steepest_weight!(v.w,1)
 end
 mod._infeasibility_certified(v.w,v.rho,v.below)
end
sink(x::Bool)=Int(x)
sink(x::Rational)=Int(x>0)
sink(::Nothing)=1
sink(x::Tuple{<:Integer,<:AbstractFloat})=Int(isfinite(x[2]))
sink(x::Tuple{<:Tuple,<:AbstractFloat})=Int(isfinite(x[2]))
sink(x::Tuple{<:Rational,<:Rational})=Int(x[2]>0)
sink(x::Tuple{<:Union{Nothing,Real},Int,J.VariableState})=100*x[2]+Int(x[3])+(isnothing(x[1]) ? -10000 : 1)
@noinline runwhole(a::A,v::V) where {A,V}=sink(whole(a,v))
function timed(a::A,v::V) where {A,V}
 t=@timed runwhole(a,v);merge(cost(t),Dict("sink"=>t.value))
end
function inputs(v)
 v.scope===:norm&&return (v.vector,)
 w=v.w;A=w.problem.A
 q=(A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal)
 v.scope in (:snap,:step,:ratio) ? (q...,v.vector) : v.scope===:cert ? (q...,v.rho) : q
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 a=inputs(v);all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
end
outputs(v,z)=v.scope in (:init,:solve) ? (z,v.w.pricing_weights,v.w.scratch.steepest_valid,v.w.scratch.steepest_initialized,v.w.basis.basic_indices,v.w.basis.states,v.w.primal) : z
aliaspattern(q)=Bool[q[i]===q[j] for i in eachindex(q),j in eachindex(q)]
function checkpair(a,b,arm)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test x[1]===y[1]
 @test x[1]===:value ? same(outputs(a,x[2]),outputs(b,y[2])) : same(x,y)
 @test intact(a,sa)&&intact(b,sb)
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 if x[1]===:value&&a.scope===:init;@test aliaspattern(a.w.pricing_weights)==aliaspattern(b.w.pricing_weights);end
 x
end
function correctness(::Type{T}) where T
 @testset "Bounds norm certificate $T" begin
  for scope in (:snap,:step,:ratio,:norm,:init,:solve),density in (:sparse,:dense),shape in (:positive,:negative,:mixed)
   arm=scope in (:snap,:step,:ratio) ? :A : :B
   a=fixture(T,8,density,shape,scope);b=fixture(T,8,density,shape,scope);x=checkpair(a,b,arm)
   if scope in (:snap,:step);@test x==(:value,true)
   elseif scope===:ratio;@test x[1]===:value&&x[2][2]>0&&x[2][1]==1
   end
  end
  for below in (true,false),density in (:sparse,:dense),shape in (:positive,:negative,:mixed),mode in (:finite,:one_sided,:zero_tol)
   a=fixture(T,16,density,shape,:cert;below,mode);b=fixture(T,16,density,shape,:cert;below,mode)
   @test checkpair(a,b,:C)==(:value,true)
   a.rho .*= -one(T);b.rho .*= -one(T);@test checkpair(a,b,:C)==(:value,false)
  end
  for scope in (:snap,:step,:ratio),variant in (:empty,:unbounded,:short,:nonfinite,:bad_point,:zero_tol,:negative_tol,:tol512,:alias)
   a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
   for v in (a,b)
    w=v.w
    if variant===:empty;empty!(w.basis.basic_indices)
    elseif variant===:unbounded
     for j in 3:length(w.lower);w.lower[j]=J._unbounded_bound(T);w.upper[j]=J._unbounded_bound(T);end
    elseif variant===:short;empty!(w.upper)
    elseif variant===:nonfinite&&T<:AbstractFloat;w.primal[end]=T(Inf)
    elseif variant===:bad_point;w.primal[end]=T(100)
    elseif variant in (:zero_tol,:negative_tol)||variant===:tol512&&T===BigFloat
     tol=variant===:zero_tol ? zero(T) : variant===:negative_tol ? -one(T) : setprecision(()->BigFloat(3//7),BigFloat,512)
     opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? tol : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
    elseif variant===:alias;w.primal[w.basis.basic_indices[1]]=v.vector[1]
    end
   end
   checkpair(a,b,:A)
  end
  for variant in (:empty,:zeros,:views,:early_invalid),scope in (:norm,:init,:solve)
   a=fixture(T,8,:sparse,:positive,scope);b=fixture(T,8,:sparse,:positive,scope)
   if scope===:norm
    if variant===:empty;a=merge(a,(vector=T[],));b=merge(b,(vector=T[],))
    elseif variant===:zeros;fill!(a.vector,zero(T));fill!(b.vector,zero(T))
    elseif variant===:views;a=merge(a,(vector=@view(a.vector[1:2:end]),));b=merge(b,(vector=@view(b.vector[1:2:end]),))
    end
   elseif variant===:early_invalid
    a.w.basis.basic_indices[1]=1;b.w.basis.basic_indices[1]=1
   end
   checkpair(a,b,:B)
  end
  for variant in (:zero,:unbounded_bad,:short,:nonfinite,:tol512)
   a=fixture(T,16,:dense,:positive,:cert);b=fixture(T,16,:dense,:positive,:cert)
   for v in (a,b)
    if variant===:zero;fill!(v.rho,zero(T))
    elseif variant===:unbounded_bad;v.w.lower[1]=J._unbounded_bound(T)
    elseif variant===:short;resize!(v.rho,0)
    elseif variant===:nonfinite&&T<:AbstractFloat;v.rho[1]=T(NaN)
    elseif variant===:tol512&&T===BigFloat
     opts=v.w.options;v.w.options=typeof(opts)((k===:primal_tolerance ? setprecision(()->BigFloat(3//7),BigFloat,512) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
    end
   end
   x=checkpair(a,b,:C)
   variant in (:zero,:unbounded_bad)&&@test x==(:value,false)
  end
  if T===BigFloat
   values=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat),setprecision(()->BigFloat(3//7),BigFloat,512),setprecision(()->BigFloat(-3//7),BigFloat,512))
   for x in values
    a=(scope=:norm,vector=[x]);b=(scope=:norm,vector=[deepcopy(x)]);r=checkpair(a,b,:B)
    if r[1]===:value
     result1=whole(Val(:B),b);result2=whole(Val(:B),b);@test result1[2]!==result2[2]
    end
   end
   for scope in (:snap,:step,:ratio,:cert)
    a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
    for v in (a,b)
     wide=setprecision(()->BigFloat(-3//7),BigFloat,512)
     v.w.primal[end]=wide;v.w.lower[end]=J.Bound(deepcopy(wide));v.w.upper[end]=J.Bound(setprecision(()->BigFloat(3//7),BigFloat,512))
    end
    checkpair(a,b,scope===:cert ? :C : :A)
   end
  end
 end
end

function extra_correctness(::Type{T}) where T
 @testset "Overflow cap and conservative rejection $T" begin
  if T===BigFloat
   for signs in ((1,1),(-1,-1),(1,-1)),wide in (false,true)
    vals = if wide
     setprecision(BigFloat,512) do
      [sign*floatmax(BigFloat) for sign in signs]
     end
    else
     [sign*floatmax(BigFloat) for sign in signs]
    end
    a=(scope=:norm,vector=vals);b=(scope=:norm,vector=deepcopy(vals));r=checkpair(a,b,:B)
    poisoned = wide && any(sign<0 for sign in signs) && rounding(BigFloat) in (RoundNearest,RoundUp,RoundFromZero)
    @test r[1]===:value&&(poisoned ? isnan(r[2][2]) : same(r[2][2],floatmax(BigFloat)))
    if poisoned
     negative=first(v for v in vals if signbit(v))
     magnitude=J._primal_direction_magnitude(negative)
     @test isfinite(negative)&&precision(negative)==512
     @test isinf(magnitude)&&!signbit(magnitude)&&precision(magnitude)==precision(BigFloat)
     @test all(iszero(v/magnitude) for v in vals)&&iszero(inv(magnitude))
     @test isnan(magnitude*zero(BigFloat))
    end
    x=whole(Val(:B),b);y=whole(Val(:B),b);@test x[2]!==y[2]
    @test all(x[2]!==v for v in b.vector)
    # A product above the finite range overflows only in these positive modes.
    product=floatmax(BigFloat)*sqrt(BigFloat(2))
    @test (isinf(product)&&!signbit(product))==(rounding(BigFloat) in (RoundNearest,RoundUp,RoundFromZero))
    @test rounding(BigFloat) in (RoundDown,RoundToZero) ? same(product,floatmax(BigFloat)) : isinf(product)
   end
   for below in (true,false),sign in (1,-1)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    wide=setprecision(BigFloat,512) do;sign*(BigFloat(1//8)+ldexp(BigFloat(1),-400));end
    a.rho[1]=wide;b.rho[1]=deepcopy(wide);checkpair(a,b,:C)
   end
  end
  if T<:AbstractFloat
   for below in (true,false)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    for v in (a,b)
     fill!(v.rho,zero(T));v.rho[1]=one(T);v.rho[2]=one(T)
     v.w.problem.A[1,1]=one(T);v.w.problem.A[2,1]=-one(T)
     v.w.lower[1]=J._unbounded_bound(T);v.w.upper[1]=J.Bound(T(2))
    end
    # Exact coefficient0 is enclosed by a strict sign-straddling interval;
    # the unbounded side must remain inconclusive before any penalty relaxation.
    @test a.rho[1]*a.w.problem.A[1,1]+a.rho[2]*a.w.problem.A[2,1]==0
    @test checkpair(a,b,:C)==(:value,false)
   end
  end
 end
end

const GATES=((BigFloat,:snap,:A,:finite),(Rational{BigInt},:snap,:A,:finite),(BigFloat,:step,:A,:finite),(Rational{BigInt},:step,:A,:finite),(BigFloat,:ratio,:A,:finite),(Rational{BigInt},:ratio,:A,:finite),(BigFloat,:init,:B,:finite),(BigFloat,:solve,:B,:finite),(BigFloat,:cert,:C,:finite),(BigFloat,:cert,:C,:one_sided),)

@testset "Bounds norm and infeasibility scalar regressions" begin
 for bits in (64,128,256),roundmode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,roundmode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (T,scope,arm,mode) in GATES
    @testset "Whole-call allocation $T/$scope/$mode" begin
     a=fixture(T,64,:dense,:positive,scope;mode);b=fixture(T,64,:dense,:positive,scope;mode)
     for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),a);reset!(b);new=timed(Val(arm),b)
      else;reset!(b);new=timed(Val(arm),b);reset!(a);old=timed(Val(:original),a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["events"]<old["events"] for (old,new) in pairs)&&median([new["bytes"] for (old,new) in pairs])<median([old["bytes"] for (old,new) in pairs]) # RED whole-call allocation gate
    end
   end
  end
 end
end
end
