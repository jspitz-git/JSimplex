@testset "Original-basis restoration avoids intermediate copies" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1024, 1024), zeros(1024);
                            row_lower=ones(1024))
    options = SolverOptions(algorithm=:primal, verbose=false)
    workspace, count, _ = JSimplex._primal_phase_one(
        problem, options, JSimplex.SimplexProgressContext(problem), () -> false)
    JSimplex._primal_original_basis(workspace, 1024, count)
    @test (@allocated JSimplex._primal_original_basis(workspace, 1024, count)) <= 12_000
end

@testset "Original-basis restoration maps mixed columns and owns its storage" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        # Original columns 1:2, artificial columns 3:4, row activities 5:7.
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[1 0 0 0; 0 1 1 0; 0 0 0 -1]),
                                T[0, 0, 1, 1])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
        workspace.basis = JSimplex.Basis([1, 3, 7],
            [JSimplex.BASIC, JSimplex.AT_UPPER, JSimplex.BASIC, JSimplex.AT_LOWER,
             JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.BASIC])
        original_indices = copy(workspace.basis.basic_indices)
        original_states = copy(workspace.basis.states)
        restored = JSimplex._primal_original_basis(workspace, 2, 2)
        @test restored.basic_indices == [1, 4, 5]
        @test restored.states == [JSimplex.BASIC, JSimplex.AT_UPPER, JSimplex.AT_LOWER,
                                  JSimplex.BASIC, JSimplex.BASIC]
        another = JSimplex._primal_original_basis(workspace, 2, 2)
        restored.basic_indices[1] = 2
        restored.states[1] = JSimplex.FREE_NONBASIC
        @test workspace.basis.basic_indices == original_indices
        @test workspace.basis.states == original_states
        @test another.basic_indices == [1, 4, 5]
        @test another.states[1] == JSimplex.BASIC

        # Replacing the artificial column would collide with an existing slack.
        workspace.basis = JSimplex.Basis([3, 6, 7],
            [JSimplex.AT_LOWER, JSimplex.AT_UPPER, JSimplex.BASIC, JSimplex.AT_LOWER,
             JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.BASIC])
        collision_indices = copy(workspace.basis.basic_indices)
        collision_states = copy(workspace.basis.states)
        @test JSimplex._primal_original_basis(workspace, 2, 2) === nothing
        @test workspace.basis.basic_indices == collision_indices
        @test workspace.basis.states == collision_states

        no_artificials = JSimplex._primal_original_basis(workspace, 4, 0)
        @test no_artificials.basic_indices == collision_indices
        @test no_artificials.states == collision_states
        @test no_artificials.basic_indices !== workspace.basis.basic_indices
        @test no_artificials.states !== workspace.basis.states
    end
end

@testset "Basis construction retains input-copy semantics" begin
    indices = [1, 3]
    states = [JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC]
    basis = @inferred JSimplex.Basis(indices, states)
    indices[1] = 2
    states[1] = JSimplex.AT_UPPER
    @test basis.basic_indices == [1, 3]
    @test basis.states == [JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC]
end

@testset "Original-basis restoration handles empty original columns" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for rows in (0, 2)
            problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, rows, 0), T[];
                                    row_lower=ones(T, rows))
            options = SolverOptions(T;algorithm=:primal, verbose=false)
            workspace, count, _ = JSimplex._primal_phase_one(
                problem, options, JSimplex.SimplexProgressContext(problem), () -> false)
            restored = JSimplex._primal_original_basis(workspace, 0, count)
            @test restored.basic_indices == collect(1:rows)
            @test restored.states == fill(JSimplex.BASIC, rows)
        end
    end
end
