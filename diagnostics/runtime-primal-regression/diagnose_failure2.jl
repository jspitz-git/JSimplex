# Replay production projection, then a source-derived traced copy, at 8 BLAS threads.
# No installed package files, arithmetic types, tolerances, or decisions change.
module Failure2Diagnostics
using JSimplex, LinearAlgebra, Serialization, SHA, TOML
const JS = JSimplex
const events = Dict{String,Any}[]
const output_prefix = Ref("")

function quality(ws, x, rhs; transposed=false)
    B = JS.basis_matrix(ws)
    scratch = JS.SolveQualityScratch(eltype(x), length(rhs))
    q = JS._compensated_solve_quality!(scratch, B, x, rhs,
        ws.progress.numerical_policy, transposed)
    isnothing(q) && return Dict("available"=>false)
    return Dict("available"=>true, "reliable"=>q.reliable,
        "absolute_error"=>q.absolute_error, "relative_error"=>q.relative_error)
end

function violations(ws)
    n = size(ws.problem.A, 2)
    result = Dict{String,Any}[]
    for (slot, j) in enumerate(ws.basis.basic_indices)
        amount = max(JS._lower_violation(ws.lower[j], ws.primal[j]),
                     JS._upper_violation(ws.upper[j], ws.primal[j]))
        amount > ws.options.primal_tolerance || continue
        names, k = j <= n ? (ws.problem.column_names, j) : (ws.problem.row_names, j-n)
        push!(result, Dict("index"=>j, "basis_slot"=>slot,
            "kind"=>j <= n ? "column" : "row_activity",
            "name"=>isempty(names) ? string(k) : names[k],
            "value"=>ws.primal[j], "violation"=>amount,
            "lower"=>string(ws.lower[j]), "upper"=>string(ws.upper[j])))
    end
    return result
end

function snapshot!(ws, stage; details...)
    pinf, count = JS.primal_infeasibility_summary(ws)
    report = Dict{String,Any}("stage"=>stage, "iterations"=>ws.iterations,
        "infeasibility"=>pinf, "violation_count"=>count,
        "violations"=>violations(ws), "finite"=>JS._finite_workspace(ws),
        "primal_quality"=>quality(ws, ws.primal[ws.basis.basic_indices], JS._basis_primal_rhs(ws)),
        "transpose_quality"=>quality(ws, ws.scratch.rho, ws.costs[ws.basis.basic_indices]; transposed=true))
    for (k,v) in details
        report[string(k)] = v
    end
    push!(events, report)
    println(stage, ": pinf=", pinf, " (", count, "); ", details)
    flush(stdout)
    if stage == "before_reconstruction"
        f = ws.factorization
        # HH's extracted factors are portable; disposable refactor scratch may
        # contain process-local UMFPACK pointers and is not needed for replay.
        portable = typeof(f)((name == :refactor_workspace ? nothing : getfield(f,name)
            for name in fieldnames(typeof(f)))...)
        serialize(output_prefix[] * ".before-reconstruction.bin",
            (;problem=ws.problem, options=ws.options, policy=ws.progress.numerical_policy,
              basis=ws.basis, primal=ws.primal, costs=ws.costs, lower=ws.lower,
              upper=ws.upper, rho=ws.scratch.rho, reduced_costs=ws.reduced_costs,
              factorization=portable, iterations=ws.iterations,
              refactorizations=ws.refactorizations, perturbed=ws.perturbed))
    end
    return nothing
end

function reject!(ws, location)
    snapshot!(ws, "rejected"; location)
    return nothing
end

function pivot!(ws, stop)
    snapshot!(ws, "before_feasibility_pivot")
    result = JS._try_postsolve_feasibility_pivot!(ws, stop)
    snapshot!(ws, "after_feasibility_pivot"; accepted=result)
    return result
end

function traced_projection(source)
    lines = split(source, '\n')
    start = findfirst(l -> startswith(l, "function _project_postsolve_basis!"), lines)
    lastline = findnext(l -> startswith(l, "function _cleanup_primal_feasible!"), lines, start+1)-1
    selected = copy(lines[start:lastline])
    selected[1] = replace(selected[1], "_project_postsolve_basis!"=>"_failure2_traced_projection!")
    for i in eachindex(selected)
        selected[i] = replace(selected[i], "return nothing"=>
            "return Main.Failure2Diagnostics.reject!(workspace, \"solver.jl:$(start+i-1)\")")
    end
    body = join(selected, '\n')
    marker = "        reconstructed = _try_native_cleanup_recompute!(workspace, stop_requested)"
    count(marker, body) == 1 || error("Unexpected reconstruction source; refusing instrumentation")
    body = replace(body, marker=>
        "        Main.Failure2Diagnostics.snapshot!(workspace, \"before_reconstruction\"; exchanges=length(displaced), native_hint, target_feasible_after_box_projection=target_feasible)\n" *
        marker * "\n        Main.Failure2Diagnostics.snapshot!(workspace, \"after_reconstruction\"; accepted=reconstructed)")
    marker = "_try_postsolve_feasibility_pivot!(workspace, stop_requested)"
    count(marker, body) == 1 || error("Unexpected repair source; refusing instrumentation")
    body = replace(body, marker=>"Main.Failure2Diagnostics.pivot!(workspace, stop_requested)")
    return Meta.parse(body)
end

function restore(d)
    ws = JS.initialize_workspace(JS._minimization_problem(d.problem), d.options)
    ws.iterations, ws.refactorizations = d.iterations, d.refactorizations
    ws.basis = JS.Basis(copy(d.basis.basic_indices), copy(d.basis.states))
    JS.recompute!(ws; refactorize=true)
    return ws
end

function main(input, prefix)
    for suffix in (".trace.toml", ".before-reconstruction.bin")
        ispath(prefix*suffix) && error("Use a fresh output prefix")
    end
    output_prefix[] = prefix
    BLAS.set_num_threads(8)
    @assert BLAS.get_num_threads() == 8
    d = deserialize(input)
    @assert eltype(d.target_primal) == Float64
    source = read(joinpath(dirname(pathof(JS)), "solver.jl"), String)
    traced = Core.eval(JS, traced_projection(source))
    baseline = restore(d)
    baseline_result = JS._project_postsolve_basis!(baseline, d.target_primal, ()->false;
        repair_feasibility=true)
    ws = restore(d)
    traced_result = Base.invokelatest(traced, ws, d.target_primal,
        ()->false; repair_feasibility=true)
    identical = isequal(baseline_result, traced_result) &&
        baseline.basis.basic_indices == ws.basis.basic_indices &&
        baseline.basis.states == ws.basis.states &&
        reinterpret(UInt64, baseline.primal) == reinterpret(UInt64, ws.primal) &&
        reinterpret(UInt64, baseline.reduced_costs) == reinterpret(UInt64, ws.reduced_costs) &&
        reinterpret(UInt64, baseline.scratch.rho) == reinterpret(UInt64, ws.scratch.rho) &&
        baseline.iterations == ws.iterations && baseline.refactorizations == ws.refactorizations
    report = Dict("production_accepted"=>!isnothing(baseline_result),
        "traced_matches_production_bitwise"=>identical,
        "arithmetic_type"=>string(eltype(ws.primal)), "blas_threads"=>BLAS.get_num_threads(),
        "julia"=>string(VERSION), "primal_tolerance"=>d.options.primal_tolerance,
        "solve_tolerance"=>ws.progress.numerical_policy.solve_tolerance,
        "source_sha256"=>bytes2hex(sha256(source)), "input_sha256"=>bytes2hex(open(sha256,input)),
        "events"=>events)
    open(prefix*".trace.toml", "w") do io
        TOML.print(io, report; sorted=true)
    end
    @assert identical
    println("Trace matches production bitwise: ", identical)
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 2 || error("Expected: handoff.bin fresh-output-prefix")
    Failure2Diagnostics.main(ARGS...)
end
