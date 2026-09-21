using SparseArrays, LinearAlgebra

function triangular_refactorization_measure(factor, B)
    return @timed begin
        JSimplex.refactorize!(factor, B)
        nothing
    end
end

@testset "Triangular refactorization allocates only its new backend" for backend in (:native, :markowitz)
    B = spdiagm(0 => fill(2.0, 64))
    reference = JSimplex.PFIFactorization(B, Val(backend))
    triangular_refactorization_measure(reference, B)
    backend_allocations = minimum(Base.gc_alloc_count(triangular_refactorization_measure(reference, B).gcstats) for _ in 1:3)
    for Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        factor = Factor(B, Val(backend))
        # Exercise reset of a permuted, updated upper factor, not just identity.
        JSimplex.replace_column!(factor, ones(64), 1)
        triangular_refactorization_measure(factor, B)
        measured = minimum(Base.gc_alloc_count(triangular_refactorization_measure(factor, B).gcstats) for _ in 1:3)
        @test measured <= backend_allocations + 2
        @test JSimplex.forward_solve(factor, ones(64)) == fill(0.5, 64)
        @test JSimplex.transpose_solve(factor, ones(64)) == fill(0.5, 64)
    end
end

@testset "Triangular reset preserves copies and handles dimension changes" begin
    for backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        B = Matrix{T}(I, 3, 3)
        factor = Factor(B, Val(backend))
        replacement = T[2, 1, -1]
        JSimplex.replace_column!(factor, replacement, 1)
        B[:, 1] = replacement
        saved = JSimplex.copy_basis_factorization(factor)
        rhs = T[2, 3, 4]
        for n in (3, 1, 5, 0, 2)
            new_basis = Matrix{T}(I, n, n) .* T(2)
            original = copy(new_basis)
            JSimplex.refactorize!(factor, new_basis)
            @test new_basis == original
            @test isempty(factor.updates)
            @test factor.column_order == collect(1:n) && factor.positions == collect(1:n)
            @test JSimplex.forward_solve(factor, fill(T(2), n)) == ones(T, n)
            @test JSimplex.transpose_solve(factor, fill(T(2), n)) == ones(T, n)
            @test B * JSimplex.forward_solve(saved, rhs) ≈ rhs
            @test transpose(B) * JSimplex.transpose_solve(saved, rhs) ≈ rhs
            if n > 0
                # The reset factor must support another real basis update.
                column = fill(T(1), n)
                column[end] = T(2)
                tableau = JSimplex.forward_solve(factor, column)
                JSimplex.replace_column!(factor, tableau, n)
                new_basis[:, n] = column
                @test new_basis * JSimplex.forward_solve(factor, ones(T, n)) ≈ ones(T, n)
                @test transpose(new_basis) * JSimplex.transpose_solve(factor, ones(T, n)) ≈ ones(T, n)
                @test_throws SingularException JSimplex.refactorize!(factor, zeros(T, n, n))
                @test new_basis * JSimplex.forward_solve(factor, ones(T, n)) ≈ ones(T, n)
            end
        end
    end
end

@testset "Triangular identity reset uses current BigFloat precision without changing copies" begin
    for Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        factor, saved = setprecision(BigFloat, 512) do
            f = Factor(Matrix{BigFloat}(I, 2, 2))
            JSimplex.replace_column!(f, BigFloat[2, 1], 1)
            f, JSimplex.copy_basis_factorization(f)
        end
        before = deepcopy([c.values for c in saved.upper])
        setprecision(BigFloat, 64) do
            JSimplex.refactorize!(factor, Matrix{BigFloat}(I, 2, 2))
            @test all(precision(only(c.values)) == 64 for c in factor.upper)
            @test all(isone(only(c.values)) for c in factor.upper)
        end
        @test [c.values for c in saved.upper] == before
        @test all(precision(x) == 512 for c in saved.upper for x in c.values)
    end
end
