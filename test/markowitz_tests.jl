using JSimplex.LinearAlgebra
using JSimplex.SparseArrays

function markowitz_bounded_problem(::Type{T}) where {T}
    A = sparse(T[1 1; 1 0; 0 1])
    return LinearProblem(A, T[-3, -2]; objective_constant=T(1 // 3),
        row_lower=fill(nothing, 3), row_upper=T[4, 2, 3],
        column_lower=T[0, 0], column_upper=fill(nothing, 2))
end

@testset "Markowitz sparse elimination and dense core" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        basis = Matrix{T}(LinearAlgebra.I, 12, 12)
        basis[10:12, 10:12] .= T[4 1 2; 1 5 1; 2 1 6]
        factor = JSimplex.PFIFactorization(sparse(basis), Val(:markowitz))
        backend = factor.base
        @test backend isa JSimplex.MarkowitzBackend
        @test 0 < backend.sparse_pivots < 12
        @test size(backend.core, 1) == 12 - backend.sparse_pivots
        rhs = T.(1:12)
        if T <: Rational
            @test basis * JSimplex.forward_solve(factor, rhs) == rhs
            @test transpose(basis) * JSimplex.transpose_solve(factor, rhs) == rhs
        else
            @test basis * JSimplex.forward_solve(factor, rhs) ≈ rhs
            @test transpose(basis) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
        end

        replacement = T[2; zeros(T, 11)]
        tableau = JSimplex.forward_solve(factor, replacement)
        JSimplex.replace_column!(factor, tableau, 1)
        basis[:, 1] = replacement
        @test basis * JSimplex.forward_solve(factor, rhs) ≈ rhs
        @test transpose(basis) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
        copied = JSimplex.copy_basis_factorization(factor)
        @test copied.base.work !== factor.base.work
        @test basis * JSimplex.forward_solve(copied, rhs) ≈ rhs
        JSimplex.refactorize!(factor, sparse(basis))
        @test factor.base isa JSimplex.MarkowitzBackend
        @test isempty(factor.updates)
        @test basis * JSimplex.forward_solve(factor, rhs) ≈ rhs
    end

    dense = Float64[4 1 2; 1 5 1; 2 1 6]
    backend = JSimplex.MarkowitzBackend(dense)
    @test backend.sparse_pivots == 0
    @test size(backend.core, 1) == 3
    empty_backend = JSimplex.MarkowitzBackend(zeros(0, 0))
    @test JSimplex._backend_dimension(empty_backend) == 0
    @test_throws LinearAlgebra.SingularException JSimplex.MarkowitzBackend(
        sparse([1.0 0.0; 0.0 0.0]),
    )
end

@testset "Markowitz fill pivots and permutations" begin
    for T in (Float64, Rational{BigInt})
        n = 24
        tridiagonal = spdiagm(-1 => fill(-one(T), n - 1),
                              0 => fill(T(4), n),
                              1 => fill(-one(T), n - 1))
        row_permutation = vcat(2:n, 1)
        column_permutation = n:-1:1
        basis = tridiagonal[row_permutation, column_permutation]
        factor = JSimplex.PFIFactorization(basis, Val(:markowitz))
        @test factor.base.sparse_pivots > 0
        @test !isempty(factor.base.lower[1].indices)
        rhs = T.(1:n)
        solution = JSimplex.forward_solve(factor, rhs)
        transpose_solution = JSimplex.transpose_solve(factor, rhs)
        if T <: Rational
            @test basis * solution == rhs
            @test transpose(basis) * transpose_solution == rhs
        else
            @test basis * solution ≈ rhs
            @test transpose(basis) * transpose_solution ≈ rhs
        end
    end
end

@testset "Markowitz threshold respects stored BigFloat precision" begin
    larger = setprecision(BigFloat, 256) do
        BigFloat(10) + ldexp(BigFloat(1), -40)
    end
    smaller = setprecision(BigFloat, 24) do
        BigFloat(1)
    end
    setprecision(BigFloat, 24) do
        @test !JSimplex._markowitz_threshold_pass(smaller, larger)
    end
    tiny = ldexp(BigFloat(1), -1_000_000)
    JSimplex._markowitz_threshold_pass(tiny, 9 * tiny)
    @test (@allocated JSimplex._markowitz_threshold_pass(tiny, 9 * tiny)) < 100_000
end

@testset "Triangular updates accumulate over a Markowitz base" begin
    for Factorization in (JSimplex.ForrestTomlinFactorization,
                          JSimplex.BartelsGolubFactorization,
                          JSimplex.SuhlSuhlFactorization)
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            basis = Matrix{T}(LinearAlgebra.I, 12, 12)
            basis[1:4, 1:4] .= T[2 0 1 0; 1 3 0 0; 0 1 2 1; 0 0 1 2]
            factor = Factorization(sparse(basis), Val(:markowitz))
            @test factor.base.sparse_pivots > 0
            rhs = T.(1:12)
            for (column, values) in ((2, T[1, 2, 0, 1]),
                                     (1, T[3, 0, 1, 0]),
                                     (3, T[0, 1, 3, 1]))
                replacement = vcat(values, zeros(T, 8))
                tableau = JSimplex.forward_solve(factor, replacement)
                JSimplex.replace_column!(factor, tableau, column)
                basis[:, column] = replacement
                if T <: Rational
                    @test basis * JSimplex.forward_solve(factor, rhs) == rhs
                    @test transpose(basis) * JSimplex.transpose_solve(factor, rhs) == rhs
                else
                    @test basis * JSimplex.forward_solve(factor, rhs) ≈ rhs
                    @test transpose(basis) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
                end
            end
            @test length(factor.updates) == 3
            copied = JSimplex.copy_basis_factorization(factor)
            @test copied.base.work !== factor.base.work
            @test basis * JSimplex.forward_solve(copied, rhs) ≈ rhs
            JSimplex.refactorize!(factor, sparse(basis))
            @test isempty(factor.updates)
            @test basis * JSimplex.forward_solve(factor, rhs) ≈ rhs
        end
    end
end

@testset "Markowitz backend retains sparse storage and solve buffers" begin
    backend = JSimplex.MarkowitzBackend(spdiagm(0 => ones(512)))
    @test backend.sparse_pivots > 500
    @test Base.summarysize(backend) < 250_000
    stored_zeros = SparseMatrixCSC(32, 32, collect(1:32:1025),
                                   repeat(1:32, 32),
                                   vec(Matrix{Float64}(LinearAlgebra.I, 32, 32)))
    @test nnz(stored_zeros) == 1024
    @test JSimplex.MarkowitzBackend(stored_zeros).sparse_pivots > 0
    factor = JSimplex.PFIFactorization(spdiagm(0 => ones(64)), Val(:markowitz))
    rhs = ones(64)
    destination = similar(rhs)
    JSimplex.forward_solve!(destination, factor, rhs)
    JSimplex.transpose_solve!(destination, factor, rhs)
    @test (@allocated JSimplex.forward_solve!(destination, factor, rhs)) == 0
    @test (@allocated JSimplex.transpose_solve!(destination, factor, rhs)) == 0
end

@testset "Markowitz refactorization is selectable for every basis update" begin
    for mode in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl)
        for T in (Float32, Float64, BigFloat, Rational{BigInt})
            options = SolverOptions(T; basis_update=mode,
                                    basis_refactorization=:markowitz,
                                    refactorization_interval=1, verbose=false)
            problem = markowitz_bounded_problem(T)
            workspace = @inferred JSimplex.initialize_workspace(problem, options)
            @test workspace.factorization.base isa JSimplex.MarkowitzBackend
            @test all(isconcretetype, fieldtypes(typeof(workspace)))
            result = solve(problem; options)
            @test result.status == OPTIMAL
            @test result.statistics.refactorizations >= 2
            @test result.primal ≈ T[2, 2]
        end
    end
end
