using LinearAlgebra, SparseArrays

@testset "Triangular identity reset bounds retired capacity without growing small buffers" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}), stable in (false, true)
        upper = stable ? JSimplex._identity_upper(T, 4, Val(:stable)) : JSimplex._identity_upper(T, 4)
        indices(c) = stable ? c.indices.ids : c.indices
        # Include historical excess with only one active entry and an offset array.
        sizehint!(indices(upper[1]), 4096)
        sizehint!(upper[1].values, 4096)
        resize!(indices(upper[2]), 1024); resize!(upper[2].values, 1024)
        fill!(indices(upper[2]), 2); fill!(upper[2].values, T(2))
        popfirst!(indices(upper[2])); popfirst!(upper[2].values)
        sizehint!(indices(upper[3]), 64); sizehint!(upper[3].values, 64)
        small_indices = getfield(indices(upper[3]), :ref).mem
        small_values = getfield(upper[3].values, :ref).mem
        saved = JSimplex._copy_upper(upper)
        before = [(collect(c.indices), copy(c.values)) for c in saved]
        JSimplex._reset_identity_upper!(upper, 4)
        for (i,c) in enumerate(upper)
            @test collect(c.indices) == [i]
            @test c.values == T[1]
            @test length(getfield(indices(c), :ref).mem) <= 256
            @test length(getfield(c.values, :ref).mem) <= 256
        end
        @test getfield(indices(upper[3]), :ref).mem === small_indices
        @test getfield(upper[3].values, :ref).mem === small_values
        @test [(collect(c.indices), c.values) for c in saved] == before
        for n in (0, 7, 2)
            JSimplex._reset_identity_upper!(upper, n)
            @test [collect(c.indices) for c in upper] == [[i] for i in 1:n]
            @test all(c->c.values == T[1],upper)
        end
    end
end

@testset "Public triangular refactorization releases reserve and preserves saved solves" begin
    for backend in (:native, :markowitz), T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
        Factor in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        factor = Factor(Matrix{T}(I, 4, 4), Val(backend))
        ids = factor.upper[1].indices
        storage = ids isa JSimplex.UpperRowIndices ? ids.ids : ids
        sizehint!(storage, 4096); sizehint!(factor.upper[1].values, 4096)
        saved = JSimplex.copy_basis_factorization(factor)
        rhs = T[1,2,3,4]
        @test_throws ArgumentError JSimplex._refactorize_triangular!(factor, Matrix{T}(I,4,4), 0)
        @test JSimplex.forward_solve(factor,rhs) == rhs
        JSimplex.refactorize!(factor, T(2)*Matrix{T}(I,4,4))
        @test Base.summarysize(factor.upper) < 16_000
        @test JSimplex.forward_solve(factor,rhs) == rhs ./ T(2)
        @test JSimplex.transpose_solve(factor,rhs) == rhs ./ T(2)
        @test JSimplex.forward_solve(saved,rhs) == rhs
        @test JSimplex.transpose_solve(saved,rhs) == rhs
        replacement = T[2,1,1,1]
        JSimplex.replace_column!(factor,JSimplex.forward_solve(factor,replacement),1)
        B = T(2)*Matrix{T}(I,4,4);B[:,1]=replacement
        @test B*JSimplex.forward_solve(factor,rhs) ≈ rhs
        @test transpose(B)*JSimplex.transpose_solve(factor,rhs) ≈ rhs
    end
end

@testset "Retention thresholds leave active update growth unrestricted" begin
    for limit in (1,32,256,1024), stable in (false,true)
        upper=stable ? JSimplex._identity_upper(Float64,4096,Val(:stable)) : JSimplex._identity_upper(Float64,4096)
        JSimplex._packed_column!(upper[1],ones(4096))
        @test length(upper[1].values)==4096
        JSimplex._reset_identity_upper!(upper,4096,limit)
        @test upper[1].values==[1.0]
        @test length(upper[1].values.ref.mem)<=limit
    end
end
