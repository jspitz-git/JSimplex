module GenericLocalReuseTests
using Test,JSimplex,SparseArrays,LinearAlgebra
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
# Frozen pre-optimization reference; all tests exercise actual package candidates.
module Reference
using JSimplex,SparseArrays
using JSimplex: Bound,bound_value,LinearProblem,SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_is_exact,_is_fixed,_primal_nearest_rounding,_refined_primal_rows_feasible,_unbounded_bound,_dual_pivot_cutoff,_dual_pivot_eligible,_dual_ratio_tolerance
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

function dual_infeasibility_summary(workspace::SimplexWorkspace{T}) where {T}
    infeasibility = zero(T)
    count = 0
    tolerance = workspace.options.dual_tolerance
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue

        reduced_cost = workspace.reduced_costs[index]
        if state == AT_LOWER && reduced_cost < -tolerance
            infeasibility -= reduced_cost
            count += 1
        elseif state == AT_UPPER && reduced_cost > tolerance
            infeasibility += reduced_cost
            count += 1
        elseif state == FREE_NONBASIC && abs(reduced_cost) > tolerance
            infeasibility += abs(reduced_cost)
            count += 1
        end
    end
    return infeasibility, count
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


end
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::JSimplex.Bound,b::JSimplex.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
@noinline addbounds(::Val{:original},a,b)=Reference._primal_sum_bounds(a,b)
@noinline addbounds(::Val{:candidate},a,b)=JSimplex._primal_sum_bounds(a,b)
@noinline feasible(::Val{:original},p,x,t)=Reference._original_primal_feasible(p,x,t)
@noinline feasible(::Val{:candidate},p,x,t)=JSimplex._original_primal_feasible(p,x,t)
@noinline summary(::Val{:original},ws)=Reference.dual_infeasibility_summary(ws)
@noinline summary(::Val{:candidate},ws)=JSimplex.dual_infeasibility_summary(ws)
@noinline selectratio(::Val{:original},ws,row,o)=Reference.dual_ratio_test(ws,row,o)
@noinline selectratio(::Val{:candidate},ws,row,o)=JSimplex.dual_ratio_test(ws,row,o)
snap(a)=(a,map(copy,a),deepcopy(a))
function intact(a,s)
    all(a[k]===s[1][k]&&axes(a[k])==axes(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
end
parrays(p,x)=(p.A.nzval,p.A.rowval,p.A.colptr,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper,x)
warrays(ws)=(parrays(ws.problem,ws.primal)...,ws.costs,ws.reduced_costs,ws.lower,ws.upper,ws.pricing_weights,ws.basis.basic_indices,ws.basis.states)
function capture(f)
    try
        (:value,f())
    catch e
        (:error,typeof(e),sprint(showerror,e))
    end
end
function statefixture(::Type{T},n,m=0) where T
    p=LinearProblem(spzeros(T,m,n),zeros(T,n);row_lower=zeros(T,m),column_lower=zeros(T,n),column_upper=fill(T(2),n))
    policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
    JSimplex._initialize_workspace_state(p,SolverOptions(T;algorithm=:dual,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
end
function summaryfixture(::Type{T},n,pattern) where T
    ws=statefixture(T,n)
    for j in 1:n
        state=pattern===:lower_feasible||pattern===:lower_bad ? JSimplex.AT_LOWER : pattern===:upper_bad ? JSimplex.AT_UPPER : pattern===:free_bad ? JSimplex.FREE_NONBASIC : (JSimplex.AT_LOWER,JSimplex.AT_UPPER,JSimplex.FREE_NONBASIC,JSimplex.BASIC)[mod1(j,4)]
        ws.basis.states[j]=state
        state==JSimplex.FREE_NONBASIC&&(ws.lower[j]=JSimplex._unbounded_bound(T);ws.upper[j]=JSimplex._unbounded_bound(T))
        ws.reduced_costs[j]=pattern===:lower_feasible||state==JSimplex.AT_UPPER ? T(1//4) : state==JSimplex.BASIC ? zero(T) : -T(1//4)
    end
    ws
end
function ratiofixture(::Type{T},n,pattern) where T
    ws=statefixture(T,n,1);fill!(ws.reduced_costs,zero(T))
    row=T[pattern===:increasing ? j : pattern===:decreasing ? n+1-j : 1 for j in 1:n]
    push!(row,zero(T))
    ws,row,one(T)
end
function operands(::Type{T}) where T
    a=T[0,-zero(T),1,-1,T(3//7),T(-7//3),T(1//2),T(-1//2)]
    if T<:AbstractFloat
        append!(a,T[Inf,-Inf,NaN,prevfloat(one(T)),nextfloat(one(T)),nextfloat(zero(T))])
        T===BigFloat&&append!(a,[ldexp(one(T),1000),ldexp(one(T),-1000)])
    end
    a
end
function problemfixture(::Type{T},n,pattern,density) where T
    rows=Int[];cols=Int[];vals=T[];m=8
    for j in 1:n,i in 1:m
        if density===:dense||i==(j%8+1)
            v=T((5+mod(i+j,7))//8)
            pattern===:negative ? (v=-v) : pattern===:mixed&&isodd(i+j) ? (v=-v) : nothing
            push!(rows,i);push!(cols,j);push!(vals,v)
        end
    end
    p=LinearProblem(sparse(rows,cols,vals,m,n),zeros(T,n);row_lower=fill(T(-8192),m),row_upper=fill(T(8192),m),column_lower=fill(T(-4),n),column_upper=fill(T(4),n))
    p,fill(T(1//2),n),zero(T)
end
function correctness(::Type{T}) where T
    @testset "Local reuse values and owners $T" begin
        for stored in (T===BigFloat ? (precision(BigFloat),512) : (0,))
            v=T===BigFloat ? setprecision(()->operands(T),BigFloat,stored) : operands(T)
            for a in v,b in v
                saved=deepcopy((a,b));l=capture(()->addbounds(Val(:original),a,b));r=capture(()->addbounds(Val(:candidate),a,b))
                @test same(l,r)
                @test same((a,b),saved)
                if l[1]===:value
                    x,y=l[2],r[2]
                    @test (x[1]===a,x[1]===b,x[2]===a,x[2]===b)==(y[1]===a,y[1]===b,y[2]===a,y[2]===b)
                end
            end
        end
        for pattern in (:lower_feasible,:lower_bad,:upper_bad,:free_bad,:mixed)
            ws=summaryfixture(T,8,pattern);saved=snap(warrays(ws));l=summary(Val(:original),ws);r=summary(Val(:candidate),ws)
            @test same(l,r)
            want=pattern===:lower_feasible ? (zero(T),0) : pattern===:mixed ? (T(3//2),6) : (T(2),8)
            @test same(r,want)
            @test intact(warrays(ws),saved)
            ws.reduced_costs[1]=zero(T)
            @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
            ws.options=SolverOptions(T;algorithm=:dual,verbose=false,dual_tolerance=T(1//2))
            @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
            @test same(summary(Val(:candidate),ws),(zero(T),0))
        end
        for n in (0,1),pattern in (:lower_feasible,:lower_bad,:upper_bad,:free_bad,:mixed)
            ws=summaryfixture(T,n,pattern)
            @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
        end
        ws=summaryfixture(T,8,:lower_bad)
        for j in eachindex(ws.basis.states);ws.basis.states[j]=JSimplex.BASIC;end
        @test same(summary(Val(:candidate),ws),(zero(T),0))
        fill!(ws.basis.states,JSimplex.AT_LOWER)
        for j in eachindex(ws.lower);ws.upper[j]=ws.lower[j];end
        @test same(summary(Val(:candidate),ws),(zero(T),0))
        for x in operands(T),state in (JSimplex.AT_LOWER,JSimplex.AT_UPPER,JSimplex.FREE_NONBASIC)
            ws=summaryfixture(T,1,:free_bad);ws.basis.states[1]=state;ws.reduced_costs[1]=x;saved=snap(warrays(ws))
            @test same(capture(()->summary(Val(:original),ws)),capture(()->summary(Val(:candidate),ws)))
            @test intact(warrays(ws),saved)
        end
        if T===BigFloat
            ws=summaryfixture(T,8,:mixed)
            for j in 1:8;ws.reduced_costs[j]=setprecision(()->BigFloat((-1)^j//7),BigFloat,512);end
            @test same(summary(Val(:original),ws),summary(Val(:candidate),ws))
        end
        for pattern in (:increasing,:decreasing,:tied),n in (0,1,8)
            ws,row,o=ratiofixture(T,n,pattern);saved=snap((warrays(ws)...,row))
            want=n==0 ? -1 : pattern===:increasing ? n : 1
            @test selectratio(Val(:original),ws,row,o)==selectratio(Val(:candidate),ws,row,o)==want
            @test ws.scratch.candidates==collect(1:n)
            @test intact((warrays(ws)...,row),saved)
            if n>0
                push!(ws.scratch.rejected_entering,want)
                @test selectratio(Val(:original),ws,row,o)==selectratio(Val(:candidate),ws,row,o)
                empty!(ws.scratch.rejected_entering)
                row[1]=-row[1]
                @test selectratio(Val(:original),ws,row,o)==selectratio(Val(:candidate),ws,row,o)
                @test selectratio(Val(:original),ws,row,-o)==selectratio(Val(:candidate),ws,row,-o)
            end
        end
        for x in operands(T)
            ws,row,o=ratiofixture(T,4,:increasing);row[1]=x
            l=capture(()->selectratio(Val(:original),ws,row,o));left=copy(ws.scratch.candidates)
            r=capture(()->selectratio(Val(:candidate),ws,row,o))
            @test same(l,r)
            @test ws.scratch.candidates==left
        end
        ws,row,o=ratiofixture(T,4,:tied);ws.reduced_costs[2]=one(T)
        @test selectratio(Val(:original),ws,row,o)==selectratio(Val(:candidate),ws,row,o)==1
        push!(row,one(T));l=capture(()->selectratio(Val(:original),ws,row,o));left=copy(ws.scratch.candidates)
        r=capture(()->selectratio(Val(:candidate),ws,row,o))
        @test same(l,r)
        @test ws.scratch.candidates==left
        for density in (:sparse,:dense),pattern in (:positive,:negative,:mixed)
            p,x,t=problemfixture(T,8,pattern,density);saved=snap(parrays(p,x))
            @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===true
            @test intact(parrays(p,x),saved)
            x[1]=T(2^20);saved=snap(parrays(p,x))
            @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===false
            @test intact(parrays(p,x),saved)
            fill!(x,T(1//2));fill!(p.row_lower,JSimplex.Bound(zero(T)));fill!(p.row_upper,JSimplex.Bound(zero(T)));saved=snap(parrays(p,x))
            @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===false
            @test intact(parrays(p,x),saved)
        end
    end
end
@noinline function batch(method::M,::Val{:sum},v,calls) where M
    a,b=v;s=0
    for _ in 1:calls,i in eachindex(a);lo,hi=addbounds(method,a[i],b[i]);s+=Int(isfinite(lo))+Int(isfinite(hi));end
    s
end
@noinline function batch(method::M,::Val{:feasible},v,calls) where M
    p,x,t=v;s=0
    for _ in 1:calls;s+=Int(feasible(method,p,x,t));end
    s
end
@noinline function batch(method::M,::Val{:summary},ws,calls) where M
    s=0
    for _ in 1:calls;v,n=summary(method,ws);s+=n+Int(isfinite(v));end
    s
end
@noinline function batch(method::M,::Val{:ratio},v,calls) where M
    ws,row,o=v;s=0
    for _ in 1:calls;s+=selectratio(method,ws,row,o);end
    s
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
    @test 10*after.events<9*before.events && after.bytes<before.bytes # RED costgate (six reached cases)
end
@testset "Generic local reuse" begin
    for bits in (64,128,256),mode in MODES
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                correctness(BigFloat)
                # Rows/options retain higher-precision owners across a smaller ambient call.
                ws,row,o=ratiofixture(BigFloat,8,:increasing)
                for j in eachindex(row)
                    row[j]=setprecision(BigFloat,512) do
                        BigFloat(j)/BigFloat(7)
                    end
                end
                saved=snap((warrays(ws)...,row))
                @test selectratio(Val(:original),ws,row,o)==selectratio(Val(:candidate),ws,row,o)
                @test intact((warrays(ws)...,row),saved)
                @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
            end
        end
    end
    for T in (Rational{BigInt},Rational{Int64},Float32,Float64);correctness(T);end
    for T in (Float16,Float32,Float64,Rational{Int64}),a in T[0,1,-1,T(3//2)],b in T[0,1,-1,T(1//2)]
        @test same(addbounds(Val(:original),a,b),addbounds(Val(:candidate),a,b))
    end
    @testset "Warm whole-call allocation savings" begin
        setprecision(BigFloat,128) do
            setrounding(BigFloat,RoundNearest) do
                cost_pair(Val(:sum),(fill(BigFloat(3//2),128),fill(BigFloat(1//2),128)))
            end
        end
        for pattern in (:lower_feasible,:free_bad),T in (BigFloat,Rational{BigInt})
            cost_pair(Val(:summary),summaryfixture(T,128,pattern))
        end
        setprecision(BigFloat,128) do
            setrounding(BigFloat,RoundNearest) do
                cost_pair(Val(:ratio),ratiofixture(BigFloat,128,:increasing))
            end
        end
        # Hardware generics must keep zero allocation traffic.
        for T in (Float32,Float64)
            sink=Ref(0);v=summaryfixture(T,128,:lower_bad)
            for _ in 1:3,method in (Val(:original),Val(:candidate));allocation_cost(method,Val(:summary),v,sink);end
            before=allocation_cost(Val(:original),Val(:summary),v,sink);after=allocation_cost(Val(:candidate),Val(:summary),v,sink)
            @test before.bytes==after.bytes==before.events==after.events==0
        end
    end
end
end
