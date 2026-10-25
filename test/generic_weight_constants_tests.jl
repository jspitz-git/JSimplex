module GenericWeightConstantsTests
using Test,JSimplex,SparseArrays,LinearAlgebra,TOML
module WeightReference
using LinearAlgebra
import JSimplex
using JSimplex: SimplexWorkspace,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,_pipeline_weight_rhs!,_checked_basis_solve!,_pipeline_unit_rhs!,price!,_primal_updated_weight,_primal_devex_leaving_weight,_primal_store_rational_weight,_primal_direction_magnitude,_dual_pivot_cutoff,_dual_pivot_eligible,_is_fixed,dual_ratio_test,_heapify_breakpoints!,_pop_breakpoint!,_breakpoint_before,bound_value
function _primal_update_steepest!(workspace::SimplexWorkspace{T}, entering::Int,
                                  leaving_row::Int, pivot::T; shared_row::Bool=false) where {T}
    scratch = workspace.scratch
    # Fixed-width rational weights are priced exactly on demand in BigInt arithmetic.
    T <: Rational && T !== Rational{BigInt} && return nothing
    h = _pipeline_weight_rhs!(workspace,leaving_row,pivot)
    if !all(isfinite, h)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    h_norm_squared = dot(h, h)
    if !isfinite(h_norm_squared)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    tau = _checked_basis_solve!(scratch.tau,workspace,h;transposed=true,operation=:weight_btran)
    if !shared_row
        _pipeline_unit_rhs!(workspace,leaving_row)
        _checked_basis_solve!(scratch.rho,workspace,h;transposed=true,operation=:weight_btran,
                              unit_row=leaving_row)
        price!(scratch.tableau_row, workspace, scratch.rho)
    end
    rho = scratch.rho
    if !all(isfinite, tau) || !all(isfinite, rho)
        fill!(scratch.steepest_valid, false)
        return nothing
    end
    price!(scratch.pricing_row, workspace, tau)
    leaving = workspace.basis.basic_indices[leaving_row]
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC && index != leaving) &&
            continue
        scratch.steepest_valid[index] || index == leaving || continue
        weight = index == leaving ?
            (T <: AbstractFloat ? sqrt(T(2)) : T(2)) : workspace.pricing_weights[index]
        updated = _primal_updated_weight(weight, scratch.tableau_row[index],
                                         scratch.pricing_row[index], h_norm_squared)
        if isnothing(updated)
            scratch.steepest_valid[index] = false
        else
            workspace.pricing_weights[index] = updated
            scratch.steepest_valid[index] = true
        end
    end
    scratch.steepest_valid[entering] = false
    return nothing
end

_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:AbstractFloat} =
    min(floatmax(T), abs(coefficient) * leaving_weight)
_primal_devex_candidate_weight(coefficient::T, leaving_weight::T) where {T<:Rational} =
    _primal_store_rational_weight(T, big(coefficient)^2 * big(leaving_weight))

function _primal_update_devex!(workspace::SimplexWorkspace{T}, entering::Int,
                               leaving_row::Int, pivot::T; shared_row::Bool=false) where {T}
    tableau_row = workspace.scratch.tableau_row
    if !shared_row
        unit = _pipeline_unit_rhs!(workspace,leaving_row)
        rho = _checked_basis_solve!(workspace.scratch.rho,workspace,unit;
                                    transposed=true,operation=:weight_btran,unit_row=leaving_row)
        price!(tableau_row, workspace, rho)
    end
    leaving = workspace.basis.basic_indices[leaving_row]
    leaving_weight = _primal_devex_leaving_weight(
        workspace.pricing_weights[entering], pivot,
    )
    for index in eachindex(workspace.basis.states)
        (index == entering || workspace.basis.states[index] == BASIC) && continue
        workspace.pricing_weights[index] = max(
            workspace.pricing_weights[index],
            _primal_devex_candidate_weight(tableau_row[index], leaving_weight),
        )
    end
    workspace.pricing_weights[leaving] = leaving_weight
    return nothing
end

function _bound_flipping_ratio_test(workspace::SimplexWorkspace{T}, tableau_row::Vector{T},
                                    orientation::T, violation::T) where {T}
    flips = workspace.scratch.flips
    empty!(flips)
    cutoff = workspace.progress.numerical_policy.pivot_validation ? zero(T) : _dual_pivot_cutoff(T)
    # A boxed variable matters only when it can move in this tableau row.
    # Otherwise keep the linear Harris pass and its stronger pivot choice.
    has_boxed = false
    for index in eachindex(workspace.basis.states)
        if isfinite(workspace.lower[index]) && isfinite(workspace.upper[index]) &&
           _dual_pivot_eligible(workspace, index, orientation * tableau_row[index], cutoff)
            has_boxed = true
            break
        end
    end
    has_boxed || return dual_ratio_test(workspace, tableau_row, orientation), flips, false

    candidates = workspace.scratch.candidates
    empty!(candidates)
    steps = workspace.scratch.ratio_steps
    length(steps) < length(tableau_row) && resize!(steps, length(tableau_row))
    for index in eachindex(tableau_row)
        coefficient = orientation * tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        step = workspace.reduced_costs[index] / coefficient
        if !isfinite(step) || step < zero(T)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        steps[index] = step
        push!(candidates, index)
    end
    isempty(candidates) && return -1, flips, false
    # Most pivots consume a small prefix. Building a heap costs linear work
    # and reuses the candidate buffer instead of sorting every breakpoint.
    _heapify_breakpoints!(candidates,steps,tableau_row)
    sort_after = max(32,length(candidates)÷16)
    sorted_tail = false
    tail_position = 1

    remaining = violation
    while sorted_tail ? tail_position <= length(candidates) : !isempty(candidates)
        index = if sorted_tail
            value = candidates[tail_position]
            tail_position += 1
            value
        else
            _pop_breakpoint!(candidates,steps,tableau_row)
        end
        state = workspace.basis.states[index]
        opposite = state == AT_LOWER ? workspace.upper[index] : workspace.lower[index]
        if state == FREE_NONBASIC || !isfinite(opposite)
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        width = bound_value(workspace.upper[index]) - bound_value(workspace.lower[index])
        gain = abs(tableau_row[index]) * width
        if !isfinite(width) || !isfinite(gain)
            empty!(flips)
            return dual_ratio_test(workspace, tableau_row, orientation), flips, false
        end
        if remaining <= gain + workspace.options.primal_tolerance
            index in workspace.scratch.rejected_entering && return -1, flips, false
            return index, flips, false
        end
        push!(flips, index)
        remaining -= gain
        if !sorted_tail && length(flips) >= sort_after
            # A long flip sequence no longer benefits from extracting a
            # prefix. Finish in-place; the explicit index key restores the
            # same stable ties after heap construction shuffled the tail.
            sort!(candidates;lt=(a,b) -> _breakpoint_before(a,b,steps,tableau_row),alg=QuickSort)
            sorted_tail = true
        end
    end
    return -1, flips, true
end


end

const WeightCandidate=JSimplex
const J=JSimplex
const MODES=(RoundNearest,RoundDown,RoundUp,RoundToZero,RoundFromZero)
const METHODS=(:original,:candidate)
same(a,b)=isequal(a,b)
same(a::BigFloat,b::BigFloat)=isequal(a,b)&&precision(a)==precision(b)&&signbit(a)==signbit(b)
same(a::Tuple,b::Tuple)=length(a)==length(b)&&all(same(x,y) for (x,y) in zip(a,b))
same(a::AbstractArray,b::AbstractArray)=axes(a)==axes(b)&&all(same(a[i],b[i]) for i in eachindex(a,b))
same(a::J.Bound,b::J.Bound)=a.bounded==b.bounded&&same(a.value,b.value)
capture(f)=try;(:value,f());catch e;(:error,typeof(e),sprint(showerror,e));end
inputs(w)=(w.problem.A.nzval,w.problem.A.rowval,w.problem.A.colptr,w.problem.objective,w.problem.column_lower,w.problem.column_upper,w.problem.row_lower,w.problem.row_upper,w.primal,w.costs,w.reduced_costs,w.lower,w.upper,w.basis.basic_indices,w.basis.states,w.scratch.row_solution)
fixture_inputs(v)=(inputs(v.w)...,v.row)
scalar_inputs(v)=(v.pivot,v.orientation,v.violation)
snap(a)=(a,map(copy,a),deepcopy(a))
intact(a,s)=all(a[k]===s[1][k]&&same(a[k],s[3][k])&&all(a[k][i]===s[2][k][i] for i in eachindex(a[k])) for k in eachindex(a))
outputs(w)=(w.pricing_weights,w.scratch.steepest_valid,w.scratch.rho,w.scratch.tau,w.scratch.tableau_row,w.scratch.pricing_row,w.scratch.candidates,w.scratch.flips,w.scratch.ratio_steps,w.scratch.ratio_gains)
function workspace(::Type{T},n,density,pattern;factor=true,pricing=:devex) where T
 m=factor ? 4 : 1
 A=zeros(T,m,n)
 for j in 1:n,r in 1:m
  if j==1;A[r,j]=r==1 ? one(T) : zero(T)
  elseif density===:dense||j%4==0
   v=T(((r+j)%5+1)//2)
   s=pattern===:negative||pattern===:mixed&&isodd(j) ? -one(T) : one(T)
   A[r,j]=r==1 ? -s*v : T(((r+j)%3)//8)
  end
 end
 p=LinearProblem(sparse(A),zeros(T,n);row_lower=zeros(T,m),row_upper=zeros(T,m),column_lower=zeros(T,n),column_upper=fill(T(4),n))
 opt=SolverOptions(T;algorithm=:primal,pricing,verbose=false)
 policy=J.NumericalPolicy(T;refactor_timing=false)
 progress=J.SimplexProgressContext(p;numerical_policy=policy)
 w=factor ? J.initialize_workspace(p,opt;progress) : J._initialize_workspace_state(p,opt;progress)
 fill!(w.pricing_weights,T(4));fill!(w.scratch.steepest_valid,true)
 fill!(w.scratch.rho,zero(T));w.scratch.rho[1]=-one(T)
 fill!(w.scratch.tau,zero(T));fill!(w.scratch.pricing_row,zero(T));fill!(w.scratch.tableau_row,zero(T))
 fill!(w.scratch.row_solution,zero(T));w.scratch.row_solution[1]=-one(T)
 J.price!(w.scratch.tableau_row,w,w.scratch.rho)
 resize!(w.scratch.ratio_steps,n+m);fill!(w.scratch.ratio_steps,T(99))
 resize!(w.scratch.ratio_gains,n+m);fill!(w.scratch.ratio_gains,T(77))
 w
end
function fixture(::Type{T},n,scope,density,pattern,shared) where T
 w=workspace(T,n,density,pattern;factor=scope!==:bfrt,pricing=scope===:steepest ? :steepest_edge : :devex)
 row=zeros(T,length(w.basis.states))
 if scope===:bfrt
  for i in 1:n
   upper=pattern===:upper||pattern===:mixed&&isodd(i)
   w.basis.states[i]=upper ? J.AT_UPPER : J.AT_LOWER
   magnitude=T((i%3+1)//2)
   coefficient=(upper ? -one(T) : one(T))*magnitude
   row[i]=density===:dense||i%4==0 ? coefficient : zero(T)
   w.reduced_costs[i]=coefficient*T((i%4+1)//4)
   w.upper[i]=Bound(one(T))
  end
 end
 (w=w,row=row,pivot=-one(T),orientation=one(T),violation=T(3//2),shared=shared,weights=copy(w.pricing_weights),valid=copy(w.scratch.steepest_valid))
end
reset_fixture!(v)=(copyto!(v.w.pricing_weights,v.weights);copyto!(v.w.scratch.steepest_valid,v.valid);nothing)
@noinline function runwhole(::Val{:original},::Val{:steepest},v)
 WeightReference._primal_update_steepest!(v.w,1,1,v.pivot;shared_row=v.shared)
 Int(isfinite(v.w.pricing_weights[2]))+Int(v.w.scratch.steepest_valid[1])
end
@noinline function runwhole(::Val{:candidate},::Val{:steepest},v)
 WeightCandidate._primal_update_steepest!(v.w,1,1,v.pivot;shared_row=v.shared)
 Int(isfinite(v.w.pricing_weights[2]))+Int(v.w.scratch.steepest_valid[1])
end
@noinline function runwhole(::Val{:original},::Val{:devex},v)
 WeightReference._primal_update_devex!(v.w,1,1,v.pivot;shared_row=v.shared)
 Int(isfinite(v.w.pricing_weights[2]))
end
@noinline function runwhole(::Val{:candidate},::Val{:devex},v)
 WeightCandidate._primal_update_devex!(v.w,1,1,v.pivot;shared_row=v.shared)
 Int(isfinite(v.w.pricing_weights[2]))
end
@noinline function runwhole(::Val{:original},::Val{:bfrt},v)
 index,flips,exhausted=WeightReference._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
 index+length(flips)+Int(exhausted)
end
@noinline function runwhole(::Val{:candidate},::Val{:bfrt},v)
 index,flips,exhausted=WeightCandidate._bound_flipping_ratio_test(v.w,v.row,v.orientation,v.violation)
 index+length(flips)+Int(exhausted)
end
cost(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function timed(method::M,scope::S,v::V) where {M,S,V}
 t=@timed runwhole(method,scope,v);merge(cost(t),Dict("sink"=>t.value))
end
function correctness(::Type{T}) where T
 @testset "Weight constants correctness $T" begin
  if T===BigFloat
   # Same invocation contexts, older512-bit inputs, signs, exceptions and owners.
   for stored in (precision(T),512)
    coefficients=setprecision(()->BigFloat[0,-0.0,1,-1,3//7,-3//7,Inf,-Inf,NaN,floatmax(BigFloat)],T,stored)
    for coefficient in coefficients,weight in BigFloat[0,1,4]
     before=deepcopy((coefficient,weight));owner=coefficient;weight_owner=weight
     ref=capture(()->WeightReference._primal_devex_candidate_weight(coefficient,weight))
     got=capture(()->WeightCandidate._primal_devex_candidate_weight(coefficient,weight))
     @test same(ref,got)
     @test coefficient===owner&&weight===weight_owner&&same((coefficient,weight),before)
    end
   end
   for module_ in (WeightReference,WeightCandidate)
    coefficient=floatmax(BigFloat);weight=BigFloat(2);before=deepcopy((coefficient,weight))
    first=module_._primal_devex_candidate_weight(coefficient,weight)
    second=module_._primal_devex_candidate_weight(coefficient,weight)
    @test same(first,second)&&first==floatmax(BigFloat)&&first!==second
    @test first!==coefficient&&second!==coefficient&&same((coefficient,weight),before)
   end
  end
  scopes=T<:Rational ? (:bfrt,) : (:steepest,:devex,:bfrt)
  for scope in scopes,density in (:sparse,:dense),pattern in (scope===:bfrt ? (:lower,:upper,:mixed) : (:positive,:negative,:mixed)),shared in (scope===:bfrt ? (true,) : (true,false))
   a=fixture(T,8,scope,density,pattern,shared);b=fixture(T,8,scope,density,pattern,shared)
   sa=snap(fixture_inputs(a));sb=snap(fixture_inputs(b));scalar_a=deepcopy(scalar_inputs(a));scalar_b=deepcopy(scalar_inputs(b));sv=Val(scope)
   @test same(capture(()->runwhole(Val(:original),sv,a)),capture(()->runwhole(Val(:candidate),sv,b)))
   @test same(outputs(a.w),outputs(b.w))
   @test intact(fixture_inputs(a),sa)&&intact(fixture_inputs(b),sb)
   @test same(scalar_inputs(a),scalar_a)&&same(scalar_inputs(b),scalar_b)
   if scope===:steepest
    @test all(i->a.w.pricing_weights[i]==T(4),1:8)
    @test !a.w.scratch.steepest_valid[1]
   elseif scope===:devex
    @test a.w.pricing_weights[a.w.basis.basic_indices[1]]==T(4)
   end
   # A second call with explicit reset checks lifetime/context and output owners.
   reset_fixture!(a);reset_fixture!(b)
   @test same(runwhole(Val(:original),sv,a),runwhole(Val(:candidate),sv,b))
   @test same(outputs(a.w),outputs(b.w))
  end
  # Exit fixtures explicitly target the strongest first tied candidate8.
  for variant in (:no_boxed,:fixed,:rejected,:exhausted,:nonfinite_step,:negative_step,:short_row)
   T<:Rational&&variant===:nonfinite_step&&continue
   a=fixture(T,8,:bfrt,:dense,:mixed,true);b=fixture(T,8,:bfrt,:dense,:mixed,true)
   if variant===:exhausted
    a=merge(a,(violation=T(1000),));b=merge(b,(violation=T(1000),))
   elseif variant===:short_row
    a=merge(a,(row=T[],));b=merge(b,(row=T[],))
   end
   for v in (a,b)
    if variant===:no_boxed;fill!(v.w.upper,Bound{T}(nothing))
    elseif variant===:fixed;v.w.upper[2]=Bound(zero(T))
    elseif variant===:rejected;push!(v.w.scratch.rejected_entering,8)
    elseif variant===:nonfinite_step;v.w.reduced_costs[8]=T(Inf)
    elseif variant===:negative_step;v.w.reduced_costs[8]=-v.row[8]
    end
   end
   # Direct unwrapped result retains entering/flips/exhausted and borrowed owner.
   ra=capture(()->WeightReference._bound_flipping_ratio_test(a.w,a.row,a.orientation,a.violation))
   rb=capture(()->WeightCandidate._bound_flipping_ratio_test(b.w,b.row,b.orientation,b.violation))
   @test same(ra,rb)
   @test same(outputs(a.w),outputs(b.w))
   if variant===:short_row
    @test ra[1]===:error&&ra[2]===BoundsError
   else
    @test ra[1]===:value&&ra[2][2]===a.w.scratch.flips&&rb[2][2]===b.w.scratch.flips
    if variant===:rejected
     @test ra[2][1]==-1&&isempty(ra[2][2])&&ra[2][3]===false
    elseif variant===:exhausted
     @test ra[2][1]==-1&&length(ra[2][2])==8&&ra[2][3]===true
    elseif variant in (:no_boxed,:nonfinite_step,:negative_step)
     # This supplied condition forces the preserved ordinary Harris fallback.
     expected=J.dual_ratio_test(a.w,a.row,a.orientation)
     @test ra[2][1]==expected&&isempty(ra[2][2])&&ra[2][3]===false
    end
   end
  end
 end
end

function allocation_gate(::Type{T},scope,pattern,shared) where T
 a=fixture(T,128,scope,:dense,pattern,shared);b=fixture(T,128,scope,:dense,pattern,shared);sv=Val(scope)
 for _ in 1:3,method in METHODS
  v=method===:original ? a : b;reset_fixture!(v);timed(Val(method),sv,v)
 end
 before=Tuple{Int,Int}[];after=Tuple{Int,Int}[]
 for round in 1:3
  sinks=Int[]
  for method in (isodd(round) ? METHODS : reverse(METHODS))
   v=method===:original ? a : b;reset_fixture!(v)
   r=timed(Val(method),sv,v)
   @test r["compile_seconds"]==r["recompile_seconds"]==0
   push!(sinks,r["sink"])
   push!(method===:original ? before : after,(Int(r["bytes"]),Int(r["events"])))
  end
  @test sinks[1]==sinks[2]
  @test same(outputs(a.w),outputs(b.w))
 end
 # Every sampled whole-call cost must improve by3%, avoiding allocator noise
 # masquerading as an expected baseline failure. Measured minima exceed6%.
 @test all(100*after[i][1]<97*before[i][1]&&100*after[i][2]<97*before[i][2] for i in eachindex(before)) # RED costgate
end

@testset "Generic weight constants" begin
 for bits in (64,128,256),mode in MODES
  setprecision(BigFloat,bits) do
   setrounding(BigFloat,mode) do
    correctness(BigFloat)
   end
  end
 end
 for T in (Rational{BigInt},Float32,Float64,Rational{Int64});correctness(T);end
 @testset "Whole-call allocation gates" begin
  setprecision(BigFloat,128) do
   setrounding(BigFloat,RoundNearest) do
    for shared in (true,false)
     allocation_gate(BigFloat,:steepest,:mixed,shared)
     allocation_gate(BigFloat,:devex,:positive,shared)
    end
    for pattern in (:lower,:upper)
     allocation_gate(BigFloat,:bfrt,pattern,true)
     allocation_gate(Rational{BigInt},:bfrt,pattern,true)
    end
   end
  end
 end
 @testset "Unchanged hardware and fixed-rational costs" begin
  for T in (Float32,Float64,Rational{Int64}),scope in (T<:Rational ? (:bfrt,) : (:steepest,:devex,:bfrt))
   pattern=scope===:steepest ? :mixed : scope===:devex ? :positive : :upper
   a=fixture(T,32,scope,:dense,pattern,true);b=fixture(T,32,scope,:dense,pattern,true);sv=Val(scope)
   for _ in 1:3,method in METHODS
    v=method===:original ? a : b;reset_fixture!(v);timed(Val(method),sv,v)
   end
   reset_fixture!(a);reset_fixture!(b);x=timed(Val(:original),sv,a);y=timed(Val(:candidate),sv,b)
   @test x["compile_seconds"]==x["recompile_seconds"]==y["compile_seconds"]==y["recompile_seconds"]==0
   @test (x["bytes"],x["events"],x["sink"])==(y["bytes"],y["events"],y["sink"])
  end
 end
end

end
