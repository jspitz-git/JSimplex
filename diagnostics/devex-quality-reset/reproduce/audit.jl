include("audit-original.jl")
install_audit()
const quality_stream=Ref(SHA.SHA2_256_CTX())
const quality_samples=Dict{String,Any}[]
const quality_phases=Dict{String,Int}()
function quality_observed(ws,raw,stored,computed,bad,row)
    # Independent reduction, outside all benchmark processes.
    actual=0.0
    for i in eachindex(row)
        if ws.devex_reference[i]
            actual+=row[i]*row[i]
        end
    end
    @assert isequal(actual,raw)
    @assert isequal(max(1.0,actual),computed)
    key=string(ws.scratch.phase_generation,
        !(isfinite(raw) && raw>=0 && isfinite(stored) && stored>0) ? "/invalid" : bad ? "/bad" : "/good")
    quality_phases[key]=get(quality_phases,key,0)+1
    SHA.update!(quality_stream[],codeunits(string(ws.iterations,'|',ws.refactorizations,'|',
        ws.scratch.phase_generation,'|',bits(stored),'|',bits(computed),'|',bad,'\n')))
    if bad && length(quality_samples)<128
        push!(quality_samples,Dict("iteration"=>ws.iterations,"refactors"=>ws.refactorizations,
            "phase"=>Int(ws.scratch.phase_generation),"stored"=>stored,"computed"=>computed,
            "ratio"=>max(stored,computed)/min(stored,computed)))
    end
    return nothing
end
function quality_reset_observed(ws)
    @assert all(==(1.0),ws.pricing_weights)
    @assert count(ws.devex_reference)==length(ws.basis.basic_indices)
    @assert all(i->ws.devex_reference[i],ws.basis.basic_indices)
    SHA.update!(quality_stream[],codeunits(string("reset|",ws.iterations,'|',ws.refactorizations,'\n')))
end
function reset_quality_audit!()
    quality_stream[]=SHA.SHA2_256_CTX();empty!(quality_samples);empty!(quality_phases)
end
function detailed_audit()
    a=audit_report()
    a["modes"]=mode_history
    a["quality_observed"]=mode!="off"
    a["quality_sha"]=bytes2hex(SHA.digest!(quality_stream[]))
    a["quality_counts"]=quality_counts_report()
    a["quality_phases"]=quality_phases
    a["samples"]=quality_samples
    return a
end
