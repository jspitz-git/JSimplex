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
