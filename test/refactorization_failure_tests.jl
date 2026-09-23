using SparseArrays, LinearAlgebra

@testset "A failed fresh factorization earns no healthy cycle" begin
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0]),[-1.0,-1.0];
        row_lower=zeros(2),row_upper=ones(2))
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    JSimplex.replace_column!(ws.factorization,[1.0,0.0],1;zero_tolerance=0.0)
    state = ws.scratch.refactorization
    state.healthy_cycles = 2
    state.productive_updates = 1
    ws.basis.basic_indices .= [1,2]
    ws.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]
    @test_throws SingularException JSimplex.recompute!(ws;refactorize=true,diagnostic_reason=:refactor_limit)
    @test state.interval == state.initial_interval
    @test state.healthy_cycles == 0
end

@testset "Rollback records its actual LU work without a completed pivot" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    diagnostics = JSimplex.SimplexDiagnostics(kernel_timing=true)
    ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    candidate = JSimplex._candidate_workspace(ws)
    JSimplex.apply_primal_pivot!(candidate,1,1,1.0,[-1.0],[-1.0,1.0];
        leaving_state=JSimplex.AT_UPPER)
    before = diagnostics.kernel_calls[:refactorization]
    JSimplex._discard_candidate!(ws,candidate)
    @test diagnostics.kernel_calls[:refactorization] == before+1
    @test ws.refactorizations == 1
    @test ws.iterations == 0
    @test JSimplex.event_count(diagnostics,:pivot_completed) == 0
end
