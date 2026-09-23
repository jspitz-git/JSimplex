using LinearAlgebra,SparseArrays

@testset "Indexed update snapshots and refactorization lifecycle" begin
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        for kind in (:native,:markowitz)
            B = Matrix{Float64}(I,5,5)
            factor = Factor(sparse(B),Val(kind))
            @test isnothing(factor.sparse)
            rhs,dest = JSimplex.IndexedVector{Float64}(5),JSimplex.IndexedVector{Float64}(5)
            JSimplex.set_entry!(rhs,1,1.0)
            JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            cache = factor.sparse
            base = cache.base_view
            @test cache.base_builds == 1
            checkpoint = JSimplex.copy_basis_factorization(factor)
            @test checkpoint.sparse.work.values !== cache.work.values
            @test checkpoint.sparse.base_view.lower.matrix === base.lower.matrix
            @test checkpoint.sparse.base_view.lower.reach !== base.lower.reach
            JSimplex.replace_column!(factor,[1.0,2,0,0,0],1)
            B[:,1] = [1.0,2,0,0,0]
            JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            @test B*dest.values == rhs.values
            @test factor.sparse.base_view === base
            @test factor.sparse.base_builds == 1
            JSimplex.forward_solve!(dest,checkpoint,rhs;kernel_mode=:sparse)
            @test dest.values == rhs.values
            @test_throws SingularException JSimplex.refactorize!(factor,spzeros(5,5))
            @test factor.sparse === cache
            JSimplex.refactorize!(factor,sparse(B))
            @test isnothing(factor.sparse)
            JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            @test B*dest.values == rhs.values
            @test factor.sparse.base_view !== base
            JSimplex.forward_solve!(rhs,factor,rhs;kernel_mode=:sparse)
            @test B*rhs.values == [1.0,0,0,0,0]
            JSimplex.refactorize!(factor,spzeros(0,0))
            empty = JSimplex.IndexedVector{Float64}(0)
            @test isempty(JSimplex.forward_solve!(empty,factor,empty).indices)
            @test isempty(JSimplex.transpose_solve!(empty,factor,empty).indices)
        end
    end
end

@testset "Indexed update solves reject partial input aliases" begin
    factor = JSimplex.PFIFactorization(Matrix{Float64}(I,4,4))
    rhs = JSimplex.IndexedVector{Float64}(4)
    JSimplex.set_entry!(rhs,1,1.0)
    dest = JSimplex.IndexedVector(rhs.values,copy(rhs.indices),copy(rhs.membership),rhs.generation)
    @test_throws ArgumentError JSimplex.forward_solve!(dest,factor,rhs)
    dest = JSimplex.IndexedVector(copy(rhs.values),rhs.indices,copy(rhs.membership),rhs.generation)
    @test_throws ArgumentError JSimplex.transpose_solve!(dest,factor,rhs)
    dest = JSimplex.IndexedVector(copy(rhs.values),copy(rhs.indices),rhs.membership,rhs.generation)
    @test_throws ArgumentError JSimplex.forward_solve!(dest,factor,rhs)
    cache = factor.sparse
    @test_throws ArgumentError JSimplex.forward_solve!(cache.work,factor,rhs)
    @test_throws ArgumentError JSimplex.transpose_solve!(rhs,factor,cache.scratch)
    @test_throws ArgumentError JSimplex.forward_solve!(rhs,factor,rhs;kernel_mode=:unknown)
    @test_throws DimensionMismatch JSimplex.forward_solve!(JSimplex.IndexedVector{Float64}(3),factor,rhs)
end

@testset "Dense support created by the last row update reaches a dense base solve" begin
    factor = JSimplex.ForrestTomlinFactorization(Matrix{Float64}(I,4,4))
    # R maps [a,b,c,d] to [b,c,d,a+b+c+d], hence B=inv(R).
    push!(factor.updates,JSimplex.ForrestTomlinUpdate(1,[1,2,3],[1.0,1,1]))
    rhs,dest = JSimplex.IndexedVector{Float64}(4),JSimplex.IndexedVector{Float64}(4)
    JSimplex.set_entry!(rhs,4,1.0)
    JSimplex.transpose_solve!(dest,factor,rhs;kernel_mode=:auto)
    @test dest.values == ones(4)
    @test factor.sparse.dense_fallbacks > 0
    @test !factor.sparse.base_ready
end

@testset "Indexed Bartels-Golub handles a compressed rotation" begin
    for T in (Float64,Rational{BigInt})
        factor = JSimplex.BartelsGolubFactorization(Matrix{T}(I,8,8))
        tableau = [one(T);zeros(T,7)]
        JSimplex.replace_column!(factor,tableau,1)
        step = only(only(factor.updates).steps)
        @test step.swapped && step.last > step.row
        rhs,dest = JSimplex.IndexedVector{T}(8),JSimplex.IndexedVector{T}(8)
        for index in (1,3,8)
            JSimplex.clear!(rhs); JSimplex.set_entry!(rhs,index,one(T))
            JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
            @test dest.values == rhs.values
            JSimplex.transpose_solve!(dest,factor,rhs;kernel_mode=:sparse)
            @test dest.values == rhs.values
        end
    end
end
