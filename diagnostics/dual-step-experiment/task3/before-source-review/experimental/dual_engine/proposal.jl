function _begin_proposal!(e)
    p=e.proposal;p.valid=false;p.generation=e.generation;p.used=0;p.stage=0x00
    p.candidate_used=0;p.optional_used=0;p.flip_used=0;p.entering=0;p.leaving=0;p.leaving_row=0
    p.row_ticket=UInt64(0);p.direction_ticket=UInt64(0);p.bfrt_ticket=UInt64(0)
    p.planned_perturbed=e.ws.perturbed
    if p.epoch==typemax(UInt32)
        fill!(p.stamps,UInt32(0));fill!(p.flip_stamps,UInt32(0));p.epoch=UInt32(1)
        p.counts.metadata_resets+=2length(p.stamps)
    else;p.epoch+=UInt32(1)
    end
    e.counters.proposals+=1
    nothing
end
function _proposal_proofs(e;direction=false,bfrt=false)
    p=e.proposal
    e.invariants.valid && e.invariants.dual_bad.used==0 && p.owner===e.owner &&
        p.generation==e.generation && p.rhs.values===e.ws.scratch.row_rhs &&
        p.factor_id==objectid(e.ws.factorization) && _receipt_valid(e,1) &&
        p.row_ticket==e.kernels.solves[1].ticket==e.kernels.price_ticket &&
        e.supports[3].evidence_generation==e.generation || return false
    direction && !(_receipt_valid(e,2) && p.direction_ticket==e.kernels.solves[2].ticket) && return false
    bfrt && !(_receipt_valid(e,3) && p.bfrt_ticket==e.kernels.solves[3].ticket) && return false
    true
end
function _column_rhs!(e,index,change=1.;clear=true)
    q=e.proposal.rhs;clear&&clear_scratch!(q)
    A=e.ws.problem.A;m,n=size(A)
    if index<=n
        for p in J.SparseArrays.nzrange(A,index)
            add_scratch!(q,A.rowval[p],A.nzval[p]*change)
            e.proposal.counts.flip_rhs_terms+=1
        end
    else
        set_scratch!(q,index-n,q.values[index-n]-change)
        e.proposal.counts.flip_rhs_terms+=1
    end
    nothing
end
function propose_step!(e::EngineState)::StepOutcome
    _begin_proposal!(e);p=e.proposal;ws=e.ws
    e.invariants.valid && e.invariants.dual_bad.used==0 && _bindings_ok(e) && p.owner===e.owner && p.rhs.values===ws.scratch.row_rhs || return StepOutcome(InvalidState)
    e.kernels.factor_valid||return StepOutcome(FactorInvalid)
    e.clock()&&return StepOutcome(Stopped)
    row=choose_leaving(e)
    row==0&&return StepOutcome(p.selection==:feasible ? PrimalFeasible : p.selection==:exhausted ? Exhausted : RatioUncertain)
    p.leaving_row=row;p.leaving=ws.basis.basic_indices[row]
    p.below=isfinite(ws.lower[p.leaving]) && ws.lower[p.leaving].value-ws.primal[p.leaving]>e.policy.primal_tolerance
    p.bound=(p.below ? ws.lower[p.leaving] : ws.upper[p.leaving]).value
    p.orientation=p.below ? -1. : 1.;p.violation=abs(ws.primal[p.leaving]-p.bound)
    clear_scratch!(p.rhs);set_scratch!(p.rhs,row,1.)
    out=basis_solve!(e,:btran,p.rhs.values);out.reason==Ready||return out
    out=price_row!(e);out.reason==Ready||return out
    out=check_row!(e,row);out.reason==Ready||return out
    p.row_ticket=e.kernels.solves[1].ticket;p.factor_id=objectid(ws.factorization)
    out=_ratio!(e);out.reason==Ready||return out
    out=validate_proposal!(e);out.reason==Ready||return out
    plan_writes!(e)
end
function validate_proposal!(e::EngineState)::StepOutcome
    p=e.proposal
    if p.stage<0x01 || !_proposal_proofs(e;direction=p.stage>=0x02,bfrt=p.stage>=0x02&&p.flip_used>0)
        p.valid=false;return StepOutcome(InvalidState)
    end
    e.clock()&&(p.valid=false;return StepOutcome(Stopped))
    p.stage>=0x02&&return StepOutcome(Ready,p.entering,p.leaving_row)
    p.stage=0x00 # a failed validation cannot retry solves under the same proposal
    try;_column_rhs!(e,p.entering)
    catch err;err isa ArgumentError||rethrow();return StepOutcome(DirectionUnreliable)
    end
    out=basis_solve!(e,:ftran,p.rhs.values);out.reason==Ready||return out
    p.direction_ticket=e.kernels.solves[2].ticket;p.pivot=e.supports[2].values[p.leaving_row]
    row_pivot=e.supports[3].values[p.entering]
    agreement=e.policy.pivot_error_tolerance*max(abs(p.pivot),abs(row_pivot))
    J._pivot_agrees(row_pivot,p.pivot,agreement) && abs(p.pivot)>e.policy.zero_tolerance || return StepOutcome(DirectionUnreliable)
    out=check_direction!(e,e.kernels.solves[2].rhs,p.pivot);out.reason==Ready||return out
    if p.flip_used>0
        clear_scratch!(p.rhs)
        try
            for k in 1:p.flip_used
                i=p.flips[k];change=e.ws.basis.states[i]==J.AT_LOWER ? e.ws.upper[i].value-e.ws.lower[i].value : e.ws.lower[i].value-e.ws.upper[i].value
                _column_rhs!(e,i,change;clear=false)
            end
        catch err;err isa ArgumentError||rethrow();return StepOutcome(DirectionUnreliable)
        end
        out=basis_solve!(e,:bfrt,p.rhs.values);out.reason==Ready||return out
        p.bfrt_ticket=e.kernels.solves[3].ticket
        out=check_direction!(e,e.kernels.solves[3].rhs,0.;kind=:bfrt);out.reason==Ready||return out
    end
    delta=e.ws.primal[p.leaving]-p.bound
    p.flip_used>0&&(delta-=e.supports[4].values[p.leaving_row])
    p.primal_step=delta/p.pivot
    isfinite(p.primal_step)&&isfinite(p.dual_step)||return StepOutcome(NumericWriteFailed)
    !iszero(delta)&&iszero(p.primal_step)&&return StepOutcome(RatioUncertain)
    p.stage=0x02
    StepOutcome(Ready,p.entering,p.leaving_row)
end
function _plan_field!(e,i,field,x)
    p=e.proposal
    isfinite(x)&&(field!=4||x>0.)||return false
    old=(e.ws.primal,e.ws.reduced_costs,e.ws.costs,e.ws.pricing_weights)[field][i]
    isequal(x,old)&&return true
    _plan_id!(p,i)
    bit=UInt8(1)<<(field-1)
    p.masks[i]&bit==0 || throw(ArgumentError("duplicate planned numeric field"))
    p.values[field][i]=x;p.masks[i]|=bit;p.counts.plan_fields+=1
    true
end
function _plan_id!(p,i)
    if p.stamps[i]!=p.epoch
        p.used+=1;p.ids[p.used]=i;p.stamps[i]=p.epoch;p.masks[i]=0x00
        p.counts.plan_union_entries+=1
    end
    nothing
end
function _plan_state!(p,i,state)
    _plan_id!(p,i);p.states[i]=state;p.masks[i]|=0x10
end
function plan_writes!(e::EngineState)::StepOutcome
    p=e.proposal;ws=e.ws
    if p.stage<0x02 || !_proposal_proofs(e;direction=true,bfrt=p.flip_used>0)
        p.valid=false;return StepOutcome(InvalidState)
    end
    e.clock()&&(p.valid=false;return StepOutcome(Stopped))
    p.stage==0x03&&return StepOutcome(Ready,p.entering,p.leaving_row)
    p.valid=false;p.stage=0x00 # partial planning can never be reused after failure
    row=e.supports[3];direction=e.supports[2];bfrt=e.supports[4]
    reference_weight=0.
    for k in 1:row.used
        i=row.ids[k];p.counts.devex_terms+=1
        ws.devex_reference[i]&&(reference_weight+=row.values[i]^2)
        isfinite(reference_weight)||return StepOutcome(NumericWriteFailed)
    end
    denominator=p.pivot^2
    isfinite(denominator)&&denominator>0 || return StepOutcome(NumericWriteFailed)
    entering_weight=max(1.,reference_weight/denominator)
    isfinite(entering_weight)&&entering_weight>0 || return StepOutcome(NumericWriteFailed)
    # Basic primal and Devex writes share the complete union of direction and
    # BFRT support. A canceled displacement is still a planned/checkable value.
    for q in (direction,bfrt)
        q===bfrt && p.flip_used==0 && continue
        for k in 1:q.used
            r=q.ids[k]
            q===bfrt && direction.stamps[r]==direction.epoch && continue
            i=ws.basis.basic_indices[r];d=direction.values[r]
            x=i==p.leaving ? p.bound : ws.primal[i]-p.primal_step*d-(p.flip_used>0 ? bfrt.values[r] : 0.)
            _plan_field!(e,i,1,x)||return StepOutcome(NumericWriteFailed)
            if !iszero(d)
                w=max(ws.pricing_weights[i],d^2*entering_weight)
                _plan_field!(e,i,4,w)||return StepOutcome(NumericWriteFailed)
            end
        end
    end
    for k in 1:p.flip_used
        i=p.flips[k];state=ws.basis.states[i]==J.AT_LOWER ? J.AT_UPPER : J.AT_LOWER
        x=state==J.AT_UPPER ? ws.upper[i].value : ws.lower[i].value
        _plan_field!(e,i,1,x)||return StepOutcome(NumericWriteFailed)
        _plan_state!(p,i,state)
    end
    entering_value=ws.primal[p.entering]+p.primal_step
    lo=ws.lower[p.entering];hi=ws.upper[p.entering]
    if (isfinite(lo)&&lo.value-entering_value>e.policy.primal_tolerance)||(isfinite(hi)&&entering_value-hi.value>e.policy.primal_tolerance)
        return StepOutcome(RatioUncertain)
    end
    _plan_field!(e,p.entering,1,entering_value)||return StepOutcome(NumericWriteFailed)
    _plan_field!(e,p.entering,4,entering_weight)||return StepOutcome(NumericWriteFailed)
    for k in 1:row.used
        i=row.ids[k];(ws.basis.states[i]==J.BASIC || i==p.entering)&&continue
        price=ws.reduced_costs[i]-p.dual_step*row.values[i]
        state=p.flip_stamps[i]==p.epoch ? (ws.basis.states[i]==J.AT_LOWER ? J.AT_UPPER : J.AT_LOWER) : ws.basis.states[i]
        J._is_fixed(ws.lower[i],ws.upper[i]) || J._dual_price_feasible(state,price,e.policy.dual_tolerance) || return StepOutcome(RatioUncertain)
        _plan_field!(e,i,2,price)||return StepOutcome(NumericWriteFailed)
    end
    _plan_field!(e,p.leaving,2,-p.dual_step)||return StepOutcome(NumericWriteFailed)
    _plan_field!(e,p.entering,2,0.)||return StepOutcome(NumericWriteFailed)
    if p.theta==0. && !iszero(ws.reduced_costs[p.entering])
        _plan_field!(e,p.entering,3,ws.costs[p.entering]-ws.reduced_costs[p.entering])||return StepOutcome(NumericWriteFailed)
        p.planned_perturbed=true
    end
    _plan_state!(p,p.leaving,p.below ? J.AT_LOWER : J.AT_UPPER)
    _plan_state!(p,p.entering,J.BASIC)
    e.clock()&&return StepOutcome(Stopped)
    p.valid=true;p.stage=0x03
    StepOutcome(Ready,p.entering,p.leaving_row)
end
