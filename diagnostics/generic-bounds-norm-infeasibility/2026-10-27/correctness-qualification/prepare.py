from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');Q=D/'comparison-2';sys.path.insert(0,str(Q));import common as c
p=c.read('output/process.json');c.need(p['returncode']==1 and p['pins_unchanged'],'preservedfailedcomparison');s=(Q/'output/run.log').read_text();c.need(s.count('Test Failed at ')==18 and 'Error During Test' not in s,'only18oraclefailures')
extra=set(c.read('host-seed.json')['groups'])|{p[k][v] for k in ['runner','child'] for v in ['pgid','sid']};h=c.host(extra);h['diagnostic_head']=c.git(['rev-parse','HEAD'],c.R)
K=D/'correctness-qualification';K.mkdir()
def put(n,v):
 with (K/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
source=(Q/'extra-tests.jl').read_text();old='    @test r[1]===:value&&same(r[2][2],floatmax(BigFloat))';new='''    poisoned = wide && any(sign<0 for sign in signs) && rounding(BigFloat) in (RoundNearest,RoundUp,RoundFromZero)
    @test r[1]===:value&&(poisoned ? isnan(r[2][2]) : same(r[2][2],floatmax(BigFloat)))
    if poisoned
     negative=first(v for v in vals if signbit(v))
     magnitude=J._primal_direction_magnitude(negative)
     @test isfinite(negative)&&precision(negative)==512
     @test isinf(magnitude)&&!signbit(magnitude)&&precision(magnitude)==precision(BigFloat)
     @test all(iszero(v/magnitude) for v in vals)&&iszero(inv(magnitude))
     @test isnan(magnitude*zero(BigFloat))
    end''';c.need(source.count(old)==1,'exactbadexpectedcapsite');(K/'extra-corrected.jl').write_text(source.replace(old,new))
text='''using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
'''
for arm in ['Reference','A','B','C']:text+='include('+json.dumps(str(Q/(arm+'.jl')))+')\n'
text+='include('+json.dumps(str(Q/'fixtures.jl'))+')\ninclude(joinpath(@__DIR__,"extra-corrected.jl"))\n'
text+='''@testset "Bounds norm certificate correctness qualification" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat);extra_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
end
println("BNI_CORRECTNESS_QUALIFICATION_COMPLETE");flush(stdout)
''';(K/'driver.jl').write_text(text)
for n in ['common.py','launch.py','environment.json','protected-before.json']:shutil.copyfile(Q/n,K/n)
shutil.copytree(Q/'guard',K/'guard',ignore=shutil.ignore_patterns('__pycache__'));put('host-before.json',h);put('host-seed.json',h)
co=c.read('contract.json');co['command']=co['command'][:-2]+[str(K/'driver.jl')];co.update(cases=0,measured_windows=0,role='correctness-only, no time/allocmeasurementrerun');put('contract.json',co)
put('oracle-correction.json',dict(original_accepted=False,original_returncode=1,original_expectedcap_failures=18,source_explanation='stored512 negativeabs currentprecision overflows +Inf inNearest/Up/From; finitecoeff/Inf=0, Inf*0=NaN inoriginalandcandidate',corrected_expectation='exact18NaN cases, allother72cap cases unchanged; verifyeachintermediatestage',candidate_and_original_windows_unchanged=True,bindings={str(Q/n):c.sha(Q/n) for n in ['extra-tests.jl','driver.jl','output/process.json','output/run.log','output/results.toml']}))
shutil.copyfile(__file__,K/'prepare.py');paths=set(c.read('pins.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.is_relative_to(D/'baseline'))
put('pins.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import importlib.util
sp=importlib.util.spec_from_file_location('qualcommon',K/'common.py');cc=importlib.util.module_from_spec(sp);sp.loader.exec_module(cc);cc.unchanged();cc.put('author-host.json',cc.host());print('correctnessonlyqualification',len(paths),'pins;',len(h['groups']),'groups; noJulia')
