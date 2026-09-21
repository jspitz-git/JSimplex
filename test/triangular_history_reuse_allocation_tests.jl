using SparseArrays, LinearAlgebra

function triangular_history_batch!(f, column, count)
    for _ in 1:count
        JSimplex.replace_column!(f, column, 1)
    end
    return nothing
end

triangular_history_measure(f, column, count) = @timed triangular_history_batch!(f, column, count)

@testset "Triangular pivots reuse retired history buffers" begin
    for n in (1, 8), backend in (:native, :markowitz), Factor in
        (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)
        count = 32
        B = Matrix{Float64}(I, n, n)
        f = Factor(B, Val(backend))
        column = ones(n)
        for _ in 1:2
            triangular_history_batch!(f, column, count)
            JSimplex.refactorize!(f, B)
        end
        measured = triangular_history_measure(f, column, count)
        # Multirow pivots can still grow packed upper columns. Retired history
        # must remove the per-pivot vector allocation; the scalar case is zero.
        @test Base.gc_alloc_count(measured.gcstats) <= (n == 1 ? 0 : 8)
        @test measured.bytes <= (n == 1 ? 0 : 1024)
        expected = copy(B)
        expected[2:end, 1] .= count
        rhs = collect(1.0:n)
        @test expected * JSimplex.forward_solve(f, rhs) ≈ rhs
        @test transpose(expected) * JSimplex.transpose_solve(f, rhs) ≈ rhs
    end
end

const TRIANGULAR_HISTORY_FACTORS = (JSimplex.ForrestTomlinFactorization,
    JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)

function triangular_history_actual_pivot!(f, B::Matrix{T}, row, neighbor) where {T}
    column = B[:, row] + B[:, neighbor] .* (one(T) / T(4))
    tableau = JSimplex.forward_solve(f, column)
    JSimplex.replace_column!(f, tableau, row)
    B[:, row] = column
end

@testset "Triangular recycled histories isolate copied factors" begin
    for Factor in TRIANGULAR_HISTORY_FACTORS, backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        B = Matrix{T}(I, 4, 4)
        f = Factor(B, Val(backend))
        triangular_history_actual_pivot!(f, B, 1, 2)
        first_copy = JSimplex.copy_basis_factorization(f)
        first_basis = copy(B)
        triangular_history_actual_pivot!(f, B, 2, 3)
        second_copy = JSimplex.copy_basis_factorization(f)
        second_basis = copy(B)
        triangular_history_actual_pivot!(f, B, 3, 4)
        descendant = JSimplex.copy_basis_factorization(first_copy)
        factors = [f, first_copy, second_copy, descendant]
        bases = [B, first_basis, second_basis, copy(first_basis)]
        rhs = T[2, 3, 4, 5]
        for generation in 1:3, target in eachindex(factors)
            identity = Matrix{T}(I, 4, 4)
            JSimplex.refactorize!(factors[target], identity)
            bases[target] = identity
            for step in 1:3
                row = mod1(step + target + generation, 4)
                triangular_history_actual_pivot!(factors[target], bases[target], row, mod1(row + 1, 4))
                for index in eachindex(factors)
                    @test bases[index] * JSimplex.forward_solve(factors[index], rhs) ≈ rhs
                    @test transpose(bases[index]) * JSimplex.transpose_solve(factors[index], rhs) ≈ rhs
                end
            end
        end
    end
end

@testset "Triangular copied prefixes leave suffixes and retired pools reusable" begin
    for Factor in TRIANGULAR_HISTORY_FACTORS, backend in (:native, :markowitz)
        B = ones(1, 1)
        f = Factor(B, Val(backend))
        column = [2.0]
        JSimplex.replace_column!(f, column, 1)
        saved = JSimplex.copy_basis_factorization(f)
        JSimplex.replace_column!(f, column, 1)
        JSimplex.refactorize!(f, B)
        @test triangular_history_measure(f, column, 1).bytes == 0
        @test JSimplex.forward_solve(saved, [2.0]) == [1.0]
        @test JSimplex.transpose_solve(saved, [2.0]) == [1.0]
        JSimplex.refactorize!(f, B)
        # The original still owns its pool after copying an empty active history.
        other = JSimplex.copy_basis_factorization(f)
        JSimplex.replace_column!(other, [3.0], 1)
        @test triangular_history_measure(f, column, 1).bytes == 0
        @test JSimplex.forward_solve(other, [3.0]) == [1.0]
        @test JSimplex.transpose_solve(other, [3.0]) == [1.0]
    end
end

@testset "Triangular reused history handles changed dimensions and failed reset" begin
    for Factor in TRIANGULAR_HISTORY_FACTORS, backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        f = Factor(Matrix{T}(I, 4, 4), Val(backend))
        triangular_history_batch!(f, ones(T, 4), 4)
        for n in (4, 1, 0, 8, 2, 4)
            B = Matrix{T}(I, n, n)
            JSimplex.refactorize!(f, B)
            @test isempty(f.updates)
            @test JSimplex.forward_solve(f, ones(T, n)) == ones(T, n)
            @test JSimplex.transpose_solve(f, ones(T, n)) == ones(T, n)
            n == 0 && continue
            for (column, pivot, error) in ((zeros(T, n), 1, ZeroPivotException),
                                          (ones(T, n + 1), 1, DimensionMismatch),
                                          (ones(T, n), n + 1, BoundsError))
                @test_throws error JSimplex.replace_column!(f, column, pivot)
                @test JSimplex.forward_solve(f, ones(T, n)) == ones(T, n)
            end
            @test_throws ArgumentError JSimplex.replace_column!(f, ones(T, n), 1; zero_tolerance=-1)
            triangular_history_batch!(f, ones(T, n), 3)
            B[2:end, 1] .= T(3)
            saved = JSimplex.copy_basis_factorization(f)
            @test_throws SingularException JSimplex.refactorize!(f, zeros(T, n, n))
            @test B * JSimplex.forward_solve(f, ones(T, n)) ≈ ones(T, n)
            @test transpose(B) * JSimplex.transpose_solve(f, ones(T, n)) ≈ ones(T, n)
            JSimplex.refactorize!(f, Matrix{T}(I, n, n))
            triangular_history_batch!(f, fill(T(2), n), 2)
            @test B * JSimplex.forward_solve(saved, ones(T, n)) ≈ ones(T, n)
            @test transpose(B) * JSimplex.transpose_solve(saved, ones(T, n)) ≈ ones(T, n)
        end
    end
end

@testset "Triangular recycled history preserves mixed conversion and precision" begin
    for Factor in TRIANGULAR_HISTORY_FACTORS, backend in (:native, :markowitz)
        f = Factor(Matrix{Float32}(I, 3, 3), Val(backend))
        triangular_history_batch!(f, ones(Float32, 3), 3)
        JSimplex.refactorize!(f, Matrix{Float32}(I, 3, 3))
        JSimplex.replace_column!(f, [1e-100, 2.0, 4.0], 2)
        @test JSimplex.forward_solve(f, Float32[1, 2, 3]) ≈ Float32[1, 1, -1]
        @test JSimplex.transpose_solve(f, Float32[1, 2, 3]) ≈ Float32[1, -5, 3]
    end
    for Factor in TRIANGULAR_HISTORY_FACTORS
        f = setprecision(BigFloat, 512) do
            factor = Factor(Matrix{BigFloat}(I, 3, 3))
            triangular_history_batch!(factor, BigFloat[1, 1, 1], 3)
            factor
        end
        saved = JSimplex.copy_basis_factorization(f)
        before_forward = JSimplex.forward_solve(saved, BigFloat[1, 2, 3])
        before_transpose = JSimplex.transpose_solve(saved, BigFloat[1, 2, 3])
        setprecision(BigFloat, 64) do
            for _ in 1:3
                JSimplex.refactorize!(f, Matrix{BigFloat}(I, 3, 3))
                triangular_history_batch!(f, BigFloat[1, 1, 1], 3)
            end
        end
        @test JSimplex.forward_solve(saved, BigFloat[1, 2, 3]) == before_forward
        @test JSimplex.transpose_solve(saved, BigFloat[1, 2, 3]) == before_transpose
    end
end

function triangular_history_varied_batch!(f, column::Vector{T}, count) where {T}
    n = length(column)
    for step in 1:count
        row = mod1(step, n)
        fill!(column, zero(T))
        column[row] = one(T)
        column[mod1(row + 1, n)] = one(T) / T(4)
        JSimplex.replace_column!(f, column, row)
    end
    return nothing
end

@testset "Nonempty triangular histories reuse established coefficient capacity" begin
    for Factor in TRIANGULAR_HISTORY_FACTORS, backend in (:native, :markowitz)
        B = Matrix{Float64}(I, 4, 4)
        f = Factor(B, Val(backend))
        column = zeros(4)
        for _ in 1:3
            triangular_history_varied_batch!(f, column, 16)
            JSimplex.refactorize!(f, B)
        end
        @test (@allocated triangular_history_varied_batch!(f, column, 16)) == 0
        # Ensure the scenario exercises coefficient storage, not only empty records.
        if f isa JSimplex.BartelsGolubFactorization
            @test any(step -> !iszero(step.multiplier), Iterators.flatten(u.steps for u in f.updates))
        else
            @test any(u -> !isempty(u.multipliers), f.updates)
        end
        expected = copy(B)
        for step in 1:16
            row = mod1(step, 4)
            expected[:, row] += expected[:, mod1(row + 1, 4)] / 4
        end
        rhs = [1.0, 2, 3, 4]
        @test expected * JSimplex.forward_solve(f, rhs) ≈ rhs
        @test transpose(expected) * JSimplex.transpose_solve(f, rhs) ≈ rhs
    end
end
