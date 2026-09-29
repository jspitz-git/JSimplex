include("inspect-and-continue.jl")

function trace_tail(path,steps,seconds,output)
    ispath(output) && error("Choose a fresh output path")
    saved=deserialize(path)
    rows=Dict{String,Any}[]
    leaving=Ref(0)
    observer=function(event,ws)
        if event==:pivot_proposed
            leaving[]=ws.basis.basic_indices[ws.scratch.selected_row]
        elseif event==:pivot_completed
            row=ws.scratch.selected_row
            direction=ws.scratch.row_solution
            pivot=direction[row]
            push!(rows,Dict{String,Any}("iteration"=>ws.iterations,
                "entering"=>ws.scratch.selected_entering,"leaving"=>leaving[],
                "primal_step"=>ws.scratch.last_primal_step,
                "dual_step"=>ws.scratch.last_dual_step,
                "pivot"=>pivot,"direction_norm"=>norm(direction,Inf),
                "working_objective_increment_from_step"=>ws.scratch.last_primal_step*pivot*ws.scratch.last_dual_step,
                "pricing"=>string(J._effective_pricing(ws,:dual))))
        end
    end
    diagnostics=J.SimplexDiagnostics(;observer)
    ws=J._initialize_workspace_state(saved.problem,saved.options;
        progress=J.SimplexProgressContext(saved.problem;diagnostics))
    ws.basis=deepcopy(saved.basis); ws.factorization=saved.factorization
    ws.costs.=saved.costs; ws.lower.=saved.lower; ws.upper.=saved.upper
    ws.primal.=saved.primal; ws.reduced_costs.=saved.prices
    ws.pricing_weights.=saved.pricing_weights; ws.devex_reference.=saved.devex_reference
    ws.iterations=saved.iteration; ws.perturbed=saved.perturbed
    ws.zero_dual_step_streak=saved.zero_dual_step_streak
    ws.dual_pricing_fallback=saved.dual_pricing_fallback
    ws.dual_devex_fallback=saved.dual_devex_fallback
    ws.dual_refactorization_interval=saved.dual_refactorization_interval
    J._validate_basis(ws)
    J.recompute!(ws;refactorize=true)
    before=point_metrics(ws,saved)
    started=time_ns()
    stop=()->(time_ns()-started)/1e9>=seconds || ws.iterations>=saved.iteration+steps
    terminal=J._dual_optimize!(ws,stop)
    after=point_metrics(ws,saved)
    nonzero=sort!([abs(r["dual_step"]) for r in rows if !iszero(r["dual_step"])])
    report=Dict{String,Any}("snapshot_sha256"=>bytes2hex(open(sha256,path)),
        "source_revision"=>strip(read(`git rev-parse HEAD`,String)),
        "script_sha256"=>bytes2hex(open(sha256,@__FILE__)),
        "steps"=>length(rows),"terminal"=>string(terminal.status),
        "zero_dual_steps"=>count(r->iszero(r["dual_step"]),rows),
        "zero_primal_steps"=>count(r->iszero(r["primal_step"]),rows),
        "dual_steps_within_tolerance"=>count(r->abs(r["dual_step"])<=ws.options.dual_tolerance,rows),
        "minimum_nonzero_dual_step"=>isempty(nonzero) ? NaN : first(nonzero),
        "median_nonzero_dual_step"=>isempty(nonzero) ? NaN : nonzero[cld(length(nonzero),2)],
        "maximum_nonzero_dual_step"=>isempty(nonzero) ? NaN : last(nonzero),
        "minimum_relative_pivot"=>minimum(r->abs(r["pivot"])/r["direction_norm"],rows;init=Inf),
        "before"=>before,"after"=>after,"rows"=>rows,
        "counts"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0))
    open(output,"w") do io
        TOML.print(io,report)
    end
    println("FINAL ",Dict(k=>v for (k,v) in report if k!="rows")); flush(stdout)
end
length(ARGS)==4 || error("Expected: snapshot steps seconds output.toml")
with_logger(NullLogger()) do
    trace_tail(ARGS[1],parse(Int,ARGS[2]),parse(Float64,ARGS[3]),ARGS[4])
end
