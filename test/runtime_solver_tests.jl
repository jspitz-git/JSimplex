using SparseArrays, Random

@testset "Unlimited deadline checks preserve finite deadline behavior" begin
    now = time_ns()
    for start in (now, zero(UInt64), typemax(UInt64))
        @test !JSimplex.time_limit_reached(JSimplex.SolveContext(start, Inf))
    end
    @test JSimplex.time_limit_reached(JSimplex.SolveContext(now, 0.0))
    @test JSimplex.time_limit_reached(JSimplex.SolveContext(now, -0.0))
    @test JSimplex.time_limit_reached(JSimplex.SolveContext(now - UInt64(2_000_000_000), 1.0))
    @test !JSimplex.time_limit_reached(JSimplex.SolveContext(now, 1.0e6))
    # Preserve the comparison semantics even for directly constructed contexts.
    @test !JSimplex.time_limit_reached(JSimplex.SolveContext(now, NaN))
    @test JSimplex.time_limit_reached(JSimplex.SolveContext(now, -Inf))
end

# Independent allocating oracle: stable sortperm on breakpoint values, followed
# by the historical bound traversal. It also checks borrowed scratch ownership.
function runtime_reference_flips(w, row, orientation, violation)
    T = eltype(row)
    candidates = findall(i -> JSimplex._dual_pivot_eligible(w, i,
        orientation * row[i], JSimplex._dual_pivot_cutoff(T)), eachindex(row))
    fallback() = (JSimplex.dual_ratio_test(w, row, orientation), Int[], false)
    any(i -> isfinite(w.lower[i]) && isfinite(w.upper[i]), candidates) || return fallback()
    steps = [w.reduced_costs[i] / (orientation * row[i]) for i in candidates]
    any(x -> !isfinite(x) || x < zero(T), steps) && return fallback()
    flips = Int[]
    remaining = violation
    for position in sortperm(steps)
        i = candidates[position]
        state = w.basis.states[i]
        opposite = state == JSimplex.AT_LOWER ? w.upper[i] : w.lower[i]
        (state == JSimplex.FREE_NONBASIC || !isfinite(opposite)) && return i, flips, false
        width = bound_value(w.upper[i]) - bound_value(w.lower[i])
        gain = abs(row[i]) * width
        (!isfinite(width) || !isfinite(gain)) && return fallback()
        remaining <= gain + w.options.primal_tolerance && return i, flips, false
        push!(flips, i)
        remaining -= gain
    end
    return -1, flips, true
end

function runtime_ratio_fixture(::Type{T}, n=256) where T
    p = LinearProblem(sparse(ones(T, 1, n)), [T(mod(73i, 257) + 1) for i in 1:n];
        column_upper=ones(T, n))
    w = JSimplex.initialize_workspace(p, SolverOptions(T; verbose=false))
    row = [T(1 + mod(i, 5)) for i in 1:n+1]
    row[end] = zero(T)
    return w, row
end

@testset "Cached breakpoints preserve ties, orientations, and Harris fallbacks" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        w, row = runtime_ratio_fixture(T, 16)
        rng = MersenneTwister(97)
        for iteration in 1:24
            orientation = isodd(iteration) ? one(T) : -one(T)
            for i in 1:16
                w.basis.states[i] = rand(rng, (JSimplex.AT_LOWER, JSimplex.AT_UPPER))
                sign = w.basis.states[i] == JSimplex.AT_LOWER ? one(T) : -one(T)
                row[i] = orientation * sign * T(rand(rng, 1:4))
                w.reduced_costs[i] = sign * T(rand(rng, 0:4))
                w.upper[i] = w.basis.states[i] == JSimplex.AT_LOWER &&
                    iteration % 3 == 0 && i % 4 == 0 ? Bound{T}(nothing) : Bound(T(1))
            end
            iteration % 5 == 0 && (w.reduced_costs[1] = -w.reduced_costs[1])
            violation = T(rand(rng, 1:40))
            expected = runtime_reference_flips(w, row, orientation, violation)
            actual = JSimplex._bound_flipping_ratio_test(w, row, orientation, violation)
            @test isequal(actual, expected)
        end
        fill!(w.reduced_costs, zero(T))
        fill!(row, one(T))
        fill!(w.basis.states, JSimplex.AT_LOWER)
        w.basis.states[end] = JSimplex.BASIC
        fill!(w.upper, Bound(one(T)))
        @test JSimplex._bound_flipping_ratio_test(w, row, one(T), T(3)) == (3, [1, 2], false)
        # A second call must rebuild keys from changed prices and orientation.
        w.reduced_costs[1] = T(7)
        expected = runtime_reference_flips(w, row, one(T), T(3))
        @test isequal(JSimplex._bound_flipping_ratio_test(w, row, one(T), T(3)), expected)
        if T <: AbstractFloat
            for value in (T(-0.0), T(Inf), T(NaN))
                w.reduced_costs[2] = value
                expected = runtime_reference_flips(w, row, one(T), T(3))
                @test isequal(JSimplex._bound_flipping_ratio_test(w, row, one(T), T(3)), expected)
            end
        end
    end
end

function runtime_ratio_probe(w, row)
    index, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, row,
        one(eltype(row)), eltype(row)(1_000_000))
    return index + length(flips) + exhausted
end

@testset "Breakpoint keys respect the current BigFloat precision on every call" begin
    w, row = setprecision(BigFloat, 512) do
        w, row = runtime_ratio_fixture(BigFloat, 16)
        w.reduced_costs[1] = BigFloat(1) + BigFloat(2)^(-300)
        w.reduced_costs[2] = BigFloat(1)
        row[1] = row[2] = BigFloat(1)
        return w, row
    end
    original_costs, original_row = copy(w.reduced_costs), copy(row)
    for bits in (64, 512, 128, 256)
        setprecision(BigFloat, bits) do
            expected = runtime_reference_flips(w, row, one(BigFloat), BigFloat(3))
            actual = JSimplex._bound_flipping_ratio_test(w, row, one(BigFloat), BigFloat(3))
            @test isequal(actual, expected)
            @test isequal(w.reduced_costs, original_costs)
            @test isequal(row, original_row)
            @test precision(w.reduced_costs[1]) == 512
        end
    end
end

@testset "Ratio sorting does not repeatedly rebuild exact breakpoint values" begin
    for (T, budget) in ((BigFloat, 800_000), (Rational{BigInt}, 3_000_000))
        w, row = runtime_ratio_fixture(T)
        runtime_ratio_probe(w, row)
        @test (@allocated runtime_ratio_probe(w, row)) <= budget
    end
end
