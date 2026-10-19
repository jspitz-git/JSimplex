# P011 repair helpers: cold test code; no calls at include time.
# Explicit argument avoids the macro closure over the reassigned testset local f.
p011_eligibility(f::Carrier)::K.BGPanelDecision = K._bgb_eligibility(f,1)
function p011_consume!(sink::Base.RefValue{K.BGPanelDecision}, f::Carrier)
    sink[] = p011_eligibility(f)
    nothing
end
function p011_expected(d::K.BGPanelDecision)
    d.start == 1 && d.count == 0 && !d.accepted && d.reason === :dimensions &&
        d.finite && d.counters == (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
end
# Every Carrier field's value, packed contents, row order, and cache fields.
# Selected mutable owners are retained only for this cold n32 assertion group.
function p011_state(f::Carrier)
    cache = f.row_cache
    cache.prepared === nothing && f.sparse === nothing || error("Unexpected P011 cache")
    order = f.upper[1].indices.order
    values = (snapshot(f), copy(order.order), copy(order.positions),
        copy(f.column_order), copy(f.positions), f.row_columns_ready,
        Tuple(deepcopy(getfield(cache,k)) for k in fieldnames(typeof(cache))))
    owners = Any[f, f.upper, f.column_order, f.positions, f.row_columns, cache,
        order, order.order, order.positions]
    append!(owners,f.row_columns)
    for col in f.upper
        append!(owners,(col.values,col.indices.ids,col.indices.order))
    end
    for k in fieldnames(typeof(cache))
        x = getfield(cache,k)
        x isa AbstractArray && push!(owners,x)
    end
    (values=values,owners=owners)
end
function p011_probe(f::Carrier)
    before = p011_state(f)
    sentinel = K.BGPanelDecision(0,0,false,:uninitialized,false,
        (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
    sink = Ref(sentinel)
    # Five warm calls, including both allocation meters and observable-result arms.
    warm = p011_eligibility(f)
    Base.allocated(p011_eligibility,f)
    Base.allocations(p011_eligibility,f)
    Base.allocated(p011_consume!,sink,f)
    Base.allocations(p011_consume!,sink,f)
    # Four measured calls. Snapshot/Ref/record/Test costs are outside these meters.
    bytes = Base.allocated(p011_eligibility,f)
    events = Base.allocations(p011_eligibility,f)
    sink[] = sentinel
    consumed_bytes = Base.allocated(p011_consume!,sink,f)
    bytes_decision = sink[]
    sink[] = sentinel
    consumed_events = Base.allocations(p011_consume!,sink,f)
    events_decision = sink[]
    after = p011_state(f)
    (bytes=bytes,events=events,consumed_bytes=consumed_bytes,consumed_events=consumed_events,
        warm=warm,bytes_decision=bytes_decision,events_decision=events_decision,
        values_unchanged=isequal(before.values,after.values),
        owners_unchanged=length(before.owners)==length(after.owners) &&
            all(a === b for (a,b) in zip(before.owners,after.owners)))
end

