using Test,JSimplex,SparseArrays
@testset "Legacy phase construction does not sum overflowing original violations" begin
    T = Rational{Int64}
    p = LinearProblem(spdiagm(0=>ones(T,2)),zeros(T,2);
        row_lower=fill(T(typemax(Int64)),2))
    options = SolverOptions(T;verbose=false,algorithm=:primal)
    ws,count,initial = JSimplex._primal_phase_one(p,options,
        JSimplex.SimplexProgressContext(p),()->false)
    @test count == 2
    @test iszero(JSimplex.primal_infeasibility(ws))
end

@testset "Crash falls back when the initial exact violation sum overflows" begin
    T = Rational{Int64}
    p = LinearProblem(spdiagm(0=>ones(T,2)),zeros(T,2);
        row_lower=fill(T(typemax(Int64)),2))
    policy = JSimplex.NumericalPolicy(T;crash=true)
    d = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d)
    options = SolverOptions(T;verbose=false,algorithm=:primal)
    initial = JSimplex.initialize_workspace(p,options;progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test ws === initial && !expired
    @test ws.iterations == 0
    @test JSimplex.event_count(d,:crash_fallback) == 1
    phase,count,_ = JSimplex._primal_phase_one(p,options,progress,()->false;initial=ws)
    @test count == 2
    @test iszero(JSimplex.primal_infeasibility(phase))
    limited = SolverOptions(T;verbose=false,algorithm=:primal,iteration_limit=0)
    run = JSimplex._solve_continuous_primal(p,limited;progress)
    @test run.status == ITERATION_LIMIT && run.iterations == 0
end
