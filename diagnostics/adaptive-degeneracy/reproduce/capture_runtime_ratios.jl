# Observe selected small pivots and their competing Harris rows without intervention.
using JSimplex, SHA, TOML, Serialization
const ROOT = dirname(dirname(pathof(JSimplex)))
setup_path = joinpath(@__DIR__,"phase_one_first_failure.jl")
setup = read(setup_path,String)
call = "main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"
@assert count(call,setup) == 1
Base.include_string(Main,replace(setup,call=>""),setup_path)
@assert ARGS[1:3] == ["runtime","primal","both"]
const RATIO_CAPTURES = Dict{String,Any}[]
const CAPTURE_KEYS = Set{String}()
bound_number(b) = isfinite(b) ? Float64(JSimplex.bound_value(b)) : string(b)
function capture_ratio(ws,entering,direction,column,step,selected,state,refreshed)
    isnothing(ws.progress.diagnostics) && return
    refreshed || return
    journal = ws.scratch.perturbations
    bounds = isnothing(journal) ? nothing : journal.bounds
    level = isnothing(bounds) ? 0 : bounds.level
    tiny = selected > 0 && abs(column[selected]) <= ws.options.zero_tolerance
    key = selected == -1 && level > 0 ? "inconclusive_after_shift" :
        tiny ? (level == 0 ? "tiny_before_shift" : ws.iterations < 7000 ?
                "tiny_after_shift" : "tiny_late") : ""
    isempty(key) || key in CAPTURE_KEYS || length(RATIO_CAPTURES) < 4 || return
    isempty(key) && return
    key in CAPTURE_KEYS && return
    push!(CAPTURE_KEYS,key)
    tol = ws.options.primal_tolerance
    rows = Dict{String,Any}[]
    opposite = direction > 0 ? ws.upper[entering] : ws.lower[entering]
    opposite_step = isfinite(opposite) ?
        (JSimplex.bound_value(opposite)-ws.primal[entering])/direction : Inf
    relaxed_limit = opposite_step
    limiting_row = 0
    first_pass_exit = "none"
    first_pass_exit_row = 0
    for (row,index) in enumerate(ws.basis.basic_indices)
        movement = -direction*column[row]
        iszero(movement) && continue
        bound = movement > 0 ? ws.upper[index] : ws.lower[index]
        isfinite(bound) || continue
        raw = (JSimplex.bound_value(bound)-ws.primal[index])/movement
        violation = movement > 0 ? JSimplex._upper_violation(bound,ws.primal[index]) :
            JSimplex._lower_violation(bound,ws.primal[index])
        if first_pass_exit == "none" && (!isfinite(raw) || (raw < 0 && violation > tol))
            first_pass_exit = !isfinite(raw) ? "nonfinite_ratio" : "bound_violation"
            first_pass_exit_row = row
        end
        relaxed = JSimplex._primal_relaxed_step(raw,tol,movement)
        if isfinite(relaxed) && relaxed < relaxed_limit
            relaxed_limit,limiting_row = max(0.0,relaxed),row
        end
        original = isnothing(bounds) ? bound : movement > 0 ?
            bounds.original_upper[index] : bounds.original_lower[index]
        push!(rows,Dict("row"=>row,"variable"=>index,"pivot"=>column[row],
            "value"=>ws.primal[index],"bound"=>bound_number(bound),
            "original_bound"=>bound_number(original),"fixed"=>JSimplex._is_fixed(ws.lower[index],ws.upper[index]),
            "raw_step"=>raw,"candidate"=>max(0.0,raw),"relaxed_step"=>relaxed,
            "rejected_row"=>(row in ws.scratch.rejected_rows)))
    end
    # These are only reconstructed band members, not accepted pivot candidates.
    # If the first pass exits early, production never reaches this Harris band.
    eligible = filter(r->r["candidate"]<=relaxed_limit && !r["rejected_row"],rows)
    sort!(eligible;by=r->-abs(r["pivot"]))
    sort!(rows;by=r->r["candidate"])
    keep = unique(vcat([r["row"] for r in first(eligible,min(10,length(eligible)))],
        [r["row"] for r in first(rows,min(10,length(rows)))],[selected,limiting_row]))
    selected_rows = filter(r->r["row"] in keep,rows)
    for r in selected_rows
        r["snap_safe"] = JSimplex._primal_bound_snap_feasible(ws,entering,direction,column,r["row"])
    end
    path = OUTPUT_PREFIX*"-"*key*".bin"
    serialize(path,(;problem=ws.problem,basis=ws.basis,options=ws.options,
        costs=ws.costs,lower=ws.lower,upper=ws.upper,primal=ws.primal,
        reduced_costs=ws.reduced_costs,column,entering,direction,step,selected,
        iteration=ws.iterations,updates=length(ws.factorization.updates),bounds,
        policy=ws.progress.numerical_policy,rejected_rows=copy(ws.scratch.rejected_rows)))
    record = Dict("key"=>key,"iteration"=>ws.iterations,"entering"=>entering,
        "direction"=>direction,"selected_row"=>selected,"step"=>isnothing(step) ? "none" : step,
        "bound_level"=>level,"factor_updates"=>length(ws.factorization.updates),
        "cached_price"=>ws.reduced_costs[entering],"column_max"=>maximum(abs,column),
        "primal_tolerance"=>tol,"zero_tolerance"=>ws.options.zero_tolerance,
        "relaxed_limit"=>relaxed_limit,"limiting_row"=>limiting_row,
        "first_pass_exit"=>first_pass_exit,"first_pass_exit_row"=>first_pass_exit_row,
        "reconstructed_band_rows"=>length(eligible),
        "reconstructed_band_above_zero"=>count(r->abs(r["pivot"])>ws.options.zero_tolerance,eligible),
        "opposite_step"=>opposite_step,"rows"=>selected_rows,"snapshot"=>path)
    push!(RATIO_CAPTURES,record)
    println("RATIO_CAPTURE ",record);flush(stdout)
end
source = read(joinpath(ROOT,"src","primal_simplex.jl"),String)
i = first(findfirst("function _primal_iteration_unchecked!",source))
j = first(findnext("\nfunction ",source,i+1))-1
body = source[i:j]
needle = "    workspace.scratch.selected_row = leaving_row"
@assert count(needle,body) == 2
body = replace(body,needle=>"    Main.capture_ratio(workspace,entering,direction,tableau_column,step,leaving_row,leaving_state,basis_refreshed)\n"*needle;count=1)
EXTRA_DIAGNOSTIC_METADATA["ratio_capture_method_sha256"] = bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_runtime_ratios.jl")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))
report = TOML.parsefile(OUTPUT_PREFIX*".toml")
report["ratio_captures"] = RATIO_CAPTURES
open(OUTPUT_PREFIX*".toml","w") do io
    TOML.print(io,report)
end
