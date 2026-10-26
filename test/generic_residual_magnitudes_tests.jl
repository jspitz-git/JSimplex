module GenericResidualMagnitudesTests
using Test,JSimplex,SparseArrays,LinearAlgebra
module ResidualReference
using JSimplex: SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,Bound,_unbounded_bound,bound_value,_dual_pivot_cutoff,_dual_pivot_eligible,_dual_ratio_tolerance,_eligible_with_cutoff,_primal_direction_magnitude,_primal_bound_snap_feasible,_primal_step_bounds_feasible,_legacy_primal_row_validation_enabled,_lower_violation,_upper_violation,_pipeline_changed!
_primal_relaxed_step(raw_step::T, tolerance::T, movement::T) where {T<:AbstractFloat} =
    raw_step + tolerance / abs(movement)
_primal_relaxed_step(raw_step::T, tolerance::T, movement::T) where {T<:Rational} =
    big(raw_step) + big(tolerance) / abs(big(movement))

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
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > 0 ? AT_UPPER : AT_LOWER
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
        bound = movement > 0 ? workspace.upper[index] : workspace.lower[index]
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
    negative_cutoff = cutoff
    cutoff_ready = false
    negative_tolerance = tolerance
    tolerance_ready = false
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        eligible, negative_cutoff, cutoff_ready = _eligible_with_cutoff(
            workspace,index,coefficient,cutoff,negative_cutoff,cutoff_ready)
        eligible || continue
        push!(candidates, index)
        price = workspace.reduced_costs[index]
        adjustment = tolerance
        if coefficient < 0
            if !tolerance_ready
                negative_tolerance = -tolerance
                tolerance_ready = true
            end
            adjustment = negative_tolerance
        end
        relaxed_step = (price + adjustment) / coefficient
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


function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},
                                      direction::Vector{T}, pivot::T) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(direction) == length(workspace.basis.basic_indices) == row_count &&
        length(workspace.scratch.tau) == length(workspace.scratch.row_rhs) == row_count ||
        throw(DimensionMismatch("direction residual vectors must match the row count"))
    residual = workspace.scratch.tau
    scale = workspace.scratch.row_rhs
    _pipeline_changed!(workspace,residual)
    _pipeline_changed!(workspace,scale)
    @inbounds for row in eachindex(residual)
        rhs = scale[row]
        residual[row] = -rhs
        scale[row] = abs(rhs)
    end
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        value = @inbounds direction[basis_row]
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                row = A.rowval[position]
                term = A.nzval[position] * value
                residual[row] += term
                scale[row] += abs(term)
            end
        else
            row = index - column_count
            @inbounds residual[row] -= value
            @inbounds scale[row] += abs(value)
        end
    end
    roundoff = T(256) * eps(one(T))
    pivot_tolerance = sqrt(eps(one(T))) * abs(pivot)
    @inbounds for row in eachindex(residual)
        isfinite(residual[row]) && isfinite(scale[row]) || return false
        tolerance = max(workspace.options.zero_tolerance, pivot_tolerance,
                        roundoff * (scale[row] + one(T)))
        abs(residual[row]) <= tolerance || return false
    end
    return true
end

function _dual_row_residual_ratio(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, leaving_row::Int) where {T<:AbstractFloat}
    A = workspace.problem.A
    row_count, column_count = size(A)
    length(rho) == length(workspace.basis.basic_indices) == row_count ||
        throw(DimensionMismatch("tableau residual vectors must match the row count"))
    roundoff = T(256) * eps(one(T))
    worst_ratio = zero(T)
    for (basis_row, index) in enumerate(workspace.basis.basic_indices)
        1 <= index <= column_count + row_count || throw(BoundsError(workspace.primal, index))
        expected = basis_row == leaving_row ? one(T) : zero(T)
        residual = -expected
        scale = expected
        if index <= column_count
            @inbounds for position in A.colptr[index]:(A.colptr[index + 1] - 1)
                term = A.nzval[position] * rho[A.rowval[position]]
                residual += term
                scale += abs(term)
            end
        else
            term = @inbounds -rho[index - column_count]
            residual += term
            scale += abs(term)
        end
        isfinite(residual) && isfinite(scale) || return T(Inf)
        tolerance = max(workspace.options.zero_tolerance,
                        roundoff * (scale + one(T)))
        isfinite(tolerance) || return T(Inf)
        worst_ratio = max(worst_ratio, abs(residual) / tolerance)
    end
    return worst_ratio
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
isresidual(s)=s in (:direction_residual,:row_residual)
scopes(::Type{T}) where T=T<:AbstractFloat ? (:direction_residual,:row_residual,:primal_ratio,:harris) : (:primal_ratio,:harris)
patterns(scope)=isresidual(scope) ? (:exact,:perturbed) : (:positive,:negative,:mixed,:ties,:unique)
function inputs(v)
 w=v.w;A=w.problem.A
 (A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights,v.vector,v.rhs)
end
scalar_inputs(v)=(v.pivot,v.orientation,fields(v.w.options),fields(v.w.progress.numerical_policy))
function outputs(v)
 w=v.w;c=w.scratch.hypersparse
 (w.scratch.tau,w.scratch.row_rhs,w.scratch.candidates,isnothing(c) ? () : (c.valid,c.support_rebuilds))
end
function fixture(::Type{T},n,scope,density,pattern) where T
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
function reset_fixture!(v)
 if v.scope===:direction_residual
  copyto!(v.w.scratch.row_rhs,v.rhs);fill!(v.w.scratch.hypersparse.valid,true)
 end
 nothing
end
for (method,module_) in [(:original,:ResidualReference),(:candidate,:JSimplex)]
 @eval begin
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:direction_residual},v)=$module_._dual_direction_residual_ok!(v.w,v.vector,v.pivot)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:row_residual},v)=$module_._dual_row_residual_ratio(v.w,v.vector,1)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:primal_ratio},v)=$module_._primal_ratio(v.w,1,v.orientation,v.vector)
  @noinline whole(::Val{$(QuoteNode(method))},::Val{:harris},v)=$module_.dual_ratio_test(v.w,v.vector,v.orientation)
 end
end
@inline sink(x::Bool)=Int(x)
@inline sink(x::Int)=x
@inline sink(x::AbstractFloat)=isfinite(x) ? (x>1 ? 2 : iszero(x) ? 0 : 1) : -2
@inline sink(x::Tuple)=100x[2]+Int(x[3])+(isnothing(x[1]) ? -10000 : 1)
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(method::M,scope::S,v::V) where {M,S,V}
 t=@timed runwhole(method,scope,v);merge(cost(t),Dict("sink"=>t.value))
end
function checkpair(a,b)
 sv=Val(a.scope);reset_fixture!(a);reset_fixture!(b)
 x=capture(()->whole(Val(:original),sv,a));y=capture(()->whole(Val(:candidate),sv,b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 x
end
function special_correctness(::Type{T}) where T
 for scope in scopes(T),direction in (-one(T),one(T))
  a=fixture(T,8,scope,:dense,:mixed);b=fixture(T,8,scope,:dense,:mixed)
  a=merge(a,(orientation=direction,));b=merge(b,(orientation=direction,));checkpair(a,b)
 end
 if T<:AbstractFloat
  for scope in (:direction_residual,:row_residual)
   a=fixture(T,0,scope,:dense,:exact);b=fixture(T,0,scope,:dense,:exact)
   x=checkpair(a,b);@test x[1]===:value&&(scope===:direction_residual ? x[2]===true : iszero(x[2]))
  end
 end
 if T===BigFloat
  for scope in (:direction_residual,:row_residual),variant in (:huge,:tiny,:tol512)
   a=fixture(T,8,scope,:dense,:exact);b=fixture(T,8,scope,:dense,:exact)
   for v in (a,b)
    if variant===:tol512
     opts=v.w.options;wide=setprecision(()->BigFloat(3//7),BigFloat,512)
     v.w.options=typeof(opts)((n===:zero_tolerance ? wide : getfield(opts,n) for n in fieldnames(typeof(opts)))...)
    else
     factor=ldexp(one(T),variant===:huge ? 10000 : -10000)
     for i in eachindex(v.vector);v.vector[i]*=factor;end
     for i in eachindex(v.rhs);v.rhs[i]*=factor;end
    end
   end
   sa=snap(inputs(a));sb=snap(inputs(b));x=checkpair(a,b)
   @test x[1]===:value&&intact(inputs(a),sa)&&intact(inputs(b),sb)
  end
 end
 for variant in (:fixed,:basic,:free,:short_states,:short_prices,:no_candidates,:tol512,:extreme)
  a=fixture(T,8,:harris,:dense,:positive);b=fixture(T,8,:harris,:dense,:positive)
  for v in (a,b)
   w=v.w
   if variant===:fixed;w.lower[2]=w.upper[2]
   elseif variant===:basic;w.basis.states[2]=J.BASIC
   elseif variant===:free;w.basis.states[2]=J.FREE_NONBASIC;w.lower[2]=J._unbounded_bound(T);w.upper[2]=J._unbounded_bound(T)
   elseif variant===:short_states;resize!(w.basis.states,4)
   elseif variant===:short_prices;resize!(w.reduced_costs,4)
   elseif variant===:no_candidates;fill!(v.vector,zero(T))
   elseif variant===:tol512&&T===BigFloat
    opts=w.options;wide=setprecision(()->BigFloat(3//7),BigFloat,512)
    w.options=typeof(opts)((n===:dual_tolerance ? wide : getfield(opts,n) for n in fieldnames(typeof(opts)))...)
   elseif variant===:extreme&&T===BigFloat;v.vector[1]=ldexp(one(T),10000);w.reduced_costs[1]=v.vector[1]
   end
  end
  sa=snap(inputs(a));sb=snap(inputs(b));x=checkpair(a,b)
  @test intact(inputs(a),sa)&&intact(inputs(b),sb)
  if variant in (:short_states,:short_prices);@test x[1]===:error&&x[2]===BoundsError;@test a.w.scratch.candidates==collect(1:(variant===:short_prices ? 5 : 4));end
  if variant===:no_candidates;@test x==(:value,-1)&&isempty(a.w.scratch.candidates);end
 end
 # Exact dyadic tolerated violation; no recomputation, adapter or altered policy.
 for unsafe in (false,true),direction in (-one(T),one(T))
  a=fixture(T,2,:primal_ratio,:dense,:negative);b=fixture(T,2,:primal_ratio,:dense,:negative)
  for v in (a,b)
   w=v.w;opts=w.options;tol=T(1//8)
   w.options=typeof(opts)((n===:primal_tolerance ? tol : getfield(opts,n) for n in fieldnames(typeof(opts)))...)
   v.vector[1]=-one(T);v.vector[2]=unsafe ? T(10) : -T(2)
   if direction>0;w.lower[1]=Bound(zero(T));else;w.upper[1]=Bound(zero(T));end
   for i in eachindex(v.vector);v.vector[i]*=direction;end
   w.upper[2]=Bound(one(T));w.primal[2]=T(17//16)
   w.lower[3]=Bound(zero(T));w.upper[3]=Bound(unsafe ? zero(T) : T(2))
   push!(w.scratch.rejected_rows,2)
  end
  a=merge(a,(orientation=direction,));b=merge(b,(orientation=direction,))
  @test J._primal_bound_snap_feasible(a.w,1,direction,a.vector,1)===!unsafe
  @test !J._primal_step_bounds_feasible(a.w,direction,a.vector,one(T))
  x=checkpair(a,b)
  @test x[1]===:value&&(unsafe ? isnothing(x[2][1])&&x[2][2]==-1 : iszero(x[2][1])&&x[2][2]==1)
 end
end
function correctness(::Type{T}) where T
 @testset "Residual magnitudes $T" begin
  special_correctness(T)
  for scope in scopes(T),density in (:sparse,:dense),pattern in patterns(scope)
   a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern)
   sa=snap(inputs(a));sb=snap(inputs(b));ca=deepcopy(scalar_inputs(a));cb=deepcopy(scalar_inputs(b))
   ownersa=(a.w.scratch.tau,a.w.scratch.row_rhs,a.w.scratch.candidates);ownersb=(b.w.scratch.tau,b.w.scratch.row_rhs,b.w.scratch.candidates)
   x=checkpair(a,b)
   @test ownersa[1]===a.w.scratch.tau&&ownersa[2]===a.w.scratch.row_rhs&&ownersa[3]===a.w.scratch.candidates
   @test ownersb[1]===b.w.scratch.tau&&ownersb[2]===b.w.scratch.row_rhs&&ownersb[3]===b.w.scratch.candidates
   @test intact(inputs(a),sa)&&intact(inputs(b),sb)
   @test same(scalar_inputs(a),ca)&&same(scalar_inputs(b),cb)
   if scope===:direction_residual
    @test x==(:value,pattern===:exact)
    @test count(!,a.w.scratch.hypersparse.valid)==2
   elseif scope===:row_residual
    @test x[1]===:value&&(pattern===:exact ? iszero(x[2]) : x[2]>1)
   elseif scope===:primal_ratio
    @test x[1]===:value&&x[2][2]>0&&x[2][1]>=0
    if T===BigFloat;reset_fixture!(a);x2=whole(Val(:original),Val(scope),a);reset_fixture!(b);y2=whole(Val(:candidate),Val(scope),b);@test x[2][1]!==x2[1]&&x2[1]!==y2[1];end
   else;@test x[1]===:value&&x[2]>0;end
  end
  for scope in scopes(T),variant in (:empty,:short,:nonfinite,:negative_zero,:mixed_precision,:invalid_basis,:rejected,:unbounded,:negative_step,:alias)
   a=fixture(T,8,scope,:dense,:mixed);b=fixture(T,8,scope,:dense,:mixed)
   for side in (:a,:b)
    v=side===:a ? a : b;w=v.w
    if variant===:empty
     if isresidual(scope);empty!(w.basis.basic_indices);v=merge(v,(vector=T[],));if scope===:direction_residual;empty!(w.scratch.tau);empty!(w.scratch.row_rhs);v=merge(v,(rhs=T[],));end
     else;fill!(v.vector,zero(T));end
    elseif variant===:short
     if isresidual(scope);v=merge(v,(vector=T[],));else;resize!(w.lower,0);end
    elseif variant===:nonfinite&&T<:AbstractFloat;v.vector[1]=T(Inf)
    elseif variant===:negative_zero&&T<:AbstractFloat;v.vector[1]=-zero(T)
    elseif variant===:mixed_precision&&T===BigFloat
     v.vector[1]=setprecision(()->BigFloat(3//7),BigFloat,512);v=merge(v,(pivot=setprecision(()->BigFloat(3//7),BigFloat,512),))
    elseif variant===:invalid_basis;w.basis.basic_indices[end]=length(w.primal)+1
    elseif variant===:rejected;push!(w.scratch.rejected_rows,1);push!(w.scratch.rejected_entering,1)
    elseif variant===:unbounded
     for i in eachindex(w.lower);w.lower[i]=J._unbounded_bound(T);w.upper[i]=J._unbounded_bound(T);end
    elseif variant===:negative_step
     if scope===:primal_ratio;w.primal[w.basis.basic_indices[1]]=T(9)
     elseif scope===:harris;w.reduced_costs[1]=-abs(v.vector[1]);end
    elseif variant===:alias
     if scope===:direction_residual;w.scratch.tau=w.scratch.row_rhs
     elseif scope===:row_residual;v=merge(v,(vector=w.scratch.row_rhs,))
     elseif scope===:harris;v=merge(v,(vector=w.reduced_costs,));end
    end
    if side===:a;a=v;else;b=v;end
   end
   sa=snap(inputs(a));sb=snap(inputs(b));x=checkpair(a,b)
   if variant!==:alias;@test intact(inputs(a),sa)&&intact(inputs(b),sb);end
   if variant===:empty&&isresidual(scope);@test x[1]===:error&&x[2]===DimensionMismatch;end
   if variant===:short&&isresidual(scope);@test x[1]===:error&&x[2]===DimensionMismatch;end
   if variant===:invalid_basis&&isresidual(scope);@test x[1]===:error&&x[2]===BoundsError;end
  end
  if T===BigFloat
   for x in (BigFloat(0),-BigFloat(0),BigFloat(3//7),-BigFloat(3//7),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN),setprecision(()->BigFloat(3//7),BigFloat,512),setprecision(()->BigFloat(-3//7),BigFloat,512))
    @test same(abs(x),J._primal_direction_magnitude(x))
   end
  end
 end
end

function allocation_gate(scope,pattern)
 a=fixture(BigFloat,128,scope,:sparse,pattern);b=fixture(BigFloat,128,scope,:sparse,pattern);sv=Val(scope)
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
  @test same(outputs(a),outputs(b))
 end
 @test all(after[i][1]+256<before[i][1]&&after[i][2]+16<before[i][2] for i in eachindex(before)) # RED costgate
end
@testset "Generic residual magnitudes" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do;setrounding(BigFloat,mode) do;correctness(BigFloat);end;end
 end
 for T in (Rational{BigInt},Float32,Float64,Rational{Int64});correctness(T);end
 @testset "Whole-call allocation gates" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    allocation_gate(:direction_residual,:exact)
    allocation_gate(:row_residual,:exact)
    allocation_gate(:primal_ratio,:negative)
    allocation_gate(:harris,:positive)

   end
  end
 end
 @testset "Unchanged native and fixed-rational costs" begin
  for T in (Float32,Float64,Rational{Int64}),scope in scopes(T)
   pattern=first(patterns(scope));a=fixture(T,32,scope,:sparse,pattern);b=fixture(T,32,scope,:sparse,pattern);sv=Val(scope)
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
