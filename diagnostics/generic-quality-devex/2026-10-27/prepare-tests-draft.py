from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27')
body='''module GenericQualityDevexTests
using Test,JSimplex,SparseArrays,LinearAlgebra
'''+(D/'reference.jl').read_text()+'''const SavingsCandidate=JSimplex
'''+(D/'fixtures.jl').read_text()+'''
@testset "BigFloat residual, quality and Devex regressions" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 # A missing accepted optimization makes these whole-function gates fail.
 # No timing threshold, no GC tuning, no adaptive reruns; fixed three pairs.
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for scope in (:direction,:row,:quality,:quality_transposed,:devex_shared,:devex_solved)
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,32,scope,:dense,:positive);b=fixture(BigFloat,32,scope,:dense,:positive)
     m=Val(scope)
     for k in 1:3,(arm,v) in ((Val(:original),a),(Val(:candidate),b));reset!(v);timed(arm,m,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),m,a);reset!(b);new=timed(Val(:candidate),m,b)
      else;reset!(b);new=timed(Val(:candidate),m,b);reset!(a);old=timed(Val(:original),m,a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["bytes"]<0.97old["bytes"]&&new["events"]<0.97old["events"] for (old,new) in pairs) # RED whole-call cost gate
    end
   end
  end
 end
end
end
'''
(D/'new-test-draft.jl').write_text(body)
shutil.copyfile(__file__,D/'prepare-tests-draft.py');print('new test draft prepared; not installed or executed')
