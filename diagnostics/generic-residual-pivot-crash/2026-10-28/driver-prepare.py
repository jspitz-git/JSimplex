from pathlib import Path
import sys,json,itertools,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures.jl').read_text().replace('old=RPCReference._pivot_magnitude(stored);new=RPCB._pivot_magnitude(stored)','before=deepcopy(stored);old=RPCReference._pivot_magnitude(stored);new=RPCB._pivot_magnitude(stored)').replace('@test same(stored,deepcopy(stored))','@test same(stored,before)')
# Broaden edge and ownership assertions before sealing, no Julia has run.
needle='  if T===BigFloat\n'
extra='''  if T<:AbstractFloat
   for bad in (T(Inf),T(-Inf),T(NaN))
    a=fixture(T,4,:dense,:mixed,:residual);b=fixture(T,4,:dense,:mixed,:residual);a.rho[2]=bad;b.rho[2]=bad
    @test checkpair(a,b,:A)[2]==T(Inf)
   end
   for tag in (Val(:original),Val(:A))
    a=fixture(T,4,:dense,:mixed,:residual);a.w.basis.basic_indices[2]=100
    @test_throws BoundsError whole(tag,a)
   end
  end
  for tag in (Val(:original),Val(:B))
   a=fixture(T,4,:dense,:mixed,:update;recycled=true);saved=(only(a.f.recycled_updates).indices,only(a.f.recycled_updates).values)
   whole(tag,a);@test only(a.f.updates).indices===saved[1];@test only(a.f.updates).values===saved[2]
  end
'''
c.need(s.count(needle)==1,'unique edge insertion');s=s.replace(needle,extra+needle)
s=s.replace('   for x in (BigFloat(0)', '''   for scope in (:residual,:crash)
    arm=scope===:residual ? :A : :C
    a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
    stored=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-53)+ldexp(BigFloat(1),-400);end
    if scope===:residual;a.rho[2]=stored;b.rho[2]=deepcopy(stored)
    else;a.column[2]=stored;b.column[2]=deepcopy(stored);end
    @test checkpair(a,b,arm)[1]===:value
   end
   for x in (BigFloat(0)''')
(D/'fixtures.jl').write_text(s)
contexts=[('BigFloat',f'BF{bits}_{mode}') for bits in (64,128,256) for mode in ('Nearest','Down','Up','ToZero','FromZero')]+[(v,v) for v in ['Float32','Float64','Rational{BigInt}','Rational{Int64}']]
cells=[]
for typ,ctx in contexts:
 shapes=['positive','negative','mixed'] if typ in ['BigFloat','Rational{BigInt}'] else ['mixed']
 if typ not in ['Rational{BigInt}','Rational{Int64}']:
  for n,density,shape,mode in itertools.product([16,64],['sparse','dense'],shapes,['structural','slack']):cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope='residual',variant='A',mode=mode,recycled=False,cap=8))
 for n,density,shape,recycled in itertools.product([16,32],['sparse','dense'],shapes,[False,True]):cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope='update',variant='B',mode='structural',recycled=recycled,cap=8))
 for n,density,shape,cap in itertools.product([32,128],['sparse','dense'],shapes,[1,8]):cells.append(dict(type=typ,context=ctx,n=n,density=density,shape=shape,scope='crash',variant='C',mode='structural',recycled=False,cap=cap))
for v in cells:v['id']='/'.join(str(v[k]) for k in ['context','scope','n','density','shape','mode','recycled','cap'])
c.need(len(cells)==len({v['id'] for v in cells}),'unique cells');c.put('expected-cases.json',cells)
with (D/'grid.toml').open('x') as out:
 for row in cells:
  out.write('[[cells]]\n')
  for k,v in row.items():out.write(k+' = '+('true' if v is True else 'false' if v is False else str(v) if type(v) is int else json.dumps(v))+'\n')
  out.write('\n')
source='''using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
for arm in ("Reference","A","B","C");include(joinpath(@__DIR__,arm*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
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
'''
(D/'driver.jl').write_text(source)
O=D.parents[1]/'generic-sum-rational-growth/2026-10-28';cmd=c.read(str(O/'contract-ready.json'))['command'][:];cmd[-2:]=[str(D/'driver.jl'),str(D/'output/results.toml')]
c.put('contract.json',dict(command=cmd,attempts=1,contexts=19,cases=len(cells),measured_windows=len(cells)*18,expected_exit=0,shared_limit_seconds=900,guard_limit_seconds=892,baseline=c.TARGET,ordinary_Test=True))
with (D/'progress.md').open('a') as out:out.write('Task1: sealed schedule '+str(len(cells))+'cells/'+str(len(cells)*18)+'windows. Ruling: update n16/32, residual n16/64, crash n32/128; backend/setup separately included to keep comparison short. Threewarm/ninealternatingpairs per cell; all controls and slower samples retained.\n')
shutil.copyfile(__file__,D/'driver-prepare.py')
paths={n for n in c.read(str(O/'MASTER-run/pins.json'))['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in [c.M/'src',c.M/'test',D/'baseline']:paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print('sealed',len(paths),'pins',len(cells),'cells',len(cells)*18,'windows; noJulia')
