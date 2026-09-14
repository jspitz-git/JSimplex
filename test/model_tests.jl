@testset "LinearProblem" begin
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse([1.0 2.0]), [1.0],
    )

    A = JSimplex.SparseArrays.sparse(
        [1, 1, 2], [1, 2, 2], [1.0, 2.0, -1.0], 2, 2,
    )
    problem = LinearProblem(
        A, [3.0, 4.0];
        row_lower=[1.0, -Inf], row_upper=[1.0, 5.0],
        column_lower=[0.0, -Inf], column_upper=[Inf, 7.0],
        variable_domains=[CONTINUOUS, INTEGER],
        objective_sense=MAX_SENSE, objective_constant=2.0,
        name="sample", row_names=["balance", "cap"],
        column_names=["x", "y"],
    )
    @test size(problem.A) == (2, 2)
    @test problem.objective == [3.0, 4.0]
    @test problem.objective_sense == MAX_SENSE
    @test !is_continuous(problem)

    A[1, 1] = 99.0
    @test problem.A[1, 1] == 1.0

    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [NaN],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        column_lower=[2.0], column_upper=[1.0],
    )

    binary = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        variable_domains=[BINARY],
    )
    @test binary.column_lower == [0.0]
    @test binary.column_upper == [1.0]

    full_field = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0], 0.0,
        MIN_SENSE,
        [-Inf], [Inf], [0.0], [1.0], [BINARY], "",
        String[], String[],
    )
    @test full_field.column_upper == [1.0]
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), Float64[], 0.0,
        MIN_SENSE,
        [-Inf], [Inf], [0.0], [Inf], [CONTINUOUS], "", String[], String[],
    )
end
