from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');Q=D/'comparison-2'
body='''module GenericQualityLocalTests
using Test,JSimplex,SparseArrays,LinearAlgebra
'''+(Q/'Reference.jl').read_text()+'''
const LocalCandidateA=JSimplex
const LocalCandidateB=JSimplex
const LocalCandidateAB=JSimplex
const LocalCandidateC=JSimplex
'''+(Q/'fixtures.jl').read_text()+'''
@testset "BigFloat invocation-local quality regressions" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat)
    # Nonordinary matrices must retain the generic fallback.
    for scope in (:quality,:quality_transposed)
     a=fixture(BigFloat,4,scope,:dense,:mixed);b=fixture(BigFloat,4,scope,:dense,:mixed)
     a=merge(a,(B=PlainWrapper(a.B),));b=merge(b,(B=PlainWrapper(b.B),));checkpair(a,b,:AB)
    end
    # Direct whole-finalizer checks at zero/negative/nonfinite scales and
    # roundoff boundaries, including hardware result with BigFloat work.
    for scalevalue in (BigFloat(0),BigFloat(-1),BigFloat(Inf),BigFloat(NaN)),term in (0,5,typemax(Int))
     a=fixture(BigFloat,2,:finish,:vector,:mixed);b=fixture(BigFloat,2,:finish,:vector,:mixed)
     for v in (a,b);v.scale[1]=copy(scalevalue);v.terms[1]=term;end
     checkpair(a,b,:B)
    end
    for T in (Float32,Float64)
     a=fixture(BigFloat,2,:finish,:vector,:mixed);b=fixture(BigFloat,2,:finish,:vector,:mixed)
     a=merge(a,(scratch=J.SolveQualityScratch(T,2),policy=J.NumericalPolicy(T)));b=merge(b,(scratch=J.SolveQualityScratch(T,2),policy=J.NumericalPolicy(T)));checkpair(a,b,:B)
    end
   end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 # Fixed three alternating whole-call allocation pairs. No time assertion,
 # GC selection, repeated searches or reduced numerical expectations.
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (scope,pattern,m,arm) in ((:quality,:negative,0,:AB),(:quality_transposed,:negative,0,:AB),(:finish,:mixed,0,:B),(:audit,:positive,4,:C))
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,96,scope,:dense,pattern,m);b=fixture(BigFloat,96,scope,:dense,pattern,m);s=Val(scope)
     for k in 1:3,(method,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(method,s,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),s,a);reset!(b);new=timed(Val(arm),s,b)
      else;reset!(b);new=timed(Val(arm),s,b);reset!(a);old=timed(Val(:original),s,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["bytes"]<old["bytes"]&&new["events"]<old["events"] for (old,new) in pairs) # RED whole-call cost gate
    end
   end
  end
 end
end
end
'''
(D/'new-test-draft.jl').write_text(body)
shutil.copyfile(__file__,D/'prepare-tests-draft.py');print('unexecuted permanent test draft; exact allocation reduction, no timing assertion')
