using SparseArrays, LinearAlgebra, Logging

function basis_reuse_measure(workspace)
    return @timed (JSimplex.recompute!(workspace; refactorize=true); nothing)
end

function basis_reuse_backend_measure(factor, B)
    return @timed (JSimplex.refactorize!(factor, B); nothing)
end

@testset "Repeated refactorization reuses basis assembly storage" begin
    with_logger(NullLogger()) do
        for backend in (:native, :markowitz), method in
            (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
            n = 64
            problem = LinearProblem(spdiagm(0 => ones(n)), zeros(n))
            workspace = JSimplex.initialize_workspace(problem,
                SolverOptions(; verbose=false, basis_update=method,
                              basis_refactorization=backend))
            B = JSimplex.basis_matrix(workspace)
            basis_reuse_measure(workspace)
            basis_reuse_backend_measure(workspace.factorization, B)
            actual = minimum(Base.gc_alloc_count(basis_reuse_measure(workspace).gcstats) for _ in 1:3)
            expected = minimum(Base.gc_alloc_count(basis_reuse_backend_measure(workspace.factorization, B).gcstats) for _ in 1:3)
            # Recompute with zero costs/RHS needs no temporary CSC arrays.
            @test actual <= expected + 2
            @test JSimplex.forward_solve(workspace.factorization, ones(n)) == -ones(n)
        end
    end
end

function basis_reuse_set_basis!(workspace, indices)
    states = fill(JSimplex.AT_LOWER, length(workspace.basis.states))
    states[indices] .= JSimplex.BASIC
    workspace.basis = JSimplex.Basis(indices, states)
end

@testset "Borrowed assembly preserves saved factors and public matrices" begin
    with_logger(NullLogger()) do
        for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
            backend in (:native, :markowitz), method in
            (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
            # Include a stored zero, an empty structural column and mixed slacks.
            A = sparse([1, 2, 3, 2, 3, 1, 3], [1, 1, 1, 2, 2, 3, 3],
                       T[2, 1, 0, 3, 1, 4, 5], 3, 4)
            original = copy(A)
            w = JSimplex.initialize_workspace(LinearProblem(A, zeros(T, 4); row_lower=zeros(T, 3)),
                SolverOptions(T; verbose=false, basis_update=method,
                              basis_refactorization=backend))
            rhs = T[2, 3, 4]
            previous = Matrix{T}(-I, 3, 3)
            for (indices, expected) in (([1, 2, 3], T[2 0 4; 1 3 0; 0 1 5]),
                    ([5, 6, 7], Matrix{T}(-I, 3, 3)),
                    ([3, 6, 1], T[4 0 2; 0 -1 1; 5 0 0]),
                    ([1, 2, 3], T[2 0 4; 1 3 0; 0 1 5]))
                saved = JSimplex.copy_basis_factorization(w.factorization)
                basis_reuse_set_basis!(w, indices)
                owned = JSimplex.basis_matrix(w)
                borrowed = @inferred JSimplex._basis_matrix!(w)
                @test Matrix(borrowed) == expected
                @test borrowed.colptr == owned.colptr
                @test borrowed.rowval == owned.rowval
                @test borrowed.nzval == owned.nzval
                JSimplex.recompute!(w; refactorize=true)
                @test expected * JSimplex.forward_solve(w.factorization, rhs) ≈ rhs
                @test transpose(expected) * JSimplex.transpose_solve(w.factorization, rhs) ≈ rhs
                # Destroy all scratch values after LU creation. Neither the new
                # factor nor a saved old one may retain mutable CSC input arrays.
                fill!(borrowed.nzval, T(99))
                @test expected * JSimplex.forward_solve(w.factorization, rhs) ≈ rhs
                @test transpose(expected) * JSimplex.transpose_solve(w.factorization, rhs) ≈ rhs
                @test previous * JSimplex.forward_solve(saved, rhs) ≈ rhs
                @test transpose(previous) * JSimplex.transpose_solve(saved, rhs) ≈ rhs
                @test Matrix(owned) == expected
                @test A == original
                previous = expected
            end
            auxiliary = JSimplex._auxiliary_workspace(w)
            basis_reuse_set_basis!(auxiliary, [5, 6, 7])
            JSimplex.recompute!(auxiliary; refactorize=true)
            @test JSimplex.forward_solve(auxiliary.factorization, rhs) ≈ -rhs
            @test previous * JSimplex.forward_solve(w.factorization, rhs) ≈ rhs
            @test Matrix(JSimplex._basis_matrix!(w)) == previous

            # Singular or invalid new bases must leave the old LU usable.
            basis_reuse_set_basis!(w, [4, 6, 7])
            @test_throws SingularException JSimplex.recompute!(w; refactorize=true)
            @test previous * JSimplex.forward_solve(w.factorization, rhs) ≈ rhs
            @test transpose(previous) * JSimplex.transpose_solve(w.factorization, rhs) ≈ rhs
            before_invalid = copy(w.scratch.basis_matrix)
            basis_reuse_set_basis!(w, [5, 5, 7])
            @test_throws ArgumentError JSimplex._basis_matrix!(w)
            @test w.scratch.basis_matrix == before_invalid
            basis_reuse_set_basis!(w, [5, 6, 7])
            JSimplex.recompute!(w; refactorize=true)
            @test JSimplex.forward_solve(w.factorization, rhs) ≈ -rhs
        end
    end
end

@testset "Basis assembly keeps capacity across sparser bases" begin
    w = JSimplex.initialize_workspace(LinearProblem(sparse([2.0 1 1; 1 3 1; 1 1 4]), zeros(3)),
                                     SolverOptions(verbose=false))
    basis_reuse_set_basis!(w, [1, 2, 3])
    JSimplex._basis_matrix!(w)
    basis_reuse_set_basis!(w, [4, 5, 6])
    @test (@allocated JSimplex._basis_matrix!(w)) == 0
    basis_reuse_set_basis!(w, [1, 2, 3])
    @test (@allocated JSimplex._basis_matrix!(w)) == 0
    @test Matrix(JSimplex._basis_matrix!(w)) == [2.0 1 1; 1 3 1; 1 1 4]
end

@testset "Borrowed assembly handles no rows and preserves stored precision" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        w = JSimplex.initialize_workspace(LinearProblem(spzeros(T, 0, 1), T[0]),
                                         SolverOptions(T; verbose=false))
        B = @inferred JSimplex._basis_matrix!(w)
        @test size(B) == (0, 0) && B.colptr == [1]
        @test isempty(B.rowval) && isempty(B.nzval)
    end
    w = setprecision(BigFloat, 512) do
        p = LinearProblem(sparse(reshape([BigFloat(1) + BigFloat(2)^(-300)], 1, 1)), BigFloat[0])
        JSimplex.initialize_workspace(p, SolverOptions(BigFloat; verbose=false))
    end
    basis_reuse_set_basis!(w, [1])
    setprecision(BigFloat, 64) do
        B = JSimplex._basis_matrix!(w)
        @test only(B.nzval) == only(w.problem.A.nzval)
        @test precision(only(B.nzval)) == 512
    end
end
