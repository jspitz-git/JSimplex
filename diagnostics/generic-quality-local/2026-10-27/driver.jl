using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for name in ("Reference","CandidateA","CandidateB","CandidateAB","CandidateC");include(joinpath(@__DIR__,name*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
const CELLS=Dict{String,Any}[];const PREP=Dict{String,Any}[]
function onecell(::Type{T},label,n,scope,density,pattern,m,arm) where T
 f=@timed (fixture(T,n,scope,density,pattern,m),fixture(T,n,scope,density,pattern,m));a,b=f.value
 id=join((label,n,scope,density,pattern,m,arm),"/");p=Dict("cell"=>id,"fixture"=>cost(f));s=Val(scope)
 cold=Dict{String,Any}[];warm=Dict{String,Any}[];resetcost=Dict{String,Any}[]
 for (method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);push!(cold,timed(method,s,v));end
 for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);push!(warm,timed(method,s,v));end
 validation=@timed checkpair(a,b,arm);p["validation_and_snapshots"]=cost(validation)
 raw=Dict{String,Any}[]
 for pair in 1:9
  for method in (isodd(pair) ? (:original,arm) : (arm,:original))
   v=method===:original ? a : b;t=@timed reset!(v);push!(resetcost,cost(t));r=timed(Val(method),s,v)
   @test r["compile_seconds"]==r["recompile_seconds"]==0
   push!(raw,merge(Dict("pair"=>pair,"arm"=>string(method)),r))
  end
 end
 p["cold"]=cold;p["warm"]=warm;p["resets"]=resetcost;push!(PREP,p)
 push!(CELLS,Dict("id"=>id,"context"=>label,"type"=>string(T),"n"=>n,"scope"=>string(scope),"density"=>string(density),"pattern"=>string(pattern),"basis_rows"=>m,"variant"=>string(arm),"windows"=>raw))
end
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 ct=@timed correctness(T);push!(PREP,merge(Dict("context"=>label,"phase"=>"correctness_and_snapshots"),cost(ct)))
 gc=@timed GC.gc();push!(PREP,merge(Dict("context"=>label,"phase"=>"context_GC"),cost(gc)))
 patterns=T===BigFloat ? (:positive,:negative,:mixed,:zero) : (:mixed,)
 for n in (32,96),scope in (:quality,:quality_transposed),density in (:sparse,:dense),pattern in patterns,arm in (:A,:B,:AB)
  onecell(T,label,n,scope,density,pattern,0,arm)
 end
 if T<:AbstractFloat
  for n in (32,96),pattern in patterns;onecell(T,label,n,:finish,:vector,pattern,0,:B);end
 end
 for n in (32,96),m in (4,16),density in (:sparse,:dense),pattern in patterns
  onecell(T,label,n,:audit,density,pattern,m,:C)
 end
end
@testset "Local quality whole-function comparison" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;context(BigFloat,"BF$(bits)_$(mode)");end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});context(T,string(T));end
end
open(ARGS[1],"w") do io;TOML.print(io,Dict("cells"=>CELLS,"preparation"=>PREP));end
println("LOCAL_QUALITY_COMPARISON_COMPLETE cells=",length(CELLS));flush(stdout)
