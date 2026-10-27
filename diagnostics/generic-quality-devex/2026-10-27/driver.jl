using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Threads.nthreads()==BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"reference.jl"));include(joinpath(@__DIR__,"candidate.jl"));include(joinpath(@__DIR__,"fixtures.jl"))
const CELLS=Dict{String,Any}[];const PREP=Dict{String,Any}[]
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 ct=@timed correctness(T);push!(PREP,merge(Dict("context"=>label,"phase"=>"correctness_and_snapshots"),cost(ct)))
 gc=@timed GC.gc();push!(PREP,merge(Dict("context"=>label,"phase"=>"context_GC"),cost(gc)))
 for n in (32,128),scope in scopes(T),density in (:sparse,:dense),pattern in (T===BigFloat ? (:positive,:negative,:mixed) : (:mixed,))
  f=@timed (fixture(T,n,scope,density,pattern),fixture(T,n,scope,density,pattern));a,b=f.value
  id=join((label,n,scope,density,pattern),"/");p=Dict("cell"=>id,"fixture"=>cost(f));s=Val(scope)
  cold=Dict{String,Any}[];warm=Dict{String,Any}[];resetcost=Dict{String,Any}[]
  for (m,v) in ((Val(:original),a),(Val(:candidate),b));reset!(v);push!(cold,timed(m,s,v));end
  for k in 1:3,(m,v) in ((Val(:original),a),(Val(:candidate),b));reset!(v);push!(warm,timed(m,s,v));end
  validation=@timed checkpair(a,b);p["validation_and_snapshots"]=cost(validation)
  raw=Dict{String,Any}[]
  for pair in 1:9
   for arm in (isodd(pair) ? (:original,:candidate) : (:candidate,:original))
    v=arm===:original ? a : b;t=@timed reset!(v);push!(resetcost,cost(t));r=timed(Val(arm),s,v)
    @test r["compile_seconds"]==r["recompile_seconds"]==0
    push!(raw,merge(Dict("pair"=>pair,"arm"=>string(arm)),r))
   end
  end
  p["cold"]=cold;p["warm"]=warm;p["resets"]=resetcost;push!(PREP,p)
  push!(CELLS,Dict("id"=>id,"context"=>label,"type"=>string(T),"n"=>n,"scope"=>string(scope),"density"=>string(density),"pattern"=>string(pattern),"windows"=>raw))
 end
end
@testset "Quality and Devex complete comparison" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;context(BigFloat,"BF$(bits)_$(mode)");end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});context(T,string(T));end
end
open(ARGS[1],"w") do io;TOML.print(io,Dict("cells"=>CELLS,"preparation"=>PREP));end
println("QUALITY_DEVEX_COMPARISON_COMPLETE cells=",length(CELLS));flush(stdout)
