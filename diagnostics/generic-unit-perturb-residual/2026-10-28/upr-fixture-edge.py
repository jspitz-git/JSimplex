from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');p=D/'fixtures.jl';s=p.read_text()
s=s.replace(' fields=(x.values,x.multipliers,x.primal,x.dual)\n [[sameowners(owners(v),owners(w)) for v in a,w in b] for a in fields,b in fields]',' m=length(x.multipliers);n=length(x.values)-m\n (Tuple(sameowners(owners(x.values[n+i]),owners(x.primal[i])) for i in 1:m),Tuple(sameowners(owners(x.multipliers[i]),owners(x.dual[n+i])) for i in 1:m))')
s=s.replace('if T<:Rational&&w==1;','if T<:Rational&&w==1&&old[1]===:value;')
needle='  # Hand-derived lifted residual:'
extra='''  if T<:AbstractFloat
   for scope in (:dual,:primal)
    # A second level and the no-new-observation guard retain all original decisions.
    a=fixture(T,16,:dense,:mixed,scope);b=fixture(T,16,:dense,:mixed,scope)
    whole(Val(:original),a);whole(Val(:B),b)
    @test same(outputstate(a),outputstate(b))
    @test whole(Val(:original),a)==whole(Val(:B),b)==0
    for v in (a,b);J.observe_progress!(v.monitor;objective=one(T),primal_violation=zero(T),dual_violation=one(T),primal_step=zero(T),dual_step=zero(T));end
    @test whole(Val(:original),a)==whole(Val(:B),b)
    @test same(outputstate(a),outputstate(b))
    for tag in (Val(:original),Val(:B))
     v=fixture(T,16,:sparse,:mixed,scope);sentinel=ErrorException("unit scale callback");saved=deepcopy((v.w.costs,v.w.reduced_costs,v.w.lower,v.w.upper))
     caught=try
      if scope===:dual;modof(tag).perturb_dual_costs!(v.w,v.monitor,v.journal,v.policy;stop_requested=()->throw(sentinel))
      else;modof(tag).perturb_primal_bounds!(v.w,v.monitor,v.journal,v.policy;stop_requested=()->throw(sentinel));end
      nothing
     catch e;e;end
     @test caught===sentinel;@test same(saved,(v.w.costs,v.w.reduced_costs,v.w.lower,v.w.upper))
    end
   end
  end
  if T===Rational{BigInt}
   for c in (T(1,0),T(-1,0)),w in (T(1),T(3,2),T(0))
    @test same(capture(()->UPRReference._primal_weighted_score(c,w)),capture(()->UPRA._primal_weighted_score(c,w)))
   end
  end
  # Empty lifted model and retained output scalar relationships are ordinary values.
  e=J._initialize_workspace_state(LinearProblem(spzeros(T,0,0),T[]),SolverOptions(T;verbose=false))
  for mod in (UPRReference,UPRC)
   r=mod._lp_residual_values(T,e,T[],T[]);@test isempty(r.values)&&isempty(r.multipliers)&&isempty(r.primal)&&isempty(r.dual)
  end
  if T===BigFloat
   a=fixture(T,16,:dense,:mixed,:outer);b=fixture(T,16,:dense,:mixed,:outer)
   z=setprecision(BigFloat,512) do;1+ldexp(BigFloat(1),-400);end
   a.values[2]=z;b.values[2]=deepcopy(z);@test checkpair(a,b,:C)[1]===:value
  end
'''
s=s.replace(needle,extra+needle)
p.write_text(s)
# Preserve self-contained fixture setup sources as cold author records before sealing.
for src in ['/tmp/upr-driver-prepare.py','/tmp/upr-fixture-edge.py']:
 q=D/Path(src).name;q.write_bytes(Path(src).read_bytes())
