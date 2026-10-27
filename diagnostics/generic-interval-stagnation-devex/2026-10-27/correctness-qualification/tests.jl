using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
for n in ("Reference","A","B","C");include(joinpath(@__DIR__,n*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
@testset "Corrected exact oracle and active precision qualification" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    high=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
    @test exactq(high)==((BigInt(1)<<300)+1)//(BigInt(1)<<300)
    @test exactq(setprecision(BigFloat,512) do;-high;end)==-((BigInt(1)<<300)+1)//(BigInt(1)<<300)
    correctness(BigFloat);boundary_correctness(BigFloat);mixed_precision_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);boundary_correctness(T);mixed_precision_correctness(T);end
end
println("ISD_CORRECTNESS_QUALIFICATION_COMPLETE");flush(stdout)
