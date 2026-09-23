@testset "Indexed vectors preserve exact support and owned storage" begin
    @test isdefined(JSimplex, :IndexedVector)
    if isdefined(JSimplex, :IndexedVector)
        for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
            v = JSimplex.IndexedVector{T}(4)
            JSimplex.add_entry!(v, 3, T(2))
            JSimplex.add_entry!(v, 3, -T(2))
            JSimplex.add_entry!(v, 3, one(T))
            @test v.indices == [3]
            JSimplex.add_entry!(v, 3, -one(T))
            JSimplex.compact_support!(v)
            @test isempty(v.indices)
            JSimplex.add_entry!(v, 3, one(T))
            @test v.indices == [3]
            @test JSimplex.dense_values(v) == T[0,0,1,0]
            JSimplex.add_entry!(v, 1, -zero(T))
            @test v.indices == [3]
            copy_v = copy(v)
            JSimplex.add_entry!(copy_v, 3, one(T))
            @test v.values[3] == one(T)
            @test copy_v.values !== v.values && copy_v.indices !== v.indices
            JSimplex.clear!(v)
            @test isempty(v.indices) && all(iszero, v.values)
            JSimplex.load_indexed!(v, T[1,0,0,2])
            @test v.indices == [1,4]
            JSimplex.set_entry!(v, 1, zero(T))
            JSimplex.compact_support!(v)
            @test v.indices == [4]
            v.generation = typemax(UInt)
            JSimplex.clear!(v)
            JSimplex.add_entry!(v, 1, one(T))
            @test v.indices == [1] && v.values == T[1,0,0,0]
            @test v.generation != 0
            @test_throws BoundsError JSimplex.add_entry!(v, 5, one(T))
            @test_throws DimensionMismatch JSimplex.load_indexed!(v, T[1])
            @test_throws ArgumentError JSimplex.load_indexed!(v, v.values)
        end
        @test_throws ArgumentError JSimplex.IndexedVector{Float64}(-1)
        empty_v = JSimplex.IndexedVector{Float64}(0)
        JSimplex.clear!(empty_v)
        @test isempty(empty_v.values) && isempty(empty_v.indices)
        v = JSimplex.IndexedVector{Float64}(2)
        JSimplex.add_entry!(v, 2, nextfloat(0.0))
        @test v.indices == [2] && v.values[2] == nextfloat(0.0)
        @test_throws ArgumentError JSimplex.add_entry!(v, 1, NaN)
        @test_throws ArgumentError JSimplex.add_entry!(v, 1, Inf)
        JSimplex.add_entry!(v, 1, floatmax(Float64))
        @test_throws OverflowError JSimplex.add_entry!(v, 1, floatmax(Float64))
        @test v.values[1] == floatmax(Float64) && sort(v.indices) == [1,2]
        q = JSimplex.IndexedVector{Rational{Int64}}(1)
        JSimplex.add_entry!(q, 1, typemax(Int64)//1)
        @test_throws OverflowError JSimplex.add_entry!(q, 1, 1//1)
        @test q.values[1] == typemax(Int64)//1 && q.indices == [1]
        stored = setprecision(BigFloat, 512) do
            BigFloat(1) + BigFloat(2)^(-200)
        end
        setprecision(BigFloat, 64) do
            b = JSimplex.IndexedVector{BigFloat}(1)
            JSimplex.add_entry!(b, 1, stored)
            @test b.values[1] == stored && precision(b.values[1]) >= 512
            JSimplex.add_entry!(b, 1, -one(BigFloat))
            @test b.values[1] == stored - BigFloat(1; precision=512)
        end
    end
end
