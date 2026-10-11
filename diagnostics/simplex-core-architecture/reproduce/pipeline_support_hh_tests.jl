# Existing full-solver pipeline matrix omits HH. Cover its dense basis fallback
# together with pipeline pricing in both actual simplex algorithms.
using Test,JSimplex,SparseArrays,LinearAlgebra
@testset "HH pipeline fallback retains original certificates" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        backend in (:native,:markowitz),algorithm in (:primal,:dual),pricing in (:dantzig,:devex,:steepest_edge)
        n=12
        A=spdiagm(0=>ones(T,n),1=>T[isodd(i) ? 1//4 : 0 for i in 1:n-1])
        bound=A*ones(T,n)
        problem=algorithm==:primal ? LinearProblem(A,-ones(T,n);row_upper=bound) :
            LinearProblem(A,ones(T,n);row_lower=bound)
        options=SolverOptions(T;verbose=false,algorithm,pricing,basis_update=:huangfu_hall,
            basis_refactorization=backend,iteration_limit=200)
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,hypersparse=true,refactor_timing=false)
        diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true)
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
        run=JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status==OPTIMAL
        @test run.primal≈ones(T,n)
        @test JSimplex._original_primal_feasible(ws,run.primal)
        @test JSimplex.primal_infeasibility(ws)<=options.primal_tolerance
        @test JSimplex.dual_infeasibility(ws)<=options.dual_tolerance
        @test diagnostics.kernel_calls[:hypersparse_ftran_sparse]==diagnostics.kernel_calls[:hypersparse_btran_sparse]==0
        @test diagnostics.kernel_calls[:hypersparse_ftran_dense]>0
        @test diagnostics.kernel_calls[:hypersparse_btran_dense]>0
    end
end
