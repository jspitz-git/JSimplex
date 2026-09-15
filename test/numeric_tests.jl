@testset "Numeric policy and tagged bounds" begin
    finite = @inferred Bound(3.0f0)
    @test finite isa Bound{Float32}
    @test isfinite(finite)
    @test @inferred(bound_value(finite)) === 3.0f0

    missing = @inferred JSimplex._unbounded_bound(Rational{BigInt})
    constructed_missing = @inferred Bound{Rational{BigInt}}(nothing)
    @test missing isa Bound{Rational{BigInt}}
    @test constructed_missing == missing
    @test !isfinite(missing)
    @test_throws ArgumentError bound_value(missing)

    @test JSimplex._is_exact(Rational{BigInt}) === Val(true)
    @test JSimplex._is_exact(Float64) === Val(false)
    @test JSimplex._typed_ratio(Float32, 1, 10^7) isa Float32
    @test JSimplex._typed_ratio(Rational{BigInt}, 1, 10^7) == 1 // big(10)^7
    @test JSimplex._supported_value_type(Float64)
    @test JSimplex._supported_value_type(Rational{Int})
    @test !JSimplex._supported_value_type(Int)

    exact_lower = @inferred JSimplex._normalize_bound(
        Rational{BigInt}, -Inf, :lower, "column lower bound",
    )
    exact_upper = @inferred JSimplex._normalize_bound(
        Rational{BigInt}, nothing, :upper, "column upper bound",
    )
    @test !isfinite(exact_lower)
    @test !isfinite(exact_upper)
    @test_throws ArgumentError JSimplex._normalize_bound(
        Float64, Inf, :lower, "column lower bound",
    )
end
