@testset "Simplex workspace" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse([1.0 2.0; -1.0 1.0]), [3.0, 1.0];
        row_lower=[1.0, -Inf], row_upper=[1.0, 4.0],
        column_lower=[0.0, 0.0], column_upper=[Inf, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    nrows, ncols = size(problem.A)
    @test workspace.basis.basic_indices == collect(ncols + 1:ncols + nrows)
    @test all(workspace.basis.states[ncols + 1:end] .== JSimplex.BASIC)
    @test JSimplex.basis_matrix(workspace) == [-1.0 0.0; 0.0 -1.0]
    @test JSimplex.primal_infeasibility(workspace) >= 0.0
    @test JSimplex.dual_infeasibility(workspace) >= 0.0
end

@testset "Simplex workspace nonbasic bounds" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(zeros(1, 3)), zeros(3);
        column_lower=[2.0, -Inf, -Inf],
        column_upper=[2.0, 3.0, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test workspace.basis.states[1:3] == [
        JSimplex.AT_LOWER,
        JSimplex.AT_UPPER,
        JSimplex.FREE_NONBASIC,
    ]
    @test workspace.primal[1:3] == [2.0, 3.0, 0.0]
    @test workspace.lower[4] == -Inf
    @test workspace.upper[4] == Inf
end

@testset "Simplex workspace recomputation and validation" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([2.0], 1, 1)), [5.0];
        row_lower=[1.0], row_upper=[Inf],
        column_lower=[1.0], column_upper=[4.0],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test workspace.primal == [1.0, 2.0]
    @test workspace.reduced_costs == [5.0, 0.0]
    @test JSimplex.dual_infeasibility(workspace) == 0.0
    @test workspace.refactorizations == 0

    workspace.basis = JSimplex.Basis(
        [2],
        JSimplex.VariableState[JSimplex.AT_UPPER, JSimplex.BASIC],
    )
    JSimplex.recompute!(workspace)
    @test workspace.primal == [4.0, 8.0]
    @test JSimplex.dual_infeasibility(workspace) == 5.0

    workspace.basis = JSimplex.Basis(
        [1],
        JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
    )
    JSimplex.recompute!(workspace; refactorize=true)
    @test JSimplex.basis_matrix(workspace) == [2.0;;]
    @test workspace.primal == [0.5, 1.0]
    @test workspace.reduced_costs == [0.0, 2.5]
    @test workspace.refactorizations == 1
    @test JSimplex.dual_infeasibility(workspace) == 0.0

    workspace.basis = JSimplex.Basis(
        [1, 1],
        JSimplex.VariableState[JSimplex.BASIC, JSimplex.AT_LOWER],
    )
    @test_throws ArgumentError JSimplex.basis_matrix(workspace)
end

@testset "Zero-row simplex workspace" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(0, 1), [-1.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())

    @test isempty(workspace.basis.basic_indices)
    @test workspace.primal == [0.0]
    @test workspace.reduced_costs == [-1.0]
    JSimplex.recompute!(workspace; refactorize=true)
    @test workspace.refactorizations == 1
end
