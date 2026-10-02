# Replay only pure ratio/snap kernels; no captured basis is factorized or solved.
using JSimplex, Serialization, SparseArrays, TOML, SHA
function ratio_workspace(s)
    p = LinearProblem(spzeros(0,0),Float64[])
    policy = hasproperty(s,:policy) ? s.policy :
        JSimplex.NumericalPolicy(Float64;phase_one=true,adaptive_stalling=true,
            adaptive_pricing=true,adaptive_primal_perturbation=true,
            adaptive_dual_perturbation=true,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,s.options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.problem = s.problem
    ws.costs,ws.lower,ws.upper = s.costs,s.lower,s.upper
    ws.basis,ws.primal,ws.reduced_costs = s.basis,s.primal,s.reduced_costs
    ws.iterations = s.iteration
    if hasproperty(s,:rejected_rows)
        append!(ws.scratch.rejected_rows,s.rejected_rows)
    end
    if !isnothing(s.bounds)
        journal = JSimplex.PerturbationJournal(ws)
        journal.bounds = s.bounds
        ws.scratch.perturbations = journal
        ws.perturbed = true
    end
    # The empty factor belongs to the initializer. Call only the kernels below,
    # which read mathematical bounds, basis indices, point and direction.
    return ws
end
function analyze_ratio(path)
    s = deserialize(path)
    ws = ratio_workspace(s)
    step,row,state = JSimplex._primal_ratio(ws,s.entering,s.direction,s.column)
    early = "none"
    early_row = 0
    for (i,j) in enumerate(ws.basis.basic_indices)
        movement = -s.direction*s.column[i]
        iszero(movement) && continue
        b = movement > 0 ? ws.upper[j] : ws.lower[j]
        isfinite(b) || continue
        raw = (JSimplex.bound_value(b)-ws.primal[j])/movement
        violation = movement > 0 ? JSimplex._upper_violation(b,ws.primal[j]) :
            JSimplex._lower_violation(b,ws.primal[j])
        if !isfinite(raw) || (raw < 0 && violation > ws.options.primal_tolerance)
            early = !isfinite(raw) ? "nonfinite_ratio" : "bound_violation"
            early_row = i
            break
        end
    end
    return Dict("snapshot"=>path,"snapshot_sha256"=>bytes2hex(open(sha256,path)),
        "recorded_policy"=>hasproperty(s,:policy),"recorded_rejected_rows"=>hasproperty(s,:rejected_rows),
        "iteration"=>s.iteration,"entering"=>s.entering,
        "captured_row"=>s.selected,"replayed_row"=>row,
        "captured_step"=>isnothing(s.step) ? "none" : s.step,
        "replayed_step"=>isnothing(step) ? "none" : step,
        "captured_pivot"=>s.selected>0 ? s.column[s.selected] : 0.0,
        "replayed_pivot"=>row>0 ? s.column[row] : 0.0,
        "first_pass_exit"=>early,"first_pass_exit_row"=>early_row,
        "same_ratio"=>isequal((step,row),(s.step,s.selected)))
end
length(ARGS)>=2 || error("Expected output TOML and snapshot paths")
root=dirname(pathof(JSimplex))
report=Dict("source_sha256"=>Dict(name=>bytes2hex(open(sha256,joinpath(root,name)))
        for name in ("simplex.jl","primal_simplex.jl")),
    "scope"=>"Pure native ratio replay; factorization and pivot application are not exercised",
    "snapshots"=>[analyze_ratio(path) for path in ARGS[2:end]])
open(ARGS[1],"w") do io
    TOML.print(io,report)
end
TOML.print(stdout,report)
