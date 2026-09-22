# Isolate the third runtime step against a complete pre-cache source snapshot.
# Usage: julia --project=dev diagnostics/markowitz_runtime_probe.jl BEFORE_SRC OUT [AFTER_SRC]
using SparseArrays, LinearAlgebra, Logging, Statistics, SHA, TOML, Test
include_string(Main, first(split(read(joinpath(@__DIR__,"runtime_probe.jl"),String),
    "const before_scope,";limit=2)),"runtime_snapshot_loader.jl")
const old_scope,old_hashes=load_snapshot(:MarkowitzBefore,abspath(ARGS[1]))
const Old=getfield(old_scope,:JSimplex)
const new_scope,new_hashes=load_snapshot(:MarkowitzAfter,abspath(length(ARGS)>=3 ? ARGS[3] : "src"))
const New=getfield(new_scope,:JSimplex)
const measurements=Dict{String,Any}[]

function measure(label,old,new;samples=31,repetitions=10)
    for _ in 1:3; old();new(); end
    a_times,b_times=Float64[],Float64[]
    a_bytes,b_bytes=Int[],Int[]
    run(f)=(@timed for _ in 1:repetitions; f(); end)
    run(old);run(new)
    for i in 1:samples
        if isodd(i); a=run(old); b=run(new)
        else; b=run(new); a=run(old)
        end
        @test a.compile_time == b.compile_time == 0
        push!(a_times,a.time/repetitions);push!(b_times,b.time/repetitions)
        push!(a_bytes,a.bytes÷repetitions);push!(b_bytes,b.bytes÷repetitions)
    end
    row=Dict("case"=>label,"before_seconds"=>a_times,"after_seconds"=>b_times,
        "speedup"=>median(a_times./b_times),"before_bytes"=>minimum(a_bytes),"after_bytes"=>minimum(b_bytes))
    push!(measurements,row)
    println(label," speedup=",round(row["speedup"],digits=3));flush(stdout)
end

function signature(M,f,B)
    b=f.base; rhs=eltype(B).(1:size(B,1))
    return (b.sparse_pivots,copy(b.row_order),copy(b.column_order),copy(b.diagonal),
        [(copy(c.indices),copy(c.values)) for c in b.lower],
        [(copy(c.indices),copy(c.values)) for c in b.upper],
        copy(b.core.factors),copy(b.core.ipiv),
        M.forward_solve(f,rhs),M.transpose_solve(f,rhs))
end
function pivot_problem(M,::Type{T},n) where T
    D=M.OrderedCollections.OrderedDict{Int,T}
    rows=[D(1=>one(T)) for _ in 1:n]
    for i in n-1:n
        rows[i]=D(j=>(j==1 ? T(100) : one(T)) for j in 1:3)
    end
    columns=[D(i=>rows[i][1] for i in 1:n),D(n-1=>one(T),n=>one(T)),D(n-1=>one(T),n=>one(T))]
    args=(rows,columns,trues(n),trues(3),collect(1:n-2),Int[],BitSet([2,3]))
    if M===New
        cache=(Vector{T}(undef,3),falses(3))
        return ()->M._markowitz_pivot(args...,cache)
    end
    return ()->M._markowitz_pivot(args...)
end
with_logger(NullLogger()) do
    @testset "Markowitz pivot caching timings and exact refactorizations" begin
        for T in (Float32,Float64,BigFloat,Rational{BigInt})
            old,new=pivot_problem(Old,T,64),pivot_problem(New,T,64)
            @test old()==new()
            measure("pivot/$T/64/rejected-singletons",old,new)
            for n in (32,64),pattern in ("diagonal","band","fill","rejected-singletons")
                # Bound exact-arithmetic fill growth while still exercising sparse pivots.
                T===Rational{BigInt} && n==64 && pattern=="fill" && continue
                B=spdiagm(0=>fill(T(4),n))
                if pattern=="rejected-singletons"
                    # Nonsingular block triangular basis: singleton rows have
                    # distinct columns, and a dense 2x2 tail prevents column-singleton exits.
                    B=spdiagm(0=>ones(T,n))
                    for i in n-1:n, j in 1:n-2
                        B[i,j]=T(100)
                    end
                    B[n-1:n,n-1:n]=T[2 1;1 2]
                elseif pattern=="band"
                    B+=spdiagm(-1=>fill(-one(T),n-1),1=>fill(-one(T),n-1))
                elseif pattern=="fill"
                    for i in 1:n,offset in (1,5,13)
                        B[i,mod1(i+offset,n)]=-one(T)
                    end
                end
                a=Old.PFIFactorization(B,Val(:markowitz))
                b=New.PFIFactorization(B,Val(:markowitz))
                @test isequal(signature(Old,a,B),signature(New,b,B))
                old=()->(Old.refactorize!(a,B);nothing)
                new=()->(New.refactorize!(b,B);nothing)
                measure("refactor/$T/$n/$pattern",old,new)
                @test isequal(signature(Old,a,B),signature(New,b,B))
            end
        end
    end
end
open(ARGS[2],"w") do io
    TOML.print(io,Dict("julia"=>string(VERSION),"machine"=>Sys.MACHINE,
        "before_hashes"=>old_hashes,"after_hashes"=>new_hashes,"measurements"=>measurements);sorted=true)
end
