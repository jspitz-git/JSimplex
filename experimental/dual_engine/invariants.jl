@inline function _finite_variable(ws,i)
    isfinite(ws.primal[i]) && isfinite(ws.reduced_costs[i]) && isfinite(ws.costs[i]) &&
        isfinite(ws.pricing_weights[i]) && ws.pricing_weights[i]>0.
end
function _validate_numeric(ws)
    m,n=size(ws.problem.A);N=m+n
    length(ws.costs)==N && all(v->length(v)==N,(ws.primal,ws.reduced_costs,ws.pricing_weights,ws.lower,ws.upper)) || throw(ArgumentError("numeric workspace dimensions"))
    for i in eachindex(ws.costs)
        _finite_variable(ws,i)||throw(ArgumentError("nonfinite state or invalid weight at $i"))
    end
    nothing
end
@inline function _primal_bad(ws,i)
    x=ws.primal[i];tol=ws.options.primal_tolerance;lo=ws.lower[i];hi=ws.upper[i]
    (isfinite(lo)&&lo.value-x>tol)||(isfinite(hi)&&x-hi.value>tol)
end
@inline function _dual_bad(ws,i)
    state=ws.basis.states[i];state==J.BASIC&&return false
    lo=ws.lower[i];hi=ws.upper[i]
    isfinite(lo)&&isfinite(hi)&&lo.value==hi.value&&return false
    p=ws.reduced_costs[i];tol=ws.options.dual_tolerance
    state==J.AT_LOWER ? p < -tol : state==J.AT_UPPER ? p>tol : abs(p)>tol
end
function _advance_generation!(e)
    (e.recovery.finished||e.recovery.fatal)&&throw(ArgumentError("consumed or invalid engine"))
    e.proposal.valid=false;e.proposal.rejected_generation=UInt64(0);e.recovery.rejection_generation=UInt64(0)
    for q in e.supports;q.evidence_generation=UInt64(0);end
    if e.generation==typemax(UInt64)
        e.generation=UInt64(1);e.counters.generation_wraps+=1
        for q in e.supports
            clear_scratch!(q);fill!(q.stamps,UInt32(0));q.epoch=UInt32(1)
            e.counters.support_reset_entries+=length(q.stamps)
        end
        e.invariants.valid=false;e.invariants.reason=:generation_wrap
    else
        e.generation+=UInt64(1)
    end
    nothing
end
function invalidate!(e::EngineState,reason::Symbol)
    _advance_generation!(e);e.invariants.valid=false;e.invariants.reason=reason
    nothing
end
# Validate into engine-owned inverse storage. The production validator mutates
# its workspace basic_mask, so it must not be called on an imported source.
function _basis_inverse!(inverse::Vector{Int},ws)
    m,n=size(ws.problem.A);N=m+n
    length(inverse)==N && length(ws.basis.states)==N && length(ws.basis.basic_indices)==m || throw(ArgumentError("basis dimensions"))
    fill!(inverse,0)
    for (r,i) in enumerate(ws.basis.basic_indices)
        1<=i<=N && inverse[i]==0 || throw(ArgumentError("invalid or duplicate basic index"))
        inverse[i]=r
    end
    for i in 1:N
        (ws.basis.states[i]==J.BASIC)==(inverse[i]>0)||throw(ArgumentError("basis indices and states disagree"))
    end
    nothing
end
function _install_membership!(e;validated_basis::Bool=false)
    ws=e.ws;v=e.invariants
    if !validated_basis
        _basis_inverse!(v.basic_row,ws)
        fill!(v.primal_bad.position,0);v.primal_bad.used=0
        fill!(v.dual_bad.position,0);v.dual_bad.used=0
    end
    for i in eachindex(ws.costs)
        r=v.basic_row[i]
        r>0&&set_present!(v.primal_bad,r,_primal_bad(ws,i))
        set_present!(v.dual_bad,i,_dual_bad(ws,i))
    end
    v.valid=true;v.reason=:none;e.counters.invariant_rebuilds+=1
    nothing
end
function rebuild_invariants!(e::EngineState)
    invalidate!(e,:rebuilding)
    _validate_numeric(e.ws);e.counters.entry_validated_values+=4length(e.ws.costs)
    _install_membership!(e)
end
function classify_variable!(e::EngineState,i::Int)
    ws=e.ws;v=e.invariants;checkbounds(ws.costs,i)
    _advance_generation!(e)
    if !_finite_variable(ws,i) || ((v.basic_row[i]>0)!=(ws.basis.states[i]==J.BASIC))
        v.valid=false;v.reason=:invalid_variable;return nothing
    end
    _classify_owned!(e,i)
end
@inline function _classify_owned!(e,i)
    ws=e.ws;v=e.invariants;row=v.basic_row[i]
    row>0&&set_present!(v.primal_bad,row,_primal_bad(ws,i))
    set_present!(v.dual_bad,i,_dual_bad(ws,i));e.counters.classified_variables+=1
    nothing
end
function write_value!(e::EngineState,kind::Symbol,i::Int,x::Float64)
    (e.recovery.finished||e.recovery.fatal)&&throw(ArgumentError("consumed or invalid engine"))
    e.invariants.valid||throw(ArgumentError("invalid summaries require rebuild"))
    field=kind==:primal ? :primal : kind==:price ? :reduced_costs : kind==:cost ? :costs : kind==:weight ? :pricing_weights : throw(ArgumentError("unknown numeric field"))
    values=getfield(e.ws,field);checkbounds(values,i)
    isfinite(x)&&(kind!=:weight||x>0.)||throw(ArgumentError("invalid numeric write"))
    values[i]=x;_advance_generation!(e);_classify_owned!(e,i);e.counters.touched_entries+=1
    nothing
end
function _set_coherent(s)
    0<=s.used<=length(s.ids)==length(s.position)||return false
    for (i,p) in enumerate(s.position)
        0<=p<=s.used||return false
        p>0&&s.ids[p]!=i&&return false
    end
    for k in 1:s.used
        i=s.ids[k];1<=i<=length(s.position)&&s.position[i]==k||return false
    end
    true
end
"""Allocating cold oracle; never called by ordinary mutators."""
function assert_invariants(e::EngineState)
    v=e.invariants;ws=e.ws
    v.valid&&_set_coherent(v.primal_bad)&&_set_coherent(v.dual_bad)||return false
    all(i->_finite_variable(ws,i),eachindex(ws.costs))||return false
    inverse=zeros(Int,length(ws.costs));expected_p=Int[];expected_d=Int[]
    for (r,i) in enumerate(ws.basis.basic_indices)
        1<=i<=length(inverse)&&inverse[i]==0&&ws.basis.states[i]==J.BASIC||return false
        inverse[i]=r
        x=ws.primal[i];lo=ws.lower[i];hi=ws.upper[i];tol=ws.options.primal_tolerance
        ((lo.bounded&&lo.value-x>tol)||(hi.bounded&&x-hi.value>tol))&&push!(expected_p,r)
    end
    inverse==v.basic_row||return false
    for i in eachindex(ws.costs)
        state=ws.basis.states[i];(state==J.BASIC)==(inverse[i]>0)||return false
        state==J.BASIC&&continue
        lo=ws.lower[i];hi=ws.upper[i]
        lo.bounded&&hi.bounded&&lo.value==hi.value&&continue
        p=ws.reduced_costs[i];t=ws.options.dual_tolerance
        bad=state==J.AT_LOWER ? p < -t : state==J.AT_UPPER ? p>t : !(abs(p)<=t)
        bad&&push!(expected_d,i)
    end
    sort(collect(@view v.primal_bad.ids[1:v.primal_bad.used]))==expected_p &&
        sort(collect(@view v.dual_bad.ids[1:v.dual_bad.used]))==expected_d
end
