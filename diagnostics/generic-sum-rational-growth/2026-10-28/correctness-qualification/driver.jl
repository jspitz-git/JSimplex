using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const PARENT=dirname(@__DIR__)
for arm in ("Reference","A","B","C");include(joinpath(PARENT,arm*".jl"));end
include(joinpath(PARENT,"fixtures-reviewed.jl"));include(joinpath(@__DIR__,"extra-corrected.jl"))
@testset "SRG corrected exact-decoder qualification" begin
 for bits in (64,128,256),(mode,name) in zip(MODES,("Nearest","Down","Up","ToZero","FromZero"))
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    println("CONTEXT BF",bits,"_",name);flush(stdout);correctness(BigFloat);extra_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64})
  println("CONTEXT ",T);flush(stdout);correctness(T);extra_correctness(T)
 end
end
println("SRG_CORRECTNESS_COMPLETE");flush(stdout)
