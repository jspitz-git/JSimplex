from pathlib import Path
import sys,shutil,json
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');Q=D/'comparison-2';K=D/'correctness-qualification';sys.path.insert(0,str(D));import common as c
r=c.read('result-review.json');c.need(r['accepted'] and not r['findings'],'independentacceptedcost');accepted=r['accepted_variants'];c.unchanged()
specs=[('BigFloat','snap','A','finite'),('Rational{BigInt}','snap','A','finite'),('BigFloat','step','A','finite'),('Rational{BigInt}','step','A','finite'),('BigFloat','ratio','A','finite'),('Rational{BigInt}','ratio','A','finite'),('BigFloat','init','B','finite'),('BigFloat','solve','B','finite'),('BigFloat','cert','C','finite'),('BigFloat','cert','C','one_sided')];specs=[x for x in specs if x[2] in accepted]
decl='const GATES=('+','.join('('+t+',:'+scope+',:'+arm+',:'+mode+')' for t,scope,arm,mode in specs)+',)\n'
text='module GenericBoundsNormInfeasibilityTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(Q/'Reference.jl').read_text()+'\nconst BNIA=JSimplex\nconst BNIB=JSimplex\nconst BNIC=JSimplex\n'+(Q/'fixtures.jl').read_text()+'\n'+(K/'extra-corrected.jl').read_text()+'\n'+decl+'''
@testset "Bounds norm and infeasibility scalar regressions" begin
 for bits in (64,128,256),roundmode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,roundmode) do;correctness(BigFloat);extra_correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);extra_correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   for (T,scope,arm,mode) in GATES
    @testset "Whole-call allocation $T/$scope/$mode" begin
     a=fixture(T,64,:dense,:positive,scope;mode);b=fixture(T,64,:dense,:positive,scope;mode)
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
(D/'new-test.jl').write_text(text);shutil.copytree(D/'baseline',D/'RED');(D/'RED/test/generic_bounds_norm_infeasibility_tests.jl').write_text(text)
c.put('test-gates.json',dict(accepted_variants=accepted,gates=specs,expected_RED_failures=len(specs),failure_line=next(i for i,line in enumerate(text.splitlines(),1) if '# RED whole-call allocation gate' in line),rule='fixed3pairs lowerEvents each/lowerMedianBytes; originalnumericalexpectations corrected onlybyqualifiedspecific18NaNcases; no oldtestthresholdchanges'))
shutil.copyfile(__file__,D/'test-prepare.py');print('originalRED prepared',len(specs),'prospectivecostfailures')
