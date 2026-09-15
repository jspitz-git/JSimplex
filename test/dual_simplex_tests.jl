using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

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
        (1.0e-13, 0.0, -Inf, Inf, 1.0, Inf, NUMERICAL_ERROR),
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
        @test workspace.lower == [0.0, -Inf]
        @test workspace.upper == [Inf, 3.0]
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
    workspace.factorization.base = lu(zeros(1, 1); check=false)
    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    for field in (:primal, :reduced_costs, :pricing_weights)
        workspace = JSimplex.initialize_workspace(problem, SolverOptions())
        getfield(workspace, field)[1] = NaN
        terminal = JSimplex.dual_iteration!(workspace, () -> false)
        @test terminal.status == NUMERICAL_ERROR
        @test workspace.iterations == 0
    end
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
        for field in fieldnames(LinearProblem)
            @test getfield(problem, field) == getfield(before, field)
        end
    end
end

@testset "Recession direction requires primal feasibility" begin
    for (problem, status) in (
        (LinearProblem(sparse([1.0;;]), [-1.0]; row_lower=[2.0]), UNBOUNDED),
        (LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[-1.0]), INFEASIBLE),
        (LinearProblem(sparse([1.0 0.0]), [0.0, -1.0]; row_upper=[-1.0]), INFEASIBLE),
        (LinearProblem(sparse([1.0 -1.0]), [-1.0, 0.0];
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
            for run in (JSimplex._solve_continuous_dual(problem, options), solve(problem; options))
                @test run.status == status
                @test isnothing(run.primal)
                @test isnothing(run.objective_value)
            end
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
    @test run.status == NUMERICAL_ERROR
    @test isnothing(run.primal)
    @test isnothing(run.objective_value)
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
    workspace.primal[3:4] .= [2.0, 3.0]
    @test JSimplex.dual_edge_selection(workspace) == -1
    row = fill(NaN, 4)
    @test isnothing(JSimplex.price!(row, workspace, [2.0, -3.0]))
    @test row == [5.0, -3.0, -2.0, 3.0]
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
