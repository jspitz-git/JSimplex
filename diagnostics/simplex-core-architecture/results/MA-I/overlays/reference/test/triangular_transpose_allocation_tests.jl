using SparseArrays, LinearAlgebra

# Include source restoration in the measurement so all alias modes repeatedly
# solve the same system. A boxed row-order wrapper must fail the zero-byte check.
function triangular_transpose_bytes!(destination, factor, source, rhs)
    return @allocated begin
        copyto!(source, rhs)
        JSimplex.transpose_solve!(destination, factor, source)
    end
end

@testset "Triangular BTRAN avoids row-order boxing" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization),
        backend in (:native, :markowitz), T in (Float32, Float64), n in (0, 8)
        B = Matrix{T}(I, n, n)
        factor = Factor(sparse(B), Val(backend))
        rhs = T.(1:n)
        destination = similar(rhs)
        for stage in (:initial, :updated, :refactorized)
            if stage === :updated && n > 0
                # Move logical rows and exercise nonidentity upper coefficients.
                replacement = fill(T(0.125), n)
                replacement[2] = T(2)
                direction = JSimplex.forward_solve(factor, replacement)
                JSimplex.replace_column!(factor, direction, 2)
                B[:, 2] = replacement
            elseif stage === :refactorized
                JSimplex.refactorize!(factor, sparse(B))
            end
            for source in (copy(rhs), destination, factor.work)
                triangular_transpose_bytes!(destination, factor, source, rhs)
                triangular_transpose_bytes!(destination, factor, source, rhs)
                @test triangular_transpose_bytes!(destination, factor, source, rhs) == 0
                @test transpose(B) * destination ≈ rhs
            end
        end
    end
end
