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
    @test MOI.supports(optimizer, MOI.ObjectiveSense())
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

@testset "MOI optimizer attributes" begin
    optimizer = JSimplex.Optimizer{Float32}()
    @test MOI.get(optimizer, MOI.SolverName()) == "JSimplex"
    @test MOI.get(optimizer, MOI.SolverVersion()) == "0.5.0"

    @test MOI.supports(optimizer, MOI.Silent())
    @test !MOI.get(optimizer, MOI.Silent())
    MOI.set(optimizer, MOI.Silent(), true)
    @test MOI.get(optimizer, MOI.Silent())

    @test MOI.supports(optimizer, MOI.TimeLimitSec())
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === nothing
    MOI.set(optimizer, MOI.TimeLimitSec(), 2)
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === 2.0
    MOI.set(optimizer, MOI.TimeLimitSec(), nothing)
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === nothing

    values = Dict(
        "relax_integrality" => true,
        "iteration_limit" => 19,
        "primal_tolerance" => Float32(1e-5),
        "dual_tolerance" => Float32(2e-5),
        "zero_tolerance" => Float32(3e-6),
        "refactorization_interval" => 7,
        "verbose" => false,
        "algorithm" => :dual,
        "pricing" => :devex,
        "basis_update" => :suhl_suhl,
        "basis_refactorization" => :markowitz,
        "scaling" => :off,
    )
    for (name, value) in values
        attr = MOI.RawOptimizerAttribute(name)
        @test MOI.supports(optimizer, attr)
        MOI.set(optimizer, attr, value)
        @test MOI.get(optimizer, attr) == value
    end
    @test JSimplex._solver_options(optimizer) isa SolverOptions{Float32}
    @test !JSimplex._solver_options(optimizer).verbose
    @test JSimplex._solver_options(optimizer).pricing == :devex
    @test JSimplex._solver_options(optimizer).basis_update == :suhl_suhl
    @test JSimplex._solver_options(optimizer).basis_refactorization == :markowitz
    @test JSimplex._solver_options(optimizer).scaling == :off
    MOI.set(optimizer, MOI.RawOptimizerAttribute("verbose"), true)
    @test !JSimplex._solver_options(optimizer).verbose
    MOI.set(optimizer, MOI.Silent(), false)
    @test JSimplex._solver_options(optimizer).verbose
    MOI.set(optimizer, MOI.Silent(), true)
    @test_throws MOI.UnsupportedAttribute MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("unknown_parameter"),
        1,
    )
    @test_throws ArgumentError MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("iteration_limit"),
        -1,
    )
    @test_throws ArgumentError MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("pricing"),
        :unknown,
    )
    @test_throws ArgumentError MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("basis_refactorization"),
        :unknown,
    )
    @test_throws ArgumentError MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("scaling"),
        :unknown,
    )
    @test_throws ArgumentError MOI.set(
        JSimplex.Optimizer{Rational{BigInt}}(),
        MOI.RawOptimizerAttribute("scaling"),
        :on,
    )

    MOI.empty!(optimizer)
    @test MOI.get(optimizer, MOI.Silent())
    @test MOI.get(optimizer, MOI.RawOptimizerAttribute("iteration_limit")) == 19
end
