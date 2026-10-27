function extra_correctness(::Type{T}) where T
 @testset "Overflow cap and conservative rejection $T" begin
  if T===BigFloat
   for signs in ((1,1),(-1,-1),(1,-1)),wide in (false,true)
    vals=wide ? setprecision(BigFloat,512) do;[s*floatmax(BigFloat) for s in signs];end : [s*floatmax(BigFloat) for s in signs]
    a=(scope=:norm,vector=vals);b=(scope=:norm,vector=deepcopy(vals));r=checkpair(a,b,:B)
    @test r[1]===:value&&same(r[2][2],floatmax(BigFloat))
    x=whole(Val(:B),b);y=whole(Val(:B),b);@test x[2]!==y[2]
    @test all(x[2]!==v for v in b.vector)
    # A product above the finite range overflows only in these positive modes.
    product=floatmax(BigFloat)*sqrt(BigFloat(2))
    @test (isinf(product)&&!signbit(product))==(rounding(BigFloat) in (RoundNearest,RoundUp,RoundFromZero))
    @test rounding(BigFloat) in (RoundDown,RoundToZero) ? same(product,floatmax(BigFloat)) : isinf(product)
   end
   for below in (true,false),sign in (1,-1)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    wide=setprecision(BigFloat,512) do;sign*(BigFloat(1//8)+ldexp(BigFloat(1),-400));end
    a.rho[1]=wide;b.rho[1]=deepcopy(wide);checkpair(a,b,:C)
   end
  end
  if T<:AbstractFloat
   for below in (true,false)
    a=fixture(T,16,:dense,:positive,:cert;below);b=fixture(T,16,:dense,:positive,:cert;below)
    for v in (a,b)
     fill!(v.rho,zero(T));v.rho[1]=one(T);v.rho[2]=one(T)
     v.w.problem.A[1,1]=one(T);v.w.problem.A[2,1]=-one(T)
     v.w.lower[1]=J._unbounded_bound(T);v.w.upper[1]=J.Bound(T(2))
    end
    # Exact coefficient0 is enclosed by a strict sign-straddling interval;
    # the unbounded side must remain inconclusive before any penalty relaxation.
    @test a.rho[1]*a.w.problem.A[1,1]+a.rho[2]*a.w.problem.A[2,1]==0
    @test checkpair(a,b,:C)==(:value,false)
   end
  end
 end
end
