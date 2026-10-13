using SparseArrays

@testset "Row pricing agrees with the independent CSC product" begin
    @test isdefined(JSimplex, :RowAccess)
    @test isdefined(JSimplex, :sparse_price!)
    if isdefined(JSimplex, :RowAccess) && isdefined(JSimplex, :sparse_price!)
        for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
            A = sparse(T[1 2; 3 4])
            rows = JSimplex.RowAccess(A)
            rho = JSimplex.IndexedVector{T}(2)
            out = JSimplex.IndexedVector{T}(4)
            JSimplex.add_entry!(rho, 2, T(2))
            JSimplex.sparse_price!(out, A, rho, rows)
            @test out.values == T[6,8,0,-2]
            @test sort(out.indices) == [1,2,4]
            @test rho.indices == [2] && rho.values == T[0,2]
            JSimplex.load_indexed!(rho, T[2,-1])
            JSimplex.sparse_price!(out, A, rho, rows)
            @test out.values == vcat(transpose(A)*rho.values, -rho.values)
            @test Set(out.indices) == Set(findall(!iszero, out.values))
            JSimplex.clear!(rho)
            JSimplex.sparse_price!(out, A, rho, rows)
            @test isempty(out.indices) && all(iszero,out.values)
            @test_throws ArgumentError JSimplex.sparse_price!(out, copy(A), rho, rows)
            @test_throws DimensionMismatch JSimplex.sparse_price!(rho, A, rho, rows)
        end
    end
end
