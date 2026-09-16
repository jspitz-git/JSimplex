using JSimplex.SparseArrays

@testset "Primal simplex solves a model requiring phase I" begin
    problem = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
    before = deepcopy(problem)
    result = solve(problem; options=SolverOptions(algorithm=:primal, verbose=false))
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0, 0.0]
    @test result.objective_value ≈ 1.0
    for field in fieldnames(typeof(problem))
        @test getfield(problem, field) == getfield(before, field)
    end
end

@testset "Primal phase I reports progress with original objective size" begin
    problem = LinearProblem(sparse([1.0;;]), [2.0];
                            row_lower=[1.0], objective_constant=4.0)
    options = SolverOptions(; algorithm=:primal, basis_update=:suhl_suhl,
                             refactorization_interval=1)
    result = JSimplex.Logging.with_logger(JSimplex.Logging.NullLogger()) do
        solve(problem; options)
    end
    @test result.status == OPTIMAL
    @test result.objective_value == 6.0
end

@testset "Primal phase I and phase II across scalar types" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        lower = LinearProblem(sparse(T[1 1]), T[2, 1]; row_lower=T[1])
        result = @inferred solve(lower; options)
        @test result isa Solution{T}
        @test result.status == OPTIMAL
        @test result.primal ≈ T[0, 1]
        @test result.objective_value ≈ one(T)
        @test result.statistics.iterations >= 2

        upper = LinearProblem(sparse(T[1;;]), T[1]; row_upper=T[3],
                              objective_sense=MAX_SENSE)
        result = solve(upper; options)
        @test result.status == OPTIMAL
        @test result.primal ≈ T[3]
        @test result.objective_value ≈ T(3)

        infeasible = LinearProblem(sparse(T[1;;]), T[1];
                                   row_lower=T[2], column_upper=T[1])
        @test solve(infeasible; options).status == INFEASIBLE

        unbounded = LinearProblem(spzeros(T, 0, 1), T[-1])
        @test solve(unbounded; options).status == UNBOUNDED
    end
end

@testset "Primal simplex handles bounds, free variables, and empty models" begin
    options = SolverOptions(algorithm=:primal, verbose=false)
    bounded = LinearProblem(spzeros(0, 1), [-1.0]; column_upper=[2.0])
    result = solve(bounded; options)
    @test result.status == OPTIMAL
    @test result.primal == [2.0]
    @test result.objective_value == -2.0

    free = LinearProblem(sparse([1.0;;]), [2.0];
                         row_lower=[-3.0], row_upper=[-3.0],
                         column_lower=[nothing])
    result = solve(free; options)
    @test result.status == OPTIMAL
    @test result.primal ≈ [-3.0]
    @test result.objective_value ≈ -6.0

    empty = LinearProblem(spzeros(0, 0), Float64[]; objective_constant=7.0)
    result = solve(empty; options)
    @test result.status == OPTIMAL
    @test result.primal == Float64[]
    @test result.objective_value == 7.0

    binary = LinearProblem(spzeros(0, 1), [-1.0]; variable_domains=[BINARY])
    @test solve(binary; options).status == MIP_NOT_SUPPORTED
    relaxed = solve(binary; options, relax_integrality=true)
    @test relaxed.status == OPTIMAL
    @test relaxed.primal == [1.0]
end

@testset "Primal simplex honors limits across phases" begin
    problem = LinearProblem(sparse([1.0 1.0]), [2.0, 1.0]; row_lower=[1.0])
    for (limit, status) in ((0, ITERATION_LIMIT), (1, ITERATION_LIMIT), (2, OPTIMAL))
        result = solve(problem; options=SolverOptions(algorithm=:primal,
                                                      iteration_limit=limit, verbose=false))
        @test result.status == status
        @test result.statistics.iterations == limit
    end
    result = solve(problem; options=SolverOptions(algorithm=:primal,
                                                  time_limit=0.0, verbose=false))
    @test result.status == TIME_LIMIT
    @test result.statistics.iterations == 0
end

@testset "Phase I does not mistake a small reduced cost for infeasibility" begin
    problem = LinearProblem(sparse([1.0e-8;;]), [0.0]; row_lower=[1.0])
    result = solve(problem; options=SolverOptions(algorithm=:primal, verbose=false))
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0e8]
end

@testset "Phase I infeasibility requires a row-combination certificate" begin
    for T in (Float64, Rational{BigInt})
        feasible = LinearProblem(sparse(T[1;;]), T[0]; row_lower=T[1])
        infeasible = LinearProblem(sparse(T[1;;]), T[0];
                                   row_lower=T[2], column_upper=T[1])
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        feasible_workspace = JSimplex.initialize_workspace(feasible, options)
        infeasible_workspace = JSimplex.initialize_workspace(infeasible, options)
        @test !JSimplex._primal_infeasibility_certified(feasible_workspace, T[1])
        @test JSimplex._primal_infeasibility_certified(infeasible_workspace, T[1])
    end
end

@testset "Primal unboundedness requires a recession certificate" begin
    for T in (Float64, Rational{BigInt})
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        unbounded = LinearProblem(spzeros(T, 0, 1), T[-1])
        bounded = LinearProblem(spzeros(T, 0, 1), T[-1]; column_upper=T[2])
        @test JSimplex._recession_direction_status(
            JSimplex.initialize_workspace(unbounded, options), T[1],
        ) == :certified
        @test JSimplex._recession_direction_status(
            JSimplex.initialize_workspace(bounded, options), T[1],
        ) == :invalid
    end
    phase_one = LinearProblem(sparse([1.0 0.0]), [0.0, -1.0]; row_lower=[1.0])
    @test solve(phase_one; options=SolverOptions(algorithm=:primal,
                                                  verbose=false)).status == UNBOUNDED
end

@testset "Primal simplex uses selectable basis factorizations and updates" begin
    problem = LinearProblem(sparse([1.0 1.0]), [2.0, 1.0]; row_lower=[1.0])
    for basis_update in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl),
        basis_refactorization in (:native, :markowitz)
        options = SolverOptions(; algorithm=:primal, basis_update,
                                 basis_refactorization,
                                 refactorization_interval=1, verbose=false)
        result = solve(problem; options)
        @test result.status == OPTIMAL
        @test result.primal ≈ [0.0, 1.0]
        @test result.objective_value ≈ 1.0
        @test result.statistics.refactorizations >= 2
    end
end

@testset "Primal pricing distinguishes Dantzig, steepest edge, and Devex" begin
    for T in (Float64, Rational{BigInt})
        problem = LinearProblem(sparse(T[100 1]), T[-10, -9]; row_upper=T[100])
        for (pricing, expected) in ((:dantzig, 1), (:steepest_edge, 2), (:devex, 1))
            workspace = JSimplex.initialize_workspace(problem,
                SolverOptions(T; algorithm=:primal, pricing, verbose=false))
            entering, direction = JSimplex._primal_entering(workspace, zero(T))
            @test entering == expected
            @test direction == one(T)
        end
        devex = JSimplex.initialize_workspace(problem,
            SolverOptions(T; algorithm=:primal, pricing=:devex, verbose=false))
        devex.pricing_weights[1] = T(100)
        @test first(JSimplex._primal_entering(devex, zero(T))) == 2
    end
end

@testset "Primal Devex updates nonbasic weights after a pivot" begin
    problem = LinearProblem(sparse([0.5 1.0]), [-10.0, -1.0]; row_upper=[1.0])
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(algorithm=:primal, pricing=:devex, verbose=false))
    @test isnothing(JSimplex._primal_iteration!(workspace, () -> false, 0.0))
    @test workspace.basis.basic_indices == [1]
    @test workspace.pricing_weights[2] ≈ 2.0
    @test workspace.pricing_weights[3] ≈ 2.0
end

@testset "Every primal pricing rule solves across scalar types" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}),
        pricing in (:dantzig, :steepest_edge, :devex)
        problem = LinearProblem(sparse(T[1 1]), T[2, 1]; row_lower=T[1])
        options = SolverOptions(T; algorithm=:primal, pricing, verbose=false,
                                refactorization_interval=1)
        result = solve(problem; options)
        @test result.status == OPTIMAL
        @test result.primal ≈ T[0, 1]
        @test result.objective_value ≈ one(T)
    end
end

@testset "Primal weighted pricing keeps extreme finite magnitudes" begin
    for (T, magnitude, tolerance) in ((Float32, 1f-23, 1f-30),
                                      (Float64, 1e-200, 1e-300))
        problem = LinearProblem(spzeros(T, 0, 2), T[-magnitude, -2magnitude])
        for pricing in (:steepest_edge, :devex)
            options = SolverOptions(T; algorithm=:primal, pricing,
                                    dual_tolerance=tolerance, verbose=false)
            workspace = JSimplex.initialize_workspace(problem, options)
            @test first(JSimplex._primal_entering(workspace, tolerance)) == 2
            @test solve(problem; options).status == UNBOUNDED
        end
    end

    large_costs = LinearProblem(sparse(Float32[100 1]),
                                Float32[-1f20, -2f20]; row_upper=Float32[100])
    workspace = JSimplex.initialize_workspace(large_costs,
        SolverOptions(Float32; algorithm=:primal, pricing=:steepest_edge,
                      verbose=false))
    @test first(JSimplex._primal_entering(workspace, 0f0)) == 2

    tiny_scores = LinearProblem(sparse([1e200 1e200]), [-1e-200, -2e-200];
                                row_upper=[1e200])
    workspace = JSimplex.initialize_workspace(tiny_scores,
        SolverOptions(; algorithm=:primal, pricing=:steepest_edge, verbose=false))
    @test first(JSimplex._primal_entering(workspace, 0.0)) == 2

    huge_norm = LinearProblem(sparse([1e308 1.0; 1e308 0.0]), [-2.0, -1.0];
                              row_upper=[1e308, 1e308])
    workspace = JSimplex.initialize_workspace(huge_norm,
        SolverOptions(; algorithm=:primal, pricing=:steepest_edge, verbose=false))
    @test first(JSimplex._primal_entering(workspace, 0.0)) == 2
    @test isfinite(workspace.pricing_weights[1])

    saturated_norms = LinearProblem(
        sparse(hcat(vcat(fill(1e308, 4), zeros(5)), fill(1e308, 9))),
        [-1.0, -1.1]; row_upper=fill(1e308, 9),
    )
    workspace = JSimplex.initialize_workspace(saturated_norms,
        SolverOptions(; algorithm=:primal, pricing=:steepest_edge, verbose=false))
    @test first(JSimplex._primal_entering(workspace, 0.0)) == 1

    adjacent_costs = LinearProblem(spzeros(0, 2), [-1e308, -nextfloat(1e308)])
    for pricing in (:steepest_edge, :devex)
        workspace = JSimplex.initialize_workspace(adjacent_costs,
            SolverOptions(; algorithm=:primal, pricing, verbose=false))
        @test first(JSimplex._primal_entering(workspace, 0.0)) == 2
    end

    T = Rational{Int64}
    wide_cost = LinearProblem(spzeros(T, 0, 1), T[-4_000_000_000])
    for pricing in (:dantzig, :steepest_edge, :devex)
        options = SolverOptions(T; algorithm=:primal, pricing, verbose=false)
        @test solve(wide_cost; options).status == UNBOUNDED
    end
    wide_pivot = LinearProblem(sparse(T[4_000_000_000;;]), T[-1];
                               row_upper=T[4_000_000_000])
    result = solve(wide_pivot;
        options=SolverOptions(T; algorithm=:primal, pricing=:devex, verbose=false))
    @test result.status == OPTIMAL
    @test result.objective_value == -one(T)

    large_column = LinearProblem(sparse([1e200 1e200]), [-2.0, -1.0];
                                 row_upper=[1e200])
    for pricing in (:steepest_edge, :devex)
        result = solve(large_column;
            options=SolverOptions(; algorithm=:primal, pricing, verbose=false))
        @test result.status == OPTIMAL
        @test result.primal ≈ [1.0, 0.0]
        @test result.objective_value ≈ -2.0
    end
end

@testset "Primal Harris ratio prefers a stable feasible pivot" begin
    problem = LinearProblem(sparse(reshape([1e-4, 1.0], 2, 1)), [-1.0];
                            row_upper=[1e-4, 1.0 + 5e-8])
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(; algorithm=:primal, pricing=:dantzig, verbose=false))
    step, row, state = JSimplex._primal_ratio(workspace, 1, 1.0, [-1e-4, -1.0])
    @test step ≈ 1.0 + 5e-8
    @test row == 2
    @test state == JSimplex.AT_UPPER
    @test isnothing(JSimplex._primal_iteration!(workspace, () -> false, 0.0))
    @test workspace.basis.basic_indices[2] == 1
    @test JSimplex.primal_infeasibility(workspace) <= workspace.options.primal_tolerance
end

@testset "Primal Harris relaxation respects total feasibility and entering bounds" begin
    aggregate = LinearProblem(sparse(reshape([1.0, 1.0, 10.0], 3, 1)), [-1.0];
                              row_upper=[1.0, 1.0, 10.0 + 7.5e-7])
    workspace = JSimplex.initialize_workspace(aggregate,
        SolverOptions(; algorithm=:primal, pricing=:dantzig, verbose=false))
    @test JSimplex._primal_ratio(workspace, 1, 1.0, [-1.0, -1.0, -10.0])[2] == 1

    boxed = LinearProblem(sparse([1.0;;]), [-1.0];
                          row_upper=[1.0 + 5e-8], column_upper=[1.0])
    workspace = JSimplex.initialize_workspace(boxed,
        SolverOptions(; algorithm=:primal, pricing=:dantzig, verbose=false))
    @test JSimplex._primal_ratio(workspace, 1, 1.0, [-1.0]) ==
          (1.0, 0, JSimplex.BASIC)

    T = Rational{BigInt}
    tied = LinearProblem(sparse(reshape(T[1, 2], 2, 1)), T[-1]; row_upper=T[1, 2])
    workspace = JSimplex.initialize_workspace(tied,
        SolverOptions(T; algorithm=:primal, pricing=:dantzig, verbose=false))
    @test JSimplex._primal_ratio(workspace, 1, one(T), T[-1, -2])[2] == 2

    U = Rational{Int64}
    wide_movement = LinearProblem(sparse(U[4_000_000_000;;]), U[-1];
                                  row_upper=U[4_000_000_000])
    options = SolverOptions(U; algorithm=:primal, pricing=:dantzig,
                            primal_tolerance=U(1 // 4_000_000_000), verbose=false)
    result = solve(wide_movement; options)
    @test result.status == OPTIMAL
    @test result.objective_value == -one(U)
end
