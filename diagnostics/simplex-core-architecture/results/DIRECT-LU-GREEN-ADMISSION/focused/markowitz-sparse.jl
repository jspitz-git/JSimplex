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

    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        dense = T[4 1 2; 1 5 1; 2 1 6]
        factor = JSimplex.PFIFactorization(dense, Val(:markowitz))
        @test factor.base.sparse_pivots == 0
        @test size(factor.base.core, 1) == 3
        rhs = T[1, 2, 3]
        if T <: Rational
            @test dense * JSimplex.forward_solve(factor, rhs) == rhs
        else
            @test dense * JSimplex.forward_solve(factor, rhs) ≈ rhs
        end
    end
    empty_backend = JSimplex.MarkowitzBackend(zeros(0, 0))
    @test JSimplex._backend_dimension(empty_backend) == 0
    @test_throws LinearAlgebra.SingularException JSimplex.MarkowitzBackend(
        sparse([1.0 0.0; 0.0 0.0]),
    )
end

