# The ordinary entry admits only the native publisher. A private typed writer
# boundary lets tests inject a throwing store without adding a caller callback.
function _write_numeric!(::NativePublisher,e,i,field,value)
    e.recovery.counts.numeric_writes+=1
    isfinite(value)&&(field!=4||value>0.)||throw(NumericPublicationError())
    (e.ws.primal,e.ws.reduced_costs,e.ws.costs,e.ws.pricing_weights)[field][i]=value
    e.counters.touched_entries+=1
    nothing
end
function _reserve_journal!(e)
    p=e.proposal;j=e.journal;N=length(e.ws.costs)
    p.owner===e.owner===j.owner===e.recovery.owner && 0<=p.used<=N || return false
    all(a->length(a)>=N,(p.ids,p.stamps,p.masks,p.states,j.ids,j.stamps,j.masks,j.states,p.values...,j.values...)) || return false
    1<=p.leaving_row<=length(e.ws.basis.basic_indices) && e.ws.basis.basic_indices[p.leaving_row]==p.leaving && e.invariants.basic_row[p.entering]==0 || return false
    for k in 1:p.used
        i=p.ids[k]
        1<=i<=N && p.stamps[i]==p.epoch && p.masks[i]!=0 && p.masks[i]&0xe0==0 || return false
    end
    true
end
function _gather_journal!(e)
    p=e.proposal;j=e.journal;w=e.ws;c=e.recovery.counts
    j.used=0
    if j.epoch==typemax(UInt32);fill!(j.stamps,UInt32(0));j.epoch=UInt32(1);c.reset_entries+=length(j.stamps)
    else;j.epoch+=UInt32(1)
    end
    j.old_basis_row=p.leaving_row;j.old_basic_index=p.leaving;j.old_entering_index=p.entering
    j.old_entering_state=w.basis.states[p.entering];j.old_leaving_state=w.basis.states[p.leaving]
    j.old_iterations=w.iterations;j.old_refactorizations=w.refactorizations;j.old_perturbed=w.perturbed
    for k in 1:p.used
        i=p.ids[k]
        if j.stamps[i]!=j.epoch
            j.used+=1;j.ids[j.used]=i;j.stamps[i]=j.epoch;j.masks[i]=0x00;c.journal_entries+=1
        end
        fresh=p.masks[i]&~j.masks[i]
        for field in 1:4
            fresh&(UInt8(1)<<(field-1))==0&&continue
            j.values[field][i]=(w.primal,w.reduced_costs,w.costs,w.pricing_weights)[field][i];c.journal_fields+=1
        end
        if fresh&0x10!=0
            i!=p.entering&&i!=p.leaving&&(j.states[i]=w.basis.states[i])
            c.journal_fields+=1
        end
        j.masks[i]|=fresh
    end
    j.active=true
    nothing
end
function restore_journal!(e::EngineState)::Nothing
    j=e.journal;j.active||return nothing
    w=e.ws;c=e.recovery.counts
    for k in 1:j.used
        i=j.ids[k];mask=j.masks[i];c.undo_entries+=1
        for field in 1:4
            mask&(UInt8(1)<<(field-1))==0&&continue
            (w.primal,w.reduced_costs,w.costs,w.pricing_weights)[field][i]=j.values[field][i]
            c.undo_fields+=1;e.counters.touched_entries+=1
        end
        if mask&0x10!=0
            w.basis.states[i]=i==j.old_entering_index ? j.old_entering_state : i==j.old_basic_index ? j.old_leaving_state : j.states[i]
            c.undo_fields+=1
        end
    end
    w.basis.basic_indices[j.old_basis_row]=j.old_basic_index
    e.invariants.basic_row[j.old_entering_index]=0;e.invariants.basic_row[j.old_basic_index]=j.old_basis_row
    w.iterations=j.old_iterations;w.refactorizations=j.old_refactorizations;w.perturbed=j.old_perturbed
    j.active=false;e.recovery.in_commit=false
    e.kernels.factor_valid=false;_drop_all_proofs!(e);invalidate!(e,:journal_restored)
    nothing
end
function _reset_episode!(e)
    r=e.recovery
    r.rebuilds=0;r.row_corrections=0;r.direction_corrections=0;r.direction_key=0
    r.has_repriced=false;r.active_row=0;r.rejection_generation=UInt64(0)
    r.cause=Ready;r.pending_failure=Ready;r.stage=Normal;r.message=:none
end
function _commit_step!(e,publisher,event_sink)::StepOutcome
    r=e.recovery;p=e.proposal;w=e.ws
    r.finished&&return StepOutcome(InvalidState)
    p.valid&&p.stage==0x03&&_proposal_proofs(e;direction=true,bfrt=p.flip_used>0)||return StepOutcome(InvalidState)
    e.clock()&&return StepOutcome(Stopped)
    w.iterations<w.options.iteration_limit||return StepOutcome(Exhausted)
    r.since_refactor<e.policy.refactor_limit||return StepOutcome(Exhausted)
    if !_reserve_journal!(e)
        p.valid=false;p.stage=0x00;r.fatal=true;return StepOutcome(InvalidState)
    end
    _gather_journal!(e);r.in_commit=true;factor_started=false
    try
        e.clock()&&(e.journal.active=false;r.in_commit=false;return StepOutcome(Stopped))
        r.counts.factor_updates+=1;factor_started=true
        J.replace_column!(w.factorization,e.supports[2].values,p.leaving_row;zero_tolerance=e.policy.zero_tolerance)
        if e.clock();restore_journal!(e);r.stage=RebuildBasis;return StepOutcome(Stopped);end
        for k in 1:e.journal.used
            i=e.journal.ids[k];mask=p.masks[i]
            for field in 1:4
                mask&(UInt8(1)<<(field-1))==0&&continue
                _write_numeric!(publisher,e,i,field,p.values[field][i])
            end
            if mask&0x10!=0;w.basis.states[i]=p.states[i];r.counts.state_writes+=1;end
        end
        if e.clock();restore_journal!(e);r.stage=RebuildBasis;return StepOutcome(Stopped);end
        w.basis.basic_indices[p.leaving_row]=p.entering
        e.invariants.basic_row[p.leaving]=0;e.invariants.basic_row[p.entering]=p.leaving_row
        _advance_generation!(e)
        for k in 1:e.journal.used;_classify_owned!(e,e.journal.ids[k]);end
        if !e.invariants.valid
            # Rare generation wrap, never a normal per-pivot scan.
            _install_membership!(e;validated_basis=true)
        end
        w.perturbed=p.planned_perturbed;w.iterations+=1
        e.counters.accepted_pivots+=1;r.since_refactor+=1
        r.stagnation=iszero(p.primal_step)&&iszero(p.dual_step) ? r.stagnation+1 : 0
        r.maintenance_due=r.since_refactor>=e.policy.refactor_limit || r.stagnation>=e.policy.stagnation_window
        e.journal.active=false;r.in_commit=false;p.valid=false;p.stage=0x00
        _reset_episode!(e)
    catch err
        factor_started&&restore_journal!(e)
        r.stage=RebuildBasis
        (err isa NumericPublicationError || J._is_numerical_exception(err)) && return StepOutcome(factor_started ? (err isa NumericPublicationError ? NumericWriteFailed : FactorInvalid) : InvalidState)
        rethrow()
    end
    # Event code is outside the rollback/numerical handler and write interval.
    event=CompletionEvent(e.generation,w.iterations,Int128(w.progress.iteration_offset)+w.iterations,
        Int128(w.progress.refactorization_offset)+w.refactorizations,p.entering,p.leaving_row,p.primal_step,p.dual_step)
    r.counts.events+=1;event_sink(event)
    StepOutcome(Committed,p.entering,p.leaving_row)
end
commit_step!(e::EngineState;event_sink=NoEvents())=_commit_step!(e,NativePublisher(),event_sink)
