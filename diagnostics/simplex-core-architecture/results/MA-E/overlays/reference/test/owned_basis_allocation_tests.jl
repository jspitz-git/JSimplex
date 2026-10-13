@testset "Owned basis arrays avoid initialization and restoration copies" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 0, 8192), zeros(8192))
    options = SolverOptions(verbose=false)
    JSimplex.initialize_workspace(problem, options)
    @test (@allocated JSimplex.initialize_workspace(problem, options)) <= 869_000

    n = m = 1024
    step = JSimplex.PresolveMap{Float64}(collect(1:m), collect(1:n),
        fill!(Vector{Union{Nothing,Float64}}(undef, n), nothing), fill(JSimplex.AT_LOWER, n), m)
    basis = JSimplex.Basis(collect(n+1:n+m),
        vcat(fill(JSimplex.AT_LOWER, n), fill(JSimplex.BASIC, m)))
    JSimplex.restore_basis(step, basis)
    @test (@allocated JSimplex.restore_basis(step, basis)) <= 12_000
end

@testset "Initial bases own their indices and states" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[1 0 0; 0 1 0]), zeros(T, 3);
            column_lower=[T(0), nothing, nothing], column_upper=[nothing, T(4), nothing])
        options = SolverOptions(T;verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        another = JSimplex.initialize_workspace(problem, options)
        expected = [JSimplex.AT_LOWER, JSimplex.AT_UPPER, JSimplex.FREE_NONBASIC,
                    JSimplex.BASIC, JSimplex.BASIC]
        @test workspace.basis.basic_indices == [4, 5]
        @test workspace.basis.states == expected
        @test workspace.basis.basic_indices !== another.basis.basic_indices
        @test workspace.basis.states !== another.basis.states
        workspace.basis.basic_indices[1] = 1
        workspace.basis.states[1] = JSimplex.BASIC
        @test another.basis.basic_indices == [4, 5]
        @test another.basis.states == expected
        @test problem.objective == zeros(T, 3)
    end
end

@testset "Presolve basis restoration maps rows and columns without sharing" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        step = JSimplex.PresolveMap{T}([1, 3], [2, 4],
            Union{Nothing,T}[T(1), nothing, T(0), nothing],
            [JSimplex.AT_LOWER, JSimplex.FREE_NONBASIC, JSimplex.AT_UPPER, JSimplex.AT_LOWER], 3)
        basis = JSimplex.Basis([1, 4],
            [JSimplex.BASIC, JSimplex.FREE_NONBASIC, JSimplex.AT_UPPER, JSimplex.BASIC])
        original_indices, original_states = copy(basis.basic_indices), copy(basis.states)
        removed_states = copy(step.removed_states)
        restored = @inferred JSimplex.restore_basis(step, basis)
        expected_states = [JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.AT_UPPER,
            JSimplex.FREE_NONBASIC, JSimplex.AT_UPPER, JSimplex.BASIC, JSimplex.BASIC]
        @test restored.basic_indices == [2, 6, 7]
        @test restored.states == expected_states
        again = JSimplex.restore_basis(step, basis)
        restored.basic_indices[1] = 4
        restored.states[1] = JSimplex.AT_UPPER
        @test basis.basic_indices == original_indices
        @test basis.states == original_states
        @test step.removed_states == removed_states
        @test again.basic_indices == [2, 6, 7]
        @test again.states == expected_states

        inner = JSimplex.PresolveMap{T}([2], [1], Union{Nothing,T}[nothing, T(3)],
                                       [JSimplex.AT_LOWER, JSimplex.AT_UPPER], 2)
        reduced = JSimplex.Basis([1], [JSimplex.BASIC, JSimplex.AT_LOWER])
        chained = JSimplex._restore_basis((step, inner), reduced)
        @test chained.basic_indices == [5, 6, 2]
        @test chained.states == [JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.AT_UPPER,
            JSimplex.AT_UPPER, JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER]
        @test reduced.basic_indices == [1]
        @test reduced.states == [JSimplex.BASIC, JSimplex.AT_LOWER]
        identity = JSimplex._restore_basis((), reduced)
        @test identity.basic_indices == reduced.basic_indices
        @test identity.states == reduced.states
        @test identity.basic_indices !== reduced.basic_indices
        @test identity.states !== reduced.states
    end
end

@testset "Owned basis construction handles empty dimensions" begin
    for (rows, columns) in ((0, 0), (0, 3), (3, 0))
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, rows, columns), zeros(columns))
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
        @test workspace.basis.basic_indices == collect(columns+1:columns+rows)
        @test workspace.basis.states == vcat(fill(JSimplex.AT_LOWER, columns), fill(JSimplex.BASIC, rows))
        step = JSimplex.PresolveMap{Float64}(Int[], Int[],
            Union{Nothing,Float64}[0.0 for _ in 1:columns], fill(JSimplex.AT_LOWER, columns), rows)
        restored = JSimplex.restore_basis(step, JSimplex.Basis(Int[], JSimplex.VariableState[]))
        @test restored.basic_indices == workspace.basis.basic_indices
        @test restored.states == workspace.basis.states
    end
end
