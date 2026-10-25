module GenericUnitCostTests
using Test,JSimplex,SparseArrays,LinearAlgebra
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
# Frozen baseline algorithms provide an independent pre-optimization reference.
module Reference
using JSimplex,SparseArrays
using JSimplex: _refined_primal_rows_feasible
using JSimplex: Bound,bound_value,LinearProblem,SimplexWorkspace,_is_exact,_primal_nearest_rounding,_primal_sum_bounds,_primal_difference_bounds,_unbounded_bound,_dual_pivot_cutoff,_dual_pivot_eligible
function _primal_product_bounds(left::T, right::T) where {T<:AbstractFloat}
    (iszero(left) || iszero(right)) && return zero(T), zero(T)
    left == one(T) && return right, right
    right == one(T) && return left, left
    left == -one(T) && precision(right) == precision(T) && return -right, -right
    right == -one(T) && precision(left) == precision(T) && return -left, -left
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

function _original_costs_active(ws::SimplexWorkspace{T}) where T
    ws.perturbed && return false
    n = length(ws.problem.objective)
    for j in eachindex(ws.costs)
        ws.costs[j] == (j <= n ? ws.problem.objective[j] : zero(T)) || return false
    end
    return true
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
                        ifelse(coefficient < zero(T), -tolerance, tolerance)) / coefficient
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
@noinline product(::Val{:original},a,b)=Reference._primal_product_bounds(a,b)
@noinline product(::Val{:candidate},a,b)=JSimplex._primal_product_bounds(a,b)
@noinline feasible(::Val{:original},p,x,t)=Reference._original_primal_feasible(p,x,t)
@noinline feasible(::Val{:candidate},p,x,t)=JSimplex._original_primal_feasible(p,x,t)
@noinline active(::Val{:original},ws)=Reference._original_costs_active(ws)
@noinline active(::Val{:candidate},ws)=JSimplex._original_costs_active(ws)
function snap(a)
    (a,map(copy,a),deepcopy(a))
end
function intact(a,s)
    all(a[k]===s[1][k]&&axes(a[k])==axes(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
end
function parrays(p,x)
    (p.A.nzval,p.A.rowval,p.A.colptr,p.objective,p.column_lower,p.column_upper,p.row_lower,p.row_upper,x)
end
function warrays(ws)
    (parrays(ws.problem,ws.primal)...,ws.costs,ws.reduced_costs,ws.lower,ws.upper,ws.pricing_weights,ws.basis.basic_indices,ws.basis.states)
end
function operands(::Type{T}) where T
    a=T[0,-zero(T),1,-1,T(3//7),T(-7//3)]
    if T<:AbstractFloat;append!(a,T[Inf,-Inf,NaN,prevfloat(one(T)),nextfloat(one(T))]);end
    a
end
function correctness(::Type{T}) where T
    @testset "Unit interval and cost equality $T" begin
        for stored in (T===BigFloat ? (precision(BigFloat),512) : (0,))
            v=T===BigFloat ? setprecision(()->operands(T),BigFloat,stored) : operands(T)
            for a in v,b in v
                s=deepcopy((a,b));left=product(Val(:original),a,b);right=product(Val(:candidate),a,b)
                @test same(left,right)
                @test same((a,b),s)
                @test (left[1]===a,left[1]===b,left[2]===a,left[2]===b)==(right[1]===a,right[1]===b,right[2]===a,right[2]===b)
            end
        end
        ws=costfixture(T,8);saved=snap(warrays(ws))
        @test active(Val(:original),ws)===active(Val(:candidate),ws)===true
        @test intact(warrays(ws),saved)
        for at in (1,length(ws.problem.objective)+1,length(ws.costs))
            old=ws.costs[at];ws.costs[at]=one(T)
            for value in (one(T),-one(T),T<:AbstractFloat ? T(NaN) : T(1,0))
                ws.costs[at]=value;s=snap(warrays(ws))
                @test active(Val(:original),ws)===active(Val(:candidate),ws)===false
                @test intact(warrays(ws),s)
            end
            ws.costs[at]=old
        end
        ws.perturbed=true
        @test active(Val(:original),ws)===active(Val(:candidate),ws)===false
        ws.perturbed=false
        for j in (length(ws.problem.objective)+1):length(ws.costs);ws.costs[j]=-zero(T);end
        @test active(Val(:original),ws)===active(Val(:candidate),ws)===true
        p,x,t=problemfixture(T,8,:mixed,:dense);saved=snap(parrays(p,x))
        @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===true
        @test intact(parrays(p,x),saved)
        x[1]=T(2^20);s=snap(parrays(p,x))
        @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===false
        @test intact(parrays(p,x),s)
        fill!(x,T(1//2));fill!(p.row_lower,JSimplex.Bound(zero(T)));fill!(p.row_upper,JSimplex.Bound(zero(T)));s=snap(parrays(p,x))
        @test feasible(Val(:original),p,x,t)===feasible(Val(:candidate),p,x,t)===false
        @test intact(parrays(p,x),s)
    end
end
function costfixture(::Type{T},m) where T
    p=LinearProblem(spzeros(T,m,4),zeros(T,4);row_lower=zeros(T,m),column_lower=zeros(T,4))
    policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
    JSimplex._initialize_workspace_state(p,SolverOptions(T;algorithm=:dual,basis_refactorization=:markowitz,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
end
function coeff(::Type{T},i,pattern) where T
    pattern===:positive ? one(T) : pattern===:negative ? -one(T) : i%3==0 ? -one(T) : i%3==1 ? one(T) : T(3//2)
end
function problemfixture(::Type{T},n,pattern,density) where T
    rows=Int[];cols=Int[];vals=T[];m=8
    for j in 1:n,i in 1:m
        if density===:dense||i==(j%8+1);push!(rows,i);push!(cols,j);push!(vals,coeff(T,i+j,pattern));end
    end
    p=LinearProblem(sparse(rows,cols,vals,m,n),zeros(T,n);row_lower=fill(T(-8192),m),row_upper=fill(T(8192),m),column_lower=fill(T(-4),n),column_upper=fill(T(4),n))
    p,fill(T(1//2),n),zero(T)
end
capture(f)=try (true,f()) catch e;(false,(string(typeof(e)),sprint(showerror,e))) end
@noinline select(::Val{:original},ws,row,o)=Reference.dual_ratio_test(ws,row,o)
@noinline select(::Val{:lazy},ws,row,o)=JSimplex.dual_ratio_test(ws,row,o)
function ratio_fixture(::Type{T},n,pattern,density,orientation;free=false,tolerance=nothing) where T
    desired=T[(density===:all||i%4==1) ? ((pattern===:negative||pattern===:mixed&&isodd(density===:few ? (i-1)÷4+1 : i)) ? -T((i%7+2)//8) : T((i%7+2)//8)) : zero(T) for i in 1:n]
    o=T(orientation);row=vcat(T[o*x for x in desired],T[1])
    prices=free ? zeros(T,n) : T[2*x for x in desired]
    A=sparse(ones(Int,n),collect(1:n),T[-x for x in row[1:n]],1,n)
    lower=free ? fill(nothing,n) : zeros(T,n)
    upper=free ? fill(nothing,n) : fill(T(16),n)
    p=LinearProblem(A,prices;row_lower=T[-2^30],row_upper=T[2^30],column_lower=lower,column_upper=upper)
    tol=isnothing(tolerance) ? (T<:Rational ? zero(T) : T(1//1000000)) : tolerance
    opts=SolverOptions(T;algorithm=:dual,pricing=:dantzig,basis_refactorization=:markowitz,
        primal_tolerance=T<:Rational ? zero(T) : T(1//1000000),dual_tolerance=tol,verbose=false)
    policy=JSimplex.NumericalPolicy(T;refactor_timing=false)
    ws=JSimplex._initialize_workspace_state(p,opts;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    for i in 1:n
        state=free ? JSimplex.FREE_NONBASIC : desired[i]<0 ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
        ws.basis.states[i]=state;ws.primal[i]=state==JSimplex.AT_UPPER ? T(16) : zero(T)
        ws.reduced_costs[i]=prices[i]
    end
    ws.primal[end]=only(A*view(ws.primal,1:n));ws.reduced_costs[end]=zero(T)
    ws,row,o
end
function ratio_arrays(ws,row)
    (row,ws.primal,ws.costs,ws.reduced_costs,ws.lower,ws.upper,ws.pricing_weights,
     ws.basis.basic_indices,ws.basis.states,ws.problem.A.nzval,ws.problem.A.rowval,ws.problem.A.colptr,
     ws.problem.objective,ws.problem.column_lower,ws.problem.column_upper,ws.problem.row_lower,ws.problem.row_upper,
     ws.scratch.rejected_rows,ws.scratch.rejected_entering)
end
ratio_snapshot(ws,row)=(ratio_arrays(ws,row),map(copy,ratio_arrays(ws,row)),deepcopy(ratio_arrays(ws,row)),ws.options,ws.options.dual_tolerance,deepcopy(ws.options.dual_tolerance))
function ratio_unchanged(ws,row,s)
    a=ratio_arrays(ws,row)
    ws.options===s[4]&&ws.options.dual_tolerance===s[5]&&same(ws.options.dual_tolerance,s[6])&&
    all(a[k]===s[1][k]&&length(a[k])==length(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
end
function ratio_compare(ws,row,o)
    saved=ratio_snapshot(ws,row);orientation_owner=o;orientation_value=deepcopy(o);owner=ws.scratch.candidates;bits=precision(BigFloat);mode=rounding(BigFloat)
    a=capture(()->select(Val(:original),ws,row,o));entries=copy(owner)
    b=capture(()->select(Val(:lazy),ws,row,o))
    @test same(a,b)
    @test ws.scratch.candidates==entries
    @test ratio_unchanged(ws,row,saved)&&o===orientation_owner&&same(o,orientation_value)
    @test ws.scratch.candidates===owner
    @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
    a
end
function ratio_correctness(::Type{T}) where T
    @testset "Whole ratio selection state exceptions and owners $T" begin
        for pattern in (:positive,:negative,:mixed),orientation in (1,-1)
            ws,row,o=ratio_fixture(T,32,pattern,:all,orientation)
            @test ratio_compare(ws,row,o)==(true,6)
            push!(ws.scratch.rejected_entering,6)
            @test ratio_compare(ws,row,o)==(true,13)
            original_row=copy(row);fill!(row,zero(T));row[end]=one(T)
            @test ratio_compare(ws,row,o)==(true,-1)
            copyto!(row,original_row);push!(row,one(T));@test ratio_compare(ws,row,o)[1]===false
        end
        for orientation in (1,-1)
            ws,row,o=ratio_fixture(T,32,:mixed,:all,orientation;free=true)
            @test ratio_compare(ws,row,o)==(true,6)
        end
        ws,row,o=ratio_fixture(T,32,:mixed,:all,1)
        ws.lower[6]=JSimplex.Bound(zero(T));ws.upper[6]=JSimplex.Bound(zero(T));ws.basis.states[6]=JSimplex.AT_LOWER;ws.primal[6]=zero(T)
        @test ratio_compare(ws,row,o)==(true,13)
        if T===BigFloat
            tol=setprecision(BigFloat,512) do;BigFloat(1)/1000000;end
            ws,row,o=ratio_fixture(T,32,:mixed,:all,1)
            options=ws.options
            ws.options=typeof(options)((name===:dual_tolerance ? tol : getfield(options,name) for name in fieldnames(typeof(options)))...)
            @test precision(ws.options.dual_tolerance)==512
            ratio_compare(ws,row,o)
        elseif T<:Rational
            ws,row,o=ratio_fixture(T,32,:mixed,:all,1;tolerance=T(1//1000000));ratio_compare(ws,row,o)
        end
        if T<:AbstractFloat
            for v in (T(NaN),T(Inf),T(-Inf),-zero(T))
                ws,row,o=ratio_fixture(T,32,:mixed,:all,1);row[2]=v;ratio_compare(ws,row,o)
            end
        end
    end
end
@noinline function batch(method::M,::Val{:product},v,calls) where M
    a,b=v;s=0
    for _ in 1:calls,i in eachindex(a);lo,hi=product(method,a[i],b[i]);s+=Int(isfinite(lo))+Int(isfinite(hi));end
    s
end
@noinline function batch(method::M,::Val{:feasible},v,calls) where M
    p,x,t=v;s=0
    for _ in 1:calls;s+=Int(feasible(method,p,x,t));end
    s
end
@noinline function batch(method::M,::Val{:cost},ws,calls) where M
    s=0
    for _ in 1:calls;s+=Int(active(method,ws));end
    s
end

@noinline ratio_batch(method::M,ws::W,row::X,o::T) where {M,W,X,T} = select(method,ws,row,o)+select(method,ws,row,o)
@noinline allocated_ratio(method::M,ws::W,row::X,o::T,sink) where {M,W,X,T} = @allocated sink[]=ratio_batch(method,ws,row,o)
@noinline allocated_batch(method::M,scope::S,v::V,sink) where {M,S,V} = @allocated sink[]=batch(method,scope,v,2)
function allocation_checks()
    @testset "Warmed temporary scalar allocation savings" begin
        setprecision(BigFloat,128) do
            setrounding(BigFloat,RoundNearest) do
                ws,row,o=ratio_fixture(BigFloat,128,:positive,:all,1);sink=Ref(0)
                for _ in 1:3,m in (Val(:original),Val(:lazy));allocated_ratio(m,ws,row,o,sink);end
                before=allocated_ratio(Val(:original),ws,row,o,sink);after=allocated_ratio(Val(:lazy),ws,row,o,sink)
                @test before>0
                @test after<before # RED lazy BigFloat ratio tolerance
                v=(fill(BigFloat(3//2),128),fill(BigFloat(1//2),128))
                for _ in 1:3,m in (Val(:original),Val(:candidate));allocated_batch(m,Val(:product),v,sink);end
                before=allocated_batch(Val(:original),Val(:product),v,sink);after=allocated_batch(Val(:candidate),Val(:product),v,sink)
                @test before>0
                @test after<before # RED BigFloat product unit comparisons
            end
        end
        for T in (BigFloat,Rational{BigInt})
            ws=costfixture(T,128);sink=Ref(0)
            for _ in 1:3,m in (Val(:original),Val(:candidate));allocated_batch(m,Val(:cost),ws,sink);end
            before=allocated_batch(Val(:original),Val(:cost),ws,sink);after=allocated_batch(Val(:candidate),Val(:cost),ws,sink)
            @test before>0
            @test after<before # RED slack zero creation (two types)
        end
    end
end
@testset "Generic unit cost and lazy ratio savings" begin
    for bits in (64,128,256),mode in MODES
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                correctness(BigFloat)
                ratio_correctness(BigFloat)
                @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
            end
        end
    end
    for T in (Rational{BigInt},Rational{Int64},Float32,Float64)
        correctness(T);ratio_correctness(T)
    end
    for T in (Float16,Float32,Float64,Rational{Int64}),a in T[0,1,-1,T(3//2)],b in T[0,1,-1,T(1//2)]
        @test same(product(Val(:original),a,b),product(Val(:candidate),a,b))
    end
    allocation_checks()
end
end
