from pathlib import Path
import sys,shutil,json,re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common_ready as c
p=c.read('output/process.json');s=c.read('supervisor.json');c.need(p['returncode']==1 and p['pins_unchanged'] and not s['accepted'] and not s['soft_timeout'] and not s['hard_timeout'],'preserved non-timeout failure')
c.unchanged();groups=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];h=c.host(groups);c.put('failed-comparison-host.json',h)
K=D/'correctness-qualification';K.mkdir();c.put(str(K/'host-before.json'),dict(h,diagnostic_head=c.git(['rev-parse','HEAD'],c.R)));c.put(str(K/'host-seed.json'),h)
e=(D/'extra-tests-ready.jl').read_text();old='@test precision(precise)==512;@test Rational{BigInt}(precise)==exactweight';c.need(e.count(old)==1,'unique exact conversion oracle')
new='''@test precision(precise)==512
    old_decoded=Rational{BigInt}(precise)
    rounded_expected=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)
    if rounding(BigFloat) in (RoundUp,RoundFromZero)
     rounded_expected+=Rational{BigInt}(1,big(1)<<(precision(BigFloat)-1))
    end
    @test old_decoded==rounded_expected
    @test old_decoded!=exactweight
    ambient=(precision(BigFloat),rounding(BigFloat))
    decoded=setprecision(BigFloat,precision(precise)) do
     Rational{BigInt}(precise)
    end
    @test decoded==exactweight
    @test ambient==(precision(BigFloat),rounding(BigFloat))'''
(K/'extra-corrected.jl').write_text(e.replace(old,new))
log=(D/'output/run.log').read_text();rows=[v for v in log.splitlines() if v.startswith('  ordinary whole functions ') or v.startswith('  independent boundaries ')]
oldtotal=sum(int(v.split('|',1)[1].split()[-2]) for v in rows);c.need(len(rows)==38 and oldtotal==27957,'exact recorded correctness total')
c.put(str(K/'oracle-correction.json'),dict(Julia_executed=False,unchanged_original_expected_rational='1+2^-53+2^-400',root_cause='mpfr.jl Rational{BigInt}(AbstractFloat) scales using ambient-precision BigFloat ldexp',only_conversion_precision_changed=True,decoder_scope='setprecision(precision(precise)) around conversion only; original growth/input/context untouched',original_correctness_total=oldtotal,extra_assertions=270,expected_total=oldtotal+270,original_failure_count=90,measured_windows=0,original_extra_sha256=c.sha(D/'extra-tests-ready.jl'),corrected_extra_sha256=c.sha(K/'extra-corrected.jl'),original_run_remains_failed=True))
code='''using Test,JSimplex,SparseArrays,LinearAlgebra
BLAS.set_num_threads(1)
@assert realpath(pathof(JSimplex))==realpath("/home/jspitz/JSimplex.jl/src/JSimplex.jl")
@assert Base.active_project()=="/home/jspitz/JSimplex.jl/Project.toml"
@assert Threads.nthreads()==BLAS.get_num_threads()==1
const PARENT=dirname(@__DIR__)
for arm in ("Reference","A","B","C");include(joinpath(PARENT,arm*".jl"));end
include(joinpath(PARENT,"fixtures-reviewed.jl"));include(joinpath(@__DIR__,"extra-corrected.jl"))
@testset "SRG corrected exact-decoder qualification" begin
 for bits in (64,128,256),(mode,name) in zip(MODES,("Nearest","Down","Up","ToZero","FromZero"))
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    println("CONTEXT BF",bits,"_",name);flush(stdout);correctness(BigFloat);extra_correctness(BigFloat)
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64})
  println("CONTEXT ",T);flush(stdout);correctness(T);extra_correctness(T)
 end
end
println("SRG_CORRECTNESS_COMPLETE");flush(stdout)
'''
(K/'driver.jl').write_text(code)
shutil.copytree(D/'guard',K/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(K/'common.py').write_text((D/'common.py').read_text())
(K/'launch.py').write_text((D/'launch.py').read_text())
for n in ['protected-before.json','environment.json']:shutil.copyfile(D/n,K/n)
cmd=c.read('contract-ready.json')['command'][:-2]+[str(K/'driver.jl')]
c.put(str(K/'contract.json'),dict(command=cmd,attempts=1,expected_exit=0,contexts=19,expected_assertions=oldtotal+270,measured_windows=0,shared_limit_seconds=900,guard_limit_seconds=892,original_comparison_remains_failed=True))
paths=set(c.read('pins-ready.json')['files']);paths.update(str(D/n) for n in ['output/process.json','output/run.log','output/results.toml','supervisor.json','invocation.json','reservation.json','contract-ready.json','pins-ready.json','admission-ready.json','failed-comparison-host.json'])
shutil.copyfile(__file__,K/'prepare.py');paths.update(str(p) for p in K.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put(str(K/'pins.json'),dict(files=sorted(paths),trees=c.read('pins-ready.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
print('correctness-only qualifier prepared',len(paths),'pins',oldtotal+270,'expected assertions; no measurement windows; noJulia')
