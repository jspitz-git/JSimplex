using JSimplex, LinearAlgebra, Serialization, TOML, SHA, Logging
const J = JSimplex

function point_metrics(ws, saved)
    n=size(ws.problem.A,2)
    ps,pc=J.primal_infeasibility_summary(ws)
    ds,dc=J.dual_infeasibility_summary(ws)
    scratch=J._pivot_quality_buffers(ws).column
    quality=J._compensated_solve_quality!(scratch,ws.problem.A,
        @view(ws.primal[1:n]),@view(ws.primal[n+1:end]),ws.progress.numerical_policy,false)
    primal_max=maximum(eachindex(ws.primal)) do i
        max(J._lower_violation(ws.lower[i],ws.primal[i]),
            J._upper_violation(ws.upper[i],ws.primal[i]))
    end
    Dict{String,Any}("iteration"=>ws.iterations,
        "original_bounds"=>J._original_bounds_active(ws),
        "original_costs"=>J._original_costs_active(ws),
        "working_objective"=>dot(ws.costs,ws.primal),
        "logged_objective"=>dot(saved.original_objective,
            J.unscale_primal(saved.scaling,@view(ws.primal[1:n])))+saved.original_objective_constant,
        "objective_constant"=>saved.original_objective_constant,
        "primal_sum"=>ps,"primal_count"=>pc,"primal_max"=>primal_max,
        "dual_sum"=>ds,"dual_count"=>dc,
        "row_consistent"=>J._legacy_primal_row_consistent(ws,ws.options.primal_tolerance),
        "native_residual_available"=>!isnothing(quality),
        "absolute_equation_residual"=>isnothing(quality) ? NaN : quality.absolute_error,
        "relative_equation_residual"=>isnothing(quality) ? NaN : quality.relative_error,
        "pricing_effective"=>string(J._effective_pricing(ws,:dual)),
        "dantzig_fallback"=>ws.dual_pricing_fallback,
        "devex_fallback"=>ws.dual_devex_fallback)
end

function inspect_continue(path,mode,seconds,steps,output)
    mode in ("inspect","baseline","reset_devex") || error("Unknown continuation mode")
    ispath(output) && error("Choose a fresh output path")
    saved=deserialize(path)
    diagnostics=J.SimplexDiagnostics()
    ws=J._initialize_workspace_state(saved.problem,saved.options;
        progress=J.SimplexProgressContext(saved.problem;diagnostics))
    ws.basis=deepcopy(saved.basis)
    ws.factorization=saved.factorization
    ws.costs.=saved.costs; ws.lower.=saved.lower; ws.upper.=saved.upper
    ws.primal.=saved.primal; ws.reduced_costs.=saved.prices
    ws.pricing_weights.=saved.pricing_weights
    ws.devex_reference.=saved.devex_reference
    ws.iterations=saved.iteration
    ws.perturbed=saved.perturbed
    ws.zero_dual_step_streak=saved.zero_dual_step_streak
    ws.dual_pricing_fallback=saved.dual_pricing_fallback
    ws.dual_devex_fallback=saved.dual_devex_fallback
    ws.dual_refactorization_interval=saved.dual_refactorization_interval
    J._validate_basis(ws)
    before=point_metrics(ws,saved)
    println("SAVED ",before); flush(stdout)
    # Both continuations share a fresh native factor and recomputed values.
    # This is a reference continuation, not a replay of unrecorded scratch state.
    started=time_ns(); stop=()->(time_ns()-started)/1e9>=seconds
    prices=copy(ws.reduced_costs); primal=copy(ws.primal)
    J.recompute!(ws;refactorize=true,caller_guard=stop)
    after=point_metrics(ws,saved)
    after["price_change_inf"]=norm(ws.reduced_costs-prices,Inf)
    after["primal_change_inf"]=norm(ws.primal-primal,Inf)
    println("REFRESHED ",after); flush(stdout)
    terminal=nothing
    if mode != "inspect"
        J._original_bounds_active(ws) || error("Continuation requires original working bounds")
        J.dual_infeasibility(ws)<=ws.options.dual_tolerance || error("Refreshed point is not dual feasible")
        if mode == "reset_devex"
            # Diagnostic intervention: change only the post-handoff pricing
            # framework. Bounds, costs, arithmetic and tolerances are unchanged.
            ws.dual_pricing_fallback=false
            ws.dual_devex_fallback=true
            J.reset_devex!(ws)
        end
        initial_iteration=ws.iterations
        started=time_ns()
        stop=()->(time_ns()-started)/1e9>=seconds || ws.iterations>=initial_iteration+steps
        terminal=J._dual_optimize!(ws,stop)
    end
    final=point_metrics(ws,saved)
    report=Dict{String,Any}("mode"=>mode,"snapshot_sha256"=>bytes2hex(open(sha256,path)),
        "source_revision"=>strip(read(`git rev-parse HEAD`,String)),
        "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
        "seconds"=>(time_ns()-started)/1e9,"steps"=>ws.iterations-saved.iteration,
        "terminal"=>isnothing(terminal) ? "INSPECTED" : string(terminal.status),
        "requested_steps"=>steps,"diagnostic_step_limit_reached"=>mode!="inspect" && ws.iterations>=saved.iteration+steps,
        "saved"=>before,"refreshed"=>after,"final"=>final,
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("FINAL ",report); flush(stdout)
end
if abspath(PROGRAM_FILE)==(@__FILE__)
    length(ARGS)==5 || error("Expected: snapshot inspect|baseline|reset_devex seconds steps output.toml")
    with_logger(NullLogger()) do
        inspect_continue(ARGS[1],ARGS[2],parse(Float64,ARGS[3]),parse(Int,ARGS[4]),ARGS[5])
    end
end
