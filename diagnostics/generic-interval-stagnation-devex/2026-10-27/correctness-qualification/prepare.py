from pathlib import Path
import json,sys,shutil,re,collections
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');P=D/'comparison-2';Q=D/'correctness-qualification';sys.path.insert(0,str(D));import common as c
p=json.loads((P/'output/process.json').read_text());extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(set(c.read('host-seed.json')['groups'])|set(extra));h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R);c.put('measurement-terminal-host.json',h);c.unchanged()
log=(P/'output/run.log').read_text();counts=collections.Counter(int(v) for v in re.findall(r'Test Failed at .*fixtures.jl:(\d+)',log));c.need(dict(counts)=={127:60,248:60,249:60,251:60,252:120} and p['returncode']==1 and p['pins_unchanged'] is True,'only exact diagnosed oracle failures')
c.put('measurement-rejection.json',dict(accepted=False,passed=55982,failed=360,errors=0,locations=dict(counts),reason='Ambient-precision Rational conversion oracle and post-restoration B precision/owner assumptions; no candidate disagreement',bindings={str(P/n):c.sha(P/n) for n in ['output/run.log','output/process.json','output/results.toml','pins.json','fixtures.jl']}))
Q.mkdir()
for n in ['Reference.jl','A.jl','B.jl','C.jl','common.py','environment.json','protected-before.json']:shutil.copyfile(P/n,Q/n)
for n in ['host-before.json','host-seed.json']:(Q/n).write_text(json.dumps(h,indent=2,sort_keys=True)+'\n')
s=(P/'fixtures.jl').read_text()
# Exact integer reconstruction of stored dyadic bits, without rounded ldexp.
marker='function exact_enclosure(mod,a,b,op)'
exact='''exactq(x::Rational)=Rational{BigInt}(x)
function exactq(x::AbstractFloat)
    isfinite(x)||throw(ArgumentError("nonfinite exact input"))
    n,p,d=Base.decompose(x)
    p>=0 ? (BigInt(n)<<p)//BigInt(d) : BigInt(n)//(BigInt(d)<<(-p))
end
'''
s=s.replace(marker,exact+marker).replace('Rational{BigInt}(a)+Rational{BigInt}(b)','exactq(a)+exactq(b)').replace('Rational{BigInt}(a)*Rational{BigInt}(b)','exactq(a)*exactq(b)').replace('Rational{BigInt}.(a.p.A)','exactq.(a.p.A)').replace('Rational{BigInt}.(a.x)','exactq.(a.x)').replace('Rational{BigInt}.(a.p.objective)','exactq.(a.p.objective)').replace('Rational{BigInt}.(a.y)','exactq.(a.y)')
s=s.replace('for a in (high,-high),b in','for a in (high,-high,setprecision(BigFloat,512) do;-high;end),b in')
old='''   @test precision(sx.cost_scale)==precision(sy.cost_scale)==precision(BigFloat)
   @test precision(sx.value_scale)==precision(sy.value_scale)==precision(BigFloat)
   for (v,s) in ((a,sx),(b,sy))
    @test s.cost_scale!==v.w.costs[1]
    @test s.value_scale!==v.w.primal[1]&&s.value_scale!==v.w.upper[1].value&&s.value_scale!==v.w.lower[1].value
   end'''
new='''   active_bits=scope===:new ? precision(BigFloat) : 512
   @test precision(sx.cost_scale)==precision(sy.cost_scale)==active_bits
   @test precision(sx.value_scale)==precision(sy.value_scale)==active_bits
   for (v,s) in ((a,sx),(b,sy))
    @test (s.cost_scale===v.w.costs[1])==(scope!==:new&&sg==1)
    @test (s.value_scale===v.w.upper[1].value)==(scope!==:new)
    @test s.value_scale!==v.w.primal[1]&&s.value_scale!==v.w.lower[1].value
   end'''
c.need(s.count(old)==1,'one source-derived owner expectation correction');s=s.replace(old,new)
(Q/'fixtures.jl').write_text(s)
(Q/'tests.jl').write_text('''using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
for n in ("Reference","A","B","C");include(joinpath(@__DIR__,n*".jl"));end
include(joinpath(@__DIR__,"fixtures.jl"))
@testset "Corrected exact oracle and active precision qualification" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    high=setprecision(BigFloat,512) do;BigFloat(1)+ldexp(BigFloat(1),-300);end
    @test exactq(high)==((BigInt(1)<<300)+1)//(BigInt(1)<<300)
    @test exactq(setprecision(BigFloat,512) do;-high;end)==-((BigInt(1)<<300)+1)//(BigInt(1)<<300)
    correctness(BigFloat);boundary_correctness(BigFloat);mixed_precision_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);boundary_correctness(T);mixed_precision_correctness(T);end
end
println("ISD_CORRECTNESS_QUALIFICATION_COMPLETE");flush(stdout)
''')
co=json.loads((P/'contract.json').read_text());co['command']=[v.replace(str(P/'driver.jl'),str(Q/'tests.jl')) for v in co['command'][:-1]];co.update(cases=0,measured_windows=0,expected_exit=0,qualification_only=True);(Q/'contract.json').write_text(json.dumps(co,indent=2,sort_keys=True)+'\n')
shutil.copytree(P/'guard',Q/'guard',ignore=shutil.ignore_patterns('__pycache__'));shutil.copyfile(P/'launch.py',Q/'launch.py')
(Q/'RULING.md').write_text('Original measured run remains rejected55982/360; all32634timing windows and1813whole-call validations retained. Correct only independently diagnosed oracle: Base.decompose raw stored bits avoids ambient-rounded Rational{BigInt}(BigFloat) ldexp; monitor whole observes under stored512 recovery precision and restores caller context, so preserve actual512 owner-sharing rather than require outsideprecision. All validoldexpectations/source/grid/window bodies untouched; add negative512 and exactdecoderknown-binary checks. Qualify allcorrectness again inonefreshordinaryTest process, NOcost remeasurement. Separatepostexitmeasurement reconciliation may accept cost records only with independentqualification+allrawchecks; originalfailedrunneverretroactivelypasses.\n')
shutil.copyfile(__file__,Q/'prepare.py')
paths=set(json.loads((P/'pins.json').read_text())['files']);paths.update(str(p) for p in Q.rglob('*') if p.is_file() and '__pycache__' not in p.parts);paths.update(str(P/n) for n in ['pins.json','output/run.log','output/process.json','output/results.toml']);paths.add(str(D/'measurement-rejection.json'))
(Q/'pins.json').write_text(json.dumps(dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}),indent=2,sort_keys=True)+'\n')
print('correctness-only qualificationprepared',len(paths),'pins; costrecordsnotrerun')
