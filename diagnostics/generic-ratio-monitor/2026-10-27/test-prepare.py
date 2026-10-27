from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common_complete as c
r=c.read('result-review.json');c.need(r['accepted'] and not r['findings'],'accepted independent measured result');accepted=r['accepted_variants'];c.need(accepted==['A','B','C'],'this ordinary suite covers the independently accepted three variants');c.unchanged()
fixtures=(D/'fixtures-complete.jl').read_text()
fixtures=fixtures.replace('RMA._primal_nonnegative_step(x)','tested_nonnegative_step(x)')
# Baseline uses its exact original max expression; optimized source exposes the helper.
fixtures+='\ntested_nonnegative_step(x::BigFloat)=isdefined(JSimplex,:_primal_nonnegative_step) ? JSimplex._primal_nonnegative_step(x) : max(zero(BigFloat),x)\n'
body='module GenericRatioMonitorTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst RMA=JSimplex\nconst RMB=JSimplex\nconst RMC=JSimplex\nconst RMBC=JSimplex\n'+fixtures+'''
@testset "BigFloat ratio zeros and stagnation magnitudes" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (scope,arm,phase) in ((:ratio,:A,:end),(:progress,:B,:ordinary),(:progress,:C,:end),(:workspace,:BC,:end))
    @testset "Whole-call allocation $scope/$arm/$phase" begin
     a=fixture(BigFloat,64,:dense,:positive,scope,phase);b=fixture(BigFloat,64,:dense,:positive,scope,phase)
     for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
     pairs=Tuple{Dict{String,Any},Dict{String,Any}}[]
     for k in 1:3
      if isodd(k);reset!(a);old=timed(Val(:original),a);reset!(b);new=timed(Val(arm),b)
      else;reset!(b);new=timed(Val(arm),b);reset!(a);old=timed(Val(:original),a)
      end
      @test old["compile_seconds"]==old["recompile_seconds"]==new["compile_seconds"]==new["recompile_seconds"]==0
      push!(pairs,(old,new))
     end
     @test all(new["events"]<old["events"] for (old,new) in pairs)&&median([new["bytes"] for (old,new) in pairs])<median([old["bytes"] for (old,new) in pairs]) # RED whole-call allocation gate
    end
   end
  end
 end
end
end
'''
(D/'new-test.jl').write_text(body);shutil.copytree(D/'baseline',D/'RED');(D/'RED/test/generic_ratio_monitor_tests.jl').write_text(body)
c.put('test-gates.json',dict(accepted_variants=accepted,gates=[['ratio','A','end'],['progress','B','ordinary'],['progress','C','end'],['workspace','BC','end']],expected_RED_failures=4,failure_line=next(i for i,line in enumerate(body.splitlines(),1) if '# RED whole-call allocation gate' in line),rule='fixed3pairs lowerEvents each/lowerMedianBytes, no time assertions, original tests/thresholds unchanged',baseline_component_test='Uses exact old max when production helper absent; all whole-call gates call actual original functions and must fail RED'))
shutil.copyfile(__file__,D/'test-prepare.py');print('ordinary test and original RED prepared; four prospective cost failures')
