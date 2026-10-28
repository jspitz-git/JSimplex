from pathlib import Path
import json,sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');sys.path.insert(0,str(D));import common as c
r=c.read('result-review.json');c.need(r['accepted'] is True and r['findings']==[],'accepted independent cost result');accepted=r['accepted_variants'];c.need(accepted and set(accepted)<=set('ABC'),'selected variants')
gates=[]
if 'A' in accepted:
 for mode in ['structural','slack']:gates.append(dict(type='BigFloat',arm='A',scope='residual',n=64,density='sparse',shape='positive',mode=mode,recycled=False,cap=8))
if 'B' in accepted:
 for recycled in [False,True]:gates.append(dict(type='BigFloat',arm='B',scope='update',n=16,density='sparse',shape='positive',mode='structural',recycled=recycled,cap=8))
if 'C' in accepted:
 for typ in ['BigFloat','Rational{BigInt}']:gates.append(dict(type=typ,arm='C',scope='crash',n=32,density='dense',shape='mixed',mode='structural',recycled=False,cap=8))
text='module GenericResidualPivotCrashTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst RPCA=JSimplex\nconst RPCB=JSimplex\nconst RPCC=JSimplex\n'+(D/'fixtures-final.jl').read_text()+'''
function allocation_gate(::Type{T},scope,arm,n,density,shape,mode,recycled,cap) where T
 a=fixture(T,n,density,shape,scope;mode,recycled,cap);b=fixture(T,n,density,shape,scope;mode,recycled,cap)
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
@testset "Multiprecision residual pivot and crash" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
'''
for g in gates:text+='   allocation_gate('+g['type']+',:'+g['scope']+',:'+g['arm']+','+str(g['n'])+',:'+g['density']+',:'+g['shape']+',:'+g['mode']+','+str(g['recycled']).lower()+','+str(g['cap'])+')\n'
text+='  end\n end\nend\nend\n'
(D/'new-test.jl').write_text(text);line=next(i for i,s in enumerate(text.splitlines(),1) if s.startswith(' @test all(after[k]'))
grid=c.read('expected-cases.json');cellasserts=sum(18+2*(6+(2 if v['variant']=='B' else 1 if v['variant']=='C' else 0)) for v in grid)
correctness=c.read('audit.json')['assertions']-cellasserts;c.need(correctness>0,'correctness count')
total=correctness+sum(6+(2 if g['arm']=='B' else 1 if g['arm']=='C' else 0)+7 for g in gates)
c.put('test-gates.json',dict(accepted_variants=accepted,expected_RED_failures=len(gates),failure_line=line,gates=gates,expected_RED_total=total,expected_RED_passes=total-len(gates),correctness_assertions_from_unchanged_source=correctness,comparison_cell_assertions=cellasserts,rule='fixed3whole-callpairs lowerEvents each/lowerMedianBytes; all numerical expectations and oldthresholds unchanged, no timingassertion'))
shutil.copytree(D/'baseline',D/'RED');shutil.copyfile(D/'new-test.jl',D/'RED/test/generic_residual_pivot_crash_tests.jl');shutil.copyfile(__file__,D/'test-prepare.py')
print('permanent ordinarytest original RED expected',total-len(gates),'PASS +',len(gates),'costFAIL =',total,'at',line)
