using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for name in ("Reference","A","B","C");include(joinpath(@__DIR__,name*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
include(joinpath(@__DIR__,"extra-tests.jl"))
const CELLS=Dict{String,Any}[];const PREP=Dict{String,Any}[]
function onecell(::Type{T},label,n,m,scope,density,pattern) where T
 f=@timed (fixture(T,n,m,scope,density,pattern),fixture(T,n,m,scope,density,pattern));a,b=f.value
 arm=armfor(scope);s=Val(scope);id=join((label,n,m,scope,density,pattern),"/")
 p=Dict("cell"=>id,"fixture"=>cost(f));cold=Dict{String,Any}[];warm=Dict{String,Any}[];resetcost=Dict{String,Any}[];routecost=Dict{String,Any}[]
 for (method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);push!(cold,timed(method,s,v));end
 for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);push!(warm,timed(method,s,v));end
 v=@timed checkpair(a,b);p["validation_and_snapshots"]=cost(v);raw=Dict{String,Any}[]
 for pair in 1:9
  for method in (isodd(pair) ? (:original,arm) : (arm,:original))
   obj=method===:original ? a : b;rc=@timed reset!(obj);push!(resetcost,cost(rc));bc=@timed routebefore(obj)
   result=timed(Val(method),s,obj)
   @test result["compile_seconds"]==result["recompile_seconds"]==0
   ac=@timed checkroute(obj,bc.value);push!(routecost,Dict("before"=>cost(bc),"after"=>cost(ac)))
   push!(raw,merge(Dict("pair"=>pair,"arm"=>string(method)),result))
  end
 end
 p["cold"]=cold;p["warm"]=warm;p["resets"]=resetcost;p["route_checks"]=routecost;push!(PREP,p)
 route=scope in (:partial_hit,:partial_rebuild) ? (n+m>128 ? string(scope) : "full_fallback") : "none"
 push!(CELLS,Dict("id"=>id,"context"=>label,"type"=>string(T),"n"=>n,"basis_rows"=>m,"scope"=>string(scope),"density"=>string(density),"pattern"=>string(pattern),"variant"=>string(arm),"pool_route"=>route,"windows"=>raw))
end
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 ct=@timed begin;correctness(T);extra_correctness(T);end;push!(PREP,merge(Dict("context"=>label,"phase"=>"correctness_and_snapshots"),cost(ct)))
 gc=@timed GC.gc();push!(PREP,merge(Dict("context"=>label,"phase"=>"context_GC"),cost(gc)))
 for n in (32,128),m in (4,16),scope in (:audit,:virtual,:virtual_transposed,:pivot),density in (:sparse,:dense),pattern in (T===BigFloat ? (:positive,:negative,:mixed,:zero) : (:mixed,))
  onecell(T,label,n,m,scope,density,pattern)
 end
 for n in (32,128),scope in (:enter_dantzig,:enter_devex,:partial_hit,:partial_rebuild,:summary),density in (:sparse,:dense),pattern in (T===BigFloat ? (:positive,:negative,:mixed,:bound) : (:mixed,))
  onecell(T,label,n,4,scope,density,pattern)
 end
end
try
 @testset "Virtual free pivot whole-function comparison" begin
  for bits in (64,128,256),mode in MODES
   setprecision(BigFloat,bits) do
    setrounding(BigFloat,mode) do;context(BigFloat,"BF$(bits)_$(mode)");end
   end
  end
  for T in (Float32,Float64,Rational{BigInt},Rational{Int64});context(T,string(T));end
 end
finally
 open(ARGS[1],"w") do io;TOML.print(io,Dict("cells"=>CELLS,"preparation"=>PREP));end
end
println("VIRTUAL_FREE_PIVOT_COMPARISON_COMPLETE cells=",length(CELLS));flush(stdout)
