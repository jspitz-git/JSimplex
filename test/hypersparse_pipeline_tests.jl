using Test

@testset "Kernel mode uses hysteresis, occupancy, and valid costs" begin
    state = JSimplex.KernelModeState()
    choose(;k=1,n=1000,s=1.0,d=10.0) = JSimplex.choose_kernel_mode!(
        state;support_size=k,dimension=n,sparse_cost=s,dense_cost=d)
    @test choose(k=0,n=0) == :empty
    @test state.mode == :dense
    @test choose() == :dense
    @test choose() == :sparse
    @test choose(k=800) == :sparse
    @test choose() == :sparse
    @test choose(k=800) == :sparse
    @test choose(k=800) == :dense
    @test choose(k=150) == :dense
    @test choose() == :dense
    @test choose() == :sparse
    @test choose(s=20.0,d=1.0) == :sparse
    @test choose(s=20.0,d=1.0) == :dense
    @test choose(s=NaN,d=NaN) == :dense
    @test choose(s=NaN,d=NaN) == :sparse
    @test choose(k=0) == :empty
    @test_throws ArgumentError choose(k=-1)
    @test_throws ArgumentError choose(k=1001)
    @test_throws ArgumentError choose(n=-1)
    @test_throws ArgumentError JSimplex.KernelModeState(mode=:unknown)
    @test_throws ArgumentError JSimplex.KernelModeState(sparse_threshold=0.3,dense_threshold=0.2)
    @test_throws ArgumentError JSimplex.KernelModeState(dense_threshold=NaN)
end

@testset "Kernel costs retain total work and robust bounded samples" begin
    state = JSimplex.KernelModeState()
    for x in (NaN,Inf,-1.0,0.0)
        JSimplex.record_kernel_cost!(state,:sparse,x)
    end
    @test state.sparse_samples == 0
    @test isnan(JSimplex.kernel_cost(state,:sparse))
    for x in (100.0,2.0,3.0)
        JSimplex.record_kernel_cost!(state,:sparse,x)
    end
    @test state.sparse_samples == 3
    @test JSimplex.kernel_cost(state,:sparse) == 3.0
    @test state.sparse_total_seconds == 105.0
    JSimplex.record_kernel_cost!(state,:sparse,4.0)
    @test JSimplex.kernel_cost(state,:sparse) == 3.0
    @test state.sparse_total_seconds == 109.0
    for _ in 1:3
        JSimplex.record_kernel_cost!(state,:dense,5.0)
    end
    @test JSimplex.kernel_cost(state,:dense) == 5.0
    @test state.dense_total_seconds == 15.0
    @test_throws ArgumentError JSimplex.record_kernel_cost!(state,:empty,1.0)
    @test_throws ArgumentError JSimplex.kernel_cost(state,:unknown)
end
