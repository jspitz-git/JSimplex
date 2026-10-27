from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');sys.path.insert(0,str(D));import common_ready as c
# Called only once after independently accepted complete comparison.
r=c.read('comparison-3/result-review.json');c.need(r['accepted'] and not r['findings'],'comparison result accepted')
for p,h in r['bindings'].items():c.need(c.sha(p)==h,'result review binding')
c.unchanged()
reference=(D/'Reference.jl').read_text();fixtures=(D/'comparison-3/fixtures.jl').read_text();extra=(D/'extra-tests-ready.jl').read_text()
native=(D/'comparison-3/native-oracle.jl').read_text();native='\n'.join(line for line in native.splitlines() if not line.startswith('const NATIVE_ORACLES=') and not line.lstrip().startswith('push!(NATIVE_ORACLES,'))+'\n'
text='module GenericVirtualFreePivotTests\n'+reference+'\nconst VFPA=JSimplex\nconst VFPB=JSimplex\nconst VFPC=JSimplex\n'+fixtures+extra+native+'''
@testset "BigFloat virtual audit free pricing and checked pivots" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for scope in (:audit,:virtual,:enter_dantzig,:summary,:pivot)
    @testset "Whole-call allocation $scope" begin
     a=fixture(BigFloat,128,16,scope,:dense,:positive);b=fixture(BigFloat,128,16,scope,:dense,:positive);arm=armfor(scope);s=Val(scope)
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
(D/'new-test.jl').write_text(text)
shutil.copytree(D/'baseline',D/'RED');(D/'RED/test/generic_virtual_free_pivot_tests.jl').write_text(text)
shutil.copyfile(__file__,D/'test-prepare.py')
print('ordinary test and original RED source prepared; no production candidate source written')
