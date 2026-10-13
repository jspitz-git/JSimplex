using SparseArrays, LinearAlgebra

function triangular_rotation_measure(factor, position, last)
    return @timed begin
        JSimplex._rotate_columns!(factor, position, last)
        nothing
    end
end

@testset "Repacking replaces all entries and preserves input values" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        column = JSimplex._packed_column(ones(T, 16))
        for values in (T[0, 2, 0, -3, 0, 4], zeros(T, 8), T[], T[1, -2, 3])
            original = copy(values)
            @test JSimplex._packed_column!(column, values) === column
            @test column.indices == findall(!iszero, values)
            @test isequal(column.values, values[column.indices])
            @test isequal(values, original)
            if !isempty(column.values)
                column.values[1] = T(99)
                @test isequal(values, original)
            end
        end
    end
    values = [0.0, -0.0, NaN, Inf, -Inf, nextfloat(0.0)]
    column = JSimplex._packed_column(ones(16))
    JSimplex._packed_column!(column, values)
    @test column.indices == [3, 4, 5, 6]
    @test isequal(column.values, values[3:6])

    values = setprecision(BigFloat, 512) do
        [BigFloat(0), BigFloat(1) + BigFloat(2)^(-300)]
    end
    setprecision(BigFloat, 64) do
        column = JSimplex._packed_column(BigFloat[1, 2, 3])
        JSimplex._packed_column!(column, values)
        @test column.indices == [2]
        @test isequal(only(column.values), values[2])
        @test precision(only(column.values)) == 512
    end
end

@testset "Triangular rotation reuses established column capacity" begin
    for Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        factor = Factor(spdiagm(0 => ones(32)))
        # Rotate every column through a dense spike once, warming both code and
        # storage. Repeated replacement must then avoid allocating new arrays.
        factor.spike .= 2.0
        for _ in 1:32
            triangular_rotation_measure(factor, 1, 32)
        end
        measured = triangular_rotation_measure(factor, 1, 32)
        @test measured.bytes == 0
        @test Base.gc_alloc_count(measured.gcstats) == 0
        @test factor.upper[end].indices == collect(1:32)
        @test factor.upper[end].values == fill(2.0, 32)
    end
end

@testset "Reused triangular columns preserve copies through repeated pivots" begin
    for backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        B = Matrix{T}(I, 4, 4)
        factor = Factor(B, Val(backend))
        rhs = T[1, 2, 3, 4]
        for (pivot, replacement) in ((1,T[2,1,0,-1]), (4,T[0,0,1,2]),
                                      (2,T[0,2,0,0]), (1,T[1,0,0,0]),
                                      (3,T[1,-1,2,1]), (4,T[0,0,0,1]))
            old = copy(B)
            saved = JSimplex.copy_basis_factorization(factor)
            tableau = JSimplex.forward_solve(factor, replacement)
            JSimplex.replace_column!(factor, tableau, pivot)
            B[:, pivot] = replacement
            fill!(tableau, zero(T))
            @test B * JSimplex.forward_solve(factor, rhs) ≈ rhs
            @test transpose(B) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
            @test old * JSimplex.forward_solve(saved, rhs) ≈ rhs
            @test transpose(old) * JSimplex.transpose_solve(saved, rhs) ≈ rhs
        end
        JSimplex.refactorize!(factor, B)
        @test B * JSimplex.forward_solve(factor, rhs) ≈ rhs
    end
end
