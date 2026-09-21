using SparseArrays, LinearAlgebra

# Consume results as the iteration does, avoiding an escaping tuple in the probe.
function iteration_primal_ratio_probe(w, column)
    step, row, state = JSimplex._primal_ratio(w, 1, 1.0, column)
    return isnothing(step) ? -1.0 : step + row + Int(state)
end

@testset "PFI final buffers preserve ownership and numeric types" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}), mixed in (false, true)
        factor = JSimplex.PFIFactorization(spdiagm(0 => ones(T, 4)))
        column = mixed ? Rational{BigInt}[0, 2, -3, 0] : T[0, 2, -3, 0]
        original = copy(column)
        JSimplex.replace_column!(factor, column, 2)
        update = only(factor.updates)
        @test update.indices == [2, 3]
        @test update.values == T[1//2, 3//2]
        column[2] = 99
        @test update.values == T[1//2, 3//2]
        B = Matrix{T}(I, 4, 4)
        B[:, 2] = original
        rhs = T[1, 2, 3, 4]
        @test B * JSimplex.forward_solve(factor, rhs) ≈ rhs
        @test transpose(B) * JSimplex.transpose_solve(factor, rhs) ≈ rhs
    end
end
function iteration_dual_ratio_probe(w, column, violation)
    entering, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, column, 1.0, violation)
    return entering + length(flips) + exhausted
end
function iteration_pfi_probe(factor, column)
    JSimplex.replace_column!(factor, column, 1)
    return nothing
end

iteration_pfi_measure(f, c) = @timed iteration_pfi_probe(f, c)

@testset "PFI updates allocate only final owned vectors" begin
    factor = JSimplex.PFIFactorization(spdiagm(0 => ones(64)))
    sizehint!(factor.updates, 8)
    for column in (ones(64), [2.0; zeros(62); -3.0])
        iteration_pfi_measure(factor, column)
        measured = iteration_pfi_measure(factor, column)
        @test Base.gc_alloc_count(measured.gcstats) <= 4
        @test measured.bytes <= 16count(!iszero, column) + 128
    end
end

@testset "Ratio kernels avoid per-call temporary storage" begin
    p = LinearProblem(sparse([1.0;;]), [-1.0]; row_upper=[1.0])
    w = JSimplex.initialize_workspace(p, SolverOptions(; algorithm=:primal, verbose=false))
    column = [-1.0]
    iteration_primal_ratio_probe(w, column)
    @test (@allocated iteration_primal_ratio_probe(w, column)) == 0
    @test JSimplex._primal_ratio(w, 1, 1.0, column) == (1.0, 1, JSimplex.AT_UPPER)

    p = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[3.0], column_upper=[1.0, 4.0])
    w = JSimplex.initialize_workspace(p, SolverOptions(; verbose=false))
    column = [1.0, 1.0, 0.0]
    iteration_dual_ratio_probe(w, column, 3.0)
    @test (@allocated iteration_dual_ratio_probe(w, column, 3.0)) == 0
    entering, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, column, 1.0, 3.0)
    @test entering == 2 && flips == [1] && !exhausted
    # A retry with a smaller violation must discard the earlier pending flip.
    entering, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, column, 1.0, 0.5)
    @test entering == 1 && isempty(flips) && !exhausted
    before = copy(w.primal)
    entering, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, column, 1.0, 10.0)
    @test entering == -1 && flips == [1, 2] && exhausted
    @test w.primal == before
    # A finite bound range can overflow after the first flip was proposed.
    # Harris fallback must discard that partial list as well.
    w.lower[2] = Bound(-floatmax(Float64))
    w.upper[2] = Bound(floatmax(Float64))
    entering, flips, exhausted = JSimplex._bound_flipping_ratio_test(w, column, 1.0, 3.0)
    @test entering == 1 && isempty(flips) && !exhausted
    w.upper[1] = Bound{Float64}(nothing)
    w.upper[2] = Bound{Float64}(nothing)
    iteration_dual_ratio_probe(w, column, 3.0)
    @test (@allocated iteration_dual_ratio_probe(w, column, 3.0)) == 0
end

@testset "Primal optional steps preserve finite and unbounded cases" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        for (upper, expected) in ((nothing, nothing), (T(2), T(2)))
            p = LinearProblem(spzeros(T, 1, 1), T[-1]; column_upper=[upper])
            w = JSimplex.initialize_workspace(p, SolverOptions(T; algorithm=:primal, verbose=false))
            @test JSimplex._primal_ratio(w, 1, one(T), T[0]) == (expected, 0, JSimplex.BASIC)
        end
        p = LinearProblem(sparse(T[1; 2;;]), T[-1]; row_upper=T[1, 2])
        w = JSimplex.initialize_workspace(p, SolverOptions(T; algorithm=:primal, verbose=false))
        @test JSimplex._primal_ratio(w, 1, one(T), T[-1, -2]) == (one(T), 2, JSimplex.AT_UPPER)
    end
end
