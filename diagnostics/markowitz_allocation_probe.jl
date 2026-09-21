# Read-only allocation audit of the current implementation.
using JSimplex, SparseArrays, LinearAlgebra, Logging, TOML, Test
include(joinpath(pwd(), "dev", "allocations.jl"))
using .JSimplexAllocations: measure_allocations, allocation_profile
BLAS.set_num_threads(1)

function markowitz_probe_matrix(::Type{T}, n, kind) where {T}
    B = spdiagm(0=>fill(T(4),n))
    if kind == "band"
        B += spdiagm(-1=>fill(-one(T),n-1),1=>fill(-one(T),n-1))
    elseif kind == "fill"
        for i in 1:n, offset in (1,5,13)
            B[i,mod1(i+offset,n)] = -one(T)
        end
    elseif kind == "hybrid"
        start = n - n÷4 + 1
        for i in start:n, j in start:n
            B[i,j] = i==j ? T(n) : one(T)
        end
    elseif kind == "dense"
        B = sparse(fill(one(T),n,n))
        for i in 1:n
            B[i,i] = T(n)
        end
    end
    return B
end

refac_run(f,B) = (JSimplex.refactorize!(f,B); nothing)
forward_run(s) = (JSimplex.forward_solve!(s[3],s[1],s[2]); nothing)
transpose_run(s) = (JSimplex.transpose_solve!(s[3],s[1],s[2]); nothing)
rows=Dict{String,Any}[]
profiles=Dict{String,Any}[]
solves=Dict{String,Any}[]
with_logger(NullLogger()) do
    @testset "Markowitz audit reference solves" begin
        for T in (Float64,Float32,BigFloat,Rational{BigInt})
            for n in (T <: Union{Float32,Float64} ? (64,256) : (16,32)),
                kind in ("diagonal","band","fill","hybrid","dense")
                B=markowitz_probe_matrix(T,n,kind)
                setup=()->JSimplex.PFIFactorization(B,Val(:markowitz))
                factor=setup()
                rhs=B*ones(T,n)
                rhs_t=transpose(B)*ones(T,n)
                @test JSimplex.forward_solve(factor,rhs) ≈ ones(T,n)
                @test JSimplex.transpose_solve(factor,rhs_t) ≈ ones(T,n)
                metadata=Dict("value_type"=>string(T),"dimension"=>n,"pattern"=>kind,
                    "sparse_pivots"=>factor.base.sparse_pivots,"core_dimension"=>size(factor.base.core,1))
                cases=(("refactorize",f->refac_run(f,B),setup),
                       ("forward",forward_run,()->(setup(),rhs,similar(rhs))),
                       ("transpose",transpose_run,()->(setup(),rhs_t,similar(rhs_t))),
                       ("copy",f->JSimplex.copy_basis_factorization(f),setup))
                for (stage,run,prepare) in cases
                    result=measure_allocations(run;setup=prepare,samples=3)
                    merge!(result,metadata,Dict("stage"=>stage))
                    push!(rows,result)
                end
                if T===Float64 || (n==16 && kind in ("band","fill") && T!==Float32)
                    rate=T===Float64 ? 1.0 : 0.05
                    profile=allocation_profile(f->refac_run(f,B),setup;sample_rate=rate)
                    push!(profiles,merge(copy(metadata),Dict("stage"=>"refactorize","sample_rate"=>rate,"sites"=>profile)))
                end
                println(T," ",n," ",kind," pivots=",factor.base.sparse_pivots," core=",size(factor.base.core,1))
                flush(stdout)
            end
        end
    end
    for (name,path) in (("afiro","test/fixtures/solver/afiro.mps"),("adlittle","test/fixtures/solver/netlib/adlittle.mps"))
        problem=read_mps(path)
        for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), algorithm in (:dual,:primal)
            options=SolverOptions(;basis_refactorization=:markowitz,basis_update=method,algorithm,
                presolve=false,scaling=:off,verbose=false,iteration_limit=10_000)
            run=_ -> solve(problem;options)
            result=measure_allocations(run;samples=3)
            solution=run(nothing)
            merge!(result,Dict("dataset"=>name,"basis_update"=>string(method),"algorithm"=>string(algorithm),
                "refactorizations"=>solution.statistics.refactorizations))
            push!(solves,result)
            if name=="adlittle" && method==:pfi
                profile=allocation_profile(run,()->nothing;sample_rate=1.0)
                push!(profiles,Dict("dataset"=>name,"basis_update"=>string(method),"algorithm"=>string(algorithm),
                    "stage"=>"solve","sample_rate"=>1.0,"sites"=>profile))
            end
        end
        println(name," solves measured");flush(stdout)
    end
end
report=Dict("julia_version"=>string(VERSION),"machine"=>Sys.MACHINE,"threads"=>Threads.nthreads(),
    "blas_threads"=>BLAS.get_num_threads(),"presolve"=>false,"scaling"=>"off",
    "rows"=>rows,"profiles"=>profiles,"solves"=>solves)
open(io->TOML.print(io,report;sorted=true),ARGS[1],"w")
