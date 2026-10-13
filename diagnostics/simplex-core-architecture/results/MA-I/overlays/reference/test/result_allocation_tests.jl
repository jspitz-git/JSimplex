@testset "Result construction avoids duplicate vectors" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 0, 1024), zeros(1024))
    presolved = JSimplex.identity_presolve(problem)
    primal = zeros(1024)
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    JSimplex.postsolve_primal(presolved, primal)
    JSimplex._internal_solution(workspace, OPTIMAL, "optimal")
    @test (@allocated JSimplex.postsolve_primal(presolved, primal)) <= 10_000
    @test (@allocated JSimplex._internal_solution(workspace, OPTIMAL, "optimal")) <= 71_000
end

@testset "Postsolve returns independent values and preserves truncation" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 3), zeros(T, 3))
        presolved = JSimplex.identity_presolve(problem)
        parent = T[0, 1, 2, 3, 0]
        for input in (T[1, 2, 3], [1, 2, 3], 1:3, @view(parent[2:4]))
            restored = JSimplex.postsolve_primal(presolved, input)
            @test restored == T[1, 2, 3]
            @test eltype(restored) === T
            restored[1] = T(9)
            @test input[1] == 1
            @test JSimplex.postsolve_primal(presolved, input) == T[1, 2, 3]
        end
        @test parent == T[0, 1, 2, 3, 0]
        longer = T[1, 2, 3, 4]
        trimmed = JSimplex.postsolve_primal(presolved, longer)
        @test trimmed == T[1, 2, 3]
        trimmed[1] = T(9)
        @test longer == T[1, 2, 3, 4]
        @test_throws BoundsError JSimplex.postsolve_primal(presolved, T[1, 2])
        sparse_input = JSimplex.SparseArrays.sparsevec([1, 3], T[1, 3], 3)
        sparse_result = JSimplex.postsolve_primal(presolved, sparse_input)
        @test sparse_result isa JSimplex.SparseArrays.SparseVector{T}
        @test sparse_result == T[1, 0, 3]
        sparse_result[1] = T(9)
        @test sparse_input[1] == T(1)
    end
end

@testset "Postsolve chains retain independent reconstructed values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[1, 1], 1, 2)), T[1, 2];
            row_lower=T[5], column_lower=T[2, 0], column_upper=[T(2), nothing])
        reduced = JSimplex._presolve_basic(problem)
        chained = JSimplex._compose_presolve(reduced, JSimplex.reduce_singleton_rows(reduced.problem))
        input = T[3]
        restored = JSimplex.postsolve_primal(chained, input)
        @test restored == T[2, 3]
        restored[1] = T(9)
        @test input == T[3]
        @test JSimplex.postsolve_primal(chained, input) == T[2, 3]
    end
end

@testset "Internal solution primal storage is independent of workspace" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 3), zeros(T, 3))
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
        workspace.primal .= T[1, 2, 3]
        result = JSimplex._internal_solution(workspace, OPTIMAL, "optimal")
        @test result.status == OPTIMAL
        @test result.primal == T[1, 2, 3]
        result.primal[1] = T(9)
        @test workspace.primal == T[1, 2, 3]
        workspace.primal[2] = T(8)
        @test result.primal == T[9, 2, 3]
        @test isnothing(JSimplex._internal_solution(workspace, INFEASIBLE, "infeasible").primal)
    end
end
