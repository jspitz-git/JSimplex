from pathlib import Path
import sys,shutil,json
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
c.need(c.read('admission.json')['accepted'] is False,'preserved offline rejection')
(D/'extra-tests.jl').write_text('''function extra_correctness(::Type{T}) where T
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
''')
s=(D/'driver.jl').read_text().replace('include(joinpath(@__DIR__,"fixtures.jl"))','include(joinpath(@__DIR__,"fixtures.jl"))\ninclude(joinpath(@__DIR__,"extra-tests.jl"))').replace('t=@timed correctness(T);','t=@timed begin;correctness(T);extra_correctness(T);end;')
(D/'driver-reviewed.jl').write_text(s)
(D/'common_reviewed.py').write_text((D/'common.py').read_text().replace("'contract.json'","'contract-reviewed.json'").replace("'pins.json'","'pins-reviewed.json'"))
(D/'launch-reviewed.py').write_text((D/'launch.py').read_text().replace('from common import','from common_reviewed import').replace("'contract.json'","'contract-reviewed.json'").replace("'pins.json'","'pins-reviewed.json'").replace("'admission.json'","'admission-reviewed.json'"))
co=c.read('contract.json');co['command']=[x.replace(str(D/'driver.jl'),str(D/'driver-reviewed.jl')) for x in co['command']];c.put('contract-reviewed.json',co)
c.put('review-fix.json',dict(candidates_unchanged=True,grid_unchanged=True,fixes=['twofloatmax signeddirections/currentand512 overflow and finitecaptie/freshowner checks','512rho input preservation','exactzero but conservative straddlinginterval/unbounded reject'],bindings={str(D/n):c.sha(D/n) for n in ['changes.json','driver.jl','driver-reviewed.jl','fixtures.jl','extra-tests.jl','contract-reviewed.json','common_reviewed.py','launch-reviewed.py']}))
shutil.copyfile(__file__,D/'review-fix.py')
paths=set(c.read('pins.json')['inventory']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
c.put('pins-reviewed.json',dict(files=sorted(paths),trees=c.read('pins.json')['trees'],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
import common_reviewed as cc;cc.unchanged();cc.put('reviewed-host.json',cc.host());print('reviewed',len(paths),'pins; noJulia')
