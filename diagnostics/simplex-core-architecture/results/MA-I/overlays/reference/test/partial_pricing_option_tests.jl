@testset "Partial pricing is explicitly selected independently of strategy" begin
    for strategy in (:legacy, :adaptive)
        @test !JSimplex.NumericalPolicy(Float64; simplex_strategy=strategy).partial_pricing
        @test !JSimplex.NumericalPolicy(Float64, SolverOptions(simplex_strategy=strategy)).partial_pricing
        for enabled in (false, true)
            options = SolverOptions(simplex_strategy=strategy, partial_pricing=enabled)
            @test options.partial_pricing == enabled
            @test JSimplex._phase_options(options, :dual).partial_pricing == enabled
            @test JSimplex._copy_precision_options(BigFloat, options).partial_pricing == enabled
            budget = (; iteration_limit=100, iterations=3, time_limit_seconds=10.0)
            @test JSimplex._lp_auxiliary_options(options, budget).partial_pricing == enabled
            @test JSimplex.NumericalPolicy(Float64, options).partial_pricing == enabled
            @test SolverOptions(Float32, options).partial_pricing == enabled
            @test JSimplex._remaining_options(options; iterations=3).partial_pricing == enabled
            optimizer = JSimplex.Optimizer()
            attr = JSimplex.MOI.RawOptimizerAttribute("partial_pricing")
            @test JSimplex.MOI.supports(optimizer, attr)
            JSimplex.MOI.set(optimizer, attr, enabled)
            JSimplex.MOI.set(optimizer, JSimplex.MOI.RawOptimizerAttribute("simplex_strategy"), strategy)
            @test JSimplex.MOI.get(optimizer, attr) == enabled
            @test JSimplex._solver_options(optimizer).partial_pricing == enabled
            JSimplex.MOI.set(optimizer, JSimplex.MOI.TimeLimitSec(), 2.0)
            @test JSimplex.MOI.get(optimizer, attr) == enabled
            @test_throws ArgumentError JSimplex.MOI.set(optimizer, attr, "true")
            @test JSimplex.MOI.get(optimizer, attr) == enabled
        end
    end
end

@testset "Public partial-pricing option reaches native candidate selection" begin
    p = LinearProblem(JSimplex.SparseArrays.spdiagm(0 => ones(129)), -ones(129);
        row_upper=ones(129))
    for strategy in (:legacy, :adaptive), enabled in (false, true)
        options = SolverOptions(algorithm=:primal, pricing=:dantzig, presolve=false,
            verbose=false, simplex_strategy=strategy, partial_pricing=enabled)
        ws = JSimplex.initialize_workspace(p, options)
        @test JSimplex._primal_entering(ws, options.dual_tolerance) == (1, 1.0)
        @test isnothing(ws.scratch.pricing_pool) == !enabled
        solution = solve(p; options)
        @test solution.status == OPTIMAL
        @test solution.objective_value == -129.0
        @test solution.primal == ones(129)
    end
end
