using SparseArrays, LinearAlgebra

@testset "Known upper positions support read modify write and incidence updates" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        row in 1:5, value in (zero(T), -zero(T), T(3))
        column = JSimplex.PackedUpperColumn{T}([1, 3, 5], T[2, -3, 4])
        upper = [column]
        incidence = [i in column.indices ? [1] : Int[] for i in 1:5]
        position, previous = JSimplex._upper_entry(column, row)
        reference = T[2, 0, -3, 0, 4]
        @test isequal(previous, reference[row])
        updated = previous + value
        JSimplex._set_upper_value_at!(upper, incidence, 1, row, updated, position)
        reference[row] = updated
        @test column.indices == findall(!iszero, reference)
        @test isequal(column.values, reference[column.indices])
        @test incidence == [iszero(x) ? Int[] : [1] for x in reference]
    end
end
