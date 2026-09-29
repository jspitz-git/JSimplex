using JSimplex.SparseArrays

function tolerated_row_workspace(::Type{T}, sign, update=:bartels_golub;
                                  algorithm=:primal, strategy=:legacy) where {T}
    problem = LinearProblem(sparse(T(sign) .* T[-7e-8 -0.01]), T[0, -1];
        row_lower=T[sign > 0 ? 0 : -Inf], row_upper=T[sign > 0 ? Inf : 0],
        column_lower=T[1, 0], column_upper=T[1, Inf])
    options = SolverOptions(T; algorithm, simplex_strategy=strategy,
        basis_update=update, primal_tolerance=T(1e-7), verbose=false)
    return JSimplex.initialize_workspace(problem, options)
end

@testset "Legacy primal zero steps preserve tolerated row activity" begin
    for T in (Float32, Float64), sign in (-1, 1), update in (:pfi, :bartels_golub)
        workspace = tolerated_row_workspace(T, sign, update)
        old = workspace.primal[3]
        terminal = JSimplex._primal_iteration!(workspace, () -> false,
            workspace.options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.basis.basic_indices == [2]
        @test workspace.primal[3] == old
        @test abs(workspace.primal[2]) <= eps(T)
        @test JSimplex._original_primal_feasible(workspace, workspace.primal[1:2])
        JSimplex.recompute!(workspace; refactorize=true)
        @test workspace.primal[3] == old
        @test abs(workspace.primal[2]) <= eps(T)
        bound = sign > 0 ? workspace.lower[3] : workspace.upper[3]
        @test JSimplex.bound_value(bound) == zero(T)
    end
end

@testset "Tolerated row values survive recomputation only within their scope" begin
    for T in (Float32, Float64), sign in (-1, 1)
        workspace = tolerated_row_workspace(T, sign)
        old = workspace.primal[3]
        workspace.basis.basic_indices[1] = 2
        workspace.basis.states[2] = JSimplex.BASIC
        workspace.basis.states[3] = sign > 0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
        workspace.iterations = 1
        JSimplex.recompute!(workspace; refactorize=true)
        @test workspace.primal[3] == old
        @test abs(workspace.primal[2]) <= eps(T)
        workspace.iterations = 0
        @test JSimplex._nonbasic_value(workspace, 3) == zero(T)
        workspace.iterations = 1
        workspace.primal[3] = T(-sign * 2e-7)
        @test JSimplex._nonbasic_value(workspace, 3) == zero(T)
        workspace.primal[1] = one(T) - eps(T)
        @test JSimplex._nonbasic_value(workspace, 1) == one(T)
    end
    workspace = tolerated_row_workspace(Float64, 1)
    workspace.basis.states[3] = JSimplex.AT_LOWER
    workspace.iterations = 1
    # A shifted working bound cannot authorize a value outside the model bound.
    workspace.lower[3] = Bound(-1e-5)
    workspace.primal[3] = -1e-5 - 7e-8
    @test JSimplex._nonbasic_value(workspace, 3) == -1e-5
    for (algorithm, strategy) in ((:dual, :legacy), (:primal, :adaptive))
        workspace = tolerated_row_workspace(Float64, 1; algorithm, strategy)
        workspace.basis.states[3] = JSimplex.AT_LOWER
        workspace.iterations = 1
        @test JSimplex._nonbasic_value(workspace, 3) == (algorithm == :primal ? workspace.primal[3] : 0.0)
    end
end
