from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');sys.path.insert(0,str(D));import common as c
r=c.read('result-review.json');c.need(r['accepted'] and not r['findings'],'accepted source/cost result')
for p,h in r['bindings'].items():c.need(c.sha(p)==h,'accepted result binding '+p)
c.unchanged();Q=D/'correctness-qualification';accepted=[x for x,v in r['variants'].items() if v['accepted']]
text='module GenericIntervalStagnationDevexTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra\n'+(D/'Reference.jl').read_text()+'\nconst ISDA=JSimplex\nconst ISDB=JSimplex\nconst ISDC=JSimplex\n'+(Q/'fixtures.jl').read_text()+'''
@testset "Interval monitor and Devex whole-function regressions" begin
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
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (scope,arm) in GATES
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,64,16,scope,:dense,:positive);b=fixture(BigFloat,64,16,scope,:dense,:positive);s=Val(scope)
     for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(method,s,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),s,a);reset!(b);new=timed(Val(arm),s,b)
      else;reset!(b);new=timed(Val(arm),s,b);reset!(a);old=timed(Val(:original),s,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["events"]<old["events"] for (old,new) in pairs)&&sort([new["bytes"] for (old,new) in pairs])[2]<sort([old["bytes"] for (old,new) in pairs])[2] # RED whole-call cost gate
    end
   end
  end
 end
end
end
'''
gates=[('rows','A'),('witness','A'),('new','B'),('cold','B'),('rebase','B'),('devex_solve','C')];gates=[(s,a) for s,a in gates if a in accepted];c.need(gates,'accepted measured gates');decl='const GATES=('+','.join('(:'+s+',:'+a+')' for s,a in gates)+',)\n';text=text.replace('@testset "Interval monitor and Devex whole-function regressions"',decl+'@testset "Interval monitor and Devex whole-function regressions"')
(D/'new-test.jl').write_text(text);shutil.copytree(D/'baseline',D/'RED');(D/'RED/test/generic_interval_stagnation_devex_tests.jl').write_text(text);c.put('test-gates.json',dict(accepted_variants=accepted,gates=gates,expected_RED_failures=len(gates),original_numerical_expectations_preserved=True,corrected_oracles_preserved=True,allocation_rule='fixed3pairs lower events each/lower medianbytes; no time assertions or original-test changes'))
shutil.copyfile(__file__,D/'test-prepare.py');print('ordinary newtest and original REDprepared; productionstage stillabsent',len(gates),'expectedfails')
