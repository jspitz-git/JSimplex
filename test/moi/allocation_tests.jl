import MathOptInterface as MOI

function allocation_moi_source(rows=256)
    source = MOI.Utilities.Model{Float64}()
    variables = MOI.add_variables(source, 16)
    for row in 1:rows
        # Vary support and revisit one variable to exercise row aggregation.
        first_column = mod1(row, 16)
        second_column = mod1(row + 1, 16)
        f = MOI.ScalarAffineFunction([
            MOI.ScalarAffineTerm(2.0, variables[first_column]),
            MOI.ScalarAffineTerm(3.0, variables[second_column]),
            MOI.ScalarAffineTerm(-1.0, variables[first_column]),
        ], 1.0)
        MOI.add_constraint(source, f, MOI.LessThan(4.0))
    end
    return source
end

@testset "MOI translation allocation budget" begin
    source = allocation_moi_source()
    optimizer = JSimplex.Optimizer()
    JSimplex._translate_moi_model(optimizer, source)
    # Allow result storage and the source's MOI getters; reject allocating a
    # fresh aggregation dictionary for every row.
    @test (@allocated JSimplex._translate_moi_model(optimizer, source)) <= 380_000
end

@testset "MOI row aggregation keeps rows and evaluations independent" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        source = MOI.Utilities.Model{T}()
        x = MOI.add_variables(source, 3)
        functions = (
            MOI.ScalarAffineFunction([
                MOI.ScalarAffineTerm(T(2), x[1]), MOI.ScalarAffineTerm(T(3), x[2]),
                MOI.ScalarAffineTerm(T(-2), x[1]),
            ], T(1)),
            MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(T(4), x[3])], T(-1)),
            MOI.ScalarAffineFunction(MOI.ScalarAffineTerm{T}[], T(2)),
            MOI.ScalarAffineFunction([MOI.ScalarAffineTerm(T(5), x[1])], T(0)),
        )
        constraints = [MOI.add_constraint(source, f, MOI.LessThan(T(7))) for f in functions]
        translated = JSimplex._translate_moi_model(JSimplex.Optimizer{T}(), source)
        @test isnothing(translated.error)
        rows = [translated.index_map[c].value for c in constraints]
        @test Matrix(translated.problem.A[rows, :]) == T[0 3 0; 0 0 4; 0 0 0; 5 0 0]
        @test bound_value.(translated.problem.row_upper[rows]) == T[6, 8, 5, 7]
        @test [JSimplex._evaluate_moi_function(translated.evaluations[row], T[1, 2, 3])
               for row in rows] == T[7, 11, 2, 5]
        # A later translation must not overwrite stored evaluation vectors.
        MOI.empty!(source)
        again = JSimplex._translate_moi_model(JSimplex.Optimizer{T}(), source)
        @test size(again.problem.A) == (0, 0)
        @test [JSimplex._evaluate_moi_function(translated.evaluations[row], T[1, 2, 3])
               for row in rows] == T[7, 11, 2, 5]
    end
end
