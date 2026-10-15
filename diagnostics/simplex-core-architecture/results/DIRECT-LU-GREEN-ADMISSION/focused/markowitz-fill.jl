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

