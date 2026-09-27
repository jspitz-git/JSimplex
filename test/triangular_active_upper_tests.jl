using LinearAlgebra, SparseArrays
isdefined(@__MODULE__, :bg_replay_forward) || include("helpers/triangular_replay.jl")
@testset "Dense upper identity cache" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        f=Factor(Matrix{T}(I,7,7))
        rhs=T[0,-0.0,1,-2,3,4,5]
        @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
        available=hasproperty(f.row_cache,:active_upper)
        @test available
        available || continue
        @test isempty(f.row_cache.active_upper)
        @test !f.row_cache.upper_dirty
        B=Matrix{T}(I,7,7)
        for k in 1:20
            row=mod1(k,7)
            replacement=B[:,row]+B[:,mod1(row+2,7)]*T(1//8)
            JSimplex.replace_column!(f,JSimplex.forward_solve(f,replacement),row)
            B[:,row]=replacement
            @test f.row_cache.upper_dirty
            @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
            @test isequal(JSimplex.transpose_solve(f,rhs),bg_replay_transpose(f,rhs))
            @test !f.row_cache.upper_dirty
            @test issorted(f.row_cache.active_upper)
        end
        saved=JSimplex.copy_basis_factorization(f)
        @test saved.row_cache.upper_dirty
        @test isequal(JSimplex.forward_solve(saved,rhs),bg_replay_forward(saved,rhs))
        @test saved.row_cache.active_upper !== f.row_cache.active_upper
        @test_throws Exception JSimplex.refactorize!(f,zeros(T,7,7))
        @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
        JSimplex.refactorize!(f,Matrix{T}(I,7,7))
        @test isempty(f.row_cache.active_upper)
        @test !f.row_cache.upper_dirty
        # Simulate an upper mutation followed by a failed replacement: no new
        # history entry exists, and the sparse cache has never been built.
        @test isnothing(f.sparse)
        JSimplex._invalidate_sparse_upper!(f)
        pushfirst!(f.upper[2].indices,1)
        pushfirst!(f.upper[2].values,zero(T))
        f.upper[3].values[1]=-one(T)
        @test f.row_cache.upper_dirty
        special=T[Inf,-0.0,2,3,4,5,6]
        @test isequal(JSimplex.forward_solve(f,special),bg_replay_forward(f,special))
        @test isequal(JSimplex.transpose_solve(f,special),bg_replay_transpose(f,special))
        @test f.row_cache.active_upper==[2,3]
    end
end
