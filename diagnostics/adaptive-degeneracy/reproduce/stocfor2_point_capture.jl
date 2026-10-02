# Observe primal feasibility-loss sites and nearby iteration boundaries.
path=joinpath(@__DIR__,"broad_corpus.jl")
Base.include_string(Main,first(split(read(path,String),"\nhashes=instrument!()")),path)
const POINT_RECORDS=Dict{String,Any}[]
const POINT_KEYS=Set{Any}()
function capture_stocfor_point(ws,label;force=false)
    iteration=ws.iterations+ws.progress.iteration_offset
    (force || 1954<=iteration<=1957) || return
    key=(CAPTURE_PREFIX[],iteration,label)
    key in POINT_KEYS && return
    push!(POINT_KEYS,key)
    prefix=CAPTURE_PREFIX[]*"-point-"*string(length(POINT_KEYS))
    detach(ws,prefix*".bin")
    record=Dict("prefix"=>prefix,"iteration"=>iteration,"local_iteration"=>ws.iterations,
        "label"=>label,"pinf"=>JSimplex.primal_infeasibility(ws),
        "certified"=>JSimplex._legacy_primal_point_certified(ws),
        "refactorizations"=>ws.refactorizations,"algorithm"=>string(ws.options.algorithm))
    push!(POINT_RECORDS,record)
    open(ARGS[4]*"-points.toml","w") do io;TOML.print(io,Dict("captures"=>POINT_RECORDS));end
    println("POINT ",record);flush(stdout)
end
hashes=instrument!()
source=read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
needle="return DualTermination(NUMERICAL_ERROR, \"primal feasibility lost\")"
@assert count(needle,source)==5
site=Ref(0)
source=replace(source,needle=>(_)->begin
    site[]+=1
    "return (Main.capture_stocfor_point(workspace,\"loss-site-$(site[])\";force=true); DualTermination(NUMERICAL_ERROR,\"primal feasibility lost\"))"
end)
needle="        terminal = _primal_iteration!(workspace, stop_requested, reduced_cost_tolerance)"
@assert count(needle,source)==1
source=replace(source,needle=>"        Main.capture_stocfor_point(workspace,\"before-iteration\")\n"*needle*"\n        Main.capture_stocfor_point(workspace,\"after-iteration\")")
needle="        isnothing(terminal) || return terminal\n    end\nend\n\n_primal_infeasibility_certified"
@assert count(needle,source)==1
source=replace(source,needle=>"        Main.capture_stocfor_point(workspace,\"after-observation\")\n"*needle)
Base.include_string(JSimplex,source,"diagnostic_stocfor2_point.jl")
# Re-including primal code must not re-enable the separate weak-pivot heuristic.
@assert Base.invokelatest(isolate_pricing_trials!)==hashes["pricing_isolation"]
hashes["point_capture"]=bytes2hex(sha256(source))
Base.invokelatest(main,ARGS,hashes)
