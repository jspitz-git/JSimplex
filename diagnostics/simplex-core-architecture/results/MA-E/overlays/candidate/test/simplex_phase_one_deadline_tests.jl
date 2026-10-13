using Test,JSimplex,SparseArrays

@testset "Phase one stops before factoring a newly constructed auxiliary basis" begin
    p=LinearProblem(sparse(reshape([1.0,1.0],2,1)),[1.0];row_lower=ones(2),row_upper=ones(2))
    cancelled=Ref(false);late_factors=Ref(0)
    d=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        if reason==:refactor_initial && size(ws.problem.A,2)>1
            cancelled[]=true
        elseif reason==:refactor_other && cancelled[]
            late_factors[]+=1
        end
    end)
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
    ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->cancelled[])
    @test result.status==TIME_LIMIT
    @test cancelled[]
    @test late_factors[]==0
    @test result.iterations==0
    @test result.refactorizations==0
end

@testset "Modern primal entry checks cancellation before its initial factor" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
    d=JSimplex.SimplexDiagnostics()
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
    progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d)
    result=JSimplex._solve_continuous_primal(p,SolverOptions(;algorithm=:primal,verbose=false);
        progress,stop_requested=()->true)
    @test result.status==TIME_LIMIT
    @test JSimplex.event_count(d,:refactor_initial)==0
    @test result.iterations==0
end
