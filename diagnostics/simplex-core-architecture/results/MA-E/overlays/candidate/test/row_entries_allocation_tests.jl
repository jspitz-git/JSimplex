using SparseArrays

@testset "Row entries avoid repeated vector growth" begin
    dense = sparse(ones(128, 128))
    JSimplex._row_entries(dense)
    @test (@allocated JSimplex._row_entries(dense)) <= 300_000

    # A row-count scratch array would be wasteful for these sparse shapes.
    for (matrix, budget) in ((spzeros(128, 128), 6_000),
            (sparse([1, 1000], [1, 2], [1.0, 2.0], 1000, 2), 41_000),
            (SparseMatrixCSC(128, 1, [1, 129], collect(1:128), zeros(128)), 6_000))
        JSimplex._row_entries(matrix)
        @test (@allocated JSimplex._row_entries(matrix)) <= budget
    end
end

@testset "Row entries retain column order and coefficients without sharing buffers" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        matrix = SparseMatrixCSC(4, 6, [1, 3, 5, 6, 7, 8, 10],
            [1, 4, 2, 3, 4, 1, 2, 1, 3], T[1, 5, 4, 0, 6, -2, -0.0, 3, 0])
        original = copy(matrix)
        # Extra backing storage must never become an entry.
        push!(matrix.rowval, 2)
        push!(matrix.nzval, T(99))
        entries = @inferred JSimplex._row_entries(matrix)
        @test entries isa Vector{Vector{Tuple{Int,T}}}
        @test entries == [[(1, T(1)), (4, T(-2)), (6, T(3))], [(2, T(4))],
                          Tuple{Int,T}[], [(1, T(5)), (3, T(6))]]
        @test matrix.colptr == original.colptr
        @test matrix.rowval == [1, 4, 2, 3, 4, 1, 2, 1, 3, 2]
        @test isequal(matrix.nzval, vcat(original.nzval, T(99)))
        another = JSimplex._row_entries(matrix)
        entries[1][1] = (6, T(20))
        push!(entries[3], (2, T(7)))
        @test another[1] == [(1, T(1)), (4, T(-2)), (6, T(3))]
        @test isempty(another[3])
        @test matrix.nzval[1] == T(1)

        # Exercise the sparse path as well as the preallocated path.
        sparse_matrix = sparse([1, 4], [3, 1], T[2, -3], 5, 3)
        sparse_entries = @inferred JSimplex._row_entries(sparse_matrix)
        @test sparse_entries == [[(3, T(2))], Tuple{Int,T}[], Tuple{Int,T}[],
                                 [(1, T(-3))], Tuple{Int,T}[]]
        push!(sparse_entries[2], (1, T(5)))
        @test isempty(sparse_entries[3])
        @test isempty(sparse_entries[5])
    end
end

@testset "Row entries preserve stored BigFloat precision" begin
    matrix = setprecision(BigFloat, 256) do
        sparse(reshape([BigFloat(1) / 3, BigFloat(2) / 7], 1, 2))
    end
    entries = setprecision(BigFloat, 64) do
        JSimplex._row_entries(matrix)
    end
    @test entries[1][1][2] === matrix.nzval[1]
    @test entries[1][2][2] === matrix.nzval[2]
    @test precision(entries[1][1][2]) == 256
end

@testset "Row entries support empty dimensions" begin
    for (rows, columns) in ((0, 0), (0, 3), (3, 0), (3, 4))
        entries = JSimplex._row_entries(spzeros(rows, columns))
        @test length(entries) == rows
        @test all(isempty, entries)
        if rows > 0
            push!(entries[1], (1, 2.0))
            @test isempty(entries[2])
        end
    end
end
