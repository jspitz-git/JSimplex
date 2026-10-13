using Test,JSimplex,SparseArrays

@testset "LP correction consumes no steps beyond the shared iteration limit" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];column_lower=[0.0],row_lower=[1.0],row_upper=[2.0])
    diagnostics=JSimplex.SimplexDiagnostics()
    policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,refactor_timing=false)
    options=SolverOptions(;verbose=false,presolve=false,scaling=:off)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
    ws.primal .= 1.5
    budget=JSimplex.SimplexRunBudget(ws)
    budget.iterations=budget.iteration_limit=3
    before=budget.refactorizations
    run=JSimplex.refine_lp!(ws,budget,policy,()->false)
    @test run.status==ITERATION_LIMIT
    @test run.iterations==budget.iterations==3
    @test diagnostics.counts[:pivot_completed]==0
    @test run.refactorizations==budget.refactorizations==before+1
end

@testset "LP recovery certifies the representable original-type point" begin
    for T in (Float32,Float64)
        p=LinearProblem(sparse(T[3;;]),T[1];column_lower=T[0],row_lower=T[1],row_upper=T[1])
        tolerance=eps(T)^2
        options=SolverOptions(T;verbose=false,presolve=false,scaling=:off,
            primal_tolerance=tolerance,dual_tolerance=tolerance)
        diagnostics=JSimplex.SimplexDiagnostics()
        policy=JSimplex.NumericalPolicy(T;lp_refinement=true,solve_refinement=false,refactor_timing=false)
        basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
        ws=JSimplex.initialize_from_basis(p,basis,options;policy,
            progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
        @test abs(3Rational{BigInt}(ws.primal[1])-1)>Rational{BigInt}(tolerance)
        original=copy(ws.primal)
        run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status==NUMERICAL_ERROR
        @test isnothing(run.primal) && isnothing(run.objective_value)
        @test diagnostics.counts[:lp_refinement]==1
        @test ws.primal==original && p.A[1,1]==3
    end
end

@testset "Zero-row corrections retain free and fixed bounds" begin
    p=LinearProblem(spzeros(0,2),[0.0,1.0];column_lower=[nothing,3.0],
        column_upper=[nothing,3.0],objective_constant=7.0)
    policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,refactor_timing=false)
    ws=JSimplex.initialize_workspace(p,SolverOptions(;verbose=false,presolve=false,scaling=:off);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.primal .= [0.0,4.0]
    run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test run.status==OPTIMAL && run.primal==[0.0,3.0]
    @test run.objective_value==10.0
    @test run.basis.states==[JSimplex.FREE_NONBASIC,JSimplex.AT_LOWER]
end
