import MathOptInterface as MOI

@testset "MOI conformance" begin
    optimizer = MOI.instantiate(
        MOI.OptimizerWithAttributes(
            JSimplex.Optimizer,
            MOI.Silent() => true,
        );
        with_bridge_type=Float64,
    )
    config = MOI.Test.Config(
        atol=1e-6,
        rtol=1e-6,
        optimal_status=MOI.OPTIMAL,
        exclude=Any[
            MOI.ConstraintDual,
            MOI.ConstraintBasisStatus,
            MOI.ConstraintPrimalStart,
            MOI.DualObjectiveValue,
            MOI.ObjectiveBound,
            MOI.VariableBasisStatus,
            MOI.VariablePrimalStart,
        ],
    )
    tests = (
        MOI.Test.test_attribute_RawStatusString,
        MOI.Test.test_attribute_Silent,
        MOI.Test.test_attribute_SolverName,
        MOI.Test.test_attribute_SolveTimeSec,
        MOI.Test.test_attribute_TimeLimitSec,
        MOI.Test.test_linear_FEASIBILITY_SENSE,
        MOI.Test.test_linear_INFEASIBLE,
        MOI.Test.test_linear_Interval_inactive,
        MOI.Test.test_linear_LessThan_and_GreaterThan,
        MOI.Test.test_linear_inactive_bounds,
        MOI.Test.test_linear_integration,
        MOI.Test.test_linear_integration_2,
        MOI.Test.test_linear_integration_Interval,
        MOI.Test.test_linear_integration_modification,
    )
    for test in tests
        @testset "$(nameof(test))" begin
            MOI.empty!(optimizer)
            test(optimizer, config)
        end
    end
end
