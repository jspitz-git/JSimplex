using Test,JSimplex,SparseArrays

@testset "Correction terminal proofs are not original-model proofs" begin
    for expected in (INFEASIBLE,UNBOUNDED)
        p=expected==INFEASIBLE ?
            LinearProblem(sparse([1.0;;]),[1.0];column_lower=[0.0],row_upper=[-1.0]) :
            LinearProblem(spzeros(0,1),[-1.0];column_lower=[0.0])
        policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,refactor_timing=false)
        options=SolverOptions(;verbose=false,presolve=false,scaling=:off,iteration_limit=30)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        m=size(p.A,1)
        residuals=JSimplex._lp_residuals(ws,ws.primal,zeros(m))
        sp,sd=JSimplex._lp_correction_scales(ws,residuals)
        correction,map=JSimplex.build_correction_problem(ws,residuals,sp,sd)
        auxiliary,run,witness=JSimplex._lp_auxiliary_run_at_working_precision(ws,correction,map,
            JSimplex.SimplexRunBudget(ws),policy,JSimplex._guard_stop_callback(()->false))
        @test run.status==expected
        @test isnothing(witness)
        recovered=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test recovered.status==NUMERICAL_ERROR
        @test isnothing(recovered.primal) && isnothing(recovered.objective_value)
    end
end

@testset "Rounded inconsistent correction does not reject a feasible original LP" begin
    T=Float32
    p=LinearProblem(sparse(reshape(T[1,3],2,1)),T[1];column_lower=T[0],row_lower=T[1,3],row_upper=T[1,3])
    policy=JSimplex.NumericalPolicy(T;lp_refinement=true,refactor_timing=false)
    options=SolverOptions(T;verbose=false,presolve=false,scaling=:off,iteration_limit=30,
        primal_tolerance=1f-12,dual_tolerance=1f-12,zero_tolerance=1f-12)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.primal .= T[0.1,1,3]
    @test JSimplex._original_primal_feasible(p,T[1],options.primal_tolerance)
    residuals=JSimplex._lp_residuals(ws,ws.primal,T[0,0])
    sp,sd=JSimplex._lp_correction_scales(ws,residuals)
    correction,map=JSimplex.build_correction_problem(ws,residuals,sp,sd)
    rhs=Rational{BigInt}.(bound_value.(correction.row_lower))
    @test rhs[2]!=3rhs[1]
    run=JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test run.status==NUMERICAL_ERROR
    @test isnothing(run.primal)
end
