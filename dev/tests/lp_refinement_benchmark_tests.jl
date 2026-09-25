module LPRefinementBenchmarkTests
using Test, JSimplex, SparseArrays
include("../simplex_benchmarks.jl")

@testset "Benchmark diagnostics retain the certified LP multiplier" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];column_lower=[0.0],row_lower=[1.0])
    options=SolverOptions(;verbose=false,presolve=false,scaling=:off)
    basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    ws=JSimplex.initialize_from_basis(p,basis,options)
    ws.factorization=JSimplex._basis_factorization(sparse([2.0;;]),options)
    ws.scratch.lp_dual_witness=[1.0]
    @test JSimplexBenchmarks.benchmark_dual_witness(JSimplex,ws)==[1.0]
    ws.scratch.lp_dual_witness=nothing
    @test JSimplexBenchmarks.benchmark_dual_witness(JSimplex,ws)==[0.5]
    bigws=setprecision(BigFloat,512) do
        p=LinearProblem(sparse(BigFloat[1;;]),BigFloat[1];column_lower=BigFloat[0],row_lower=BigFloat[1])
        JSimplex.initialize_from_basis(p,basis,SolverOptions(BigFloat;verbose=false,presolve=false,scaling=:off))
    end
    bigws.scratch.lp_dual_witness=setprecision(BigFloat,600) do
        [BigFloat(1)+BigFloat(2)^(-500)]
    end
    # A nonunit divisor forces arithmetic that would lose stored bits if the
    # benchmark unscaled under the ambient 64-bit context.
    bigws.progress.scaling.row_factors[1] = BigFloat(3)
    expected = setprecision(BigFloat,600) do
        [(BigFloat(1)+BigFloat(2)^(-500))/3]
    end
    setprecision(BigFloat,64) do
        dual=JSimplexBenchmarks.benchmark_dual_witness(JSimplex,bigws)
        @test dual==expected
        @test minimum(precision,dual)>=600
        @test precision(BigFloat)==64
    end
end
end
