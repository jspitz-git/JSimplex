# Count final candidate rejections without changing numerical or adaptive decisions.
using JSimplex, SHA, TOML, Serialization
const ROOT = dirname(dirname(pathof(JSimplex)))
setup_path = joinpath(@__DIR__,"phase_one_first_failure.jl")
setup = read(setup_path,String)
call = "main(vcat(ARGS[1:4], [OUTPUT_PREFIX * \".toml\"]))"
@assert count(call,setup) == 1
Base.include_string(Main,replace(setup,call=>""),setup_path)
@assert ARGS[1:3] == ["runtime","primal","both"]
const REJECTIONS = Dict{Tuple{String,Bool,Int},Int}()
const ITERATION_REJECTIONS = Dict{Int,Int}()
const PRICE_SAMPLES = Dict{Int,Dict{String,Any}}()
function rejection_work(ws,message,refreshed)
    isnothing(ws.progress.diagnostics) && return nothing
    journal = ws.scratch.perturbations
    level = isnothing(journal) || isnothing(journal.bounds) ? 0 : journal.bounds.level
    key = (message,refreshed,level)
    REJECTIONS[key] = get(REJECTIONS,key,0)+1
    ITERATION_REJECTIONS[ws.iterations] = get(ITERATION_REJECTIONS,ws.iterations,0)+1
    if message == "primal reduced cost disagrees with its direction" &&
       refreshed && !haskey(PRICE_SAMPLES,level)
        entering = ws.scratch.selected_entering
        path = OUTPUT_PREFIX*"-price-level-"*string(level)*".bin"
        # Mathematical data and the observed FTRAN direction, not an exact
        # continuation checkpoint. Keep binary snapshots local.
        serialize(path,(;problem=ws.problem,basis=ws.basis,options=ws.options,
            costs=ws.costs,lower=ws.lower,upper=ws.upper,primal=ws.primal,
            reduced_costs=ws.reduced_costs,column=ws.scratch.row_solution,entering,
            iteration=ws.iterations,updates=length(ws.factorization.updates)))
        PRICE_SAMPLES[level] = Dict("iteration"=>ws.iterations,"entering"=>entering,
            "bound_level"=>level,"cached_price"=>ws.reduced_costs[entering],
            "factor_updates"=>length(ws.factorization.updates),"snapshot"=>path)
    end
    return nothing
end
source = read(joinpath(ROOT,"src","primal_simplex.jl"),String)
i = first(findfirst("function _legacy_primal_iteration!",source))
j = first(findnext("\nfunction ",source,i+1))-1
body = source[i:j]
needle = "defer_weak = workspace.progress.numerical_policy.adaptive_pricing"
@assert count(needle,body) == 1
body = replace(body,needle=>"defer_weak = false")
needle = "                push!(rejected, entering)"
@assert count(needle,body) == 1
body = replace(body,needle=>"                Main.rejection_work(workspace,terminal.message,basis_refreshed)\n"*needle)
EXTRA_DIAGNOSTIC_METADATA["rejection_counter_method_sha256"] = bytes2hex(sha256(body))
Base.include_string(JSimplex,body,"diagnostic_primal_rejection_work.jl")
main(vcat(ARGS[1:4],[OUTPUT_PREFIX*".toml"]))
report = TOML.parsefile(OUTPUT_PREFIX*".toml")
report["price_samples"] = [PRICE_SAMPLES[k] for k in sort!(collect(keys(PRICE_SAMPLES)))]
report["rejection_breakdown"] = [Dict("message"=>message,"basis_refreshed"=>fresh,
    "bound_level"=>level,"count"=>count) for ((message,fresh,level),count) in
    sort!(collect(REJECTIONS);by=x->x.first)]
report["largest_rejection_iterations"] = [Dict("iteration"=>iteration,"count"=>count)
    for (iteration,count) in first(sort!(collect(ITERATION_REJECTIONS);
        by=x->(-x.second,x.first)),min(10,length(ITERATION_REJECTIONS)))]
@assert sum(values(REJECTIONS);init=0) == get(report["events"],"pivot_rejected",0)
open(OUTPUT_PREFIX*".toml","w") do io
    TOML.print(io,report)
end
println("REJECTIONS ",report["rejection_breakdown"])
println("LARGEST ",report["largest_rejection_iterations"])
