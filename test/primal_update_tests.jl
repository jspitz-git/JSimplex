using SparseArrays, LinearAlgebra

@testset "Primal bound flips preserve the basis and prices" begin
    @test isdefined(JSimplex, :apply_primal_flip!)
    if isdefined(JSimplex, :apply_primal_flip!)
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            p = LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1];
                row_upper=T[2], column_upper=T[1])
            w = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
            basis, factor = copy(w.basis.basic_indices), w.factorization
            costs, prices = copy(w.costs), copy(w.reduced_costs)
            weights = copy(w.pricing_weights)
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, one(T), T[-1]))
            @test w.primal == T[1, 1]
            @test w.basis.states[1] == JSimplex.AT_UPPER
            @test w.basis.basic_indices == basis
            @test w.factorization === factor
            @test (w.costs, w.reduced_costs, w.pricing_weights) == (costs, prices, weights)
            @test w.iterations == 0
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, -one(T), T[-1]))
            @test w.primal == T[0, 0]
            @test w.basis.states[1] == JSimplex.AT_LOWER
            @test w.basis.basic_indices == basis
            @test w.factorization === factor
            @test (w.costs, w.reduced_costs, w.pricing_weights) == (costs, prices, weights)
        end
    end
end

@testset "Flip updates retain stored precision and reject aliased directions" begin
    setprecision(BigFloat, 512) do
        coefficient = one(BigFloat) + BigFloat(2)^-400
        p = LinearProblem(sparse(reshape([coefficient], 1, 1)), BigFloat[-1];
            row_upper=BigFloat[2], column_upper=BigFloat[1])
        w = JSimplex.initialize_workspace(p, SolverOptions(BigFloat; verbose=false))
        column = [-coefficient]
        setprecision(BigFloat, 64) do
            JSimplex.apply_primal_flip!(w, 1, one(BigFloat), column)
            @test w.primal[2] == coefficient
            @test precision(w.primal[2]) >= 512
            @test precision(BigFloat) == 64
        end
    end
    p = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[2.0], column_upper=[1.0])
    w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
    w.primal[2] = -1.0
    before = copy(w.primal)
    @test_throws ArgumentError JSimplex.apply_primal_flip!(w, 1, 1.0, view(w.primal, 2:2))
    @test w.primal == before
end

function flip_workspace(::Type{T}=Float64; count=1, update=:pfi, backend=:native,
                        observer=nothing, adaptive=false, incremental=true) where T
    p = LinearProblem(sparse(ones(T, 1, count)), -ones(T, count);
        row_upper=T[count+1], column_upper=ones(T, count))
    options = SolverOptions(T; verbose=false, algorithm=:primal, pricing=:dantzig,
        presolve=false, basis_update=update, basis_refactorization=backend)
    policy = JSimplex.NumericalPolicy(T; simplex_strategy=adaptive ? :adaptive : :legacy,
        incremental_primal=incremental)
    d = JSimplex.SimplexDiagnostics(; observer, kernel_timing=true)
    w = JSimplex.initialize_workspace(p, options;
        progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy, diagnostics=d))
    for key in keys(d.kernel_calls)
        d.kernel_calls[key] = 0
    end
    return w, d
end

@testset "A completed flip has one FTRAN and no hidden recomputation" begin
    legacy, legacy_diagnostics = flip_workspace(; incremental=false)
    @test isnothing(JSimplex._primal_iteration!(legacy, ()->false, legacy.options.dual_tolerance))
    @test legacy.primal == [1.0, 1.0]
    @test legacy_diagnostics.kernel_calls[:ftran] == 2
    @test legacy_diagnostics.kernel_calls[:btran] == 1
    for adaptive in (false, true), update in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl),
        backend in (:native, :markowitz)
        w, d = flip_workspace(; adaptive, update, backend)
        factor = w.factorization
        @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
        @test w.primal == [1.0, 1.0]
        @test w.iterations == 1
        @test w.factorization === factor
        @test isempty(factor.updates)
        @test d.kernel_calls[:ftran] == 1
        @test d.kernel_calls[:btran] == 0
        @test JSimplex.event_count(d, :flip_completed) == 1
    end
end

@testset "A deadline before flip commit preserves the live state" begin
    for adaptive in (false, true)
        proposed = Ref(false)
        observer = (event, w) -> (event == :pivot_proposed && (proposed[] = true); nothing)
        w, d = flip_workspace(; observer, adaptive)
        before = (copy(w.primal), copy(w.basis.states), copy(w.reduced_costs))
        result = JSimplex._primal_iteration!(w, ()->proposed[], w.options.dual_tolerance)
        @test result.status == TIME_LIMIT
        @test (w.primal, w.basis.states, w.reduced_costs) == before
        @test w.iterations == 0
        @test JSimplex.event_count(d, :flip_completed) == 0
    end
end

@testset "Flip chains use periodic independent audits" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        w, d = flip_workspace(T; count=45)
        for i in 1:45
            @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
            @test w.primal[end] == T(i)
            @test sum(w.primal[1:45]) == w.primal[end]
        end
        @test w.iterations == 45
        @test d.kernel_calls[:btran] == 2
        @test w.primal == vcat(ones(T,45), T[45])
        @test w.reduced_costs == vcat(-ones(T,45), T[0])
    end
    @test isdefined(JSimplex, :audit_primal_values!)
    if isdefined(JSimplex, :audit_primal_values!)
        w, _ = flip_workspace()
        w.primal[end] = 0.25
        @test !JSimplex.audit_primal_values!(w)
        @test w.primal == [0.0, 0.0]
        @test JSimplex.audit_primal_values!(w)
    end
end

@testset "A zero flip changes no bound state or counter" begin
    if isdefined(JSimplex, :apply_primal_flip!)
        for upper in (0.0, 1.0)
            p = LinearProblem(sparse([1.0;;]), [-1.0];
                row_upper=[2.0], column_upper=[upper])
            w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
            before = (copy(w.primal), copy(w.basis.states), w.iterations)
            @test isnothing(JSimplex.apply_primal_flip!(w, 1, 0.0, [-1.0]))
            @test (w.primal, w.basis.states, w.iterations) == before
        end
    end
end

@testset "Unsafe flip predictions leave live values untouched" begin
    if isdefined(JSimplex, :apply_primal_flip!)
        p = LinearProblem(sparse([1.0;;]), [-1.0];
            row_upper=[nothing], column_upper=[2.0])
        w = JSimplex.initialize_workspace(p, SolverOptions(verbose=false))
        before = (copy(w.primal), copy(w.basis.states), w.iterations)
        @test_throws JSimplex._UnreliableBasisSolve JSimplex.apply_primal_flip!(
            w, 1, 2.0, [-floatmax(Float64)])
        @test (w.primal, w.basis.states, w.iterations) == before
        @test_throws ArgumentError JSimplex.apply_primal_flip!(w, 1, -2.0, [-1.0])
        @test (w.primal, w.basis.states, w.iterations) == before
        @test_throws DimensionMismatch JSimplex.apply_primal_flip!(w, 1, 2.0, Float64[])
        @test (w.primal, w.basis.states, w.iterations) == before
    end
end

@testset "Reverse flips and audits preserve completed work" begin
    w, d = flip_workspace(; count=25)
    for _ in 1:19
        JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance)
    end
    w.primal[end] += 0.25
    @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
    @test w.iterations == 20
    @test w.primal[end] == 20.0
    @test JSimplex.event_count(d, :flip_completed) == 20
    @test JSimplex.event_count(d, :pivot_rejected) > 0
    @test JSimplex.primal_infeasibility(w) == 0.0

    w, d = flip_workspace()
    JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance)
    w.costs[1] = 1.0
    JSimplex.recompute!(w)
    for key in keys(d.kernel_calls)
        d.kernel_calls[key] = 0
    end
    @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
    @test w.primal == [0.0, 0.0]
    @test w.iterations == 2
    @test w.basis.states[1] == JSimplex.AT_LOWER
    @test d.kernel_calls[:ftran] == 1
    @test d.kernel_calls[:btran] == 0
end

@testset "Boxed public solves retain Phase I and original-model certification" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}),
        pricing in (:dantzig, :devex, :steepest_edge), phase_one in (false, true)
        p = LinearProblem(sparse(ones(T, 1, 5)), -ones(T, 5);
            row_lower=T[phase_one ? 3 : 0], row_upper=T[6], column_upper=ones(T, 5))
        o = SolverOptions(T; algorithm=:primal, pricing, presolve=false,
            verbose=false, simplex_strategy=:adaptive)
        result = solve(p; options=o)
        @test result.status == OPTIMAL
        @test result.primal == ones(T, 5)
        @test result.objective_value == T(-5)
    end
    for limit in (0, 1, 5), presolve in (false, true)
        p = LinearProblem(sparse(ones(1, 5)), -ones(5);
            row_upper=[6.0], column_upper=ones(5))
        o = SolverOptions(; algorithm=:primal, pricing=:dantzig, presolve,
            verbose=false, iteration_limit=limit)
        policy = JSimplex.NumericalPolicy(Float64; incremental_primal=true)
        result = JSimplex._solve_diagnosed(p, nothing; options=o, numerical_policy=policy)
        @test result.status == (presolve || limit == 5 ? OPTIMAL : ITERATION_LIMIT)
        @test result.statistics.iterations <= limit
        if result.status == OPTIMAL
            @test result.primal == ones(5)
            @test result.objective_value == -5.0
        end
    end
end

@testset "Flip observers see a complete step and retain exception provenance" begin
    seen = Ref(false)
    failure = JSimplex.SingularException(17)
    observer = (event, ws) -> begin
        if event == :flip_completed
            @test ws.primal == [1.0, 1.0]
            @test ws.basis.states[1] == JSimplex.AT_UPPER
            @test ws.iterations == 1
            seen[] = true
            throw(failure)
        end
        nothing
    end
    w, d = flip_workspace(; observer)
    exception = try
        JSimplex._solve_diagnosed(w.problem, d; options=w.options,
            numerical_policy=w.progress.numerical_policy)
    catch e
        e
    end
    @test seen[]
    @test exception isa JSimplex.DiagnosticObserverFailure
    @test exception.cause === failure
end

@testset "The integrated flip retains a stored high-precision bound" begin
    setprecision(BigFloat, 512) do
        upper = one(BigFloat) + BigFloat(2)^-400
        p = LinearProblem(sparse(BigFloat[1;;]), BigFloat[-1];
            row_upper=BigFloat[2], column_upper=[upper])
        policy = JSimplex.NumericalPolicy(BigFloat; incremental_primal=true)
        w = JSimplex.initialize_workspace(p, SolverOptions(BigFloat; verbose=false, pricing=:dantzig);
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        setprecision(BigFloat, 64) do
            @test isnothing(JSimplex._primal_iteration!(w, ()->false, w.options.dual_tolerance))
            @test w.primal == [upper, upper]
            @test w.iterations == 1
            @test precision(BigFloat) == 64
        end
    end
end
