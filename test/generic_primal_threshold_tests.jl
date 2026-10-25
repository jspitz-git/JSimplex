module GenericPrimalThresholdTests
using Test,JSimplex,SparseArrays,LinearAlgebra
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
const METHODS=(:original,:candidate)
module Reference
import JSimplex
using LinearAlgebra
using JSimplex: SimplexWorkspace,NumericalPolicy,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_can_preserve_primal_bound_value,_legacy_primal_row_validation_enabled,_primal_relaxed_step,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,_primal_weighted_score,_record_full_pricing!,_is_fixed,_primal_cacheable_weight,_weight_pricing,_reject_auto_weight!
_primal_updated_weight(a,b,c,d)=JSimplex._primal_updated_weight(a,b,c,d)
validate_edge_weight(a,b,p;kw...)=JSimplex.validate_edge_weight(a,b,p;kw...)
function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}, entering::Int,
                                    direction::T, column::Vector{T}, leaving_row::Int) where {T}
    leaving = workspace.basis.basic_indices[leaving_row]
    movement = -direction * column[leaving_row]
    bound = movement > zero(T) ? workspace.upper[leaving] : workspace.lower[leaving]
    step = (bound_value(bound) - workspace.primal[leaving]) / movement
    step >= zero(T) && return true
    state = movement > zero(T) ? AT_UPPER : AT_LOWER
    _can_preserve_primal_bound_value(workspace, leaving, state, bound) && return true
    # A tolerated bound violation has a negative ratio. Clipping it to zero
    # does not eliminate the movement imposed by fixing the leaving variable
    # exactly at its bound during the subsequent basis recomputation.
    value = workspace.primal[entering] + direction * step
    isfinite(value) || return false
    tolerance = workspace.options.primal_tolerance
    violation = max(zero(T), _lower_violation(workspace.lower[entering], value),
                    _upper_violation(workspace.upper[entering], value))
    violation <= tolerance || return false
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row == leaving_row && continue
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        bound_violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                              _upper_violation(workspace.upper[index], value))
        # Use the same per-bound feasibility criterion as legacy Harris pricing
        # and recomputation, including the movement imposed by this bound snap.
        violation = max(violation, bound_violation)
        violation <= tolerance || return false
    end
    return true
end

function _primal_step_bounds_feasible(workspace::SimplexWorkspace{T}, direction::T,
                                      column::Vector{T}, step::T) where {T}
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        value = workspace.primal[index] - direction * column[row] * step
        isfinite(value) || return false
        violation = max(zero(T), _lower_violation(workspace.lower[index], value),
                        _upper_violation(workspace.upper[index], value))
        violation <= tolerance || return false
    end
    return true
end

function _primal_ratio(workspace::SimplexWorkspace{T}, entering::Int, direction::T,
                       tableau_column::Vector{T}) where {T}
    opposite = direction > zero(T) ? workspace.upper[entering] : workspace.lower[entering]
    # Keep optionality in flags so numeric loop accumulators stay concrete.
    has_step = isfinite(opposite)
    entering_step = has_step ?
        (bound_value(opposite) - workspace.primal[entering]) / direction : zero(T)
    strict_step = entering_step
    strict_row = 0
    strict_state = BASIC
    relaxed_limit = entering_step
    has_relaxed_limit = has_step
    tolerance = workspace.options.primal_tolerance
    for (row, index) in enumerate(workspace.basis.basic_indices)
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        raw_step = (bound_value(bound) - workspace.primal[index]) / movement
        isfinite(raw_step) || return nothing, -1, BASIC
        if raw_step < zero(T)
            violation = movement > zero(T) ?
                _upper_violation(bound, workspace.primal[index]) :
                _lower_violation(bound, workspace.primal[index])
            violation > tolerance && return nothing, -1, BASIC
        end
        candidate = max(zero(T), raw_step)
        if !has_step || candidate < strict_step ||
           (candidate == strict_step && strict_row == 0)
            strict_step = candidate
            strict_row = row
            strict_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            has_step = true
        end
        relaxed = _primal_relaxed_step(raw_step, tolerance, movement)
        if isfinite(relaxed) && (!has_relaxed_limit || relaxed < relaxed_limit)
            relaxed_limit = max(zero(T), relaxed)
            has_relaxed_limit = true
        end
    end
    has_step || return nothing, strict_row, strict_state
    strict_row == 0 && return strict_step, strict_row, strict_state
    has_relaxed_limit || return strict_step, strict_row, strict_state

    strict_safe = !(strict_row in workspace.scratch.rejected_rows) &&
        _primal_bound_snap_feasible(
            workspace, entering, direction, tableau_column, strict_row)
    fallback = strict_safe ? (strict_step, strict_row, strict_state) : (nothing, -1, BASIC)
    leaving_row = 0
    leaving_step = strict_step
    leaving_state = strict_state
    largest_pivot = zero(T)
    for (row, index) in enumerate(workspace.basis.basic_indices)
        row in workspace.scratch.rejected_rows && continue
        movement = -direction * tableau_column[row]
        iszero(movement) && continue
        bound = movement > zero(T) ? workspace.upper[index] : workspace.lower[index]
        isfinite(bound) || continue
        candidate = max(zero(T),
                        (bound_value(bound) - workspace.primal[index]) / movement)
        candidate <= relaxed_limit || continue
        pivot = abs(tableau_column[row])
        if pivot > largest_pivot
            !_primal_bound_snap_feasible(
                workspace, entering, direction, tableau_column, row) && continue
            leaving_row = row
            leaving_step = candidate
            leaving_state = movement > zero(T) ? AT_UPPER : AT_LOWER
            largest_pivot = pivot
        end
    end
    # Tolerated initial bound violations can create zero ratios on coefficients
    # too small to pivot on. A finite entering bound remains a valid Harris move
    # when the entire predicted step respects the same per-bound tolerance.
    if _legacy_primal_row_validation_enabled(workspace) &&
       largest_pivot <= workspace.options.zero_tolerance && isfinite(opposite) &&
       isfinite(entering_step) && entering_step > zero(T) && entering_step <= relaxed_limit &&
       _primal_step_bounds_feasible(workspace, direction, tableau_column, entering_step)
        return entering_step, 0, BASIC
    end
    if leaving_row == 0
        return fallback
    end
    _primal_step_bounds_feasible(workspace, direction, tableau_column, leaving_step) ||
        return fallback
    return leaving_step, leaving_row, leaving_state
end


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


function _primal_updated_weight(weight::T, alpha::T, beta::T,
                                h_norm_squared::T) where {T<:AbstractFloat}
    squared = muladd(alpha * alpha, h_norm_squared,
                     muladd(-2 * alpha, beta, weight * weight))
    isfinite(squared) && squared >= one(T) || return nothing
    updated = sqrt(squared)
    return _primal_cacheable_weight(updated) ? updated : nothing
end


function validate_edge_weight(stored::BigFloat,actual::BigFloat,policy::NumericalPolicy;
                              square_root::Bool=false)::Bool
    return setprecision(BigFloat,max(precision(stored),precision(actual),
                                     precision(policy.solve_tolerance))) do
        isfinite(stored) && isfinite(actual) && stored > 0 && actual > 0 || return false
        ratio = min(stored,actual)/max(stored,actual)
        (square_root ? ratio*ratio : ratio) >= BigFloat(1)/2
    end
end


function _validate_dual_edge!(ws,index::Int,rho::AbstractVector{T})::Bool where T
    ws.options.pricing == :auto && _weight_pricing(ws,:dual) == :steepest_edge || return true
    ws.scratch.pricing.validated_weights += 1
    stored = ws.pricing_weights[index]
    if T <: Rational
        # Validation can precede an infeasibility proof with no pivot at all.
        # Widen its squared norm rather than introducing a fixed-width overflow.
        actual = zero(Rational{BigInt})
        for value in rho
            actual += abs2(big(value))
        end
        valid = validate_edge_weight(big(stored),actual,ws.progress.numerical_policy)
    else
        valid = validate_edge_weight(stored,dot(rho,rho),ws.progress.numerical_policy)
    end
    return valid || _reject_auto_weight!(ws)
end


end
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
function capture(f)
 try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
end
snap(a)=(a,map(copy,a),deepcopy(a))
intact(a,s)=all(a[k]===s[1][k]&&axes(a[k])==axes(s[2][k])&&all(a[k][i]===s[2][k][i]&&same(a[k][i],s[3][k][i]) for i in eachindex(a[k])) for k in eachindex(a))
warrays(w)=(w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.primal,w.costs,w.reduced_costs,w.lower,w.upper,w.pricing_weights,w.basis.basic_indices,w.basis.states)
function statefixture(::Type{T},n,m;pricing=:devex,diagnostics=nothing) where T
 p=LinearProblem(spzeros(T,m,n),zeros(T,n);row_lower=zeros(T,m),row_upper=fill(T(2),m),column_lower=zeros(T,n),column_upper=fill(T(2),n))
 policy=J.NumericalPolicy(T;refactor_timing=false)
 J._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,pricing,verbose=false);progress=J.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
end
function ratiofixture(::Type{T},n,pattern,density) where T
 w=statefixture(T,1,n);w.primal[1]=zero(T)
 c=zeros(T,n)
 for i in 1:n
  w.primal[i+1]=one(T)
  if density===:dense||i==n||i%8==0
   c[i]=T(i)*(pattern===:negative||pattern===:mixed&&isodd(i) ? -one(T) : one(T))
  end
 end
 w,1,one(T),c
end
function enteringfixture(::Type{T},n,pattern,pricing;diagnostics=nothing) where T
 w=statefixture(T,n,0;pricing,diagnostics)
 for i in 1:n
  lower=pattern===:lower||pattern===:mixed&&isodd(i)
  w.basis.states[i]=lower ? J.AT_LOWER : J.AT_UPPER
  w.reduced_costs[i]=(lower ? -one(T) : one(T))*T(i//16)
  w.pricing_weights[i]=T(2)
 end
 J._prepare_auto_pricing!(w,:primal)
 w
end
function validationfixture(::Type{T},n) where T
 w=statefixture(T,1,n;pricing=:auto)
 state=J.PricingState(T);state.algorithm=:dual;state.active=state.return_mode=:steepest_edge;w.scratch.pricing=state
 w.pricing_weights[1]=T(n)
 w,1,ones(T,n)
end
@noinline ratio(::Val{:original},v)=Reference._primal_ratio(v...)
@noinline ratio(::Val{:candidate},v)=J._primal_ratio(v...)
@noinline entering(::Val{:original},w)=Reference._primal_entering(w,w.options.dual_tolerance)
@noinline entering(::Val{:candidate},w)=J._primal_entering(w,w.options.dual_tolerance)
@noinline updated(::Val{:original},v)=Reference._primal_updated_weight(v...)
@noinline updated(::Val{:candidate},v)=J._primal_updated_weight(v...)
@noinline validate(::Val{:original},v)=Reference.validate_edge_weight(v[1],v[2],v[3];square_root=v[4])
@noinline validate(::Val{:candidate},v)=J.validate_edge_weight(v[1],v[2],v[3];square_root=v[4])
@noinline consumer(::Val{:original},v)=Reference._validate_dual_edge!(v...)
@noinline consumer(::Val{:candidate},v)=J._validate_dual_edge!(v...)
function operands(::Type{T}) where T
 a=T[0,-zero(T),1,-1,T(3//7),T(-7//3),T(1//2),T(-1//2)]
 if T<:AbstractFloat
  append!(a,T[Inf,-Inf,NaN,prevfloat(one(T)),nextfloat(one(T)),nextfloat(zero(T))])
  T===BigFloat&&append!(a,[ldexp(one(T),1000),ldexp(one(T),-1000)])
 end
 a
end
function correctness(::Type{T}) where T
 @testset "Primal threshold values $T" begin
  policy=J.NumericalPolicy(T;refactor_timing=false)
  for stored in (T===BigFloat ? (precision(BigFloat),512) : (0,))
   a=T===BigFloat ? setprecision(()->operands(T),BigFloat,stored) : operands(T)
   for x in a,y in T[0,1,2],root in (false,true)
    v=(x,y,policy,root);s=deepcopy((x,y))
    @test same(capture(()->validate(Val(:original),v)),capture(()->validate(Val(:candidate),v)))
    @test same((x,y),s)
   end
   for x in a,alpha in T[0,1,-1],beta in T[0,1]
    v=(x,alpha,beta,T(2));s=deepcopy(v)
    @test same(capture(()->updated(Val(:original),v)),capture(()->updated(Val(:candidate),v)))
    @test same(v,s)
   end
   for x in (T<:AbstractFloat ? T[prevfloat(T(1//2)),T(1//2),nextfloat(T(1//2))] : T[1//4,1//2,3//4])
    # Native floating boundary only; rational path below has exact values.
    @test same(validate(Val(:original),(x,one(T),policy,false)),validate(Val(:candidate),(x,one(T),policy,false)))
   end
  end
  T===Rational{Int64} || (@test updated(Val(:candidate),(T(2),zero(T),zero(T),one(T)))==T(2))
  @test validate(Val(:candidate),(one(T),T(2),policy,false))===true
  @test validate(Val(:candidate),(one(T),T(4),policy,false))===false
  for n in (0,1,8),p in (:positive,:negative,:mixed),d in (:sparse,:dense)
   v=ratiofixture(T,n,p,d);a=(warrays(v[1])...,v[4]);s=snap(a)
   @test same(ratio(Val(:original),v),ratio(Val(:candidate),v))
   want=n==0 ? (T(2),0,J.BASIC) : (one(T)/T(n),n,p===:negative||p===:mixed&&isodd(n) ? J.AT_UPPER : J.AT_LOWER)
   @test same(ratio(Val(:candidate),v),want)
   @test intact(a,s)
   n==0&&continue
   for x in operands(T)
    v[4][1]=x;s=snap(a)
    @test same(capture(()->ratio(Val(:original),v)),capture(()->ratio(Val(:candidate),v)))
    @test intact(a,s)
   end
   push!(v[1].scratch.rejected_rows,n)
   @test same(capture(()->ratio(Val(:original),v)),capture(()->ratio(Val(:candidate),v)))
  end
  for n in (0,1,8),p in (:lower,:upper,:mixed),pricing in (:dantzig,:devex)
   w=enteringfixture(T,n,p,pricing);s=snap(warrays(w))
   @test same(entering(Val(:original),w),entering(Val(:candidate),w))
   @test same(entering(Val(:candidate),w),n==0 ? (0,zero(T)) : (n,p===:lower||p===:mixed&&isodd(n) ? one(T) : -one(T)))
   @test intact(warrays(w),s)
   n==0&&continue
   for x in operands(T)
    w.reduced_costs[1]=x;s=snap(warrays(w))
    @test same(capture(()->entering(Val(:original),w)),capture(()->entering(Val(:candidate),w)))
    @test intact(warrays(w),s)
   end
   push!(w.scratch.rejected_entering,n);@test same(entering(Val(:original),w),entering(Val(:candidate),w));empty!(w.scratch.rejected_entering)
   w.options=SolverOptions(T;algorithm=:primal,pricing,verbose=false,dual_tolerance=T(1//2))
   @test same(entering(Val(:original),w),entering(Val(:candidate),w))
  end
  for pricing in (:dantzig,:devex,:steepest_edge)
   w=enteringfixture(T,8,:lower,pricing)
   w.scratch.steepest_initialized=true;fill!(w.scratch.steepest_valid,true)
   @test same(entering(Val(:original),w),entering(Val(:candidate),w))
  end
  w=enteringfixture(T,129,:lower,:devex);previous=w.progress
  policy=J.NumericalPolicy(T;partial_pricing=true,refactor_timing=false)
  w.progress=typeof(previous)(previous.start_ns,previous.objective,previous.objective_constant,previous.scaling,previous.iteration_offset,previous.refactorization_offset,previous.diagnostics,policy)
  fill!(w.reduced_costs,zero(T));w.reduced_costs[129]=-T(2)
  @test entering(Val(:candidate),w)[1]==129
  w.reduced_costs[129]=zero(T);w.reduced_costs[1]=-T(3)
  @test entering(Val(:candidate),w)[1]==1
  w.reduced_costs[1]=zero(T);@test entering(Val(:candidate),w)[1]==0
  for n in (1,8)
   v=validationfixture(T,n);s=snap((warrays(v[1])...,v[3]));count=v[1].scratch.pricing.validated_weights
   @test consumer(Val(:original),v)===consumer(Val(:candidate),v)===true
   @test v[1].scratch.pricing.validated_weights==count+2
   @test intact((warrays(v[1])...,v[3]),s)
  end
 end
end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
@noinline function batch(method::M,::Val{S},v,calls) where {M,S}
 sink=0
 for _ in 1:calls
  if S===:ratio
   step,row,state=ratio(method,v);sink+=row+Int(!isnothing(step))
  elseif S===:entering
   index,dir=entering(method,v);sink+=index+Int(isfinite(dir))
  elseif S===:update
   for a in v;r=updated(method,a);sink+=Int(!isnothing(r));end
  elseif S===:validation
   for a in v;sink+=Int(validate(method,a));end
  else;sink+=Int(consumer(method,v))
  end
 end
 sink
end
function timed(method::M,scope::S,v::V,calls) where {M,S,V}
 t=@timed batch(method,scope,v,calls);merge(cost(t),Dict("sink"=>t.value))
end

@noinline function allocation_cost(method::M,scope::S,v::V,sink) where {M,S,V}
 t=@timed batch(method,scope,v,2)
 sink[]=t.value
 (bytes=t.bytes,events=Base.gc_alloc_count(t.gcstats),compile=t.compile_time,recompile=t.recompile_time,value=t.value)
end
function cost_pair(scope,v)
 sink=Ref(0)
 for _ in 1:3,method in (Val(:original),Val(:candidate));allocation_cost(method,scope,v,sink);end
 GC.gc()
 before=allocation_cost(Val(:original),scope,v,sink)
 after=allocation_cost(Val(:candidate),scope,v,sink)
 @test before.compile==after.compile==before.recompile==after.recompile==0
 @test before.value==after.value>0
 @test after.bytes<before.bytes && after.events<before.events # RED costgate
end
function callback_fixture(::Type{T},seen) where T
 d=J.SimplexDiagnostics(observer=(reason,trial)->begin
  if reason===:pricing_weight_rejected
   seen[]+=1
   trial.reduced_costs[1]=-T(1//2)
   trial.options=SolverOptions(T;algorithm=:primal,pricing=:auto,verbose=false,dual_tolerance=one(T))
  end
 end)
 w=enteringfixture(T,4,:lower,:devex;diagnostics=d)
 w.options=SolverOptions(T;algorithm=:primal,pricing=:auto,verbose=false)
 state=J.PricingState(T);state.algorithm=:primal;w.scratch.pricing=state
 fill!(w.reduced_costs,zero(T));w.pricing_weights[1]=zero(T)
 w
end
@testset "Generic primal thresholds" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat)
   end
  end
 end
 for T in (Rational{BigInt},Rational{Int64},Float32,Float64);correctness(T);end
 @testset "Current-call mixed precision and callback mutation" begin
  for bits in (64,128,256),mode in MODES,pricing in (:dantzig,:devex,:steepest_edge)
   values,tolerance=setprecision(BigFloat,512) do
    t=BigFloat(1)/32+ldexp(one(BigFloat),-200)
    (BigFloat[-t+ldexp(one(BigFloat),-201),0,0,0],t)
   end
   setprecision(BigFloat,bits) do
    setrounding(BigFloat,mode) do
     w=enteringfixture(BigFloat,4,:lower,pricing)
     w.reduced_costs.=values
     w.scratch.steepest_initialized=true;fill!(w.scratch.steepest_valid,true)
     saved=snap(warrays(w));before=deepcopy(tolerance)
     @test same(capture(()->Reference._primal_entering(w,tolerance)),capture(()->J._primal_entering(w,tolerance)))
     expected=bits<200 && mode in (RoundNearest,RoundUp,RoundToZero) ? 1 : 0
     @test first(J._primal_entering(w,tolerance))==expected
     @test intact(warrays(w),saved)&&same(tolerance,before)
     @test precision(BigFloat)==bits&&rounding(BigFloat)==mode
    end
   end
  end
  for T in (BigFloat,Rational{BigInt},Float32,Float64)
   left,right=Ref(0),Ref(0)
   a=callback_fixture(T,left);b=callback_fixture(T,right)
   left_result=entering(Val(:original),a);right_result=entering(Val(:candidate),b)
   @test same(left_result,right_result) && left_result==(1,one(T))
   # The argument tolerance was captured before the observer replaced options.
   @test left[]==right[]==1
   @test a.options.dual_tolerance==b.options.dual_tolerance==one(T)
   @test first(entering(Val(:candidate),b))==0
   @test same(a.reduced_costs,b.reduced_costs)
  end
 end
 @testset "Warm whole-function allocation savings" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    for density in (:sparse,:dense);cost_pair(Val(:ratio),ratiofixture(BigFloat,128,:positive,density));end
    for pricing in (:dantzig,:devex);cost_pair(Val(:entering),enteringfixture(BigFloat,128,:lower,pricing));end
    cost_pair(Val(:update),[(BigFloat(2),BigFloat(1//4),BigFloat(0),BigFloat(2)) for _ in 1:128])
    p=J.NumericalPolicy(BigFloat;refactor_timing=false)
    cost_pair(Val(:validation),[(BigFloat(2),BigFloat(2),p,isodd(i)) for i in 1:128])
    cost_pair(Val(:consumer),validationfixture(BigFloat,128))
   end
  end
  for pricing in (:dantzig,:devex);cost_pair(Val(:entering),enteringfixture(Rational{BigInt},128,:lower,pricing));end
  for T in (Float32,Float64)
   for (scope,v) in ((Val(:ratio),ratiofixture(T,128,:positive,:dense)),(Val(:entering),enteringfixture(T,128,:lower,:dantzig)),(Val(:consumer),validationfixture(T,128)))
    sink=Ref(0)
    for _ in 1:3,method in (Val(:original),Val(:candidate));allocation_cost(method,scope,v,sink);end
    before=allocation_cost(Val(:original),scope,v,sink);after=allocation_cost(Val(:candidate),scope,v,sink)
    @test before.bytes==after.bytes==before.events==after.events==0
    @test before.value==after.value
   end
  end
 end
end

end
