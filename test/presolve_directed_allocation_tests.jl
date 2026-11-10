using SparseArrays

directed_propagation_bytes(p) = @allocated JSimplex.propagate_row_bounds(p)

@testset "Directed bound conversion does not allocate a result box per endpoint" begin
    # Exactly representable endpoints isolate conversion/dispatch overhead from
    # newly admitted reductions. A boxed result for each of 256 endpoints adds
    # 8192 bytes; allow runtime variation without permitting that extra traffic.
    p=LinearProblem(sparse(repeat(collect(1:128),inner=2),collect(1:256),ones(256),128,256),
        zeros(256);row_upper=fill(64.0,128),column_lower=zeros(256))
    # Warm the measuring wrapper as well as the kernel, independently of which
    # other testsets ran first and which call sites they compiled.
    for _ in 1:3
        directed_propagation_bytes(p)
    end
    @test directed_propagation_bytes(p) <= 540_000
end
