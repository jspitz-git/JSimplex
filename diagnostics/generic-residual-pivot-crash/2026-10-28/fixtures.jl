using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
modof(::Val{:original})=RPCReference
modof(::Val{:A})=RPCA
modof(::Val{:B})=RPCB
modof(::Val{:C})=RPCC
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
statevalues(s)=Tuple(getfield(s,k) for k in fieldnames(typeof(s)))
function fixture(::Type{T},n,density,shape,scope;mode=:structural,recycled=false,cap=8) where T
 if scope===:update
  f=J.PFIFactorization(spdiagm(0=>ones(T,n)))
  column=zeros(T,n)
  for i in 1:n
   if i==1||density===:dense||i%4==0
    sign=shape===:negative||shape===:mixed&&iseven(i) ? -1 : 1
    column[i]=T(sign*((i%5)+1)//8)
   end
  end
  if recycled
   J.replace_column!(f,column,1;zero_tolerance=zero(T));push!(f.recycled_updates,pop!(f.updates))
  end
  return (scope=scope,f=f,column=column,recycled=recycled,tol=zero(T))
 end
 A=zeros(T,n,n)
 for j in 1:n,i in 1:n
  if i==j||density===:dense||(i+j)%7==0
   A[i,j]=i==j ? one(T) : T(((i+j)%3+1)//(16*n))
  end
 end
 p=LinearProblem(sparse(A),zeros(T,n);column_lower=fill(-T(8),n),column_upper=fill(T(8),n),row_lower=fill(-T(8),n),row_upper=fill(T(8),n))
 o=SolverOptions(T;verbose=false,basis_update=:pfi,pricing=:dantzig)
 pol=J.NumericalPolicy(T;refactor_timing=false,solve_refinement=false,recovery=false,max_pivot_candidates=cap)
 w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 if scope===:residual
  if mode===:structural
   fill!(w.basis.states,J.AT_LOWER);w.basis.basic_indices.=1:n;w.basis.states[1:n].=J.BASIC
  end
  rho=[T((shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*(i%5+1)//16) for i in 1:n]
  return (scope=scope,w=w,rho=rho,leaving=1)
 end
 for j in w.basis.basic_indices;w.primal[j]=T(16);end
 column=[T((shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1)*((i*7)%n+1)//16) for i in 1:n]
 return (scope=scope,w=w,column=column,rows=Int[],policy=pol,cap=cap)
end
function reset!(v)
 if v.scope===:update
  if v.recycled&&!isempty(v.f.updates)
   @assert isempty(v.f.recycled_updates)
   push!(v.f.recycled_updates,pop!(v.f.updates))
  elseif !v.recycled
   empty!(v.f.updates)
  end
 end
 nothing
end
@noinline function whole(tag::A,v::V) where {A,V}
 m=modof(tag)
 v.scope===:residual&&return m._dual_row_residual_ratio(v.w,v.rho,v.leaving)
 v.scope===:update&&return m.replace_column!(v.f,v.column,1;zero_tolerance=v.tol)
 return m._crash_rows!(v.rows,v.w,v.column,v.policy)
end
function key(v,result)
 v.scope===:residual&&return Float64(result)
 v.scope===:crash&&return sum(result;init=0)
 eta=only(result.updates)
 return sum(Float64,eta.values;init=0.0)+sum(eta.indices;init=0)
end
@noinline function timed(tag::A,v::V) where {A,V}
 t=@timed whole(tag,v);k=@timed key(v,t.value)
 merge(cost(t),Dict("result"=>k.value,"capture_preparation"=>cost(k)))
end
function inputvalues(v)
 if v.scope===:update
  f=v.f
  return (v.column,v.tol,f.work,f.base,Tuple(getfield(f.base.factorization,k) for k in fieldnames(typeof(f.base.factorization)) if getfield(f.base.factorization,k) isa AbstractArray{<:Real}))
 end
 w=v.w
 return (w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.basis.basic_indices,w.basis.states,w.costs,w.primal,w.reduced_costs,w.lower,w.upper,w.pricing_weights,w.scratch.tau,w.scratch.row_rhs,w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,w.progress.objective,statevalues(w.options),statevalues(w.progress.numerical_policy),v.scope===:residual ? v.rho : v.column)
end
# Backend itself is retained for identity checks, its numerical arrays are captured separately.
function valuesonly(x)
 x isa Tuple&&return map(valuesonly,x)
 x isa Union{J.UMFPACKBackend,J.DenseLUBackend,J.Float32LUBackend,J.MarkowitzBackend}&&return typeof(x)
 return x
end
function owners(x)
 x isa BigFloat&&return (x,)
 x isa Rational{BigInt}&&return (numerator(x),denominator(x))
 x isa J.Bound&&return owners(x.value)
 x isa AbstractArray&&return (x,Tuple(owners(y) for y in x))
 x isa Tuple&&return Tuple(owners(y) for y in x)
 return x isa Real||x isa Symbol||x isa String||x===nothing ? nothing : x
end
sameowners(a,b)=a===b
sameowners(a::Tuple,b::Tuple)=length(a)==length(b)&&all(sameowners(x,y) for (x,y) in zip(a,b))
function resultvalue(v,x)
 x[1]===:error&&return x
 v.scope===:update&&return (:value,Tuple((eta.indices,eta.values,eta.pivot_row) for eta in v.f.updates))
 return x
end
function checkpair(a,b,arm)
 reset!(a);reset!(b)
 va=deepcopy(valuesonly(inputvalues(a)));vb=deepcopy(valuesonly(inputvalues(b)));oa=owners(inputvalues(a));ob=owners(inputvalues(b));ambient=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test same(resultvalue(a,x),resultvalue(b,y))
 @test ambient==(precision(BigFloat),rounding(BigFloat))
 @test same(va,valuesonly(inputvalues(a)));@test same(vb,valuesonly(inputvalues(b)))
 @test sameowners(oa,owners(inputvalues(a)));@test sameowners(ob,owners(inputvalues(b)))
 if a.scope===:update&&x[1]===:value
  @test x[2]===a.f&&y[2]===b.f
  @test a.f.updates[1].indices!==a.column&&b.f.updates[1].indices!==b.column
 elseif a.scope===:crash&&x[1]===:value
  @test x[2]===a.rows&&y[2]===b.rows
 end
 return x
end
function correctness(::Type{T}) where T
 @testset "ordinary residual pivot crash $(T)" begin
  if T<:AbstractFloat
   for basis in (:structural,:slack),shape in (:positive,:negative,:mixed),density in (:sparse,:dense)
    a=fixture(T,8,density,shape,:residual;mode=basis);b=fixture(T,8,density,shape,:residual;mode=basis)
    @test checkpair(a,b,:A)[1]===:value
   end
   for tag in (Val(:original),Val(:A))
    a=fixture(T,4,:sparse,:positive,:residual;mode=:slack);fill!(a.rho,zero(T));a.rho[1]=-one(T)
    x=whole(tag,a);y=whole(tag,a);@test iszero(x);@test !signbit(x)
    T===BigFloat&&(@test x!==y;@test all(z->x!==z,a.rho))
    resize!(a.rho,3);@test_throws DimensionMismatch whole(tag,a)
   end
  end
  for shape in (:positive,:negative,:mixed),density in (:sparse,:dense),recycled in (false,true)
   a=fixture(T,8,density,shape,:update;recycled);b=fixture(T,8,density,shape,:update;recycled)
   @test checkpair(a,b,:B)[1]===:value
  end
  for tag in (Val(:original),Val(:B))
   a=fixture(T,4,:dense,:positive,:update);a.column.=T.([2,1//2,0,-1]);whole(tag,a);eta=only(a.f.updates)
   @test eta.indices==[1,2,4];@test eta.values==T.([1//2,-1//4,1//2])
   out=zeros(T,4);J.forward_solve!(out,a.f,a.column);@test out==T.([1,0,0,0])
   reset!(a);a.column[1]=zero(T);@test_throws LinearAlgebra.ZeroPivotException whole(tag,a)
   @test isempty(a.f.updates)
   a.column[1]=one(T);bad=merge(a,(tol=-one(T),));@test_throws ArgumentError whole(tag,bad)
  end
  for shape in (:positive,:negative,:mixed),density in (:sparse,:dense),cap in (1,8)
   a=fixture(T,8,density,shape,:crash;cap);b=fixture(T,8,density,shape,:crash;cap)
   @test checkpair(a,b,:C)[1]===:value
  end
  for tag in (Val(:original),Val(:C))
   a=fixture(T,4,:dense,:positive,:crash;cap=2);a.column.=T.([1,4,2,4]);@test whole(tag,a)==[2,4]
   fill!(a.column,zero(T));@test isempty(whole(tag,a))
   a.column.=T.([1,4,2,4]);fill!(a.w.primal,zero(T));@test isempty(whole(tag,a))
   a=fixture(T,4,:dense,:mixed,:crash;cap=2);cv=@view a.column[:];@test modof(tag)._crash_rows!(a.rows,a.w,cv,a.policy)==RPCReference._crash_rows!(Int[],a.w,cv,a.policy)
  end
  if T<:AbstractFloat
   for bad in (T(Inf),T(-Inf),T(NaN))
    a=fixture(T,4,:dense,:mixed,:residual);b=fixture(T,4,:dense,:mixed,:residual);a.rho[2]=bad;b.rho[2]=bad
    @test checkpair(a,b,:A)[2]==T(Inf)
   end
   for tag in (Val(:original),Val(:A))
    a=fixture(T,4,:dense,:mixed,:residual);a.w.basis.basic_indices[2]=100
    @test_throws BoundsError whole(tag,a)
   end
  end
  for tag in (Val(:original),Val(:B))
   a=fixture(T,4,:dense,:mixed,:update;recycled=true);saved=(only(a.f.recycled_updates).indices,only(a.f.recycled_updates).values)
   whole(tag,a);@test only(a.f.updates).indices===saved[1];@test only(a.f.updates).values===saved[2]
  end
  if T===BigFloat
   for bits in (64,128,512),sign in (-1,1)
    stored=setprecision(BigFloat,bits) do;BigFloat(sign)*(1+ldexp(BigFloat(1),-53)+ldexp(BigFloat(1),-400));end
    before=deepcopy(stored);old=RPCReference._pivot_magnitude(stored);new=RPCB._pivot_magnitude(stored)
    @test same(old,new);@test same(stored,before)
   end
   for scope in (:residual,:crash)
    arm=scope===:residual ? :A : :C
    a=fixture(T,8,:dense,:mixed,scope);b=fixture(T,8,:dense,:mixed,scope)
    stored=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-53)+ldexp(BigFloat(1),-400);end
    if scope===:residual;a.rho[2]=stored;b.rho[2]=deepcopy(stored)
    else;a.column[2]=stored;b.column[2]=deepcopy(stored);end
    @test checkpair(a,b,arm)[1]===:value
   end
   for x in (BigFloat(0),-BigFloat(0),BigFloat(Inf),BigFloat(-Inf),BigFloat(NaN))
    @test same(RPCReference._pivot_magnitude(x),RPCB._pivot_magnitude(x))
   end
  end
 end
 nothing
end
