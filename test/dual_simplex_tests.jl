using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

function test_typed_dual_kernel(::Type{T}) where {T}
    pivoting = LinearProblem(sparse(T[1 0; -1 1]), T[1, 1]; row_lower=T[1, 1])
    for interval in (1, 20)
        run = @inferred JSimplex._solve_continuous_dual(
            pivoting, SolverOptions(T; refactorization_interval=interval),
        )
        @test run isa JSimplex.DualRunResult{T}
        @test run.status == OPTIMAL
        @test run.primal == T[1, 2]
        @test run.objective_value == T(3)
        @test run.iterations == 2
        @test run.refactorizations == (interval == 1 ? 2 : 0)
    end

    for (problem, expected_primal, expected_objective) in (
        (LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1]; row_upper=T[3]), T[3], T(-3)),
        (LinearProblem(sparse(reshape(T[1], 1, 1)), T[1]; row_lower=T[-3],
                       column_lower=[nothing], column_upper=T[0]), T[-3], T(-3)),
        (LinearProblem(sparse(reshape(T[1], 1, 1)), T[2]; row_lower=T[-3], row_upper=T[4],
                       column_lower=[nothing]), T[-3], T(-6)),
    )
        run = @inferred JSimplex._solve_continuous_dual(problem, SolverOptions(T))
        @test run isa JSimplex.DualRunResult{T}
        @test run.status == OPTIMAL
        @test run.primal == expected_primal
        @test run.objective_value == expected_objective
    end

    for (problem, expected_status) in (
        (LinearProblem(sparse(T[1 0]), T[0, -1]; row_lower=T[1], row_upper=T[1]), UNBOUNDED),
        (LinearProblem(sparse(T[1 -3]), T[-1, 0]; row_lower=T[1], row_upper=T[1]),
         T <: Rational ? UNBOUNDED : NUMERICAL_ERROR),
        (LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1]; row_upper=T[-1]), INFEASIBLE),
        (LinearProblem(spzeros(T, 1, 0), T[]; row_lower=T[1]), INFEASIBLE),
        (LinearProblem(spzeros(T, 0, 0), T[]; objective_constant=T(7)), OPTIMAL),
    )
        run = @inferred JSimplex._solve_continuous_dual(problem, SolverOptions(T))
        @test run isa JSimplex.DualRunResult{T}
        @test run.status == expected_status
        @test expected_status == OPTIMAL ? run.primal == T[] : isnothing(run.primal)
        @test expected_status == OPTIMAL ? run.objective_value == T(7) : isnothing(run.objective_value)
    end

    workspace = JSimplex.initialize_workspace(pivoting, SolverOptions(T))
    row = zeros(T, 4)
    @test (@inferred JSimplex.price!(row, workspace, T[2, -3])) === nothing
    @test row == T[5, -3, -2, 3]
    ratio_problem = LinearProblem(spzeros(T, 1, 3), T[1, 10, 20])
    ratio_workspace = JSimplex.initialize_workspace(ratio_problem, SolverOptions(T))
    @test (@inferred JSimplex.dual_ratio_test(ratio_workspace, T[1, 10, 20, 0])) == 3
    @test (@inferred JSimplex.dual_ratio_test(ratio_workspace, T[-1, -10, -20, 0])) == -1
end

function stale_primal_workspace()
    problem = LinearProblem(sparse([1.0;;]), [1.0];
        row_lower=[1.0], column_upper=[1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    JSimplex.dual_iteration!(workspace, () -> false)
    workspace.primal[1] = 2.0
    return workspace
end

@testset "Dual pivot refreshes a stale floating basis before numerical failure" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    options = SolverOptions(basis_update=:suhl_suhl, zero_tolerance=0.5,
                            verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    # The updated factor is stale: it still solves a basis scaled by ten.
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-10.0;;]))
    JSimplex.recompute!(workspace)
    @test abs(only(JSimplex.forward_solve(workspace.factorization, [1.0]))) <
          options.zero_tolerance

    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test workspace.refactorizations == 1
    @test JSimplex.primal_infeasibility(workspace) <= options.primal_tolerance

    # A genuinely small pivot still fails after one fresh factorization.
    persistent = JSimplex.initialize_workspace(
        problem, SolverOptions(basis_update=:suhl_suhl, zero_tolerance=2.0,
                               verbose=false),
    )
    terminal = JSimplex.dual_iteration!(persistent, () -> false)
    @test terminal.status == NUMERICAL_ERROR
    @test persistent.iterations == 0
    @test persistent.refactorizations == 1
end

@testset "Dual pivot rejects a false nonzero direction from stale factors" begin
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 0.0];
                            row_lower=[1.0, -Inf])
    for false_pivot in (5.0e-7, 5.0e-3)
        workspace = JSimplex.initialize_workspace(
            problem, SolverOptions(basis_update=:suhl_suhl, verbose=false),
        )
        # The actual slack basis is -I. This stale factorization makes the
        # second structural column appear to enter the first basis row.
        workspace.factorization.base = JSimplex._factorize_basis(
            sparse([-1.0 false_pivot; 0.0 -1.0]),
        )
        JSimplex.recompute!(workspace)

        terminal = JSimplex.dual_iteration!(workspace, () -> false)
        @test isnothing(terminal)
        @test workspace.basis.basic_indices == [1, 4]
        @test workspace.refactorizations == 1
    end
end

@testset "Dual ratio test refreshes an inaccurate tableau row" begin
    # The stale LU changes the transposed solve for row 1, while the direction
    # for the selected first column remains exact. A direction-only check misses it.
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 10.0];
                            row_lower=[1.0, -Inf])
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(refactorization_interval=50, verbose=false))
    workspace.factorization.base = JSimplex._factorize_basis(
        sparse([-1.0 1.0e-5; 0.0 -1.0]))
    # One identity update represents a basis that has changed since LU.
    JSimplex.replace_column!(workspace.factorization, [1.0, 0.0], 1)
    JSimplex.recompute!(workspace)

    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test isnothing(terminal)
    @test workspace.basis.basic_indices == [1, 4]
    @test workspace.refactorizations == 1
end

@testset "A clean cycle promptly restores a shortened refactorization interval" begin
    rows = 7
    problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)),
                            collect(1.0:rows); row_lower=ones(rows))
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(refactorization_interval=50, verbose=false))

    function inject_bad_updated_basis!(workspace, leaving_row, coupled_row)
        stale = Matrix(JSimplex.basis_matrix(workspace))
        stale[leaving_row, coupled_row] = 1.0e-5
        workspace.factorization.base = JSimplex._factorize_basis(sparse(stale))
        JSimplex.replace_column!(workspace.factorization,
                                 [1.0; zeros(rows - 1)], 1)
        JSimplex.recompute!(workspace)
    end

    inject_bad_updated_basis!(workspace, 1, 2)
    for step in 1:rows
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        if step == 1
            # One repaired row is isolated and keeps the configured interval.
            @test workspace.refactorizations == 1
            @test length(workspace.factorization.updates) == 1
            inject_bad_updated_basis!(workspace, 2, 1)
        elseif step == 2
            # The second repair makes the next pivot refresh immediately.
            @test workspace.refactorizations == 3
            @test isempty(workspace.factorization.updates)
            @test workspace.dual_refactorization_interval == 1
        elseif step == 3
            # One clean cycle is enough to leave the one-update fallback.
            @test workspace.refactorizations == 4
            @test workspace.dual_refactorization_interval == 2
        elseif step == 5
            # Recovery below the configured target doubles after each clean cycle.
            @test workspace.refactorizations == 5
            @test workspace.dual_refactorization_interval == 4
        elseif step == 7
            @test workspace.refactorizations == 5
            @test length(workspace.factorization.updates) == 2
        end
    end
    @test JSimplex.primal_infeasibility(workspace) == 0.0
    @test workspace.options.refactorization_interval == 50
end

@testset "Clean productive dual pivots lengthen the factorization interval" begin
    rows = 24
    function solve_diagonal_with_costs(costs)
        problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)), costs;
                                row_lower=ones(rows))
        workspace = JSimplex.initialize_workspace(problem,
            SolverOptions(refactorization_interval=2, verbose=false))
        for _ in 1:rows
            @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        end
        @test workspace.iterations == rows
        @test JSimplex.primal_infeasibility(workspace) == 0.0
        @test workspace.options.refactorization_interval == 2
        return workspace
    end

    productive = solve_diagonal_with_costs(collect(1.0:rows))
    @test productive.refactorizations < rows ÷ 2
    degenerate = solve_diagonal_with_costs(zeros(rows))
    @test degenerate.refactorizations == rows ÷ 2
end

@testset "One inaccurate updated row pauses growth without shortening" begin
    rows = 24
    problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)),
                            collect(1.0:rows); row_lower=ones(rows))
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(refactorization_interval=2, verbose=false))
    for _ in 1:6
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    end
    @test workspace.dual_refactorization_interval == 4

    stale = Matrix(JSimplex.basis_matrix(workspace))
    stale[7, 8] = 1.0e-5
    workspace.factorization.base = JSimplex._factorize_basis(sparse(stale))
    JSimplex.replace_column!(workspace.factorization,
                             [1.0; zeros(rows - 1)], 1)
    JSimplex.recompute!(workspace)
    for _ in 7:20
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    end
    @test length(workspace.factorization.updates) == 2
end

@testset "Repairs after growth use the actual failed update counts" begin
    rows = 140
    problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)),
                            collect(1.0:rows); row_lower=ones(rows))
    workspace = JSimplex.initialize_workspace(problem,
        SolverOptions(refactorization_interval=20, verbose=false))

    function corrupt_base!(workspace, structural_rows, leaving_row)
        diagonal = vcat(ones(structural_rows), -ones(rows - structural_rows))
        stale = spdiagm(0 => diagonal)
        stale[leaving_row, leaving_row + 1] = 1.0e-5
        workspace.factorization.base = JSimplex._factorize_basis(stale)
    end

    for _ in 1:90
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    end
    @test workspace.dual_refactorization_interval == 40
    @test length(workspace.factorization.updates) == 30
    corrupt_base!(workspace, 60, 91)
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))

    for _ in 92:115
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    end
    @test length(workspace.factorization.updates) == 25
    corrupt_base!(workspace, 90, 116)
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.dual_refactorization_interval == 12
end

@testset "Dual direction refinement repairs a failed floating solve" begin
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 0.0];
                            row_lower=[1.0, -Inf])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.scratch.row_solution .= [-1.0, 0.5]
    @test JSimplex._try_refine_dual_direction!(workspace, 1, 1, -1.0, -1.0,
                                               () -> false)
    @test workspace.scratch.row_solution == [-1.0, 0.0]

    # Column 2 has no component in row 1, so it cannot replace that slack.
    workspace.scratch.row_solution .= [0.5, -1.0]
    @test !JSimplex._try_refine_dual_direction!(workspace, 2, 1, 0.5, 0.5,
                                                () -> false)
    @test workspace.scratch.row_solution == [0.5, -1.0]
end

@testset "Failed dual pivot can refine its row, direction, and prices together" begin
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 0.0];
                            row_lower=[1.0, -Inf])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.scratch.row_solution .= [-1.01, 0.25]
    workspace.scratch.tableau_row .= [-0.99, 0.0, 1.0, 0.0]
    workspace.reduced_costs[1] = 1.1

    decision = JSimplex._try_refine_dual_pivot!(workspace, 1, -1.0, 1.0,
                                                () -> false)
    @test decision == (entering_index=1, flips=Int[], pivot=-1.0)
    @test workspace.scratch.row_solution == [-1.0, 0.0]
    @test workspace.scratch.tableau_row == [-1.0, 0.0, 1.0, 0.0]
    @test workspace.reduced_costs[1] == 1.0
    @test workspace.scratch.rho == [-1.0, 0.0]

    competing = LinearProblem(sparse([1.0 2.0]), [1.0, 0.1]; row_lower=[1.0])
    other = JSimplex.initialize_workspace(competing, SolverOptions(verbose=false))
    other.scratch.row_solution .= [-1.01]
    other.scratch.tableau_row .= [-0.99, -0.01, 1.0]
    other.reduced_costs[1] = 1.1
    alternate = JSimplex._try_refine_dual_pivot!(other, 1, -1.0, 1.0,
                                                 () -> false)
    @test alternate == (entering_index=2, flips=Int[], pivot=-2.0)
    @test other.reduced_costs[1] == 1.0
    @test other.scratch.tableau_row == [-1.0, -2.0, 1.0]
    @test other.scratch.row_solution == [-2.0]

    # A wrong factorization can make the floating ratio test choose column 2.
    # The complete retry must select column 1 before changing the basis.
    stale = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    stale.factorization.base = JSimplex._factorize_basis(
        sparse([-1.0 0.4; 0.4 -1.0]),
    )
    JSimplex.recompute!(stale)
    @test isnothing(JSimplex._dual_iteration!(stale, () -> false, true))
    @test stale.basis.basic_indices == [1, 4]
    @test stale.iterations == 1
    @test !stale.dual_devex_fallback
    @test stale.pricing_weights[1] ≈ 1.0
end

@testset "Small dual pivot checks the entering price before a cost shift" begin
    for (coefficient, row_bound) in ((6.24213518e-7, :lower),
                                     (-6.24213518e-7, :upper))
        problem = LinearProblem(sparse([coefficient;;]), [-4.6096933e-11];
            row_lower=[row_bound == :lower ? 1.0 : -Inf],
            row_upper=[row_bound == :upper ? -1.0 : Inf])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
        # A stored zero can hide a small adverse price. The resulting dual
        # step is amplified by the near-cutoff pivot.
        workspace.reduced_costs[1] = 0.0
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        @test workspace.iterations == 1
        @test workspace.perturbed
        @test abs(workspace.costs[1]) < 1e-14
        B = JSimplex.basis_matrix(workspace)
        prices = JSimplex._refined_dual_prices(workspace, lu(B), B, 256, () -> false)
        @test JSimplex._dual_price_feasible(workspace.basis.states[2], prices[2],
                                           BigFloat(workspace.options.dual_tolerance))
    end

    # A small backward price is already safe after amplification. Avoid an
    # unnecessary working-cost change that can alter later pivot choices.
    harmless = LinearProblem(sparse([6.24213518e-7;;]), [-4.0e-14];
                             row_lower=[1.0])
    workspace = JSimplex.initialize_workspace(harmless, SolverOptions(verbose=false))
    workspace.reduced_costs[1] = 0.0
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test !workspace.perturbed
    @test workspace.costs[1] == harmless.objective[1]
end

@testset "Dual pivot refreshes before applying bound flips" begin
    problem = LinearProblem(sparse([-1.0 1.0]), [-1.0, 2.0];
                            row_lower=[2.0], column_upper=[1.0, Inf])
    workspace = JSimplex.initialize_workspace(
        problem, SolverOptions(basis_update=:suhl_suhl, verbose=false),
    )
    workspace.basis.states[1] = JSimplex.AT_UPPER
    # A stale solve makes the chosen pivot tiny. The boxed first column
    # crosses an earlier dual breakpoint, so the ratio test proposes a flip.
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-5.0e6;;]))
    JSimplex.recompute!(workspace)

    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test isnothing(terminal)
    @test workspace.refactorizations == 1
    @test workspace.iterations == 1
    @test workspace.basis.states[1] == JSimplex.AT_LOWER
    @test workspace.primal[1:2] ≈ [0.0, 2.0]
    @test JSimplex.dual_infeasibility(workspace) <= workspace.options.dual_tolerance
end

@testset "Dual price refinement releases a harmful cost shift" begin
    for (state, original_cost, working_cost, perturbed, expected_status) in (
        (JSimplex.AT_UPPER, 0.0, 4.0e-7, true, OPTIMAL),
        (JSimplex.AT_LOWER, 0.0, -4.0e-7, true, OPTIMAL),
        (JSimplex.AT_UPPER, 0.0, 4.0e-7, false, NUMERICAL_ERROR),
        (JSimplex.AT_LOWER, 0.0, -4.0e-7, false, NUMERICAL_ERROR),
        (JSimplex.AT_UPPER, 2.0e-7, 4.0e-7, true, NUMERICAL_ERROR),
        (JSimplex.AT_LOWER, -2.0e-7, -4.0e-7, true, NUMERICAL_ERROR),
    )
        problem = LinearProblem(sparse([1.0;;]), [original_cost];
                                row_upper=[2.0], column_upper=[1.0])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
        workspace.basis.states[1] = state
        workspace.costs[1] = working_cost
        workspace.perturbed = perturbed
        JSimplex.recompute!(workspace; refactorize=true)
        @test JSimplex.dual_infeasibility(workspace) > workspace.options.dual_tolerance

        terminal = JSimplex._dual_optimize!(workspace, () -> false)
        @test terminal.status == expected_status
        @test workspace.costs[1] == (expected_status == OPTIMAL ? original_cost : working_cost)
        @test workspace.iterations == 0
        if expected_status == OPTIMAL
            @test JSimplex.dual_infeasibility(workspace) <= workspace.options.dual_tolerance
        end
    end

    # Both signs of a cost shift can be released in a nontrivial basis.
    problem = LinearProblem(sparse([1.0 2.0 3.0]), [1.0, 2.0, 3.0];
                            row_lower=[2.0], row_upper=[2.0],
                            column_upper=[Inf, 1.0, 1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.basis = JSimplex.Basis([1],
        [JSimplex.BASIC, JSimplex.AT_UPPER, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
    workspace.costs[2] += 4.0e-7
    workspace.costs[3] -= 4.0e-7
    workspace.perturbed = true
    JSimplex.recompute!(workspace; refactorize=true)
    @test JSimplex.dual_infeasibility(workspace) > workspace.options.dual_tolerance
    @test JSimplex._try_refine_dual_prices!(workspace, () -> false)
    @test workspace.costs[2:3] == problem.objective[2:3]
    @test JSimplex.dual_infeasibility(workspace) <= workspace.options.dual_tolerance
end

@testset "Dual pivot keeps a full-sized pivot with harmless solve roundoff" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    workspace = JSimplex.initialize_workspace(
        problem, SolverOptions(basis_update=:suhl_suhl, verbose=false),
    )
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-1.0 - 3.0e-12;;]))
    JSimplex.recompute!(workspace)

    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.basis.basic_indices == [1]
    @test workspace.refactorizations == 0
end

@testset "Dual feasibility is checked against a fresh factorization" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    for update in (:pfi, :suhl_suhl)
        workspace = JSimplex.initialize_workspace(
            problem, SolverOptions(basis_update=update, verbose=false),
        )
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        workspace.reduced_costs[2] = -1.0
        @test JSimplex.dual_infeasibility(workspace) > workspace.options.dual_tolerance
        terminal = JSimplex._dual_optimize!(workspace, () -> false)
        @test terminal.status == OPTIMAL
        @test workspace.refactorizations == 1

        workspace.costs[2] = -2.0
        JSimplex.recompute!(workspace)
        @test JSimplex.dual_infeasibility(workspace) > workspace.options.dual_tolerance
        terminal = JSimplex._dual_optimize!(workspace, () -> false)
        @test terminal.status == NUMERICAL_ERROR
        @test workspace.refactorizations == 1
    end
end

@testset "Ill-conditioned fresh basis does not invent dual infeasibility" begin
    magnitude = 100_000_001.0
    basis_columns = [1.0 magnitude 0.0;
                     0.0 1.0 magnitude;
                     0.0 0.0 1.0]
    entering_column = [0.0, -1.5magnitude, -1.5]
    matrix = sparse(hcat(basis_columns, entering_column))
    for (cost, expected_status) in ((0.5, OPTIMAL), (-0.5, NUMERICAL_ERROR))
        problem = LinearProblem(matrix, [1.0, 0.0, 0.0, cost];
                                row_lower=zeros(3), row_upper=zeros(3))
        workspace = JSimplex.initialize_workspace(
            problem, SolverOptions(basis_update=:suhl_suhl, verbose=false),
        )
        workspace.basis = JSimplex.Basis([1, 2, 3],
            [JSimplex.BASIC, JSimplex.BASIC, JSimplex.BASIC,
             JSimplex.AT_LOWER, JSimplex.AT_LOWER,
             JSimplex.AT_LOWER, JSimplex.AT_LOWER])
        JSimplex.recompute!(workspace; refactorize=true)
        @test workspace.reduced_costs[4] < -workspace.options.dual_tolerance
        exact_cost = setprecision(BigFloat, 256) do
            y = transpose(BigFloat.(basis_columns)) \ BigFloat[1, 0, 0]
            BigFloat(cost) - sum(BigFloat(entering_column[i]) * y[i] for i in 1:3)
        end
        @test exact_cost == BigFloat(cost)

        terminal = JSimplex._dual_optimize!(workspace, () -> false)
        @test terminal.status == expected_status
        if expected_status == OPTIMAL
            @test workspace.reduced_costs[4] == cost
            @test JSimplex.dual_infeasibility(workspace) == 0.0
        end
    end
end

@testset "Optimal results certify the original structural primal" begin
    unstable = LinearProblem(
        sparse([1.0 1.0; 1.0 1.0 + 1.0e-6]), zeros(2);
        row_lower=[0.1, 1.0e10], row_upper=[0.1, 1.0e10],
        column_lower=fill(-Inf, 2),
    )
    regular = LinearProblem(
        sparse([0.1 0.2; 0.2 -0.1]), [1.0, 2.0];
        row_lower=[0.3, 0.1], row_upper=[0.3, 0.1],
        column_lower=fill(-Inf, 2),
    )
    for interval in (1, 20)
        run = JSimplex._solve_continuous_dual(unstable, SolverOptions(refactorization_interval=interval))
        @test run.status == NUMERICAL_ERROR
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)

        run = JSimplex._solve_continuous_dual(regular, SolverOptions(refactorization_interval=interval))
        @test run.status == OPTIMAL
        @test run.primal ≈ [1.0, 1.0] atol=1.0e-7
        @test regular.A * run.primal ≈ [0.3, 0.1] atol=1.0e-7
        @test run.objective_value ≈ 3.0 atol=1.0e-7
    end

    column_problem = LinearProblem(spzeros(0, 1), [0.0]; column_upper=[1.0])
    row_problem = LinearProblem(sparse([1.0;;]), [0.0]; row_lower=[0.0], row_upper=[1.0],
                                column_lower=[-Inf])
    for problem in (column_problem, row_problem)
        for (value, expected) in ((-2.0e-7, NUMERICAL_ERROR), (1.0 + 2.0e-7, NUMERICAL_ERROR),
                                  (-5.0e-8, OPTIMAL), (1.0 + 5.0e-8, OPTIMAL))
            workspace = JSimplex.initialize_workspace(problem, SolverOptions())
            workspace.primal[1] = value
            run = JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
            @test run.status == expected
            @test isnothing(run.primal) == (expected != OPTIMAL)
            @test isnothing(run.objective_value) == (expected != OPTIMAL)
        end
    end
    overflow = LinearProblem(sparse([1.0e308;;]), [0.0])
    workspace = JSimplex.initialize_workspace(overflow, SolverOptions())
    workspace.primal[1] = 2.0
    run = JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
    @test run.status == NUMERICAL_ERROR
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
end

@testset "Caller callback exceptions retain their provenance" begin
    main_problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    phase_problem = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
    for exception in (SingularException(7), ZeroPivotException(7))
        # Cover entry, main iterations, phase I, and both refactorization sites.
        for (problem, interval, positions) in ((main_problem, 1, 1:6), (phase_problem, 20, 1:7))
            for position in positions
                calls = Ref(0)
                callback = () -> (calls[] += 1; calls[] == position ? throw(exception) : false)
                caught = try
                    JSimplex._solve_continuous_dual(problem, SolverOptions(refactorization_interval=interval);
                                                  stop_requested=callback)
                    nothing
                catch error
                    error
                end
                @test caught === exception
            end
        end
        workspace = JSimplex.initialize_workspace(main_problem, SolverOptions(refactorization_interval=1))
        callback = () -> workspace.iterations == 1 ? throw(exception) : false
        caught = try
            JSimplex.dual_iteration!(workspace, callback)
            nothing
        catch error
            error
        end
        @test caught === exception

        workspace = JSimplex.initialize_workspace(phase_problem, SolverOptions())
        calls = Ref(0)
        callback = () -> (calls[] += 1; calls[] == 5 ? throw(exception) : false)
        caught = try
            JSimplex.make_dual_feasible!(workspace, callback)
            nothing
        catch error
            error
        end
        @test caught === exception
    end
end

@testset "Dual simplex core" begin
    bounded = LinearProblem(
        sparse(reshape([1.0, 1.0], 1, 2)), [1.0, 2.0];
        row_lower=[1.0], row_upper=[Inf],
    )
    bounded_run = JSimplex._solve_continuous_dual(bounded, SolverOptions())
    @test bounded_run.status == OPTIMAL
    @test bounded_run.objective_value ≈ 1.0 atol=1.0e-7
    @test bounded_run.primal ≈ [1.0, 0.0] atol=1.0e-7

    infeasible = LinearProblem(
        sparse(reshape([1.0], 1, 1)), [1.0];
        row_lower=[2.0], row_upper=[Inf],
        column_lower=[0.0], column_upper=[1.0],
    )
    @test JSimplex._solve_continuous_dual(infeasible, SolverOptions()).status ==
          INFEASIBLE

    unbounded = LinearProblem(
        spzeros(0, 1), [-1.0];
        column_lower=[0.0], column_upper=[Inf],
    )
    @test JSimplex._solve_continuous_dual(unbounded, SolverOptions()).status ==
          UNBOUNDED
end

@testset "Rejected small pivots are numerical failures" begin
    for (coefficient, status) in ((1.0e-8, NUMERICAL_ERROR), (0.0, INFEASIBLE), (-1.0e-8, INFEASIBLE))
        problem = LinearProblem(sparse([coefficient;;]), [1.0]; row_lower=[1.0])
        run = JSimplex._solve_continuous_dual(problem, SolverOptions())
        @test run.status == status
        @test run.iterations == 0
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
    end
end

@testset "An auxiliary bound violation cannot certify an improving direction" begin
    problem = LinearProblem(sparse([1.0e-8;;]), [-1.0]; row_upper=[1.0])
    run = JSimplex._solve_continuous_dual(problem, SolverOptions())
    @test run.status == NUMERICAL_ERROR
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
end

@testset "Exact nonzero coefficients cannot certify impossible LP statuses" begin
    for (coefficient, cost, lower, upper, row_lower, row_upper, status) in (
        (1.0e-13, 1.0, 0.0, Inf, 1.0, Inf, NUMERICAL_ERROR),
        (1.0e-12, 1.0, 0.0, Inf, 1.0, Inf, NUMERICAL_ERROR),
        (-1.0e-13, -1.0, -Inf, 0.0, 1.0, Inf, NUMERICAL_ERROR),
        (1.0e-13, -1.0, 0.0, Inf, -Inf, 1.0, NUMERICAL_ERROR),
        (1.0e-12, -1.0, 0.0, Inf, -Inf, 1.0, NUMERICAL_ERROR),
        (-1.0e-13, 1.0, -Inf, 0.0, -Inf, 1.0, NUMERICAL_ERROR),
        (1.0e-13, -1.0, 0.0, Inf, 1.0, 1.0, NUMERICAL_ERROR),
        (0.0, 1.0, 0.0, Inf, 1.0, Inf, INFEASIBLE),
        (-1.0e-13, 1.0, 0.0, Inf, 1.0, Inf, INFEASIBLE),
        (0.0, -1.0, 0.0, Inf, -Inf, 1.0, UNBOUNDED),
        (-1.0e-13, -1.0, 0.0, Inf, -Inf, 1.0, UNBOUNDED),
        (1.0e-13, -1.0, 0.0, Inf, 0.0, Inf, UNBOUNDED),
    )
        problem = LinearProblem(sparse([coefficient;;]), [cost];
            row_lower=[row_lower], row_upper=[row_upper],
            column_lower=[lower], column_upper=[upper])
        for run in (JSimplex._solve_continuous_dual(problem, SolverOptions()), solve(problem))
            @test run.status == status
            @test isnothing(run.primal)
            @test isnothing(run.objective_value)
        end
    end
end

@testset "Scaling certifies a feasible zero-cost model with a tiny coefficient" begin
    problem = LinearProblem(sparse([1.0e-13;;]), [0.0];
        row_lower=[1.0], column_lower=[-Inf], column_upper=[Inf])
    @test JSimplex._solve_continuous_dual(problem, SolverOptions()).status == NUMERICAL_ERROR
    @test solve(problem; options=SolverOptions(scaling=:off)).status == NUMERICAL_ERROR
    scaled = solve(problem; options=SolverOptions(scaling=:on))
    @test scaled.status == OPTIMAL
    @test scaled.primal == [1.0e13]
    @test scaled.objective_value == 0.0
    @test JSimplex._original_primal_feasible(problem, something(scaled.primal), 1.0e-7)
end

@testset "Auxiliary workspaces own their factorization backend" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    auxiliary = JSimplex._auxiliary_workspace(workspace)

    JSimplex.refactorize!(auxiliary.factorization, sparse([2.0;;]))

    @test JSimplex.forward_solve(workspace.factorization, [1.0]) == [-1.0]
end

@testset "Recession certification rejects unresolved row dot products" begin
    uncertain_cancellation = (
        LinearProblem(sparse([1.0 -3.0]), [-1.0, 0.0]; row_lower=[0.0], row_upper=[0.0]),
        LinearProblem(sparse([1.0e6 -3.0e6]), [-1.0, 0.0]; row_lower=[0.0], row_upper=[0.0]),
        LinearProblem(sparse([0.1 -0.3]), [-1.0, 0.0]; row_lower=[0.0], row_upper=[0.0]),
        LinearProblem(sparse([1.0 -3.0]), [-1.0, 0.0]; row_upper=[0.0]),
        LinearProblem(sparse([-1.0 3.0]), [-1.0, 0.0]; row_lower=[0.0]),
        LinearProblem(sparse([1.0 -3.0]), [1.0, 0.0]; row_lower=[0.0], row_upper=[0.0],
                      column_lower=[-Inf, -Inf], column_upper=[0.0, 0.0]),
        LinearProblem(sparse([1.0 -3.0 0.0; 1.0 0.0 -7.0]), [-1.0, 0.0, 0.0];
                      row_lower=[0.0, 0.0], row_upper=[0.0, 0.0]),
    )
    ambiguous = (
        LinearProblem(sparse([1.0e-13;;]), [1.0]; row_lower=[1.0]),
        LinearProblem(sparse([1.0e-13;;]), [-1.0]; row_upper=[1.0]),
        LinearProblem(sparse([1.0e6 -3.0e6; 1.0e-13 0.0]), [-1.0, 0.0];
                      row_lower=[0.0, -Inf], row_upper=[0.0, 1.0]),
        LinearProblem(sparse([1.0e6 -3.0e6; -1.0e-13 0.0]), [-1.0, 0.0];
                      row_lower=[0.0, -1.0], row_upper=[0.0, Inf]),
    )
    conclusive = (
        LinearProblem(spzeros(1, 1), [-1.0]; row_lower=[0.0], row_upper=[0.0]),
        LinearProblem(spzeros(0, 1), [-1.0]),
    )
    for (problems, status) in ((uncertain_cancellation, NUMERICAL_ERROR),
                               (ambiguous, NUMERICAL_ERROR), (conclusive, UNBOUNDED))
        for problem in problems, interval in (1, 20)
            options = SolverOptions(refactorization_interval=interval)
            for run in (JSimplex._solve_continuous_dual(problem, options), solve(problem; options))
                @test run.status == status
                @test isnothing(run.primal)
                @test isnothing(run.objective_value)
            end
        end
    end
end

@testset "Recession roundoff bounds preserve ambiguous and invalid directions" begin
    problem = LinearProblem(sparse([1.0 -3.0]), [-1.0, 0.0];
                            row_lower=[0.0], row_upper=[0.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    for (direction, status) in (([1.0, 1.0 / 3.0], :ambiguous),
                               ([1.0, (1.0 - 1.0e-13) / 3.0], :ambiguous),
                               ([1.0, (1.0 - 1.0e-8) / 3.0], :invalid),
                               ([NaN, 0.0], :invalid), ([Inf, 0.0], :invalid))
        auxiliary.primal[1:2] .= direction
        @test JSimplex._recession_direction_status(workspace, auxiliary) == status
    end
    overflow = LinearProblem(sparse([1.0e308 -1.0e308]), [-1.0, 0.0];
                             row_lower=[0.0], row_upper=[0.0])
    workspace = JSimplex.initialize_workspace(overflow, SolverOptions())
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    auxiliary.primal[1:2] .= [1.0, 1.0]
    @test JSimplex._recession_direction_status(workspace, auxiliary) != :certified
end

@testset "Phase I stops before either refactorization" begin
    problem = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0])
    for (interval, stop_check) in ((1, 4), (20, 5))
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(refactorization_interval=interval))
        checks = Ref(0)
        terminal = JSimplex.make_dual_feasible!(workspace, () -> (checks[] += 1; checks[] >= stop_check))
        @test terminal.status == TIME_LIMIT
        @test workspace.iterations == 1
        @test workspace.refactorizations == 0
        @test workspace.basis.basic_indices == [2]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, workspace.lower) == [0.0, nothing]
        @test map(bound -> isfinite(bound) ? bound_value(bound) : nothing, workspace.upper) == [nothing, 3.0]
    end
    run = JSimplex._solve_continuous_dual(problem, SolverOptions(zero_tolerance=2.0))
    @test run.status == NUMERICAL_ERROR
    @test run.iterations == 0
end

@testset "Feasibility restoration detects overflow from a bound flip" begin
    problem = LinearProblem(sparse([1.0e308;;]), [-1.0]; column_upper=[2.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    terminal = JSimplex.make_dual_feasible!(workspace, () -> false)
    @test terminal isa JSimplex.DualTermination
    if terminal isa JSimplex.DualTermination
        @test terminal.status == NUMERICAL_ERROR
    end
    @test workspace.iterations == 0
end

@testset "Cost shifting respects upper, free, and fixed columns" begin
    for (coefficient, lower, upper, shifted) in (
        (-1.0e-8, -Inf, 0.0, true),
        (1.0e-8, -Inf, Inf, true),
        (-1.0e-8, -Inf, Inf, true),
        (1.0e-8, 0.0, 0.0, false),
    )
        problem = LinearProblem(sparse([1.0 coefficient]), [100.0, 0.0];
            row_lower=[1.0], column_lower=[0.0, lower], column_upper=[Inf, upper])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions())
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        @test workspace.perturbed == shifted
        @test JSimplex.dual_infeasibility(workspace) == 0.0
        @test workspace.costs[2] ≈ (shifted ? 100.0 * coefficient : 0.0)
        @test problem.objective == [100.0, 0.0]
    end
end

@testset "Iteration limits and deadline boundaries" begin
    problem = LinearProblem(
        sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
        row_lower=[1.0, 1.0], row_upper=[Inf, Inf],
    )
    for limit in 0:2
        run = JSimplex._solve_continuous_dual(
            problem, SolverOptions(iteration_limit=limit, refactorization_interval=1),
        )
        @test run.status == (limit < 2 ? ITERATION_LIMIT : OPTIMAL)
        @test run.iterations == limit
        @test run.refactorizations == limit
        @test isnothing(run.primal) == (limit < 2)
        @test isnothing(run.objective_value) == (limit < 2)
    end
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(refactorization_interval=1))
    terminal = JSimplex.dual_iteration!(workspace, () -> workspace.iterations == 1)
    @test terminal.status == TIME_LIMIT
    @test workspace.iterations == 1
    @test workspace.refactorizations == 0
    @test length(workspace.factorization.updates) == 1
    @test workspace.primal ≈ [1.0, 0.0, 1.0, -1.0]
    run = JSimplex._internal_solution(workspace, terminal)
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
    @test run.iterations == 1

    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    terminal = JSimplex._dual_optimize!(workspace, () -> workspace.iterations == 1)
    @test terminal.status == TIME_LIMIT
    @test workspace.iterations == 1

    phase_problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [-1.0, -1.0]; row_upper=[1.0, 2.0])
    for limit in 0:2
        run = JSimplex._solve_continuous_dual(phase_problem, SolverOptions(iteration_limit=limit))
        @test run.status == (limit < 2 ? ITERATION_LIMIT : OPTIMAL)
        @test run.iterations == limit
    end
    workspace = JSimplex.initialize_workspace(phase_problem, SolverOptions())
    checks = Ref(0)
    stop_in_phase = () -> (checks[] += 1; checks[] >= 4)
    terminal = JSimplex.make_dual_feasible!(workspace, stop_in_phase)
    @test terminal.status == TIME_LIMIT
    @test workspace.iterations == 1
    @test workspace.refactorizations == 0

    run = JSimplex._solve_continuous_dual(problem, SolverOptions(); stop_requested=() -> true)
    @test run.status == TIME_LIMIT
    @test run.iterations == 0
    @test run.refactorizations == 0
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
end

@testset "Zero rows, zero variables, and objective result ownership" begin
    for (costs, lower, upper, expected, objective) in (
        ([-2.0, 3.0], [0.0, -4.0], [5.0, Inf], [5.0, -4.0], -15.0),
        ([0.0, 2.0], [-Inf, 3.0], [Inf, 3.0], [0.0, 3.0], 13.0),
        (Float64[], Float64[], Float64[], Float64[], 7.0),
    )
        problem = LinearProblem(spzeros(0, length(costs)), costs;
                                column_lower=lower, column_upper=upper, objective_constant=7.0)
        run = JSimplex._solve_continuous_dual(problem, SolverOptions(iteration_limit=0))
        @test run.status == OPTIMAL
        @test run.primal == expected
        @test run.objective_value == objective
        @test run.iterations == 0
    end
    for (cost, lower, upper) in ((-1.0, 0.0, Inf), (1.0, -Inf, 0.0), (1.0e-10, -Inf, Inf))
        problem = LinearProblem(spzeros(0, 1), [cost]; column_lower=[lower], column_upper=[upper])
        run = JSimplex._solve_continuous_dual(problem, SolverOptions())
        @test run.status == UNBOUNDED
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
    end
    for (lower, upper, status) in (([-1.0], [1.0], OPTIMAL), ([1.0], [2.0], INFEASIBLE))
        problem = LinearProblem(spzeros(1, 0), Float64[];
                                row_lower=lower, row_upper=upper, objective_constant=4.0)
        run = JSimplex._solve_continuous_dual(problem, SolverOptions())
        @test run.status == status
        @test run.iterations == 0
        @test status == OPTIMAL ? run.objective_value == 4.0 : isnothing(run.objective_value)
    end
    problem = LinearProblem(sparse([1.0;;]), [2.0]; row_lower=[3.0], objective_constant=7.0)
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    JSimplex.dual_iteration!(workspace, () -> false)
    run = JSimplex._internal_solution(workspace, OPTIMAL, "optimal")
    @test run.objective_value == 13.0
    workspace.primal[1] = 99.0
    @test run.primal == [3.0]
    for status in (INFEASIBLE, UNBOUNDED, ITERATION_LIMIT, TIME_LIMIT, NUMERICAL_ERROR)
        run = JSimplex._internal_solution(workspace, status, "terminated")
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
    end
end

@testset "Numerical failure classification" begin
    for problem in (
        LinearProblem(sparse([1.0e308;;]), [1.0]; column_lower=[2.0]),
        LinearProblem(sparse([2.0e-7;;]), [1.0]; row_lower=[1.0e308]),
        LinearProblem(spzeros(0, 1), [1.0e308]; column_lower=[2.0], column_upper=[2.0]),
    )
        run = JSimplex._solve_continuous_dual(problem, SolverOptions())
        @test run.status == NUMERICAL_ERROR
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
    end
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    run = JSimplex._solve_continuous_dual(problem, SolverOptions(zero_tolerance=2.0))
    @test run.status == NUMERICAL_ERROR
    @test run.iterations == 0
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)

    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    workspace.factorization.base = JSimplex.UMFPACKBackend(
        lu(spzeros(1, 1); check=false), 1,
    )
    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    for field in (:primal, :reduced_costs)
        workspace = JSimplex.initialize_workspace(problem, SolverOptions())
        getfield(workspace, field)[1] = NaN
        terminal = JSimplex.dual_iteration!(workspace, () -> false)
        @test terminal.status == NUMERICAL_ERROR
        @test workspace.iterations == 0
    end
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(pricing=:devex))
    workspace.pricing_weights[1] = NaN
    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test_throws ArgumentError JSimplex._solve_continuous_dual(
        problem, SolverOptions(); stop_requested=() -> throw(ArgumentError("callback failure")),
    )
end

@testset "Bound flips and auxiliary dual feasibility" begin
    boxed = LinearProblem(
        sparse([1.0;;]), [-1.0]; row_upper=[3.0], column_upper=[2.0],
    )
    workspace = JSimplex.initialize_workspace(boxed, SolverOptions())
    @test isnothing(JSimplex.make_dual_feasible!(workspace, () -> false))
    @test workspace.basis.states[1] == JSimplex.AT_UPPER
    @test workspace.primal == [2.0, 2.0]
    @test workspace.iterations == 0
    @test workspace.refactorizations == 0
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    for (problem, expected_primal, expected_objective) in (
        (LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[3.0]), [3.0], -3.0),
        (LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[-3.0],
                       column_lower=[-Inf], column_upper=[0.0]), [-3.0], -3.0),
        (LinearProblem(sparse([1.0;;]), [2.0]; row_lower=[-3.0], row_upper=[4.0],
                       column_lower=[-Inf], column_upper=[Inf]), [-3.0], -6.0),
        (LinearProblem(sparse([1.0;;]), [-2.0]; row_lower=[-3.0], row_upper=[4.0],
                       column_lower=[-Inf], column_upper=[Inf]), [4.0], -8.0),
    )
        before = deepcopy(problem)
        workspace = JSimplex.initialize_workspace(problem, SolverOptions())
        lower, upper = copy(workspace.lower), copy(workspace.upper)
        @test isnothing(JSimplex.make_dual_feasible!(workspace, () -> false))
        @test workspace.problem === problem
        @test workspace.lower == lower
        @test workspace.upper == upper
        @test JSimplex.dual_infeasibility(workspace) == 0.0
        @test workspace.basis.basic_indices == [1]
        @test workspace.iterations == 1
        @test workspace.refactorizations == 1
        @test workspace.primal[1:1] ≈ expected_primal
        @test workspace.pricing_weights[1] ≈ 1.0
        run = JSimplex._solve_continuous_dual(problem, SolverOptions())
        @test run.status == OPTIMAL
        @test run.primal ≈ expected_primal
        @test run.objective_value ≈ expected_objective
        for field in fieldnames(typeof(problem))
            @test getfield(problem, field) == getfield(before, field)
        end
    end
end

@testset "Recession direction requires primal feasibility" begin
    for (problem, status) in (
        (LinearProblem(sparse([1.0;;]), [-1.0]; row_lower=[2.0]), UNBOUNDED),
        (LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[-1.0]), INFEASIBLE),
        (LinearProblem(sparse([1.0 0.0]), [0.0, -1.0]; row_upper=[-1.0]), INFEASIBLE),
        (LinearProblem(sparse([1.0 -1.0 0.0]), [0.0, 0.0, -1.0];
                       row_lower=[1.0], row_upper=[1.0]), UNBOUNDED),
    )
        run = JSimplex._solve_continuous_dual(problem, SolverOptions(iteration_limit=20))
        @test run.status == status
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
    end
end

@testset "Recession feasibility is certified in the original model" begin
    for (lower, upper, status) in ((0.1, 0.1, NUMERICAL_ERROR),
                                  (0.1, Inf, NUMERICAL_ERROR),
                                  (0.0, 0.0, UNBOUNDED))
        problem = LinearProblem(sparse([1.0 1.0 0.0]), [0.0, 0.0, -1.0];
            row_lower=[lower], row_upper=[upper],
            column_lower=[0.0, -1.0e16, 0.0], column_upper=[1.0e16, -1.0e16, Inf])
        for interval in (1, 20)
            options = SolverOptions(refactorization_interval=interval)
            direct = JSimplex._solve_continuous_dual(problem, options)
            @test direct.status == status
            @test isnothing(direct.primal)
            @test isnothing(direct.objective_value)
            public_result = solve(problem; options)
            @test public_result.status == (lower == 0.1 ? INFEASIBLE : status)
            @test isnothing(public_result.primal)
            @test isnothing(public_result.objective_value)
        end
    end
end

@testset "Cost shifts preserve dual feasibility and are removed before certification" begin
    near_zero = LinearProblem(sparse([1.0;;]), [-5.0e-8]; row_lower=[1.0])
    workspace = JSimplex.initialize_workspace(near_zero, SolverOptions())
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.perturbed
    @test workspace.costs[1] ≈ 0.0 atol=1.0e-15
    @test near_zero.objective == [-5.0e-8]
    @test workspace.reduced_costs[2] >= 0.0

    weak_column = LinearProblem(sparse([1.0 1.0e-8]), [100.0, 0.0]; row_lower=[1.0])
    workspace = JSimplex.initialize_workspace(weak_column, SolverOptions())
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.perturbed
    @test JSimplex.dual_infeasibility(workspace) == 0.0
    @test workspace.costs[2] > 0.0
    @test weak_column.objective == [100.0, 0.0]
    run = JSimplex._solve_continuous_dual(weak_column, SolverOptions())
    @test run.status == OPTIMAL
    @test run.primal == [0.0, 1.0e8]
    @test run.objective_value == 0.0
end

@testset "Original costs are optimized from a perturbed primal-feasible basis" begin
    for (original_cost, shifted_cost, starting_state, expected_x) in (
        (-4.0e-7, 4.0e-7, JSimplex.AT_LOWER, 1.0),
        (4.0e-7, -4.0e-7, JSimplex.AT_UPPER, 0.0),
    )
        problem = LinearProblem(sparse([1.0 1.0]), [original_cost, 0.0];
                                row_lower=[1.0], row_upper=[1.0],
                                column_upper=[1.0, 1.0])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
        workspace.basis = JSimplex.Basis([2],
            [starting_state, JSimplex.BASIC, JSimplex.AT_LOWER])
        workspace.costs[1] = shifted_cost
        workspace.perturbed = true
        workspace.dual_devex_fallback = true
        JSimplex.recompute!(workspace; refactorize=true)
        @test JSimplex.primal_infeasibility(workspace) == 0.0
        @test JSimplex.dual_infeasibility(workspace) == 0.0

        run = JSimplex._solve_continuous_dual!(workspace, () -> false)
        @test run.status == OPTIMAL
        @test run.primal ≈ [expected_x, 1.0 - expected_x]
        @test run.objective_value ≈ original_cost * expected_x
        @test run.iterations == 1
        @test !workspace.perturbed
        @test !workspace.dual_devex_fallback
    end
end

@testset "Dual edge selection and full pricing" begin
    problem = LinearProblem(
        sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
        row_lower=[2.0, 3.0], row_upper=[Inf, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    @test JSimplex.dual_edge_selection(workspace) == 2
    workspace.pricing_weights[4] = 4.0
    @test JSimplex.dual_edge_selection(workspace) == 1

    dantzig = JSimplex.initialize_workspace(problem, SolverOptions(pricing=:dantzig))
    dantzig.pricing_weights[4] = 4.0
    @test JSimplex.dual_edge_selection(dantzig) == 2

    devex = JSimplex.initialize_workspace(problem, SolverOptions(pricing=:devex))
    devex.pricing_weights[4] = 4.0
    @test JSimplex.dual_edge_selection(devex) == 1
    workspace.primal[3:4] .= [2.0, 3.0]
    @test JSimplex.dual_edge_selection(workspace) == -1
    row = fill(NaN, 4)
    @test isnothing(JSimplex.price!(row, workspace, [2.0, -3.0]))
    @test row == [5.0, -3.0, -2.0, 3.0]
end

@testset "Inaccurate dual steepest-edge weight restarts pricing with Devex" begin
    problem = LinearProblem(
        sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0]; row_lower=[1.0, 1.0],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    # The second row would win with this stale weight; after resetting the
    # reference, the first row wins the equal-violation tie.
    workspace.pricing_weights[4] = 0.1
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.basis.basic_indices == [1, 4]
    @test workspace.dual_devex_fallback
    @test !workspace.dual_pricing_fallback
    @test workspace.devex_reference == BitVector([false, false, true, true])
    @test all(weight -> isfinite(weight) && weight > 0, workspace.pricing_weights)

    clean = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    @test isnothing(JSimplex.dual_iteration!(clean, () -> false))
    @test !clean.dual_devex_fallback
end

@testset "Non-finite DSE weights recover through Devex" begin
    problem = LinearProblem(sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
                            row_lower=[1.0, 1.0])
    workspace = JSimplex.initialize_workspace(
        problem, SolverOptions(verbose=false, refactorization_interval=1),
    )
    workspace.pricing_weights[4] = NaN
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.dual_devex_fallback
    @test workspace.basis.basic_indices == [1, 4]
    @test workspace.devex_reference == BitVector([true, false, false, true])
    @test all(isone, workspace.pricing_weights)
end

@testset "DSE update overflow includes the current pivot in Devex" begin
    problem = LinearProblem(sparse(reshape([1.0, 0.0], 2, 1)), [1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    @test JSimplex.update_dual_pricing_weights!(
        workspace, [1.0e150, 0.0], [0.0, 1.0, 0.0], [1.0e10, 1.0],
        1, 1.0, 1.0e300, () -> false,
    )
    @test workspace.dual_devex_fallback
    @test workspace.devex_reference == BitVector([false, true, true])
    @test workspace.pricing_weights[1] == 1.0
    @test workspace.pricing_weights[2] == 1.0e20
    @test all(isfinite, workspace.pricing_weights)
end

@testset "A prolonged dual zero-step stall perturbs costs and restores the LP" begin
    problem = LinearProblem(
        sparse([1.0 0.0 0.0; 0.0 1.0 0.0; 0.0 0.0 1.0]),
        zeros(3); row_lower=[-Inf, 1.0, 1.0],
        column_lower=[nothing, 0.0, 0.0],
        column_upper=[0.0, nothing, nothing],
    )
    options = SolverOptions(pricing=:dantzig, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    workspace.zero_dual_step_streak = 1023
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.iterations == 1
    @test workspace.perturbed
    @test workspace.costs[1] < 0.0
    @test workspace.costs[3] > 0.0
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    run = JSimplex._solve_continuous_dual!(workspace, () -> false)
    @test run.status == OPTIMAL
    @test run.objective_value == 0.0
    @test workspace.primal[2:3] == [1.0, 1.0]
    @test all(iszero, workspace.costs)

    no_stall = JSimplex.initialize_workspace(problem, options)
    no_stall.zero_dual_step_streak = 1022
    @test isnothing(JSimplex.dual_iteration!(no_stall, () -> false))
    @test !no_stall.perturbed
    @test all(iszero, no_stall.costs)

    exact = LinearProblem(sparse(Rational{BigInt}[1 0; 0 1]),
                          zeros(Rational{BigInt}, 2);
                          row_lower=ones(Rational{BigInt}, 2))
    rational = JSimplex.initialize_workspace(
        exact, SolverOptions(Rational{BigInt}; pricing=:dantzig, verbose=false),
    )
    rational.zero_dual_step_streak = 1023
    @test isnothing(JSimplex.dual_iteration!(rational, () -> false))
    @test !rational.perturbed
end

@testset "Anti-degeneracy skips a cost shift larger than its tolerance scale" begin
    problem = LinearProblem(sparse([1.0 1.0]), [1.0e20, 1.0e20];
                            row_lower=[1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.basis = JSimplex.Basis(
        [1], JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER,
                                    JSimplex.AT_LOWER],
    )
    JSimplex.recompute!(workspace; refactorize=true)
    @test workspace.reduced_costs[2] == 0.0
    original_costs = copy(workspace.costs)
    @test JSimplex._perturb_degenerate_dual_costs!(workspace, () -> false) == 0
    @test workspace.costs == original_costs
    @test !workspace.perturbed
end

@testset "Auxiliary dual iterations do not perturb costs across artificial bounds" begin
    problem = LinearProblem(sparse([1.0 0.0 0.0; 0.0 1.0 0.0]), zeros(3);
                            row_lower=zeros(2), row_upper=zeros(2),
                            column_lower=zeros(3))
    workspace = JSimplex.initialize_workspace(
        problem, SolverOptions(pricing=:dantzig, verbose=false),
    )
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    auxiliary.basis.states[1:3] .= JSimplex.AT_UPPER
    JSimplex.recompute!(auxiliary)
    auxiliary.zero_dual_step_streak = 1023
    @test JSimplex.primal_infeasibility(auxiliary) == 2.0
    @test isnothing(JSimplex.dual_iteration!(auxiliary, () -> false;
                                             perturb_degenerate=false))
    @test auxiliary.iterations == 1
    @test JSimplex.primal_infeasibility(auxiliary) == 1.0
    @test !auxiliary.perturbed
    @test all(iszero, auxiliary.costs)
end

@testset "Dual Devex reference weights" begin
    for T in (Float64, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 0 1]), T[0, 0])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T; pricing=:devex))
        @test workspace.devex_reference == BitVector([false, false, true, true])

        tableau_row = T[2, 3, -1, 4]
        tableau_column = T[2, 2]
        JSimplex.update_devex!(workspace, tableau_row, tableau_column, 1, T(2))
        @test workspace.pricing_weights[1] == T(17 // 4)
        @test workspace.pricing_weights[4] == T(17)

        workspace.basis = JSimplex.Basis(
            [1, 4],
            JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER,
                                   JSimplex.AT_LOWER, JSimplex.BASIC],
        )
        JSimplex.reset_devex!(workspace)
        @test workspace.devex_reference == BitVector([true, false, false, true])
        @test all(isone, workspace.pricing_weights)
    end
end

@testset "Pricing strategies update only their required weights" begin
    problem = LinearProblem(sparse(reshape([0.5, 1.0], 2, 1)), [1.0];
                            row_lower=[2.0, 1.0])
    devex = JSimplex.initialize_workspace(problem, SolverOptions(pricing=:devex))
    @test isnothing(JSimplex.dual_iteration!(devex, () -> false))
    @test devex.pricing_weights[[1, 3]] == [4.0, 4.0]
    @test devex.devex_reference == BitVector([false, true, true])

    dantzig = JSimplex.initialize_workspace(problem, SolverOptions(pricing=:dantzig))
    dantzig.pricing_weights .= NaN
    @test isnothing(JSimplex.dual_iteration!(dantzig, () -> false))
    @test all(isnan, dantzig.pricing_weights)

    reset = JSimplex.initialize_workspace(
        problem, SolverOptions(pricing=:devex, refactorization_interval=1),
    )
    @test isnothing(JSimplex.dual_iteration!(reset, () -> false))
    @test all(isone, reset.pricing_weights)
    @test reset.devex_reference == BitVector([true, false, true])
end

@testset "Every pricing strategy solves an LP across scalar types" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; -1 1]), T[1, 1]; row_lower=T[1, 1])
        for pricing in (:steepest_edge, :devex, :dantzig)
            result = @inferred solve(problem; options=SolverOptions(T; pricing, verbose=false))
            @test result.status == OPTIMAL
            @test result.primal == T[1, 2]
            @test result.objective_value == T(3)
        end
    end
end

@testset "Harris ratio test" begin
    problem = LinearProblem(
        spzeros(1, 3), [1.0, 10.0 + 5.0e-7, 21.0],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    # The relaxed first pass admits column 2, whose pivot is larger than 1.
    @test JSimplex.dual_ratio_test(workspace, [1.0, 10.0, 20.0, 0.0]) == 2
    @test JSimplex.dual_ratio_test(workspace, [1.0e-7, 0.0, -2.0, 1.0]) == -1

    bounded = LinearProblem(
        spzeros(1, 4), [1.0, -1.0, 0.0, 0.0];
        column_lower=[0.0, -Inf, -Inf, 2.0],
        column_upper=[Inf, 0.0, Inf, 2.0],
    )
    workspace = JSimplex.initialize_workspace(bounded, SolverOptions())
    @test JSimplex.dual_ratio_test(workspace, [-1.0, -2.0, 0.0, 100.0, 1.0]) == 2
    @test JSimplex.dual_ratio_test(workspace, [1.0, 2.0, -3.0, 100.0, 1.0]) == 3
    @test JSimplex.dual_ratio_test(workspace, [-1.0, 2.0, 0.0, 100.0, 1.0]) == -1
end

@testset "Bound-flipping dual ratio test" begin
    for T in (Float64, Rational{BigInt})
        problem = LinearProblem(
            sparse(reshape(T[1, 1], 1, 2)), T[1, 2];
            row_lower=T[2], column_lower=T[0, 0],
            column_upper=[T(1), nothing],
        )
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        @test workspace.iterations == 1
        @test workspace.basis.states[1] == JSimplex.AT_UPPER
        @test workspace.basis.states[2] == JSimplex.BASIC
        @test workspace.primal[1:2] == T[1, 1]
        @test JSimplex.dual_infeasibility(workspace) == zero(T)
        run = JSimplex._solve_continuous_dual(problem, SolverOptions(T))
        @test run.status == OPTIMAL
        @test run.objective_value == T(3)
        @test run.iterations == 1
    end

    upper_flip = LinearProblem(
        sparse(reshape([-1.0, 1.0], 1, 2)), [-1.0, 2.0];
        row_lower=[2.0], column_lower=[-1.0, 0.0],
        column_upper=[0.0, Inf],
    )
    workspace = JSimplex.initialize_workspace(upper_flip, SolverOptions())
    workspace.basis.states[1] = JSimplex.AT_UPPER
    JSimplex.recompute!(workspace)
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.basis.states[1] == JSimplex.AT_LOWER
    @test workspace.primal[1:2] == [-1.0, 1.0]
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    above_upper = LinearProblem(
        sparse(reshape([-1.0, -1.0], 1, 2)), [1.0, 2.0];
        row_upper=[-2.0], column_lower=[0.0, 0.0],
        column_upper=[1.0, Inf],
    )
    run = JSimplex._solve_continuous_dual(above_upper, SolverOptions())
    @test run.status == OPTIMAL
    @test run.primal == [1.0, 1.0]
    @test run.objective_value == 3.0
    @test run.iterations == 1

    multiple_flips = LinearProblem(
        sparse(reshape([1.0, 1.0, 1.0], 1, 3)), [1.0, 2.0, 3.0];
        row_lower=[3.0], column_lower=[0.0, 0.0, 0.0],
        column_upper=[1.0, 1.0, Inf],
    )
    workspace = JSimplex.initialize_workspace(multiple_flips, SolverOptions())
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.iterations == 1
    @test workspace.basis.states[1:3] == [JSimplex.AT_UPPER, JSimplex.AT_UPPER,
                                           JSimplex.BASIC]
    @test workspace.primal[1:3] == [1.0, 1.0, 1.0]
    before = copy(workspace.primal)
    JSimplex.recompute!(workspace)
    @test workspace.primal == before
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    tied_breakpoints = LinearProblem(
        sparse(reshape([1.0, 2.0], 1, 2)), [1.0, 2.0];
        row_lower=[2.0], column_lower=[0.0, 0.0],
        column_upper=[3.0, 0.1],
    )
    workspace = JSimplex.initialize_workspace(tied_breakpoints, SolverOptions())
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.basis.basic_indices == [1]
    @test workspace.primal[1:2] == [2.0, 0.0]
    @test JSimplex.primal_infeasibility(workspace) == 0.0

    irrelevant_box = LinearProblem(
        sparse(reshape([1.0e-6, 1.0, 0.0], 1, 3)), [1.0e-6, 1.00000005, 0.0];
        row_lower=[1.0], column_lower=[0.0, 0.0, 0.0],
        column_upper=[Inf, Inf, 1.0],
    )
    workspace = JSimplex.initialize_workspace(irrelevant_box, SolverOptions())
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test workspace.basis.basic_indices == [2]
    @test workspace.primal[1:2] == [0.0, 1.0]

    insufficient = LinearProblem(
        sparse(reshape([1.0, 1.0], 1, 2)), [1.0, 2.0];
        row_lower=[3.0], column_lower=[0.0, 0.0],
        column_upper=[1.0, 1.0],
    )
    run = JSimplex._solve_continuous_dual(insufficient, SolverOptions())
    @test run.status == INFEASIBLE
    @test run.iterations == 0
end

@testset "Exact pivot updates and periodic refactorization" begin
    for interval in (2, 20)
        problem = LinearProblem(
            sparse([1.0 0.0; -1.0 1.0]), [1.0, 1.0];
            row_lower=[1.0, 1.0], row_upper=[Inf, Inf],
        )
        workspace = JSimplex.initialize_workspace(
            problem, SolverOptions(refactorization_interval=interval),
        )
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        @test workspace.primal ≈ [1.0, 0.0, 1.0, -1.0]
        @test workspace.reduced_costs ≈ [0.0, 1.0, 1.0, 0.0]
        @test workspace.basis.basic_indices == [1, 4]
        @test workspace.basis.states == [
            JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.BASIC,
        ]
        @test workspace.pricing_weights[[1, 4]] ≈ [1.0, 2.0]
        @test workspace.iterations == 1
        @test length(workspace.factorization.updates) == 1
        @test JSimplex.forward_solve(workspace.factorization, [2.0, 3.0]) ≈ [2.0, -5.0]
        @test JSimplex.transpose_solve(workspace.factorization, [2.0, 3.0]) ≈ [-1.0, -3.0]

        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
        @test workspace.primal ≈ [1.0, 2.0, 1.0, 1.0]
        @test workspace.reduced_costs ≈ [0.0, 0.0, 2.0, 1.0]
        @test workspace.basis.basic_indices == [1, 2]
        @test workspace.pricing_weights[1:2] ≈ [1.0, 2.0]
        @test workspace.iterations == 2
        @test workspace.refactorizations == (interval == 2 ? 1 : 0)
        @test length(workspace.factorization.updates) == (interval == 2 ? 0 : 2)
        @test JSimplex.forward_solve(workspace.factorization, [2.0, 3.0]) ≈ [2.0, 5.0]
        @test JSimplex.transpose_solve(workspace.factorization, [2.0, 3.0]) ≈ [5.0, 3.0]
        @test JSimplex.dual_infeasibility(workspace) == 0.0
        @test JSimplex.primal_infeasibility(workspace) == 0.0
    end
end

@testset "Parametric dual-simplex arithmetic" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        @testset "$T" begin
            test_typed_dual_kernel(T)
        end
    end
end

@testset "Rational pivots and feasibility use exact comparisons" begin
    T = Rational{BigInt}
    tiny = T(1 // big(10)^13)
    for (cost, lower, upper, expected) in ((T(1), T[1], [nothing], T(big(10)^13)),
                                         (T(-1), [nothing], T[1], T(-big(10)^13)))
        problem = LinearProblem(sparse(reshape(T[tiny], 1, 1)), T[cost];
                                row_lower=lower, row_upper=upper)
        run = @inferred JSimplex._solve_continuous_dual(problem, SolverOptions(T))
        @test run.status == OPTIMAL
        @test run.primal == T[big(10)^13]
        @test run.objective_value == expected
    end

    problem = LinearProblem(sparse(T[1 -3]), T[-1, 0]; row_lower=T[0], row_upper=T[0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    auxiliary.primal[1:2] .= T[1, 1 // 3]
    @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) == :certified
    auxiliary.primal[2] -= T(1 // big(10)^30)
    @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) == :invalid
    workspace.primal[1:2] .= auxiliary.primal[1:2]
    run = @inferred JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
    @test run.status == NUMERICAL_ERROR
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
end

@testset "Overflowing Harris relaxation retains floating failure semantics" begin
    for T in (Float32, Float64)
        @testset "$T" begin
            for (coefficient, tolerance, expected) in (
                (one(T), floatmax(T), OPTIMAL),
                (T(1 // 10^6), T(1 // 10^7), NUMERICAL_ERROR),
            )
                @testset "$expected" begin
                    problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)),
                                            T[floatmax(T) / T(2)]; row_lower=T[1])
                    result = @inferred solve(problem; options=SolverOptions(T; dual_tolerance=tolerance))
                    @test result isa Solution{T}
                    @test result.status == expected
                    @test expected == OPTIMAL ? result.primal == T[1] : isnothing(result.primal)
                    @test expected == OPTIMAL ? result.objective_value == floatmax(T) / T(2) :
                                               isnothing(result.objective_value)
                end
            end
        end
    end
end

@testset "Infeasibility verification preserves pivot counts and caller control" begin
    auxiliary = stale_primal_workspace()
    terminal = JSimplex.dual_iteration!(auxiliary, () -> false)
    @test terminal.status == OPTIMAL
    @test JSimplex.primal_infeasibility(auxiliary) == 0f0
    @test auxiliary.iterations == 1
    @test auxiliary.refactorizations == 1

    auxiliary = stale_primal_workspace()
    checks = Ref(0)
    terminal = JSimplex.dual_iteration!(auxiliary, () -> (checks[] += 1; checks[] == 2))
    @test terminal.status == TIME_LIMIT
    @test auxiliary.iterations == 1
    @test auxiliary.refactorizations == 0

    auxiliary = stale_primal_workspace()
    terminal = JSimplex.dual_iteration!(auxiliary, () -> auxiliary.refactorizations == 1)
    @test terminal.status == TIME_LIMIT
    @test auxiliary.iterations == 1
    @test auxiliary.refactorizations == 1

    for exception in (SingularException(7), ZeroPivotException(7))
        auxiliary = stale_primal_workspace()
        checks = Ref(0)
        callback = () -> (checks[] += 1; checks[] == 2 ? throw(exception) : false)
        captured = try
            JSimplex.dual_iteration!(auxiliary, callback)
        catch error
            error
        end
        @test captured === exception
        @test auxiliary.iterations == 1
        @test auxiliary.refactorizations == 0
    end

    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
                                row_lower=T[2], column_upper=T[1])
        run = @inferred JSimplex._solve_continuous_dual(problem, SolverOptions(T))
        @test run.status == INFEASIBLE
        @test run.iterations == 0
        @test isnothing(run.primal)
        @test isnothing(run.objective_value)
        T <: Rational && @test run.refactorizations == 0
    end
end

@testset "Rounded ray objective improvement must exceed its uncertainty" begin
    problem = LinearProblem(sparse(Float32[-7 3; -8 -6]), Float32[4, 3];
        row_lower=[nothing, -6f0], row_upper=[nothing, -4f0], column_lower=[nothing, nothing])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(Float32))
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    auxiliary.primal[1:2] .= Float32[90.90906, -121.2121]
    @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) != :certified

    exact = LinearProblem(sparse(Rational{BigInt}[1 -3]), Rational{BigInt}[-1, 0];
        row_lower=Rational{BigInt}[0], row_upper=Rational{BigInt}[0])
    workspace = JSimplex.initialize_workspace(exact, SolverOptions(Rational{BigInt}))
    auxiliary = JSimplex._auxiliary_workspace(workspace)
    auxiliary.primal[1:2] .= Rational{BigInt}[1, 1 // 3]
    @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) == :certified
end

@testset "Subnormal dot products cannot certify an increasing ray" begin
    for T in (Float16, Float32, Float64)
        smallest = nextfloat(zero(T))
        costs = vcat(fill(T(-3 // 4), 4), fill(T(1 // 2), 8))
        direction = fill(smallest, 12)
        # Exact products sum to +smallest; rounded products instead sum to -4smallest.
        @test dot(Rational{BigInt}.(costs), Rational{BigInt}.(direction)) == Rational{BigInt}(smallest)
        lower, upper = @inferred JSimplex._recession_objective_bounds(costs, direction, direction, Val(false))
        @test lower <= smallest <= upper
        # A free row prevents row uncertainty from masking an objective-sign bug.
        for row_lower in (T[0], [nothing])
            problem = LinearProblem(sparse(reshape(T(4) .* costs, 1, 12)), costs;
                row_lower, column_lower=fill(nothing, 12))
            workspace = JSimplex.initialize_workspace(problem, SolverOptions(T; dual_tolerance=smallest))
            auxiliary = JSimplex._auxiliary_workspace(workspace)
            auxiliary.primal[1:12] .= direction
            @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) != :certified
        end
    end
end

@testset "Floating row uncertainty is not a feasible recession direction" begin
    for T in (Float32, Float64, BigFloat), sign in (one(T), -one(T))
        problem = LinearProblem(sparse(reshape(sign .* T[1, -3], 1, 2)), T[-1, 0];
            row_lower=T[0], row_upper=T[0])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        auxiliary = JSimplex._auxiliary_workspace(workspace)
        auxiliary.primal[1:2] .= T[1, 1 // 3]
        @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) != :certified
    end

    for T in (Float16, Float32, Float64)
        for (coefficient, lower, upper, certified) in (
            (T(1 // 2), nothing, zero(T), false),
            (T(-1 // 2), zero(T), nothing, false),
            (T(1 // 2), zero(T), zero(T), false),
            (T(-1 // 2), zero(T), zero(T), false),
            (T(1 // 2), nothing, nothing, true),
            (zero(T), zero(T), zero(T), true),
        )
            problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[-4];
                row_lower=[lower], row_upper=[upper])
            workspace = JSimplex.initialize_workspace(problem,
                SolverOptions(T; dual_tolerance=nextfloat(zero(T))))
            auxiliary = JSimplex._auxiliary_workspace(workspace)
            auxiliary.primal[1] = nextfloat(zero(T))
            status = @inferred JSimplex._recession_direction_status(workspace, auxiliary)
            @test (status == :certified) == certified
        end
    end
end

@testset "Conclusive recession signs respect row and column bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (coefficient, direction, row_lower, row_upper, column_lower, column_upper, expected) in (
            (1, 2, 0, nothing, 0, nothing, :certified),
            (-1, 2, nothing, 0, 0, nothing, :certified),
            (1, -2, nothing, 0, nothing, 0, :certified),
            (-1, -2, 0, nothing, nothing, 0, :certified),
            (0, 2, 0, 0, nothing, nothing, :certified),
            (1, 2, nothing, nothing, nothing, nothing, :certified),
            (1, 2, nothing, 0, nothing, nothing, :invalid),
            (-1, 2, 0, nothing, nothing, nothing, :invalid),
            (1, 2, 0, 0, nothing, nothing, :invalid),
            (1, 2, nothing, nothing, 0, 1, :invalid),
            (1, -2, nothing, nothing, 0, nothing, :invalid),
            (1, 2, nothing, nothing, nothing, 0, :invalid),
        )
            convert_bound(value) = isnothing(value) ? nothing : T(value)
            problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[-sign(direction)];
                row_lower=[convert_bound(row_lower)], row_upper=[convert_bound(row_upper)],
                column_lower=[convert_bound(column_lower)], column_upper=[convert_bound(column_upper)])
            workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
            auxiliary = JSimplex._auxiliary_workspace(workspace)
            auxiliary.primal[1] = T(direction)
            @test (@inferred JSimplex._recession_direction_status(workspace, auxiliary)) == expected
        end
    end
end

@testset "Primal certification checks exact stored row activities" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 3; 3 9]), T[0, 0];
            row_lower=T[0, -4], row_upper=T[0, -4], column_lower=[nothing, T(-16777220)],
            column_upper=[nothing, T(-16777220)])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        primal = T[50331660, -16777220]
        @test Rational{BigInt}.(problem.A) * Rational{BigInt}.(primal) == Rational{BigInt}[0, 0]
        @test !(@inferred JSimplex._original_primal_feasible(workspace, primal))
        workspace.primal[1:2] .= primal
        result = @inferred JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
        @test result.status == NUMERICAL_ERROR

        normal = LinearProblem(sparse(T[1 3; 3 9]), T[0, 0];
            row_lower=T[0, 0], row_upper=T[0, 0], column_lower=fill(nothing, 2))
        workspace = JSimplex.initialize_workspace(normal, SolverOptions(T))
        @test (@inferred JSimplex._original_primal_feasible(workspace, T[3, -1]))
    end
end

@testset "Ambiguous floating row sums use a refined primal certificate" begin
    for (T, magnitude) in ((Float32, 1.0e5), (Float64, 1.0e10))
        problem = LinearProblem(sparse(reshape(T[0.1, -0.1, 1], 1, 3)),
                                zeros(T, 3); row_upper=T[0])
        tolerance = SolverOptions(T).primal_tolerance
        feasible = T[T(magnitude), T(magnitude), 0]
        lower, upper = JSimplex._primal_row_bounds(problem.A, feasible,
                                                   JSimplex._is_exact(T))
        @test !JSimplex._within_primal_intervals(lower, upper,
                                                 problem.row_lower,
                                                 problem.row_upper, tolerance)
        @test JSimplex._original_primal_feasible(problem, feasible, tolerance)
        within_tolerance = copy(feasible)
        within_tolerance[3] = tolerance / T(2)
        @test JSimplex._original_primal_feasible(problem, within_tolerance, tolerance)
        violated = copy(feasible)
        violated[3] = T(2) * tolerance
        @test !JSimplex._original_primal_feasible(problem, violated, tolerance)
    end
end

@testset "Absolute primal tolerance cannot be enlarged by subtraction rounding" begin
    for T in (Float16, Float32, Float64, BigFloat)
        small = eps(one(T)) / T(4)
        unbounded = Bound{T}(nothing)
        @test !(@inferred JSimplex._within_primal_bounds(T[small], [unbounded], [Bound(-one(T))], one(T)))
        @test !(@inferred JSimplex._within_primal_bounds(T[-small], [Bound(one(T))], [unbounded], one(T)))
    end
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (value, expected) in ((15 // 8, true), (17 // 8, true), (7 // 4, false), (9 // 4, false))
            @test (@inferred JSimplex._within_primal_bounds(T[value], [Bound(T(2))], [Bound(T(2))], T(1 // 8))) == expected
        end
    end
end

@testset "Primal interval arithmetic encloses mixed precision and nonfinite inputs" begin
    high, tolerance = setprecision(BigFloat, 256) do
        displacement = BigFloat(2)^(-100)
        one(BigFloat) + displacement, one(BigFloat) - displacement
    end
    setprecision(BigFloat, 32) do
        left = -one(BigFloat)
        expected_sum = big(1) // big(2)^100
        lower, upper = @inferred JSimplex._primal_sum_bounds(left, high)
        @test Rational{BigInt}(lower) <= expected_sum <= Rational{BigInt}(upper)
        expected_product = -1 - expected_sum
        lower, upper = @inferred JSimplex._primal_product_bounds(left, high)
        @test Rational{BigInt}(lower) <= expected_product <= Rational{BigInt}(upper)
        @test !(@inferred JSimplex._within_primal_bounds(BigFloat[0], [Bound(one(BigFloat))],
            [Bound{BigFloat}(nothing)], tolerance))
    end
    for T in (Float16, Float32, Float64, BigFloat)
        lower, upper = @inferred JSimplex._primal_sum_bounds(T(Inf), T(-Inf))
        @test !isfinite(lower) && !isfinite(upper)
    end
end

@testset "Optimality certification includes canceled and basic reduced costs" begin
    for (T, exponent) in ((Float32, 27), (Float64, 54))
        magnitude = T(big(2)^exponent)
        problem = LinearProblem(sparse(T[1 0 0 1; 0 1 0 1; 0 0 1 1]),
            T[magnitude, 1, magnitude, 2magnitude];
            row_lower=ones(T, 3), row_upper=ones(T, 3), objective_constant=-2magnitude)
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        workspace.basis = JSimplex.Basis([1, 2, 3],
            [JSimplex.BASIC, JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER,
             JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
        JSimplex.recompute!(workspace; refactorize=true)
        dual = JSimplex.transpose_solve(workspace.factorization, problem.objective[1:3])
        exact_reduced = Rational{BigInt}.(problem.objective) -
                        transpose(Rational{BigInt}.(problem.A)) * Rational{BigInt}.(dual)
        @test exact_reduced == Rational{BigInt}[0, 0, 0, -1]
        result = @inferred JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
        @test result.status == NUMERICAL_ERROR
        @test isnothing(result.primal)
    end

    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        tolerance = T <: Rational ? zero(T) : eps(T) / T(8)
        problem = LinearProblem(sparse(T[3;;]), T[1]; row_lower=T[3], row_upper=T[3])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T; dual_tolerance=tolerance))
        workspace.basis = JSimplex.Basis([1], [JSimplex.BASIC, JSimplex.AT_LOWER])
        JSimplex.recompute!(workspace; refactorize=true)
        dual = only(JSimplex.transpose_solve(workspace.factorization, T[1]))
        exact_reduced = 1 - 3Rational{BigInt}(dual)
        @test T <: Rational ? iszero(exact_reduced) : abs(exact_reduced) > Rational{BigInt}(tolerance)
        result = @inferred JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
        @test result.status == (T <: Rational ? OPTIMAL : NUMERICAL_ERROR)
    end
end

@testset "Optimality uses original costs and actual bound complementarity" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (cost, lower, upper, value, expected) in (
            (1, 0, 2, 0, OPTIMAL), (-1, 0, 2, 2, OPTIMAL),
            (1, 0, 2, 2, NUMERICAL_ERROR), (-1, 0, 2, 0, NUMERICAL_ERROR),
            (1, 0, 2, 1, NUMERICAL_ERROR), (-1, 0, 2, 1, NUMERICAL_ERROR),
            (1, 0, nothing, 0, OPTIMAL), (-1, nothing, 2, 2, OPTIMAL),
            (0, nothing, nothing, 1, OPTIMAL), (1, nothing, nothing, 1, NUMERICAL_ERROR),
            (3, 1, 1, 1, OPTIMAL), (-3, 1, 1, 1, OPTIMAL),
        )
            problem = LinearProblem(spzeros(T, 0, 1), T[cost];
                column_lower=[isnothing(lower) ? nothing : T(lower)],
                column_upper=[isnothing(upper) ? nothing : T(upper)])
            workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
            workspace.primal[1] = T(value)
            result = @inferred JSimplex._internal_solution(workspace, OPTIMAL, "candidate")
            @test result.status == expected
        end

        problem = LinearProblem(spzeros(T, 0, 1), T[1]; column_upper=T[2])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        workspace.costs[1] = -one(T)
        workspace.primal[1] = T(2)
        workspace.basis.states[1] = JSimplex.AT_UPPER
        @test JSimplex._internal_solution(workspace, OPTIMAL, "shifted candidate").status == NUMERICAL_ERROR

        problem = LinearProblem(sparse(T[1;;]), T[1]; row_lower=T[0], row_upper=T[2],
                                column_lower=[nothing])
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T))
        workspace.basis = JSimplex.Basis([1], [JSimplex.BASIC, JSimplex.AT_LOWER])
        JSimplex.recompute!(workspace; refactorize=true)
        workspace.primal[1] = one(T)
        @test JSimplex._internal_solution(workspace, OPTIMAL, "stale slack").status == NUMERICAL_ERROR
        workspace.primal[1] = zero(T)
        workspace.costs .= zero(T)
        @test JSimplex._internal_solution(workspace, OPTIMAL, "original costs").status == OPTIMAL
    end
end
