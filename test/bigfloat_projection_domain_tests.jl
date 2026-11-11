using JSimplex,SparseArrays,Test,Serialization,SHA
_bf_screen_digest(x)=begin io=IOBuffer();serialize(io,x);bytes2hex(sha256(take!(io))) end
function _bf_screen_workspace(bits;bad=false)
    m=32;n=64
    p=LinearProblem(sparse(fill(BigFloat(.5),m,n)),zeros(BigFloat,n);row_lower=zeros(BigFloat,m),row_upper=zeros(BigFloat,m),column_lower=fill(-one(BigFloat),n),column_upper=ones(BigFloat,n))
    w=JSimplex._initialize_workspace_state(p,SolverOptions(BigFloat;algorithm=:primal,presolve=false,simplex_strategy=:legacy,verbose=false))
    fill!(w.primal,zero(BigFloat));fill!(w.scratch.row_solution,zero(BigFloat))
    if bad
        w.problem.row_lower[1]=JSimplex.Bound(one(BigFloat));w.problem.row_upper[1]=JSimplex.Bound(one(BigFloat))
    end
    w
end
# Compare the screen to the original preparation's exact row predicate.
function _bf_screen_original_row_test(w,row,anchor)
 n=size(w.problem.A,2);i=n+row;t=w.options.primal_tolerance
 lo,hi=JSimplex._joint_primal_interval(w.lower[i],w.upper[i],t)
 if w.basis.states[i]==JSimplex.BASIC
  radius=BigFloat(8)*max(t,eps(BigFloat)*max(one(BigFloat),abs(anchor)))
  lo=max(lo,anchor-radius);hi=min(hi,anchor+radius)
  lo<=hi || return false
 else
  lo=hi=w.primal[i]
 end
 ml,mu=w.problem.row_lower[row],w.problem.row_upper[row]
 isfinite(ml)&&(lo=max(JSimplex.bound_value(ml),lo))
 isfinite(mu)&&(hi=min(JSimplex.bound_value(mu),hi))
 JSimplex._ResidualProjection.difference(hi,lo,zero(BigFloat),BigFloat(2)*t)>=zero(BigFloat)
end
@testset "Reject only outside original full band, including prediction anchors" begin
 for bits in (32,64,128,240,256,512)
  setprecision(BigFloat,bits) do
   for basic in (false,true),sign in (-1,1),q in (0,1,2,2.5,3,3.5,4,10)
    w=_bf_screen_workspace(bits);n=size(w.problem.A,2);i=n+1;t=w.options.primal_tolerance
    w.basis.states[i]=basic ? JSimplex.BASIC : JSimplex.AT_LOWER
    v=BigFloat(sign)*BigFloat(q)*t
    w.problem.row_lower[1]=JSimplex.Bound(v);w.problem.row_upper[1]=JSimplex.Bound(v)
    before=_bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.lower,w.upper,w.problem,w.options,w.progress.numerical_policy))
    possible=JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false)
    @test _bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.lower,w.upper,w.problem,w.options,w.progress.numerical_policy))==before
    for anchor in (-100t,-8t,zero(BigFloat),8t,100t)
     @test possible || !_bf_screen_original_row_test(w,1,anchor)
    end
    # 2.5*t remains inside the BASIC preparation's complete 3*t reach.
    if basic && q==2.5;@test possible;end
    if q>=4;@test !possible;end
    # A valid owned journal uses working bounds exclusively.
    @test JSimplex._ResidualProjection.row_domains_compatible(w,()->false,true)
   end
   # Infinite sides and looser working domains cannot be falsely rejected.
   w=_bf_screen_workspace(bits);i=size(w.problem.A,2)+1
   w.lower[i]=JSimplex.Bound{BigFloat}(nothing);w.upper[i]=JSimplex.Bound{BigFloat}(nothing)
   w.problem.row_lower[1]=JSimplex.Bound(BigFloat(1));w.problem.row_upper[1]=JSimplex.Bound(BigFloat(2))
   @test JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false)
   # Stored precision 320 at active 32..512, exact boundary retained.
   large=setprecision(BigFloat,320) do;BigFloat(2)^100+1;end
   w=_bf_screen_workspace(bits);i=size(w.problem.A,2)+1
   w.lower[i]=w.upper[i]=JSimplex.Bound(large);w.problem.row_lower[1]=w.problem.row_upper[1]=JSimplex.Bound(deepcopy(large))
   before=_bf_screen_digest((w.lower,w.upper,w.problem))
   @test JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false)
   @test _bf_screen_digest((w.lower,w.upper,w.problem))==before && precision(w.lower[i].value)==320
  end
 end
end

@testset "Domain rejection, predictions and stop preserve the full point" begin
    setprecision(BigFloat,128) do
        for prediction in (nothing,zeros(BigFloat,32),fill(BigFloat(99),32),BigFloat[],BigFloat[NaN])
            w=_bf_screen_workspace(128;bad=true)
            before=_bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.lower,w.upper,w.options))
            @test !JSimplex._try_joint_primal_point_recovery!(w,()->false,prediction)
            @test _bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.lower,w.upper,w.options))==before
        end
        m=256
        p=LinearProblem(spzeros(BigFloat,m,1),zeros(BigFloat,1);row_lower=zeros(BigFloat,m),row_upper=zeros(BigFloat,m))
        for throwing in (false,true)
            w=JSimplex._initialize_workspace_state(p,SolverOptions(BigFloat;algorithm=:primal,presolve=false,simplex_strategy=:legacy,verbose=false))
            fill!(w.primal,zero(BigFloat));fill!(w.scratch.row_solution,zero(BigFloat))
            before=_bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.options));calls=Ref(0)
            stop=()->begin calls[]+=1;if calls[]==2;throwing&&error("screen stop");return true;end;false;end
            if throwing;@test_throws ErrorException JSimplex._try_joint_primal_point_recovery!(w,stop)
            else;@test !JSimplex._try_joint_primal_point_recovery!(w,stop);end
            @test _bf_screen_digest((w.primal,w.scratch.row_solution,w.basis,w.options))==before
        end
    end
end
@testset "Finite tolerance with overflowing double remains unresolved" begin
 setprecision(BigFloat,128) do
  old_emax=ccall((:mpfr_get_emax,Base.MPFR.libmpfr),Clong,())
  env=(precision(BigFloat),rounding(BigFloat))
  try
   @test ccall((:mpfr_set_emax,Base.MPFR.libmpfr),Cint,(Clong,),128)==0
   t=ldexp(BigFloat(1.5),127)
   @test isfinite(t) && isinf(BigFloat(2)*t)
   p=LinearProblem(sparse(reshape(BigFloat[1],1,1)),zeros(BigFloat,1);row_lower=[t],row_upper=[t])
   o=SolverOptions(BigFloat;algorithm=:primal,presolve=false,simplex_strategy=:legacy,primal_tolerance=t,verbose=false)
   w=JSimplex._initialize_workspace_state(p,o);w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.FREE_NONBASIC])
   w.primal.=BigFloat[t/2,0];w.lower[2]=w.upper[2]=JSimplex.Bound(zero(BigFloat));w.scratch.row_solution.=[w.primal[1]]
   @test JSimplex._ResidualProjection.certified(w)
   before=_bf_screen_digest((w.primal,w.lower,w.upper,w.problem,w.options))
   outcome=try JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false) catch e;e;end
   @test outcome===true
   @test JSimplex._try_joint_primal_point_recovery!(w,()->false)
   @test _bf_screen_digest((w.primal,w.lower,w.upper,w.problem,w.options))==before
  finally
   @test ccall((:mpfr_set_emax,Base.MPFR.libmpfr),Cint,(Clong,),old_emax)==0
  end
  @test ccall((:mpfr_get_emax,Base.MPFR.libmpfr),Clong,())==old_emax
  @test env==(precision(BigFloat),rounding(BigFloat))
 end
end
@testset "Huge exponents use no rational conversion in the screen" begin
 setprecision(BigFloat,128) do
  huge=ldexp(one(BigFloat),1000000)
  p=LinearProblem(sparse(reshape(BigFloat[1],1,1)),zeros(BigFloat,1);row_lower=[huge],row_upper=[huge])
  w=JSimplex._initialize_workspace_state(p,SolverOptions(BigFloat;algorithm=:primal,presolve=false,simplex_strategy=:legacy,verbose=false));w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.FREE_NONBASIC]);fill!(w.primal,zero(BigFloat));w.lower[2]=w.upper[2]=JSimplex.Bound(zero(BigFloat))
  @test !JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false)
 end
end
@testset "Unequal stored-320-bit bounds and tolerance at mixed working precision" begin
 for bits in (32,64,128,240,512),factor in (2.5,4)
  w=setprecision(BigFloat,320) do
   t=BigFloat("1e-7");v=BigFloat(factor)*t
   p=LinearProblem(sparse(reshape(BigFloat[1],1,1)),zeros(BigFloat,1);row_lower=[v],row_upper=[v])
   o=SolverOptions(BigFloat;algorithm=:primal,presolve=false,simplex_strategy=:legacy,primal_tolerance=t,verbose=false)
   z=JSimplex._initialize_workspace_state(p,o);fill!(z.primal,zero(BigFloat));z.lower[2]=z.upper[2]=JSimplex.Bound(zero(BigFloat));z
  end
  setprecision(BigFloat,bits) do
   before=_bf_screen_digest((w.primal,w.lower,w.upper,w.problem,w.options))
   @test precision(w.options.primal_tolerance)==precision(w.problem.row_lower[1].value)==320
   @test JSimplex._ResidualProjection.row_domains_compatible(w,()->false,false)==(factor==2.5)
   @test _bf_screen_digest((w.primal,w.lower,w.upper,w.problem,w.options))==before
  end
 end
end