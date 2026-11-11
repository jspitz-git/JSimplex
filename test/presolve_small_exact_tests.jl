using Test, JSimplex, SparseArrays, Random, Profile

module _PresolveSmallExactTestTools
using JSimplex, SparseArrays
const JS = JSimplex
const S = JS._SmallExact
const Q = Rational{BigInt}

function outcome(f)
    try
        value = f()
        return (:value, value isa S.E ? S.wide(value) : value)
    catch exception
        return (:error, typeof(exception))
    end
end

# Compare all model, map and proof fields, including stored BigFloat precision.
snapshot(x::BigFloat) = (JS._exact_rational(x), precision(x), signbit(x))
snapshot(x::Union{Nothing,Real,Enum,AbstractString}) = x
snapshot(x::Tuple) = map(snapshot, x)
snapshot(x::AbstractArray) = (size(x), map(snapshot, collect(x)))
snapshot(x) = map(name -> snapshot(getfield(x, name)), fieldnames(typeof(x)))

function overflow_work()
    a = S.E((big(2)^100 + 1) // (big(2)^80 + 1))
    b = S.E((big(2)^100 + 3) // (big(2)^81 + 5))
    for _ in 1:20
        a < b
        S.wide(a + b)
        S.wide(a * b)
        S.wide(a / b)
        S.E(ldexp(1.234, 150))
        S.add(typemax(Int128), Int128(1))
        S.sub(typemin(Int128), Int128(1))
        S.mul(typemax(Int128), Int128(2))
    end
    return nothing
end

function propagation_pair(problem; directed_bounds=true, rows=trues(size(problem.A, 1)))
    T = eltype(problem.A)
    before = snapshot(problem)
    changed_reference, changed = falses(size(problem.A, 2)), falses(size(problem.A, 2))
    reference_history = JS._PropagationHistory.Builder(T)
    history = JS._PropagationHistory.Builder(T)
    reference = JS._propagate_row_bounds_kernel(problem, copy(rows), changed_reference, Q;
        directed_bounds, history=reference_history)
    result = JS._propagate_row_bounds(problem, copy(rows), changed;
        directed_bounds, history)
    return (isequal(snapshot(reference), snapshot(result)), changed_reference == changed,
            isequal(snapshot(reference_history), snapshot(history)), isequal(snapshot(problem), before))
end
end

@testset "Small exact conversion and checked integer boundaries" begin
    H = _PresolveSmallExactTestTools
    S, E, Q = H.S, H.S.E, H.Q
    for x in (Float32(1.25), Float64(1.25), Float32(-3), Float64(-3))
        @test S.is_small(E(x))
        @test S.wide(E(x)) == Q(x)
    end
    @test S.add(typemax(Int128), Int128(1)) == BigInt(typemax(Int128)) + 1
    @test S.sub(typemin(Int128), Int128(1)) == BigInt(typemin(Int128)) - 1
    @test S.mul(typemax(Int128), Int128(2)) == BigInt(typemax(Int128)) * 2
    @test S.add(Int64(1), Int64(2)) === Int64(3)
    @test S.wide(S.form(S.add(typemax(Int128), typemax(Int128)), Int128(1))) ==
        2BigInt(typemax(Int128))
    minimum, maximum = BigInt(typemin(Int128)), BigInt(typemax(Int128))
    for n in (minimum, minimum + 1, -maximum, -1, 0, 1, maximum),
        d in (minimum, -maximum, -2, -1, 0, 1, 2, maximum)
        @test H.outcome(() -> S.form(Int128(n), Int128(d))) == H.outcome(() -> Q(n, d))
    end
    @test !S.is_small(E(Q(minimum)))
    @test !S.is_small(E(big(2)^500 // 3))
    @test S.is_small(E(Q(maximum)))

    rng = MersenneTwister(781)
    for T in (Float32, Float64)
        values = T[0, -zero(T), 1, -1, nextfloat(zero(T)), prevfloat(zero(T)),
                   floatmin(T), -floatmin(T), floatmax(T), -floatmax(T)]
        for exponent in (-149, -127, -126, 0, 75, 100, 126, 127)
            value = ldexp(one(T), exponent)
            isfinite(value) && append!(values, T[prevfloat(value), value, nextfloat(value), -value])
        end
        append!(values, T[ldexp(T(randn(rng)), rand(rng, -150:150)) for _ in 1:100])
        filter!(isfinite, values)
        for value in values
            @test S.wide(E(value)) == Q(value)
        end
        for _ in 1:100
            a, b = rand(rng, values), rand(rng, values)
            x, y, qa, qb = E(a), E(b), Q(a), Q(b)
            for op in (+, -, *, /, <, <=, >, >=, ==)
                @test H.outcome(() -> op(x, y)) == H.outcome(() -> op(qa, qb))
            end
        end
        for value in (T(Inf), T(-Inf), T(NaN))
            @test H.outcome(() -> E(value)) == H.outcome(() -> Q(value))
        end
    end
end

@testset "Small exact arithmetic agrees with BigInt rational oracle" begin
    H = _PresolveSmallExactTestTools
    S, E, Q = H.S, H.S.E, H.Q
    minimum, maximum = BigInt(typemin(Int128)), BigInt(typemax(Int128))
    values = Q[minimum // 1, (minimum + 1) // 1, -maximum // 1, maximum // 1,
               1 // 2, -1 // 2, 0 // 1, 1 // 1, -1 // 1, 1 // 0, -1 // 0,
               (big(2)^100 + 1) // (big(2)^80 + 1),
               (big(2)^100 + 3) // (big(2)^81 + 5), big(2)^126 // 1,
               big(2)^500 // 3, 3 // big(2)^500]
    for a in values
        @test S.wide(-E(a)) == -a
        for b in values, op in (+, -, *, /, <, <=, >, >=, ==)
            @test H.outcome(() -> op(E(a), E(b))) == H.outcome(() -> op(a, b))
        end
    end
    # Cross cancellation can keep a result small when uncancelled products overflow.
    a = E(Q(big(2)^100, 3))
    b = E(Q(3, big(2)^100))
    @test S.is_small(a * b)
    @test S.wide(a * b) == 1
    @test S.is_small(a / a)
    @test S.wide(a / a) == 1
    a, b = E(Q(maximum)), E(Q(1))
    @test !S.is_small(a + b)
    @test S.wide(a + b) == maximum + 1
    # Direct small-storage exceptional endpoints also take the wide oracle path.
    for a in (Rational{Int128}(typemin(Int128)), Rational{Int128}(1, 0), Rational{Int128}(-1, 0)),
        b in (Rational{Int128}(1), Rational{Int128}(1, 0), Rational{Int128}(-1, 0)),
        op in (+, -, *, /, <, <=, >, >=, ==)
        @test H.outcome(() -> op(E(a), E(b))) == H.outcome(() -> op(Q(a), Q(b)))
    end

    H.overflow_work() # Exclude compilation from the allocation sample.
    Profile.Allocs.clear()
    Profile.Allocs.@profile sample_rate=1.0 H.overflow_work()
    allocations = Profile.Allocs.fetch()
    @test count(entry -> entry.type === OverflowError, allocations.allocs) == 0
    Profile.Allocs.clear()
end

@testset "Small exact helpers preserve cached activity and endpoint guards" begin
    H = _PresolveSmallExactTestTools
    S, E, Q, JS = H.S, H.S.E, H.Q, JSimplex
    for total in Q[0, 1, -1, 1 // 3, big(2)^126],
        term in (nothing, Q(0), Q(1), Q(-1), Q(1, 3)), unbounded in 0:2
        expected = JS._other_activity(total, unbounded, term, zero(Q))
        result = JS._other_activity(E(total), unbounded, isnothing(term) ? nothing : E(term), zero(E))
        @test isnothing(expected) ? isnothing(result) : !isnothing(result) && S.wide(result) == expected
    end
    cache = Vector{Union{Nothing,E}}(nothing, 3)
    bounds = [Bound(1.25), Bound{Float64}(nothing), Bound(-3.0)]
    @test S.wide(JS._cached_bound_rational!(cache, bounds, 1)) == Q(5, 4)
    @test JS._cached_bound_rational!(cache, bounds, 1) === cache[1]
    @test isnothing(JS._cached_bound_rational!(cache, bounds, 2))
    @test S.wide(JS._cached_bound_rational!(cache, bounds, 3)) == -3
    for T in (Float32, Float64, BigFloat), upper in (false, true), directed in (false, true)
        values = Q[1 // 3, -1 // 3, 1 // 10, -1 // 10, 0, 1, -1, big(2)^300 // 3]
        if T !== BigFloat
            append!(values, Q[Q(nextfloat(zero(T))) / 2, -Q(nextfloat(zero(T))) / 2,
                              2Q(floatmax(T)), -2Q(floatmax(T))])
        end
        for value in values
            expected = JS._propagation_bound(T, value, upper, directed)
            result = JS._propagation_bound(T, E(value), upper, directed)
            @test isnothing(expected) ? isnothing(result) : !isnothing(result) &&
                isequal(expected, (result[1], S.wide(result[2])))
        end
    end
end

@testset "Propagation arithmetic selection preserves model, history and worklists" begin
    H = _PresolveSmallExactTestTools
    JS, E, Q = JSimplex, H.S.E, H.Q
    for T in (Float32, Float64, BigFloat, Rational{BigInt}, Rational{Int}, Float16)
        @test JS._propagation_arithmetic(T) === (T in (Float32, Float64) ? E : Q)
        for A in (T[1 1; 2 -1], T[3 1; 0 1], T[-3 1; 1 0]), directed_bounds in (false, true)
            problem = LinearProblem(sparse(A), T[0, 1];
                row_lower=T[1, -1], row_upper=T[3, 2],
                column_lower=T[0, 0], column_upper=T[4, 4])
            @test all(H.propagation_pair(problem; directed_bounds))
            @test all(H.propagation_pair(problem; directed_bounds, rows=BitVector([true, false])))
        end
        for sign in (-1, 1)
            problem = LinearProblem(sparse(T[3 0; sign*3 sign]), zeros(T, 2);
                row_upper=sign == 1 ? [T(1), nothing] : T[1, -1],
                row_lower=sign == 1 ? [nothing, T(1)] : [nothing, nothing],
                column_lower=T[0, -1])
            @test all(H.propagation_pair(problem; rows=BitVector([true, false])))
        end
        contradictory = LinearProblem(sparse(T[1 1]), zeros(T, 2);
            row_lower=T[3], column_lower=T[0, 0], column_upper=T[1, 1])
        @test all(H.propagation_pair(contradictory))
        unbounded = LinearProblem(sparse(T[1 -1; 0 0]), zeros(T, 2);
            row_lower=[T(1), nothing], row_upper=[nothing, T(1)],
            column_lower=[nothing, T(0)], column_upper=[T(4), nothing])
        @test all(H.propagation_pair(unbounded))
        @test all(H.propagation_pair(unbounded; rows=falses(2)))
    end
    # Stored high-precision values remain exact under a lower working precision.
    problem, exact_stored = setprecision(BigFloat, 192) do
        value = BigFloat(1) / BigFloat(10)
        problem = LinearProblem(sparse(BigFloat[value 1; 1 -1]), BigFloat[0, 1];
            row_lower=BigFloat[1, -1], row_upper=BigFloat[3, 2],
            column_lower=BigFloat[0, 0], column_upper=BigFloat[4, 4])
        return problem, Q(value)
    end
    setprecision(BigFloat, 64) do
        @test all(H.propagation_pair(problem))
        @test JS._propagation_exact(Q, problem.A[1, 1]) == exact_stored
        @test H.S.wide(E(problem.A[1, 1])) == exact_stored
    end
    for T in (Float32, Float64)
        large = ldexp(one(T), 100)
        problem = LinearProblem(sparse(T[large -large; 1 1]), zeros(T, 2);
            row_lower=[nothing, T(1)], row_upper=T[1, 3],
            column_lower=T[0, 0], column_upper=T[2, 2])
        @test all(H.propagation_pair(problem))
    end
    old_subnormals = get_zero_subnormals()
    try
        set_zero_subnormals(true)
        for T in (Float32, Float64)
            @test JS._propagation_arithmetic(T) === Q
            problem = LinearProblem(sparse(T[3 1]), zeros(T, 2);
                row_upper=T[1], column_lower=T[0, 0])
            @test all(H.propagation_pair(problem))
        end
    finally
        set_zero_subnormals(old_subnormals)
    end
    old_rounding = Base.Rounding.rounding_raw(Float64)
    try
        for mode in (RoundDown, RoundUp, RoundToZero)
            Base.Rounding.setrounding_raw(Float64, Base.Rounding.to_fenv(mode))
            for T in (Float32, Float64)
                @test JS._propagation_arithmetic(T) === Q
                problem = LinearProblem(sparse(T[3 1]), zeros(T, 2);
                    row_upper=T[1], column_lower=T[0, 0])
                @test all(H.propagation_pair(problem))
            end
        end
    finally
        Base.Rounding.setrounding_raw(Float64, old_rounding)
    end
end
