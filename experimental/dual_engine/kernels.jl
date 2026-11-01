_slot(kind::Symbol)=kind===:btran ? 1 : kind===:ftran ? 2 : kind===:bfrt ? 3 : throw(ArgumentError("unknown basis solve kind"))
_output_slot(slot)=slot==3 ? 4 : slot
_failed(slot)=StepOutcome(slot==1 ? RowUnreliable : DirectionUnreliable)
function _forget_output!(q)
    q.used=0;q.evidence_generation=UInt64(0)
    if q.epoch==typemax(UInt32);fill!(q.stamps,UInt32(0));q.epoch=UInt32(1)
    else;q.epoch+=UInt32(1)
    end
    nothing
end
function _capture_output!(q::StampedScratch,values::AbstractVector{Float64},counts)
    length(values)==length(q.values)||throw(DimensionMismatch("output capture"))
    ((values!==q.values&&Base.mightalias(values,q.values))||Base.mightalias(values,q.ids)||Base.mightalias(values,q.stamps))&&throw(ArgumentError("capture aliases metadata or overlapping output"))
    _forget_output!(q)
    try
        for i in eachindex(q.values)
            x=values[i];isnothing(counts)||(counts.output_capture_entries+=1)
            isfinite(x)||throw(ArgumentError("nonfinite native output"))
            q.values[i]=x
            if !iszero(x);q.used+=1;q.ids[q.used]=i;q.stamps[i]=q.epoch;end
        end
    catch
        # Failure-only dense cleanup restores a canonical empty scratch.
        fill!(q.values,0.);fill!(q.stamps,UInt32(0));q.epoch=UInt32(1);q.used=0
        rethrow()
    end
    nothing
end
capture_output!(q::StampedScratch,values::AbstractVector{Float64})=_capture_output!(q,values,nothing)
function _bindings_ok(e)
    s=e.supports;w=e.ws.scratch
    s[1].values===w.rho && s[2].values===w.row_solution && s[3].values===w.tableau_row &&
        s[4].values===w.tau && s[5].values===e.kernels.residual_owner && e.rows.matrix===e.ws.problem.A
end
function _drop_all_proofs!(e)
    for r in e.kernels.solves;r.valid=false;end
    for q in e.supports;q.evidence_generation=UInt64(0);end
    e.kernels.price_ticket=UInt64(0);e.proposal.valid=false
    nothing
end
function _receipt_valid(e,slot)
    r=e.kernels.solves[slot];q=e.supports[_output_slot(slot)]
    e.invariants.valid && e.kernels.factor_valid && _bindings_ok(e) && r.valid && r.owner===e.owner &&
        r.generation==e.generation && r.ticket!=0 && r.ticket==e.kernels.latest[slot] &&
        r.output===q.values && q.evidence_generation==e.generation && r.factor_id==objectid(e.ws.factorization)
end
function _rhs_guard(e,rhs,dest)
    length(rhs)==length(dest)||throw(DimensionMismatch("basis RHS dimension"))
    # Owned inputs may share a saved RHS exactly, but no overlapping native
    # destination, factor scratch, numeric state/model or index metadata.
    protected=(dest,e.ws.factorization.work,e.ws.primal,e.ws.reduced_costs,e.ws.costs,e.ws.pricing_weights,
        e.ws.lower,e.ws.upper,e.ws.problem.A.nzval,e.ws.basis.basic_indices,e.ws.basis.states,
        e.rows.rowptr,e.rows.columns,e.rows.positions)
    any(a->Base.mightalias(rhs,a),protected)&&throw(ArgumentError("RHS aliases protected storage"))
    for q in e.supports
        (Base.mightalias(rhs,q.ids)||Base.mightalias(rhs,q.stamps))&&throw(ArgumentError("RHS aliases support metadata"))
    end
    for r in e.kernels.solves
        rhs!==r.rhs&&Base.mightalias(rhs,r.rhs)&&throw(ArgumentError("overlapping saved RHS"))
    end
    nothing
end
function basis_solve!(e::EngineState,kind::Symbol,rhs::AbstractVector{Float64})::StepOutcome
    slot=_slot(kind);ks=e.kernels;q=e.supports[_output_slot(slot)];r=ks.solves[slot]
    (e.recovery.finished||e.recovery.fatal)&&return StepOutcome(InvalidState)
    ks.factor_valid||return StepOutcome(FactorInvalid)
    e.recovery.since_refactor>=e.policy.refactor_limit&&return StepOutcome(Exhausted)
    e.invariants.valid&&_bindings_ok(e)||return StepOutcome(InvalidState)
    e.clock()&&return StepOutcome(Stopped)
    _rhs_guard(e,rhs,q.values)
    r.valid=false;q.evidence_generation=UInt64(0);e.proposal.valid=false
    if slot==1;ks.price_ticket=UInt64(0);e.supports[3].evidence_generation=UInt64(0);end
    if ks.next_ticket==typemax(UInt64);_drop_all_proofs!(e);ks.next_ticket=UInt64(0);end
    ks.next_ticket+=UInt64(1);r.ticket=ks.next_ticket;r.rhs_used=0;r.unit_row=0
    ks.latest=Base.setindex(ks.latest,r.ticket,slot)
    for i in eachindex(r.rhs)
        x=rhs[i];ks.counts.rhs_capture_entries+=1
        isfinite(x)||return _failed(slot)
        r.rhs[i]=x
        if !iszero(x);r.rhs_used+=1;r.rhs_ids[r.rhs_used]=i;end
    end
    if r.rhs_used==1
        i=r.rhs_ids[1];r.unit_row=r.rhs[i]==1. ? i : 0
    end
    e.recovery.failed_slot=slot
    try
        if slot==1;e.counters.btran+=1;J.transpose_solve!(q.values,e.ws.factorization,r.rhs)
        elseif slot==2;e.counters.ftran+=1;J.forward_solve!(q.values,e.ws.factorization,r.rhs)
        else;e.counters.bfrt_ftran+=1;J.forward_solve!(q.values,e.ws.factorization,r.rhs)
        end
    catch err
        ks.factor_valid=false;_drop_all_proofs!(e);invalidate!(e,:factor_exception)
        J._is_numerical_exception(err)&&return StepOutcome(FactorInvalid)
        rethrow()
    end
    try
        _capture_output!(q,q.values,ks.counts)
    catch err
        err isa ArgumentError||rethrow()
        return _failed(slot)
    end
    e.counters.scanned_entries+=length(q.values) # complete dense-output capture
    e.counters.dense_routes+=1
    r.output=q.values;r.owner=e.owner;r.generation=e.generation;r.factor_id=objectid(e.ws.factorization)
    r.valid=true;q.evidence_generation=e.generation
    e.clock() ? StepOutcome(Stopped) : StepOutcome(Ready)
end
function price_row!(e::EngineState)::StepOutcome
    e.recovery.failed_slot=0
    _receipt_valid(e,1)||return StepOutcome(RowUnreliable)
    e.clock()&&return StepOutcome(Stopped)
    ks=e.kernels;rho=e.supports[1];out=e.supports[3];A=e.ws.problem.A;m,n=size(A)
    ks.price_ticket=UInt64(0);clear_scratch!(out)
    q=0
    for k in 1:rho.used
        row=rho.ids[k];q+=e.rows.rowptr[row+1]-e.rows.rowptr[row]
    end
    sparse=e.rows.ordered_csc && q<=J.SparseArrays.nnz(A)÷e.policy.sparse_divisor
    ks.last_pricing_mode=sparse ? :sparse : :dense
    try
        if sparse
            ks.counts.sparse_prices+=1;previous=0
            for k in 1:rho.used
                row=rho.ids[k];row>previous||throw(ArgumentError("nonascending rho support"));previous=row
                value=rho.values[row]
                for p in e.rows.rowptr[row]:(e.rows.rowptr[row+1]-1)
                    col=e.rows.columns[p];term=A.nzval[e.rows.positions[p]]*value
                    ks.counts.pricing_entries+=1
                    isfinite(term)||throw(ArgumentError("pricing product overflow"))
                    add_scratch!(out,col,term)
                end
                set_scratch!(out,n+row,-value)
            end
        else
            ks.counts.dense_prices+=1
            for col in 1:n
                value=0.
                for p in J.SparseArrays.nzrange(A,col)
                    term=A.nzval[p]*rho.values[A.rowval[p]];ks.counts.pricing_entries+=1
                    isfinite(term)||throw(ArgumentError("pricing product overflow"))
                    value+=term;isfinite(value)||throw(ArgumentError("pricing sum overflow"))
                end
                set_scratch!(out,col,value)
            end
            for row in 1:m;set_scratch!(out,n+row,-rho.values[row]);end
        end
        compact_scratch!(out)
    catch err
        clear_scratch!(out)
        err isa ArgumentError||rethrow()
        return StepOutcome(RowUnreliable)
    end
    out.evidence_generation=e.generation;ks.price_ticket=ks.solves[1].ticket
    e.clock() ? StepOutcome(Stopped) : StepOutcome(Ready)
end
function check_row!(e::EngineState,leaving::Int)::StepOutcome
    _receipt_valid(e,1)||return StepOutcome(RowUnreliable)
    r=e.kernels.solves[1]
    r.unit_row==leaving&&1<=leaving<=length(r.rhs)||return StepOutcome(RowUnreliable)
    e.clock()&&return StepOutcome(Stopped)
    e.recovery.failed_slot=1
    e.kernels.counts.row_checks+=1
    # Deliberately retain the independent original complete row criterion.
    ratio=J._dual_row_residual_ratio(e.ws,r.output,leaving)
    e.clock()&&return StepOutcome(Stopped)
    isfinite(ratio)&&ratio<=1. ? StepOutcome(Ready) : StepOutcome(RowUnreliable)
end
function _touch_residual!(e,row)
    q=e.supports[5]
    if q.stamps[row]!=q.epoch
        q.used+=1;q.ids[q.used]=row;q.stamps[row]=q.epoch
        q.values[row]=0.;e.residual_scale[row]=0.
    end
    nothing
end
function _direction_residual_ok!(e,q,rhs,pivot,rhs_ids,rhs_used)
    isfinite(pivot)||return false
    residual=e.supports[5]
    length(q.values)==length(rhs)==length(residual.values)||throw(DimensionMismatch("residual dimensions"))
    (Base.mightalias(q.values,residual.values)||Base.mightalias(rhs,residual.values)||Base.mightalias(q.values,e.residual_scale)||Base.mightalias(rhs,e.residual_scale))&&throw(ArgumentError("residual aliases input"))
    clear_scratch!(residual)
    for k in 1:rhs_used
        row=rhs_ids[k];_touch_residual!(e,row)
        e.kernels.counts.residual_terms+=1
        x=rhs[row];isfinite(x)||return false
        residual.values[row]=-x;e.residual_scale[row]=abs(x)
    end
    A=e.ws.problem.A;m,n=size(A);previous=0
    for k in 1:q.used
        col=q.ids[k];previous<col<=m||throw(ArgumentError("direction support order/dimension"));previous=col
        value=q.values[col];isfinite(value)||return false
        index=e.ws.basis.basic_indices[col]
        if index<=n
            for p in J.SparseArrays.nzrange(A,index)
                row=A.rowval[p];_touch_residual!(e,row)
                term=A.nzval[p]*value
                residual.values[row]+=term;e.residual_scale[row]+=abs(term)
                e.kernels.counts.residual_terms+=1
            end
        else
            row=index-n;_touch_residual!(e,row)
            residual.values[row]-=value;e.residual_scale[row]+=abs(value)
            e.kernels.counts.residual_terms+=1
        end
    end
    roundoff=256eps(Float64);pivot_tolerance=sqrt(eps(Float64))*abs(pivot)
    for k in 1:residual.used
        row=residual.ids[k];r=residual.values[row];scale=e.residual_scale[row]
        e.kernels.counts.residual_rows+=1
        isfinite(r)&&isfinite(scale)||return false
        tolerance=max(e.ws.options.zero_tolerance,pivot_tolerance,roundoff*(scale+1.))
        isfinite(tolerance)&&abs(r)<=tolerance||return false
    end
    true
end
"""Cold component entry with an unindexed RHS; accounts its complete scan."""
function direction_residual_ok!(e::EngineState,q::StampedScratch,rhs::Vector{Float64},pivot::Float64)::Bool
    m=length(e.ws.basis.basic_indices)
    length(q.values)==length(rhs)==m||throw(DimensionMismatch("direction residual"))
    # Unindexed component input visits all RHS rows explicitly. The ordinary
    # receipt path below uses the producer's retained nonzero RHS index.
    _direction_residual_ok!(e,q,rhs,pivot,eachindex(rhs),length(rhs))
end
function check_direction!(e::EngineState,rhs::AbstractVector{Float64},pivot::Float64;kind::Symbol=:ftran)::StepOutcome
    slot=_slot(kind);slot==1&&throw(ArgumentError("direction check requires FTRAN"))
    _receipt_valid(e,slot)||return StepOutcome(DirectionUnreliable)
    e.clock()&&return StepOutcome(Stopped)
    r=e.kernels.solves[slot];length(rhs)==length(r.rhs)||throw(DimensionMismatch("direction RHS"))
    if rhs!==r.rhs
        for i in eachindex(r.rhs)
            e.kernels.counts.rhs_compare_entries+=1
            if !isequal(rhs[i],r.rhs[i]);r.valid=false;return StepOutcome(DirectionUnreliable);end
        end
    end
    e.recovery.failed_slot=slot
    e.kernels.counts.direction_checks+=1
    valid=_direction_residual_ok!(e,e.supports[_output_slot(slot)],r.rhs,pivot,r.rhs_ids,r.rhs_used)
    e.clock()&&return StepOutcome(Stopped)
    valid ? StepOutcome(Ready) : StepOutcome(DirectionUnreliable)
end
