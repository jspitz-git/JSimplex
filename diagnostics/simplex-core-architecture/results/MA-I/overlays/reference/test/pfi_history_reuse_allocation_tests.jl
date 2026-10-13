using SparseArrays, LinearAlgebra

function pfi_history_update_measure(f, column)
    return @timed (JSimplex.replace_column!(f, column, 1); nothing)
end

@testset "PFI reuses retired eta storage after refactorization" begin
    for backend in (:native, :markowitz)
        B = spdiagm(0 => ones(64))
        f = JSimplex.PFIFactorization(B, Val(backend))
        column = ones(64)
        pfi_history_update_measure(f, column)
        JSimplex.refactorize!(f, B)
        pfi_history_update_measure(f, column)
        JSimplex.refactorize!(f, B)
        measured = pfi_history_update_measure(f, column)
        @test Base.gc_alloc_count(measured.gcstats) == 0
        @test measured.bytes == 0
        updated = Matrix(B)
        updated[:, 1] = column
        rhs = collect(1.0:64.0)
        @test updated * JSimplex.forward_solve(f, rhs) ≈ rhs
        @test transpose(updated) * JSimplex.transpose_solve(f, rhs) ≈ rhs
    end
end

function pfi_history_actual_pivot!(f, B, column)
    tableau = JSimplex.forward_solve(f, column)
    JSimplex.replace_column!(f, tableau, 1)
    B[:, 1] = column
end

@testset "PFI recycled histories isolate copies and copies of copies" begin
    for backend in (:native, :markowitz),
        T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        B = Matrix{T}(I, 4, 4)
        f = JSimplex.PFIFactorization(B, Val(backend))
        pfi_history_actual_pivot!(f, B, T[2, 1, -1, 3])
        first_copy = JSimplex.copy_basis_factorization(f)
        first_basis = copy(B)
        pfi_history_actual_pivot!(f, B, T[3, 2, -2, 4])
        second_copy = JSimplex.copy_basis_factorization(f)
        second_basis = copy(B)
        pfi_history_actual_pivot!(f, B, T[4, 3, -3, 5])
        descendant = JSimplex.copy_basis_factorization(first_copy)
        factors = [f, first_copy, second_copy, descendant]
        bases = [B, first_basis, second_basis, copy(first_basis)]
        rhs = T[2, 3, 4, 5]
        for generation in 1:3, target in eachindex(factors)
            identity = Matrix{T}(I, 4, 4)
            JSimplex.refactorize!(factors[target], identity)
            bases[target] = identity
            for step in 1:3
                column = T[2 + step, generation, -target, step]
                pfi_history_actual_pivot!(factors[target], bases[target], column)
                for index in eachindex(factors)
                    @test bases[index] * JSimplex.forward_solve(factors[index], rhs) ≈ rhs
                    @test transpose(bases[index]) * JSimplex.transpose_solve(factors[index], rhs) ≈ rhs
                end
            end
        end
    end
end

@testset "PFI retires only the unshared suffix" begin
    for backend in (:native, :markowitz)
        B = spdiagm(0 => ones(64))
        f = JSimplex.PFIFactorization(B, Val(backend))
        column = ones(64)
        JSimplex.replace_column!(f, column, 1)
        saved = JSimplex.copy_basis_factorization(f)
        # This second update was never shared and may be reused after reset.
        JSimplex.replace_column!(f, column, 1)
        JSimplex.refactorize!(f, B)
        measured = pfi_history_update_measure(f, column)
        @test measured.bytes == 0
        updated = Matrix(B)
        updated[:, 1] = column
        rhs = collect(1.0:64.0)
        @test updated * JSimplex.forward_solve(saved, rhs) ≈ rhs
        @test transpose(updated) * JSimplex.transpose_solve(saved, rhs) ≈ rhs
        # Copying must not transfer the source's already retired storage.
        JSimplex.refactorize!(f, B)
        empty_copy = JSimplex.copy_basis_factorization(f)
        JSimplex.replace_column!(empty_copy, fill(2.0, 64), 1)
        @test pfi_history_update_measure(f, column).bytes == 0
        updated[:, 1] .= 2.0
        @test updated * JSimplex.forward_solve(empty_copy, rhs) ≈ rhs
    end
end

@testset "PFI history reuse retains capacity through sparsity and dimension changes" begin
    for backend in (:native, :markowitz)
        B = spdiagm(0 => ones(64))
        f = JSimplex.PFIFactorization(B, Val(backend))
        dense_column = ones(64)
        sparse_column = [2.0; zeros(63)]
        pfi_history_update_measure(f, dense_column)
        JSimplex.refactorize!(f, B)
        @test pfi_history_update_measure(f, sparse_column).bytes == 0
        JSimplex.refactorize!(f, B)
        @test pfi_history_update_measure(f, dense_column).bytes == 0
        for n in (1, 0, 128, 2, 64)
            basis = spdiagm(0 => ones(n))
            JSimplex.refactorize!(f, basis)
            @test JSimplex.forward_solve(f, ones(n)) == ones(n)
            n == 0 && continue
            column = fill(2.0, n)
            JSimplex.replace_column!(f, column, 1)
            expected = Matrix(basis)
            expected[:, 1] = column
            rhs = collect(1.0:n)
            @test expected * JSimplex.forward_solve(f, rhs) ≈ rhs
            @test transpose(expected) * JSimplex.transpose_solve(f, rhs) ≈ rhs
        end
    end
end

@testset "PFI reuse preserves rejected updates and failed refactorizations" begin
    for backend in (:native, :markowitz), T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        B = Matrix{T}(I, 4, 4)
        f = JSimplex.PFIFactorization(B, Val(backend))
        JSimplex.replace_column!(f, T[2, 1, 0, -1], 1)
        JSimplex.refactorize!(f, B)
        for (column, pivot, error) in ((zeros(T, 4), 1, ZeroPivotException),
                                      (ones(T, 3), 1, DimensionMismatch),
                                      (ones(T, 4), 5, BoundsError))
            @test_throws error JSimplex.replace_column!(f, column, pivot)
            @test JSimplex.forward_solve(f, ones(T, 4)) == ones(T, 4)
        end
        @test_throws ArgumentError JSimplex.replace_column!(f, ones(T, 4), 1; zero_tolerance=-1)
        @test_throws InexactError JSimplex.replace_column!(f, Any[T(2), 1 + im, 0, 0], 1)
        @test JSimplex.forward_solve(f, ones(T, 4)) == ones(T, 4)
        pfi_history_actual_pivot!(f, B, T[2, 1, 0, -1])
        saved = JSimplex.copy_basis_factorization(f)
        @test_throws SingularException JSimplex.refactorize!(f, zeros(T, 4, 4))
        @test B * JSimplex.forward_solve(f, ones(T, 4)) ≈ ones(T, 4)
        @test transpose(B) * JSimplex.transpose_solve(f, ones(T, 4)) ≈ ones(T, 4)
        JSimplex.refactorize!(f, Matrix{T}(I, 4, 4))
        JSimplex.replace_column!(f, T[3, -1, 2, 1], 1)
        @test B * JSimplex.forward_solve(saved, ones(T, 4)) ≈ ones(T, 4)
    end
end

@testset "Reused PFI buffers preserve mixed conversion and BigFloat precision" begin
    for backend in (:native, :markowitz)
        f = JSimplex.PFIFactorization(Matrix{Float32}(I, 3, 3), Val(backend))
        JSimplex.replace_column!(f, ones(Float32, 3), 1)
        JSimplex.refactorize!(f, Matrix{Float32}(I, 3, 3))
        JSimplex.replace_column!(f, [1e-100, 2.0, 4.0], 2)
        @test only(f.updates).indices == [2, 3]
        @test only(f.updates).values == Float32[0.5, -2]
        @test JSimplex.forward_solve(f, Float32[1, 2, 3]) == Float32[1, 1, -1]
        @test JSimplex.transpose_solve(f, Float32[1, 2, 3]) == Float32[1, -5, 3]
    end
    f = setprecision(BigFloat, 512) do
        factor = JSimplex.PFIFactorization(Matrix{BigFloat}(I, 2, 2))
        JSimplex.replace_column!(factor, BigFloat[2, 1], 1)
        factor
    end
    saved = JSimplex.copy_basis_factorization(f)
    setprecision(BigFloat, 64) do
        JSimplex.refactorize!(f, Matrix{BigFloat}(I, 2, 2))
        JSimplex.replace_column!(f, BigFloat[2, 1], 1)
        JSimplex.refactorize!(f, Matrix{BigFloat}(I, 2, 2))
        JSimplex.replace_column!(f, BigFloat[4, 1], 1)
        @test all(precision(x) == 64 for x in only(f.updates).values)
    end
    @test all(precision(x) == 512 for x in only(saved.updates).values)
end
