from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');sys.path.insert(0,str(D));import common_reviewed as c
r=c.read('result-review.json');c.need(r['accepted'] and not r['findings'],'accepted comparison review')
for p,h in r['bindings'].items():c.need(c.sha(p)==h,'result binding '+p)
c.unchanged();Q=D/'comparison-2'
text='module GenericStagnationUnitSeedTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra\n'+(D/'Reference.jl').read_text()+'\nconst SSUA=JSimplex\nconst SSUB=JSimplex\nconst SSUC=JSimplex\nconst SSUBC=JSimplex\n'+(Q/'fixtures-reviewed.jl').read_text()+(Q/'extra-tests-reviewed.jl').read_text()+(D/'boundary-tests.jl').read_text()+'''
@testset "Stagnation unit and shared row-weight regressions" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);boundary_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);boundary_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (T,n,m,scope,shape,arm) in ((BigFloat,128,32,:values,:unbounded,:A),(BigFloat,128,32,:observe,:unbounded,:A),(BigFloat,32,32,:unit,:positive,:B),(Rational{BigInt},32,32,:unit,:positive,:B),(BigFloat,8,32,:init,:slack,:C))
    @testset "Whole-call allocation $T $scope" begin
     a=fixture(T,n,m,scope,:sparse,shape);b=fixture(T,n,m,scope,:sparse,shape);s=Val(scope)
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
(D/'new-test.jl').write_text(text);shutil.copytree(D/'baseline',D/'RED');(D/'RED/test/generic_stagnation_unit_seed_tests.jl').write_text(text);shutil.copyfile(__file__,D/'test-prepare.py');print('new ordinarytest and baselineRED prepared, no productioncandidate stage yet')
