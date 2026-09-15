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
