# Observe one production candidate pass at the saved Phase-II endpoint.
using JSimplex, Serialization, SHA, TOML, LinearAlgebra
BLAS.set_num_threads(1)
length(ARGS)==2 || error("Expected snapshot output-prefix")
snapshot,output=ARGS
include(joinpath(@__DIR__,"pricing_isolation.jl"))
const ISOLATION_HASH=isolate_pricing_trials!()
const RECORDS=Dict{String,Any}[]
const DIRECTIONS=Any[]
function price_probe(ws,j,column,tolerance,accepted)
    push!(RECORDS,Dict("kind"=>"price","entering"=>j,"price"=>ws.reduced_costs[j],
        "implied"=>ws.costs[j]-dot(ws.costs[ws.basis.basic_indices],column),
        "accepted"=>accepted,"max_direction"=>maximum(abs,column)))
end
function ratio_probe(ws,j,d,column,result)
    step,row,state=result
    record=Dict{String,Any}("kind"=>"ratio","entering"=>j,"direction"=>d,
        "row"=>row,"state"=>string(state),"price"=>ws.reduced_costs[j],
        "step"=>isnothing(step) ? "none" : step,"max_direction"=>maximum(abs,column),
        "refactorizations"=>ws.refactorizations)
    if row>0
        index=ws.basis.basic_indices[row]
        record["leaving"]=index;record["pivot"]=column[row]
        record["value"]=ws.primal[index]
        record["lower"]=isfinite(ws.lower[index]) ? JSimplex.bound_value(ws.lower[index]) : "-Inf"
        record["upper"]=isfinite(ws.upper[index]) ? JSimplex.bound_value(ws.upper[index]) : "Inf"
    end
    candidates=Dict{String,Any}[]
    for (r,index) in enumerate(ws.basis.basic_indices)
        movement=-d*column[r];iszero(movement) && continue
        bound=movement>0 ? ws.upper[index] : ws.lower[index]
        isfinite(bound) || continue
        raw=(JSimplex.bound_value(bound)-ws.primal[index])/movement
        push!(candidates,Dict("row"=>r,"index"=>index,"pivot"=>column[r],"raw_step"=>raw,
            "value"=>ws.primal[index],"bound"=>JSimplex.bound_value(bound),
            "relaxed"=>JSimplex._primal_relaxed_step(raw,ws.options.primal_tolerance,movement)))
    end
    sort!(candidates;by=x->max(0.0,x["raw_step"]))
    record["limiting_rows"]=first(candidates,min(12,length(candidates)))
    push!(RECORDS,record);push!(DIRECTIONS,(;entering=j,direction=d,column=copy(column),result))
    println("RATIO entering=",j," row=",row," step=",step," pivot=",get(record,"pivot",0.0));flush(stdout)
end
source=read(joinpath(dirname(pathof(JSimplex)),"legacy_primal_pivot.jl"),String)
a=first(findfirst("function _legacy_primal_direction_price_ok",source));b=first(findfirst("\n# A forward residual",source))-1
body=replace(source[a:b],"function _legacy_primal_direction_price_ok"=>"function _probe_direction_price_ok")
Base.include_string(JSimplex,body*"\nfunction _legacy_primal_direction_price_ok(ws::SimplexWorkspace{T},j::Int,column::Vector{T},tol::T) where {T<:Union{Float32,Float64}}\n result=_probe_direction_price_ok(ws,j,column,tol)\n Main.price_probe(ws,j,column,tol,result)\n return result\nend","diagnostic_price_probe.jl")
source=read(joinpath(dirname(pathof(JSimplex)),"primal_simplex.jl"),String)
a=first(findfirst("function _primal_ratio(",source));b=first(findnext("\nfunction ",source,a+1))-1
body=replace(source[a:b],"function _primal_ratio("=>"function _probe_primal_ratio(")
Base.include_string(JSimplex,body*"\nfunction _primal_ratio(ws::SimplexWorkspace{T},j::Int,d::T,column::Vector{T}) where T\n result=_probe_primal_ratio(ws,j,d,column)\n Main.ratio_probe(ws,j,d,column,result)\n return result\nend","diagnostic_ratio_probe.jl")
ws=deserialize(snapshot)
p=ws.progress
ws.progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=time_ns(),scaling=p.scaling,
    iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
    numerical_policy=p.numerical_policy)
isnothing(ws.scratch.perturbations) || (ws.scratch.perturbations.workspace_id=objectid(ws))
start=time_ns();stop=()->(time_ns()-start)/1e9>180
before=(iterations=ws.iterations,refactorizations=ws.refactorizations,objective=dot(ws.costs,ws.primal))
terminal=JSimplex._primal_iteration!(ws,stop,ws.options.dual_tolerance)
report=Dict("snapshot_sha256"=>bytes2hex(open(sha256,snapshot)),"isolation_sha256"=>ISOLATION_HASH,
    "records"=>RECORDS,"before_iterations"=>before.iterations,"after_iterations"=>ws.iterations,
    "before_refactorizations"=>before.refactorizations,"after_refactorizations"=>ws.refactorizations,
    "zero_tolerance"=>ws.options.zero_tolerance,"primal_tolerance"=>ws.options.primal_tolerance,
    "dual_tolerance"=>ws.options.dual_tolerance,
    "status"=>isnothing(terminal) ? "step" : string(terminal.status),
    "message"=>isnothing(terminal) ? "" : terminal.message)
serialize(output*".bin",(;workspace=ws,directions=DIRECTIONS))
open(io->TOML.print(io,report),output*".toml","w")
println("RESULT ",report["status"]," ",report["message"]," records=",length(RECORDS));flush(stdout)
