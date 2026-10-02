# Probe complete certificates; these trials do not change the solver's recovery policy.
using JSimplex,Serialization,LinearAlgebra,SHA,TOML
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
function main(prefix,output)
    ws=deserialize(prefix*"-before.bin")
    ws.scratch.perturbations.workspace_id=objectid(ws)
    terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
    failed=deserialize(prefix*".bin")
    @assert !isnothing(terminal) && terminal.status==NUMERICAL_ERROR
    @assert isequal(ws.primal,failed.primal) && ws.basis.states==failed.basis.states
    prediction=deserialize(prefix*"-8464-prediction.bin")
    rounded=deserialize(prefix*"-8464-rounded.bin")
    basic=ws.basis.basic_indices
    nonbasic=findall(!=(JSimplex.BASIC),ws.basis.states)
    @assert isequal(prediction[nonbasic],rounded[nonbasic])
    records=Dict{String,Any}[]
    function report(tag; extra=Dict{String,Any}())
        record=Dict{String,Any}("tag"=>tag,"certified"=>JSimplex._legacy_primal_point_certified(ws),
            "model"=>JSimplex._legacy_primal_model_feasible(ws),
            "equations"=>JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance),
            "x9126"=>ws.primal[9126],"x1312"=>ws.primal[1312],
            "nonbasic_unchanged"=>isequal(ws.primal[nonbasic],rounded[nonbasic]))
        merge!(record,extra);push!(records,record);println(record);flush(stdout)
    end
    ws.primal .= rounded
    @assert ws.basis.states[9126]==JSimplex.BASIC
    ws.primal[9126]=prevfloat(ws.primal[9126])
    report("adjacent_basic_9126")
    for alpha in (0.0,0.25,0.5,0.75,1.0)
        ws.primal .= rounded
        for j in basic
            ws.primal[j]=(1-alpha)*rounded[j]+alpha*prediction[j]
        end
        report("blend";extra=Dict("prediction_fraction"=>alpha))
    end
    for tag in ("prediction","balanced")
        ws.primal .= deserialize(prefix*"-8464-"*tag*".bin")
        accepted=JSimplex._try_native_primal_point_correction!(ws,()->false)
        report("correct_"*tag;extra=Dict("accepted"=>accepted))
        accepted && serialize(prefix*"-probe-"*tag*".bin",copy(ws.primal))
    end
    open(output,"w") do io
        TOML.print(io,Dict("scope"=>"Diagnostic native point trials at the captured basis; no driver continuation", "records"=>records))
    end
end
main(ARGS...)
