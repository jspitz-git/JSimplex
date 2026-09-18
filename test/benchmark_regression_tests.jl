# Small upstream benchmark instances checked into the repository so the mandatory
# suite remains independent of the user's NetLib and MIPLib installations.
@testset "NetLib and MIPLib numerical regressions" begin
    cases = (
        # NetLib: varied coefficients and bounds, linked equalities, and wide scaling.
        ("netlib", "kb2", (43, 41), 0, -1749.9001299062088),
        ("netlib", "sc50a", (50, 48), 0, -64.57507705856445),
        ("netlib", "adlittle", (56, 97), 0, 225494.9631623819),
        # MIPLib: integer-infeasible but LP-feasible, mixed-domain scaling,
        # and a zero-cost LP relaxation with equality constraints.
        ("miplib", "stein9inf", (14, 9), 9, 4.0),
        ("miplib", "flugpl", (18, 18), 11, 1.16718572559232e6),
        ("miplib", "markshare_4_0", (4, 34), 30, 0.0),
    )

    for (collection, name, dimensions, discrete_count, expected) in cases
        @testset "$collection/$name" begin
            path = joinpath(@__DIR__, "fixtures", "solver", collection, "$name.mps")
            problem = read_mps(path)
            @test size(problem.A) == dimensions
            @test count(!=(CONTINUOUS), problem.variable_domains) == discrete_count
            if discrete_count > 0
                @test solve(problem).status == MIP_NOT_SUPPORTED
            end

            for algorithm in (:dual, :primal)
                @testset "$algorithm" begin
                    options = SolverOptions(algorithm=algorithm, iteration_limit=2_000,
                                            verbose=false)
                    result = solve(problem; relax_integrality=discrete_count > 0, options)
                    @test result.status == OPTIMAL
                    @test result.objective_value isa Real
                    if result.objective_value isa Real
                        @test isapprox(result.objective_value, expected; atol=1e-6, rtol=1e-8)
                    end
                    @test result.primal isa Vector{Float64}
                    if result.primal isa Vector{Float64}
                        @test length(result.primal) == dimensions[2]
                        @test all(isfinite, result.primal)
                    end
                end
            end
        end
    end

    @testset "MIPLib pk1 dual zero-step stall recovers" begin
        path = joinpath(@__DIR__, "fixtures", "solver", "miplib", "pk1.mps")
        problem = read_mps(path)
        @test size(problem.A) == (45, 86)
        @test count(!=(CONTINUOUS), problem.variable_domains) == 55
        @test solve(problem).status == MIP_NOT_SUPPORTED

        primal = solve(problem; relax_integrality=true,
                       options=SolverOptions(algorithm=:primal, iteration_limit=2_000,
                                             verbose=false))
        @test primal.status == OPTIMAL
        @test primal.objective_value isa Real
        if primal.objective_value isa Real
            @test isapprox(primal.objective_value, 0.0; atol=1e-6)
        end

        # Steepest-edge pricing can follow zero-dual-step pivots indefinitely;
        # automatic fallback must recover the optimal LP relaxation.
        dual = solve(problem; relax_integrality=true,
                     options=SolverOptions(algorithm=:dual, iteration_limit=500,
                                           verbose=false))
        @test dual.status == OPTIMAL
        @test dual.objective_value == 0.0
        @test dual.statistics.iterations <= 500
    end
end
