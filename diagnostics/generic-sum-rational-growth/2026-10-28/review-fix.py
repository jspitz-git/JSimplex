from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
s=(D/'fixtures.jl').read_text()
s=s.replace('if v.scope===:rows;return mod._primal_row_bounds!(v.lower,v.upper,v.p.A,v.x)','if v.scope===:rows\n  return eltype(v.x)<:Rational ? mod._primal_row_bounds(v.p.A,v.x,J._is_exact(eltype(v.x))) : mod._primal_row_bounds!(v.lower,v.upper,v.p.A,v.x)')
s=s.replace('if a.scope===:rows;@test x[2][1]===a.lower&&x[2][2]===a.upper;@test y[2][1]===b.lower&&y[2][2]===b.upper;end','''if a.scope===:rows && x[1]===:value && y[1]===:value
  if eltype(a.x)<:Rational
   @test x[2][1]===x[2][2];@test y[2][1]===y[2][2]
  else
   @test x[2][1]===a.lower&&x[2][2]===a.upper;@test y[2][1]===b.lower&&y[2][2]===b.upper
  end
 end''')
s=s.replace('Rational{BigInt}(a.lower[i])<=exact[i]<=Rational{BigInt}(a.upper[i])','Rational{BigInt}(out[2][1][i])<=exact[i]<=Rational{BigInt}(out[2][2][i])')
(D/'fixtures-reviewed.jl').write_text(s)
e=(D/'extra-tests.jl').read_text()
e=e.replace('what in (:infinite,:explicit_zero)','what in (:infinite,:explicit_zero),rhosign in (1,-1)').replace('v.rho[1]=T(1,0)','v.rho[1]=T(rhosign,0)')
e=e.replace('  # Caller ambient precision and rounding must be restored even on failure paths.','''  # Empty matrix/point/certificate and zero-dimensional PFI use the real paths.
  for scope in (:rows,:feasible)
   a=fixture(T,0,:sparse,:positive,scope);b=fixture(T,0,:sparse,:positive,scope);out=checkpair(a,b,:A)
   @test out[1]===:value
   if scope===:feasible;@test out[2]===true;else;@test isempty(out[2][1])&&isempty(out[2][2]);end
  end
  for below in (true,false)
   a=fixture(T,0,:sparse,:positive,:cert;below);b=fixture(T,0,:sparse,:positive,:cert;below);@test checkpair(a,b,:B)==(:value,false)
  end
  for scope in (:growth,:refresh,:scheduled)
   a=fixture(T,0,:sparse,:positive,scope;chain=0);b=fixture(T,0,:sparse,:positive,scope;chain=0);@test checkpair(a,b,:C)[1]===:value
  end
  if T===BigFloat
   for chain in (0,1)
    a=fixture(T,8,:dense,:positive,:growth;chain);b=fixture(T,8,:dense,:positive,:growth;chain)
    for v in (a,b),eta in v.w.factorization.updates;fill!(eta.values,T(1//2));end
    old1=whole(Val(:original),a);old2=whole(Val(:original),a);new1=whole(Val(:C),b);new2=whole(Val(:C),b)
    @test same(old1,new1)&&same(old2,new2)&&new1==1
    @test old1!==old2;@test new1!==new2
    @test all(new1!==z for eta in b.w.factorization.updates for z in eta.values)
   end
   # Independently chosen dyadic lies just above the binary64 midpoint;
   # ambient64/128/256 loses its last bit, while the actual recovery512 path retains it.
   wideweight=setprecision(BigFloat,512) do
    -(BigFloat(1)+ldexp(BigFloat(1),-53)+ldexp(BigFloat(1),-400))
   end
   exactweight=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)+Rational{BigInt}(1,big(1)<<400)
   expected_float=rounding(BigFloat) in (RoundDown,RoundToZero) ? 1.0 : nextfloat(1.0)
   for site in (:cost,:policy,:bound),scope in (:refresh,:scheduled)
    a=fixture(T,8,:dense,:positive,scope;chain=8);b=fixture(T,8,:dense,:positive,scope;chain=8)
    for v in (a,b)
     for eta in v.w.factorization.updates;fill!(eta.values,T(1//2));end
     v.w.factorization.updates[1].values[1]=wideweight
     if site===:cost
      v.w.costs[1]=setprecision(BigFloat,512) do;BigFloat(1//4);end
     elseif site===:bound
      v.w.lower[1]=Bound(setprecision(BigFloat,512) do;BigFloat(-8);end)
     else
      p=v.w.progress;old=p.numerical_policy;tol=setprecision(BigFloat,512) do;BigFloat(1//1024);end
      pol=typeof(old)((k===:solve_tolerance ? tol : getfield(old,k) for k in fieldnames(typeof(old)))...)
      v.w.progress=typeof(p)((k===:numerical_policy ? pol : getfield(p,k) for k in fieldnames(typeof(p)))...)
     end
    end
    aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),))
    @test checkpair(aa,bb,:C)[1]===:value
    @test a.w.scratch.refactorization.growth_scale===expected_float
    @test b.w.scratch.refactorization.growth_scale===expected_float
    @test b.w.scratch.refactorization.metrics_update_count==8
    @test b.w.scratch.refactorization.stored_elements==J._factor_storage_count(b.w.factorization)
    precise=setprecision(BigFloat,512) do;SRGC._factor_growth_measure(b.w.factorization);end
    @test precision(precise)==512;@test Rational{BigInt}(precise)==exactweight
   end
  end
  # Caller ambient precision and rounding must be restored even on failure paths.''')
(D/'extra-tests-reviewed.jl').write_text(e)
driver=(D/'driver.jl').read_text().replace('"fixtures.jl"','"fixtures-reviewed.jl"').replace('"extra-tests.jl"','"extra-tests-reviewed.jl"');(D/'driver-reviewed.jl').write_text(driver)
common=(D/'common.py').read_text().replace("read('contract.json')","read('contract-reviewed.json')").replace("read('pins.json')","read('pins-reviewed.json')");(D/'common_reviewed.py').write_text(common)
launch=(D/'launch.py').read_text().replace('from common import *','from common_reviewed import *').replace("'admission.json'","'admission-reviewed.json'").replace("'contract.json'","'contract-reviewed.json'").replace("'pins.json'","'pins-reviewed.json'");(D/'launch-reviewed.py').write_text(launch)
contract=c.read('contract.json');contract['command']=[v.replace(str(D/'driver.jl'),str(D/'driver-reviewed.jl')) for v in contract['command']];c.put('contract-reviewed.json',contract)
c.put('review-fix.json',dict(Julia_executed=False,candidates_unchanged={a:c.sha(D/(a+'.jl')) for a in ['Reference','A','B','C']},grid_unchanged=c.sha(D/'grid.toml'),cases=2636,windows=47448,changes=['Exact-rational row controls use existing allocating route; floating retains provided output owners','Exact enclosure assertions read actual returned outputs','Genuine512 cost/policy/bound widening with hand-chosen binary64-midpoint dyadic, full state/storage/ambient checks','Actual zero-dimensional row/feasibility/certificate/PFI controls','Fresh unit owner across consecutive empty/all-subunit growth calls','Stored negative and positive rational infinity plus explicit-zero DivideError controls']))
shutil.copyfile(__file__,D/'review-fix.py');print('separate harness-only correction; candidate/grid unchanged; noJulia')
