function _set_attempt_row!(e,row)
    r=e.recovery
    if r.rejection_generation!=e.generation || r.active_row!=row
        s=r.rejected_entering
        while s.used>0;set_present!(s,s.ids[s.used],false);end
        r.entering_attempts=0;r.row_corrections=0;r.direction_corrections=0;r.direction_key=0
        r.rejection_generation=e.generation;r.active_row=row
    end
    nothing
end
function _transition!(e,stage)
    e.recovery.stage=stage;e.recovery.counts.transitions+=1
    nothing
end
function _mark_factor_invalid!(e)
    e.kernels.factor_valid=false;_drop_all_proofs!(e);invalidate!(e,:repair_factor_failure)
    nothing
end
function _repair_solve!(e,slot,rhs)
    r=e.kernels.solves[slot];q=e.supports[_output_slot(slot)];ks=e.kernels
    ks.factor_valid||return StepOutcome(FactorInvalid)
    e.clock()&&return StepOutcome(Stopped)
    _rhs_guard(e,rhs,q.values);r.valid=false
    r.rhs_used=0;r.unit_row=0
    for i in eachindex(r.rhs)
        x=rhs[i];ks.counts.rhs_capture_entries+=1;isfinite(x)||return _failed(slot)
        r.rhs[i]=x
        if !iszero(x);r.rhs_used+=1;r.rhs_ids[r.rhs_used]=i;end
    end
    r.rhs_used==1&&(r.unit_row=r.rhs[r.rhs_ids[1]]==1. ? r.rhs_ids[1] : 0)
    e.recovery.failed_slot=slot
    try
        if slot==1;e.counters.btran+=1;J.transpose_solve!(q.values,e.ws.factorization,r.rhs)
        elseif slot==2;e.counters.ftran+=1;J.forward_solve!(q.values,e.ws.factorization,r.rhs)
        else;e.counters.bfrt_ftran+=1;J.forward_solve!(q.values,e.ws.factorization,r.rhs)
        end
    catch err
        _mark_factor_invalid!(e);J._is_numerical_exception(err)&&return StepOutcome(FactorInvalid);rethrow()
    end
    try;_capture_output!(q,q.values,ks.counts)
    catch err;err isa ArgumentError||rethrow();return _failed(slot)
    end
    e.counters.scanned_entries+=length(q.values);e.counters.dense_routes+=1
    _publish_repaired_output!(e,slot)
    e.clock() ? StepOutcome(Stopped) : StepOutcome(Ready)
end
function _publish_repaired_output!(e,slot)
    ks=e.kernels;r=ks.solves[slot];q=e.supports[_output_slot(slot)]
    if ks.next_ticket==typemax(UInt64);_drop_all_proofs!(e);ks.next_ticket=UInt64(0);end
    ks.next_ticket+=UInt64(1);ks.latest=Base.setindex(ks.latest,ks.next_ticket,slot)
    r.ticket=ks.next_ticket;r.generation=e.generation;r.owner=e.owner;r.output=q.values
    r.factor_id=objectid(e.ws.factorization);r.valid=true;q.evidence_generation=e.generation
    slot==1&&(ks.price_ticket=UInt64(0);e.supports[3].evidence_generation=UInt64(0))
    nothing
end
# Cold/failure equation kernel, original B, same arithmetic precision. The
# residual shares the already-owned indexed row_rhs; only correction is new.
function _equation_residual!(e,slot,approx,rhs,pivot=0.)
    e.recovery.residual_valid=false
    q=e.proposal.rhs;m=length(e.ws.basis.basic_indices);A=e.ws.problem.A;n=size(A,2)
    length(approx)==length(rhs)==m||throw(DimensionMismatch("repair equation"))
    (Base.mightalias(approx,q.values)||Base.mightalias(rhs,q.values)||Base.mightalias(approx,e.recovery.correction)||Base.mightalias(rhs,e.recovery.correction))&&throw(ArgumentError("repair aliases input"))
    clear_scratch!(q);fill!(e.residual_scale,0.)
    try
        if slot==1
            for col in 1:m
                value=rhs[col];scale=abs(value);isfinite(value)||return false
                index=e.ws.basis.basic_indices[col]
                if index<=n
                    for k in J.SparseArrays.nzrange(A,index)
                        term=A.nzval[k]*approx[A.rowval[k]];e.recovery.counts.residual_terms+=1
                        value-=term;scale+=abs(term)
                    end
                else
                    term=-approx[index-n];value-=term;scale+=abs(term);e.recovery.counts.residual_terms+=1
                end
                isfinite(scale)||return false
                set_scratch!(q,col,value);e.residual_scale[col]=scale
            end
        else
            for row in 1:m
                x=rhs[row];set_scratch!(q,row,x);e.residual_scale[row]=abs(x)
            end
            for col in 1:m
                x=approx[col];isfinite(x)||return false;iszero(x)&&continue
                index=e.ws.basis.basic_indices[col]
                if index<=n
                    for k in J.SparseArrays.nzrange(A,index)
                        row=A.rowval[k];term=A.nzval[k]*x;add_scratch!(q,row,-term)
                        e.residual_scale[row]+=abs(term);e.recovery.counts.residual_terms+=1
                    end
                else
                    row=index-n;add_scratch!(q,row,x);e.residual_scale[row]+=abs(x);e.recovery.counts.residual_terms+=1
                end
            end
        end
    catch err
        err isa ArgumentError||rethrow();return false
    end
    reliable=true
    for row in 1:m
        value=q.values[row];scale=e.residual_scale[row]
        tol=max(e.policy.zero_tolerance,256eps(Float64)*(scale+1.),slot==1 ? 0. : sqrt(eps(Float64))*abs(pivot))
        isfinite(value)&&isfinite(scale)&&isfinite(tol)||return false
        abs(value)<=tol||(reliable=false)
    end
    e.recovery.residual_valid=true
    reliable
end
function _correct_equation!(e,slot::Int,approx::Vector{Float64},rhs::Vector{Float64};pivot=0.)::StepOutcome
    slot in (1,2,3)||throw(ArgumentError("correction slot"))
    (e.recovery.finished||e.recovery.fatal)&&return StepOutcome(InvalidState)
    e.recovery.owner===e.owner||return StepOutcome(InvalidState)
    e.kernels.factor_valid||return StepOutcome(FactorInvalid)
    e.clock()&&return StepOutcome(Stopped)
    _rhs_guard(e,rhs,approx)
    protected=(e.ws.primal,e.ws.reduced_costs,e.ws.costs,e.ws.pricing_weights,e.ws.factorization.work,e.ws.problem.A.nzval)
    any(a->Base.mightalias(approx,a),protected)&&throw(ArgumentError("correction aliases committed/factor storage"))
    _equation_residual!(e,slot,approx,rhs,pivot)
    # The precheck computes the residual even if it is already acceptable; a
    # requested correction is an explicit, counted native solve, never a flag.
    residual=e.proposal.rhs.values;delta=e.recovery.correction
    if !e.recovery.residual_valid;e.recovery.failed_slot=0;return _failed(slot);end
    e.proposal.valid=false
    e.counters.corrections+=1
    try
        if slot==1;e.counters.btran+=1;J.transpose_solve!(delta,e.ws.factorization,residual)
        elseif slot==2;e.counters.ftran+=1;J.forward_solve!(delta,e.ws.factorization,residual)
        else;e.counters.bfrt_ftran+=1;J.forward_solve!(delta,e.ws.factorization,residual)
        end
    catch err
        _mark_factor_invalid!(e);J._is_numerical_exception(err)&&return StepOutcome(FactorInvalid);rethrow()
    end
    for i in eachindex(approx)
        value=approx[i]+delta[i]
        isfinite(delta[i])&&isfinite(value)||return _failed(slot)
        approx[i]=value
    end
    e.clock()&&return StepOutcome(Stopped)
    _equation_residual!(e,slot,approx,rhs,pivot) ? StepOutcome(Ready) : _failed(slot)
end
function _retry_ratio!(e)
    p=e.proposal
    _proposal_proofs(e)||return StepOutcome(InvalidState)
    p.valid=false;p.stage=0x00;p.used=0
    out=_ratio!(e);out.reason==Ready||return out
    out=validate_proposal!(e);out.reason==Ready||return out
    plan_writes!(e)
end
function _resume_corrected_row!(e)
    row=e.proposal.leaving_row;w=e.ws
    _begin_proposal!(e);p=e.proposal
    p.leaving_row=row;p.leaving=w.basis.basic_indices[row]
    p.below=isfinite(w.lower[p.leaving])&&w.lower[p.leaving].value-w.primal[p.leaving]>e.policy.primal_tolerance
    p.bound=(p.below ? w.lower[p.leaving] : w.upper[p.leaving]).value
    p.orientation=p.below ? -1. : 1.;p.violation=abs(w.primal[p.leaving]-p.bound)
    _proposal_after_row!(e)
end
function _repair_target!(e,slot)
    r=e.recovery;p=e.proposal;record=e.kernels.solves[slot];q=e.supports[_output_slot(slot)]
    _receipt_valid(e,slot)||return StepOutcome(FactorInvalid)
    if slot==1;r.row_corrections+=1
    else;r.direction_corrections+=1
    end
    p.valid=false;p.stage=0x00;record.valid=false;q.evidence_generation=UInt64(0)
    pivot=slot==2 ? p.pivot : 0.
    out=_correct_equation!(e,slot,q.values,record.rhs;pivot)
    if all(isfinite,q.values) && e.kernels.factor_valid
        _capture_output!(q,q.values,e.kernels.counts);e.counters.scanned_entries+=length(q.values)
        _publish_repaired_output!(e,slot)
    end
    out.reason==Ready||return out
    _transition!(e,Normal)
    if slot==1;return _resume_corrected_row!(e)
    elseif slot==2
        p.direction_ticket=record.ticket
        out=_validate_direction_output!(e);out.reason==Ready||return out
    else
        p.bfrt_ticket=record.ticket
        _proposal_proofs(e;direction=true,bfrt=true)||return StepOutcome(InvalidState)
        out=_finish_direction_proposal!(e);out.reason==Ready||return out
    end
    plan_writes!(e)
end
function _request_rebuild!(e)
    e.recovery.need_primal=true;e.recovery.need_reset=true
    _transition!(e,RebuildBasis)
end
function _route_failure!(e,reason)
    r=e.recovery;p=e.proposal;r.cause=reason
    if reason==Stopped;r.message=:deadline;_transition!(e,Terminate)
    elseif r.fatal;r.message=:invalid_metadata;_transition!(e,Terminate)
    elseif reason==RowUnreliable && r.failed_slot==1 && _receipt_valid(e,1) && r.row_corrections<e.policy.max_corrections
        _transition!(e,CorrectRow)
    elseif reason==DirectionUnreliable && r.failed_slot in (2,3) && _receipt_valid(e,r.failed_slot)
        key=3p.entering+r.failed_slot
        if r.direction_key!=key;r.direction_key=key;r.direction_corrections=0;end
        if r.direction_corrections<e.policy.max_corrections
            _transition!(e,CorrectDirection)
        elseif _proposal_proofs(e)
            set_present!(r.rejected_entering,p.entering,true);e.counters.rejections+=1
            _transition!(e,Normal)
            return _retry_ratio!(e)
        else;_request_rebuild!(e)
        end
    elseif reason in (RatioUncertain,Exhausted) && e.invariants.valid && e.kernels.factor_valid
        _expire_row_rejections!(e)
        p.leaving_row>0&&p.rejected_rows.position[p.leaving_row]==0&&reject_leaving!(e,p.leaving_row)
        if p.rejected_rows.used>=min(e.policy.max_leaving,e.invariants.primal_bad.used);_request_rebuild!(e)
        else;_transition!(e,Normal)
        end
    elseif reason==InvalidState && e.invariants.valid && e.invariants.dual_bad.used>0 && !r.has_repriced
        r.need_primal=false;r.need_reset=false;invalidate!(e,:reprice);_transition!(e,Reprice)
    else;_request_rebuild!(e)
    end
    StepOutcome(Ready)
end
function _rebuild_factor!(e)
    r=e.recovery
    if r.rebuilds>=e.policy.max_rebuilds
        r.cause=Exhausted;r.message=:recovery_exhausted;_transition!(e,LegacyBoundary);return StepOutcome(Exhausted)
    end
    e.clock()&&return StepOutcome(Stopped)
    r.rebuilds+=1;r.row_corrections=0;r.direction_corrections=0;r.direction_key=0
    invalidate!(e,:rebuild);_drop_all_proofs!(e);e.kernels.factor_valid=false
    _basis_inverse!(e.invariants.basic_row,e.ws)
    r.counts.basis_assemblies+=1;B=J._assemble_basis_matrix(e.ws,nothing)
    e.clock()&&return StepOutcome(Stopped)
    r.counts.refactor_attempts+=1;e.counters.refactors+=1
    try;J.refactorize!(e.ws.factorization,B)
    catch err
        J._is_numerical_exception(err)&&return StepOutcome(FactorInvalid);rethrow()
    end
    e.ws.refactorizations+=1;r.counts.refactor_successes+=1;e.kernels.factor_valid=true
    r.since_refactor=0;r.stagnation=0;r.maintenance_due=false;r.need_primal=true;r.need_reset=true
    e.clock()&&return StepOutcome(Stopped)
    _transition!(e,Reprice);StepOutcome(Ready)
end
function _reprice_staged!(e)
    r=e.recovery;p=e.proposal;w=e.ws;A=w.problem.A;m,n=size(A);N=m+n
    e.kernels.factor_valid||return StepOutcome(FactorInvalid)
    p.valid=false;p.stage=0x00;r.staging_ready=false
    r.cost_pending=r.restore_costs
    if r.cost_pending
        r.counts.cost_restore_attempts+=1
        for i in 1:N
            value=i<=n ? w.problem.objective[i] : 0.
            isfinite(value)||return StepOutcome(NumericWriteFailed);p.values[3][i]=value
        end
    end
    costs=r.cost_pending ? p.values[3] : w.costs
    if r.need_primal
        clear_scratch!(p.rhs)
        try
            for i in 1:N
                w.basis.states[i]==J.BASIC&&continue
                x=J._nonbasic_value(w,i);isfinite(x)||return StepOutcome(NumericWriteFailed)
                p.values[1][i]=x;r.counts.reprice_entries+=1
                if i<=n
                    for k in J.SparseArrays.nzrange(A,i)
                        a=A.nzval[k];term=a*x
                        !iszero(a)&&!iszero(x)&&iszero(term)&&return StepOutcome(NumericWriteFailed)
                        add_scratch!(p.rhs,A.rowval[k],-term)
                    end
                else;add_scratch!(p.rhs,i-n,x)
                end
            end
        catch err;err isa ArgumentError||rethrow();return StepOutcome(NumericWriteFailed)
        end
        out=_repair_solve!(e,2,p.rhs.values);out.reason==Ready||return out
        _equation_residual!(e,2,e.supports[2].values,e.kernels.solves[2].rhs)||return StepOutcome(DirectionUnreliable)
        for (row,i) in enumerate(w.basis.basic_indices);p.values[1][i]=e.supports[2].values[row];end
    end
    clear_scratch!(p.rhs)
    for (row,i) in enumerate(w.basis.basic_indices);set_scratch!(p.rhs,row,costs[i]);end
    out=_repair_solve!(e,1,p.rhs.values);out.reason==Ready||return out
    dual=e.supports[1].values
    _equation_residual!(e,1,dual,e.kernels.solves[1].rhs)||return StepOutcome(RowUnreliable)
    for col in 1:n
        value=costs[col]
        for k in J.SparseArrays.nzrange(A,col);value-=A.nzval[k]*dual[A.rowval[k]];r.counts.reprice_entries+=1;end
        isfinite(value)||return StepOutcome(NumericWriteFailed);p.values[2][col]=value
    end
    for row in 1:m
        value=costs[n+row]+dual[row];isfinite(value)||return StepOutcome(NumericWriteFailed);p.values[2][n+row]=value
    end
    for i in w.basis.basic_indices;p.values[2][i]=0.;end
    r.staging_generation=e.generation;r.staging_factor=objectid(w.factorization);r.staging_ready=true;r.has_repriced=true
    _transition!(e,ResetDevex);StepOutcome(Ready)
end
function _publish_reprice!(e)
    r=e.recovery;p=e.proposal;w=e.ws;N=length(w.costs)
    r.staging_ready&&r.staging_generation==e.generation&&r.staging_factor==objectid(w.factorization)&&e.kernels.factor_valid||return StepOutcome(InvalidState)
    e.clock()&&return StepOutcome(Stopped)
    for i in 1:N
        r.need_primal&&(w.primal[i]=p.values[1][i])
        w.reduced_costs[i]=p.values[2][i]
        r.cost_pending&&(w.costs[i]=p.values[3][i])
        if r.need_reset;w.pricing_weights[i]=1.;w.devex_reference[i]=false;end
    end
    if r.need_reset
        for i in w.basis.basic_indices;w.devex_reference[i]=true;end
        r.counts.reset_entries+=2N+length(w.basis.basic_indices)
    end
    if r.cost_pending;w.perturbed=false;r.counts.cost_restores+=1;r.restore_costs=false;end
    _install_membership!(e;validated_basis=true)
    r.staging_ready=false;r.need_primal=false;r.need_reset=false;r.cost_pending=false
    _transition!(e,Normal);StepOutcome(Ready)
end
function recover!(e::EngineState,cause)::StepOutcome
    r=e.recovery;(r.finished||r.fatal)&&return StepOutcome(InvalidState)
    e.journal.active&&restore_journal!(e)
    e.clock()&&return StepOutcome(Stopped)
    if cause===:restore_costs
        r.restore_costs=true;r.need_primal=false;r.need_reset=false
        invalidate!(e,:restore_costs)
        e.kernels.factor_valid ? _transition!(e,Reprice) : _request_rebuild!(e)
    elseif r.stage==Normal
        out=_route_failure!(e,cause isa StepOutcome ? cause.reason : cause)
        if out.reason!=Ready;r.pending_failure=out.reason;return out;end
        e.proposal.valid&&return out
    end
    out=if r.stage==CorrectRow;_repair_target!(e,1)
    elseif r.stage==CorrectDirection;_repair_target!(e,r.failed_slot)
    elseif r.stage==RebuildBasis;_rebuild_factor!(e)
    elseif r.stage==Reprice;_reprice_staged!(e)
    elseif r.stage==ResetDevex;_publish_reprice!(e)
    elseif r.stage==LegacyBoundary;StepOutcome(Exhausted)
    elseif r.stage==Terminate;StepOutcome(r.cause)
    else;StepOutcome(Ready)
    end
    out.reason!=Ready&&!(out.reason==Exhausted&&r.stage==LegacyBoundary)&&(r.pending_failure=out.reason)
    out
end
function _export_ready(e)
    !e.journal.active && !e.recovery.in_commit && !e.recovery.fatal && e.invariants.valid && e.kernels.factor_valid && _bindings_ok(e)
end
function _finish_phase!(e,reason,message;export=false)
    r=e.recovery;ready=export&&_export_ready(e)
    ready&&reason==Exhausted&&(e.counters.legacy_boundaries+=1)
    c=NamedTuple{fieldnames(EngineCounters)}(ntuple(i->getfield(e.counters,i),Val(fieldcount(EngineCounters))))
    repairs=NamedTuple{fieldnames(RecoveryCounts)}(ntuple(i->getfield(r.counts,i),Val(fieldcount(RecoveryCounts))))
    r.finished=true;r.stage=Terminate;r.cause=reason;r.message=message
    PhaseResult{typeof(e.ws),typeof(c),typeof(repairs)}(reason,message,ready ? e.ws : nothing,ready,c,repairs)
end
function run_phase!(e::EngineState;event_sink=NoEvents())::PhaseResult
    r=e.recovery
    r.finished&&return _finish_phase!(e,InvalidState,:consumed)
    while true
        e.clock()&&return _finish_phase!(e,Stopped,:deadline)
        r.fatal&&return _finish_phase!(e,InvalidState,:invalid_metadata)
        if r.pending_failure!=Ready
            cause=r.pending_failure;r.pending_failure=Ready
            routed=_route_failure!(e,cause)
            routed.reason!=Ready&&(r.pending_failure=routed.reason)
            continue
        elseif r.stage==LegacyBoundary
            return _finish_phase!(e,Exhausted,:recovery_exhausted;export=true)
        elseif r.stage==Terminate
            return _finish_phase!(e,r.cause,r.message)
        elseif r.stage==Normal
            if e.invariants.valid&&e.invariants.primal_bad.used==0&&e.invariants.dual_bad.used==0
                return _finish_phase!(e,PrimalFeasible,:working_primal_feasible;export=true)
            end
            e.ws.iterations<e.ws.options.iteration_limit||return _finish_phase!(e,Exhausted,:iteration_limit)
            if r.maintenance_due;_request_rebuild!(e);continue;end
            out=e.proposal.valid ? StepOutcome(Ready) : propose_step!(e)
            if out.reason==Ready
                out=commit_step!(e;event_sink)
                out.reason==Committed&&continue
            elseif out.reason==PrimalFeasible
                return _finish_phase!(e,PrimalFeasible,:working_primal_feasible;export=true)
            end
        else
            out=recover!(e,r.cause)
            out.reason==Ready&&continue
        end
        out.reason==Stopped&&return _finish_phase!(e,Stopped,:deadline)
        if out.reason==Exhausted&&r.stage==LegacyBoundary;continue;end
        r.pending_failure=out.reason
    end
end
