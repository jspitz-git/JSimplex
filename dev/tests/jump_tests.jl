using Test
using JSimplex
using JuMP

const MOI = JuMP.MOI

@testset "JuMP Float64 cache integration" begin
    model = JuMP.Model(JSimplex.Optimizer)
    JuMP.set_silent(model)
    JuMP.set_time_limit_sec(model, 60.0)
    JuMP.set_optimizer_attribute(model, "iteration_limit", 10_000)
    @variable(model, x >= 0)
    @variable(model, -2 <= y <= 4)
    @objective(model, Min, x + 2y + 7)
    row = @constraint(model, x + y >= 1)

    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OPTIMAL
    @test JuMP.objective_value(model) ≈ 6.0
    @test JuMP.value(x) ≈ 3.0
    @test JuMP.value(y) ≈ -2.0
    @test JuMP.value(row) ≈ 1.0

    JuMP.set_lower_bound(y, 0.0)
    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OPTIMAL
    @test JuMP.objective_value(model) ≈ 8.0
    @test JuMP.value(x) ≈ 1.0
    @test JuMP.value(y) ≈ 0.0
    @test !MOI.supports_incremental_interface(JSimplex.Optimizer())
end

@testset "JuMP LP relaxation" begin
    model = JuMP.Model(JSimplex.Optimizer)
    JuMP.set_silent(model)
    @variable(model, 0 <= x <= 1, Int)
    @constraint(model, x >= 0.5)
    @objective(model, Min, x)

    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OTHER_ERROR
    JuMP.set_optimizer_attribute(model, "relax_integrality", true)
    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OPTIMAL
    @test JuMP.value(x) ≈ 0.5
end

@testset "JuMP generic numeric integration" begin
    let T = Float32
        model = JuMP.GenericModel{T}(() -> JSimplex.Optimizer{T}())
        JuMP.set_silent(model)
        lower = T(3) / T(2)
        @variable(model, x >= lower)
        @objective(model, Min, x + T(1) / T(2))
        JuMP.optimize!(model)
        @test JuMP.termination_status(model) == MOI.OPTIMAL
        @test JuMP.value(x) === lower
        @test JuMP.objective_value(model) === T(2)
    end

    setprecision(BigFloat, 256) do
        model = JuMP.GenericModel{BigFloat}(() -> JSimplex.Optimizer{BigFloat}())
        JuMP.set_silent(model)
        lower = parse(BigFloat,
                      "1.0000000000000000000000000000000000000000000000000000000000000001")
        @variable(model, x >= lower)
        @objective(model, Min, x)
        JuMP.optimize!(model)
        @test JuMP.termination_status(model) == MOI.OPTIMAL
        @test JuMP.value(x) == lower
        @test JuMP.objective_value(model) == lower
        @test precision(JuMP.value(x)) == 256
    end

    let T = Rational{BigInt}
        model = JuMP.GenericModel{T}(() -> JSimplex.Optimizer{T}())
        JuMP.set_silent(model)
        lower = T(3) / T(2)
        offset = T(1) / T(3)
        @variable(model, x >= lower)
        @objective(model, Min, x + offset)
        JuMP.optimize!(model)
        @test JuMP.termination_status(model) == MOI.OPTIMAL
        @test JuMP.value(x) === lower
        @test JuMP.objective_value(model) == T(11) / T(6)
    end
end
