using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for arm in ("Reference","A","B","C");include(joinpath(@__DIR__,arm*".jl"));end
include(joinpath(@__DIR__,"fixtures-final.jl"))
const CELLS=Any[];const PREP=Any[]
const GRID=TOML.parsefile(joinpath(@__DIR__,"grid.toml"))["cells"]
function cell(::Type{T},spec) where T
 arm=Symbol(spec["variant"]);id=spec["id"]
 make()=fixture(T,spec["n"],Symbol(spec["density"]),Symbol(spec["shape"]),Symbol(spec["scope"]);mode=Symbol(spec["mode"]),recycled=spec["recycled"],cap=spec["cap"])
 f=@timed (make(),make());a,b=f.value
 p=Dict{String,Any}("cell"=>id,"fixture"=>cost(f));cold=Any[];warm=Any[];resets=Any[]
 for (tag,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(cold,Dict("cost"=>timed(tag,v),"reset"=>cost(rt)));end
 for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(warm,Dict("cost"=>timed(tag,v),"reset"=>cost(rt)));end
 valid=@timed checkpair(a,b,arm);p["validation"]=cost(valid);rows=Any[]
 for pair in 1:9,tag in (isodd(pair) ? (:original,arm) : (arm,:original))
  v=tag===:original ? a : b;rt=@timed reset!(v);push!(resets,cost(rt));z=timed(Val(tag),v)
  @test z["compile_seconds"]==z["recompile_seconds"]==0
  push!(rows,merge(Dict("pair"=>pair,"arm"=>string(tag)),z))
 end
 finalcheck=@timed checkpair(a,b,arm);p["final_validation"]=cost(finalcheck)
 p["cold"]=cold;p["warm"]=warm;p["resets"]=resets;push!(PREP,p)
 push!(CELLS,merge(copy(spec),Dict("windows"=>rows)))
end
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 t=@timed correctness(T);push!(PREP,Dict("context"=>label,"correctness"=>cost(t)))
 g=@timed GC.gc();push!(PREP,Dict("context"=>label,"GC"=>cost(g)))
 for spec in GRID;spec["context"]==label&&cell(T,spec);end
end
try
 @testset "Residual pivot crash whole-function comparison" begin
  for bits in (64,128,256),(mode,name) in zip(MODES,("Nearest","Down","Up","ToZero","FromZero"))
   setprecision(BigFloat,bits) do
    setrounding(BigFloat,mode) do;context(BigFloat,"BF$(bits)_$(name)");end
   end
  end
  for T in (Float32,Float64,Rational{BigInt},Rational{Int64});context(T,string(T));end
 end
finally
 open(ARGS[1],"w") do io;TOML.print(io,Dict("cells"=>CELLS,"preparation"=>PREP));end
end
println("RESIDUAL_PIVOT_CRASH_COMPLETE cells=",length(CELLS));flush(stdout)
