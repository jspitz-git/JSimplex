# Diagnostic-local wrappers; no production method replacement.
const J = JSimplex
const MA = MutableArithmetics
const Q = Rational{BigInt}
include("reference-upper.jl")
qparse(s)=parse(BigInt,split(s,"/")[1])//(occursin("/",s) ? parse(BigInt,split(s,"/")[2]) : BigInt(1))
function fixture(::Type{T},f) where T
    n=f["n"]
    A=T[qparse(f["matrix"][i][j]) for i in 1:n,j in 1:n]
    rhs=T[qparse(s) for s in f["rhs"]]
    return f["storage"]=="sparse" ? sparse(A) : A,rhs
end
function withscalar(f,label)
    if startswith(label,"BigFloat")
        return setprecision(BigFloat,parse(Int,label[9:end])) do
            setrounding(BigFloat,RoundNearest) do; f(BigFloat); end
        end
    end
    return f(label=="RationalBigInt" ? Q : label=="Float32" ? Float32 : Float64)
end
function encoded(v)
    [Dict("value"=>string(Q(x)),"sign"=>signbit(x),"precision"=>x isa BigFloat ? precision(x) : 0) for x in v]
end
function metadata(b,f,T)
    s=b.sparse_pivots;k=sum(length(v.indices) for v in b.upper;init=0)
    e=T in (BigFloat,Q) ? count(v->length(v.indices)>=2,b.upper) : 0
    return Dict("S"=>s,"K"=>k,"E"=>e,"rows"=>b.row_order,"columns"=>b.column_order,
                "upper_indices"=>[v.indices for v in b.upper],"upper_values"=>[encoded(v.values) for v in b.upper],"diagonal"=>encoded(b.diagonal))
end
function seed(b,rhs,f)
    w=ones(eltype(rhs),length(rhs))
    if f["family"]=="star"
        for i in 1:b.sparse_pivots;w[i]=rhs[b.row_order[i]];end
    end
    return w
end
# Exact original prefix, diagnostic only in qualification; no extra cost-stage solve.
function reference_prefix!(b,rhs)
    w=b.work;s=b.sparse_pivots
    for i in 1:b.dimension;w[i]=rhs[b.row_order[i]];end
    for p in 1:s
        v=w[p];col=b.lower[p]
        for k in eachindex(col.indices);w[col.indices[k]]-=col.values[k]*v;end
    end
    for i in eachindex(b.core_work);b.core_work[i]=w[s+i];end
    isempty(b.core_work)||ldiv!(b.core,b.core_work)
    for i in eachindex(b.core_work);w[s+i]=b.core_work[i];end
    return w
end
@noinline function full_window!(out,b,rhs,reps::Int)
    for i in 1:reps;J._backend_forward_solve!(out,b,rhs);end
    return nothing
end
@noinline function upper_window!(f,w,b,initial,reps::Int)
    for i in 1:reps;copyto!(w,initial);f(w,b.upper,b.diagonal,b.sparse_pivots);end
    return nothing
end
scratch(::Type{T}) where T=(zero(T),MA.buffer_for(MA.sub_mul,T,T,T))
function measured(f,args...)
    t=@timed f(args...)
    return t.value,Dict("seconds"=>t.time,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),
      "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
end
