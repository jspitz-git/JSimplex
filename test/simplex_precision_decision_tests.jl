using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Higher precision reaches pricing, ratio tests and real pivots" begin
    for update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub), backend in (:native, :markowitz)
        p = LinearProblem(sparse([1e16 1.0 1.0; nextfloat(1e16) 1.0 0.0]), [2.0, 1.0, -1.0];
            column_lower=[nothing, -5e15, 0.0], column_upper=[nothing, nothing, 2.0],
            row_lower=[5e15+1, 5e15+2], row_upper=[5e15+1, 5e15+2])
        observed = Tuple{Int,Int,Int}[]
        diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
            if reason == :pivot_completed
                push!(observed, (minimum(precision, ws.primal),
                    minimum(precision, ws.reduced_costs), minimum(precision, ws.scratch.row_solution)))
            end
        end)
        policy = JSimplex.NumericalPolicy(Float64; simplex_strategy=:adaptive,
            precision_boosting=true, refactor_timing=false)
        options = SolverOptions(; algorithm=:primal, verbose=false, presolve=false, scaling=:off,
            basis_update=update, basis_refactorization=backend, pricing=:devex,
            primal_tolerance=1e-10, dual_tolerance=1e-10)
        progress = JSimplex.SimplexProgressContext(p; diagnostics, numerical_policy=policy)
        basis = JSimplex.Basis([1, 2],
            [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
        ws = JSimplex.initialize_from_basis(p, basis, options; policy, progress)
        run = JSimplex.solve_with_precision_recovery(ws, JSimplex.SimplexRunBudget(ws), policy, ()->false)
        expected = [1.0, -5e15, 1.0]
        exact_A = Matrix(Rational{BigInt}.(p.A))
        exact_x = Rational{BigInt}.(expected)
        @test exact_A * exact_x == Rational{BigInt}.(bound_value.(p.row_lower))
        @test Rational{BigInt}.(p.objective) - exact_A' * Rational{BigInt}[-1, 1] == [0, 1, 0]
        @test run.status == JSimplex.OPTIMAL
        @test run.primal == expected
        @test run.objective_value == 1-5e15
        @test run.iterations >= 1
        @test !isempty(observed)
        @test all(values -> all(>=(128), values), observed)
    end
end

@testset "Float32 first uses a real Float64 workspace" begin
    p = LinearProblem(sparse(Float32[2 1; 1 3]), zeros(Float32, 2);
        column_lower=fill(nothing, 2), column_upper=fill(nothing, 2),
        row_lower=Float32[2, 0], row_upper=Float32[2, 0])
    levels = Int[]
    diagnostics = JSimplex.SimplexDiagnostics(; observer=(reason, ws)->begin
        reason == :precision_boost && push!(levels, precision(first(ws.primal)))
    end)
    policy = JSimplex.NumericalPolicy(Float32; precision_boosting=true)
    options = SolverOptions(Float32; verbose=false)
    progress = JSimplex.SimplexProgressContext(p; diagnostics, numerical_policy=policy)
    basis = JSimplex.Basis([1, 2],
        [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
    ws = JSimplex.initialize_from_basis(p, basis, options; policy, progress)
    run = JSimplex.solve_with_precision_recovery(ws, JSimplex.SimplexRunBudget(ws), policy, ()->false)
    @test run isa JSimplex.DualRunResult{Float32}
    @test run.status == JSimplex.OPTIMAL
    @test levels == [53]
    @test JSimplex._original_primal_feasible(p, run.primal, options.primal_tolerance)
end

@testset "BigFloat recovery preserves stored precision in a lower ambient context" begin
    ws = setprecision(BigFloat, 512) do
        p = LinearProblem(sparse(BigFloat[2 1; 1 3]), zeros(BigFloat, 2);
            column_lower=fill(nothing, 2), column_upper=fill(nothing, 2),
            row_lower=BigFloat[2, 0], row_upper=BigFloat[2, 0])
        policy = JSimplex.NumericalPolicy(BigFloat; precision_boosting=true, max_precision_bits=1024)
        basis = JSimplex.Basis([1, 2],
            [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
        JSimplex.initialize_from_basis(p, basis, SolverOptions(BigFloat; verbose=false); policy)
    end
    run = setprecision(BigFloat, 64) do
        result = JSimplex.solve_with_precision_recovery(ws, JSimplex.SimplexRunBudget(ws),
            ws.progress.numerical_policy, ()->false)
        @test precision(BigFloat) == 64
        result
    end
    @test run isa JSimplex.DualRunResult{BigFloat}
    @test run.status == JSimplex.OPTIMAL
    @test minimum(precision, run.primal) >= 1024
    @test minimum(precision, ws.problem.A.nzval) == 512
end
