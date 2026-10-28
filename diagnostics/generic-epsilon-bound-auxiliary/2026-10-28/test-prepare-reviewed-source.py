from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
r=c.read('result-review.json');c.need(r['accepted'] is True and r['findings']==[],'accepted independent results');accepted=r['accepted_variants'];c.need(accepted and set(accepted)<=set('ABC'),'accepted variants')
gates=[]
if 'A' in accepted:
 for n in [16,64]:
  for density in ['sparse','dense']:gates.append(dict(type='BigFloat',arm='A',scope='direction',n=n,density=density,shape='mixed',mode='good'))
if 'B' in accepted:
 for typ in ['BigFloat','Rational{BigInt}']:
  for mode in ['free','mixed']:gates.append(dict(type=typ,arm='B',scope='errors',n=64,density='sparse',shape='mixed',mode=mode))
if 'C' in accepted:
 for typ in ['Float32','Float64']:
  for density in ['sparse','dense']:gates.append(dict(type=typ,arm='C',scope='auxiliary',n=16,density=density,shape='positive',mode='good'))
text='module GenericEpsilonBoundAuxiliaryTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst EBAA=JSimplex\nconst EBAB=JSimplex\nconst EBAC=JSimplex\n'+(D/'fixtures-supported.jl').read_text()+'''
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
@testset "Multiprecision epsilon bound and auxiliary" begin
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
with (D/'new-test.jl').open('x') as f:f.write(text)
line=next(i for i,x in enumerate(text.splitlines(),1) if x.startswith(' @test all(after[k]'))
checks={'A':7,'B':8,'C':10};grid=[v for v in c.read('expected-cases.json') if not (v['variant']=='C' and v['context'].startswith('Rational'))];cellasserts=sum(18+2*checks[v['variant']]+(18 if v['variant'] in ['A','C'] else 0) for v in grid)
prefix=c.read('audit-prefix.json');remaining=c.read('remaining-qualified/audit.json')
prefix_cells=sum(18+2*checks[v['variant']]+(18 if v['variant'] in ['A','C'] else 0) for v in c.read('expected-cases.json')[:1196])
floating=prefix['original_root_passed']-prefix_cells-193
rational=remaining['assertions']-30*(2*8+18)
correctness=floating+rational;c.need(floating==6745 and rational==408 and correctness==c.read('route-supplement.json')['supported_correctness_assertions']==7153,'observed successful correctness schedules, no rejected root acceptance')
total=correctness+sum(checks[g['arm']]+7 for g in gates)
c.put('test-gates.json',dict(accepted_variants=accepted,expected_RED_failures=len(gates),failure_line=line,gates=gates,expected_RED_total=total,expected_RED_passes=total-len(gates),correctness_assertions_from_unchanged_source=correctness,comparison_cell_assertions=cellasserts,rule='fixed3whole-callpairs lowerEvents each/lowerMedianBytes; all numerical expectations and oldthresholds unchanged, no timingassertion'))
shutil.copytree(D/'baseline',D/'RED');shutil.copyfile(D/'new-test.jl',D/'RED/test/generic_epsilon_bound_auxiliary_tests.jl');shutil.copyfile(__file__,D/'test-prepare.py')
print('permanent ordinarytest RED expected',total-len(gates),'PASS+',len(gates),'costFAIL=',total,'at',line)
