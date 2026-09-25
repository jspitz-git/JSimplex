using Test, JSimplex, SparseArrays

@testset "Auxiliary witnesses finish before their diagnostic context is closed" begin
    captured=Ref{Any}(nothing)
    injected=Ref(false)
    observed=Dict(:correction_attempt=>0,:correction=>0)
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        reason == :lp_correction_certification && (captured[]=ws)
        haskey(observed,reason) && (observed[reason]+=1)
    end)
    p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];
        column_lower=[0.0],row_lower=[1.0],row_upper=[2.0])
    policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,solve_refinement=true,
        recovery=false,refactor_timing=false)
    options=SolverOptions(;verbose=false,presolve=false,scaling=:off)
    progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy)
    basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress)
    ws.factorization=JSimplex._basis_factorization(sparse(reshape([2.0],1,1)),options)
    stop=()->begin
        if !isnothing(captured[]) && !injected[]
            auxiliary=captured[]
            auxiliary.factorization=JSimplex._basis_factorization(sparse(reshape([2.0],1,1)),auxiliary.options)
            injected[]=true
        end
        false
    end
    run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,stop)
    @test injected[]
    @test run.status==OPTIMAL && run.primal==[1.0]
    @test diagnostics.counts[:correction_attempt]==observed[:correction_attempt]
    @test diagnostics.counts[:correction]==observed[:correction]
end
