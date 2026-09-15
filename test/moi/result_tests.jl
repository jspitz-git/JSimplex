import MathOptInterface as MOI

@testset "MOI optimal result" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 2)
    x_bound = MOI.add_constraint(source, x[1], MOI.GreaterThan(0.0))
    MOI.add_constraint(source, x[2], MOI.GreaterThan(0.0))
    row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1]),
         MOI.ScalarAffineTerm(1.0, x[2])],
        2.0,
    )
    ci = MOI.add_constraint(source, row, MOI.GreaterThan(3.0))
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1]),
         MOI.ScalarAffineTerm(2.0, x[2])],
        4.0,
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

    optimizer = JSimplex.Optimizer()
    index_map, copied = MOI.optimize!(optimizer, source)
    @test !copied
    @test !MOI.is_empty(optimizer)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
    @test MOI.get(optimizer, MOI.ResultCount()) == 1
    @test MOI.get(optimizer, MOI.PrimalStatus()) == MOI.FEASIBLE_POINT
    @test MOI.get(optimizer, MOI.DualStatus()) == MOI.NO_SOLUTION
    @test MOI.get(optimizer, MOI.ObjectiveValue()) == 5.0
    @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x[1]]) == 1.0
    @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x[2]]) == 0.0
    @test MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[x_bound]) == 1.0
    @test MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[ci]) == 3.0
    @test MOI.get(optimizer, MOI.SolveTimeSec()) >= 0.0
    @test MOI.get(optimizer, MOI.SimplexIterations()) >= 0
end

@testset "MOI BigFloat constraint primals preserve stored precision" begin
    source, x, fixed_constraint, fixed_value = setprecision(BigFloat, 256) do
        source = MOI.Utilities.Model{BigFloat}()
        x = MOI.add_variable(source)
        fixed_value = BigFloat(1) + ldexp(BigFloat(1), -100)
        fixed_constraint = MOI.add_constraint(source, x, MOI.EqualTo(fixed_value))
        return source, x, fixed_constraint, fixed_value
    end

    setprecision(BigFloat, 24) do
        optimizer = JSimplex.Optimizer{BigFloat}()
        index_map, _ = MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
        variable_primal = MOI.get(optimizer, MOI.VariablePrimal(), index_map[x])
        constraint_primal = MOI.get(
            optimizer,
            MOI.ConstraintPrimal(),
            index_map[fixed_constraint],
        )
        @test precision(variable_primal) == 256
        @test precision(constraint_primal) == 256
        @test variable_primal == fixed_value
        @test constraint_primal == variable_primal
    end
end

@testset "MOI numeric result types" begin
    for T in (Float32, Float64, Rational{BigInt})
        source = MOI.Utilities.Model{T}()
        x = MOI.add_variable(source)
        lower = MOI.add_constraint(source, x, MOI.GreaterThan(T(2)))
        objective = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(one(T), x)],
            one(T),
        )
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

        optimizer = JSimplex.Optimizer{T}()
        index_map, _ = MOI.optimize!(optimizer, source)
        objective_value = MOI.get(optimizer, MOI.ObjectiveValue())
        variable_primal = MOI.get(optimizer, MOI.VariablePrimal(), index_map[x])
        constraint_primal = MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[lower])
        @test objective_value isa T
        @test variable_primal isa T
        @test constraint_primal isa T
        @test objective_value == T(3)
        @test variable_primal == T(2)
        @test constraint_primal == T(2)
    end
end

@testset "MOI BigFloat results preserve stored precision" begin
    setprecision(BigFloat, 256) do
        source = MOI.Utilities.Model{BigFloat}()
        x = MOI.add_variable(source)
        expected = parse(BigFloat, "2.0000000000000000000000000000000000000000000000000000000000001")
        lower = MOI.add_constraint(source, x, MOI.GreaterThan(expected))
        objective = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(one(BigFloat), x)],
            zero(BigFloat),
        )
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

        optimizer = JSimplex.Optimizer{BigFloat}()
        index_map, _ = MOI.optimize!(optimizer, source)
        objective_value = MOI.get(optimizer, MOI.ObjectiveValue())
        variable_primal = MOI.get(optimizer, MOI.VariablePrimal(), index_map[x])
        constraint_primal = MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[lower])
        @test objective_value isa BigFloat
        @test variable_primal isa BigFloat
        @test constraint_primal isa BigFloat
        @test precision(objective_value) == 256
        @test precision(variable_primal) == 256
        @test precision(constraint_primal) == 256
        @test objective_value == expected
        @test variable_primal == expected
        @test constraint_primal == expected
    end
end

function _moi_integrality_relaxation_model(; include_integer=false, bounds=false)
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    if bounds
        MOI.add_constraint(source, x, MOI.GreaterThan(0.5))
        MOI.add_constraint(source, x, MOI.LessThan(0.75))
    else
        MOI.add_constraint(source, x, MOI.GreaterThan(0.5))
    end
    include_integer && MOI.add_constraint(source, x, MOI.Integer())
    MOI.add_constraint(source, x, MOI.ZeroOne())
    objective = MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(1.0, x)], 0.0)
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
    return source, x
end

@testset "MOI integrality relaxation" begin
    source, x = _moi_integrality_relaxation_model()
    optimizer = JSimplex.Optimizer()
    MOI.optimize!(optimizer, source)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OTHER_ERROR
    @test MOI.get(optimizer, MOI.RawStatusString()) ==
          "integer variables require a MIP solver; set relax_integrality=true to solve the LP relaxation"

    MOI.set(optimizer, MOI.RawOptimizerAttribute("relax_integrality"), true)
    index_map, _ = MOI.optimize!(optimizer, source)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
    @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x]) == 0.5
end

@testset "MOI integrality domains compose with bounds" begin
    for (source, x) in (
        _moi_integrality_relaxation_model(bounds=true),
        _moi_integrality_relaxation_model(include_integer=true),
    )
        optimizer = JSimplex.Optimizer()
        MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OTHER_ERROR

        MOI.set(optimizer, MOI.RawOptimizerAttribute("relax_integrality"), true)
        index_map, _ = MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
        @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x]) == 0.5
    end
end

function _moi_result_model(; integer=false)
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    MOI.add_constraint(source, x, MOI.GreaterThan(1.0))
    integer && MOI.add_constraint(source, x, MOI.Integer())
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{MOI.VariableIndex}(), x)
    return source
end

function _moi_pivot_model()
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 2)
    first_row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1])],
        0.0,
    )
    second_row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(-1.0, x[1]),
         MOI.ScalarAffineTerm(1.0, x[2])],
        0.0,
    )
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1]),
         MOI.ScalarAffineTerm(1.0, x[2])],
        0.0,
    )
    MOI.add_constraint(source, first_row, MOI.GreaterThan(1.0))
    MOI.add_constraint(source, second_row, MOI.GreaterThan(1.0))
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
    return source
end

function _moi_row_model()
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    row = MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(1.0, x)], 0.0)
    MOI.add_constraint(source, row, MOI.GreaterThan(1.0))
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{MOI.VariableIndex}(), x)
    return source
end

function _moi_unbounded_recession_model(::Type{T}) where {T}
    source = MOI.Utilities.Model{T}()
    x, y = MOI.add_variables(source, 2)
    row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(T(-1), x), MOI.ScalarAffineTerm(T(2), y)],
        zero(T),
    )
    MOI.add_constraint(source, row, MOI.LessThan(zero(T)))
    MOI.add_constraint(source, x, MOI.GreaterThan(zero(T)))
    MOI.add_constraint(source, y, MOI.GreaterThan(zero(T)))
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(T(-1), x), MOI.ScalarAffineTerm(T(-1), y)],
        zero(T),
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
    return source
end

@testset "MOI recession status follows numeric certification" begin
    inexact = JSimplex.Optimizer{Float64}()
    MOI.optimize!(inexact, _moi_unbounded_recession_model(Float64))
    @test MOI.get(inexact, MOI.TerminationStatus()) == MOI.NUMERICAL_ERROR
    @test MOI.get(inexact, MOI.RawStatusString()) ==
          "auxiliary direction has uncertain feasibility or objective improvement"
    @test MOI.get(inexact, MOI.ResultCount()) == 0
    @test MOI.get(inexact, MOI.PrimalStatus()) == MOI.NO_SOLUTION

    exact = JSimplex.Optimizer{Rational{BigInt}}()
    MOI.optimize!(exact, _moi_unbounded_recession_model(Rational{BigInt}))
    @test MOI.get(exact, MOI.TerminationStatus()) == MOI.DUAL_INFEASIBLE
    @test MOI.get(exact, MOI.ResultCount()) == 0
    @test MOI.get(exact, MOI.PrimalStatus()) == MOI.NO_SOLUTION
end

@testset "MOI statuses and unavailable results" begin
    untouched = JSimplex.Optimizer()
    @test MOI.get(untouched, MOI.TerminationStatus()) == MOI.OPTIMIZE_NOT_CALLED
    @test MOI.get(untouched, MOI.RawStatusString()) == "optimize not called"
    @test MOI.get(untouched, MOI.ResultCount()) == 0
    @test MOI.get(untouched, MOI.PrimalStatus()) == MOI.NO_SOLUTION
    @test MOI.get(untouched, MOI.DualStatus()) == MOI.NO_SOLUTION

    infeasible = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(infeasible)
    MOI.add_constraint(infeasible, x, MOI.GreaterThan(0.0))
    infeasible_row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x)],
        0.0,
    )
    MOI.add_constraint(infeasible, infeasible_row, MOI.LessThan(-1.0))
    MOI.set(infeasible, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(infeasible, MOI.ObjectiveFunction{MOI.VariableIndex}(), x)

    unbounded = MOI.Utilities.Model{Float64}()
    unbounded_x = MOI.add_variable(unbounded)
    MOI.set(unbounded, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(unbounded, MOI.ObjectiveFunction{MOI.VariableIndex}(), unbounded_x)

    invalid = MOI.Utilities.Model{Float64}()
    invalid_x = MOI.add_variable(invalid)
    MOI.add_constraint(invalid, invalid_x, MOI.GreaterThan(2.0))
    MOI.add_constraint(invalid, invalid_x, MOI.LessThan(1.0))

    cases = (
        (infeasible, JSimplex.Optimizer(), MOI.INFEASIBLE),
        (unbounded, JSimplex.Optimizer(), MOI.DUAL_INFEASIBLE),
        (_moi_pivot_model(), JSimplex.Optimizer(), MOI.ITERATION_LIMIT,
         "iteration_limit", 0),
        (_moi_result_model(), JSimplex.Optimizer(), MOI.TIME_LIMIT,
         "time_limit", 0.0),
        (_moi_row_model(), JSimplex.Optimizer(), MOI.NUMERICAL_ERROR,
         "zero_tolerance", 2.0),
        (invalid, JSimplex.Optimizer(), MOI.INVALID_MODEL),
        (_moi_result_model(integer=true), JSimplex.Optimizer(), MOI.OTHER_ERROR),
        (_moi_result_model(), JSimplex.Optimizer(), MOI.INVALID_OPTION,
         "algorithm", :primal),
    )
    for case in cases
        source, optimizer, expected = case[1:3]
        if length(case) == 5
            if case[4] == "time_limit"
                MOI.set(optimizer, MOI.TimeLimitSec(), case[5])
            else
                MOI.set(optimizer, MOI.RawOptimizerAttribute(case[4]), case[5])
            end
        end
        _, copied = MOI.optimize!(optimizer, source)
        @test !copied
        @test MOI.get(optimizer, MOI.TerminationStatus()) == expected
        @test MOI.get(optimizer, MOI.ResultCount()) == 0
        @test MOI.get(optimizer, MOI.PrimalStatus()) == MOI.NO_SOLUTION
        @test MOI.get(optimizer, MOI.DualStatus()) == MOI.NO_SOLUTION
        @test_throws MOI.ResultIndexBoundsError MOI.get(optimizer, MOI.ObjectiveValue())
    end
end

@testset "MOI result lifecycle" begin
    source = _moi_result_model()
    optimizer = JSimplex.Optimizer()
    MOI.set(optimizer, MOI.RawOptimizerAttribute("iteration_limit"), 5)
    MOI.optimize!(optimizer, source)
    @test optimizer.solution isa Solution{Float64}
    @test optimizer.constraint_primals isa Vector{Float64}
    @test !isempty(optimizer.constraint_primals)

    MOI.empty!(optimizer)
    @test isnothing(optimizer.solution)
    @test isempty(optimizer.constraint_primals)
    @test MOI.get(optimizer, MOI.RawOptimizerAttribute("iteration_limit")) == 5

    MOI.optimize!(optimizer, source)
    @test MOI.get(optimizer, MOI.ResultCount()) == 1
    MOI.set(optimizer, MOI.TimeLimitSec(), 1.0)
    @test MOI.get(optimizer, MOI.ResultCount()) == 0
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMIZE_NOT_CALLED
    @test_throws MOI.ResultIndexBoundsError MOI.get(optimizer, MOI.ObjectiveValue())
end

@testset "MOI invalid variable bounds clear stale results" begin
    valid = _moi_result_model()
    invalid = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(invalid)
    MOI.add_constraint(invalid, x, MOI.LessThan(NaN))

    optimizer = JSimplex.Optimizer()
    MOI.optimize!(optimizer, valid)
    @test MOI.get(optimizer, MOI.ResultCount()) == 1

    @test_nowarn MOI.optimize!(optimizer, invalid)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.INVALID_MODEL
    @test MOI.get(optimizer, MOI.ResultCount()) == 0
    @test MOI.get(optimizer, MOI.PrimalStatus()) == MOI.NO_SOLUTION
    @test_throws MOI.ResultIndexBoundsError MOI.get(optimizer, MOI.ObjectiveValue())
end

@testset "MOI invalid unbounded affine constants clear stale results" begin
    unbounded_sets = (
        MOI.GreaterThan(-Inf),
        MOI.LessThan(Inf),
        MOI.Interval(-Inf, Inf),
    )
    for set in unbounded_sets, constant in (NaN, Inf, -Inf)
        invalid = MOI.Utilities.Model{Float64}()
        x = MOI.add_variable(invalid)
        function_ = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(1.0, x)],
            constant,
        )
        constraint = MOI.add_constraint(invalid, function_, set)

        optimizer = JSimplex.Optimizer()
        MOI.optimize!(optimizer, _moi_result_model())
        @test MOI.get(optimizer, MOI.ResultCount()) == 1

        index_map, _ = MOI.optimize!(optimizer, invalid)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.INVALID_MODEL
        @test MOI.get(optimizer, MOI.ResultCount()) == 0
        @test isempty(optimizer.constraint_primals)
        @test_throws MOI.ResultIndexBoundsError MOI.get(
            optimizer,
            MOI.ConstraintPrimal(),
            index_map[constraint],
        )
    end
end

@testset "MOI variable constraint primals use variable indices" begin
    source = MOI.Utilities.Model{Float64}()
    _, y = MOI.add_variables(source, 2)
    fixed_y = MOI.add_constraint(source, y, MOI.EqualTo(2.0))

    optimizer = JSimplex.Optimizer()
    index_map, _ = MOI.optimize!(optimizer, source)
    implied_index = MOI.ConstraintIndex{MOI.VariableIndex,MOI.EqualTo{Float64}}(2)
    @test index_map[fixed_y] == implied_index
    @test MOI.get(optimizer, MOI.ConstraintPrimal(), implied_index) == 2.0
end
