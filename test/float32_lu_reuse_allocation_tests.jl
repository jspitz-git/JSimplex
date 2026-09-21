using SparseArrays, LinearAlgebra

const FLOAT32_REUSE_FACTORS = (JSimplex.PFIFactorization, JSimplex.ForrestTomlinFactorization,
    JSimplex.SuhlSuhlFactorization, JSimplex.BartelsGolubFactorization)

float32_lu_reset_measure(f, B) = @timed (JSimplex.refactorize!(f, B); nothing)

@testset "Float32 repeated LU refactorization allocates no storage" begin
    for Factor in FLOAT32_REUSE_FACTORS, make_matrix in (identity, sparse)
        B = make_matrix(Matrix{Float32}(I, 64, 64) .* 2)
        f = Factor(B)
        for _ in 1:3
            float32_lu_reset_measure(f, B)
        end
        samples = [float32_lu_reset_measure(f, B) for _ in 1:3]
        @test minimum(t.bytes for t in samples) == 0
        @test minimum(Base.gc_alloc_count(t.gcstats) for t in samples) == 0
        @test JSimplex.forward_solve(f, ones(Float32, 64)) == fill(0.5f0, 64)
        @test JSimplex.transpose_solve(f, ones(Float32, 64)) == fill(0.5f0, 64)
    end
end

function check_float32_reused_solves(f, B)
    rhs = Float32.(1:size(B, 1))
    expected = Float64.(B)
    @test JSimplex.forward_solve(f, rhs) ≈ expected \ Float64.(rhs) rtol=2e-5 atol=2e-5
    @test JSimplex.transpose_solve(f, rhs) ≈ transpose(expected) \ Float64.(rhs) rtol=2e-5 atol=2e-5
end

@testset "Float32 LU owns inputs across values, pivots and dimension changes" begin
    for Factor in FLOAT32_REUSE_FACTORS
        B = Float32[0 2 1; 4 1 0; 1 0 5]
        f = @inferred Factor(sparse(B))
        saved = JSimplex.copy_basis_factorization(f)
        for pass in 1:4
            replacement = B .* Float32(pass)
            input = isodd(pass) ? sparse(replacement) : copy(replacement)
            @test (@inferred JSimplex.refactorize!(f, input)) === f
            @test input == replacement
            fill!(input isa Matrix ? input : input.nzval, 99f0)
            check_float32_reused_solves(f, replacement)
            check_float32_reused_solves(saved, B)
        end
        for n in (0, 0, 1, 8, 2, 8, 0, 0, 8)
            replacement = Matrix{Float32}(I, n, n) .* 2
            JSimplex.refactorize!(f, replacement)
            check_float32_reused_solves(f, replacement)
            child = JSimplex.copy_basis_factorization(f)
            grandchild = JSimplex.copy_basis_factorization(child)
            JSimplex.refactorize!(child, replacement .* 3)
            JSimplex.refactorize!(f, sparse(replacement .* 4))
            check_float32_reused_solves(child, replacement .* 3)
            check_float32_reused_solves(f, replacement .* 4)
            check_float32_reused_solves(grandchild, replacement)
            check_float32_reused_solves(saved, B)
        end
    end
end

@testset "Float32 candidate failure preserves updated bases and copies" begin
    for Factor in FLOAT32_REUSE_FACTORS, warm in (false, true), shared in (false, true)
        B = Float32[4 1 0; 1 5 1; 0 1 6]
        f = Factor(sparse(B))
        if warm
            JSimplex.refactorize!(f, sparse(B))
            JSimplex.refactorize!(f, sparse(B))
        end
        tableau = Float32[1, 0.25, 0]
        actual = copy(B)
        actual[:, 1] = B * tableau
        JSimplex.replace_column!(f, tableau, 1)
        saved = shared ? JSimplex.copy_basis_factorization(f) : nothing
        for bad in (zeros(Float32, 3, 3), zeros(Float32, 4, 4))
            updates = length(f.updates)
            @test_throws SingularException JSimplex.refactorize!(f, sparse(bad))
            @test length(f.updates) == updates
            check_float32_reused_solves(f, actual)
            shared && check_float32_reused_solves(saved, actual)
        end
        @test_throws DimensionMismatch JSimplex.refactorize!(f, zeros(Float32, 2, 3))
        check_float32_reused_solves(f, actual)
        for pass in 1:4
            replacement = B .* Float32(pass)
            JSimplex.refactorize!(f, replacement)
            check_float32_reused_solves(f, replacement)
            shared && check_float32_reused_solves(saved, actual)
        end
        # A nonfinite same-size candidate fails after private storage exists.
        bad = copy(B)
        bad[1, 1] = NaN32
        @test_throws ArgumentError JSimplex.refactorize!(f, bad)
        check_float32_reused_solves(f, B .* 4)
        JSimplex.refactorize!(f, B)
        check_float32_reused_solves(f, B)
    end
end

@testset "Float32 LU copies stay isolated through mixed update histories" begin
    for Factor in FLOAT32_REUSE_FACTORS
        B = Float32[4 1 0; 1 5 1; 0 1 6]
        f = Factor(sparse(B))
        JSimplex.refactorize!(f, sparse(B))
        factors = [f, JSimplex.copy_basis_factorization(f)]
        matrices = [copy(B), copy(B)]
        for step in 1:48
            slot = mod1(step, length(factors))
            target = factors[slot]
            if step % 4 == 0
                copied = JSimplex.copy_basis_factorization(target)
                if length(factors) < 5
                    push!(factors, copied)
                    push!(matrices, copy(matrices[slot]))
                else
                    other = mod1(slot + 1, length(factors))
                    factors[other] = copied
                    matrices[other] = copy(matrices[slot])
                end
            elseif step % 3 == 0
                replacement = B .* Float32(1 + step % 5)
                JSimplex.refactorize!(target, sparse(replacement))
                matrices[slot] = replacement
            else
                pivot = mod1(step, 3)
                column = zeros(Float32, 3)
                column[pivot] = 1
                column[mod1(pivot + 1, 3)] = 0.125
                replacement = matrices[slot] * column
                JSimplex.replace_column!(target, column, pivot)
                matrices[slot][:, pivot] = replacement
            end
            for (branch, matrix) in zip(factors, matrices)
                check_float32_reused_solves(branch, matrix)
            end
        end
    end
end

float32_backend_reset_measure(b, B) = @timed (JSimplex._refactorize_backend(b, B); nothing)

@testset "Repeated empty Float32 bases preserve reusable nonempty capacity" begin
    B = Matrix{Float32}(I, 64, 64)
    empty = zeros(Float32, 0, 0)
    b = JSimplex._factorize_basis(B)
    for _ in 1:3
        float32_backend_reset_measure(b, B)
        float32_backend_reset_measure(b, empty)
        float32_backend_reset_measure(b, empty)
    end
    @test float32_backend_reset_measure(b, B).bytes == 0
    @test b.factorization \ ones(Float32, 64) == ones(Float32, 64)
end
