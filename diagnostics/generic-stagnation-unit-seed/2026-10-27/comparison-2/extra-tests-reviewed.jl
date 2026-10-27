function extra_correctness(::Type{T}) where T
 @testset "Stagnation invalidation and seed ownership $T" begin
  for mod in (SSUReference,SSUA)
   @test mod._observe_stagnation!((progress=(numerical_policy=(adaptive_stalling=false,),),),:primal,0,0)===:progress
  end
  for scope in (:values,:observe,:observe_cold,:observe_same)
   a=fixture(T,0,0,scope,:sparse,:free);b=fixture(T,0,0,scope,:sparse,:free);checkpair(a,b,:A)
  end
  # Ordinary primal cost-context rebuild, bound invalidation, same-iteration and
  # nonfinite early return must retain the complete outer behavior.
  for change in (:cost,:bound,:nonfinite,:short_primal,:short_weights)
   a=fixture(T,8,4,:observe,:sparse,:free);b=fixture(T,8,4,:observe,:sparse,:free)
   for v in (a,b)
    if change===:cost;v.w.costs[1]+=one(T)
    elseif change===:bound;v.w.upper[end]=J.Bound(T(3))
    elseif change===:nonfinite&&T<:AbstractFloat;v.w.primal[1]=T(Inf)
    elseif change===:short_primal;resize!(v.w.primal,1)
    elseif change===:short_weights;resize!(v.w.pricing_weights,1)
    end
   end
   checkpair(a,b,:A)
  end
  for arm in (:B,:C,:BC),which in (:weights,:flags)
   a=fixture(T,8,4,:init,:sparse,:slack);b=fixture(T,8,4,:init,:sparse,:slack)
   for v in (a,b)
    if which===:weights;resize!(v.w.pricing_weights,9)
    else;resize!(v.w.scratch.steepest_valid,9)
    end
   end
   z=checkpair(a,b,arm;reset_state=false)
   @test T===Rational{Int64} ? z[1]===:value : z[1]===:error&&z[2]===BoundsError
  end
  if T===BigFloat
   for scope in (:values,:observe),whichfield in (:primal,:cost,:price,:bound)
    a=fixture(T,8,4,scope,:sparse,:free);b=fixture(T,8,4,scope,:sparse,:free)
    for v in (a,b)
     value=setprecision(BigFloat,512) do;BigFloat(3//7);end
     if whichfield===:primal;v.w.primal[end]=value
     elseif whichfield===:cost;v.w.costs[1]=value
     elseif whichfield===:price;v.w.reduced_costs[1]=value
     else;v.w.upper[end]=J.Bound(value)
     end
    end
    checkpair(a,b,:A)
   end
   # Real observer: a window event can mutate bounds or throw. Cache is
   # invocation-local, so the next context must be checked/rebuilt normally.
   for action in (:mutate,:throw)
    sentinel=ErrorException("SSU observer sentinel");counts=[Ref(0),Ref(0)];hits=[Ref(0),Ref(0)];threw=false
    function obs(counter,hit)
     (reason,w)->begin
      counter[]+=1
      if reason===:stagnation_watch
       hit[]+=1
       action===:throw&&throw(sentinel)
       w.upper[end]=J.Bound(BigFloat(7))
      end
      nothing
     end
    end
    a=fixture(T,4,2,:observe,:sparse,:free;observer=obs(counts[1],hits[1]));b=fixture(T,4,2,:observe,:sparse,:free;observer=obs(counts[2],hits[2]))
    for i in 2:6
     a.w.iterations=b.w.iterations=i
     x=try;(:value,SSUReference._observe_stagnation!(a.w,:primal,a.steps...));catch e;(:error,typeof(e),e isa J.DiagnosticObserverFailure&&e.cause===sentinel);end
     y=try;(:value,SSUA._observe_stagnation!(b.w,:primal,b.steps...));catch e;(:error,typeof(e),e isa J.DiagnosticObserverFailure&&e.cause===sentinel);end
     @test same(x,y)&&same(outputs(a),outputs(b))
     @test counts[1][]==counts[2][]
     if x[1]===:error;@test x[3]===true;threw=true;break;end
    end
    @test hits[1][]==hits[2][]&&hits[1][]>0
    @test threw==(action===:throw)
   end
  elseif T===Rational{BigInt}
   for pair in ((BigInt(1),BigInt(0)),(BigInt(2),BigInt(2)),(BigInt(-1),BigInt(-1)),(BigInt(-1),BigInt(1)))
    a=fixture(T,4,2,:unit,:sparse,:positive);b=fixture(T,4,2,:unit,:sparse,:positive)
    for v in (a,b);v.w.problem.A.nzval[v.w.problem.A.colptr[1]]=Base.unsafe_rational(copy(pair[1]),copy(pair[2]));end
    checkpair(a,b,:B)
   end
  end
 end
end
