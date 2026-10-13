using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

function safety_workspace(algorithm; adaptive=false, rows=12, T=Float64, update=:pfi, interval=50)
    A = sparse(Matrix{T}(I, rows, rows))
    p = algorithm == :primal ?
        LinearProblem(A, -collect(T, 1:rows); row_upper=ones(T, rows)) :
        LinearProblem(A, collect(T, 1:rows); row_lower=ones(T, rows))
    options = SolverOptions(T; algorithm, pricing=:dantzig, basis_update=update,
        refactorization_interval=interval, verbose=false)
    policy = JSimplex.NumericalPolicy(T; adaptive_refactor=adaptive, refactor_timing=false)
    return JSimplex.initialize_workspace(p, options;
        progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
end

function safety_step!(ws)
    return ws.options.algorithm == :primal ?
        JSimplex._primal_iteration!(ws, () -> false, ws.options.dual_tolerance) :
        JSimplex.dual_iteration!(ws, () -> false)
end

function damage_safety_factors!(ws, row; age=1)
    # Replace the represented basis by one with a tenfold diagonal error.
    # A no-op update makes this an updated solve, rather than a fresh LU failure.
    stale = Matrix(JSimplex.basis_matrix(ws))
    stale[row, row] *= 10
    JSimplex.refactorize!(ws.factorization, sparse(stale))
    identity_column = zeros(eltype(ws.costs), size(stale, 1))
    identity_column[1] = 1
    for _ in 1:age
        JSimplex.replace_column!(ws.factorization, identity_column, 1)
    end
    JSimplex.recompute!(ws)
end

@testset "Both native methods shorten after repeated inaccurate updated solves" begin
    for algorithm in (:primal, :dual), adaptive in (false, true), T in (Float32, Float64),
        update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        ws = safety_workspace(algorithm; adaptive, T, update)
        # Primal Dantzig visits decreasing costs, dual visits increasing row ties.
        first_row = algorithm == :primal ? 12 : 1
        second_row = algorithm == :primal ? 11 : 2
        damage_safety_factors!(ws, first_row)
        @test isnothing(safety_step!(ws))
        @test ws.dual_refactorization_interval == 50
        @test ws.refactorizations == 1
        damage_safety_factors!(ws, second_row)
        @test isnothing(safety_step!(ws))
        @test ws.dual_refactorization_interval == 1
        adaptive && @test ws.scratch.refactorization.interval == 50
        @test isempty(ws.factorization.updates)
        @test isnothing(safety_step!(ws))
        @test ws.dual_refactorization_interval == 2
        @test JSimplex.primal_infeasibility(ws) <= (algorithm == :primal ? ws.options.primal_tolerance : 9)
        @test ws.options.refactorization_interval == 50
    end
end

@testset "Adaptive economics cannot overrule the numerical limit" begin
    for algorithm in (:primal, :dual)
        ws = safety_workspace(algorithm; adaptive=true, rows=100)
        for row in (algorithm == :primal ? (100, 99) : (1, 2))
            damage_safety_factors!(ws, row)
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 1
        # Model an economic preference for the longest permitted update chain.
        state = ws.scratch.refactorization
        state.interval = state.hard_ceiling
        before = ws.refactorizations
        @test isnothing(safety_step!(ws))
        @test ws.refactorizations == before + 1
        @test ws.dual_refactorization_interval == 2
        for _ in 4:100
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 50
        @test JSimplex.primal_infeasibility(ws) == 0
        @test JSimplex.dual_infeasibility(ws) == 0
    end
end

@testset "Degeneracy and cautious small-pivot refreshes do not count as factor failures" begin
    for adaptive in (false, true), weak_preference in (false, true)
        # Independent zero-length pivots in highly scaled columns. Each aged
        # factor triggers the existing cautious refresh, with no bad residual.
        A = sparse([1e-8 0.0; 1e9 0.0; 0.0 1e-8; 0.0 1e9])
        p = LinearProblem(A, [-2.0, -1.0]; row_upper=[0.0, Inf, 0.0, Inf],
            column_upper=ones(2))
        options = SolverOptions(algorithm=:primal, pricing=:dantzig,
            refactorization_interval=50, verbose=false)
        policy = JSimplex.NumericalPolicy(Float64; adaptive_refactor=adaptive,
            adaptive_pricing=weak_preference, refactor_timing=false)
        ws = JSimplex.initialize_workspace(p, options;
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        # Isolate the cautious pivot trigger from independent adaptive
        # factor-growth/storage heuristics on these extremely scaled columns.
        ws.scratch.refactorization.growth_limit = Inf
        ws.scratch.refactorization.fill_limit = Inf
        for _ in 1:2
            JSimplex.replace_column!(ws.factorization, [1.0,0,0,0], 1)
            @test isnothing(safety_step!(ws))
            @test ws.scratch.last_primal_step == 0
            @test ws.dual_recent_repairs == 0
            @test ws.dual_refactorization_interval == 50
        end
        @test ws.refactorizations >= 2
        adaptive && @test ws.scratch.refactorization.interval == 50
    end
    for adaptive in (false, true)
        p = LinearProblem(sparse(Matrix{Float64}(I, 12, 12)), zeros(12); row_lower=ones(12))
        options = SolverOptions(algorithm=:dual, verbose=false, refactorization_interval=4)
        policy = JSimplex.NumericalPolicy(Float64; adaptive_refactor=adaptive, refactor_timing=false)
        ws = JSimplex.initialize_workspace(p, options;
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        for _ in 1:12
            @test isnothing(safety_step!(ws))
            @test ws.scratch.last_dual_step == 0
            @test ws.dual_recent_repairs == 0
            @test min(ws.dual_refactorization_interval, options.refactorization_interval) == 4
        end
    end
end

@testset "Fresh factor failures cannot repeatedly shorten the update limit" begin
    for algorithm in (:primal, :dual), adaptive in (false, true)
        ws = safety_workspace(algorithm; adaptive)
        stale = Matrix(JSimplex.basis_matrix(ws))
        # No update chain exists: a shorter chain cannot repair this error.
        stale .*= 10
        for _ in 1:2
            JSimplex.refactorize!(ws.factorization, sparse(stale))
            terminal = algorithm == :primal ?
                JSimplex._primal_iteration_unchecked!(ws, () -> false, ws.options.dual_tolerance, true) :
                JSimplex._dual_iteration_unchecked!(ws, () -> false, true)
            @test isnothing(terminal) || terminal.status == JSimplex.NUMERICAL_ERROR
            @test ws.dual_recent_repairs == 0
            @test ws.dual_refactorization_interval == 50
        end
    end
end

@testset "Numerical triggers outrank a coincident safety ceiling" begin
    for algorithm in (:primal, :dual)
        ws = safety_workspace(algorithm; adaptive=true)
        for row in (algorithm == :primal ? (12, 11) : (1, 2))
            damage_safety_factors!(ws, row)
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 1
        JSimplex.replace_column!(ws.factorization, [1.0; zeros(11)], 1)
        ws.scratch.refactorization.growth_limit = 0.0
        @test JSimplex._scheduled_refactor_reason(ws, algorithm) == :pivot_growth
        @test isnothing(safety_step!(ws))
        # The basis was rebuilt, but the preceding cycle was not healthy.
        @test ws.dual_refactorization_interval == 1
    end
end

@testset "Late adaptive failures can impose the configured ceiling" begin
    for algorithm in (:primal, :dual)
        ws = safety_workspace(algorithm; adaptive=true)
        state = ws.scratch.refactorization
        state.interval = state.hard_ceiling
        for row in (algorithm == :primal ? (12, 11) : (1, 2))
            damage_safety_factors!(ws, row; age=120)
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 50
        # A shorter economic cycle has not demonstrated a safe 50-update chain.
        state.interval = 4
        for _ in 1:3
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 50
        state.interval = state.hard_ceiling
        while length(ws.factorization.updates) < 50
            JSimplex.replace_column!(ws.factorization, [1.0; zeros(11)], 1)
        end
        @test JSimplex._scheduled_refactor_reason(ws, algorithm) == :limit
        before = ws.refactorizations
        @test isnothing(safety_step!(ws))
        @test ws.refactorizations == before + 1
        # A completed clean cycle at the configured ceiling may release it.
        while length(ws.factorization.updates) < 50
            JSimplex.replace_column!(ws.factorization, [1.0; zeros(11)], 1)
        end
        @test JSimplex._scheduled_refactor_reason(ws, algorithm) == :none
    end
end

@testset "A configured one-update ceiling can be reapplied after adaptive release" begin
    for algorithm in (:primal, :dual)
        ws = safety_workspace(algorithm; adaptive=true, interval=1)
        @test isnothing(safety_step!(ws))
        @test isempty(ws.factorization.updates)
        ws.scratch.refactorization.interval = ws.scratch.refactorization.hard_ceiling
        for row in (algorithm == :primal ? (11, 10) : (2, 3))
            damage_safety_factors!(ws, row; age=3)
            @test isnothing(safety_step!(ws))
        end
        @test ws.dual_refactorization_interval == 1
        @test isempty(ws.factorization.updates)
        @test isnothing(safety_step!(ws))
        @test ws.dual_refactorization_interval == typemax(Int)
    end
end

@testset "Sensitive small pivots do not imply inaccurate updated solves" begin
    for adaptive in (false, true)
        p = LinearProblem(sparse([0.0 0.0; 1e9 0.0; 0.0 0.0; 0.0 1e9]),
            [-2.0, -1.0]; row_upper=[0.0, Inf, 0.0, Inf], column_upper=ones(2))
        options = SolverOptions(algorithm=:primal, pricing=:dantzig,
            refactorization_interval=80, verbose=false)
        policy = JSimplex.NumericalPolicy(Float64; adaptive_refactor=adaptive,
            refactor_timing=false)
        ws = JSimplex.initialize_workspace(p, options;
            progress=JSimplex.SimplexProgressContext(p; numerical_policy=policy))
        for row in (1, 3)
            stale = Matrix(JSimplex.basis_matrix(ws))
            # A tiny perturbation passes the ordinary backward-error check,
            # yet creates an unsafe pivot in a highly scaled entering column.
            stale[row, row + 1] = 1e-14
            JSimplex.refactorize!(ws.factorization, sparse(stale))
            JSimplex.replace_column!(ws.factorization, [1.0, 0, 0, 0], 1)
            JSimplex.recompute!(ws)
            @test isnothing(safety_step!(ws))
            @test ws.dual_recent_repairs == 0
            @test ws.dual_refactorization_interval == 80
        end
        @test ws.refactorizations == 2
        adaptive && @test ws.scratch.refactorization.interval == 80
        @test ws.primal[1:2] == ones(2)
        @test JSimplex.primal_infeasibility(ws) == 0
    end
end
