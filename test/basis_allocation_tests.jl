@testset "Basis assembly allocates only CSC result storage" begin
    dimension = 512
    problem = LinearProblem(JSimplex.SparseArrays.spdiagm(0 => ones(dimension)),
                            zeros(dimension))
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    JSimplex.basis_matrix(workspace)
    # Three result arrays need about 12 KiB. Reject the temporary arrays used
    # to sort and assemble a matrix from already ordered triplets.
    @test (@allocated JSimplex.basis_matrix(workspace)) <= 15_000
end

@testset "Basis assembly preserves columns and owns its result arrays" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        A = JSimplex.SparseArrays.sparse([1, 2, 3, 2, 1, 3], [1, 1, 1, 2, 3, 3],
                                       T[2, 0, 5, 3, 4, 6], 3, 3)
        problem = LinearProblem(A, zeros(T, 3); row_lower=zeros(T, 3))
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
        workspace.basis = JSimplex.Basis([3, 5, 1],
            [JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC,
             JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.AT_LOWER])
        B = @inferred JSimplex.basis_matrix(workspace)
        @test Matrix(B) == T[4 0 2; 0 -1 0; 6 0 5]
        @test B.colptr == [1, 3, 4, 7]
        @test B.rowval == [1, 3, 2, 1, 2, 3]
        @test B.nzval == T[4, 6, -1, 2, 0, 5]
        another = JSimplex.basis_matrix(workspace)
        fill!(B.nzval, T(9))
        fill!(B.rowval, 1)
        @test Matrix(another) == T[4 0 2; 0 -1 0; 6 0 5]
        @test Matrix(workspace.problem.A) == T[2 0 4; 0 3 0; 5 0 6]
        JSimplex.recompute!(workspace;refactorize=true)
        rhs = T[2, 4, 6]
        @test another * JSimplex.forward_solve(workspace.factorization, rhs) ≈ rhs
        @test transpose(another) * JSimplex.transpose_solve(workspace.factorization, rhs) ≈ rhs

        empty_problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[0])
        empty_workspace = JSimplex.initialize_workspace(empty_problem, SolverOptions(T;verbose=false))
        empty_basis = @inferred JSimplex.basis_matrix(empty_workspace)
        @test size(empty_basis) == (0, 0)
        @test empty_basis.colptr == [1]
        @test isempty(empty_basis.rowval) && isempty(empty_basis.nzval)
    end
end

@testset "Basis assembly handles an empty structural column" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 2, 1), [0.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.basis = JSimplex.Basis([1, 3],
        [JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.BASIC])
    B = JSimplex.basis_matrix(workspace)
    @test Matrix(B) == [0.0 0.0; 0.0 -1.0]
    @test B.colptr == [1, 1, 2]
end
