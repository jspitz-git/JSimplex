function extra_correctness(::Type{T}) where T
 @testset "independent boundaries $(T)" begin
  # Exact dyadics independently fix the expected sum; owner patterns are separate.
  pairs=[(T(3//2),T(1//4),T(7//4)),(-T(3//2),-T(1//4),-T(7//4)),(T(3//2),-T(3//2),zero(T)),(T(3//2),-T(1//4),T(5//4))]
  for (a,b,want) in pairs
   old=SRGReference._primal_sum_bounds(a,b);new=SRGA._primal_sum_bounds(a,b)
   @test same(old,new);@test new[1]<=want<=new[2]
   @test (old[1]===a,old[2]===a,old[1]===b,old[2]===b,old[1]===old[2])==(new[1]===a,new[2]===a,new[1]===b,new[2]===b,new[1]===new[2])
   if T===BigFloat&&iszero(want);@test new[1]!==new[2];end
  end
  # Truly empty/invalid primal structures and finite row/column rejection.
  for density in (:sparse,:dense)
   a=fixture(T,16,density,:positive,:feasible);b=fixture(T,16,density,:positive,:feasible)
   a.p.column_upper[1]=Bound(zero(T));b.p.column_upper[1]=Bound(zero(T));@test checkpair(a,b,:A)==(:value,false)
  end
  for chain in (0,1,4,8,32),scope in (:refresh,:scheduled)
   a=fixture(T,8,:dense,:mixed,scope;chain);b=fixture(T,8,:dense,:mixed,scope;chain)
   for fixed in (false,true),cached in (false,true)
    for v in (a,b)
     v.w.scratch.refactorization.fixed=fixed
     v.w.scratch.refactorization.metrics_update_count=cached ? chain : -1
    end
    # Explicitly freeze the changed initial state; resets keep the intended gate.
    aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),))
    @test checkpair(aa,bb,:C)[1]===:value
   end
  end
  if T===BigFloat
   wide=setprecision(BigFloat,512) do
    (BigFloat(3//2),BigFloat(-3//2),floatmax(BigFloat),-floatmax(BigFloat))
   end
   values=(BigFloat(0),-BigFloat(0),BigFloat(1),BigFloat(-1),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN),wide...)
   for a in values,b in values
    x=capture(()->SRGReference._primal_sum_bounds(a,b));y=capture(()->SRGA._primal_sum_bounds(a,b));@test same(x,y)
    @test aliaspattern(x,a,b)==aliaspattern(y,a,b)
    if x[1]===:value;@test (x[2][1]===x[2][2])==(y[2][1]===y[2][2]);end
   end
   for probe in (:unit,:wide_positive,:wide_negative,:nan,:inf,:growth)
    a=fixture(T,8,:dense,:positive,:growth;chain=1);b=fixture(T,8,:dense,:positive,:growth;chain=1)
    for v in (a,b)
     fill!(v.w.factorization.updates[1].values,one(T))
     value=probe===:unit ? one(T) : probe===:wide_positive ? wide[1] : probe===:wide_negative ? wide[2] : probe===:nan ? T(NaN) : probe===:inf ? T(Inf) : T(10^10)
     v.w.factorization.updates[1].values[1]=value
    end
    x=checkpair(a,b,:C);@test x[1]===:value
    old=x[2];new=whole(Val(:C),b)
    @test Tuple(old===z for z in a.w.factorization.updates[1].values)==Tuple(new===z for z in b.w.factorization.updates[1].values)
    @test same(new,whole(Val(:C),b))
   end
   # A growth failure outranks the coincident configured interval, then residual wins.
   a=fixture(T,8,:dense,:positive,:scheduled;chain=32);b=fixture(T,8,:dense,:positive,:scheduled;chain=32)
   for v in (a,b);v.w.factorization.updates[1].values[1]=T(10^10);end
   @test checkpair(a,b,:C)==(:value,:pivot_growth)
   for v in (a,b);v.w.scratch.refactorization.residual_bad=true;end
   aa=merge(a,(initial=statevalues(a.w.scratch.refactorization),));bb=merge(b,(initial=statevalues(b.w.scratch.refactorization),));@test checkpair(aa,bb,:C)==(:value,:residual)
  elseif T===Rational{BigInt}
   for below in (true,false),mode in (:valid,:one_sided),what in (:infinite,:explicit_zero),rhosign in (1,-1)
    a=fixture(T,16,:dense,:wide,:cert;below,mode);b=fixture(T,16,:dense,:wide,:cert;below,mode)
    for v in (a,b)
     v.rho[1]=T(rhosign,0)
     what===:explicit_zero&&(v.w.problem.A.nzval[1]=zero(T))
    end
    out=checkpair(a,b,:B)
    if rhosign==-1&&mode===:one_sided&&what===:infinite
     @test out[1]===:value;@test out[2]===false
    else
     @test out[1]===:error;@test out[2]===DivideError
    end
   end
  elseif T===Rational{Int64}
   for below in (true,false)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    for v in (a,b);v.rho[1]=T(2);v.w.problem.A.nzval[1]=T(typemax(Int64));end
    @test checkpair(a,b,:B)==(:value,false)
   end
  end
  # Empty matrix/point/certificate and zero-dimensional PFI use the real paths.
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
      v.w.costs[1]=BigFloat(v.w.costs[1];precision=512)
     elseif site===:bound
      v.w.lower[end]=Bound(BigFloat(bound_value(v.w.lower[end]);precision=512))
     else
      p=v.w.progress;old=p.numerical_policy;tol=BigFloat(old.solve_tolerance;precision=512)
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
    @test precision(precise)==512
    old_decoded=Rational{BigInt}(precise)
    rounded_expected=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)
    if rounding(BigFloat) in (RoundUp,RoundFromZero)
     rounded_expected+=Rational{BigInt}(1,big(1)<<(precision(BigFloat)-1))
    end
    @test old_decoded==rounded_expected
    @test old_decoded!=exactweight
    ambient=(precision(BigFloat),rounding(BigFloat))
    decoded=setprecision(BigFloat,precision(precise)) do
     Rational{BigInt}(precise)
    end
    @test decoded==exactweight
    @test ambient==(precision(BigFloat),rounding(BigFloat))
   end
  end
  # Caller ambient precision and rounding must be restored even on failure paths.
  @test precision(BigFloat)>=64
 end
end
