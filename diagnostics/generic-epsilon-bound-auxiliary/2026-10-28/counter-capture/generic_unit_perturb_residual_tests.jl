module GenericUnitPerturbResidualTests
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
module UPRReference
import JSimplex
using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,Bound,bound_value,PerturbationJournal,BoundPerturbationState,StagnationMonitor,LPResiduals,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,
    _is_exact,_is_fixed,_primal_direction_magnitude,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,_record_full_pricing!,
    _check_perturbation_owner,_perturbation_stopped,_with_recovery_precision,_finite_workspace,dual_infeasibility,primal_infeasibility,_invalidate_basis_checkpoints!,_reset_workspace_stagnation!,_simplex_event!,_copy_working_values,_working_value_bits,_lp_residual_bits
function _primal_weighted_score(reduced_cost::T,
                                weight::Tuple{I,T}) where {I<:Integer,T<:AbstractFloat}
    cost_mantissa, cost_exponent = frexp(abs(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end

# Positive scores keep the original owner without a discarded negation.
function _primal_weighted_score(reduced_cost::BigFloat,
                                weight::Tuple{I,BigFloat}) where {I<:Integer}
    cost_mantissa, cost_exponent = frexp(_primal_direction_magnitude(reduced_cost))
    weight_exponent, weight_mantissa = weight
    score_mantissa, correction = frexp(cost_mantissa / weight_mantissa)
    return (cost_exponent - weight_exponent + correction, score_mantissa)
end


function _primal_weighted_score(reduced_cost::T, weight::T) where {T<:AbstractFloat}
    mantissa, exponent = frexp(weight)
    return _primal_weighted_score(reduced_cost, (exponent, mantissa))
end
_primal_weighted_score(reduced_cost::Rational, weight::Rational) =
    big(reduced_cost)^2 / big(weight)

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < zero(T) ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = (state == AT_LOWER && reduced_cost < -tolerance) ||
                    (state == AT_UPPER && reduced_cost > tolerance) ||
                    (state == FREE_NONBASIC && abs(reduced_cost) > tolerance)
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < zero(T) ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end

function _primal_entering(workspace::SimplexWorkspace{T}, tolerance::T) where {T<:Union{BigFloat,Rational{BigInt}}}
    _prepare_auto_pricing!(workspace,:primal)
    state = workspace.scratch.pricing
    isnothing(state) || (state.pricing_passes += 1)
    if _partial_pricing_enabled(workspace,:primal)
        entering = _select_workspace_pool!(workspace,:primal;tolerance)
        direction = entering == 0 ? zero(T) :
            (workspace.reduced_costs[entering] < 0 ? one(T) : -one(T))
        return entering,direction
    end
    pricing = _effective_pricing(workspace,:primal)
    pricing == :steepest_edge && _primal_initialize_steepest!(workspace)
    entering = 0
    scored = 0
    direction = zero(T)
    best_score = _primal_dantzig_score(one(T))
    negative_tolerance = tolerance
    negative_ready = false
    reuse_negative = pricing === :dantzig || pricing === :devex
    for index in eachindex(workspace.basis.states)
        state = workspace.basis.states[index]
        state == BASIC && continue
        index in workspace.scratch.rejected_entering && continue
        _is_fixed(workspace.lower[index], workspace.upper[index]) && continue
        reduced_cost = workspace.reduced_costs[index]
        improving = if state == AT_LOWER
            if reuse_negative
                if !negative_ready
                    negative_tolerance = -tolerance
                    negative_ready = true
                end
                reduced_cost < negative_tolerance
            else
                reduced_cost < -tolerance
            end
        else
            (state == AT_UPPER && reduced_cost > tolerance) ||
            (state == FREE_NONBASIC && _primal_direction_magnitude(reduced_cost) > tolerance)
        end
        improving || continue
        scored += 1
        score = if pricing == :dantzig
            _primal_dantzig_score(reduced_cost)
        else
            weight = pricing == :steepest_edge && !workspace.scratch.steepest_valid[index] ?
                _primal_steepest_weight!(workspace, index) : workspace.pricing_weights[index]
            _primal_weighted_score(reduced_cost, weight)
        end
        if entering == 0 || score > best_score
            entering = index
            direction = reduced_cost < 0 ? one(T) : -one(T)
            best_score = score
        end
    end
    _record_full_pricing!(workspace.progress.diagnostics,length(workspace.basis.states),scored)
    return entering, direction
end


function perturb_dual_costs!(ws,monitor::StagnationMonitor,
                            journal::PerturbationJournal{T},policy;
                            stop_requested=nothing)::Int where T
    _check_perturbation_owner(ws,journal)
    _is_exact(T) === Val(true) && return 0
    policy.adaptive_dual_perturbation && ws.scratch.dual_perturbation_allowed || return 0
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    (monitor !== journal.last_monitor || monitor.observations > journal.last_observation) &&
        journal.level < 3 || return 0
    ws.iterations >= journal.cooldown_until || return 0
    _perturbation_stopped(stop_requested) && return -1
    return _with_recovery_precision(ws,ws) do
        _perturb_dual_costs_precise!(ws,monitor,journal,policy,stop_requested)
    end
end

function _perturb_dual_costs_precise!(ws,monitor,journal::PerturbationJournal{T},
                                    policy,stop_requested)::Int where T
    tolerance = ws.options.dual_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return 0
    _finite_workspace(ws) && dual_infeasibility(ws) <= tolerance || return 0
    level = journal.level+1
    cap = T(512)*tolerance
    isfinite(cap) || return 0
    costs,prices = copy(ws.costs),copy(ws.reduced_costs)
    shifted = 0
    for j in eachindex(ws.basis.states)
        j % 1024 == 0 && _perturbation_stopped(stop_requested) && return -1
        state = ws.basis.states[j]
        (state == AT_LOWER || state == AT_UPPER) || continue
        _is_fixed(ws.lower[j],ws.upper[j]) && continue
        old_cost,price = ws.costs[j],ws.reduced_costs[j]
        direction = state == AT_LOWER ? one(T) : -one(T)
        local_scale = one(T)+min(abs(old_cost),one(T))
        target = min(cap,tolerance*T(8+j%16)*local_scale*T(1 << (level-1)))
        isfinite(target) && target > tolerance || continue
        previous_shift = !isequal(old_cost,journal.original_costs[j])
        (abs(price) <= tolerance || (journal.active && previous_shift && abs(price) <= target)) || continue
        direction*price < target || continue
        requested = direction*target-price
        new_cost = old_cost+requested
        isfinite(new_cost) && new_cost != old_cost || continue
        actual = new_cost-old_cost
        isfinite(actual) && abs(actual) <= 2abs(requested) || continue
        displacement = new_cost-journal.original_costs[j]
        isfinite(displacement) && abs(displacement) <= cap || continue
        new_price = price+actual
        isfinite(new_price) && direction*new_price > tolerance || continue
        costs[j],prices[j] = new_cost,new_price
        shifted += 1
    end
    _perturbation_stopped(stop_requested) && return -1
    # Even an unrepresentable attempt consumes one level and one observation.
    journal.level = level
    journal.last_monitor = monitor
    journal.last_observation = monitor.observations
    shifted == 0 && return 0
    copyto!(journal.active_costs,costs)
    ws.costs = journal.active_costs
    copyto!(ws.reduced_costs,prices)
    journal.active = true
    ws.perturbed = true
    ws.scratch.perturbations = journal
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:perturbation)
    return shifted
end

function perturb_primal_bounds!(ws,monitor::StagnationMonitor,
                               journal::PerturbationJournal{T},policy;
                               stop_requested=nothing)::Int where T
    _check_perturbation_owner(ws,journal)
    _is_exact(T) === Val(true) && return 0
    policy.adaptive_primal_perturbation && ws.scratch.primal_perturbation_allowed || return 0
    monitor.state == :stalled && monitor.window_count == monitor.window || return 0
    ws.iterations >= journal.cooldown_until || return 0
    bounds = journal.bounds
    if !isnothing(bounds)
        (monitor !== bounds.last_monitor || monitor.observations > bounds.last_observation) &&
            bounds.level < 3 || return 0
        ws.iterations >= bounds.cooldown_until || return 0
    end
    _perturbation_stopped(stop_requested) && return -1
    return _with_recovery_precision(ws,ws) do
        _perturb_primal_bounds_precise!(ws,monitor,journal,stop_requested)
    end
end

function _expanded_basic_bound(original::Bound{T},current::Bound{T},value::T,
                               direction::T,tolerance::T,cap::T,level::Int,index::Int) where T
    isfinite(current) && isfinite(original) || return current
    abs(value-current.value) <= tolerance || return current
    scale = one(T)+min(abs(original.value),one(T))
    margin = min(cap,tolerance*T(8+index%16)*scale*T(1 << (level-1)))
    isfinite(margin) && margin > tolerance || return current
    requested = original.value+direction*margin
    isfinite(requested) || return current
    change = direction*(requested-current.value)
    change > zero(T) && change <= 2margin || return current
    displacement = direction*(requested-original.value)
    isfinite(displacement) && zero(T) < displacement <= cap || return current
    return Bound(requested)
end

function _perturb_primal_bounds_precise!(ws,monitor,journal::PerturbationJournal{T},
                                       stop_requested)::Int where T
    tolerance = ws.options.primal_tolerance
    isfinite(tolerance) && tolerance > zero(T) || return 0
    _finite_workspace(ws) && primal_infeasibility(ws) <= tolerance || return 0
    cap = T(512)*tolerance
    isfinite(cap) || return 0
    bounds = journal.bounds
    isnothing(bounds) && (bounds = BoundPerturbationState(ws))
    level = bounds.level+1
    lower,upper = copy(ws.lower),copy(ws.upper)
    shifted = 0
    for (row,j) in enumerate(ws.basis.basic_indices)
        row % 1024 == 0 && _perturbation_stopped(stop_requested) && return -1
        _is_fixed(ws.lower[j],ws.upper[j]) && continue
        lo = _expanded_basic_bound(bounds.original_lower[j],ws.lower[j],ws.primal[j],
            -one(T),tolerance,cap,level,j)
        hi = _expanded_basic_bound(bounds.original_upper[j],ws.upper[j],ws.primal[j],
            one(T),tolerance,cap,level,j)
        shifted += !isequal(lo,lower[j]) + !isequal(hi,upper[j])
        lower[j],upper[j] = lo,hi
    end
    _perturbation_stopped(stop_requested) && return -1
    bounds.level = level
    bounds.last_monitor = monitor
    bounds.last_observation = monitor.observations
    journal.bounds = bounds
    shifted == 0 && return 0
    copyto!(bounds.active_lower,lower)
    copyto!(bounds.active_upper,upper)
    ws.lower,ws.upper = bounds.active_lower,bounds.active_upper
    bounds.active = true
    ws.perturbed = true
    ws.scratch.perturbations = journal
    _invalidate_basis_checkpoints!(ws)
    _reset_workspace_stagnation!(ws)
    _simplex_event!(ws,:perturbation)
    return shifted
end

function _lp_residual_values(::Type{R}, ws, values, multipliers) where R
    m, n = size(ws.problem.A)
    length(values) == n+m && length(multipliers) == m ||
        throw(DimensionMismatch("LP residual coordinates do not match the original model"))
    v, y = _copy_working_values(R, values), _copy_working_values(R, multipliers)
    all(isfinite, v) && all(isfinite, y) || throw(ArgumentError("Nonfinite LP residual candidate"))
    primal = copy(v[n+1:end])
    dual = vcat(_copy_working_values(R, ws.problem.objective), copy(y))
    for j in 1:n, k in nzrange(ws.problem.A, j)
        i, a = ws.problem.A.rowval[k], R(ws.problem.A.nzval[k])
        primal[i] -= a*v[j]
        dual[j] -= a*y[i]
    end
    return LPResiduals(v, y, primal, dual)
end

function _lp_residuals(ws::SimplexWorkspace{T}, values, multipliers;
                       bits::Int=_lp_residual_bits(ws)) where T
    if _is_exact(T) === Val(true)
        return _lp_residual_values(T, ws, values, multipliers)
    end
    actual = max(bits, _working_value_bits(values), _working_value_bits(multipliers))
    return setprecision(BigFloat, actual) do
        _lp_residual_values(BigFloat, ws, values, multipliers)
    end
end


end

const UPRA=JSimplex
const UPRB=JSimplex
const UPRC=JSimplex
using Test,JSimplex,SparseArrays,LinearAlgebra,Statistics
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
modof(::Val{:original})=UPRReference
modof(::Val{:A})=UPRA
modof(::Val{:B})=UPRB
modof(::Val{:C})=UPRC
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
statevalues(s)=Tuple(getfield(s,k) for k in fieldnames(typeof(s)))
function owners(x)
 x isa BigFloat&&return (x,)
 x isa Rational{BigInt}&&return (numerator(x),denominator(x))
 x isa J.Bound&&return owners(x.value)
 x isa AbstractArray&&return (x,Tuple(owners(y) for y in x))
 x isa Tuple&&return Tuple(owners(y) for y in x)
 nothing
end
sameowners(a,b)=a===b
sameowners(a::Tuple,b::Tuple)=length(a)==length(b)&&all(sameowners(x,y) for (x,y) in zip(a,b))
function fixture(::Type{T},n,density,shape,scope;mode=:unit) where T
 m=min(8,max(1,n÷2));A=zeros(T,m,n)
 for j in 1:n,i in 1:m
  if j<=m
   A[i,j]=i==j ? one(T) : zero(T)
  elseif density===:dense||i==mod1(j,m)
   A[i,j]=T(((i+2j)%5+1)//16)
  end
 end
 signof(i)=shape===:negative||shape===:mixed&&isodd(i) ? -1 : 1
 if scope===:score
  c=shape===:wide&&T===Rational{BigInt} ? T((big(1)<<127)+7,(big(1)<<63)+13) : T(signof(1)*3//2)
  w=mode===:unit ? one(T) : T(3//2)
  return (scope=scope,c=c,weight=w)
 end
 objective=zeros(T,n)
 lo=fill(Bound(zero(T)),n);hi=[J._unbounded_bound(T) for _ in 1:n]
 rl=fill(Bound(zero(T)),m);ru=copy(rl)
 if scope===:dual
  rho=T[signof(i)//2 for i in 1:m];objective=transpose(A)*rho
  for j in m+1:n
   if iseven(j);lo[j]=J._unbounded_bound(T);hi[j]=Bound(zero(T));end
  end
 elseif scope===:primal
  for i in 1:m
   target=T(signof(i)//2);rl[i]=ru[i]=Bound(target)
   if isodd(i);lo[i]=Bound(target);hi[i]=J._unbounded_bound(T)
   else;lo[i]=J._unbounded_bound(T);hi[i]=Bound(target);end
  end
 end
 p=LinearProblem(sparse(A),objective;column_lower=lo,column_upper=hi,row_lower=rl,row_upper=ru)
 pricing=scope in (:devex,:steepest) ? (scope===:devex ? :devex : :steepest_edge) : :dantzig
 o=SolverOptions(T;verbose=false,basis_update=:pfi,pricing,partial_pricing=false)
 pol=J.NumericalPolicy(T;simplex_strategy=scope in (:dual,:primal) ? :adaptive : :legacy,adaptive_pricing=false,refactor_timing=false,solve_refinement=false,recovery=false,stagnation_window=2)
 w=J._initialize_workspace_state(p,o;progress=J.SimplexProgressContext(p;numerical_policy=pol))
 if scope in (:devex,:steepest)
  for j in 1:n
   price=T(signof(j)*(j%7+1)//8)
   shape===:wide&&T===Rational{BigInt}&&(price=T((big(1)<<127)+j,(big(1)<<63)+13))
   if price<0;w.basis.states[j]=J.AT_LOWER;w.lower[j]=Bound(zero(T));w.upper[j]=J._unbounded_bound(T)
   else;w.basis.states[j]=J.AT_UPPER;w.lower[j]=J._unbounded_bound(T);w.upper[j]=Bound(zero(T));end
   w.reduced_costs[j]=price
   w.pricing_weights[j]=mode===:unit||(mode===:mixed&&isodd(j)) ? one(T) : T(3//2)
  end
  w.scratch.steepest_initialized=true;fill!(w.scratch.steepest_valid,true)
  return (scope=scope,w=w)
 elseif scope in (:residual,:outer)
  values=T[signof(j)*(j%7+1)//16 for j in 1:n+m];multipliers=T[signof(j)*(j%3+1)//8 for j in 1:m]
  return (scope=scope,w=w,values=values,multipliers=multipliers)
 end
 # Genuine structural basis/recompute establishes zero prices (dual) or exact active basic bounds (primal).
 w.basis=J.Basis(collect(1:m),vcat(fill(J.BASIC,m),fill(J.AT_LOWER,n)))
 for j in m+1:n;w.basis.states[j]=isfinite(w.lower[j]) ? J.AT_LOWER : J.AT_UPPER;end
 J.recompute!(w;refactorize=true)
 monitor=J.StagnationMonitor{T}(2;tolerance=pol.solve_tolerance)
 for _ in 1:4;J.observe_progress!(monitor;objective=one(T),primal_violation=zero(T),dual_violation=one(T),primal_step=zero(T),dual_step=zero(T));end
 journal=J.PerturbationJournal(w)
 return (scope=scope,w=w,monitor=monitor,journal=journal,policy=pol,initial_costs=w.costs,initial_lower=w.lower,initial_upper=w.upper,initial_prices=copy(w.reduced_costs),initial_perturbed=w.perturbed,initial_phase=w.scratch.phase_generation)
end
function reset!(v)
 if v.scope in (:dual,:primal)
  w=v.w;j=v.journal;w.costs=v.initial_costs;w.lower=v.initial_lower;w.upper=v.initial_upper;copyto!(w.reduced_costs,v.initial_prices)
  copyto!(j.active_costs,j.original_costs);j.active=false;j.level=0;j.last_monitor=nothing;j.last_observation=0;j.cooldown_until=0;j.bounds=nothing
  w.perturbed=v.initial_perturbed;w.scratch.perturbations=nothing;w.scratch.phase_generation=v.initial_phase
 end
 nothing
end
@noinline function whole(tag::A,v::V) where {A,V}
 m=modof(tag)
 v.scope===:score&&return m._primal_weighted_score(v.c,v.weight)
 v.scope in (:devex,:steepest)&&return m._primal_entering(v.w,v.w.options.dual_tolerance)
 v.scope===:dual&&return m.perturb_dual_costs!(v.w,v.monitor,v.journal,v.policy)
 v.scope===:primal&&return m.perturb_primal_bounds!(v.w,v.monitor,v.journal,v.policy)
 T=eltype(v.values)
 v.scope===:residual&&return m._lp_residual_values(T,v.w,v.values,v.multipliers)
 return m._lp_residuals(v.w,v.values,v.multipliers)
end
function resultvalue(x)
 x isa J.LPResiduals&&return (x.values,x.multipliers,x.primal,x.dual)
 x
end
function resultkey(x)
 x isa J.LPResiduals&&return sum(Float64,x.primal;init=0.0)+sum(Float64,x.dual;init=0.0)
 x isa Tuple&&return Float64(x[1])+Float64(x[2])
 x isa Integer&&return x
 Float64(x)
end
@noinline function timed(tag::A,v::V) where {A,V}
 t=@timed whole(tag,v);k=@timed resultkey(t.value)
 merge(cost(t),Dict("result"=>k.value,"capture_preparation"=>cost(k)))
end
function inputvalues(v)
 v.scope===:score&&return (v.c,v.weight)
 w=v.w
 base=(w.problem.A.colptr,w.problem.A.rowval,w.problem.A.nzval,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.basis.basic_indices,w.basis.states,w.primal,w.pricing_weights,w.progress.start_ns,w.progress.iteration_offset,w.progress.refactorization_offset,statevalues(w.options),statevalues(w.progress.numerical_policy))
 if v.scope in (:residual,:outer);return (base,v.values,v.multipliers);end
 v.scope in (:dual,:primal)&&return (base,v.journal.original_costs,v.initial_costs,v.initial_lower,v.initial_upper)
 return (base,w.costs,w.reduced_costs)
end
function outputstate(v)
 v.scope in (:dual,:primal)||return nothing
 w=v.w;j=v.journal;b=j.bounds
 bounds=isnothing(b) ? nothing : (b.original_lower,b.original_upper,b.active_lower,b.active_upper,b.active,b.level,b.last_monitor===v.monitor,b.last_observation,b.cooldown_until,w.lower===b.active_lower,w.upper===b.active_upper)
 (w.costs,w.reduced_costs,w.lower,w.upper,w.perturbed,w.costs===j.active_costs,j.active,j.level,j.last_monitor===v.monitor,j.last_observation,j.cooldown_until,bounds,w.scratch.perturbations===j,w.scratch.phase_generation,isempty(w.scratch.checkpoints),isempty(w.scratch.recovery_rejections))
end
function sharing(x)
 m=length(x.multipliers);n=length(x.values)-m
 (Tuple(sameowners(owners(x.values[n+i]),owners(x.primal[i])) for i in 1:m),Tuple(sameowners(owners(x.multipliers[i]),owners(x.dual[n+i])) for i in 1:m))
end
function outowners(x)
 x isa J.LPResiduals||return true
 fields=(x.values,x.multipliers,x.primal,x.dual)
 all(fields[i]!==fields[j] for i in 1:4 for j in i+1:4)
end
function checkpair(a,b,arm)
 reset!(a);reset!(b);va=deepcopy(inputvalues(a));vb=deepcopy(inputvalues(b));oa=owners(inputvalues(a));ob=owners(inputvalues(b));ambient=(precision(BigFloat),rounding(BigFloat))
 x=capture(()->whole(Val(:original),a));y=capture(()->whole(Val(arm),b))
 @test same(x[1]===:value ? (:value,resultvalue(x[2])) : x,y[1]===:value ? (:value,resultvalue(y[2])) : y)
 @test ambient==(precision(BigFloat),rounding(BigFloat))
 @test same(va,inputvalues(a));@test same(vb,inputvalues(b));@test sameowners(oa,owners(inputvalues(a)));@test sameowners(ob,owners(inputvalues(b)))
 if a.scope in (:dual,:primal);@test x[1]===:value&&(eltype(a.w.primal)<:Rational ? x[2]==0 : x[2]>0);@test same(outputstate(a),outputstate(b));@test a.journal.workspace_id==objectid(a.w)&&b.journal.workspace_id==objectid(b.w);end
 if a.scope in (:residual,:outer)&&x[1]===:value
  @test outowners(x[2])&&outowners(y[2]);@test x[2].values!==a.values&&y[2].values!==b.values;@test x[2].multipliers!==a.multipliers&&y[2].multipliers!==b.multipliers
  # Original extra shallow copies share the same scalar roles across output fields.
  @test sharing(x[2])==sharing(y[2])
 end
 x
end
function correctness(::Type{T}) where T
 @testset "unit perturb residual $(T)" begin
  for shape in (:positive,:negative,:mixed),mode in (:unit,:mixed,:nonunit),scope in (:devex,:steepest)
   a=fixture(T,16,:sparse,shape,scope;mode);b=fixture(T,16,:sparse,shape,scope;mode);@test checkpair(a,b,:A)[1]===:value
  end
  for c in T.([0,1,-1,3//2,-7//4]),w in T.([1,3//2,0,-1])
   old=capture(()->UPRReference._primal_weighted_score(c,w));new=capture(()->UPRA._primal_weighted_score(c,w));@test same(old,new)
   if T<:Rational&&w==1&&old[1]===:value;@test old[2]==c*c;end
   if T===Rational{BigInt}&&isfinite(c)&&w==1
    x=UPRA._primal_weighted_score(c,w);y=UPRA._primal_weighted_score(c,w)
    @test numerator(x)!==numerator(c)&&denominator(x)!==denominator(c)
    @test numerator(x)!==numerator(w)&&denominator(x)!==denominator(w)
    @test numerator(x)!==numerator(y)&&denominator(x)!==denominator(y)
   end
  end
  for density in (:sparse,:dense),shape in (:positive,:negative,:mixed),scope in (:dual,:primal)
   a=fixture(T,16,density,shape,scope);b=fixture(T,16,density,shape,scope);out=checkpair(a,b,:B)
   @test out[1]===:value
   @test T<:Rational ? out[2]==0 : out[2]>0
  end
  for density in (:sparse,:dense),shape in (:positive,:negative,:mixed),scope in (:residual,:outer)
   a=fixture(T,16,density,shape,scope);b=fixture(T,16,density,shape,scope);@test checkpair(a,b,:C)[1]===:value
  end
  if T<:AbstractFloat
   for scope in (:dual,:primal)
    # A second level and the no-new-observation guard retain all original decisions.
    a=fixture(T,16,:dense,:mixed,scope);b=fixture(T,16,:dense,:mixed,scope)
    whole(Val(:original),a);whole(Val(:B),b)
    @test same(outputstate(a),outputstate(b))
    @test whole(Val(:original),a)==whole(Val(:B),b)==0
    for v in (a,b),_ in 1:2;J.observe_progress!(v.monitor;objective=one(T),primal_violation=zero(T),dual_violation=one(T),primal_step=zero(T),dual_step=zero(T));end
    @test whole(Val(:original),a)==whole(Val(:B),b)
    @test same(outputstate(a),outputstate(b))
    @test scope===:dual ? a.journal.level==b.journal.level==2 : a.journal.bounds.level==b.journal.bounds.level==2
    for tag in (Val(:original),Val(:B)),throw_at in (1,2)
     calls=Ref(0)
     v=fixture(T,16,:sparse,:mixed,scope);sentinel=ErrorException("unit scale callback");saved=deepcopy((v.w.costs,v.w.reduced_costs,v.w.lower,v.w.upper))
     caught=try
      if scope===:dual;modof(tag).perturb_dual_costs!(v.w,v.monitor,v.journal,v.policy;stop_requested=()->(calls[]+=1;calls[]==throw_at ? throw(sentinel) : false))
      else;modof(tag).perturb_primal_bounds!(v.w,v.monitor,v.journal,v.policy;stop_requested=()->(calls[]+=1;calls[]==throw_at ? throw(sentinel) : false));end
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
   a=fixture(T,16,:dense,:mixed,:residual);b=fixture(T,16,:dense,:mixed,:residual)
   a.values[2]=z;b.values[2]=deepcopy(z);@test checkpair(a,b,:C)[1]===:value
  end
  # Overlapping input arrays must still produce independently copied working scalars.
  p0=LinearProblem(spzeros(T,1,0),T[]);w0=J._initialize_workspace_state(p0,SolverOptions(T;verbose=false));v0=T[3//2]
  ra=UPRReference._lp_residual_values(T,w0,v0,v0);rb=UPRC._lp_residual_values(T,w0,v0,v0)
  @test same(resultvalue(ra),resultvalue(rb));@test sharing(ra)==sharing(rb)
  @test ra.values!==v0&&rb.values!==v0&&ra.multipliers!==v0&&rb.multipliers!==v0
  if T===BigFloat
   for r in (ra,rb)
    @test !sameowners(owners(v0[1]),owners(r.values[1]))
    @test !sameowners(owners(v0[1]),owners(r.multipliers[1]))
    @test !sameowners(owners(r.values[1]),owners(r.multipliers[1]))
    @test sameowners(owners(r.values[1]),owners(r.primal[1]))
    @test sameowners(owners(r.multipliers[1]),owners(r.dual[1]))
   end
  end
  if T===Rational{BigInt}
   for r in (ra,rb)
    @test sameowners(owners(v0[1]),owners(r.values[1]))
    @test sameowners(owners(v0[1]),owners(r.multipliers[1]))
    @test sameowners(owners(r.values[1]),owners(r.primal[1]))
    @test sameowners(owners(r.multipliers[1]),owners(r.dual[1]))
   end
  end
  # Hand-derived lifted residual: A=[2], objective=[3], values=[5,7], y=[11].
  p=LinearProblem(sparse(reshape(T[2],1,1)),T[3]);w=J._initialize_workspace_state(p,SolverOptions(T;verbose=false))
  for mod in (UPRReference,UPRC)
   q=mod._lp_residual_values(T,w,T[5,7],T[11]);@test q.primal==T[-3];@test q.dual==T[-19,11];@test q.values==T[5,7];@test q.multipliers==T[11]
   @test_throws DimensionMismatch mod._lp_residual_values(T,w,T[5],T[11])
  end
  if T<:AbstractFloat
   for mod in (UPRReference,UPRC);@test_throws ArgumentError mod._lp_residual_values(T,w,T[Inf,7],T[11]);end
   for scope in (:dual,:primal),tag in (Val(:original),Val(:B)),at in (1,2)
    a=fixture(T,16,:sparse,:mixed,scope);saved=deepcopy((a.w.costs,a.w.reduced_costs,a.w.lower,a.w.upper));calls=Ref(0);stop=()->(calls[]+=1;calls[]==at)
    out=scope===:dual ? modof(tag).perturb_dual_costs!(a.w,a.monitor,a.journal,a.policy;stop_requested=stop) : modof(tag).perturb_primal_bounds!(a.w,a.monitor,a.journal,a.policy;stop_requested=stop)
    @test out==-1;@test same(saved,(a.w.costs,a.w.reduced_costs,a.w.lower,a.w.upper));@test !a.journal.active&&isnothing(a.journal.bounds)
   end
  end
 end
 nothing
end

function allocation_gate(::Type{T},scope,arm,n,density,shape,mode) where T
 a=fixture(T,n,density,shape,scope;mode);b=fixture(T,n,density,shape,scope;mode)
 checkpair(a,b,arm)
 for k in 1:3,(tag,v) in ((Val(:original),a),(Val(arm),b));reset!(v);timed(tag,v);end
 before=Any[];after=Any[]
 for pair in 1:3,tag in (isodd(pair) ? (:original,arm) : (arm,:original))
  v=tag===:original ? a : b;reset!(v);t=timed(Val(tag),v)
  @test t["compile_seconds"]==t["recompile_seconds"]==0
  push!(tag===:original ? before : after,t)
 end
 if T===Rational{BigInt}&&arm===:C
  println("COUNTER_CAPTURE_BEGIN UPR")
  Main.TOML.print(stdout,Dict("kind"=>"UPR","type"=>string(T),"scope"=>String(scope),"arm"=>String(arm),"n"=>n,"density"=>String(density),"shape"=>String(shape),"mode"=>String(mode),"before"=>before,"after"=>after,"events_predicate"=>all(after[k]["events"]<before[k]["events"] for k in 1:3),"bytes_predicate"=>median(x["bytes"] for x in after)<median(x["bytes"] for x in before)))
  println("\nCOUNTER_CAPTURE_END UPR");flush(stdout)
 end
 @test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)
 nothing
end
@testset "Multiprecision unit perturb and residual" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do;correctness(BigFloat);end
  end
 end
 for T in (Float32,Float64,Rational{BigInt},Rational{Int64});correctness(T);end
 setprecision(BigFloat,128) do
  setrounding(BigFloat,RoundNearest) do
   allocation_gate(Rational{BigInt},:devex,:A,64,:sparse,:mixed,:unit)
   allocation_gate(Rational{BigInt},:steepest,:A,64,:sparse,:mixed,:unit)
   allocation_gate(BigFloat,:dual,:B,64,:dense,:mixed,:unit)
   allocation_gate(BigFloat,:primal,:B,64,:dense,:mixed,:unit)
   allocation_gate(Float64,:residual,:C,64,:sparse,:mixed,:unit)
   allocation_gate(Float64,:outer,:C,64,:sparse,:mixed,:unit)
   allocation_gate(BigFloat,:residual,:C,64,:sparse,:mixed,:unit)
   allocation_gate(BigFloat,:outer,:C,64,:sparse,:mixed,:unit)
   allocation_gate(Rational{BigInt},:residual,:C,64,:sparse,:mixed,:unit)
   allocation_gate(Rational{BigInt},:outer,:C,64,:sparse,:mixed,:unit)
  end
 end
end
end
