using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "LP residual precision does not silently increase factor precision" begin
    seen = Int[]
    ws,policy = setprecision(BigFloat,512) do
        p=LinearProblem(sparse(BigFloat[2 1;1 3]),BigFloat[1,1];
            column_lower=BigFloat[0,0],row_lower=BigFloat[3,4],row_upper=BigFloat[6,8])
        policy=JSimplex.NumericalPolicy(BigFloat;lp_refinement=true,solve_refinement=false,
            recovery=false,refactor_timing=false)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
            if reason == :refactor_other && size(ws.problem.A,2)==4
                push!(seen,maximum(precision,ws.factorization.base.factorization.factors))
            end
        end)
        options=SolverOptions(BigFloat;verbose=false,presolve=false,scaling=:off)
        progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy)
        basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress)
        ws.factorization=JSimplex._basis_factorization(sparse(BigFloat[4 2;2 6]),options)
        ws,policy
    end
    setprecision(BigFloat,64) do
        run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status == OPTIMAL && run.primal == [1,1]
        @test !isempty(seen)
        @test maximum(seen)==512
        @test minimum(seen)==512
        @test precision(BigFloat)==64
        @test ws.progress.diagnostics.counts[:precision_boost]==0
    end
end

@testset "Correction pivots support every configured update and backend" begin
    for update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), backend in (:native,:markowitz)
        p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];
            column_lower=[0.0],row_lower=[1.0],row_upper=[2.0])
        policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,refactor_timing=false)
        diagnostics=JSimplex.SimplexDiagnostics()
        options=SolverOptions(;verbose=false,presolve=false,scaling=:off,
            basis_update=update,basis_refactorization=backend)
        progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy)
        ws=JSimplex.initialize_workspace(p,options;progress)
        ws.primal .= 1.5
        run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status==OPTIMAL && run.primal==[1.0]
        @test run.iterations>=1
        @test diagnostics.counts[:pivot_completed]>=1
        @test diagnostics.counts[:precision_boost]==0
        @test run.basis.basic_indices==[1]
    end
end
