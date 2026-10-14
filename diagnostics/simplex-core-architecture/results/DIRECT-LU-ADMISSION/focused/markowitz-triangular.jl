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

