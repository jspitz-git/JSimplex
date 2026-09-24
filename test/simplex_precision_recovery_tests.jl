using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Precision recovery interfaces" begin
    @test isdefined(JSimplex, :next_working_precision)
    @test isdefined(JSimplex, :solve_with_precision_recovery)
end

if isdefined(JSimplex, :next_working_precision)
    @testset "Working precision levels and ceilings" begin
        policy = JSimplex.NumericalPolicy(Float64; precision_boosting=true)
        @test JSimplex.next_working_precision(Float32, 24, policy) == 53
        @test JSimplex.next_working_precision(Float64, 53, policy) == 128
        @test JSimplex.next_working_precision(BigFloat, 128, policy) == 256
        @test JSimplex.next_working_precision(BigFloat, 160, policy) == 256
        @test JSimplex.next_working_precision(BigFloat, 256, policy) == 512
        @test isnothing(JSimplex.next_working_precision(BigFloat, 512, policy))
        @test isnothing(JSimplex.next_working_precision(BigFloat, 1024, policy))
        @test isnothing(JSimplex.next_working_precision(Rational{BigInt}, 0, policy))
        @test isnothing(JSimplex.next_working_precision(Float64, 53,
            JSimplex.NumericalPolicy(Float64)))
        limited = JSimplex.NumericalPolicy(Float64;
            precision_boosting=true, max_precision_bits=192)
        @test JSimplex.next_working_precision(Float64, 53, limited) == 128
        @test isnothing(JSimplex.next_working_precision(BigFloat, 128, limited))
        wider = JSimplex.NumericalPolicy(Float64;
            precision_boosting=true, max_precision_bits=2048)
        @test JSimplex.next_working_precision(BigFloat, 600, wider) == 1024
        @test JSimplex.next_working_precision(BigFloat, 1024, wider) == 2048
        @test_throws ArgumentError JSimplex.next_working_precision(Float64, -1, policy)
        @test_throws ArgumentError JSimplex.NumericalPolicy(Float64;
            max_precision_memory_bytes=-1)
    end
end
