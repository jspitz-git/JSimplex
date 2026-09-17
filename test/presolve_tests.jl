using SparseArrays
using JSimplex.Logging

@testset "Singleton equality aggregation preserves LP and basis" begin
    problem = LinearProblem(sparse([1.0 1.0; 0.0 1.0]), [2.0, 1.0];
        row_lower=[5.0, nothing], row_upper=[5.0, 4.0],
        column_lower=[0.0, 0.0], column_upper=[3.0, nothing])
    reduced = JSimplex.aggregate_singleton_equalities(problem)
    @test size(reduced.problem.A) == (2, 1)
    @test reduced.problem.A[:, 1] == [1.0, 1.0]
    @test bound_value(reduced.problem.row_lower[1]) == 2.0
    @test bound_value(reduced.problem.row_upper[1]) == 5.0
    @test reduced.problem.objective == [-1.0]
    @test reduced.problem.objective_constant == 10.0
    @test JSimplex.postsolve_primal(reduced, [4.0]) == [1.0, 4.0]
    basis = JSimplex.Basis([2, 1], JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_UPPER])
    restored = JSimplex.restore_basis(reduced, basis)
    @test restored.basic_indices == [1, 2]
    @test restored.states == JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_UPPER]
    exchanged_basis = JSimplex.Basis([1, 2], JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_UPPER])
    exchanged = JSimplex.restore_basis(reduced, exchanged_basis)
    @test exchanged.basic_indices == [2, 1]
    @test exchanged.states == JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_UPPER]
    solution = solve(problem; options=SolverOptions(verbose=false))
    @test solution.status == OPTIMAL
    @test solution.primal == [1.0, 4.0]
    @test solution.objective_value == 6.0

    negative = LinearProblem(sparse([-2.0 1.0; 0.0 1.0]), [1.0, 0.0];
        row_lower=[4.0, nothing], row_upper=[4.0, 8.0],
        column_lower=[-1.0, 0.0], column_upper=[2.0, nothing])
    projected = JSimplex.aggregate_singleton_equalities(negative)
    @test bound_value(projected.problem.row_lower[1]) == 2.0
    @test bound_value(projected.problem.row_upper[1]) == 8.0
    @test projected.problem.objective == [0.5]
    @test projected.problem.objective_constant == -2.0
    lower_basis = JSimplex.Basis([1, 3], JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC])
    lower_restored = JSimplex.restore_basis(projected, lower_basis)
    @test lower_restored.basic_indices == [2, 4]
    @test lower_restored.states[1] == JSimplex.AT_LOWER
    @test JSimplex.postsolve_primal(projected, [2.0]) == [-1.0, 2.0]
end

@testset "Sparse equality aggregation handles bounds and limited fill" begin
    bounded = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [2.0, 1.0];
        row_lower=[4.0, nothing], row_upper=[4.0, 0.0],
        column_lower=[0.0, 0.0], column_upper=[3.0, nothing])
    projected = JSimplex.aggregate_sparse_equalities(bounded)
    @test size(projected.problem.A) == (2, 1)
    @test projected.problem.A[:, 1] == [1.0, -2.0]
    @test bound_value(projected.problem.row_lower[1]) == 1.0
    @test bound_value(projected.problem.row_upper[1]) == 4.0
    @test bound_value(projected.problem.row_upper[2]) == -4.0
    @test projected.problem.objective == [-1.0]
    @test projected.problem.objective_constant == 8.0
    @test JSimplex.postsolve_primal(projected, [4.0]) == [0.0, 4.0]
    @test solve(bounded; options=SolverOptions(verbose=false)).objective_value == 4.0

    implied = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [2.0, 1.0];
        row_lower=[5.0, nothing], row_upper=[5.0, 0.0],
        column_lower=[0.0, 0.0], column_upper=[10.0, 4.0])
    removed = JSimplex.aggregate_sparse_equalities(implied)
    @test size(removed.problem.A) == (1, 1)
    @test removed.problem.A[1, 1] == -2.0
    @test bound_value(removed.problem.row_upper[1]) == -5.0
    @test JSimplex.postsolve_primal(removed, [4.0]) == [1.0, 4.0]
    @test solve(implied; options=SolverOptions(verbose=false)).objective_value == 6.0

    three_term = LinearProblem(sparse([1.0 1.0 1.0; 1.0 -1.0 0.0]),
        [2.0, 1.0, 0.0];
        row_lower=[5.0, nothing], row_upper=[5.0, 0.0],
        column_lower=[0.0, 0.0, 0.0], column_upper=[10.0, 4.0, 1.0])
    three_term_reduced = JSimplex.aggregate_sparse_equalities(three_term)
    @test size(three_term_reduced.problem.A) == (1, 2)
    @test three_term_reduced.problem.A == sparse([-2.0 -1.0])
    @test three_term_reduced.problem.objective == [-1.0, -2.0]
    @test three_term_reduced.problem.objective_constant == 10.0
    @test JSimplex.postsolve_primal(three_term_reduced, [4.0, 1.0]) ==
          [0.0, 4.0, 1.0]
    reduced_basis = JSimplex.Basis([3], JSimplex.VariableState[
        JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.BASIC])
    restored_basis = JSimplex.restore_basis(three_term_reduced, reduced_basis)
    @test restored_basis.basic_indices == [1, 5]
    @test restored_basis.states == JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER,
        JSimplex.AT_LOWER, JSimplex.BASIC]
    @test solve(three_term; options=SolverOptions(verbose=false)).objective_value == 4.0

    wide = zeros(13, 14)
    wide[1, 1:2] .= 1
    for row in 2:13
        wide[row, 1] = 1
        wide[row, row + 1] = 1
    end
    expensive = LinearProblem(sparse(wide), ones(14);
        row_lower=[5.0; fill(nothing, 12)],
        row_upper=[5.0; fill(10.0, 12)])
    @test isempty(JSimplex.aggregate_sparse_equalities(expensive).postsolve_stack)

    inexact = LinearProblem(sparse([3.0 1.0; 1.0 0.0]), [0.0, 0.0];
        row_lower=[1.0, nothing], row_upper=[1.0, 1.0])
    @test isempty(JSimplex.aggregate_sparse_equalities(inexact).postsolve_stack)
end

@testset "Dual fixing respects objective and row direction" begin
    lower = LinearProblem(sparse([1.0 1.0]), [1.0, -1.0];
        row_upper=[4.0], column_lower=[0.0, 0.0],
        column_upper=[5.0, 3.0])
    lower_reduced = JSimplex.reduce_dual_fixings(lower)
    @test size(lower_reduced.problem.A) == (1, 1)
    @test lower_reduced.problem.objective == [-1.0]
    @test JSimplex.postsolve_primal(lower_reduced, [3.0]) == [0.0, 3.0]
    reduced_basis = JSimplex.Basis([2], JSimplex.VariableState[
        JSimplex.AT_UPPER, JSimplex.BASIC])
    restored_basis = JSimplex.restore_basis(lower_reduced, reduced_basis)
    @test restored_basis.basic_indices == [3]
    @test restored_basis.states == JSimplex.VariableState[
        JSimplex.AT_LOWER, JSimplex.AT_UPPER, JSimplex.BASIC]
    @test solve(lower; options=SolverOptions(verbose=false)).objective_value == -3.0

    ranged = LinearProblem(sparse([1.0 1.0]), [1.0, -1.0];
        row_lower=[2.0], row_upper=[4.0],
        column_lower=[0.0, 0.0], column_upper=[5.0, 3.0])
    @test isempty(JSimplex.reduce_dual_fixings(ranged).postsolve_stack)

    upper = LinearProblem(sparse([-1.0 1.0]), [-2.0, 0.0];
        row_upper=[2.0], column_lower=[0.0, nothing],
        column_upper=[3.0, nothing])
    upper_reduced = JSimplex.reduce_dual_fixings(upper)
    @test size(upper_reduced.problem.A) == (1, 1)
    @test JSimplex.postsolve_primal(upper_reduced, [0.0]) == [3.0, 0.0]
    @test JSimplex.restore_basis(upper_reduced, JSimplex.Basis([2],
        JSimplex.VariableState[JSimplex.FREE_NONBASIC, JSimplex.BASIC])).states[1] ==
          JSimplex.AT_UPPER
    @test solve(upper; options=SolverOptions(verbose=false)).objective_value == -6.0

    maximization = LinearProblem(sparse([-1.0 1.0]), [1.0, 0.0];
        objective_sense=MAX_SENSE, row_upper=[1.0],
        column_lower=[0.0, nothing], column_upper=[2.0, nothing])
    @test JSimplex.postsolve_primal(JSimplex.reduce_dual_fixings(maximization),
                                    [0.0]) == [2.0, 0.0]
    @test solve(maximization; options=SolverOptions(verbose=false)).objective_value == 2.0

    unbounded_direction = LinearProblem(sparse([1.0 1.0]), [1.0, -1.0];
        row_upper=[4.0], column_lower=[nothing, 0.0],
        column_upper=[5.0, 3.0])
    @test isempty(JSimplex.reduce_dual_fixings(unbounded_direction).postsolve_stack)

    zero_cost = LinearProblem(sparse([1.0 1.0]), [0.0, -1.0];
        row_upper=[4.0], column_lower=[1.0, 0.0],
        column_upper=[5.0, 3.0])
    @test JSimplex.postsolve_primal(JSimplex.reduce_dual_fixings(zero_cost),
                                    [3.0]) == [1.0, 3.0]
end

@testset "Multi-term row bound propagation" begin
    upper = LinearProblem(sparse([1.0 1.0]), [1.0, 0.0];
        objective_sense=MAX_SENSE, row_upper=[10.0],
        column_lower=[0.0, 4.0])
    propagated = JSimplex.propagate_row_bounds(upper)
    @test bound_value(propagated.problem.column_upper[1]) == 6.0
    @test size(propagated.problem.A) == (1, 2)
    basis = JSimplex.Basis([3], JSimplex.VariableState[
        JSimplex.AT_UPPER, JSimplex.AT_LOWER, JSimplex.BASIC])
    restored = JSimplex.restore_basis(propagated, basis)
    @test restored.states[1] == JSimplex.AT_LOWER
    for algorithm in (:dual, :primal)
        solution = solve(upper; options=SolverOptions(Float64; algorithm, verbose=false))
        @test solution.status == OPTIMAL
        @test solution.primal == [6.0, 4.0]
    end

    free_column = LinearProblem(sparse([1.0 1.0]), [1.0, 0.0];
        objective_sense=MAX_SENSE, row_upper=[10.0],
        column_lower=[nothing, 4.0])
    free_step = JSimplex.propagate_row_bounds(free_column)
    free_basis = JSimplex.Basis([3], JSimplex.VariableState[
        JSimplex.AT_UPPER, JSimplex.AT_LOWER, JSimplex.BASIC])
    @test JSimplex.restore_basis(free_step, free_basis).states[1] ==
          JSimplex.FREE_NONBASIC
    @test solve(free_column; options=SolverOptions(verbose=false)).primal == [6.0, 4.0]

    lower = LinearProblem(sparse([1.0 1.0]), [1.0, 0.0];
        row_lower=[5.0], column_upper=[nothing, 2.0])
    @test bound_value(JSimplex.propagate_row_bounds(lower).problem.column_lower[1]) == 3.0

    negative = LinearProblem(sparse([-2.0 1.0]), [1.0, 0.0];
        row_upper=[-2.0])
    @test bound_value(JSimplex.propagate_row_bounds(negative).problem.column_lower[1]) == 1.0

    impossible = LinearProblem(sparse([1.0 1.0]), [0.0, 0.0];
        row_lower=[10.0], column_upper=[3.0, 4.0])
    @test JSimplex.propagate_row_bounds(impossible).status == INFEASIBLE

    redundant = LinearProblem(sparse([1.0 1.0]), [0.0, 0.0];
        row_upper=[10.0], column_upper=[3.0, 4.0])
    @test size(JSimplex.propagate_row_bounds(redundant).problem.A) == (0, 2)

    inexact = LinearProblem(sparse([3.0 1.0]), [1.0, 1.0]; row_upper=[1.0])
    @test !isfinite(JSimplex.propagate_row_bounds(inexact).problem.column_upper[1])
end

@testset "Presolve repeats bound propagation and structural passes" begin
    chain = LinearProblem(sparse([1.0 1.0 0.0; 0.0 1.0 1.0]),
        [1.0, 0.0, 0.0]; row_lower=[nothing, 5.0],
        row_upper=[10.0, nothing], column_upper=[nothing, nothing, 2.0])
    chained = JSimplex.presolve_problem(chain)
    @test size(chained.problem.A) == (0, 0)
    @test JSimplex.postsolve_primal(chained, Float64[]) == [0.0, 3.0, 2.0]

    fixed = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [1.0, 1.0];
        row_lower=[5.0, nothing], row_upper=[nothing, 1.0],
        column_upper=[nothing, 2.0])
    reduced = JSimplex.presolve_problem(fixed)
    @test size(reduced.problem.A) == (0, 0)
    for algorithm in (:dual, :primal)
        result = solve(fixed; options=SolverOptions(Float64; algorithm, verbose=false))
        @test result.status == OPTIMAL
        @test result.primal == [3.0, 2.0]
    end
end

@testset "Original LP resolves an inconclusive reduced numerical run" begin
    problem = LinearProblem(sparse(Float32[3 -1]), Float32[-4, 2];
        row_upper=Float32[2], column_lower=[-1f0, nothing],
        column_upper=[nothing, 2f0])
    result = solve(problem; options=SolverOptions(Float32; verbose=false))
    @test result.status == OPTIMAL
    @test result.primal == Float32[-1, -5]
end

@testset "Advanced presolve reduces rows and restores solutions" begin
    singleton = LinearProblem(sparse([2.0 0.0; 1.0 1.0]), [1.0, 1.0];
                              row_lower=[4.0, 1.0], row_upper=[8.0, nothing],
                              column_lower=[0.0, 0.0])
    one = JSimplex.presolve_problem(singleton)
    @test size(one.problem.A) == (0, 0)
    @test JSimplex.postsolve_primal(one, Float64[]) == [2.0, 0.0]
    @test bound_value(JSimplex.reduce_singleton_rows(singleton).problem.column_lower[1]) == 2.0
    @test solve(singleton).status == OPTIMAL

    parallel = LinearProblem(sparse([1.0 1.0; 2.0 2.0; 1.0 -1.0]), [1.0, 1.0];
                             row_lower=[1.0, 0.0, nothing],
                             row_upper=[3.0, 8.0, 2.0])
    two = JSimplex.presolve_problem(parallel)
    @test size(two.problem.A, 1) == 2
    @test solve(parallel).status == OPTIMAL

    dependent = LinearProblem(sparse([1.0 1.0 0.0; 0.0 1.0 1.0; 1.0 2.0 1.0]),
                              [1.0, 1.0, 1.0];
                              row_lower=[1.0, 0.0, 0.0],
                              row_upper=[2.0, 1.0, 3.0])
    three = JSimplex.presolve_problem(dependent)
    @test size(three.problem.A, 1) == 2
    @test solve(dependent).status == OPTIMAL
end

@testset "Advanced presolve keeps necessary constraints" begin
    structure = sparse([1.0 1.0 0.0; 0.0 1.0 1.0; 1.0 2.0 1.0])
    necessary = LinearProblem(structure, ones(3);
        row_lower=[1.0, 0.0, 2.0], row_upper=[2.0, 1.0, 3.0])
    @test size(JSimplex.presolve_problem(necessary).problem.A, 1) == 3
    impossible = LinearProblem(structure, ones(3);
        row_lower=[1.0, 0.0, 4.0], row_upper=[2.0, 1.0, nothing])
    @test JSimplex.presolve_problem(impossible).status == INFEASIBLE

    inconsistent_parallel = LinearProblem(sparse([1.0 1.0; 2.0 2.0]), ones(2);
        row_upper=[1.0, nothing], row_lower=[nothing, 4.0])
    @test JSimplex.presolve_problem(inconsistent_parallel).status == INFEASIBLE

    inexact = LinearProblem(sparse([3.0 0.0; 1.0 1.0]), ones(2);
        row_lower=[1.0, 1.0])
    @test size(JSimplex.presolve_problem(inexact).problem.A, 1) == 2
end

@testset "Doubleton substitution and cleanup" begin
    problem = LinearProblem(sparse([1.0 1.0; 1.0 -1.0]), [2.0, 1.0];
        row_lower=[4.0, 0.0], row_upper=[4.0, nothing],
        column_lower=[nothing, 0.0])
    result = JSimplex.presolve_problem(problem)
    @test size(result.problem.A) == (0, 0)
    @test JSimplex.postsolve_primal(result, Float64[]) == [2.0, 2.0]
    restored = JSimplex.restore_basis(result,
        JSimplex.Basis(Int[], JSimplex.VariableState[]))
    @test restored.basic_indices == [1, 4]
    @test restored.states == JSimplex.VariableState[
        JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.BASIC]
    for algorithm in (:dual, :primal)
        solution = solve(problem; options=SolverOptions(Float64; algorithm, verbose=false))
        @test solution.status == OPTIMAL
        @test solution.primal == [2.0, 2.0]
        @test solution.objective_value == 6.0
    end
end

@testset "Dependent-row proof supports all solver scalar types" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 1 0; 0 1 1; 1 2 1]), T[1, 1, 1];
            row_lower=T[1, 0, 0], row_upper=T[2, 1, 3])
        @test size(JSimplex.presolve_problem(problem).problem.A) == (2, 3)
    end
end

@testset "Exact bounds and signed row coefficients" begin
    negative = LinearProblem(sparse([-2.0 0.0; 1.0 1.0]), [2.0, 1.0];
        row_lower=[-8.0, 3.0], row_upper=[-4.0, nothing])
    reduced = JSimplex.presolve_problem(negative)
    @test size(reduced.problem.A) == (1, 2)
    @test bound_value(reduced.problem.column_lower[1]) == 2.0
    @test bound_value(reduced.problem.column_upper[1]) == 4.0
    for algorithm in (:dual, :primal)
        solution = solve(negative; options=SolverOptions(Float64; algorithm, verbose=false))
        @test solution.status == OPTIMAL
        @test solution.primal ≈ [2.0, 1.0]
    end
    impossible = LinearProblem(sparse([-2.0 0.0; 1.0 1.0]), [1.0, 1.0];
        row_lower=[-8.0, 3.0], row_upper=[-4.0, nothing],
        column_upper=[1.0, nothing])
    @test JSimplex.presolve_problem(impossible).status == INFEASIBLE

    reversed = LinearProblem(sparse([1.0 1.0; -2.0 -2.0]), [1.0, 1.0];
        row_lower=[1.0, -8.0], row_upper=[3.0, -1.0])
    @test size(JSimplex.presolve_problem(reversed).problem.A, 1) == 1

    inexact_substitution = LinearProblem(sparse([3.0 1.0]), [1.0, 1.0];
        row_lower=[1.0], row_upper=[1.0], column_lower=[nothing, 0.0])
    safe_projection = JSimplex.presolve_problem(inexact_substitution)
    @test size(safe_projection.problem.A) == (1, 1)
    @test safe_projection.problem.A[1, 1] == 3.0
    @test safe_projection.problem.objective == [-2.0]
    @test safe_projection.problem.objective_constant == 1.0
    bounded_doubleton = LinearProblem(sparse([1.0 1.0]), [1.0, 1.0];
        row_lower=[1.0], row_upper=[1.0])
    @test size(JSimplex.presolve_problem(bounded_doubleton).problem.A) == (0, 0)
    @test solve(bounded_doubleton; options=SolverOptions(verbose=false)).objective_value == 1.0
end

function problem_stat_messages(problem; options=SolverOptions())
    logger = Test.TestLogger(min_level=Logging.Info)
    with_logger(logger) do
        solve(problem; options)
    end
    return [record.message for record in logger.logs
            if record.message isa AbstractString &&
               (startswith(record.message, "Loaded problem:") ||
                startswith(record.message, "After presolve:"))]
end

@testset "Problem statistics bracket presolve" begin
    reduced = LinearProblem(sparse([1.0 0.0; 0.0 0.0]), [1.0, 2.0];
                            row_lower=[1.0, nothing],
                            column_lower=[0.0, 3.0],
                            column_upper=[nothing, 3.0])
    @test problem_stat_messages(reduced) == [
        "Loaded problem: rows=2 columns=2 nnz=1",
        "After presolve: rows=0 columns=0 nnz=0",
    ]

    unchanged = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    @test problem_stat_messages(unchanged) == [
        "Loaded problem: rows=1 columns=1 nnz=1",
        "After presolve: rows=0 columns=0 nnz=0",
    ]
    @test isempty(problem_stat_messages(unchanged;
        options=SolverOptions(verbose=false)))
    @test problem_stat_messages(unchanged;
        options=SolverOptions(time_limit=0.0)) ==
          ["Loaded problem: rows=1 columns=1 nnz=1"]

    infeasible = LinearProblem(spzeros(1, 1), [0.0]; row_lower=[1.0])
    @test problem_stat_messages(infeasible) == [
        "Loaded problem: rows=1 columns=1 nnz=0",
        "After presolve: rows=0 columns=0 nnz=0",
    ]
end

@testset "Presolve removes reversible structure" begin
    problem = LinearProblem(sparse([2.0 1.0 0.0; 0.0 0.0 0.0]),
                            [5.0, 1.0, -4.0]; objective_constant=7.0,
                            row_lower=[8.0, nothing],
                            column_lower=[3.0, 0.0, 0.0],
                            column_upper=[3.0, nothing, 5.0],
                            row_names=["active", "empty"],
                            column_names=["fixed", "active", "empty"])
    original = deepcopy(problem)
    reduced = JSimplex.presolve_problem(problem)
    @test reduced isa JSimplex.PresolveResult{Float64}
    @test size(reduced.problem.A) == (0, 0)
    @test reduced.problem.objective == Float64[]
    @test reduced.problem.objective_constant == 4.0
    @test reduced.problem.row_names == String[]
    @test reduced.problem.column_names == String[]
    @test JSimplex.postsolve_primal(reduced, Float64[]) == [3.0, 2.0, 5.0]
    basis = JSimplex.Basis(Int[], JSimplex.VariableState[])
    restored = JSimplex.restore_basis(reduced, basis)
    @test restored.basic_indices == [2, 5]
    @test restored.states == JSimplex.VariableState[
        JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.AT_UPPER,
        JSimplex.AT_LOWER, JSimplex.BASIC,
    ]
    @test problem.A == original.A
    @test problem.objective == original.objective
    @test problem.row_lower == original.row_lower
    @test problem.column_upper == original.column_upper
end

@testset "Cleanup resolves the original model from a restored basis" begin
    problem = LinearProblem(sparse([2.0 1.0]), [5.0, 1.0];
                            objective_constant=7.0, row_lower=[8.0],
                            column_lower=[3.0, 0.0],
                            column_upper=[3.0, nothing])
    reduced = JSimplex.presolve_problem(problem)
    options = SolverOptions(Float64; scaling=:off)
    run = JSimplex._solve_continuous_dual(reduced.problem, options)
    @test run.status == OPTIMAL
    basis = JSimplex.restore_basis(reduced, run.basis)
    context = JSimplex.SolveContext(time_ns(), Inf)
    cleanup = JSimplex.cleanup_original(problem, basis, options, context,
                                        run.iterations, run.refactorizations)
    @test cleanup.status == OPTIMAL
    @test cleanup.primal == [3.0, 2.0]
    @test cleanup.objective_value == 24.0
    @test cleanup.iterations == run.iterations
    @test cleanup.refactorizations > run.refactorizations
    for algorithm in (:dual, :primal)
        result = solve(problem; options=SolverOptions(Float64; algorithm, scaling=:off))
        @test result.status == OPTIMAL
        @test result.primal == [3.0, 2.0]
        @test result.objective_value == 24.0
        @test result.statistics.refactorizations > run.refactorizations
    end
end

@testset "Cleanup can pivot on the original LP" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    basis = JSimplex.Basis([2], JSimplex.VariableState[JSimplex.AT_LOWER, JSimplex.BASIC])
    context = JSimplex.SolveContext(time_ns(), Inf)
    run = JSimplex.cleanup_original(problem, basis, SolverOptions(Float64), context, 0, 0)
    @test run.status == OPTIMAL
    @test run.primal == [1.0]
    @test run.iterations == 1
end

@testset "Presolve handles a completely reduced LP" begin
    problem = LinearProblem(sparse([1.0;;]), [2.0];
                            row_lower=[3.0], row_upper=[3.0],
                            column_lower=[3.0], column_upper=[3.0])
    for algorithm in (:dual, :primal)
        result = solve(problem; options=SolverOptions(Float64; algorithm, iteration_limit=0))
        @test result.status == OPTIMAL
        @test result.primal == [3.0]
        @test result.objective_value == 6.0
        @test result.statistics.iterations == 0
    end
    impossible = LinearProblem(sparse([1.0;;]), [2.0];
                               row_lower=[4.0], column_lower=[3.0], column_upper=[3.0])
    @test solve(impossible).status == INFEASIBLE
end

@testset "Optimal simplex runs retain an original-column basis" begin
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    options = SolverOptions(Float64; scaling=:off)
    for algorithm in (JSimplex._solve_continuous_dual, JSimplex._solve_continuous_primal)
        run = algorithm(problem, options)
        @test run.status == OPTIMAL
        @test run.basis isa JSimplex.Basis
        @test length(run.basis.basic_indices) == 1
        @test length(run.basis.states) == 2
        @test all(index -> 1 <= index <= 2, run.basis.basic_indices)
    end
end

@testset "Presolve detects impossible empty rows" begin
    problem = LinearProblem(spzeros(1, 1), [0.0]; row_lower=[1.0])
    result = JSimplex.presolve_problem(problem)
    @test result.status == INFEASIBLE
end

@testset "Stored zero coefficients count as empty structure" begin
    matrix = SparseMatrixCSC(1, 1, [1, 2], [1], [0.0])
    problem = LinearProblem(matrix, [1.0]; column_upper=[3.0])
    result = JSimplex.presolve_problem(problem)
    @test size(result.problem.A) == (0, 0)
    @test JSimplex.postsolve_primal(result, Float64[]) == [0.0]
end

@testset "Empty columns respect objective sense and bound direction" begin
    problem = LinearProblem(spzeros(0, 1), [2.0]; objective_sense=MAX_SENSE,
                            column_lower=[0.0], column_upper=[5.0])
    presolved = JSimplex.presolve_problem(problem)
    @test size(presolved.problem.A) == (0, 0)
    @test presolved.problem.objective_constant == 10.0
    @test JSimplex.postsolve_primal(presolved, Float64[]) == [5.0]
    result = solve(problem)
    @test result.status == OPTIMAL
    @test result.primal == [5.0]
    @test result.objective_value == 10.0
end

@testset "Presolve skips inexact floating reductions" begin
    problem = LinearProblem(sparse([0.1 1.0]), [0.0, 1.0];
                            row_lower=[1.0], column_lower=[0.1, 0.0],
                            column_upper=[0.1, nothing])
    result = JSimplex.presolve_problem(problem)
    @test size(result.problem.A) == (1, 2)
    @test result.problem.A == problem.A
end

@testset "Presolve supports exact scalar types" begin
    for T in (Float32, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 1]), T[3, 1];
                                objective_constant=T(4), row_lower=T[8],
                                column_lower=T[3, 0],
                                column_upper=[T(3), nothing])
        result = JSimplex.presolve_problem(problem)
        @test result.problem isa LinearProblem{T}
        @test size(result.problem.A) == (0, 0)
        @test result.problem.objective_constant == T(15)
        @test JSimplex.postsolve_primal(result, T[]) == T[3, 2]
    end
end

@testset "Zero shifts retain stored BigFloat precision" begin
    problem = setprecision(BigFloat, 256) do
        precise = big"1.00000000000000000000000000000000000001"
        LinearProblem(sparse(BigFloat[1 1]), BigFloat[0, 1];
                      objective_constant=precise, row_lower=[precise],
                      column_lower=BigFloat[0, 0],
                      column_upper=[big"0", nothing])
    end
    result = setprecision(BigFloat, 64) do
        JSimplex.presolve_problem(problem)
    end
    @test size(result.problem.A) == (1, 1)
    @test result.problem.objective_constant == problem.objective_constant
    @test bound_value(only(result.problem.row_lower)) ==
          bound_value(only(problem.row_lower))

    inexact = setprecision(BigFloat, 256) do
        LinearProblem(spzeros(BigFloat, 0, 1),
                      BigFloat[big"1.00000000000000000000000000000000000001"];
                      column_lower=BigFloat[1], column_upper=BigFloat[1])
    end
    retained = setprecision(BigFloat, 64) do
        JSimplex.presolve_problem(inexact)
    end
    @test size(retained.problem.A, 2) == 1
end
