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

    binary_error = try
        LinearProblem(
            JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
            column_lower=[2.0], column_upper=[Inf], variable_domains=[BINARY],
        )
        nothing
    catch error
        error
    end
    @test binary_error isa ArgumentError
    @test sprint(showerror, binary_error) ==
          "ArgumentError: binary variable bounds must intersect [0, 1]"

    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        variable_domains=[SEMI_CONTINUOUS], column_upper=[0.0],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        variable_domains=[SEMI_INTEGER], column_upper=[0.0],
    )

    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        row_lower=Float64[], row_upper=Float64[],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        column_lower=Float64[], column_upper=Float64[],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        variable_domains=VariableDomain[],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        row_names=["too", "many"],
    )
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), [1.0];
        column_names=["too", "many"],
    )

    full_A = JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1))
    full_objective = [1.0]
    full_row_lower = [-Inf]
    full_row_upper = [Inf]
    full_column_lower = [0.0]
    full_column_upper = [1.0]
    full_domains = [BINARY]
    full_row_names = ["row"]
    full_column_names = ["column"]
    full_field = LinearProblem(
        full_A, full_objective, 0.0, MIN_SENSE, full_row_lower, full_row_upper,
        full_column_lower, full_column_upper, full_domains, "", full_row_names,
        full_column_names,
    )
    full_A[1, 1] = 99.0
    full_objective[1] = 99.0
    full_row_lower[1] = 99.0
    full_row_upper[1] = 99.0
    full_column_lower[1] = 99.0
    full_column_upper[1] = 99.0
    full_domains[1] = CONTINUOUS
    full_row_names[1] = "changed"
    full_column_names[1] = "changed"
    @test full_field.A[1, 1] == 1.0
    @test full_field.objective == [1.0]
    @test full_field.row_lower == [-Inf]
    @test full_field.row_upper == [Inf]
    @test full_field.column_lower == [0.0]
    @test full_field.column_upper == [1.0]
    @test full_field.variable_domains == [BINARY]
    @test full_field.row_names == ["row"]
    @test full_field.column_names == ["column"]
    @test_throws ArgumentError LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0], 1, 1)), Float64[], 0.0,
        MIN_SENSE,
        [-Inf], [Inf], [0.0], [Inf], [CONTINUOUS], "", String[], String[],
    )
end

@testset "Bounds must admit finite real values" begin
    for bound in (-Inf, Inf)
        @test_throws ArgumentError LinearProblem(
            JSimplex.SparseArrays.spzeros(0, 1), [0.0];
            column_lower=[bound], column_upper=[bound],
        )
        @test_throws ArgumentError LinearProblem(
            JSimplex.SparseArrays.spzeros(1, 0), Float64[];
            row_lower=[bound], row_upper=[bound],
        )
    end
    for (field, bound) in ((:row_lower, Inf), (:row_upper, -Inf),
                           (:column_lower, Inf), (:column_upper, -Inf))
        problem = LinearProblem(
            JSimplex.SparseArrays.spzeros(1, 1), [0.0];
            column_lower=[-Inf], column_upper=[Inf],
        )
        getfield(problem, field)[1] = bound
        @test !isnothing(JSimplex._validation_error(problem))
    end
    for (lower, upper) in ((-Inf, Inf), (0.0, Inf), (-Inf, 2.0), (1.0, 1.0))
        problem = LinearProblem(
            JSimplex.SparseArrays.spzeros(1, 1), [0.0];
            row_lower=[lower], row_upper=[upper],
            column_lower=[lower], column_upper=[upper],
        )
        @test isnothing(JSimplex._validation_error(problem))
    end
end
