@testset "PFI packing preserves pivot-first order and scalar arithmetic" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        backend in (:native, :markowitz), pivot in (1, 4, 7), use_view in (false, true)
        B = Matrix{T}(JSimplex.LinearAlgebra.I, 7, 7)
        factor = JSimplex.PFIFactorization(B, Val(backend))
        for support in (:dense, :sparse, :dense)
            column = T[3, -2, 1, 7, -4, 5, 2]
            support == :sparse && (column[[2, 3, 5, 6]] .= zero(T))
            input = use_view ? view(column, :) : column
            JSimplex.replace_column!(factor, input, pivot)
            eta = only(factor.updates)
            expected_indices = [pivot; [i for i in eachindex(column) if i != pivot && !iszero(column[i])]]
            expected_values = T[inv(column[pivot]); [-(column[i] / column[pivot]) for i in expected_indices[2:end]]]
            @test eta.indices == expected_indices
            @test isequal(eta.values, expected_values)
            B[:, pivot] .= column
            rhs = T[1, 2, 3, 4, 5, 6, 7]
            x = JSimplex.forward_solve(factor, rhs)
            y = JSimplex.transpose_solve(factor, rhs)
            if T <: Rational
                @test B * x == rhs
                @test transpose(B) * y == rhs
            else
                @test B * x ≈ rhs
                @test transpose(B) * y ≈ rhs
            end
            B .= Matrix{T}(JSimplex.LinearAlgebra.I, 7, 7)
            JSimplex.refactorize!(factor, B)
        end
    end
    for T in (Float32, Float64)
        f = JSimplex.PFIFactorization(Matrix{T}(JSimplex.LinearAlgebra.I, 5, 5))
        JSimplex.replace_column!(f, T[-0.0, 0.0, 3, -2, 1], 3)
        @test only(f.updates).indices == [3, 4, 5]
        @test isequal(only(f.updates).values, T[inv(T(3)), -(T(-2)/T(3)), -(T(1)/T(3))])
    end
end
