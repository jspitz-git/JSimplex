using SparseArrays, LinearAlgebra, Random

function bg_replay_forward(f, rhs)
    x = similar(rhs)
    JSimplex._backend_forward_solve!(x, f.base, rhs)
    for update in f.updates
        JSimplex._apply_row_update!(x, update)
    end
    JSimplex._upper_backsolve!(x, f.upper)
    out = similar(x)
    out[f.column_order] = x
    return out
end
function bg_replay_transpose(f, rhs)
    x = rhs[f.column_order]
    JSimplex._upper_transpose_solve!(x, f.upper)
    for update in Iterators.reverse(f.updates)
        JSimplex._apply_transposed_row_update!(x, update)
    end
    out = similar(x)
    JSimplex._backend_transpose_solve!(out, f.base, x)
    return out
end

@testset "BG composed permutations avoid numeric history work" begin
    n = 100
    f = JSimplex.BartelsGolubFactorization(spdiagm(0 => ones(n)))
    for row in 1:80
        direction = zeros(n); direction[row] = 1
        JSimplex.replace_column!(f, direction, row)
    end
    rhs = collect(1.0:n)
    @test JSimplex.forward_solve(f, rhs) == rhs
    @test JSimplex.transpose_solve(f, rhs) == rhs
    @test hasproperty(f, :row_cache)
    if hasproperty(f, :row_cache)
        @test length(f.row_cache.operations) == 0
        @test f.row_cache.update_count == 80
    end
end

@testset "BG composed history preserves the exact replay arithmetic" begin
    rng = MersenneTwister(7721)
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), backend in (:native, :markowitz)
        n = 9
        B = Matrix{T}(I, n, n)
        f = JSimplex.BartelsGolubFactorization(B, Val(backend))
        rhs = T.(rand(rng, -7:7, n))
        for k in 1:35
            row = mod1(k, n)
            replacement = copy(B[:,row])
            neighbor = mod1(row+1,n)
            replacement .+= B[:,neighbor] .* T(1//8)
            direction = JSimplex.forward_solve(f, replacement)
            JSimplex.replace_column!(f, direction, row)
            B[:,row] = replacement
            for (solve!, replay, matrix) in ((JSimplex.forward_solve!,bg_replay_forward,B),
                                            (JSimplex.transpose_solve!,bg_replay_transpose,transpose(B)))
                expected = replay(f,rhs)
                out = similar(rhs)
                @test isequal(solve!(out,f,rhs),expected)
                alias = copy(rhs)
                @test isequal(solve!(alias,f,alias),expected)
                copyto!(f.work,rhs)
                @test isequal(solve!(out,f,f.work),expected)
                @test isequal(solve!(f.spike,f,rhs),expected)
                @test matrix*out ≈ rhs
            end
            if k == 17
                saved = JSimplex.copy_basis_factorization(f)
                old = bg_replay_forward(saved,rhs)
                JSimplex.refactorize!(f,B)
                @test isequal(JSimplex.forward_solve(saved,rhs),old)
                @test isempty(f.row_cache.operations)
                @test f.row_cache.update_count == 0
            end
        end
        for n2 in (0,1,12,3)
            JSimplex.refactorize!(f,Matrix{T}(I,n2,n2))
            @test JSimplex.forward_solve(f,ones(T,n2)) == ones(T,n2)
            @test JSimplex.transpose_solve(f,ones(T,n2)) == ones(T,n2)
        end
    end
end
