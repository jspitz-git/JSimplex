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
   for below in (true,false),mode in (:valid,:one_sided),what in (:infinite,:explicit_zero)
    a=fixture(T,16,:dense,:wide,:cert;below,mode);b=fixture(T,16,:dense,:wide,:cert;below,mode)
    for v in (a,b)
     v.rho[1]=T(1,0)
     what===:explicit_zero&&(v.w.problem.A.nzval[1]=zero(T))
    end
    out=checkpair(a,b,:B);@test out[1]===:error;@test out[2]===DivideError
   end
  elseif T===Rational{Int64}
   for below in (true,false)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    for v in (a,b);v.rho[1]=T(2);v.w.problem.A.nzval[1]=T(typemax(Int64));end
    @test checkpair(a,b,:B)==(:value,false)
   end
  end
  # Caller ambient precision and rounding must be restored even on failure paths.
  @test precision(BigFloat)>=64
 end
end
