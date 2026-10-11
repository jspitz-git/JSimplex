using Test, JSimplex, SparseArrays, LinearAlgebra

_hh_scratch_vectors(f) = (f.work, f.auxiliary, f.prepared_partial, f.prepared_direction)
_hh_scratch_capacity(f) = sum(length(getfield(v, :ref).mem) for v in _hh_scratch_vectors(f))
_hh_identity_basis(::Type{T}, n, scale=1) where {T} = spdiagm(0 => fill(T(scale), n))

@testset "HH dimension change releases obsolete solve scratch" begin
    large = 65_536
    f = JSimplex.HuangfuHallFactorization(_hh_identity_basis(Float64, large))
    saved = JSimplex.copy_basis_factorization(f)
    vectors = _hh_scratch_vectors(f)
    JSimplex.refactorize!(f, _hh_identity_basis(Float64, large, 2))
    @test all(a === b for (a, b) in zip(vectors, _hh_scratch_vectors(f)))
    for n in (4, 0)
        JSimplex.refactorize!(f, _hh_identity_basis(Float64, n, 2))
        @test _hh_scratch_capacity(f) == 4n
        @test JSimplex.forward_solve(f, ones(n)) == fill(0.5, n)
        @test JSimplex.transpose_solve(f, ones(n)) == fill(0.5, n)
    end
    @test JSimplex.forward_solve(saved, ones(large)) == ones(large)
end

@testset "HH scratch publication preserves scalar and failure contracts" begin
    for T in (Float16, Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt}),
        backend in (:native, :markowitz)
        @testset "$T/$backend" begin
            f = JSimplex.HuangfuHallFactorization(_hh_identity_basis(T, 12), Val(backend))
            saved = JSimplex.copy_basis_factorization(f)
            for n in (3, 7, 0, 5)
                JSimplex.refactorize!(f, _hh_identity_basis(T, n, 2))
                @test _hh_scratch_capacity(f) == 4n
                @test !f.prepared_valid
                rhs = ones(T, n)
                @test JSimplex.forward_solve(f, rhs) == fill(T(1)/T(2), n)
                @test JSimplex.transpose_solve(f, rhs) == fill(T(1)/T(2), n)
                vectors = _hh_scratch_vectors(f)
                JSimplex.refactorize!(f, _hh_identity_basis(T, n, 4))
                @test all(a === b for (a, b) in zip(vectors, _hh_scratch_vectors(f)))
            end
            # A failed new shape must also preserve a nonempty update history.
            new_column = zeros(T, 5); new_column[1] = T(8)
            direction = JSimplex.forward_solve(f, new_column)
            JSimplex.replace_column!(f, direction, 1)
            JSimplex.forward_solve(f, ones(T, 5))
            @test f.prepared_valid
            vectors = _hh_scratch_vectors(f)
            partial, direction = copy(f.prepared_partial), copy(f.prepared_direction)
            base, updates = f.base, copy(f.updates)
            @test_throws Exception JSimplex.refactorize!(f, spzeros(T, 2, 2))
            @test f.base === base && f.updates == updates
            @test all(a === b for (a, b) in zip(vectors, _hh_scratch_vectors(f)))
            @test f.prepared_valid
            @test f.prepared_partial == partial && f.prepared_direction == direction
            expected = fill(T(1)/T(4), 5); expected[1] = T(1)/T(8)
            @test JSimplex.forward_solve(f, ones(T, 5)) == expected
            @test JSimplex.forward_solve(saved, ones(T, 12)) == ones(T, 12)
        end
    end
end
