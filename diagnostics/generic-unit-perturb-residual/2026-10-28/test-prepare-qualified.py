from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
r=c.read('result-review.json');c.need(r['accepted'] is True and r['findings']==[],'accepted independent results');accepted=r['accepted_variants'];c.need(accepted and set(accepted)<=set('ABC'),'accepted variants')
gates=[]
if 'A' in accepted:
 for scope in ['devex','steepest']:gates.append(dict(type='Rational{BigInt}',arm='A',scope=scope,n=64,density='sparse',shape='mixed',mode='unit'))
if 'B' in accepted:
 for scope in ['dual','primal']:gates.append(dict(type='BigFloat',arm='B',scope=scope,n=64,density='dense',shape='mixed',mode='unit'))
if 'C' in accepted:
 for typ in ['Float64','BigFloat','Rational{BigInt}']:
  for scope in ['residual','outer']:gates.append(dict(type=typ,arm='C',scope=scope,n=64,density='sparse',shape='mixed',mode='unit'))
text='module GenericUnitPerturbResidualTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst UPRA=JSimplex\nconst UPRB=JSimplex\nconst UPRC=JSimplex\n'+(D/'fixtures-qualified.jl').read_text()+'''
function allocation_gate(::Type{T},scope,arm,n,density,shape,mode) where T
 a=fixture(T,n,density,shape,scope;mode);b=fixture(T,n,density,shape,scope;mode)
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
@testset "Multiprecision unit perturb and residual" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
'''
for g in gates:text+='   allocation_gate('+g['type']+',:'+g['scope']+',:'+g['arm']+','+str(g['n'])+',:'+g['density']+',:'+g['shape']+',:'+g['mode']+')\n'
text+='  end\n end\nend\nend\n'
(D/'new-test.jl').write_text(text);line=next(i for i,x in enumerate(text.splitlines(),1) if x.startswith(' @test all(after[k]'))
checks={'A':6,'B':9,'C':10}
grid=c.read('expected-cases.json');cellasserts=sum(18+2*checks[v['variant']]+(18 if v['variant']=='B' else 0) for v in grid)
correctness=c.read('audit.json')['assertions']-cellasserts;c.need(correctness>0,'correctness count')
total=correctness+sum(checks[g['arm']]+7 for g in gates)
c.put('test-gates.json',dict(accepted_variants=accepted,expected_RED_failures=len(gates),failure_line=line,gates=gates,expected_RED_total=total,expected_RED_passes=total-len(gates),correctness_assertions_from_unchanged_source=correctness,comparison_cell_assertions=cellasserts,rule='fixed3whole-callpairs lowerEvents each/lowerMedianBytes; all numerical expectations and oldthresholds unchanged, no timingassertion'))
shutil.copytree(D/'baseline',D/'RED');shutil.copyfile(D/'new-test.jl',D/'RED/test/generic_unit_perturb_residual_tests.jl')
print('permanent ordinarytest RED expected',total-len(gates),'PASS+',len(gates),'costFAIL=',total,'at',line)
