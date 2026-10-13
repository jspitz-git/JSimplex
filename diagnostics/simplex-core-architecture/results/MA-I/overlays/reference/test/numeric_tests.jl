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

    normalized_finite = @inferred JSimplex._normalize_bound(
        Float64, finite, :lower, "column lower bound",
    )
    @test normalized_finite == Bound(3.0)

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

@testset "Bound equality and hashed collection lookup" begin
    equal_bounds = (Bound(big(3) // 4), Bound(big(3) // 4), Bound(3 // 4),
                    Bound(0.75f0), Bound(0.75), Bound(big"0.75"))
    for left in equal_bounds, right in equal_bounds
        @test left == right
        @test @inferred(isequal(left, right))
        @test @inferred(hash(left)) == hash(right)
        @test hash(left, UInt(17)) == hash(right, UInt(17))
        @test get(Dict(left => :found), right, :missing) === :found
        @test right in Set([left])
    end
    @test length(Set(equal_bounds)) == 1
    @test !isequal(first(equal_bounds), Bound(1))

    unbounded = (Bound{Float32}(nothing), Bound{Float64}(nothing),
                 Bound{BigFloat}(nothing), Bound{Rational{BigInt}}(nothing))
    for left in unbounded, right in unbounded
        @test left == right
        @test isequal(left, right)
        @test hash(left) == hash(right)
        @test get(Dict(left => :found), right, :missing) === :found
    end
    @test length(Set(unbounded)) == 1
    for missing in unbounded
        @test missing != Bound(0)
        @test !isequal(missing, Bound(0))
        @test length(Set([missing, Bound(0)])) == 2
    end

    positive_zeros = (Bound(0.0f0), Bound(0.0), Bound(big"0.0"), Bound(big(0) // 1))
    negative_zeros = (Bound(-0.0f0), Bound(-0.0), Bound(big"-0.0"))
    for positive in positive_zeros, negative in negative_zeros
        @test positive == negative
        @test !isequal(positive, negative)
        @test length(Set([positive, negative])) == 2
        @test get(Dict(positive => :positive, negative => :negative),
                  Bound(-0.0), :missing) === :negative
    end
    @test length(Set(positive_zeros)) == 1
    @test length(Set(negative_zeros)) == 1
end
