@testset "Refactorization safety precedes economics" begin
    policy = JSimplex.NumericalPolicy(Float64)
    state = JSimplex.RefactorizationState(nupdates=4, residual_bad=true,
        fresh_seconds=100.0, update_seconds=0.0)
    @test JSimplex.refactor_reason(state, policy) == :residual
    state.residual_bad = false
    @test JSimplex.refactor_reason(state, policy) == :none
    state.growth_scale = Inf
    state.stored_elements = 1000
    @test JSimplex.refactor_reason(state, policy) == :pivot_growth
    state.growth_scale = 1.0
    @test JSimplex.refactor_reason(state, policy) == :fill
    state.stored_elements = 1
    state.nupdates = state.hard_ceiling
    @test JSimplex.refactor_reason(state, policy) == :limit

    for interval in (1, 20, 100, typemax(Int))
        state = JSimplex.RefactorizationState(initial_interval=interval)
        state.nupdates = interval - 1
        @test JSimplex.refactor_reason(state, policy) == :none
        state.nupdates = interval
        @test JSimplex.refactor_reason(state, policy) == :limit
    end
end

@testset "Both simplex methods share deterministic refactorization state" begin
    for T in (Float32,Float64,Rational{BigInt}), algorithm in (:primal,:dual),
        update in (:pfi,:forrest_tomlin)
        n = 48
        A = JSimplex.spdiagm(0=>ones(T,n))
        p = algorithm == :primal ?
            LinearProblem(A,-ones(T,n);row_upper=ones(T,n)) :
            LinearProblem(A,ones(T,n);row_lower=ones(T,n))
        options = SolverOptions(T;verbose=false,presolve=false,algorithm,
            pricing=:dantzig,basis_update=update,refactorization_interval=4)
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            adaptive_refactor=true,refactor_timing=false)
        ws = JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        state = ws.scratch.refactorization
        @test state.initial_interval == 4
        @test !state.timing_enabled
        for _ in 1:n
            terminal = algorithm == :primal ?
                JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance) :
                JSimplex._dual_iteration!(ws,()->false)
            @test isnothing(terminal)
            @test ws.scratch.refactorization === state
            @test state.nupdates == length(ws.factorization.updates)
        end
        @test ws.primal[1:n] == ones(T,n)
        @test ws.iterations == n
        @test (state.fresh_samples,state.update_samples,state.factor_samples) == (0,0,0)
        if T <: Rational
            @test state.interval == 4
            @test ws.refactorizations == n ÷ 4
        else
            @test state.interval > 4
            @test ws.refactorizations < n ÷ 4
        end
    end
end

@testset "Refactorization costs require usable evidence" begin
    policy = JSimplex.NumericalPolicy(Float64)
    state = JSimplex.RefactorizationState(nupdates=8, initial_interval=40)
    for seconds in (0.0, -1.0, NaN, Inf)
        @test JSimplex.record_basis_cost!(state, :fresh, seconds) === nothing
        JSimplex.record_basis_cost!(state, :update, seconds)
        JSimplex.record_basis_cost!(state, :refactorization, seconds)
    end
    @test (state.fresh_samples, state.update_samples, state.factor_samples) == (0,0,0)
    @test JSimplex.refactor_reason(state, policy) == :none
    JSimplex.record_basis_cost!(state, :refactorization, 1.0)
    JSimplex.record_basis_cost!(state, :fresh, 0.01)
    JSimplex.record_basis_cost!(state, :update, 1.0)
    @test JSimplex.refactor_reason(state, policy) == :none
    for _ in 1:3
        JSimplex.record_basis_cost!(state, :fresh, 0.01)
        JSimplex.record_basis_cost!(state, :update, 1.0)
    end
    @test JSimplex.refactor_reason(state, policy) == :cost
    state.update_seconds = state.fresh_seconds / 2
    @test JSimplex.refactor_reason(state, policy) == :none
    state.update_seconds = floatmax(Float64)
    @test JSimplex.refactor_reason(state, policy) == :cost
    state.residual_bad = true
    @test JSimplex.refactor_reason(state, policy) == :residual
    @test_throws ArgumentError JSimplex.record_basis_cost!(state, :unknown, 1.0)

    tiny = JSimplex.RefactorizationState(nupdates=8)
    for _ in 1:8
        JSimplex.record_basis_cost!(tiny, :fresh, 1e-9)
        JSimplex.record_basis_cost!(tiny, :update, 1e-8)
        JSimplex.record_basis_cost!(tiny, :refactorization, 1e-8)
    end
    @test JSimplex.refactor_reason(tiny, policy) == :none
end

@testset "Refactorization intervals recover conservatively" begin
    state = JSimplex.RefactorizationState(initial_interval=20, hard_ceiling=80)
    for _ in 1:2
        JSimplex.record_refactor_cycle!(state; reliable=true, productive=true)
        @test state.interval == 20
    end
    JSimplex.record_refactor_cycle!(state; reliable=true, productive=true)
    @test state.interval == 40
    for _ in 1:30
        JSimplex.record_refactor_cycle!(state; reliable=true, productive=true)
    end
    @test state.interval == 80
    state.nupdates = 8
    JSimplex.record_refactor_cycle!(state; reliable=false, productive=true)
    @test state.interval == 80
    state.nupdates = 6
    JSimplex.record_refactor_cycle!(state; reliable=false, productive=false)
    @test state.interval == 3
    for _ in 1:12
        JSimplex.record_refactor_cycle!(state; reliable=true, productive=false)
    end
    @test state.interval == 3
    for _ in 1:3
        JSimplex.record_refactor_cycle!(state; reliable=true, productive=true)
    end
    @test state.interval == 6

    huge = JSimplex.RefactorizationState(initial_interval=typemax(Int))
    for _ in 1:6
        JSimplex.record_refactor_cycle!(huge; reliable=true, productive=true)
    end
    @test huge.interval == typemax(Int)
    exact = JSimplex.RefactorizationState(Rational{BigInt}; initial_interval=7)
    for _ in 1:12
        JSimplex.record_refactor_cycle!(exact; reliable=true, productive=true)
    end
    @test exact.interval == 7
    exact.nupdates = 6
    exact.growth_scale = Inf
    exact.stored_elements = typemax(Int)
    @test JSimplex.refactor_reason(exact, JSimplex.NumericalPolicy(Rational{BigInt})) == :none
    exact.nupdates = 7
    @test JSimplex.refactor_reason(exact, JSimplex.NumericalPolicy(Rational{BigInt})) == :limit
end
