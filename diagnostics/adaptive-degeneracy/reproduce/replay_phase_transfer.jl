# Replay a captured phase export and compare point-preserving alternatives.
using JSimplex, Serialization, Test, SHA, TOML, LinearAlgebra
BLAS.set_num_threads(1)
length(ARGS)==2 || error("Expected capture-prefix output-prefix")
prefix,output=ARGS
function rebind_transfer_workspace!(ws)
    p=ws.progress
    ws.progress=JSimplex.SimplexProgressContext(ws.problem;start_ns=time_ns(),scaling=p.scaling,
        iteration_offset=p.iteration_offset,refactorization_offset=p.refactorization_offset,
        numerical_policy=p.numerical_policy)
    journal=ws.scratch.perturbations
    isnothing(journal) || (journal.workspace_id=objectid(ws))
    return ws
end
function load_transfer()
    data=deserialize(prefix*"-before.bin")
    rebind_transfer_workspace!(data.phase);rebind_transfer_workspace!(data.original)
    return data
end
function point_report(ws,label;check_reconstruction=true)
    tolerance=ws.options.primal_tolerance
    bounds=Dict{String,Any}[]
    for j in eachindex(ws.primal)
        violation=max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),
            JSimplex._upper_violation(ws.upper[j],ws.primal[j]))
        violation>tolerance && push!(bounds,Dict("index"=>j,"value"=>ws.primal[j],
            "violation"=>violation,"basic"=>ws.basis.states[j]==JSimplex.BASIC))
    end
    ps,pc=JSimplex.primal_infeasibility_summary(ws)
    result=Dict{String,Any}("label"=>label,"pinf"=>ps,"pinf_count"=>pc,"bounds"=>bounds,
        "finite"=>JSimplex._finite_workspace(ws),
        "basic_bounds_feasible"=>JSimplex._start_primal_feasible(ws),
        "point_certified"=>JSimplex._legacy_primal_point_certified(ws),
        "original_primal_feasible"=>JSimplex._original_primal_feasible(ws,ws.primal[1:size(ws.problem.A,2)]),
        "objective"=>dot(ws.costs,ws.primal))
    if check_reconstruction
        result["basis_reliable"]=JSimplex._recomputed_basis_reliable(ws)
        B=JSimplex._basis_matrix!(ws)
        rhs=JSimplex._basis_primal_rhs(ws)
        scratch=JSimplex.SolveQualityScratch(eltype(ws.primal),length(rhs))
        for (label,x,b,transposed) in (("primal_solve",ws.primal[ws.basis.basic_indices],rhs,false),
            ("dual_solve",ws.scratch.rho,ws.costs[ws.basis.basic_indices],true))
            quality=JSimplex.solve_quality!(scratch,B,x,b,ws.progress.numerical_policy;transposed)
            result[label]=Dict("absolute_error"=>quality.absolute_error,
                "relative_error"=>quality.relative_error,"finite"=>quality.finite,
                "reliable"=>quality.reliable)
        end
    end
    return result
end
function mapped_workspace(data;carry=false)
    phase,original,mapping=data.phase,data.original,data.mapping
    fresh=JSimplex.initialize_workspace(original.problem,original.options;progress=original.progress)
    JSimplex._phase_inherit_work!(fresh,phase)
    fresh.basis=JSimplex.Basis(mapping.phase_to_original[phase.basis.basic_indices],
        phase.basis.states[mapping.original_to_phase])
    mapped=copy(phase.primal[mapping.original_to_phase])
    carry && (fresh.primal.=mapped)
    candidate=copy(mapped[fresh.basis.basic_indices])
    JSimplex._phase_refactor!(fresh,original,()->false)
    return fresh,mapped,candidate
end
records=Dict{String,Any}[]
metadata=Dict{String,Any}("scope"=>"Local phase-boundary replay; timers reset, no outer-driver continuation",
    "before_sha256"=>bytes2hex(open(sha256,prefix*"-before.bin")),
    "fresh_sha256"=>bytes2hex(open(sha256,prefix*"-fresh.bin")))
@testset "Captured phase transfer replay" begin
    data=load_transfer();phase,mapping=data.phase,data.mapping
    @test all(j->phase.basis.states[j]!=JSimplex.BASIC,mapping.artificial_columns)
    metadata["iteration"]=phase.iterations
    metadata["artificial_sum"]=sum(phase.primal[mapping.artificial_columns])
    metadata["nonzero_artificials"]=count(!iszero,phase.primal[mapping.artificial_columns])
    metadata["maximum_artificial_magnitude"]=maximum(abs,phase.primal[mapping.artificial_columns];init=0.0)
    push!(records,point_report(phase,"auxiliary before transfer";check_reconstruction=false))
    metadata["auxiliary_optimality_certified"]=JSimplex._original_optimality_certified(phase,phase.primal[1:size(phase.problem.A,2)])
    @test metadata["auxiliary_optimality_certified"]
    data=load_transfer();before=copy(data.original.primal);basis=copy(data.original.basis.basic_indices)
    accepted=JSimplex.remove_artificials!(data.phase,data.mapping,data.original,data.policy,()->false)
    metadata["baseline_transfer_accepted"]=accepted
    @test !accepted
    @test isequal(data.original.primal,before) && data.original.basis.basic_indices==basis
    baseline,mapped,candidate=mapped_workspace(load_transfer())
    captured=rebind_transfer_workspace!(deserialize(prefix*"-fresh.bin"))
    @test isequal(baseline.primal,captured.primal)
    @test baseline.basis.basic_indices==captured.basis.basic_indices && baseline.basis.states==captured.basis.states
    push!(records,point_report(baseline,"replayed baseline reconstruction"))
    nonbasic=baseline.basis.states.!=JSimplex.BASIC
    metadata["changed_nonbasic_indices"]=findall(nonbasic .& (baseline.primal.!=mapped))
    metadata["maximum_nonbasic_change"]=maximum(abs.(baseline.primal[nonbasic].-mapped[nonbasic]);init=0.0)
    metadata["changed_nonbasic_values"]=[Dict("index"=>j,"mapped"=>mapped[j],
        "reconstructed"=>baseline.primal[j],"state"=>string(baseline.basis.states[j]),
        "structural"=>j<=size(baseline.problem.A,2),"lower"=>(isfinite(baseline.lower[j]) ? baseline.lower[j].value : -Inf),
        "upper"=>(isfinite(baseline.upper[j]) ? baseline.upper[j].value : Inf)) for j in metadata["changed_nonbasic_indices"]]
    for carry in (false,true)
        fresh,mapped,candidate=mapped_workspace(load_transfer();carry)
        label=carry ? "mapped nonbasic values" : "baseline nonbasic values"
        push!(records,point_report(fresh,label*" before completion"))
        nonbasic=fresh.basis.states.!=JSimplex.BASIC
        saved_nonbasic=copy(fresh.primal[nonbasic])
        terminal=JSimplex._finish_legacy_primal_point!(fresh,candidate,()->false)
        @test isequal(fresh.primal[nonbasic],saved_nonbasic)
        result=point_report(fresh,label*" after completion")
        result["completion_returned_success"]=isnothing(terminal)
        result["completion_message"]=isnothing(terminal) ? "" : terminal.message
        result["same_mapped_point"]=isequal(fresh.primal,mapped)
        result["maximum_change_from_mapped"]=maximum(abs.(fresh.primal.-mapped);init=0.0)
        push!(records,result)
        serialize(output*(carry ? "-carried.bin" : "-baseline.bin"),fresh)
    end
    source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
    i=first(findfirst("function _remove_artificials!",source))
    j=first(findnext("\nfunction ",source,i+1))-1
    body=source[i:j]
    before="    _phase_refactor!(fresh,original,stop)"
    after="    fresh.primal .= phase.primal[map.original_to_phase]\n    candidate = copy(fresh.primal[fresh.basis.basic_indices])\n"*before*"\n    isnothing(_finish_legacy_primal_point!(fresh,candidate,stop)) || return false"
    @assert count(before,body)==1
    body=replace(body,before=>after)
    metadata["export_variant_sha256"]=bytes2hex(sha256(body))
    write(output*"-export-method.jl",body)
    Base.include_string(JSimplex,body,"diagnostic_mapped_point_export.jl")
    data=load_transfer()
    exported=Base.invokelatest(JSimplex.remove_artificials!,data.phase,data.mapping,data.original,data.policy,()->false)
    metadata["complete_export_accepted"]=exported
    if exported
        row=point_report(data.original,"completed mapped-point export")
        @test row["finite"] && row["basis_reliable"] && row["basic_bounds_feasible"]
        @test row["point_certified"] && row["original_primal_feasible"]
        row["pricing"]=string(JSimplex._effective_pricing(data.original,:primal))
        push!(records,row)
        serialize(output*"-exported.bin",data.original)
    end
end
metadata["records"]=records
open(output*".toml","w") do io
    TOML.print(io,metadata)
end
