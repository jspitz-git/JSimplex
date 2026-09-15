import MathOptInterface as MOI

@testset "MOI column translation" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 6)
    MOI.set(source, MOI.VariableName(), x[1], "free")
    lower_constraint = MOI.add_constraint(source, x[2], MOI.GreaterThan(-1.0))
    MOI.add_constraint(source, x[2], MOI.LessThan(3.0))
    MOI.add_constraint(source, x[3], MOI.Integer())
    MOI.add_constraint(source, x[4], MOI.ZeroOne())
    MOI.add_constraint(source, x[5], MOI.EqualTo(2.0))
    MOI.add_constraint(source, x[6], MOI.Interval(-4.0, 5.0))

    columns = JSimplex._collect_moi_columns(JSimplex.Optimizer(), source)
    @test !isfinite(columns.lower[1])
    @test !isfinite(columns.upper[1])
    @test bound_value(columns.lower[2]) == -1.0
    @test bound_value(columns.upper[2]) == 3.0
    @test columns.domains == [
        CONTINUOUS,
        CONTINUOUS,
        INTEGER,
        BINARY,
        CONTINUOUS,
        CONTINUOUS,
    ]
    @test bound_value(columns.lower[4]) == 0.0
    @test bound_value(columns.upper[4]) == 1.0
    @test bound_value(columns.lower[5]) == 2.0
    @test bound_value(columns.upper[5]) == 2.0
    @test bound_value(columns.lower[6]) == -4.0
    @test bound_value(columns.upper[6]) == 5.0
    @test columns.names == ["free", "", "", "", "", ""]
    @test columns.index_map[x[1]] == MOI.VariableIndex(1)
    @test columns.index_map[lower_constraint] ==
          MOI.ConstraintIndex{MOI.VariableIndex,MOI.GreaterThan{Float64}}(1)
    @test columns.evaluations[1].columns == [2]
    @test columns.evaluations[1].coefficients == [1.0]
    @test columns.evaluations[1].constant == 0.0
end

@testset "MOI column translation reports conflicting bounds" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    MOI.add_constraint(source, x, MOI.GreaterThan(2.0))
    MOI.add_constraint(source, x, MOI.LessThan(1.0))

    columns = JSimplex._collect_moi_columns(JSimplex.Optimizer(), source)
    @test columns.error == "column lower bound exceeds column upper bound for variable 1"
end

@testset "MOI affine model translation" begin
    T = Rational{BigInt}
    source = MOI.Utilities.Model{T}()
    x = MOI.add_variables(source, 2)
    MOI.set(source, MOI.Name(), "typed model")
    MOI.set(source, MOI.VariableName(), x[1], "x")
    f = MOI.ScalarAffineFunction(
        MOI.ScalarAffineTerm{T}[
            MOI.ScalarAffineTerm(T(2), x[1]),
            MOI.ScalarAffineTerm(T(3), x[2]),
            MOI.ScalarAffineTerm(T(-1), x[1]),
        ],
        T(5),
    )
    ci = MOI.add_constraint(source, f, MOI.Interval(T(7), T(11)))
    MOI.set(source, MOI.ConstraintName(), ci, "range")
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(T(4), x[2])],
        T(3),
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MAX_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

    translated = JSimplex._translate_moi_model(JSimplex.Optimizer{T}(), source)
    @test translated.error === nothing
    problem = something(translated.problem)
    @test problem isa LinearProblem{T}
    @test Matrix(problem.A) == T[1 3]
    @test bound_value(problem.row_lower[1]) == T(2)
    @test bound_value(problem.row_upper[1]) == T(6)
    @test problem.objective == T[0, 4]
    @test problem.objective_constant == T(3)
    @test problem.objective_sense == MAX_SENSE
    @test problem.name == "typed model"
    @test problem.column_names == ["x", ""]
    @test problem.row_names == ["range"]
    @test translated.index_map[ci].value == 1
end

@testset "MOI affine set bounds subtract function constants" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    function affine(constant)
        return MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(2.0, x)], constant)
    end
    greater = MOI.add_constraint(source, affine(3.0), MOI.GreaterThan(7.0))
    less = MOI.add_constraint(source, affine(4.0), MOI.LessThan(9.0))
    equal = MOI.add_constraint(source, affine(5.0), MOI.EqualTo(11.0))
    interval = MOI.add_constraint(source, affine(6.0), MOI.Interval(13.0, 17.0))

    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), source)
    @test translated.error === nothing
    problem = something(translated.problem)
    for (constraint, lower, upper) in [
        (greater, 4.0, nothing),
        (less, nothing, 5.0),
        (equal, 6.0, 6.0),
        (interval, 7.0, 11.0),
    ]
        row = translated.index_map[constraint].value
        lower === nothing ? @test(!isfinite(problem.row_lower[row])) :
                           @test(bound_value(problem.row_lower[row]) == lower)
        upper === nothing ? @test(!isfinite(problem.row_upper[row])) :
                           @test(bound_value(problem.row_upper[row]) == upper)
    end
end

@testset "MOI variable and feasibility objectives" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 2)
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{MOI.VariableIndex}(), x[2])

    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), source)
    @test translated.error === nothing
    problem = something(translated.problem)
    @test problem.objective == [0.0, 1.0]
    @test problem.objective_constant == 0.0
    @test problem.objective_sense == MIN_SENSE

    feasibility = MOI.Utilities.Model{Float64}()
    MOI.add_variable(feasibility)
    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), feasibility)
    @test translated.error === nothing
    problem = something(translated.problem)
    @test problem.objective == [0.0]
    @test problem.objective_constant == 0.0
    @test problem.objective_sense == MIN_SENSE
end

@testset "MOI translation rejects unsupported and non-finite data" begin
    quadratic = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(quadratic)
    q = MOI.ScalarQuadraticFunction(
        MOI.ScalarQuadraticTerm{Float64}[],
        [MOI.ScalarAffineTerm(1.0, x)],
        0.0,
    )
    MOI.add_constraint(quadratic, q, MOI.LessThan(1.0))
    @test_throws MOI.UnsupportedConstraint JSimplex._translate_moi_model(
        JSimplex.Optimizer(),
        quadratic,
    )

    nonfinite = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(nonfinite)
    f = MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(NaN, x)], 0.0)
    MOI.add_constraint(nonfinite, f, MOI.LessThan(1.0))
    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), nonfinite)
    @test translated.error !== nothing
    @test occursin("constraint matrix coefficient", translated.error)
end

@testset "MOI translation preserves stored BigFloat model data" begin
    source, values = setprecision(BigFloat, 512) do
        source = MOI.Utilities.Model{BigFloat}()
        x = MOI.add_variable(source)
        matrix_coefficient = BigFloat(2)^200 + 1
        row_constant = BigFloat(2)^190 + 1
        row_bound = BigFloat(2)^180 + 1
        objective_coefficient = BigFloat(2)^170 + 1
        objective_constant = BigFloat(2)^160 + 1
        column_lower = BigFloat(2)^150 + 1
        row = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(matrix_coefficient, x)],
            row_constant,
        )
        MOI.add_constraint(source, row, MOI.EqualTo(row_constant + row_bound))
        MOI.add_constraint(source, x, MOI.GreaterThan(column_lower))
        objective = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(objective_coefficient, x)],
            objective_constant,
        )
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
        source, (
            matrix_coefficient,
            row_constant,
            row_bound,
            objective_coefficient,
            objective_constant,
            column_lower,
        )
    end

    setprecision(BigFloat, 64) do
        translated = JSimplex._translate_moi_model(JSimplex.Optimizer{BigFloat}(), source)
        @test translated.error === nothing
        problem = something(translated.problem)
        @test problem.A[1, 1] == values[1]
        @test precision(problem.A[1, 1]) == 512
        @test translated.evaluations[2].constant == values[2]
        @test precision(translated.evaluations[2].constant) == 512
        @test bound_value(problem.row_lower[1]) == values[3]
        @test precision(bound_value(problem.row_lower[1])) == 512
        @test problem.objective == [values[4]]
        @test precision(problem.objective[1]) == 512
        @test problem.objective_constant == values[5]
        @test precision(problem.objective_constant) == 512
        @test bound_value(problem.column_lower[1]) == values[6]
        @test precision(bound_value(problem.column_lower[1])) == 512
    end
end

@testset "MOI translation reports invalid affine constants and set bounds" begin
    invalid_constant = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(invalid_constant)
    f = MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(1.0, x)], NaN)
    MOI.add_constraint(invalid_constant, f, MOI.LessThan(1.0))
    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), invalid_constant)
    @test translated.problem === nothing
    @test translated.error !== nothing

    invalid_bound = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(invalid_bound)
    f = MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(1.0, x)], 0.0)
    MOI.add_constraint(invalid_bound, f, MOI.LessThan(NaN))
    translated = JSimplex._translate_moi_model(JSimplex.Optimizer(), invalid_bound)
    @test translated.problem === nothing
    @test translated.error !== nothing
end
