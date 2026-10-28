module GenericSumRationalGrowthTests
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
module SRGReference
import JSimplex
using JSimplex: SimplexWorkspace,LinearProblem,Bound,bound_value,PFIFactorization,_is_exact,_primal_nearest_rounding,_primal_direction_magnitude,_infeasibility_bound_allowance,_factor_storage_count,_with_recovery_precision,refactor_reason
using SparseArrays
_refined_primal_rows_feasible(args...) = JSimplex._refined_primal_rows_feasible(args...)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},b::Bool) where {T<:AbstractFloat} = JSimplex._infeasibility_certified(w,rho,b)
_factor_growth_measure(factor) = JSimplex._factor_growth_measure(factor)
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
        left_magnitude, right_magnitude = _primal_direction_magnitude(left), _primal_direction_magnitude(right)
        if min(left_magnitude, right_magnitude) >= ldexp(nextfloat(zero(T)), precision(T))
            large, small = left_magnitude >= right_magnitude ? (left, right) : (right, left)
            error = (large - value) + small
            if isfinite(error)
                return error < 0 ? (prevfloat(value), value) :
                       error > 0 ? (value, nextfloat(value)) : (value, value)
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

# Exact integer comparisons avoid temporary zeros; every enclosure guard remains.
function _primal_product_bounds(left::BigFloat, right::BigFloat)
    T=BigFloat
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
           _primal_direction_magnitude(value) >= ldexp(nextfloat(zero(T)), precision(left) + precision(right)))
            return error < 0 ? (prevfloat(value), value) :
                   error > 0 ? (value, nextfloat(value)) : (value, value)
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


_refined_primal_rows_feasible(::LinearProblem, ::Vector, tolerance, rows) = false

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

_original_primal_feasible(workspace::SimplexWorkspace{T}, primal::Vector{T}) where {T} =
    _original_primal_feasible(workspace.problem, primal, workspace.options.primal_tolerance)

function _infeasibility_certified(workspace::SimplexWorkspace{T},
                                  rho::Vector{T}, below::Bool) where {T<:Rational}
    try
        A = workspace.problem.A
        n = size(A,2)
        orientation = below ? one(T) : -one(T)
        minimum_value = zero(T)
        for index in eachindex(workspace.lower)
            coefficient = zero(T)
            if index <= n
                for position in nzrange(A,index)
                    coefficient += orientation*rho[A.rowval[position]]*A.nzval[position]
                end
            else
                coefficient = -orientation*rho[index-n]
            end
            iszero(coefficient) && continue
            bound = coefficient > zero(T) ? workspace.lower[index] : workspace.upper[index]
            isfinite(bound) || return false
            minimum_value += coefficient*bound_value(bound) -
                abs(coefficient)*_infeasibility_bound_allowance(workspace,index)
        end
        return minimum_value > zero(T)
    catch exception
        # Bounded rational intermediates may exceed their integer storage.
        # Failure to represent the proof is inconclusive, never infeasibility.
        exception isa OverflowError || rethrow()
        return false
    end
end

_factor_growth_measure(factor::PFIFactorization{T}) where T =
    maximum(eta -> maximum(abs,eta.values;init=one(T)),factor.updates;init=one(T))

function _refresh_refactor_metrics!(ws;force::Bool=false)
    state = ws.scratch.refactorization
    age = state.nupdates = length(ws.factorization.updates)
    if !force
        age == state.metrics_update_count && return nothing
        age == 1 || iszero(age % 8) || age >= state.interval || return nothing
    end
    state.stored_elements = _factor_storage_count(ws.factorization)
    if !state.fixed
        state.growth_scale = _with_recovery_precision(ws,ws) do
            current = _factor_growth_measure(ws.factorization)
            baseline = state.base_growth_scale
            iszero(baseline) ? (iszero(current) ? 1.0 : Inf) : Float64(current/baseline)
        end
    end
    state.metrics_update_count = age
    return nothing
end

function _scheduled_refactor_reason(ws, algorithm::Symbol)
    if ws.progress.numerical_policy.adaptive_refactor
        state = ws.scratch.refactorization
        state.nupdates = length(ws.factorization.updates)
        state.fixed || _refresh_refactor_metrics!(ws)
        # Preserve numerical reason priority when a safety limit coincides
        # with a residual or growth trigger.
        reason = refactor_reason(state,ws.progress.numerical_policy)
        reason != :none && return reason
        # Once the numerical limit fully recovers, economics may again grow
        # the interval beyond the configured initial value.
        return state.nupdates >= ws.dual_refactorization_interval ? :limit : :none
    end
    interval = min(ws.options.refactorization_interval, ws.dual_refactorization_interval)
    return length(ws.factorization.updates) >= interval ? :limit : :none
end


end

const SRGA=JSimplex
const SRGB=JSimplex
const SRGC=JSimplex
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
modof(::Val{:original})=SRGReference
modof(::Val{:A})=SRGA
modof(::Val{:B})=SRGB
modof(::Val{:C})=SRGC
statevalues(s)=Tuple(getfield(s,k) for k in fieldnames(typeof(s)))
function restorestate!(s,t)
 for (k,v) in zip(fieldnames(typeof(s)),t);setfield!(s,k,v);end
 nothing
end
function fixture(::Type{T},n,density,shape,scope;below=true,mode=:valid,chain=8) where T
 if scope in (:rows,:feasible)
  m=min(8,n);A=zeros(T,m,n)
  for j in 1:n,i in 1:m
   if density===:dense||(i+j)%5==0
    sign=shape===:negative||shape===:mixed&&isodd(j) ? -1 : 1
    A[i,j]=T(sign*((i+j)%7+1)//16)
   end
  end
  p=LinearProblem(sparse(A),zeros(T,n);row_lower=fill(-T(4096),m),row_upper=fill(T(4096),m),column_lower=fill(-T(4),n),column_upper=fill(T(4),n))
  x=fill(T(1//2),n)
  return (scope=scope,p=p,x=x,lower=zeros(T,m),upper=zeros(T,m),tol=zero(T))
 elseif scope===:cert
  m=min(8,n);A=zeros(T,m,n)
  for j in 1:n,i in 1:m
   if density===:dense||(i+j)%5==0||(i==1&&j==1)
    A[i,j]=shape===:wide && T===Rational{BigInt} ? T((big(1)<<127)+i+j,(big(1)<<63)+13) : T(((i+j)%7+1)//16)
   end
  end
  p=LinearProblem(sparse(A),zeros(T,n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),m),row_upper=fill(T(8),m))
  o=SolverOptions(T;verbose=false,pricing=:dantzig,basis_update=:pfi)
  pol=J.NumericalPolicy(T;refactor_timing=false,solve_refinement=false,recovery=false)
  w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol));rho=fill(T(1//8),m)
  endpoint=(below ? 1 : -1)*(mode===:invalid ? -1 : 1)*T(2)
  for j in 1:n
   w.lower[j]=Bound(endpoint);w.upper[j]=Bound(endpoint)
   if mode===:one_sided
    if below;w.upper[j]=J._unbounded_bound(T);else;w.lower[j]=J._unbounded_bound(T);end
   end
  end
  for j in n+1:n+m;w.lower[j]=Bound(zero(T));w.upper[j]=Bound(zero(T));end
  if mode===:zero_tol
   opts=w.options;w.options=typeof(opts)((k===:primal_tolerance ? zero(T) : getfield(opts,k) for k in fieldnames(typeof(opts)))...)
  end
  return (scope=scope,w=w,rho=rho,below=below,mode=mode)
 end
 # A real PFI and genuine replace_column! calls construct the packed update chain.
 p=LinearProblem(spdiagm(0=>ones(T,n)),zeros(T,n);row_lower=fill(-T(8),n),row_upper=fill(T(8),n))
 o=SolverOptions(T;verbose=false,basis_update=:pfi,refactorization_interval=20)
 pol=J.NumericalPolicy(T;simplex_strategy=:adaptive,refactor_timing=false,solve_refinement=false,recovery=false)
 w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 for k in 1:chain
  pivot=mod1(k,n);direction=zeros(T,n);pv=shape===:negative ? -T(1//2) : T(1//2);direction[pivot]=pv
  for i in 1:n
   i==pivot&&continue
   if density===:dense||mod(i+k,4)==0
    desired=shape===:negative||shape===:mixed&&isodd(i+k) ? -T((i%5+1)//8) : T((i%5+1)//8)
    direction[i]=-desired*pv
   end
  end
  J.replace_column!(w.factorization,direction,pivot;zero_tolerance=zero(T))
 end
 w.scratch.refactorization.metrics_update_count=-1
 return (scope=scope,w=w,initial=statevalues(w.scratch.refactorization),chain=chain)
end
function reset!(v)
 if v.scope in (:growth,:refresh,:scheduled);restorestate!(v.w.scratch.refactorization,v.initial);end
 nothing
end
@noinline function whole(tag::A,v::V) where {A,V}
 mod=modof(tag)
 if v.scope===:rows
  return eltype(v.x)<:Rational ? mod._primal_row_bounds(v.p.A,v.x,J._is_exact(eltype(v.x))) : mod._primal_row_bounds!(v.lower,v.upper,v.p.A,v.x)
 elseif v.scope===:feasible;return mod._original_primal_feasible(v.p,v.x,v.tol)
 elseif v.scope===:cert;return mod._infeasibility_certified(v.w,v.rho,v.below)
 elseif v.scope===:growth;return mod._factor_growth_measure(v.w.factorization)
 elseif v.scope===:refresh;return mod._refresh_refactor_metrics!(v.w;force=true)
 end
 mod._scheduled_refactor_reason(v.w,:dual)
end
function inputvalues(v)
 if v.scope in (:rows,:feasible)
  return (v.p.A.colptr,v.p.A.rowval,v.p.A.nzval,v.x,v.p.column_lower,v.p.column_upper,v.p.row_lower,v.p.row_upper,v.tol)
 end
 w=v.w
 arrays=((w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,w.progress.objective,w.progress.objective_constant),w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.reduced_costs,w.pricing_weights,w.progress.scaling.row_factors,w.progress.scaling.column_factors)
 if v.scope===:cert;return (arrays,v.rho,statevalues(w.options),statevalues(w.progress.numerical_policy));end
 (arrays,Tuple((e.indices,e.values,e.pivot_row) for e in w.factorization.updates),w.factorization.work,Tuple(getfield(w.factorization.base.factorization,k) for k in fieldnames(typeof(w.factorization.base.factorization)) if getfield(w.factorization.base.factorization,k) isa AbstractArray{<:Real}),statevalues(w.options),statevalues(w.progress.numerical_policy))
end
function owners(x)
 if x isa BigFloat;return (x,)
 elseif x isa Rational{BigInt};return (numerator(x),denominator(x))
 elseif x isa J.Bound;return owners(x.value)
 elseif x isa AbstractArray;return (x,Tuple(owners(y) for y in x))
 elseif x isa Tuple;return Tuple(owners(y) for y in x)
 end
 nothing
end
sameowners(a,b)=a===b
sameowners(a::Tuple,b::Tuple)=length(a)==length(b)&&all(sameowners(x,y) for (x,y) in zip(a,b))
function checkpair(a,b,arm)
 va=deepcopy(inputvalues(a));vb=deepcopy(inputvalues(b));oa=owners(inputvalues(a));ob=owners(inputvalues(b));reset!(a);reset!(b)
 ambient=(precision(BigFloat),rounding(BigFloat));x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b));@test same(x,y);@test ambient==(precision(BigFloat),rounding(BigFloat))
 @test same(va,inputvalues(a));@test same(vb,inputvalues(b));@test sameowners(oa,owners(inputvalues(a)));@test sameowners(ob,owners(inputvalues(b)))
 if a.scope in (:growth,:refresh,:scheduled);@test same(statevalues(a.w.scratch.refactorization),statevalues(b.w.scratch.refactorization));end
 if a.scope===:rows && x[1]===:value && y[1]===:value
  if eltype(a.x)<:Rational
   @test x[2][1]===x[2][2];@test y[2][1]===y[2][2]
  else
   @test x[2][1]===a.lower&&x[2][2]===a.upper;@test y[2][1]===b.lower&&y[2][2]===b.upper
  end
 end
 x
end
resultkey(x::Bool)=Int(x)
resultkey(::Nothing)=0
resultkey(x::Symbol)=String(x)
resultkey(x::Real)=Float64(x)
resultkey(x::Tuple{<:AbstractArray,<:AbstractArray})=sum(Float64.(x[1]))+sum(Float64.(x[2]))
@noinline function timed(tag::A,v::V) where {A,V}
 t=@timed whole(tag,v);k=@timed resultkey(t.value)
 merge(cost(t),Dict("result"=>k.value,"capture_preparation"=>cost(k)))
end
function aliaspattern(x,a,b)
 x[1]===:value||return ()
 out=x[2]
 out isa Tuple||return ()
 Tuple((y===a,y===b, y isa BigFloat ? precision(y) : 0) for y in out)
end
function correctness(::Type{T}) where T
 @testset "ordinary whole functions $(T)" begin
  for shape in (:positive,:negative,:mixed),density in (:sparse,:dense),scope in (:rows,:feasible)
   a=fixture(T,16,density,shape,scope);b=fixture(T,16,density,shape,scope);out=checkpair(a,b,:A);@test out[1]===:value
   if scope===:feasible
    @test out[2]===true
    a.p.row_lower[1]=Bound(T(8192));b.p.row_lower[1]=Bound(T(8192));@test checkpair(a,b,:A)[2]===false
   else
    exact=Rational{BigInt}.(a.p.A)*Rational{BigInt}.(a.x)
    @test all(Rational{BigInt}(out[2][1][i])<=exact[i]<=Rational{BigInt}(out[2][2][i]) for i in eachindex(exact))
   end
  end
  for below in (true,false),mode in (:valid,:invalid,:one_sided,:zero_tol),shape in (T===Rational{BigInt} ? (:positive,:wide) : (:positive,))
   a=fixture(T,16,:sparse,shape,:cert;below,mode);b=fixture(T,16,:sparse,shape,:cert;below,mode)
   @test checkpair(a,b,:B)==(:value,mode!==:invalid)
  end
  for chain in (0,1,4,8,32),shape in (:positive,:negative,:mixed),scope in (:growth,:refresh,:scheduled)
   a=fixture(T,8,:sparse,shape,scope;chain);b=fixture(T,8,:sparse,shape,scope;chain)
   out=checkpair(a,b,:C);@test out[1]===:value
   if scope===:growth;@test out[2]==(chain==0 ? one(T) : T(2));end
   if scope!==:growth
    @test a.w.scratch.refactorization.nupdates==chain
   end
  end
  for aa in (T(1),-T(1),zero(T)),bb in (T(1),-T(1),zero(T))
   x=capture(()->SRGReference._primal_sum_bounds(aa,bb));y=capture(()->SRGA._primal_sum_bounds(aa,bb));@test same(x,y);@test aliaspattern(x,aa,bb)==aliaspattern(y,aa,bb)
   @test x[1]===:value&&x[2][1]<=aa+bb<=x[2][2]
  end
 end
end

function extra_correctness(::Type{T}) where T
 @testset "independent boundaries $(T)" begin
  # Exact dyadics independently fix the expected sum; owner patterns are separate.
  pairs=[(T(3//2),T(1//4),T(7//4)),(-T(3//2),-T(1//4),-T(7//4)),(T(3//2),-T(3//2),zero(T)),(T(3//2),-T(1//4),T(5//4))]
  for (a,b,want) in pairs
   old=SRGReference._primal_sum_bounds(a,b);new=SRGA._primal_sum_bounds(a,b)
   @test same(old,new);@test new[1]<=want<=new[2]
   @test (old[1]===a,old[2]===a,old[1]===b,old[2]===b,old[1]===old[2])==(new[1]===a,new[2]===a,new[1]===b,new[2]===b,new[1]===new[2])
   if T===BigFloat&&iszero(want);@test new[1]!==new[2];end
  end
  # Truly empty/invalid primal structures and finite row/column rejection.
  for density in (:sparse,:dense)
   a=fixture(T,16,density,:positive,:feasible);b=fixture(T,16,density,:positive,:feasible)
   a.p.column_upper[1]=Bound(zero(T));b.p.column_upper[1]=Bound(zero(T));@test checkpair(a,b,:A)==(:value,false)
  end
  for chain in (0,1,4,8,32),scope in (:refresh,:scheduled)
   a=fixture(T,8,:dense,:mixed,scope;chain);b=fixture(T,8,:dense,:mixed,scope;chain)
   for fixed in (false,true),cached in (false,true)
    for v in (a,b)
     v.w.scratch.refactorization.fixed=fixed
     v.w.scratch.refactorization.metrics_update_count=cached ? chain : -1
    end
    # Explicitly freeze the changed initial state; resets keep the intended gate.
    aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),))
    @test checkpair(aa,bb,:C)[1]===:value
   end
  end
  if T===BigFloat
   wide=setprecision(BigFloat,512) do
    (BigFloat(3//2),BigFloat(-3//2),floatmax(BigFloat),-floatmax(BigFloat))
   end
   values=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN),wide...)
   for a in values,b in values
    x=capture(()->SRGReference._primal_sum_bounds(a,b));y=capture(()->SRGA._primal_sum_bounds(a,b));@test same(x,y)
    @test aliaspattern(x,a,b)==aliaspattern(y,a,b)
    if x[1]===:value;@test (x[2][1]===x[2][2])==(y[2][1]===y[2][2]);end
   end
   for probe in (:unit,:wide_positive,:wide_negative,:nan,:inf,:growth)
    a=fixture(T,8,:dense,:positive,:growth;chain=1);b=fixture(T,8,:dense,:positive,:growth;chain=1)
    for v in (a,b)
     fill!(v.w.factorization.updates[1].values,one(T))
     value=probe===:unit ? one(T) : probe===:wide_positive ? wide[1] : probe===:wide_negative ? wide[2] : probe===:nan ? T(NaN) : probe===:inf ? T(Inf) : T(10^10)
     v.w.factorization.updates[1].values[1]=value
    end
    x=checkpair(a,b,:C);@test x[1]===:value
    old=x[2];new=whole(Val(:C),b)
    @test Tuple(old===z for z in a.w.factorization.updates[1].values)==Tuple(new===z for z in b.w.factorization.updates[1].values)
    @test same(new,whole(Val(:C),b))
   end
   # A growth failure outranks the coincident configured interval, then residual wins.
   a=fixture(T,8,:dense,:positive,:scheduled;chain=32);b=fixture(T,8,:dense,:positive,:scheduled;chain=32)
   for v in (a,b);v.w.factorization.updates[1].values[1]=T(10^10);end
   @test checkpair(a,b,:C)==(:value,:pivot_growth)
   for v in (a,b);v.w.scratch.refactorization.residual_bad=true;end
   aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),));@test checkpair(aa,bb,:C)==(:value,:residual)
  elseif T===Rational{BigInt}
   for below in (true,false),mode in (:valid,:one_sided),what in (:infinite,:explicit_zero),rhosign in (1,-1)
    a=fixture(T,16,:dense,:wide,:cert;below,mode);b=fixture(T,16,:dense,:wide,:cert;below,mode)
    for v in (a,b)
     v.rho[1]=T(rhosign,0)
     what===:explicit_zero&&(v.w.problem.A.nzval[1]=zero(T))
    end
    out=checkpair(a,b,:B)
    if rhosign==-1&&mode===:one_sided&&what===:infinite
     @test out[1]===:value;@test out[2]===false
    else
     @test out[1]===:error;@test out[2]===DivideError
    end
   end
  elseif T===Rational{Int64}
   for below in (true,false)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    for v in (a,b);v.rho[1]=T(2);v.w.problem.A.nzval[1]=T(typemax(Int64));end
    @test checkpair(a,b,:B)==(:value,false)
   end
  end
  # Empty matrix/point/certificate and zero-dimensional PFI use the real paths.
  for scope in (:rows,:feasible)
   a=fixture(T,0,:sparse,:positive,scope);b=fixture(T,0,:sparse,:positive,scope);out=checkpair(a,b,:A)
   @test out[1]===:value
   if scope===:feasible;@test out[2]===true;else;@test isempty(out[2][1])&&isempty(out[2][2]);end
  end
  for below in (true,false)
   a=fixture(T,0,:sparse,:positive,:cert;below);b=fixture(T,0,:sparse,:positive,:cert;below);@test checkpair(a,b,:B)==(:value,false)
  end
  for scope in (:growth,:refresh,:scheduled)
   a=fixture(T,0,:sparse,:positive,scope;chain=0);b=fixture(T,0,:sparse,:positive,scope;chain=0);@test checkpair(a,b,:C)[1]===:value
  end
  if T===BigFloat
   for chain in (0,1)
    a=fixture(T,8,:dense,:positive,:growth;chain);b=fixture(T,8,:dense,:positive,:growth;chain)
    for v in (a,b),eta in v.w.factorization.updates;fill!(eta.values,T(1//2));end
    old1=whole(Val(:original),a);old2=whole(Val(:original),a);new1=whole(Val(:C),b);new2=whole(Val(:C),b)
    @test same(old1,new1)&&same(old2,new2)&&new1==1
    @test old1!==old2;@test new1!==new2
    @test all(new1!==z for eta in b.w.factorization.updates for z in eta.values)
   end
   # Independently chosen dyadic lies just above the binary64 midpoint;
   # ambient64/128/256 loses its last bit, while the actual recovery512 path retains it.
   wideweight=setprecision(BigFloat,512) do
    -(BigFloat(1)+ldexp(BigFloat(1),-53)+ldexp(BigFloat(1),-400))
   end
   exactweight=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)+Rational{BigInt}(1,big(1)<<400)
   expected_float=rounding(BigFloat) in (RoundDown,RoundToZero) ? 1.0 : nextfloat(1.0)
   for site in (:cost,:policy,:bound),scope in (:refresh,:scheduled)
    a=fixture(T,8,:dense,:positive,scope;chain=8);b=fixture(T,8,:dense,:positive,scope;chain=8)
    for v in (a,b)
     for eta in v.w.factorization.updates;fill!(eta.values,T(1//2));end
     v.w.factorization.updates[1].values[1]=wideweight
     if site===:cost
      v.w.costs[1]=BigFloat(v.w.costs[1];precision=512)
     elseif site===:bound
      v.w.lower[end]=Bound(BigFloat(bound_value(v.w.lower[end]);precision=512))
     else
      p=v.w.progress;old=p.numerical_policy;tol=BigFloat(old.solve_tolerance;precision=512)
      pol=typeof(old)((k===:solve_tolerance ? tol : getfield(old,k) for k in fieldnames(typeof(old)))...)
      v.w.progress=typeof(p)((k===:numerical_policy ? pol : getfield(p,k) for k in fieldnames(typeof(p)))...)
     end
    end
    aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),))
    @test checkpair(aa,bb,:C)[1]===:value
    @test a.w.scratch.refactorization.growth_scale===expected_float
    @test b.w.scratch.refactorization.growth_scale===expected_float
    @test b.w.scratch.refactorization.metrics_update_count==8
    @test b.w.scratch.refactorization.stored_elements==J._factor_storage_count(b.w.factorization)
    precise=setprecision(BigFloat,512) do;SRGC._factor_growth_measure(b.w.factorization);end
    @test precision(precise)==512
    old_decoded=Rational{BigInt}(precise)
    rounded_expected=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)
    if rounding(BigFloat) in (RoundUp,RoundFromZero)
     rounded_expected+=Rational{BigInt}(1,big(1)<<(precision(BigFloat)-1))
    end
    @test old_decoded==rounded_expected
    @test old_decoded!=exactweight
    ambient=(precision(BigFloat),rounding(BigFloat))
    decoded=setprecision(BigFloat,precision(precise)) do
     Rational{BigInt}(precise)
    end
    @test decoded==exactweight
    @test ambient==(precision(BigFloat),rounding(BigFloat))
   end
  end
  # Caller ambient precision and rounding must be restored even on failure paths.
  @test precision(BigFloat)>=64
 end
end

function allocation_gate(::Type{T},scope,arm,n,density,shape,below,chain) where T
 a=fixture(T,n,density,shape,scope;below,chain);b=fixture(T,n,density,shape,scope;below,chain)
 checkpair(a,b,arm)
 for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
 before=Any[];after=Any[]
 for pair in 1:3,tag in (isodd(pair) ? (:original,arm) : (arm,:original))
  v=tag===:original ? a : b;reset!(v);t=timed(Val(tag),v)
  @test t["compile_seconds"]==t["recompile_seconds"]==0
  push!(tag===:original ? before : after,t)
 end
 @test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)
 nothing
end
@testset "Multiprecision sums exact certificate and growth" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   allocation_gate(BigFloat,:rows,:A,64,:dense,:positive,true,8)
   allocation_gate(BigFloat,:feasible,:A,64,:dense,:positive,true,8)
   allocation_gate(Rational{BigInt},:cert,:B,16,:dense,:wide,true,8)
   allocation_gate(Rational{BigInt},:cert,:B,16,:dense,:wide,false,8)
   allocation_gate(BigFloat,:growth,:C,8,:dense,:positive,true,8)
   allocation_gate(BigFloat,:refresh,:C,8,:dense,:positive,true,8)
   allocation_gate(BigFloat,:scheduled,:C,8,:dense,:positive,true,8)
  end
 end
end
end
