using SparseArrays, LinearAlgebra

function runtime_band_upper!(factor, ::Type{T}, n) where T
    B = Matrix(spdiagm(0 => fill(T(2), n), 1 => fill(T(1//4), n-1),
                       7 => fill(T(-1//8), max(0,n-7))))
    for j in 1:n
        factor.upper[j] = JSimplex._packed_column(B[:,j])
    end
    return B
end

@testset "Local row incidence visits only ascending trailing columns" begin
    for Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization)
        f = Factor(spdiagm(0 => ones(64)))
        B = runtime_band_upper!(f, Float64, 64)
        rows = JSimplex._triangular_row_columns!(f, 3, 40)
        @test sum(length, rows) < 2 * 64
        for row in 1:64
            expected = 3 <= row <= 40 ? [j for j in row+1:64 if !iszero(B[row,j])] : Int[]
            @test rows[row] == expected
        end
        # Rebuilding a different range clears old lists and excludes diagonals.
        rows = JSimplex._triangular_row_columns!(f, 20, 25)
        for row in 1:64
            expected = 20 <= row <= 25 ? [j for j in row+1:64 if !iszero(B[row,j])] : Int[]
            @test rows[row] == expected
        end
        warm = JSimplex._triangular_row_columns!(f, 3, 40)
        @test (@allocated JSimplex._triangular_row_columns!(f, 3, 40)) == 0
        saved = JSimplex.copy_basis_factorization(f)
        @test saved.row_columns !== f.row_columns
        JSimplex._triangular_row_columns!(saved, 3, 40)
        @test all(saved.row_columns[i] !== f.row_columns[i] for i in 1:64)
        JSimplex.refactorize!(f, spdiagm(0 => ones(8)))
        @test length(f.row_columns) >= 64
        @test all(isempty, f.row_columns)
        @test all(isempty, JSimplex._triangular_row_columns!(f, 1, 7))
    end
end

@testset "Sparse row traversal preserves solves through pivots, copies and resets" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization),
        reach in (24,32)
        n = 32
        f = Factor(spdiagm(0 => ones(T,n)))
        B = runtime_band_upper!(f,T,n)
        if T === Rational{Int64}
            # A long chain of rational pivots exceeds fixed-width denominators.
            # Keep the sparse traversal span but limit arithmetic depth.
            for j in 9:n
                B[:,j] .= zero(T)
                B[j,j] = T(2)
                f.upper[j] = JSimplex._packed_column(B[:,j])
            end
        end
        rhs = T.(1:n)
        for pivot in (1, 8, 2)
            saved = JSimplex.copy_basis_factorization(f)
            previous = copy(B)
            direction = zeros(T,n)
            direction[1:reach] .= T(1//8)
            direction[pivot] = T(2)
            replacement = B * direction
            JSimplex.replace_column!(f,direction,pivot)
            if Factor === JSimplex.SuhlSuhlFactorization && reach == 24 && pivot == 1
                @test f.updates[end].last == 24 < n
                @test !isempty(f.row_columns)
                T === Rational{Int64} || @test 31 in f.row_columns[23]
            end
            B[:,pivot] = replacement
            @test B * JSimplex.forward_solve(f,rhs) ≈ rhs
            @test transpose(B) * JSimplex.transpose_solve(f,rhs) ≈ rhs
            @test previous * JSimplex.forward_solve(saved,rhs) ≈ rhs
            @test transpose(previous) * JSimplex.transpose_solve(saved,rhs) ≈ rhs
        end
        @test !isempty(f.row_columns)
        JSimplex.refactorize!(f,spdiagm(0 => ones(T,n)))
        @test all(isempty,f.row_columns)
        @test JSimplex.forward_solve(f,rhs) == rhs
    end
end
