from pathlib import Path
import json,itertools,sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
p=D/'fixtures.jl';s=p.read_text();(D/'fixtures.before-context-check.jl').write_text(s)
s=s.replace('arrays=(w.problem.A.colptr','arrays=((w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,w.progress.objective,w.progress.objective_constant),w.problem.A.colptr')
s=s.replace('x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b));@test same(x,y)','ambient=(precision(BigFloat),rounding(BigFloat));x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b));@test same(x,y);@test ambient==(precision(BigFloat),rounding(BigFloat))')
p.write_text(s);c.put('author-context-check.json',dict(Julia_executed=False,changes=['Include shared clock/offset/objective snapshot','Check exact ambient precision and rounding restoration after every pair'],before=c.sha(D/'fixtures.before-context-check.jl'),after=c.sha(p)))
contexts=[('BigFloat',f'BF{bits}_{mode}') for bits in [64,128,256] for mode in ['Nearest','Down','Up','ToZero','FromZero']]+[(t,t) for t in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
cells=[]
for typ,ctx in contexts:
 for n,density,shape,scope in itertools.product([16,64],['sparse','dense'],['positive','negative','mixed'] if typ=='BigFloat' else ['mixed'],['rows','feasible']):
  cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope=scope,variant='A',below=True,mode='valid',chain=8))
 for n,density,below,mode,shape in itertools.product([16,64],['sparse','dense'],[True,False],['valid','invalid','one_sided'],['positive','wide'] if typ=='Rational{BigInt}' else ['positive']):
  cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope='cert',variant='B',below=below,mode=mode,chain=8))
 for n,density,shape,chain,scope in itertools.product([8,16],['sparse','dense'],['positive','negative','mixed'] if typ=='BigFloat' else ['mixed'],[0,8,32],['growth','refresh','scheduled']):
  cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope=scope,variant='C',below=True,mode='valid',chain=chain))
for row in cells:row['id']='/'.join(str(row[k]) for k in ['context','n','density','shape','scope','variant','below','mode','chain'])
c.need(len(cells)==2636 and len({v['id'] for v in cells})==2636,'fixed grid')
c.put('expected-cases.json',cells)
with (D/'grid.toml').open('x') as f:
 for row in cells:
  f.write('[[cells]]\n')
  for k,v in row.items():f.write(k+' = '+('true' if v is True else 'false' if v is False else str(v) if type(v) is int else json.dumps(v))+'\n')
  f.write('\n')
source='''using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for arm in ("Reference","A","B","C");include(joinpath(@__DIR__,arm*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"));include(joinpath(@__DIR__,"extra-tests.jl"))
const CELLS=Any[];const PREP=Any[]
const GRID=TOML.parsefile(joinpath(@__DIR__,"grid.toml"))["cells"]
function cell(::Type{T},spec) where T
 n=spec["n"];density=Symbol(spec["density"]);shape=Symbol(spec["shape"]);scope=Symbol(spec["scope"]);arm=Symbol(spec["variant"]);below=spec["below"];mode=Symbol(spec["mode"]);chain=spec["chain"];id=spec["id"]
 f=@timed (fixture(T,n,density,shape,scope;below,mode,chain),fixture(T,n,density,shape,scope;below,mode,chain));a,b=f.value
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
 t=@timed begin;correctness(T);extra_correctness(T);end;push!(PREP,Dict("context"=>label,"correctness"=>cost(t)))
 g=@timed GC.gc();push!(PREP,Dict("context"=>label,"GC"=>cost(g)))
 for spec in GRID;spec["context"]==label&&cell(T,spec);end
end
try
 @testset "Sum rational growth whole-function comparison" begin
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
println("SUM_RATIONAL_GROWTH_COMPLETE cells=",length(CELLS));flush(stdout)
'''
(D/'driver.jl').write_text(source)
O=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27';cmd=c.read(str(O/'comparison-2/contract.json'))['command'][:];cmd[-2:]=[str(D/'driver.jl'),str(D/'output/results.toml')]
c.put('contract.json',dict(command=cmd,attempts=1,contexts=19,cases=len(cells),measured_windows=len(cells)*18,expected_exit=0,shared_limit_seconds=900,guard_limit_seconds=892,baseline=c.TARGET,ordinary_Test=True))
shutil.copyfile(__file__,D/'driver-prepare.py')
paths={n for n in c.read(str(O/'MASTER-run/pins.json'))['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in [c.M/'src',c.M/'test',D/'baseline']:paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print('sealed',len(paths),'pins',len(cells),'cells',len(cells)*18,'windows; noJulia')
