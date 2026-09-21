@testset "Presolve allocation budgets" begin
    problem = read_mps(joinpath(@__DIR__, "fixtures", "solver", "netlib", "adlittle.mps"))
    # Warm every entry point independently. These budgets allow runtime variation
    # but catch repeated exact-bound conversions and needless rational arithmetic.
    for (pass, budget) in ((JSimplex.propagate_row_bounds, 1_200_000),
                           (JSimplex.reduce_dependent_rows, 900_000),
                           (JSimplex.presolve_problem, 5_500_000))
        pass(problem)
        @test (@allocated pass(problem)) <= budget
    end
end

@testset "Exact sparse elimination preserves source coefficients" begin
    Q = Rational{BigInt}
    source = Dict(1 => Q(2, 3), 2 => Q(-4, 5), 3 => Q(7, 11))
    original = deepcopy(source)
    target = Dict(1 => Q(2, 3), 2 => Q(1, 5), 4 => Q(3))
    JSimplex._subtract_scaled!(target, source, Q(1))
    @test target == Dict(2 => Q(1), 3 => Q(-7, 11), 4 => Q(3))
    @test source == original
    JSimplex._subtract_scaled!(target, source, Q(-2))
    @test target == Dict(1 => Q(4, 3), 2 => Q(-3, 5), 3 => Q(7, 11), 4 => Q(3))
    @test source == original
end
