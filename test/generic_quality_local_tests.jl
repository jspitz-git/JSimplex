module GenericQualityLocalTests
using Test,JSimplex,SparseArrays,LinearAlgebra
module LocalReference
using JSimplex,SparseArrays
using JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,
    _is_exact,_compensated_solve_quality!,_primal_direction_magnitude,
    _with_recovery_precision,_finite_workspace,_recomputed_basis_reliable,
    _primal_price_prediction_reliable,recompute!,_PriceAuditMatrix
function _componentwise_backward_error(residual::AbstractVector{T}, scale) where {T<:AbstractFloat}
    axes(residual) == axes(scale) || throw(DimensionMismatch("Residual and scale dimensions differ"))
    error = zero(T)
    for i in eachindex(residual,scale)
        r, s = abs(residual[i]), scale[i]
        isfinite(r) && isfinite(s) && s >= zero(s) || return T(Inf)
        ratio = iszero(s) ? (iszero(r) ? zero(T) : T(Inf)) : r/s
        error = max(error,ratio)
    end
    return error
end

_quality_values(B::AbstractMatrix) = B
_quality_values(B::SparseMatrixCSC) = nonzeros(B)

@inline function _accumulate_quality_term!(r::AbstractVector{W}, scale, terms,
                                          x, a, row, column, transposed) where {W}
    target, source = transposed ? (column,row) : (row,column)
    product = W(a)*W(x[source])
    r[target] -= product
    scale[target] += abs(product)
    terms[target] += 2
    return W <: AbstractFloat && !iszero(a) && !iszero(x[source]) &&
           abs(product) < floatmin(W)
end

function _quality_components!(r::AbstractVector{W}, scale, terms, B, x, rhs, transposed) where {W}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B.nzval[p],B.rowval[p],column,transposed)
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe_range |= _accumulate_quality_term!(r,scale,terms,x,B[row,column],row,column,transposed)
        end
    end
    return unsafe_range
end

# A call-local comparison limit is shared only across ordinary array accesses.
@inline function _bigfloat_quality_term!(r, scale, terms, x, a, row, column,
                                         transposed, limit::Union{Nothing,BigFloat})
    target, source = transposed ? (column,row) : (row,column)
    product = BigFloat(a)*BigFloat(x[source])
    r[target] -= product
    scale[target] += _primal_direction_magnitude(product)
    terms[target] += 2
    if !iszero(a) && !iszero(x[source])
        if limit === nothing
            limit = floatmin(BigFloat)
        end
        return _primal_direction_magnitude(product) < limit, limit
    end
    return false, limit
end

function _quality_components!(r::Vector{BigFloat}, scale::Vector{BigFloat},
                              terms::Vector{Int},
                              B::Union{Matrix{BigFloat},SparseMatrixCSC{BigFloat}},
                              x::Vector{BigFloat}, rhs::Vector{BigFloat}, transposed)
    for i in eachindex(rhs)
        r[i] = BigFloat(rhs[i])
        scale[i] = _primal_direction_magnitude(r[i])
        terms[i] = 1
    end
    unsafe_range = false
    limit::Union{Nothing,BigFloat} = nothing
    if B isa SparseMatrixCSC
        for column in axes(B,2), p in nzrange(B,column)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B.nzval[p],
                B.rowval[p],column,transposed,limit)
            unsafe_range |= unsafe
        end
    else
        for column in axes(B,2), row in axes(B,1)
            unsafe, limit = _bigfloat_quality_term!(r,scale,terms,x,B[row,column],
                row,column,transposed,limit)
            unsafe_range |= unsafe
        end
    end
    return unsafe_range
end

function _quality_roundoff(::Type{W}, terms) where {W<:AbstractFloat}
    k = maximum(terms; init=0)
    product = W(k)*eps(W)
    return isfinite(product) && product < one(W) ? product/(one(W)-product) : W(Inf)
end

function _floating_quality!(scratch::SolveQualityScratch{T}, r, scale, terms, policy) where {T}
    ratio = _componentwise_backward_error(r,scale)
    absolute = maximum(abs,r; init=zero(eltype(r)))
    for i in eachindex(r)
        scratch.residual[i] = convert(T,r[i])
    end
    absolute_T, ratio_T = convert(T,absolute), convert(T,ratio)
    iszero(absolute_T) && absolute > 0 && (absolute_T = nextfloat(zero(T)))
    finite = isfinite(absolute_T) && isfinite(ratio_T) && all(isfinite,scratch.residual)
    roundoff = _quality_roundoff(eltype(r),terms)
    reliable = finite && isfinite(roundoff) && roundoff < 1 &&
        (ratio + roundoff)/(1-roundoff) <= policy.solve_tolerance
    return SolveQuality{T}(absolute_T,ratio_T,finite,reliable)
end

_stored_quality_bits(::Type{T}, B, x, rhs, policy) where {T<:AbstractFloat} = precision(T)
function _stored_quality_bits(::Type{BigFloat}, B, x, rhs, policy)
    return max(precision(BigFloat), precision(policy.solve_tolerance),
        maximum(precision,_quality_values(B);init=2), maximum(precision,x;init=2),
        maximum(precision,rhs;init=2))
end

function _wide_solve_quality!(scratch::SolveQualityScratch{T}, B, x, rhs, policy, transposed) where {T}
    input_bits = _stored_quality_bits(T,B,x,rhs,policy)
    term_count = max(size(B,1),size(B,2),1)
    # Additional bits keep residual-evaluation uncertainty below the policy's
    # solve tolerance; this does not change the basis working precision.
    bits = max(128, 2*input_bits + ndigits(term_count; base=2) + 16)
    return setprecision(BigFloat,bits) do
        r, scale = zeros(BigFloat,length(rhs)), zeros(BigFloat,length(rhs))
        unsafe_range = _quality_components!(r,scale,scratch.terms,B,x,rhs,transposed)
        quality = _floating_quality!(scratch,r,scale,scratch.terms,policy)
        unsafe_range ? SolveQuality{T}(quality.absolute_error,quality.relative_error,false,false) : quality
    end
end

"""Evaluate an absolute residual and a componentwise backward error.

Scratch is owned separately from live tableau vectors. Float32 and Float64 use
native compensated accumulation before a local BigFloat evaluation is needed
for unsafe range or an inconclusive rounding-error enclosure. Stored
BigFloat precision is respected. Small backward error is not a forward-error
or pivot-safety certificate. Exact rationals require an exactly zero residual.
"""
function solve_quality!(scratch::SolveQualityScratch{T}, B::AbstractMatrix{T},
                        x::AbstractVector{T}, rhs::AbstractVector{T},
                        policy::NumericalPolicy{T}; transposed::Bool=false) where {T}
    rows, columns = transposed ? reverse(size(B)) : size(B)
    length(rhs) == rows && length(x) == columns && length(scratch.residual) == rows ||
        throw(DimensionMismatch("Incompatible basis residual dimensions"))
    any(array -> Base.mightalias(array,rhs) || Base.mightalias(array,x) ||
        Base.mightalias(array,_quality_values(B)),
        (scratch.residual,scratch.work_residual,scratch.work_scale,
         scratch.compensation,scratch.error_sum)) &&
        throw(ArgumentError("Quality scratch must not alias basis, solution, or RHS"))
    if _is_exact(T) === Val(true)
        _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
        copyto!(scratch.residual,scratch.work_residual)
        absolute = maximum(abs,scratch.residual;init=zero(T))
        return SolveQuality{T}(absolute,nothing,true,iszero(absolute))
    end
    if !all(isfinite,_quality_values(B)) || !all(isfinite,x) || !all(isfinite,rhs)
        fill!(scratch.residual,T(Inf))
        return SolveQuality{T}(T(Inf),T(Inf),false,false)
    end
    T === BigFloat && return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    unsafe_range = _quality_components!(scratch.work_residual,scratch.work_scale,scratch.terms,B,x,rhs,transposed)
    roundoff = _quality_roundoff(eltype(scratch.work_residual),scratch.terms)
    if unsafe_range || !all(isfinite,scratch.work_residual) || !all(isfinite,scratch.work_scale) ||
       roundoff > policy.solve_tolerance/4
        if !unsafe_range
            native = _compensated_solve_quality!(scratch,B,x,rhs,policy,transposed)
            isnothing(native) || return native
        end
        return _wide_solve_quality!(scratch,B,x,rhs,policy,transposed)
    end
    return _floating_quality!(scratch,scratch.work_residual,scratch.work_scale,scratch.terms,policy)
end


_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)
function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix{T},
                               x,rhs,transposed) where {W,T}
    for i in eachindex(rhs)
        r[i] = W(rhs[i])
        scale[i] = abs(r[i])
        terms[i] = 1
    end
    A = B.matrix
    m,n = size(A)
    unsafe = false
    for j in axes(A,2), p in nzrange(A,j)
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,A.nzval[p],j,A.rowval[p],transposed)
    end
    for i in 1:m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,-one(T),n+i,i,transposed)
    end
    for i in 1:n+m
        unsafe |= _accumulate_quality_term!(r,scale,terms,x,one(T),i,m+i,transposed)
    end
    return unsafe
end


function _audit_primal_values!(ws::SimplexWorkspace{T})::Symbol where T
    return _with_recovery_precision(ws, ws) do
        predicted = copy(ws.primal)
        predicted_costs = copy(ws.reduced_costs)
        recompute!(ws)
        _finite_workspace(ws) && _recomputed_basis_reliable(ws) || return :unreliable
        tolerance = ws.progress.numerical_policy.solve_tolerance
        for i in eachindex(predicted)
            old, current = predicted[i], ws.primal[i]
            isfinite(old) || return :corrected
            if T <: Rational
                old == current || return :corrected
            else
                scale = max(one(T), abs(old), abs(current))
                abs(old / scale - current / scale) <= tolerance || return :corrected
            end
        end
        return _primal_price_prediction_reliable(ws,predicted_costs) ? :accurate : :corrected
    end
end


end

const LocalCandidateA=JSimplex
const LocalCandidateB=JSimplex
const LocalCandidateAB=JSimplex
const LocalCandidateC=JSimplex
using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.SolveQuality,b::J.SolveQuality)=same(a.absolute_error,b.absolute_error)&&same(a.relative_error,b.relative_error)&&a.finite==b.finite&&a.reliable==b.reliable
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
struct PlainWrapper{T} <: AbstractMatrix{T};data::Matrix{T};end
Base.size(B::PlainWrapper)=size(B.data)
Base.getindex(B::PlainWrapper,i::Int,j::Int)=B.data[i,j]
function fixture(::Type{T},n,scope,density,pattern,m=4) where T
 if scope===:finish
  r=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//64) for i in 1:n]
  scale=fill(T(2),n);terms=fill(5,n)
  return (scope=scope,r=r,scale=scale,terms=terms,scratch=J.SolveQualityScratch(T,n),policy=J.NumericalPolicy(T))
 elseif scope in (:quality,:quality_transposed)
  B=zeros(T,n,n)
  for j in 1:n,i in 1:n
   if i==j;B[i,j]=T(2)
   elseif density===:dense||(i+j)%8==0;B[i,j]=T(1//32);end
  end
  density===:sparse&&(B=sparse(B))
  x=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%5+1)//8) for i in 1:n]
  rhs=scope===:quality ? B*x : transpose(B)*x
  return (scope=scope,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,n),policy=J.NumericalPolicy(T))
 end
 A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if density===:dense||(i+j)%4==0;A[i,j]=T(((i+j)%5+1)//32);end
 end
 lo=T[(pattern===:zero ? 0 : pattern===:negative||pattern===:mixed&&isodd(i) ? -1 : 1)*((i%3+1)//4) for i in 1:n]
 p=LinearProblem(sparse(A),T[(i%3+1)//8 for i in 1:n];column_lower=lo,column_upper=lo.+T(4),row_lower=fill(-T(1024),m),row_upper=fill(T(1024),m))
 opt=SolverOptions(T;algorithm=:primal,pricing=:dantzig,verbose=false)
 pol=J.NumericalPolicy(T;refactor_timing=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 (scope=scope,w=w,primal=copy(w.primal),prices=copy(w.reduced_costs))
end
function reset!(v)
 if v.scope===:audit;copyto!(v.w.primal,v.primal);copyto!(v.w.reduced_costs,v.prices);end
 nothing
end
function inputs(v)
 if v.scope===:finish;return (v.r,v.scale,v.terms);end
 if v.scope!==:audit
  B=v.B
  if B isa J._PriceAuditMatrix;B=B.matrix;end
  return B isa SparseMatrixCSC ? (B.nzval,B.rowval,B.colptr,v.x,v.rhs) : (B,v.x,v.rhs)
 end
 w=v.w
 (w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.problem.objective,w.costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states)
end
function outputs(v)
 if v.scope!==:audit
  s=v.scratch;return (s.residual,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum)
 end
 w=v.w
 (w.primal,w.reduced_costs,w.pricing_weights,w.scratch.rho,w.scratch.row_rhs,w.scratch.row_solution,w.scratch.tableau_row,w.iterations,w.refactorizations)
end
snapshot(v)=(inputs(v),map(copy,inputs(v)),deepcopy(inputs(v)))
function intact(v,s)
 all(inputs(v)[i]===s[1][i]&&same(inputs(v)[i],s[3][i])&&all(inputs(v)[i][j]===s[2][i][j] for j in eachindex(s[2][i])) for i in eachindex(s[1]))
end
@noinline function whole(::Val{arm},::Val{scope},v) where {arm,scope}
 mod=arm===:original ? LocalReference : arm===:A ? LocalCandidateA : arm===:B ? LocalCandidateB : arm===:AB ? LocalCandidateAB : LocalCandidateC
 if scope===:audit;return mod._audit_primal_values!(v.w)
 elseif scope===:finish;return mod._floating_quality!(v.scratch,v.r,v.scale,v.terms,v.policy)
 else;return mod.solve_quality!(v.scratch,v.B,v.x,v.rhs,v.policy;transposed=scope===:quality_transposed)
 end
end
sink(x::Symbol)=x===:accurate ? 1 : x===:corrected ? 2 : 3
sink(x::J.SolveQuality)=Int(x.finite)+2Int(x.reliable)+Int(iszero(x.absolute_error))
@noinline runwhole(m,s,v)=sink(whole(m,s,v))
function timed(m::M,s::S,v::V) where {M,S,V}
 t=@timed runwhole(m,s,v);merge(cost(t),Dict("sink"=>t.value))
end
function checkpair(a,b,arm;protect=true)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),Val(a.scope),a));y=capture(()->whole(Val(arm),Val(b.scope),b))
 @test same(x,y)
 @test same(outputs(a),outputs(b))
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 protect&&@test intact(a,sa)&&intact(b,sb)
 x
end
variants(scope)=scope===:audit ? (:C,) : scope===:finish ? (:B,) : (:A,:B,:AB)
scopes(::Type{T}) where T=T<:AbstractFloat ? (:quality,:quality_transposed,:finish,:audit) : (:quality,:quality_transposed,:audit)
function correctness(::Type{T}) where T
 @testset "Local quality correctness $T" begin
  for scope in scopes(T),arm in variants(scope),pattern in (:positive,:negative,:mixed,:zero)
   for density in (scope===:finish ? (:vector,) : (:sparse,:dense))
    a=fixture(T,8,scope,density,pattern);b=fixture(T,8,scope,density,pattern)
    z=checkpair(a,b,arm)
    @test z[1]===:value
    scope===:audit&&@test z[2]===:accurate
   end
  end
  for scope in scopes(T),arm in variants(scope),edge in (:empty,:short,:nonfinite,:mixed_precision,:view,:alias,:perturbed)
   a=fixture(T,8,scope,:dense,:mixed);b=fixture(T,8,scope,:dense,:mixed)
   if edge===:empty&&scope!==:audit;a=fixture(T,0,scope,:dense,:zero);b=fixture(T,0,scope,:dense,:zero);end
   for side in (:a,:b)
    v=side===:a ? a : b
    if scope===:finish
     if edge===:short;v=merge(v,(scale=v.scale[1:end-1],))
     elseif edge===:nonfinite&&T<:AbstractFloat;v.r[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.r[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:view;v=merge(v,(r=view(v.r,:),))
     elseif edge===:alias;v=merge(v,(r=v.scratch.residual,))
     elseif edge===:perturbed;v.scale[1]=-one(T)
     end
    elseif scope===:audit
     if edge===:nonfinite&&T<:AbstractFloat;v.primal[1]=T(NaN)
     elseif edge===:mixed_precision&&T===BigFloat;v.primal[1]=setprecision(()->BigFloat(v.primal[1]),BigFloat,512)
     elseif edge===:perturbed;v.primal[1]+=one(T)
     end
    else
     if edge===:short;v=merge(v,(x=v.x[1:end-1],))
     elseif edge===:nonfinite&&T<:AbstractFloat;v.x[1]=T(Inf)
     elseif edge===:mixed_precision&&T===BigFloat;v.x[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
     elseif edge===:view;v=merge(v,(x=view(v.x,:),))
     elseif edge===:alias
      s=v.scratch;v=merge(v,(scratch=J.SolveQualityScratch(v.x,s.work_residual,s.work_scale,s.terms,s.compensation,s.error_sum),))
     elseif edge===:perturbed;v.rhs[1]+=one(T)
     end
    end
    side===:a ? (a=v) : (b=v)
   end
   # Alias correctness permits the original explicitly mutable scratch overlap.
   z=checkpair(a,b,arm;protect=edge!==:alias)
   edge===:short&&scope!==:audit&&@test z[1]===:error&&z[2]===DimensionMismatch
   edge===:alias&&scope in (:quality,:quality_transposed)&&@test z[1]===:error&&z[2]===ArgumentError
   edge===:nonfinite&&scope===:audit&&@test z[1]===:value&&z[2]===(T<:AbstractFloat ? :corrected : :accurate)
   edge===:perturbed&&scope===:audit&&@test z[1]===:value&&z[2]===:corrected
  end
  for transposed in (false,true),arm in (:A,:B,:AB)
   B=J._PriceAuditMatrix(sparse(T[1 0;0 2]));x=ones(T,transposed ? size(B,1) : size(B,2));rhs=transposed ? transpose(B)*x : B*x
   scope=transposed ? :quality_transposed : :quality
   a=(scope=scope,B=B,x=x,rhs=rhs,scratch=J.SolveQualityScratch(T,length(rhs)),policy=J.NumericalPolicy(T));b=merge(a,(x=copy(x),rhs=copy(rhs),scratch=J.SolveQualityScratch(T,length(rhs))))
   z=checkpair(a,b,arm);@test z[1]===:value&&z[2].reliable
  end
  if T===BigFloat
   for modeval in (BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat))
    for arm in (:A,:B,:AB),scope in (:quality,:quality_transposed,:finish)
     a=fixture(T,2,scope,:dense,:positive);b=fixture(T,2,scope,:dense,:positive)
     for v in (a,b)
      if scope===:finish;v.r[1]=copy(modeval)
      else;v.x[1]=copy(modeval);end
     end
     checkpair(a,b,arm)
    end
   end
  elseif T<:AbstractFloat
   for scope in (:quality,:quality_transposed),arm in (:B,:AB)
    a=fixture(T,2,scope,:dense,:positive);b=fixture(T,2,scope,:dense,:positive)
    for v in (a,b);v.B[1,1]=T(2);v.x[1]=floatmax(T);v.rhs[1]=floatmax(T);end
    checkpair(a,b,arm)
   end
  end
 end
end

@testset "BigFloat invocation-local quality regressions" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat)
    # Nonordinary matrices must retain the generic fallback.
    for scope in (:quality,:quality_transposed)
     a=fixture(BigFloat,4,scope,:dense,:mixed);b=fixture(BigFloat,4,scope,:dense,:mixed)
     a=merge(a,(B=PlainWrapper(a.B),));b=merge(b,(B=PlainWrapper(b.B),));checkpair(a,b,:AB)
    end
    # Direct whole-finalizer checks at zero/negative/nonfinite scales and
    # roundoff boundaries, including hardware result with BigFloat work.
    for scalevalue in (BigFloat(0),BigFloat(-1),BigFloat(Inf),BigFloat(NaN)),term in (0,5,typemax(Int))
     a=fixture(BigFloat,2,:finish,:vector,:mixed);b=fixture(BigFloat,2,:finish,:vector,:mixed)
     for v in (a,b);v.scale[1]=copy(scalevalue);v.terms[1]=term;end
     checkpair(a,b,:B)
    end
    for T in (Float32,Float64)
     a=fixture(BigFloat,2,:finish,:vector,:mixed);b=fixture(BigFloat,2,:finish,:vector,:mixed)
     a=merge(a,(scratch=J.SolveQualityScratch(T,2),policy=J.NumericalPolicy(T)));b=merge(b,(scratch=J.SolveQualityScratch(T,2),policy=J.NumericalPolicy(T)));checkpair(a,b,:B)
    end
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 # Fixed three alternating whole-call allocation pairs. No time assertion,
 # GC selection, repeated searches or reduced numerical expectations.
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (scope,pattern,m,arm) in ((:quality,:negative,0,:AB),(:quality_transposed,:negative,0,:AB),(:finish,:mixed,0,:B),(:audit,:positive,4,:C))
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,96,scope,:dense,pattern,m);b=fixture(BigFloat,96,scope,:dense,pattern,m);s=Val(scope)
     for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(method,s,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),s,a);reset!(b);new=timed(Val(arm),s,b)
      else;reset!(b);new=timed(Val(arm),s,b);reset!(a);old=timed(Val(:original),s,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["bytes"]<old["bytes"]&&new["events"]<old["events"] for (old,new) in pairs) # RED whole-call cost gate
    end
   end
  end
 end
end
end
