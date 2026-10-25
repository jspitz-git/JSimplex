module GenericPoolBoundTests
using Test,JSimplex,SparseArrays,LinearAlgebra
# Frozen pre-change algorithms are test-local references, not production overrides.
module Reference
using JSimplex
using JSimplex: CandidatePool,_pool_dual_violation,_effective_pricing,_primal_dantzig_score,_dual_pricing_score,
    _prepare_auto_pricing!,_primal_initialize_steepest!,_pool_primal_eligible,_pool_primal_score
_supported_value_type(::Type{T}) where {T} =
    isconcretetype(T) && (T <: AbstractFloat || T <: Rational)

_is_exact(::Type{<:Rational}) = Val(true)
_is_exact(::Type{<:AbstractFloat}) = Val(false)

_typed_ratio(::Type{T}, numerator::Integer, denominator::Integer) where {T<:Real} =
    T(numerator // denominator)

struct Bound{T<:Real}
    value::T
    bounded::Bool

    function Bound{T}(value::T, bounded::Bool) where {T<:Real}
        bounded && !isfinite(value) &&
            throw(ArgumentError("a finite bound must contain a finite value"))
        return new{T}(bounded ? value : zero(T), bounded)
    end
end

Bound(value::T) where {T<:Real} = Bound{T}(value, true)
Bound{T}(value::Real) where {T<:Real} = Bound{T}(T(value), true)
Bound{T}(::Nothing) where {T<:Real} = Bound{T}(zero(T), false)

_finite_bound(::Type{T}, value) where {T<:Real} = Bound{T}(T(value), true)
_unbounded_bound(::Type{T}) where {T<:Real} = Bound{T}(zero(T), false)

Base.isfinite(bound::Bound) = bound.bounded
Base.:(==)(left::Bound, right::Bound) =
    left.bounded == right.bounded && (!left.bounded || left.value == right.value)
Base.isequal(left::Bound, right::Bound) =
    left.bounded == right.bounded && (!left.bounded || isequal(left.value, right.value))
Base.hash(bound::Bound, seed::UInt) =
    bound.bounded ? hash(bound.value, hash(true, hash(:Bound, seed))) :
                    hash(false, hash(:Bound, seed))

function bound_value(bound::Bound)
    isfinite(bound) || throw(ArgumentError("an unbounded bound has no finite value"))
    return bound.value
end

function _normalize_bound(::Type{T}, input, side::Symbol, label::AbstractString) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported value type for $label: $T"))
    input isa Bound && !isfinite(input) && return _unbounded_bound(T)
    input === nothing && return _unbounded_bound(T)
    input isa Bound && return _finite_bound(T, bound_value(input))

    input isa Real || throw(ArgumentError("$label must be a real value or nothing"))
    if isnan(input)
        throw(ArgumentError("$label cannot be NaN"))
    elseif isinf(input)
        if input > 0
            side === :upper || throw(ArgumentError("$label cannot be +Inf"))
        else
            side === :lower || throw(ArgumentError("$label cannot be -Inf"))
        end
        return _unbounded_bound(T)
    end
    return _finite_bound(T, input)
end
function pool_best!(pool,eligible,score,initial,accept_first)
    best,best_score,kept = 0,initial,0
    for index in pool.indices
        eligible(index) || continue
        kept += 1
        pool.indices[kept] = index
        value = score(index)
        pool.scored_entries += 1
        if (accept_first && best == 0) || value > best_score ||
           (best != 0 && value == best_score && index < best)
            best,best_score = index,value
        end
    end
    resize!(pool.indices,kept)
    return best
end

function select_pool!(pool,count,eligible,score,initial,accept_first;force_full=false)
    pool.passes += 1
    pool.full_scan = false
    force_full = force_full || !pool.valid
    if force_full
        empty!(pool.indices)
        pool.scan_position = 1
        pool.valid = true
    else
        best = pool_best!(pool,eligible,score,initial,accept_first)
        best != 0 && return best
        empty!(pool.indices)
    end
    # Every exhaustion checks the entire current domain, including blocks seen
    # before a pivot. An old empty block is never an optimality certificate.
    visited = 0
    cursor = clamp(pool.scan_position,1,max(1,count))
    while visited < count
        take = min(pool.block_size,count-visited)
        for _ in 1:take
            eligible(cursor) && push!(pool.indices,cursor)
            cursor = cursor == count ? 1 : cursor+1
        end
        pool.block_scans += 1
        visited += take
        pool.scanned_entries += take
        pool.scan_position = cursor
        if visited == count
            pool.full_scan = true
            pool.full_scans += 1
        end
        if !force_full || pool.full_scan
            best = pool_best!(pool,eligible,score,initial,accept_first)
            best != 0 && return best
        end
    end
    if count == 0
        pool.full_scan = true
        pool.full_scans += 1
    end
    return 0
end

function select_dual_pool!(ws,pool,scoring::Val{S};force_full=false) where S
    T = eltype(ws.costs)
    weighted = _effective_pricing(ws,:dual) != :dantzig
    initial = S === :scaled ? _primal_dantzig_score(one(T)) : zero(S)
    eligible = row -> !(row in ws.scratch.rejected_rows) &&
                      _pool_dual_violation(ws,row) > ws.options.primal_tolerance
    score = row -> _dual_pricing_score(_pool_dual_violation(ws,row),
        ws.pricing_weights[ws.basis.basic_indices[row]],weighted,scoring)
    return select_pool!(pool,length(ws.basis.basic_indices),eligible,score,
                         initial,S === :scaled;force_full)
end

"""Select a current candidate; zero requires a complete scan during this call."""
function select_candidate!(ws,pool::CandidatePool,policy;
                                   force_full::Bool=false,
                                   tolerance=ws.options.dual_tolerance)::Int
    force_full = force_full || !policy.partial_pricing
    T = eltype(ws.costs)
    _prepare_auto_pricing!(ws,pool.algorithm)
    if pool.algorithm == :primal
        pricing = _effective_pricing(ws,:primal)
        pricing == :steepest_edge && _primal_initialize_steepest!(ws)
        eligible = index -> _pool_primal_eligible(ws,index,tolerance)
        score = index -> _pool_primal_score(ws,index,pricing)
        return select_pool!(pool,length(ws.basis.states),eligible,score,
                             _primal_dantzig_score(one(T)),true;force_full)
    end
    if ws.options.pricing == :auto && T <: Rational
        return select_dual_pool!(ws,pool,Val(Rational{BigInt});force_full)
    elseif ws.options.pricing == :auto
        return select_dual_pool!(ws,pool,Val(:scaled);force_full)
    end
    return select_dual_pool!(ws,pool,Val(T);force_full)
end

function direction_weight(direction::AbstractVector{T}) where {T<:AbstractFloat}
    scale = one(T)
    for coefficient in direction
        scale = max(scale, abs(coefficient))
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

end
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a,b)=isequal(a,b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
function bound_same(a,b)
    a.bounded==b.bounded&&same(a.value,b.value)
end
function capture(f)
    try (true,f()) catch e;(false,(string(typeof(e)),sprint(showerror,e))) end
end
@noinline bound_make(::Val{:original},::Val{:constructor},::Type{T},x) where T=Reference.Bound{T}(nothing)
@noinline bound_make(::Val{:candidate},::Val{:constructor},::Type{T},x) where T=JSimplex.Bound{T}(nothing)
@noinline bound_make(::Val{:original},::Val{:helper},::Type{T},x) where T=Reference._unbounded_bound(T)
@noinline bound_make(::Val{:candidate},::Val{:helper},::Type{T},x) where T=JSimplex._unbounded_bound(T)
@noinline bound_make(::Val{:original},::Val{:normalize},::Type{T},x) where T=Reference._normalize_bound(T,x,:upper,"probe")
@noinline bound_make(::Val{:candidate},::Val{:normalize},::Type{T},x) where T=JSimplex._normalize_bound(T,x,:upper,"probe")
@noinline build_bounds(method::M,::Type{T},inputs) where {M,T}=[bound_make(method,Val(:normalize),T,x) for x in inputs]
@noinline pool_select(::Val{:original},ws,pool,policy,full)=Reference.select_candidate!(ws,pool,policy;force_full=full)
@noinline pool_select(::Val{:candidate},ws,pool,policy,full)=JSimplex.select_pricing_candidate!(ws,pool,policy;force_full=full)
function fixture(::Type{T},n,density,pricing) where T
    coeffs=T[(density===:all || i%4==1) ? -T((16+i%7)//16)*T(2^(i%3)) : one(T) for i in 1:n]
    p=LinearProblem(sparse(collect(1:n),ones(Int,n),coeffs,n,1),T[0];row_lower=zeros(T,n),row_upper=fill(T(16),n),column_lower=T[0])
    opts=SolverOptions(T;algorithm=:dual,pricing,partial_pricing=true,basis_refactorization=:markowitz,verbose=false)
    policy=JSimplex.NumericalPolicy(T;partial_pricing=true,refactor_timing=false)
    ws=JSimplex._initialize_workspace_state(p,opts;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.primal[1]=one(T);copyto!(ws.primal,2,coeffs,1,n)
    if pricing===:auto
        state=JSimplex.PricingState(T);state.algorithm=:dual;state.active=state.return_mode=:steepest_edge
        ws.scratch.pricing=state
    end
    ws,policy
end
function arrays(ws)
    (ws.primal,ws.costs,ws.reduced_costs,ws.pricing_weights,ws.lower,ws.upper,ws.basis.basic_indices,ws.basis.states,
     ws.problem.A.nzval,ws.problem.A.rowval,ws.problem.A.colptr,ws.scratch.rejected_rows,ws.scratch.rejected_entering)
end
same(a::JSimplex.Bound,b::JSimplex.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
snapshot(ws)=(arrays(ws),map(copy,arrays(ws)),deepcopy(arrays(ws)))
function unchanged(ws,s)
    a=arrays(ws)
    all(a[k]===s[1][k]&&length(a[k])==length(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
end
pool_state(pool)=Tuple(deepcopy(getfield(pool,k)) for k in fieldnames(typeof(pool)))
function pool_pair(ws)
    rows=[i for i in eachindex(ws.basis.basic_indices) if !(i in ws.scratch.rejected_rows)&&JSimplex._pool_dual_violation(ws,i)>ws.options.primal_tolerance]
    a=JSimplex.CandidatePool(;algorithm=:dual);b=JSimplex.CandidatePool(;algorithm=:dual)
    append!(a.indices,rows);append!(b.indices,rows)
    a,b
end
function correctness(::Type{T}) where T
    @testset "Unbounded constructors and normalization" begin
        for scope in (:constructor,:helper),_ in 1:2
            a=bound_make(Val(:original),Val(scope),T,nothing);b=bound_make(Val(:candidate),Val(scope),T,nothing)
            @test bound_same(a,b)
            @test capture(()->Reference.bound_value(a))==capture(()->JSimplex.bound_value(b))
            c=bound_make(Val(:candidate),Val(scope),T,nothing)
            @test T in (BigFloat,Rational{BigInt}) ? b.value !== c.value : isequal(b.value,c.value)
            @test T===Rational{BigInt} ? numerator(b.value)!==numerator(c.value)&&denominator(b.value)!==denominator(c.value) : true
        end
        positive_infinity=T<:Rational ? T(1,0) : T(Inf)
        for x in (nothing,positive_infinity,zero(T),one(T),-one(T),T(3//7))
            a=bound_make(Val(:original),Val(:normalize),T,x);b=bound_make(Val(:candidate),Val(:normalize),T,x)
            @test bound_same(a,b)
            @test isfinite(a)==isfinite(b)
        end
        for x in (-positive_infinity,)
            @test capture(()->bound_make(Val(:original),Val(:normalize),T,x))==capture(()->bound_make(Val(:candidate),Val(:normalize),T,x))
        end
        if T<:AbstractFloat
            @test capture(()->bound_make(Val(:original),Val(:normalize),T,T(NaN)))==capture(()->bound_make(Val(:candidate),Val(:normalize),T,T(NaN)))
        end
        input=one(T);saved=deepcopy(input)
        a=Reference.Bound{T}(input,false);b=JSimplex.Bound{T}(input,false)
        @test bound_same(a,b)
        @test same(input,saved)
        @test T in (BigFloat,Rational{BigInt}) ? a.value!==input&&b.value!==input : true
    end
    @testset "Unbounded false constructor discards arbitrary input" begin
        inf=T<:Rational ? T(1,0) : T(Inf)
        values=T[zero(T),-zero(T),one(T),inf,-inf]
        T<:AbstractFloat && push!(values,T(NaN))
        for input in values
            saved=deepcopy(input)
            a=Reference.Bound{T}(input,false);b=JSimplex.Bound{T}(input,false)
            @test bound_same(a,b)
            @test same(input,saved)
            @test !(T in (BigFloat,Rational{BigInt})) || b.value!==input
        end
    end
    @testset "Pool state transitions ties rejection invalidation" begin
        for pricing in (:dantzig,:auto),density in (:few,:all)
            ws,policy=fixture(T,129,density,pricing);a,b=pool_pair(ws)
            for full in (false,true,false)
                saved=snapshot(ws)
                @test pool_select(Val(:original),ws,a,policy,full)==pool_select(Val(:candidate),ws,b,policy,full)
                @test pool_state(a)==pool_state(b)
                @test unchanged(ws,saved)
            end
            ws.primal[2]=ws.primal[3]=-T(8)
            for p in (a,b);p.valid=false;empty!(p.indices);end
            @test pool_select(Val(:original),ws,a,policy,true)==pool_select(Val(:candidate),ws,b,policy,true)==1
            @test pool_state(a)==pool_state(b)
            push!(ws.scratch.rejected_rows,1)
            @test pool_select(Val(:original),ws,a,policy,true)==pool_select(Val(:candidate),ws,b,policy,true)==2
            @test pool_state(a)==pool_state(b)
            empty!(ws.scratch.rejected_rows);fill!(@view(ws.primal[2:end]),zero(T))
            @test pool_select(Val(:original),ws,a,policy,false)==pool_select(Val(:candidate),ws,b,policy,false)==0
            @test pool_state(a)==pool_state(b)&&a.full_scan
        end
        a=JSimplex.CandidatePool();b=JSimplex.CandidatePool();append!(a.indices,[2,1]);append!(b.indices,[2,1])
        fail(i)=throw(ArgumentError("score sentinel"))
        @test capture(()->Reference.pool_best!(a,i->i==1,fail,zero(T),false))==capture(()->JSimplex._pool_best!(b,i->i==1,fail,zero(T),false))
        @test pool_state(a)==pool_state(b)
        @test capture(()->Reference.pool_best!(a,i->1,identity,zero(T),false))==capture(()->JSimplex._pool_best!(b,i->1,identity,zero(T),false))
        @test capture(()->Reference.pool_best!(a,i->nothing,identity,zero(T),false))==capture(()->JSimplex._pool_best!(b,i->nothing,identity,zero(T),false))
    end
end
aliases(a::BigFloat,input)=Tuple(a===x for x in input)
aliases(a::Tuple,input)=map(x->aliases(x,input),a)
aliases(a,input)=nothing
function norm_inputs(stored)
    setprecision(BigFloat,stored) do
        z=zero(BigFloat);o=one(BigFloat);q=BigFloat(3)/7
        [BigFloat[],BigFloat[z],BigFloat[-z],BigFloat[o],BigFloat[-o],
         BigFloat[q,2q,3q],BigFloat[-q,-2q,-3q],BigFloat[q,-2q,3q],
         BigFloat[z,q,z,-q,z],BigFloat[Inf,o],BigFloat[-Inf,-o],BigFloat[NaN,q],
         BigFloat[ldexp(q,-10000),ldexp(-q,10000),nextfloat(o),prevfloat(o)]]
    end
end
function norm_correctness()
    @testset "Whole norm equivalence input owners and context" begin
        for stored in (64,128,256,512)
            vectors=norm_inputs(stored)
            for bits in (64,128,256),mode in MODES
                setprecision(BigFloat,bits) do
                    setrounding(BigFloat,mode) do
                        for x in vectors
                            saved=(x,copy(x),deepcopy(x))
                            a=capture(()->Reference.direction_weight(x))
                            b=capture(()->JSimplex._primal_direction_weight(x))
                            @test same(a,b)
                            @test aliases(a,x)==aliases(b,x)
                            @test x===saved[1]&&length(x)==length(saved[2])&&all(x[i]===saved[2][i]&&same(x[i],saved[3][i]) for i in eachindex(x))
                            @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
                        end
                    end
                end
            end
        end
    end
end
@noinline function batch_pool(method::M,ws::W,pool::P,policy::Y,full,calls) where {M,W,P,Y}
    sink=0
    for _ in 1:calls;sink+=pool_select(method,ws,pool,policy,full);end
    sink
end
@noinline function batch_bound(method::M,scope::S,::Type{T},inputs,calls) where {M,S,T}
    sink=0
    for _ in 1:calls
        if scope===Val(:vector)
            values=build_bounds(method,T,inputs)
            for b in values;sink+=Int(isfinite(b))+Int(iszero(b.value));end
        else
            for x in inputs
                b=bound_make(method,scope,T,x);sink+=Int(isfinite(b))+Int(iszero(b.value))
            end
        end
    end
    sink
end

# Consume results through typed helpers; compilation is warmed outside allocation checks.
@noinline function norm_batch(::Val{:original},x,calls)
    sink=0
    for _ in 1:calls
        (e,m),w=Reference.direction_weight(x);sink=xor(sink,e)+Int(isfinite(m))+Int(isfinite(w))
    end
    sink
end
@noinline function norm_batch(::Val{:candidate},x,calls)
    sink=0
    for _ in 1:calls
        (e,m),w=JSimplex._primal_direction_weight(x);sink=xor(sink,e)+Int(isfinite(m))+Int(isfinite(w))
    end
    sink
end
@noinline allocated_norm(v::V,x::X,sink) where {V,X} = @allocated sink[]=norm_batch(v,x,4)
@noinline allocated_bound(v::V,scope::S,::Type{T},inputs,sink) where {V,S,T} = @allocated sink[]=batch_bound(v,scope,T,inputs,4)
@noinline allocated_pool(v::V,ws::W,p::P,policy::Y,full,sink) where {V,W,P,Y} = @allocated sink[]=batch_pool(v,ws,p,policy,full,2)
function allocation_checks()
    @testset "Whole-call warmed allocation savings" begin
        setprecision(BigFloat,128) do
            x=BigFloat[1+i/256 for i in 1:256];sink=Ref(0)
            for _ in 1:3,v in (Val(:original),Val(:candidate));allocated_norm(v,x,sink);end
            before=allocated_norm(Val(:original),x,sink);after=allocated_norm(Val(:candidate),x,sink)
            @test before>0
            @test 10*after<9*before # RED norm allocation saving
        end
        for T in (BigFloat,Rational{BigInt}),scope in (:constructor,:helper)
            inputs=fill(nothing,32);sink=Ref(0)
            for _ in 1:3,v in (Val(:original),Val(:candidate));allocated_bound(v,Val(scope),T,inputs,sink);end
            before=allocated_bound(Val(:original),Val(scope),T,inputs,sink);after=allocated_bound(Val(:candidate),Val(scope),T,inputs,sink)
            @test before>0
            @test 10*after<9*before # RED bound allocation saving (four cases)
        end
        for T in (BigFloat,Rational{BigInt}),full in (false,true)
            ws,policy=fixture(T,129,:all,:dantzig);a,b=pool_pair(ws);sink=Ref(0)
            for _ in 1:3
                allocated_pool(Val(:original),ws,a,policy,full,sink);allocated_pool(Val(:candidate),ws,b,policy,full,sink)
            end
            before=allocated_pool(Val(:original),ws,a,policy,full,sink);after=allocated_pool(Val(:candidate),ws,b,policy,full,sink)
            @test before>0
            @test 10*after<9*before # RED pool allocation saving (four cases)
        end
    end
    @testset "Hardware paths retain allocation costs" begin
        for T in (Float32,Float64)
            ws,policy=fixture(T,129,:all,:dantzig);a,b=pool_pair(ws);sink=Ref(0)
            for _ in 1:3
                allocated_pool(Val(:original),ws,a,policy,false,sink);allocated_pool(Val(:candidate),ws,b,policy,false,sink)
            end
            @test allocated_pool(Val(:candidate),ws,b,policy,false,sink)<=allocated_pool(Val(:original),ws,a,policy,false,sink)
            for scope in (:constructor,:helper)
                inputs=fill(nothing,32)
                for _ in 1:3,v in (Val(:original),Val(:candidate));allocated_bound(v,Val(scope),T,inputs,sink);end
                @test allocated_bound(Val(:candidate),Val(scope),T,inputs,sink)<=allocated_bound(Val(:original),Val(scope),T,inputs,sink)
            end
            x=T[1,2,3]
            for _ in 1:3,v in (Val(:original),Val(:candidate));allocated_norm(v,x,sink);end
            @test allocated_norm(Val(:candidate),x,sink)==allocated_norm(Val(:original),x,sink)
        end
    end
end
@testset "Generic pool bound direction savings" begin
    for bits in (64,128,256),mode in MODES
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,mode) do
                correctness(BigFloat)
            end
        end
    end
    for T in (Rational{BigInt},Rational{Int64},Float32,Float64);correctness(T);end
    norm_correctness()
    @testset "Generic direction and Float16 bound paths" begin
        for T in (Float16,Float32,Float64),x in (T[1,-2,0],T[0,-0.0])
            saved=copy(x)
            @test same(capture(()->Reference.direction_weight(x)),capture(()->JSimplex._primal_direction_weight(x)))
            @test isequal(x,saved)
        end
        for scope in (:constructor,:helper)
            a=bound_make(Val(:original),Val(scope),Float16,nothing);b=bound_make(Val(:candidate),Val(scope),Float16,nothing)
            @test bound_same(a,b)
            @test !isfinite(b)
        end
    end
    allocation_checks()
end
end
