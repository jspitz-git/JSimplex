using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for arm in ("Reference","A","B","C","BC");include(joinpath(@__DIR__,arm*".jl"));end
include(joinpath(@__DIR__,"fixtures-complete.jl"))
const CELLS=Any[];const PREP=Any[]
function cell(::Type{T},label,n,density,shape,scope,arm,phase=:end) where T
 id=join((label,n,density,shape,scope,arm,phase),"/")
 f=@timed (fixture(T,n,density,shape,scope,phase),fixture(T,n,density,shape,scope,phase));a,b=f.value
 p=Dict{String,Any}("cell"=>id,"fixture"=>cost(f));cold=Any[];warm=Any[];resets=Any[]
 for (tag,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(cold,Dict("cost"=>timed(tag,v),"reset"=>cost(rt)));end
 for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));rt=@timed reset!(v);push!(warm,Dict("cost"=>timed(tag,v),"reset"=>cost(rt)));end
 valid=@timed checkpair(a,b,arm);p["validation"]=cost(valid)
 rows=Any[]
 for pair in 1:9,tag in (isodd(pair) ? (:original,arm) : (arm,:original))
  v=tag===:original ? a : b;rt=@timed reset!(v);push!(resets,cost(rt));z=timed(Val(tag),v)
  @test z["compile_seconds"]==z["recompile_seconds"]==0
  push!(rows,merge(Dict("pair"=>pair,"arm"=>string(tag)),z))
 end
 p["cold"]=cold;p["warm"]=warm;p["resets"]=resets;push!(PREP,p)
 push!(CELLS,Dict("id"=>id,"type"=>string(T),"context"=>label,"n"=>n,"density"=>string(density),"shape"=>string(shape),"scope"=>string(scope),"variant"=>string(arm),"phase"=>string(phase),"windows"=>rows))
end
function context(::Type{T},label) where T
 println("CONTEXT ",label);flush(stdout)
 t=@timed correctness(T);push!(PREP,Dict("context"=>label,"correctness"=>cost(t)))
 g=@timed GC.gc();push!(PREP,Dict("context"=>label,"GC"=>cost(g)))
 shapes=T===BigFloat ? (:positive,:negative,:mixed) : (:mixed,)
 for n in (16,64),density in (:sparse,:dense),shape in shapes;cell(T,label,n,density,shape,:ratio,:A);end
 for arm in (:B,:C,:BC),phase in (:first,:ordinary,:end),shape in shapes;cell(T,label,16,:sparse,shape,:progress,arm,phase);end
 for arm in (:B,:C,:BC),n in (16,64),density in (:sparse,:dense),shape in shapes;cell(T,label,n,density,shape,:workspace,arm);end
end
try
 @testset "Ratio monitor whole-function comparison" begin
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
println("RATIO_MONITOR_COMPARISON_COMPLETE cells=",length(CELLS));flush(stdout)
