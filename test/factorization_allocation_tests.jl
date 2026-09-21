@testset "PFI update storage follows the nonzero count" begin
    dimension = 512
    basis = JSimplex.SparseArrays.spdiagm(0 => ones(dimension))
    dense_column = ones(dimension)
    sparse_column = zeros(dimension)
    sparse_column[[1, 256, 512]] .= 1.0
    for (column, budget) in ((dense_column, 10_000), (sparse_column, 1_000))
        factor = JSimplex.PFIFactorization(basis)
        JSimplex.replace_column!(factor, column, 256)
        # Discard the warmup update but retain capacity for the update list.
        empty!(factor.updates)
        @test (@allocated JSimplex.replace_column!(factor, column, 256)) <= budget
    end
end

@testset "PFI updates retain their own coefficients" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        B = Matrix{T}(JSimplex.LinearAlgebra.I, 4, 4)
        factor = JSimplex.PFIFactorization(B)
        rhs = T[2, 4, 6, 8]
        column = T[0, 2, 0, -1]
        JSimplex.replace_column!(factor, column, 2)
        B[:, 2] = column
        saved = JSimplex.copy_basis_factorization(factor)
        # Reusing caller storage and adding another update must not alter the
        # first update, including the one shared by the copied factorization.
        column .= T[1, 0, 0, 0]
        JSimplex.replace_column!(factor, column, 1)
        fill!(column, zero(T))
        @test JSimplex.forward_solve(factor, rhs) == T[2, 2, 6, 10]
        @test JSimplex.transpose_solve(factor, rhs) == T[2, 6, 6, 8]
        JSimplex.refactorize!(factor, Matrix{T}(JSimplex.LinearAlgebra.I, 4, 4))
        @test JSimplex.forward_solve(saved, rhs) == T[2, 2, 6, 10]
        @test JSimplex.transpose_solve(saved, rhs) == T[2, 6, 6, 8]
    end
end

@testset "PFI packing tests zeros after scalar conversion" begin
    factor = JSimplex.PFIFactorization(Matrix{Float32}(JSimplex.LinearAlgebra.I, 3, 3))
    # The first coefficient becomes zero on conversion to Float32.
    column = [1.0e-100, 2.0, 4.0]
    JSimplex.replace_column!(factor, column, 2)
    @test JSimplex.forward_solve(factor, Float32[1, 2, 3]) == Float32[1, 1, -1]
    @test JSimplex.transpose_solve(factor, Float32[1, 2, 3]) == Float32[1, -5, 3]
end

@testset "PFI mixed-type updates convert coefficients only once" begin
    T = Rational{BigInt}
    factor = JSimplex.PFIFactorization(Matrix{T}(JSimplex.LinearAlgebra.I, 128, 128))
    column = zeros(128)
    column[[1, 64, 128]] .= 2.0
    JSimplex.replace_column!(factor, column, 64)
    empty!(factor.updates)
    @test (@allocated JSimplex.replace_column!(factor, column, 64)) <= 50_000
end
