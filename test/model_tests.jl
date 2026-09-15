# Julia 1.13's @inferred erases a type-valued keyword to DataType. Keep T in
# the helper's positional signature while checking the public keyword path.
typed_model_override(A, objective, ::Type{T}) where {T} =
    LinearProblem(A, objective; value_type=T)

@testset "Parametric LinearProblem inference" begin
    sparse = JSimplex.SparseArrays.sparse
    @test (@inferred LinearProblem(sparse(Float32[1 2]), Float32[3, 4])) isa LinearProblem{Float32}
    @test (@inferred LinearProblem(sparse(BigFloat[1 2]), BigFloat[3, 4])) isa LinearProblem{BigFloat}
    exact = @inferred LinearProblem(sparse(Rational{BigInt}[1 2]), Rational{BigInt}[3, 4];
        row_lower=Union{Nothing,Rational{BigInt}}[nothing], row_upper=Rational{BigInt}[5])
    @test exact isa LinearProblem{Rational{BigInt}}
    @test !isfinite(only(exact.row_lower))
    @test bound_value(only(exact.row_upper)) == 5
    @test (@inferred LinearProblem(sparse([1 2]), [3, 4])) isa LinearProblem{Float64}
    @test (@inferred typed_model_override(sparse([1 2]), [3, 4], Rational{BigInt})) isa LinearProblem{Rational{BigInt}}
    @test (@inferred LinearProblem(sparse(Float32[1 2]), [3, 4])) isa LinearProblem{Float32}
    @test_throws ArgumentError LinearProblem(sparse([1;;]), [1]; value_type=Int)
    @test_throws ArgumentError LinearProblem(sparse([1;;]), [1]; value_type=ComplexF64)
    @test LinearProblem(sparse(Float32[1;;]), Float32[1]; objective_constant=big"0.1") isa LinearProblem{BigFloat}
    @test LinearProblem(sparse(Float32[1;;]), Float32[1]; row_upper=[2.0]) isa LinearProblem{Float64}
    @test LinearProblem(sparse(Float32[1;;]), Float32[1]; row_upper=[Inf]) isa LinearProblem{Float32}
    @test LinearProblem(sparse(Float32[1;;]), Float32[1]; row_upper=[Bound{BigFloat}(nothing)]) isa LinearProblem{Float32}
    @test LinearProblem(sparse(Float32[1;;]), Float32[1]; row_upper=[Bound(big"2")]) isa LinearProblem{BigFloat}
    @test_throws ArgumentError LinearProblem(sparse([1.0e100;;]), [1.0]; value_type=Float32)
    @test_throws ArgumentError LinearProblem(sparse([1.0;;]), [1.0]; column_upper=[1.0e100], value_type=Float32)
    @test_throws ArgumentError LinearProblem(sparse([1.0e100;;]), [1.0]; value_type=Rational{Int})
end

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
    @test bound_value.(binary.column_lower) == [0.0]
    @test bound_value.(binary.column_upper) == [1.0]

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
    @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, full_field.row_lower) == [nothing]
    @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, full_field.row_upper) == [nothing]
    @test bound_value.(full_field.column_lower) == [0.0]
    @test bound_value.(full_field.column_upper) == [1.0]
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
        @test_throws ArgumentError LinearProblem(
            JSimplex.SparseArrays.spzeros(1, 1), [0.0]; NamedTuple{(field,)}(([bound],))...,
        )
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
