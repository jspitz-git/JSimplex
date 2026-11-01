# All arrays below have fixed physical length; only used prefixes are sorted.
function _new_step_proposal(owner,ws)
    m=length(ws.basis.basic_indices);N=length(ws.costs);s=ws.scratch
    for a in (s.candidates,s.ratio_optional,s.flips,s.ratio_steps,s.ratio_gains)
        resize!(a,N) # phase setup only; never a per-proposal resize
    end
    StepProposal(values=ntuple(_->Vector{Float64}(undef,N),4),ids=Vector{Int}(undef,N),
        stamps=zeros(UInt32,N),masks=Vector{UInt8}(undef,N),states=Vector{J.VariableState}(undef,N),
        candidates=s.candidates,optional=s.ratio_optional,flips=s.flips,steps=s.ratio_steps,gains=s.ratio_gains,
        flip_stamps=zeros(UInt32,N),rhs=_zero_scratch(s.row_rhs),rejected_rows=SparseSet(m),owner=owner)
end
function _expire_row_rejections!(e)
    p=e.proposal
    if p.rejected_generation!=e.generation
        while p.rejected_rows.used>0
            set_present!(p.rejected_rows,p.rejected_rows.ids[p.rejected_rows.used],false)
        end
        p.rejected_generation=e.generation
    end
end
function reject_leaving!(e::EngineState,row::Int)
    _expire_row_rejections!(e)
    set_present!(e.proposal.rejected_rows,row,true)
    e.proposal.valid=false;e.proposal.stage=0x00;e.counters.rejections+=1
    nothing
end
function choose_leaving(e::EngineState)::Int
    p=e.proposal;p.selection=:invalid
    e.invariants.valid && e.invariants.dual_bad.used==0 || return 0
    _expire_row_rejections!(e)
    if p.rejected_rows.used>=e.policy.max_leaving;p.selection=:exhausted;return 0;end
    best=0;score=(typemin(Int),0.);ws=e.ws;s=e.invariants.primal_bad
    for k in 1:s.used
        row=s.ids[k];p.counts.leaving_entries+=1
        p.rejected_rows.position[row]!=0 && continue
        i=ws.basis.basic_indices[row];x=ws.primal[i]
        v=max(isfinite(ws.lower[i]) ? ws.lower[i].value-x : 0.,isfinite(ws.upper[i]) ? x-ws.upper[i].value : 0.)
        isfinite(v) && v>e.policy.primal_tolerance || (p.selection=:uncertain;return 0)
        w=ws.pricing_weights[i]
        isfinite(w)&&w>0 || (p.selection=:uncertain;return 0)
        candidate=J._dual_pricing_score(v,w,true,Val(:scaled))
        if best==0 || candidate>score || (candidate==score && row<best)
            best=row;score=candidate
        end
    end
    p.selection=best>0 ? :ready : s.used==0 ? :feasible : :exhausted
    best
end
function _clear_flips!(p)
    for k in 1:p.flip_used;p.flip_stamps[p.flips[k]]=UInt32(0);end
    p.flip_used=0;p.optional_used=0
end
function _push_flip!(p,i)
    p.flip_used+=1;p.flips[p.flip_used]=i;p.flip_stamps[i]=p.epoch
end
_boxed(ws,i)=isfinite(ws.lower[i])&&isfinite(ws.upper[i])
function _ratio_candidate!(e,entering)
    p=e.proposal;ws=e.ws;q=e.supports[3];_clear_flips!(p)
    p.counts.candidate_checks+=1
    remaining=p.violation;theta=p.steps[entering];tol=e.policy.dual_tolerance;ptol=e.policy.primal_tolerance
    for k in 1:q.used
        i=q.ids[k];p.counts.candidate_entries+=1
        state=ws.basis.states[i]
        (state==J.BASIC || J._is_fixed(ws.lower[i],ws.upper[i])) && continue
        coefficient=p.orientation*q.values[i];price=ws.reduced_costs[i]-theta*coefficient
        isfinite(price)||return false
        if i==entering
            abs(price)<=tol || return false
            continue
        end
        feasible=J._dual_price_feasible(state,price,tol)
        opposite=state==J.AT_LOWER ? J.AT_UPPER : J.AT_LOWER
        can_flip=_boxed(ws,i) && J._dual_pivot_eligible(ws,i,coefficient,0.) && J._dual_price_feasible(opposite,price,tol)
        if !feasible
            can_flip||return false
            remaining-=p.gains[i]
            isfinite(remaining)&&remaining>=-ptol||return false
            _push_flip!(p,i)
        elseif can_flip
            p.optional_used+=1;p.optional[p.optional_used]=i
        end
    end
    if _boxed(ws,entering)
        capacity=p.gains[entering]
        sort!(@view(p.optional[1:p.optional_used]);alg=QuickSort,by=i->(p.steps[i],i))
        for k in 1:p.optional_used
            remaining<=capacity+ptol && break
            i=p.optional[k];gain=p.gains[i]
            gain<=remaining+ptol || continue
            remaining-=gain;_push_flip!(p,i)
        end
        remaining<=capacity+ptol || return false
    end
    isfinite(remaining)&&remaining>=-ptol
end
function _ratio!(e)::StepOutcome
    p=e.proposal;ws=e.ws;q=e.supports[3];tol=e.policy.dual_tolerance;ptol=e.policy.primal_tolerance
    cutoff=J._dual_pivot_cutoff(Float64);small=false;p.candidate_used=0
    for k in 1:q.used
        i=q.ids[k];p.counts.ratio_entries+=1
        state=ws.basis.states[i]
        (state==J.BASIC || J._is_fixed(ws.lower[i],ws.upper[i])) && continue
        coefficient=p.orientation*q.values[i]
        isfinite(coefficient)||return StepOutcome(RatioUncertain)
        J._dual_pivot_eligible(ws,i,coefficient,0.) || continue
        gain=0.
        if _boxed(ws,i)
            width=ws.upper[i].value-ws.lower[i].value;gain=abs(coefficient)*width
            isfinite(width)&&isfinite(gain)&&!(width>0 && iszero(gain)) || return StepOutcome(RatioUncertain)
        end
        p.gains[i]=gain
        step=ws.reduced_costs[i]/coefficient
        isfinite(step)||return StepOutcome(RatioUncertain)
        # Tolerated negative breakpoints become a pending entering-cost shift;
        # do not move backwards in the oriented dual direction.
        p.steps[i]=max(0.,step)
        if !J._dual_pivot_eligible(ws,i,coefficient,cutoff);small=true;continue;end
        p.candidate_used+=1;p.candidates[p.candidate_used]=i
    end
    sort!(@view(p.candidates[1:p.candidate_used]);alg=QuickSort,by=i->(p.steps[i],i))
    capacity=0.;unbounded=false;first=1;attempts=0
    while first<=p.candidate_used
        i=p.candidates[first];limit=p.steps[i]+tol/abs(q.values[i]);isfinite(limit)||return StepOutcome(RatioUncertain)
        last=first
        while last<p.candidate_used && p.steps[p.candidates[last+1]]<=limit
            last+=1;j=p.candidates[last];limit=min(limit,p.steps[j]+tol/abs(q.values[j]))
        end
        for k in first:last
            j=p.candidates[k]
            if _boxed(ws,j);capacity+=p.gains[j];isfinite(capacity)||return StepOutcome(RatioUncertain)
            else;unbounded=true
            end
        end
        if unbounded || capacity+ptol>=p.violation
            sort!(@view(p.candidates[first:last]);alg=QuickSort,by=j->(-abs(q.values[j]),j))
            for k in first:last
                j=p.candidates[k]
                e.recovery.rejected_entering.position[j]!=0&&continue
                attempts+=1;attempts<=e.policy.max_entering||return StepOutcome(RatioUncertain)
                e.recovery.entering_attempts<e.policy.max_entering||return StepOutcome(RatioUncertain)
                e.recovery.entering_attempts+=1
                if _ratio_candidate!(e,j)
                    p.entering=j;p.theta=p.steps[j];p.dual_step=p.orientation*p.theta;p.stage=0x01
                    return StepOutcome(Ready,j,p.leaving_row)
                end
            end
            unbounded&&return StepOutcome(RatioUncertain)
        end
        first=last+1
    end
    _clear_flips!(p)
    StepOutcome(small || capacity+ptol>=p.violation ? RatioUncertain : Exhausted)
end
