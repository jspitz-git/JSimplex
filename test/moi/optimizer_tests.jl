import MathOptInterface as MOI

@testset "MOI optimizer construction and lifecycle" begin
    optimizer = JSimplex.Optimizer()
    @test optimizer isa JSimplex.Optimizer{Float64}
    @test JSimplex.Optimizer{Float32}() isa JSimplex.Optimizer{Float32}
    @test JSimplex.Optimizer{BigFloat}() isa JSimplex.Optimizer{BigFloat}
    @test JSimplex.Optimizer{Rational{BigInt}}() isa
          JSimplex.Optimizer{Rational{BigInt}}
    @test_throws ArgumentError JSimplex.Optimizer{Int}()
    @test !MOI.supports_incremental_interface(optimizer)
    @test MOI.is_empty(optimizer)
    @test sprint(summary, optimizer) == "JSimplex optimizer (Float64)"
    MOI.empty!(optimizer)
    @test MOI.is_empty(optimizer)

    for set_type in (
        MOI.GreaterThan{Float64},
        MOI.LessThan{Float64},
        MOI.EqualTo{Float64},
        MOI.Interval{Float64},
    )
        @test MOI.supports_constraint(optimizer, MOI.VariableIndex, set_type)
        @test MOI.supports_constraint(
            optimizer,
            MOI.ScalarAffineFunction{Float64},
            set_type,
        )
    end
    @test MOI.supports_constraint(
        optimizer,
        MOI.ScalarAffineFunction{Float64},
        MOI.EqualTo{Float64},
    )
    @test MOI.supports_constraint(optimizer, MOI.VariableIndex, MOI.Integer)
    @test MOI.supports_constraint(optimizer, MOI.VariableIndex, MOI.ZeroOne)
    @test MOI.supports(
        optimizer,
        MOI.ObjectiveFunction{MOI.ScalarAffineFunction{Float64}}(),
    )
    @test MOI.supports(optimizer, MOI.ObjectiveFunction{MOI.VariableIndex}())
    @test !MOI.supports_constraint(
        optimizer,
        MOI.ScalarQuadraticFunction{Float64},
        MOI.LessThan{Float64},
    )
    @test !MOI.supports_constraint(
        optimizer,
        MOI.VectorOfVariables,
        MOI.Nonnegatives,
    )
end
