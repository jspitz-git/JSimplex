using SparseArrays, LinearAlgebra

umfpack_reuse_measure(f, B) = @timed (JSimplex.refactorize!(f, B); nothing)
umfpack_fresh_measure(B) = @timed (JSimplex._factorize_basis(B); nothing)

@testset "Repeated UMFPACK refactorization reuses private LU storage" begin
    B = spdiagm(-1 => fill(-1.0, 63), 0 => fill(4.0, 64), 1 => fill(-1.0, 63))
    umfpack_fresh_measure(B)
    fresh = minimum(Base.gc_alloc_count(umfpack_fresh_measure(B).gcstats) for _ in 1:3)
    for Factor in (JSimplex.PFIFactorization, JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)
        f = Factor(B)
        for _ in 1:3
            umfpack_reuse_measure(f, B)
        end
        count = minimum(Base.gc_alloc_count(umfpack_reuse_measure(f, B).gcstats) for _ in 1:3)
        @test count <= fresh ÷ 2
        rhs = collect(1.0:64.0)
        @test B * JSimplex.forward_solve(f, rhs) ≈ rhs
        @test transpose(B) * JSimplex.transpose_solve(f, rhs) ≈ rhs
    end
end

const UMFPACK_REUSE_FACTORS = (JSimplex.PFIFactorization, JSimplex.ForrestTomlinFactorization,
    JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)

@testset "UMFPACK reuse handles changed values, structure and dimensions" begin
    patterns = ([4.0 1 0; 1 5 1; 0 1 6],
                [4.0 0 1; 1 5 1; 0 1 6], # Same nnz, different column pointers.
                [4.0 1 0; 0 5 1; 1 1 6]) # Same colptr as first, different rows.
    for Factor in UMFPACK_REUSE_FACTORS
        f = Factor(sparse(patterns[1]))
        for pass in 1:3, pattern in patterns
            B = sparse(pattern * pass)
            before = copy(B)
            JSimplex.refactorize!(f, B)
            rhs = [1.0, 2, 3]
            @test B * JSimplex.forward_solve(f, rhs) ≈ rhs
            @test transpose(B) * JSimplex.transpose_solve(f, rhs) ≈ rhs
            @test B == before
            # Subsequent LU reuse must not retain caller-owned CSC storage.
            fill!(B.nzval, 99.0)
            @test before * JSimplex.forward_solve(f, rhs) ≈ rhs
        end
        for n in (1, 0, 0, 8, 2, 0, 3)
            B = Matrix{Float64}(I, n, n) .* 2
            JSimplex.refactorize!(f, B)
            saved = JSimplex.copy_basis_factorization(f)
            @test JSimplex.forward_solve(f, ones(n)) == fill(0.5, n)
            @test JSimplex.transpose_solve(f, ones(n)) == fill(0.5, n)
            JSimplex.refactorize!(f, B .* 2)
            @test JSimplex.forward_solve(f, ones(n)) == fill(0.25, n)
            @test JSimplex.forward_solve(saved, ones(n)) == fill(0.5, n)
            @test JSimplex.transpose_solve(saved, ones(n)) == fill(0.5, n)
        end
    end
end

@testset "Failed candidate LU leaves active factor and saved copies usable" begin
    for Factor in UMFPACK_REUSE_FACTORS, shared in (false, true), changed_pattern in (false, true)
        B = sparse([4.0 1 0; 1 5 1; 0 1 6])
        f = Factor(B)
        JSimplex.refactorize!(f, B)
        JSimplex.refactorize!(f, B) # A private spare is available.
        tableau = [1.0, 0.25, 0]
        column = B * tableau
        JSimplex.replace_column!(f, tableau, 1)
        actual = Matrix(B)
        actual[:, 1] = column
        saved = shared ? JSimplex.copy_basis_factorization(f) : nothing
        rhs = [1.0, 2, 3]
        update_count = length(f.updates)
        failed = changed_pattern ? spzeros(3, 3) : copy(B)
        fill!(failed.nzval, 0.0)
        @test_throws SingularException JSimplex.refactorize!(f, failed)
        @test length(f.updates) == update_count
        @test actual * JSimplex.forward_solve(f, rhs) ≈ rhs
        @test transpose(actual) * JSimplex.transpose_solve(f, rhs) ≈ rhs
        @test_throws DimensionMismatch JSimplex.refactorize!(f, zeros(3, 4))
        @test actual * JSimplex.forward_solve(f, rhs) ≈ rhs
        # The failed candidate may contain incomplete symbolic/numeric data.
        # Recovery must start safely and support repeated reuse afterwards.
        for pass in 1:3
            replacement = sparse([5.0 0 1; 1 6 0; 0 1 7] .* pass)
            JSimplex.refactorize!(f, replacement)
            @test replacement * JSimplex.forward_solve(f, rhs) ≈ rhs
            @test transpose(replacement) * JSimplex.transpose_solve(f, rhs) ≈ rhs
            if shared
                @test actual * JSimplex.forward_solve(saved, rhs) ≈ rhs
                @test transpose(actual) * JSimplex.transpose_solve(saved, rhs) ≈ rhs
            end
        end
    end
end

@testset "LU slots stay isolated across branching factor copies and pivots" begin
    for Factor in UMFPACK_REUSE_FACTORS
        B = [4.0 1 0; 1 5 1; 0 1 6]
        f = Factor(sparse(B))
        JSimplex.refactorize!(f, sparse(B))
        JSimplex.refactorize!(f, sparse(B))
        factors = [f, JSimplex.copy_basis_factorization(f)]
        for _ in 1:3
            push!(factors, JSimplex.copy_basis_factorization(factors[end]))
        end
        bases = [copy(B) for _ in factors]
        rhs = [1.0, 2, 3]
        for step in 1:45
            target = mod1(step, length(factors))
            if step % 4 == 0
                source = mod1(target + 2, length(factors))
                factors[target] = JSimplex.copy_basis_factorization(factors[source])
                bases[target] = copy(bases[source])
            elseif step % 3 == 0
                row = mod1(step ÷ 3, 3)
                column = bases[target][:, row] + bases[target][:, mod1(row + 1, 3)] / 4
                tableau = JSimplex.forward_solve(factors[target], column)
                JSimplex.replace_column!(factors[target], tableau, row)
                bases[target][:, row] = column
            else
                B = [4.0 1 0; 1 5 1; 0 1 6] .* (1 + step / 16)
                if step % 2 == 0
                    B[1, 2] = 0
                    B[1, 3] = 1
                end
                JSimplex.refactorize!(factors[target], sparse(B))
                bases[target] = B
            end
            for i in eachindex(factors)
                @test bases[i] * JSimplex.forward_solve(factors[i], rhs) ≈ rhs
                @test transpose(bases[i]) * JSimplex.transpose_solve(factors[i], rhs) ≈ rhs
            end
        end
    end
end

@testset "Shared and private LU storage survives empty bases" begin
    for Factor in UMFPACK_REUSE_FACTORS, shared in (false, true)
        B = sparse([2.0 1; 0 3])
        f = Factor(B)
        JSimplex.refactorize!(f, B)
        saved = shared ? JSimplex.copy_basis_factorization(f) : nothing
        for _ in 1:3
            JSimplex.refactorize!(f, spzeros(0, 0))
            @test isempty(JSimplex.forward_solve(f, Float64[]))
            @test isempty(JSimplex.transpose_solve(f, Float64[]))
            JSimplex.refactorize!(f, sparse([4.0 0; 1 5]))
            @test [4.0 0; 1 5] * JSimplex.forward_solve(f, [1.0, 2]) ≈ [1.0, 2]
            if shared
                @test B * JSimplex.forward_solve(saved, [1.0, 2]) ≈ [1.0, 2]
                @test transpose(B) * JSimplex.transpose_solve(saved, [1.0, 2]) ≈ [1.0, 2]
            end
        end
    end
end
