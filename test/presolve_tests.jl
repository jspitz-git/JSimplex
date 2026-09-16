using SparseArrays

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
    @test size(reduced.problem.A) == (1, 1)
    @test reduced.problem.A == sparse([1.0;;])
    @test reduced.problem.objective == [1.0]
    @test reduced.problem.objective_constant == 2.0
    @test bound_value(only(reduced.problem.row_lower)) == 2.0
    @test reduced.problem.row_names == ["active"]
    @test reduced.problem.column_names == ["active"]
    @test JSimplex.postsolve_primal(reduced, [2.0]) == [3.0, 2.0, 5.0]
    basis = JSimplex.Basis([1], JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER])
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
        @test size(result.problem.A) == (1, 1)
        @test bound_value(only(result.problem.row_lower)) == T(2)
        @test result.problem.objective_constant == T(13)
        @test JSimplex.postsolve_primal(result, T[2]) == T[3, 2]
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
