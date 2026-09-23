using LinearAlgebra

@testset "Update overflow is numerical and leaves reusable scratch" begin
    for mode in (:sparse,:dense,:auto)
        factor = JSimplex.PFIFactorization(Matrix{Float64}(I,4,4))
        JSimplex.replace_column!(factor,[1.0,1e300,0,0],1)
        rhs,dest = JSimplex.IndexedVector{Float64}(4),JSimplex.IndexedVector{Float64}(4)
        JSimplex.load_indexed!(rhs,[1e300,1.0,1.0,1.0])
        @test_throws OverflowError JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=mode)
        JSimplex.load_indexed!(rhs,[0.0,0.0,1.0,0.0])
        JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=mode)
        @test dest.values == rhs.values
        @test dest.indices == [3]
    end
end
