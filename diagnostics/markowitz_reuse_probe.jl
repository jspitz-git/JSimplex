# Complete-production before/after audit. Run from the repository root.
# julia --startup-file=no --compiled-modules=existing --project=dev \
#   diagnostics/markowitz_reuse_probe.jl before diagnostics/markowitz_reuse_before.toml
# Optional third argument selects an entire source directory, for reproducibility.
using SparseArrays, LinearAlgebra, Logging, TOML, Statistics, Test, SHA
BLAS.set_num_threads(1)
const mode = ARGS[1]
@assert mode in ("before", "after")
const source_root = abspath(length(ARGS) >= 3 ? ARGS[3] :
    mode == "before" ? "/tmp/jsimplex-markowitz-original/src" : "src")
const source_hashes = Dict{String,String}()
for (root,dirs,files) in walkdir(source_root), name in sort(files)
    endswith(name,".jl") || continue
    path=joinpath(root,name)
    source_hashes[relpath(path,source_root)]=bytes2hex(sha256(read(path)))
end
# Freeze the complete source before loading so concurrent edits cannot mix versions.
# Base.require only supplies the dependency context lost by direct module inclusion.
const snapshot_root = joinpath(mktempdir(),"src")
cp(source_root,snapshot_root)
for (name,old,new) in (
    ("JSimplex.jl", "import OrderedCollections",
     "const OrderedCollections = Base.require(Base.PkgId(Base.UUID(\"bac558e1-5e72-5ebc-8fee-abe8a469f55d\"),\"OrderedCollections\"))"),
    ("moi.jl", "import MathOptInterface as MOI",
     "const MOI = Base.require(Base.PkgId(Base.UUID(\"b8f27783-ece8-5eb3-8dc8-9495eed66fee\"),\"MathOptInterface\"))"))
    path=joinpath(snapshot_root,name)
    write(path,replace(read(path,String),old=>new))
end
include(joinpath(snapshot_root,"JSimplex.jl"))
using .JSimplex

function audit_matrix(::Type{T},n,kind) where T
    B=spdiagm(0=>fill(T(4),n))
    if kind=="band"
        B+=spdiagm(-1=>fill(-one(T),n-1),1=>fill(-one(T),n-1))
    elseif kind=="fill"
        for i in 1:n, offset in (1,5,13)
            B[i,mod1(i+offset,n)]=-one(T)
        end
    elseif kind=="hybrid"
        start=n-n÷4+1
        for i in start:n,j in start:n
            B[i,j]=i==j ? T(n) : one(T)
        end
    elseif kind=="dense"
        B=sparse(fill(one(T),n,n))
        for i in 1:n; B[i,i]=T(n); end
    end
    B
end
_timed_audit_call(f)=@timed f()
function measure_repeated(f;samples=5)
    # Three calls populate both protected output slots and any capacity growth.
    _timed_audit_call(f); _timed_audit_call(f); _timed_audit_call(f)
    records=map(1:samples) do _
        GC.gc()
        _timed_audit_call(f)
    end
    Dict{String,Any}("bytes"=>minimum(t.bytes for t in records),
        "allocations"=>minimum(Base.gc_alloc_count(t.gcstats) for t in records),
        "bytes_max"=>maximum(t.bytes for t in records),
        "allocations_max"=>maximum(Base.gc_alloc_count(t.gcstats) for t in records),
        "seconds_min"=>minimum(t.time for t in records),
        "seconds_median"=>median([t.time for t in records]),
        "compile_seconds"=>maximum(t.compile_time for t in records),"samples"=>samples)
end
function factor_metadata(f,B)
    base=f.base; T=eltype(B); n=size(B,1)
    x=JSimplex.forward_solve(f,B*ones(T,n))
    xt=JSimplex.transpose_solve(f,transpose(B)*ones(T,n))
    @test x ≈ ones(T,n)
    @test xt ≈ ones(T,n)
    Dict{String,Any}("row_order"=>copy(base.row_order),"column_order"=>copy(base.column_order),
        "sparse_pivots"=>base.sparse_pivots,"core_dimension"=>size(base.core,1),
        "lower_nnz"=>sum(v->length(v.indices),base.lower;init=0),
        "upper_nnz"=>sum(v->length(v.indices),base.upper;init=0),
        "forward_error"=>Float64(maximum(abs,x.-one(T))),
        "transpose_error"=>Float64(maximum(abs,xt.-one(T))))
end

const updates=(:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
rows=Dict{String,Any}[]; solves=Dict{String,Any}[]
function save_results()
    open(io->TOML.print(io,Dict("mode"=>mode,"source_root"=>source_root,
        "source_hashes"=>source_hashes,"julia_version"=>string(VERSION),
        "machine"=>Sys.MACHINE,"threads"=>Threads.nthreads(),
        "blas_threads"=>BLAS.get_num_threads(),"presolve"=>false,"scaling"=>"off",
        "rows"=>rows,"solves"=>solves);sorted=true),ARGS[2],"w")
end
@testset "Production Markowitz repeated-refactorization reference solves" begin
    for T in (Float64,Float32,BigFloat,Rational{BigInt})
        ns=T<:Union{Float32,Float64} ? (64,256) : (32,)
        patterns=T<:Union{Float32,Float64} ? ("diagonal","band","fill","hybrid","dense") : ("band","fill")
        methods=T<:Union{Float32,Float64} ? updates : (:pfi,)
        for n in ns,kind in patterns
            B=audit_matrix(T,n,kind); original=copy(B)
            for method in methods
                factor=JSimplex._basis_factorization(B,Val(method),Val(:markowitz))
                cold=factor_metadata(factor,B)
                run=()->(JSimplex.refactorize!(factor,B); nothing)
                row=measure_repeated(run;samples=T<:Union{Float32,Float64} ? 5 : 3)
                warm=factor_metadata(factor,B)
                @test B==original
                merge!(row,warm,Dict("value_type"=>string(T),"dimension"=>n,"pattern"=>kind,
                    "basis_update"=>string(method),
                    "cold_matches_warm"=>cold["row_order"]==warm["row_order"] && cold["column_order"]==warm["column_order"]))
                push!(rows,row)
            end
            println(mode," ",T," n",n," ",kind," recorded");flush(stdout)
            save_results()
        end
    end
end
with_logger(NullLogger()) do
    @testset "Production Markowitz complete reference solves" begin
        for (name,path,reference) in (
            ("afiro","test/fixtures/solver/afiro.mps",-464.75314285714285),
            ("adlittle","test/fixtures/solver/netlib/adlittle.mps",225494.9631623803))
            problem=read_mps(path)
            for method in updates,algorithm in (:dual,:primal)
                options=SolverOptions(;basis_refactorization=:markowitz,basis_update=method,algorithm,
                    presolve=false,scaling=:off,verbose=false,iteration_limit=10_000)
                run=()->solve(problem;options)
                result=measure_repeated(run;samples=5)
                solution=run()
                @test solution.status==OPTIMAL
                @test isapprox(solution.objective_value,reference;rtol=1e-10,atol=1e-7)
                merge!(result,Dict("dataset"=>name,"basis_update"=>string(method),"algorithm"=>string(algorithm),
                    "status"=>string(solution.status),"objective"=>solution.objective_value,
                    "iterations"=>solution.statistics.iterations,
                    "refactorizations"=>solution.statistics.refactorizations))
                push!(solves,result)
                println(mode," ",name," ",method," ",algorithm," ",solution.status);flush(stdout)
                save_results()
            end
        end
    end
end
save_results()
