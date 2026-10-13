@testset "Native LU avoids redundant matrix copies" begin
    for (T, dimension, budget) in ((Float32, 128, 90_000), (Float64, 512, 570_000))
        B = JSimplex.SparseArrays.spdiagm(-1 => ones(T, dimension - 1),
            0 => fill(T(4), dimension), 1 => ones(T, dimension - 1))
        JSimplex.PFIFactorization(B)
        @test (@allocated JSimplex.PFIFactorization(B)) <= budget
    end
end

@testset "Native LU owns data across input mutation and refactorization" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}),
        make_matrix in (identity, JSimplex.SparseArrays.sparse)
        B = make_matrix(T[2 1; 1 3])
        factor = @inferred JSimplex.PFIFactorization(B)
        @test B == T[2 1; 1 3]
        fill!(B isa Matrix ? B : B.nzval, zero(T))
        rhs = T[5, 7]
        @test JSimplex.forward_solve(factor, rhs) ≈ T[8//5, 9//5]
        @test JSimplex.transpose_solve(factor, rhs) ≈ T[8//5, 9//5]

        saved = JSimplex.copy_basis_factorization(factor)
        replacement = make_matrix(T[4 1; -1 3])
        JSimplex.refactorize!(factor, replacement)
        @test replacement == T[4 1; -1 3]
        fill!(replacement isa Matrix ? replacement : replacement.nzval, zero(T))
        @test JSimplex.forward_solve(factor, rhs) ≈ T[8//13, 33//13]
        @test JSimplex.transpose_solve(factor, rhs) ≈ T[22//13, 23//13]
        @test JSimplex.forward_solve(saved, rhs) ≈ T[8//5, 9//5]
        @test JSimplex.transpose_solve(saved, rhs) ≈ T[8//5, 9//5]

        @test_throws JSimplex.LinearAlgebra.SingularException JSimplex.refactorize!(
            factor, make_matrix(zeros(T, 2, 2)))
        @test JSimplex.forward_solve(factor, rhs) ≈ T[8//13, 33//13]
        @test_throws DimensionMismatch JSimplex.PFIFactorization(make_matrix(zeros(T, 2, 3)))
    end
end
