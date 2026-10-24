module PhasePointCopyTests

using Test, JSimplex

function copy_bytes(destination::Vector{T}, source::Vector{T}, indices::Vector{Int}) where T
    return @allocated JSimplex._copy_phase_point!(destination, source, indices)
end

@testset "Phase point copy retains mapped values and scalar owners" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        source = T[11, 22, 99, 100, 33, 44]
        mapping = [1, 2, 5, 6]
        saved = deepcopy(source)
        owners = copy(source)
        destination = zeros(T, 4)
        result = @inferred JSimplex._copy_phase_point!(destination, source, mapping)
        @test result === destination
        @test destination == T[11, 22, 33, 44]
        @test isequal(source, saved)
        @test mapping == [1, 2, 5, 6]
        @test all(source[i] === owners[i] for i in eachindex(source))
        @test all(destination[i] === owners[mapping[i]] for i in eachindex(mapping))

        padded = fill(T(-99), 6)
        @test JSimplex._copy_phase_point!(padded, source, [5, 5, 2]) === padded
        @test padded == T[33, 33, 22, -99, -99, -99]
        @test padded[1] === padded[2] === source[5]
        empty_result = T[7, 8]
        @test JSimplex._copy_phase_point!(empty_result, T[], Int[]) === empty_result
        @test empty_result == T[7, 8]
        singleton = zeros(T, 1)
        @test JSimplex._copy_phase_point!(singleton, T[9, 10], [2]) === singleton
        @test singleton == T[10]
    end
end

@testset "Phase point copy retains overlapping-input snapshots" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        point = T[1, 2, 3, 4]
        mapping = [4, 3, 2, 1]
        @test JSimplex._copy_phase_point!(point, point, mapping) === point
        @test point == T[4, 3, 2, 1]
        @test mapping == [4, 3, 2, 1]

        parent = T[1, 2, 3, 4, 5, 6]
        source = view(parent, 1:5)
        destination = view(parent, 2:5)
        @test JSimplex._copy_phase_point!(destination, source, [5, 3, 2, 1]) === destination
        @test parent == T[1, 5, 3, 2, 1, 6]
    end
    # The destination may also be the index storage. Snapshot indices before
    # the first write, exactly as the original materializing expression does.
    indices = [4, 3, 2, 1]
    @test JSimplex._copy_phase_point!(indices, [11, 22, 33, 44], indices) === indices
    @test indices == [44, 33, 22, 11]
end

@testset "Phase point copy rejects invalid access before publishing values" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        source = T[11, 22, 33, 44]
        saved = deepcopy(source)
        destination = fill(T(-99), 4)
        invalid = [1, 2, 5, 4]
        @test_throws BoundsError JSimplex._copy_phase_point!(destination, source, invalid)
        @test destination == fill(T(-99), 4)
        @test invalid == [1, 2, 5, 4]
        @test isequal(source, saved)
        short = fill(T(-99), 2)
        @test_throws BoundsError JSimplex._copy_phase_point!(short, source, [1, 2, 3, 4])
        @test short == T[-99, -99]
        @test isequal(source, saved)
    end
end

@testset "Phase point copy retains exact hardware-float bits" begin
    for T in (Float32, Float64)
        U = T === Float32 ? UInt32 : UInt64
        source = T[-0.0, Inf, -Inf, NaN, 1]
        destination = zeros(T, 5)
        JSimplex._copy_phase_point!(destination, source, [5, 4, 3, 2, 1])
        @test reinterpret(U, destination) == reverse(reinterpret(U, source))
    end
end

@testset "Phase point copy retains stored BigFloat precision" begin
    source = setprecision(BigFloat, 512) do
        [BigFloat(1) + BigFloat(2)^(-300), BigFloat(3)]
    end
    setprecision(BigFloat, 64) do
        setrounding(BigFloat, RoundDown) do
            destination = zeros(BigFloat, 2)
            @test JSimplex._copy_phase_point!(destination, source, [2, 1]) === destination
            @test destination[1] === source[2]
            @test destination[2] === source[1]
            @test precision.(destination) == [512, 512]
            @test precision(BigFloat) == 64
            @test rounding(BigFloat) == RoundDown
        end
    end
end

@testset "Disjoint phase point copy avoids a selected temporary" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        source = T.(1:4352)
        destination = zeros(T, 4096)
        mapping = vcat(collect(1:2048), collect(2305:4352))
        JSimplex._copy_phase_point!(destination, source, mapping)
        copy_bytes(destination, source, mapping)
        @test copy_bytes(destination, source, mapping) == 0
        @test destination[1] == T(1)
        @test destination[2048] == T(2048)
        @test destination[2049] == T(2305)
        @test destination[end] == T(4352)
    end
end

end # module
