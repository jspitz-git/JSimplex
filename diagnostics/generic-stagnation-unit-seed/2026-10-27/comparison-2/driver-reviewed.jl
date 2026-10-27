using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for name in ("Reference","A","B","C","BC");include(joinpath(@__DIR__,name*".jl"));end
include(joinpath(@__DIR__,"fixtures-reviewed.jl"))
include(joinpath(@__DIR__,"extra-tests-reviewed.jl"))
include(joinpath(@__DIR__,"boundary-tests.jl"))
const CELLS=Dict{String,Any}[];const PREP=Dict{String,Any}[]
function onecell(::Type{T},label,n,m,scope,density,shape,arm) where T
 f=@timed (fixture(T,n,m,scope,density,shape),fixture(T,n,m,scope,density,shape));a,b=f.value;s=Val(scope)
 id=join((label,n,m,scope,density,shape,arm),"/");p=Dict("cell"=>id,"fixture"=>cost(f))
 cold=Dict{String,Any}[];warm=Dict{String,Any}[];resets=Dict{String,Any}[]
 for (method,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(cold,merge(timed(method,s,v),Dict("preparation_reset"=>cost(rt))));end
 for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(warm,merge(timed(method,s,v),Dict("preparation_reset"=>cost(rt))));end
 validation=@timed checkpair(a,b,arm);p["validation_and_snapshots"]=cost(validation)
 raw=Dict{String,Any}[]
 for pair in 1:9
  for method in (isodd(pair) ? (:original,arm) : (arm,:original))
   v=method===:original ? a : b;rt=@timed reset!(v);push!(resets,cost(rt));z=timed(Val(method),s,v)
   @test z["compile_seconds"]==z["recompile_seconds"]==0
   push!(raw,merge(Dict("pair"=>pair,"arm"=>string(method)),z))
  end
 end
 p["cold"]=cold;p["warm"]=warm;p["resets"]=resets;push!(PREP,p)
 push!(CELLS,Dict("id"=>id,"context"=>label,"type"=>string(T),"n"=>n,"rows"=>m,"scope"=>string(scope),"density"=>string(density),"shape"=>string(shape),"variant"=>string(arm),"windows"=>raw))
end
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 ct=@timed begin;correctness(T);extra_correctness(T);boundary_correctness(T);end;push!(PREP,merge(Dict("context"=>label,"phase"=>"correctness_and_snapshots"),cost(ct)))
 gc=@timed GC.gc();push!(PREP,merge(Dict("context"=>label,"phase"=>"context_GC"),cost(gc)))
 for n in (32,128),m in (8,32),scope in (:values,:observe,:observe_dual),density in (:sparse,:dense),shape in (T===BigFloat ? (:bounded,:unbounded,:free) : (:free,))
  onecell(T,label,n,m,scope,density,shape,:A)
 end
 for n in (8,32),m in (8,32),density in (:sparse,:dense),shape in (T in (BigFloat,Rational{BigInt}) ? (:positive,:negative,:mixed,:slack) : (:mixed,))
  onecell(T,label,n,m,:unit,density,shape,:B)
  for arm in (:B,:C,:BC);onecell(T,label,n,m,:init,density,shape,arm);end
 end
 for scope in (:observe_cold,:observe_same);onecell(T,label,32,8,scope,:sparse,:free,:A);end
 for scope in (:init_ready,);for arm in (:B,:C,:BC);onecell(T,label,32,8,scope,:sparse,:slack,arm);end;end
end
try
 @testset "Stagnation unit seed whole-function comparison" begin
  for bits in (64,128,256),mode in MODES
   setprecision(BigFloat,bits) do
    setrounding(BigFloat,mode) do;context(BigFloat,"BF$(bits)_$(mode)");end
   end
  end
  for T in (Float32,Float64,Rational{BigInt},Rational{Int64});context(T,string(T));end
 end
finally
 fields=("seconds","bytes","events","gc_seconds","compile_seconds","recompile_seconds")
 cv(x)=Any[x[k] for k in fields]
 cells=[merge(Dict(k=>v for (k,v) in c if k!="windows"),Dict("windows"=>[Any[w["pair"],w["arm"],cv(w)...,w["sink"]] for w in c["windows"]])) for c in CELLS]
 preparation=Dict{String,Any}[]
 for p in PREP
  if haskey(p,"phase");push!(preparation,Dict("context"=>p["context"],"phase"=>p["phase"],"cost"=>cv(p)))
  else
   push!(preparation,Dict("cell"=>p["cell"],"fixture"=>cv(p["fixture"]),"validation_and_snapshots"=>cv(p["validation_and_snapshots"]),"cold"=>[Any[cv(x)...,x["sink"],cv(x["preparation_reset"])...] for x in p["cold"]],"warm"=>[Any[cv(x)...,x["sink"],cv(x["preparation_reset"])...] for x in p["warm"]],"resets"=>[cv(x) for x in p["resets"]]))
  end
 end
 open(ARGS[1],"w") do io;TOML.print(io,Dict("cost_fields"=>collect(fields),"window_fields"=>["pair","arm",fields...,"sink"],"cells"=>cells,"preparation"=>preparation));end
end
println("STAGNATION_UNIT_SEED_COMPARISON_COMPLETE cells=",length(CELLS));flush(stdout)
