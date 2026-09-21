@testset "Phase-I matrix avoids intermediate sparse matrices" begin
    A = JSimplex.SparseArrays.spdiagm(0 => ones(1024))
    rows, signs = collect(1:1024), ones(1024)
    JSimplex._primal_phase_one_matrix(A, rows, signs)
    # Final CSC storage needs about 48 KiB for 2,048 one-entry columns.
    @test (@allocated JSimplex._primal_phase_one_matrix(A, rows, signs)) <= 55_000
end

@testset "Phase-I matrix appends ordered owned columns" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        # Keep an explicitly stored zero in the original matrix.
        A = JSimplex.SparseArrays.SparseMatrixCSC(3, 2, [1, 3, 4], [1, 3, 2], T[2, 0, -3])
        rows, signs = [1, 3], T[1, -1]
        B = @inferred JSimplex._primal_phase_one_matrix(A, rows, signs)
        @test size(B) == (3, 4)
        @test B.colptr == [1, 3, 4, 5, 6]
        @test B.rowval == [1, 3, 2, 1, 3]
        @test isequal(B.nzval, T[2, 0, -3, 1, -1])
        @test Matrix(B) == T[2 0 1 0; 0 -3 0 0; 0 0 0 -1]
        B.colptr[2] = 2
        B.rowval[1] = 2
        B.rowval[end] = 2
        B.nzval[1] = T(99)
        B.nzval[end] = T(99)
        @test A.colptr == [1, 3, 4]
        @test A.rowval == [1, 3, 2]
        @test A.nzval == T[2, 0, -3]
        @test rows == [1, 3]
        @test signs == T[1, -1]

        for (m, n, added_rows) in ((0, 0, Int[]), (0, 3, Int[]),
                                  (3, 0, Int[]), (3, 0, [2]), (3, 2, Int[]))
            original = JSimplex.SparseArrays.spzeros(T, m, n)
            added_signs = ones(T, length(added_rows))
            result = @inferred JSimplex._primal_phase_one_matrix(original, added_rows, added_signs)
            expected = hcat(original, JSimplex.SparseArrays.sparse(
                added_rows, collect(1:length(added_rows)), added_signs, m, length(added_rows)))
            @test result == expected
            @test result.colptr == expected.colptr
            @test result.rowval == expected.rowval
            @test result.nzval == expected.nzval
            @test result.colptr !== original.colptr
            @test result.rowval !== original.rowval
            @test result.nzval !== original.nzval
        end
    end
end

@testset "Phase-I matrix copies only active CSC storage" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        A = JSimplex.SparseArrays.SparseMatrixCSC(2, 1, [1, 2], [1], T[2])
        # Grow backing arrays after construction without adding a matrix entry.
        push!(A.rowval, 2)
        push!(A.nzval, T(99))
        result = JSimplex._primal_phase_one_matrix(A, [2], T[-1])
        @test result.colptr == [1, 2, 3]
        @test result.rowval == [1, 2]
        @test result.nzval == T[2, -1]
        @test Matrix(result) == T[2 0; 0 -1]
    end
end

@testset "Phase-I matrix retains stored BigFloat coefficient bits" begin
    A, signs = setprecision(BigFloat, 512) do
        value = BigFloat(1) + BigFloat(2)^(-300)
        JSimplex.SparseArrays.sparse(reshape([value], 1, 1)), [BigFloat(-1)]
    end
    setprecision(BigFloat, 64) do
        result = JSimplex._primal_phase_one_matrix(A, [1], signs)
        @test isequal(result.nzval, [only(A.nzval), only(signs)])
        @test all(value -> precision(value) == 512, result.nzval)
    end
end
