using SparseArrays

function refactor_timing_workspace()
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    policy = JSimplex.NumericalPolicy(Float64;adaptive_refactor=true,refactor_timing=false)
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    w.scratch.refactorization.timing_enabled = true
    return w
end

@testset "Economic sampling covers complete work without duplicate samples" begin
    ws = refactor_timing_workspace()
    state = ws.scratch.refactorization
    ticks = UInt64[0,2_000_000_000]
    clock = ()->popfirst!(ticks)
    JSimplex._measure_basis_iteration!(ws;clock) do
        JSimplex._measure_basis_iteration!(ws;clock) do
            ws.iterations += 1
        end
    end
    @test isempty(ticks)
    @test state.fresh_samples == 1
    @test state.fresh_seconds == 2.0
    @test state.work_seconds == 2.0
    @test state.timing_depth == 0

    ticks = UInt64[0,500_000_000,1_500_000_000,2_000_000_000]
    JSimplex._measure_basis_iteration!(ws;clock) do
        JSimplex._measure_basis_factorization!(ws;clock) do
            ws.refactorizations += 1
        end
        ws.iterations += 1
    end
    @test isempty(ticks)
    @test state.fresh_samples == 1 # a refactorizing step is not a fresh-solve sample
    @test state.factor_samples == 1
    @test state.factor_seconds == 1.0
    @test state.work_seconds == 4.0

    ticks = UInt64[0,1_000_000_000]
    @test_throws ErrorException JSimplex._measure_basis_iteration!(ws;clock) do
        error("injected caller failure")
    end
    @test state.work_seconds == 5.0
    @test state.fresh_samples == 1
    @test state.timing_depth == 0
    state.timing_enabled = false
    @test JSimplex._measure_basis_iteration!(() -> 7,ws;clock=()->error("clock disabled")) == 7
    @test JSimplex._measure_basis_factorization!(() -> 9,ws;clock=()->error("clock disabled")) == 9
end

@testset "Unknown numerical quality does not count as a failed cycle" begin
    n = 12
    p = LinearProblem(spdiagm(0=>ones(n)),-ones(n);row_upper=ones(n))
    policy = JSimplex.NumericalPolicy(Float64;adaptive_refactor=true,refactor_timing=false)
    options = SolverOptions(verbose=false,pricing=:dantzig,refactorization_interval=4)
    ws = JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    for _ in 1:n
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
    end
    @test ws.scratch.refactorization.interval == 4
    @test ws.scratch.refactorization.recent_failures == 0
    @test ws.refactorizations == 3
end
