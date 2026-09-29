include("inspect-and-continue.jl")

function reconstruct_handoff(auxiliary_path,original_path,output)
    ispath(output) && error("Choose a fresh output path")
    a=deserialize(auxiliary_path)
    b=deserialize(original_path)
    ws=J._initialize_workspace_state(a.problem,a.options)
    ws.basis=deepcopy(a.basis)
    ws.costs.=a.costs
    ws.iterations=a.iteration
    ws.dual_pricing_fallback=a.dual_pricing_fallback
    ws.dual_devex_fallback=a.dual_devex_fallback
    ws.pricing_weights.=a.pricing_weights
    ws.devex_reference.=a.devex_reference
    for i in eachindex(ws.basis.states)
        ws.basis.states[i]==J.BASIC && continue
        if !isfinite(ws.lower[i]) && !isfinite(ws.upper[i])
            ws.basis.states[i]=J.FREE_NONBASIC
        elseif !isfinite(ws.lower[i])
            ws.basis.states[i]=J.AT_UPPER
        elseif !isfinite(ws.upper[i])
            ws.basis.states[i]=J.AT_LOWER
        end
    end
    mapped_states=copy(ws.basis.states)
    J.recompute!(ws;refactorize=true)
    before=point_metrics(ws,a)
    println("BEFORE_FLIPS ",before); flush(stdout)
    J._flip_bounds!(ws)
    after=point_metrics(ws,a)
    println("AFTER_FLIPS ",after); flush(stdout)
    report=Dict{String,Any}("auxiliary_snapshot_sha256"=>bytes2hex(open(sha256,auxiliary_path)),
        "original_snapshot_sha256"=>bytes2hex(open(sha256,original_path)),
        "before_flips"=>before,"after_flips"=>after,
        "bounds_changed"=>count(i->a.lower[i]!=ws.lower[i] || a.upper[i]!=ws.upper[i],eachindex(ws.lower)),
        "states_remapped"=>count(i->a.basis.states[i]!=mapped_states[i],eachindex(mapped_states)),
        "bound_flips"=>count(i->mapped_states[i]!=ws.basis.states[i],eachindex(mapped_states)),
        "basis_matches_live_handoff"=>ws.basis.basic_indices==b.basis.basic_indices,
        "states_match_live_handoff"=>ws.basis.states==b.basis.states,
        "primal_difference_from_live"=>norm(ws.primal-b.primal,Inf),
        "price_difference_from_live"=>norm(ws.reduced_costs-b.prices,Inf))
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("FINAL ",report)
end
length(ARGS)==3 || error("Expected: auxiliary_snapshot original_snapshot output.toml")
with_logger(NullLogger()) do
    reconstruct_handoff(ARGS...)
end
