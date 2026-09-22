const RUNTIME_FACTORIZATION_TYPES =
    (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})

@testset "Packed upper setters preserve entries and row incidence" begin
    for T in RUNTIME_FACTORIZATION_TYPES, present in (false, true),
        value in (zero(T), -zero(T), T(-9))
        column = JSimplex.PackedUpperColumn{T}(
            present ? [1, 2, 3] : [1, 3], present ? T[2, 5, 6] : T[2, 6],
        )
        plain_column = JSimplex.PackedUpperColumn{T}(copy(column.indices), copy(column.values))
        upper = [JSimplex.PackedUpperColumn{T}([1], T[1]), column,
                 JSimplex.PackedUpperColumn{T}([2, 3], T[4, 1])]
        row_columns = [[1, 2], present ? [2, 3] : [3], [2, 3]]
        @test isnothing(JSimplex._set_upper_value!(upper, row_columns, 2, 2, value))
        @test isnothing(JSimplex._set_upper_value!(plain_column, 2, value))
        expected_indices = iszero(value) ? [1, 3] : [1, 2, 3]
        expected_values = iszero(value) ? T[2, 6] : T[2, value, 6]
        @test column.indices == expected_indices
        @test isequal(column.values, expected_values)
        @test plain_column.indices == expected_indices
        @test isequal(plain_column.values, expected_values)
        @test row_columns == [[1, 2], iszero(value) ? [3] : [2, 3], [2, 3]]
        @test isequal(upper[1].values, T[1])
        @test isequal(upper[3].values, T[4, 1])
    end
end

@testset "Markowitz setters preserve mirrored entries and dictionary order" begin
    for T in RUNTIME_FACTORIZATION_TYPES, D in (Dict{Int,T}, JSimplex.OrderedCollections.OrderedDict{Int,T}),
        present in (false, true), value in (zero(T), -zero(T), T(-9))
        rows = [D(3 => T(6), 1 => T(2)), D(2 => T(4)), D(2 => T(7))]
        columns = [D(1 => T(2)), D(2 => T(4), 3 => T(7)), D(1 => T(6))]
        if present
            rows[1][2] = T(5)
            columns[2][1] = T(5)
        end
        singleton_rows = [2, 3]
        singleton_columns = [1, 3]
        doubleton_columns = present ? BitSet() : BitSet([2])
        nonzeros = JSimplex._markowitz_set_entry!(
            rows, columns, singleton_rows, singleton_columns, doubleton_columns,
            1, 2, value, 4 + present,
        )
        expected_rows = [D(3 => T(6), 1 => T(2)), D(2 => T(4)), D(2 => T(7))]
        expected_columns = [D(1 => T(2)), D(2 => T(4), 3 => T(7)), D(1 => T(6))]
        if !iszero(value)
            expected_rows[1][2] = value
            expected_columns[2][1] = value
        end
        @test nonzeros == 4 + !iszero(value)
        @test all(isequal.(rows, expected_rows))
        @test all(isequal.(columns, expected_columns))
        if D <: JSimplex.OrderedCollections.OrderedDict
            @test isequal(collect.(rows), collect.(expected_rows))
            @test isequal(collect.(columns), collect.(expected_columns))
        end
        @test singleton_rows == [2, 3]
        @test singleton_columns == [1, 3]
        @test doubleton_columns == (iszero(value) ? BitSet([2]) : BitSet())
    end
    for T in RUNTIME_FACTORIZATION_TYPES
        D = JSimplex.OrderedCollections.OrderedDict{Int,T}
        rows = [D(2 => T(3), 1 => T(2)), D(1 => T(4))]
        columns = [D(1 => T(2), 2 => T(4)), D(1 => T(3))]
        singleton_rows, singleton_columns, doubleton_columns = [2], [2], BitSet([1])
        @test JSimplex._markowitz_set_entry!(
            rows, columns, singleton_rows, singleton_columns, doubleton_columns,
            1, 1, zero(T), 3,
        ) == 2
        @test singleton_rows == [2, 1]
        @test singleton_columns == [2, 1]
        @test isempty(doubleton_columns)
        @test isequal(collect.(rows), [[2 => T(3)], [1 => T(4)]])
        @test isequal(collect.(columns), [[2 => T(4)], [1 => T(3)]])
    end
end

# Delegate storage and mutations to a real dictionary; count only explicit
# membership probes made by the setter, independently of runtime timings.
mutable struct RuntimeMembershipDict{T} <: AbstractDict{Int,T}
    data::Dict{Int,T}
    probes::Int
end
Base.length(dict::RuntimeMembershipDict) = length(dict.data)
Base.iterate(dict::RuntimeMembershipDict, args...) = iterate(dict.data, args...)
function Base.haskey(dict::RuntimeMembershipDict, key)
    dict.probes += 1
    return haskey(dict.data, key)
end
Base.setindex!(dict::RuntimeMembershipDict, value, key) = setindex!(dict.data, value, key)
Base.delete!(dict::RuntimeMembershipDict, key) = (delete!(dict.data, key); dict)

@testset "Nonzero Markowitz writes avoid a redundant membership probe" begin
    for present in (false, true)
        rows = [RuntimeMembershipDict(present ? Dict(1 => 2.0) : Dict{Int,Float64}(), 0)]
        columns = [RuntimeMembershipDict(copy(rows[1].data), 0)]
        singleton_rows, singleton_columns = present ? ([1], [1]) : (Int[], Int[])
        @test JSimplex._markowitz_set_entry!(
            rows, columns, singleton_rows, singleton_columns, BitSet(),
            1, 1, 3.0, Int(present),
        ) == 1
        @test rows[1].data == Dict(1 => 3.0)
        @test columns[1].data == Dict(1 => 3.0)
        @test singleton_rows == [1]
        @test singleton_columns == [1]
        @test rows[1].probes == 0
        @test columns[1].probes == 0
    end
end
