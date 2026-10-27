from pathlib import Path
import json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');O=D.parents[1]/'generic-residual-magnitudes/2026-10-26/measure'
s=(O/'driver.jl').read_text();a=s.index('function fixture(');b=s.index('function reset_fixture!',a)
ratio_fixture=s[a:b].replace('function fixture(','function ratio_fixture(')
p=D/'fixtures.jl'
p.write_text('''using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
fields(x)=Tuple(getfield(x,n) for n in fieldnames(typeof(x)))
function restore!(x,seed)
 for (i,n) in enumerate(fieldnames(typeof(x)));setfield!(x,n,seed[i]);end
 nothing
end
modof(::Val{:original})=RMReference
modof(::Val{:A})=RMA
modof(::Val{:B})=RMB
modof(::Val{:C})=RMC
modof(::Val{:BC})=RMBC
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
'''+ratio_fixture+'''
function monitorof(::Type{T},shape,phase) where T
 tol=T<:Rational ? zero(T) : T(1//128)
 m=J.StagnationMonitor{T}(4;tolerance=tol)
 objective=T(shape===:negative ? -2 : 2)
 ps=T(shape===:negative ? -1//1024 : 1//1024)
 ds=T(shape===:positive ? 1//1024 : -1//1024)
 m.initialized=phase!==:first;m.window_count=phase===:end ? 3 : phase===:ordinary ? 1 : 0
 m.best_objective=objective+one(T);m.best_primal=T(1//2);m.best_dual=T(1//4)
 m.start_objective=m.minimum_objective=objective+one(T)
 m.start_primal=m.minimum_primal=T(1//2);m.start_dual=m.minimum_dual=T(1//4)
 (m=m,seed=fields(m),values=(objective,T(1//4),T(1//8),ps,ds))
end
function fixture(::Type{T},n,density,shape,scope,phase=:end) where T
 if scope===:ratio
  v=ratio_fixture(T,n,:primal_ratio,density,shape)
  return merge(v,(scope=scope,))
 elseif scope===:progress
  return merge(monitorof(T,shape,phase),(scope=scope,))
 end
 A=zeros(T,n÷2,n)
 for j in 1:n,i in 1:n÷2
  (density===:dense||(i+j)%5==0)&&(A[i,j]=T((i+j)%7+1)/T(16))
 end
 p=LinearProblem(sparse(A),fill(T(1//8),n);column_lower=zeros(T,n),column_upper=fill(T(4),n),row_lower=fill(-T(8),n÷2),row_upper=fill(T(8),n÷2))
 opt=SolverOptions(T;algorithm=:dual,pricing=:devex,verbose=false)
 pol=J.NumericalPolicy(T;adaptive_stalling=true,stagnation_window=4,refactor_timing=false,solve_refinement=false,recovery=false)
 w=J.initialize_workspace(p,opt;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 w.iterations=1;J._observe_stagnation!(w,:dual,zero(T),zero(T));state=w.scratch.stagnation
 mon=monitorof(T,shape,:end);restore!(state.monitor,mon.seed)
 state.last_iteration=1;w.iterations=2
 (scope=scope,w=w,state=state,seed=fields(state),monseed=fields(state.monitor),steps=mon.values[4:5])
end
function reset!(v)
 if v.scope===:progress;restore!(v.m,v.seed)
 elseif v.scope===:workspace
  restore!(v.state,v.seed);restore!(v.state.monitor,v.monseed);v.w.scratch.stagnation=v.state;v.w.iterations=2
 end
 nothing
end
@noinline function whole(a::A,v::V) where {A,V}
 mod=modof(a)
 if v.scope===:ratio;return mod._primal_ratio(v.w,1,v.orientation,v.vector)
 elseif v.scope===:progress
  q=v.values;return mod.observe_progress!(v.m;objective=q[1],primal_violation=q[2],dual_violation=q[3],primal_step=q[4],dual_step=q[5])
 end
 mod._observe_stagnation!(v.w,:dual,v.steps[1],v.steps[2])
end
sink(x::Symbol)=x===:progress ? 1 : x===:watch ? 2 : 3
sink(x::Tuple)=100*x[2]+Int(x[3])+(isnothing(x[1]) ? -10000 : 1)
@noinline function runwhole(a::A,v::V) where {A,V}
 sink(whole(a,v))
end
function timed(a::A,v::V) where {A,V}
 t=@timed runwhole(a,v);merge(cost(t),Dict("sink"=>t.value))
end
function arrays(v)
 v.scope===:progress&&return ()
 w=v.w;A=w.problem.A
 q=(A.nzval,A.rowval,A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights)
 v.scope===:ratio ? (q...,v.vector) : q
end
snapshot(v)=(arrays(v),map(copy,arrays(v)),deepcopy(arrays(v)))
function intact(v,s)
 a=arrays(v);all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
end
output(v,x)=v.scope===:ratio ? x : v.scope===:progress ? (x,fields(v.m)) : (x,fields(v.state.monitor),v.state.last_iteration,v.state.cost_scale,v.state.value_scale)
function checkpair(a,b,arm)
 reset!(a);reset!(b);sa=snapshot(a);sb=snapshot(b);ctx=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test x[1]===y[1]
 @test x[1]===:value ? same(output(a,x[2]),output(b,y[2])) : same(x,y)
 @test intact(a,sa)&&intact(b,sb)
 @test ctx==(precision(BigFloat),rounding(BigFloat))
 if x[1]===:value&&a.scope===:ratio&&eltype(a.vector)===BigFloat&&!isnothing(x[2][1])
  z=whole(Val(arm),b);@test z[1]!==y[2][1]
 end
 x
end
function correctness(::Type{T}) where T
 @testset "Ratio and monitor parity $T" begin
  for density in (:sparse,:dense),shape in (:positive,:negative,:mixed,:ties,:unique)
   a=fixture(T,8,density,shape,:ratio);b=fixture(T,8,density,shape,:ratio)
   x=checkpair(a,b,:A);@test x[1]===:value&&x[2][2]>0&&x[2][1]>=0
  end
  for variant in (:zero,:negativezero,:short,:invalidbasis,:nan,:infinity,:rejected,:unbounded,:negative_step,:mixedprecision,:alias)
   a=fixture(T,8,:dense,:mixed,:ratio);b=fixture(T,8,:dense,:mixed,:ratio)
   for v in (a,b)
    w=v.w
    if variant===:zero;fill!(v.vector,zero(T))
    elseif variant===:negativezero;v.vector[1]=-zero(T)
    elseif variant===:short;empty!(w.lower)
    elseif variant===:invalidbasis;w.basis.basic_indices[end]=length(w.primal)+1
    elseif variant===:nan&&T<:AbstractFloat;v.vector[1]=T(NaN)
    elseif variant===:infinity&&T<:AbstractFloat;v.vector[1]=T(Inf)
    elseif variant===:rejected;push!(w.scratch.rejected_rows,1)
    elseif variant===:unbounded;fill!(w.lower,J._unbounded_bound(T));fill!(w.upper,J._unbounded_bound(T))
    elseif variant===:negative_step;w.primal[w.basis.basic_indices[1]]=T(9)
    elseif variant===:mixedprecision&&T===BigFloat;v.vector[1]=setprecision(()->BigFloat(3//7),BigFloat,512)
    elseif variant===:alias;w.primal[w.basis.basic_indices[1]]=v.vector[1]
    end
   end
   checkpair(a,b,:A)
  end
  # Independent known identity direction: positive step1, first row wins a tie.
  v=fixture(T,8,:dense,:positive,:ratio);x=whole(Val(:A),v)
  @test x[1]==1&&x[2]==1&&x[3]===J.AT_LOWER
  for arm in (:B,:C,:BC),shape in (:positive,:negative,:mixed),phase in (:first,:ordinary,:end)
   checkpair(fixture(T,8,:dense,shape,:progress,phase),fixture(T,8,:dense,shape,:progress,phase),arm)
   checkpair(fixture(T,8,:sparse,shape,:workspace),fixture(T,8,:sparse,shape,:workspace),arm)
  end
  for arm in (:B,:C,:BC),alg in (:all,:primal,:dual,:invalid),bad in (:none,:negative_primal,:nanstep,:infstep)
   a=monitorof(T,:positive,:end);b=monitorof(T,:positive,:end)
   q=a.values
   if bad===:negative_primal;q=(q[1],-one(T),q[3],q[4],q[5])
   elseif bad===:nanstep&&T<:AbstractFloat;q=(q[1],q[2],q[3],T(NaN),q[5])
   elseif bad===:infstep&&T<:AbstractFloat;q=(q[1],q[2],q[3],T(Inf),q[5])
   end
   ctx=(precision(BigFloat),rounding(BigFloat))
   call(mod,m)=mod.observe_progress!(m;algorithm=alg,objective=q[1],primal_violation=q[2],dual_violation=q[3],primal_step=q[4],dual_step=q[5])
   @test same(capture(()->call(RMReference,a.m)),capture(()->call(modof(Val(arm)),b.m)))
   @test same(fields(a.m),fields(b.m))
   @test ctx==(precision(BigFloat),rounding(BigFloat))
  end
  if T===BigFloat
   vals=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),-BigFloat(Inf),BigFloat(NaN),floatmin(BigFloat),floatmax(BigFloat),setprecision(()->BigFloat(-3//7),BigFloat,512),setprecision(()->BigFloat(3//7),BigFloat,512))
   for x in vals
    old=deepcopy(x);z=max(zero(T),x);v=RMA._primal_nonnegative_step(x)
    @test same(z,v);@test (z===x)==(v===x);@test same(x,old)
    if !(z===x);@test v!==RMA._primal_nonnegative_step(x);end
   end
   for x in vals,y in vals,s in (BigFloat(1),BigFloat(3//8))
    old=(deepcopy(x),deepcopy(y),deepcopy(s));a=capture(()->RMReference._stagnation_improvement(x,y,s));b=capture(()->RMC._stagnation_improvement(x,y,s))
    @test same(a,b);@test same((x,y,s),old)
    if a[1]===:value;@test (a[2]===x,a[2]===y,a[2]===s)==(b[2]===x,b[2]===y,b[2]===s);end
   end
   # Multi-window independent state transitions and fresh result owners.
   for mod in (RMReference,RMB,RMC,RMBC)
    m=J.StagnationMonitor{T}(2;tolerance=BigFloat(1//128))
    seq=Symbol[]
    for k in 1:4
     push!(seq,mod.observe_progress!(m;objective=BigFloat(1),primal_violation=BigFloat(0),dual_violation=BigFloat(0),primal_step=BigFloat(0),dual_step=BigFloat(0)))
    end
    @test seq==[:progress,:watch,:watch,:stalled]
   end
  end
 end
end
''')
(D/'driver.jl').write_text('''using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for arm in ("Reference","A","B","C","BC");include(joinpath(@__DIR__,arm*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
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
  push!(rows,merge(Dict("pair"=>pair,"arm"=>string(tag)),z)))
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
'''.replace('push!(rows,merge(Dict("pair"=>pair,"arm"=>string(tag)),z)))','push!(rows,merge(Dict("pair"=>pair,"arm"=>string(tag)),z))'))
shutil.copyfile(__file__,D/'driver-prepare.py')
print('fixtures driver prepared')
