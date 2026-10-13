using JSimplex.LinearAlgebra, JSimplex.SparseArrays

@testset "PFI eta payload dimensions and indirect indices remain checked" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}),
        transposed in (false, true)
        f = JSimplex.PFIFactorization(Matrix{T}(I, 3, 3))
        push!(f.updates, JSimplex.PackedEta{T}([1, 2], T[1], 1))
        solve! = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
        @test_throws DimensionMismatch solve!(zeros(T, 3), f, ones(T, 3))
        empty!(f.updates)
        push!(f.updates, JSimplex.PackedEta{T}([1], T[1, 2], 1))
        @test_throws DimensionMismatch solve!(zeros(T, 3), f, ones(T, 3))
        empty!(f.updates)
        for invalid in (0, 4)
            push!(f.updates, JSimplex.PackedEta{T}([1, invalid], T[1, 1], 1))
            @test_throws BoundsError solve!(zeros(T, 3), f, ones(T, 3))
            empty!(f.updates)
        end
        @test_throws DimensionMismatch solve!(zeros(T, 2), f, ones(T, 3))
        @test_throws DimensionMismatch solve!(zeros(T, 3), f, ones(T, 2))
        @test_throws ArgumentError solve!(f.work, f, ones(T, 3))
    end
end

# A scalar reference retains the original ordered eta operations. This checks
# exact floating-point equality, not only a normwise residual against fresh LU.
function pfi_ordered_reference!(out, f, rhs, transposed)
    T = eltype(out)
    if transposed
        work = copy(rhs)
        for eta in Iterators.reverse(f.updates)
            value = zero(T)
            for i in eachindex(eta.indices)
                value += eta.values[i] * work[eta.indices[i]]
            end
            work[eta.pivot_row] = value
        end
        JSimplex._backend_transpose_solve!(out, f.base, work)
    else
        JSimplex._backend_forward_solve!(out, f.base, rhs)
        for eta in f.updates
            pivot = out[eta.pivot_row]
            out[eta.pivot_row] = zero(T)
            for i in eachindex(eta.indices)
                out[eta.indices[i]] += pivot * eta.values[i]
            end
        end
    end
    out
end

@testset "PFI solve order across precisions, ownership and aliases" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}),
        backend in (:native, :markowitz)
        B = Matrix{T}(I, 4, 4)
        f = JSimplex.PFIFactorization(sparse(B), Val(backend))
        # Dyadic coefficients keep exact-type tests well inside Int arithmetic.
        for k in 1:4
            column = copy(B[:, k]); column[k] *= 2
            k < 4 && (column[k+1] += T(1 // 8))
            direction = JSimplex.forward_solve(f, column)
            JSimplex.replace_column!(f, direction, k; zero_tolerance=zero(T))
            B[:, k] = column
        end
        shared = JSimplex.copy_basis_factorization(f)
        for current in (f, shared), transposed in (false, true)
            solve! = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
            for rhs in (T[1, -2, 0, 3], T[0, 0, 0, 0])
                reference = pfi_ordered_reference!(similar(rhs), current, rhs, transposed)
                actual = similar(rhs); solve!(actual, current, rhs)
                @test isequal(actual, reference)
                alias = copy(rhs); solve!(alias, current, alias)
                @test isequal(alias, reference)
                copyto!(current.work, rhs); solve!(actual, current, current.work)
                @test isequal(actual, reference)
                solve!(actual, current, view(rhs, :))
                @test isequal(actual, reference)
                @test (transposed ? transpose(B) : B) * actual == rhs
            end
        end
        # A refactorization may recycle only unshared records.
        before = JSimplex.forward_solve(shared, ones(T, 4))
        JSimplex.refactorize!(f, sparse(B))
        JSimplex.replace_column!(f, T[1, 0, 0, 0], 1; zero_tolerance=zero(T))
        @test JSimplex.forward_solve(shared, ones(T, 4)) == before
    end
end

@testset "PFI cancellation and signed zeros retain scalar operation order" begin
    for T in (Float16, Float32, Float64, BigFloat), transposed in (false, true)
        f = JSimplex.PFIFactorization(Matrix{T}(I, 3, 3))
        large = T(4) / eps(one(T))
        push!(f.updates, JSimplex.PackedEta{T}([1,2,3], T[large,1,-large], 1))
        solve! = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
        for rhs in (ones(T,3), T[-0.0,0.0,-0.0])
            expected = pfi_ordered_reference!(similar(rhs), f, rhs, transposed)
            actual = similar(rhs); solve!(actual, f, rhs)
            @test isequal(actual, expected)
        end
    end
end
