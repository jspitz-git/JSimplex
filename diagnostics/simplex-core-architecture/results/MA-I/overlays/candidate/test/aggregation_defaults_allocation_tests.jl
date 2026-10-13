using SparseArrays

function aggregation_defaults_problem(::Type{T}, count, sparse_pass) where {T}
    A = hcat(sparse(1:count, 1:count, ones(T, count), count, count), sparse(ones(T, count, 1)))
    lower = Union{Nothing,T}[one(T) for _ in 1:count]
    upper = ones(T, count)
    if sparse_pass
        A = vcat(A, sparse(reshape([ones(T, count); T(2)], 1, count + 1)))
        push!(lower, nothing)
        push!(upper, T(100))
    end
    return LinearProblem(A, [ones(T, count); T(2)]; row_lower=lower, row_upper=upper,
                         column_lower=fill(nothing, count + 1))
end

@testset "Aggregation skips unused exact defaults" begin
    for (sparse_pass, pass, budget) in ((false, JSimplex.aggregate_singleton_equalities, 360_000),
                                       (true, JSimplex.aggregate_sparse_equalities, 710_000))
        problem = aggregation_defaults_problem(Float64, 64, sparse_pass)
        pass(problem)
        @test (@allocated pass(problem)) <= budget
    end
end

@testset "Aggregation uses committed objective and matrix updates" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), count in (1, 3)
        for sparse_pass in (false, true)
            problem = aggregation_defaults_problem(T, count, sparse_pass)
            matrix = copy(problem.A)
            pass = sparse_pass ? JSimplex.aggregate_sparse_equalities : JSimplex.aggregate_singleton_equalities
            result = pass(problem)
            @test result.problem.objective == T[count == 1 ? 1 : -1]
            @test result.problem.objective_constant == T(count)
            @test length(only(result.postsolve_stack).records) == count
            @test only(result.postsolve_stack).map.columns == [count + 1]
            restored = JSimplex.postsolve_primal(result, T[3])
            @test restored == [fill(T(-2), count); T(3)]
            @test sum(problem.objective .* restored) == T(count == 1 ? 4 : 0)
            @test problem.A == matrix
            @test problem.objective == [ones(T, count); T(2)]
            if sparse_pass
                @test result.problem.A == reshape(T[count == 1 ? 1 : -1], 1, 1)
                @test !isfinite(only(result.problem.row_lower))
                @test bound_value(only(result.problem.row_upper)) == T(100 - count)
            else
                @test result.problem.A == ones(T, count, 1)
                @test all(!isfinite, result.problem.row_lower)
                @test all(!isfinite, result.problem.row_upper)
            end
        end
    end
end
