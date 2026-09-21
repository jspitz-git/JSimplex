@testset "Packed upper columns avoid vector growth" begin
    values = ones(1024)
    column = JSimplex._packed_column(values)
    @test column.indices == collect(1:1024)
    @test column.values == values
    # Two final arrays require about 16 KiB; repeated growth exceeds this budget.
    @test (@allocated JSimplex._packed_column(values)) <= 20_000
end

@testset "Packed columns leave room for the row rotation" begin
    for Factorization in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization)
        B = JSimplex.SparseArrays.spdiagm(0 => ones(128))
        values = ones(128)
        warmup = Factorization(B)
        JSimplex.replace_column!(warmup, values, 1)
        factor = Factorization(B)
        @test (@allocated JSimplex.replace_column!(factor, values, 1)) <= 4_000
        B[:, 1] = values
        rhs = collect(1.0:128.0)
        @test B * JSimplex.forward_solve(factor, rhs) ≈ rhs
        @test transpose(B) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
    end
end

@testset "Packed upper columns preserve values and own their arrays" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for values in (T[], zeros(T, 8), T[0, 2, 0, -3, 0, 4], T[1, -2, 3])
            original = copy(values)
            column = @inferred JSimplex._packed_column(values)
            repeated = JSimplex._packed_column(values)
            @test column.indices == findall(!iszero, original)
            @test isequal(column.values, original[column.indices])
            @test column.indices !== repeated.indices
            @test column.values !== repeated.values
            if !isempty(column.values)
                column.values[1] = T(99)
                column.indices[1] = 99
                @test isequal(values, original)
                @test repeated.indices == findall(!iszero, original)
                @test isequal(repeated.values, original[repeated.indices])
            end
        end
    end
    values = [0.0, -0.0, NaN, Inf, -Inf, nextfloat(0.0)]
    column = JSimplex._packed_column(values)
    @test column.indices == [3, 4, 5, 6]
    @test isequal(column.values, values[3:6])

    values = setprecision(BigFloat, 512) do
        [BigFloat(0), BigFloat(1) + BigFloat(2)^(-300)]
    end
    setprecision(BigFloat, 64) do
        column = JSimplex._packed_column(values)
        @test column.indices == [2]
        @test isequal(only(column.values), values[2])
        @test precision(only(column.values)) == 512
    end
end
