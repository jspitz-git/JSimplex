from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common_ready as c
r=c.read('result-review.json');c.need(r['accepted'] is True and r['findings']==[],'independent accepted result');accepted=r['accepted_variants'];c.need(accepted and set(accepted)<=set('ABC'),'accepted source choices')
gates=[]
if 'A' in accepted:
 for scope in ['rows','feasible']:gates.append(dict(type='BigFloat',scope=scope,arm='A',n=64,density='dense',shape='positive',below=True,chain=8))
if 'B' in accepted:
 for below in [True,False]:gates.append(dict(type='Rational{BigInt}',scope='cert',arm='B',n=16,density='dense',shape='wide',below=below,chain=8))
if 'C' in accepted:
 for scope in ['growth','refresh','scheduled']:gates.append(dict(type='BigFloat',scope=scope,arm='C',n=8,density='dense',shape='positive',below=True,chain=8))
text='module GenericSumRationalGrowthTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst SRGA=JSimplex\nconst SRGB=JSimplex\nconst SRGC=JSimplex\n'+(D/'fixtures-reviewed.jl').read_text()+'\n'+(D/'correctness-qualification/extra-corrected.jl').read_text()+'''\nfunction allocation_gate(::Type{T},scope,arm,n,density,shape,below,chain) where T
 a=fixture(T,n,density,shape,scope;below,chain);b=fixture(T,n,density,shape,scope;below,chain)
 checkpair(a,b,arm)
 for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
 before=Any[];after=Any[]
 for pair in 1:3,tag in (isodd(pair) ? (:original,arm) : (arm,:original))
  v=tag===:original ? a : b;reset!(v);t=timed(Val(tag),v)
  @test t["compile_seconds"]==t["recompile_seconds"]==0
  push!(tag===:original ? before : after,t)
 end
 @test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)
 nothing
end
@testset "Multiprecision sums exact certificate and growth" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
'''
for q in gates:text+='   allocation_gate('+q['type']+',:'+q['scope']+',:'+q['arm']+','+str(q['n'])+',:'+q['density']+',:'+q['shape']+','+str(q['below']).lower()+','+str(q['chain'])+')\n'
text+='  end\n end\nend\nend\n'
(D/'new-test.jl').write_text(text);line=next(i for i,v in enumerate(text.splitlines(),1) if v.startswith(' @test all(after[k]'))
c.put('test-gates.json',dict(accepted_variants=accepted,expected_RED_failures=len(gates),failure_line=line,gates=gates,rule='fixed3whole-callpairs: lowerEvents ineach/lowerMedianBytes; allnumericalexpectations unchanged, decoderonlyqualified; no oldthreshold or timingassertion'))
shutil.copytree(D/'baseline',D/'RED');shutil.copyfile(D/'new-test.jl',D/'RED/test/generic_sum_rational_growth_tests.jl');shutil.copyfile(__file__,D/'test-prepare.py')
print('ordinary permanent test prepared; expected original allocation failures',len(gates),'line',line)
