# Inspect the complete working-bound and equation certificate for each captured point.
using JSimplex,Serialization,LinearAlgebra,SparseArrays,SHA,TOML
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
q(x)=Rational{BigInt}(x)
bound_number(b)=isfinite(b) ? JSimplex.bound_value(b) : "unbounded"
function exact_violation(value,lower,upper)
    max(zero(value),isfinite(lower) ? q(JSimplex.bound_value(lower))-value : zero(value),
        isfinite(upper) ? value-q(JSimplex.bound_value(upper)) : zero(value))
end
function inspect_point(ws,tag)
    p=ws.problem;n=size(p.A,2);tol=ws.options.primal_tolerance
    point=ws.primal
    bounds=Dict{String,Any}[]
    for j in eachindex(point)
        violation=exact_violation(q(point[j]),ws.lower[j],ws.upper[j])
        violation>q(tol) || continue
        push!(bounds,Dict("variable"=>j,"basic"=>(ws.basis.states[j]==JSimplex.BASIC),
            "structural"=>(j<=n),"value"=>point[j],"lower"=>bound_number(ws.lower[j]),
            "upper"=>bound_number(ws.upper[j]),"exact_excess"=>Float64(violation-q(tol)),
            "native_violation"=>max(JSimplex._lower_violation(ws.lower[j],point[j]),
                JSimplex._upper_violation(ws.upper[j],point[j]))))
    end
    lo,hi=JSimplex._primal_row_bounds(p.A,point[1:n],Val(false))
    suspects=Int[]
    for i in eachindex(lo)
        stored=Bound(point[n+i])
        model_ok=JSimplex._primal_interval_within_bounds(lo[i],hi[i],ws.lower[n+i],ws.upper[n+i],tol)
        equation_ok=JSimplex._primal_interval_within_bounds(lo[i],hi[i],stored,stored,tol)
        model_ok && equation_ok || push!(suspects,i)
    end
    slots=Dict(row=>k for (k,row) in enumerate(suspects))
    exact=zeros(Rational{BigInt},length(suspects))
    for col in axes(p.A,2), k in nzrange(p.A,col)
        slot=get(slots,p.A.rowval[k],0)
        slot==0 && continue
        exact[slot]+=q(p.A.nzval[k])*q(point[col])
    end
    rows=Dict{String,Any}[]
    for (slot,row) in enumerate(suspects)
        violation=exact_violation(exact[slot],ws.lower[n+row],ws.upper[n+row])
        error=exact[slot]-q(point[n+row])
        violation<=q(tol) && abs(error)<=q(tol) && continue
        indices,coefficients=findnz(p.A[row,:])
        push!(rows,Dict("row"=>row,"activity_variable"=>n+row,"stored"=>point[n+row],
            "basic"=>(ws.basis.states[n+row]==JSimplex.BASIC),
            "lower"=>bound_number(ws.lower[n+row]),"upper"=>bound_number(ws.upper[n+row]),
            "exact_activity"=>Float64(exact[slot]),"exact_bound_excess"=>Float64(violation-q(tol)),
            "exact_equation_error"=>Float64(error),"model_ok"=>violation<=q(tol),
            "equation_ok"=>abs(error)<=q(tol),"indices"=>indices,"coefficients"=>coefficients,
            "values"=>point[indices],"basic_columns"=>[j for j in indices if ws.basis.states[j]==JSimplex.BASIC]))
    end
    record=Dict("tag"=>tag,"certified"=>JSimplex._legacy_primal_point_certified(ws),
        "model"=>JSimplex._legacy_primal_model_feasible(ws),
        "rows_consistent"=>JSimplex._legacy_primal_row_consistent(ws,tol),
        "bounds"=>bounds,"rows"=>rows)
    println("POINT tag=",tag," certified=",record["certified"]," exact_bound_failures=",length(bounds),
        " model_row_failures=",count(x->!x["model_ok"],rows),
        " equation_failures=",count(x->!x["equation_ok"],rows))
    for r in bounds; println("BOUND ",r);end
    for r in rows; println("ROW ",r);end
    return record
end
function main(prefix,output)
    ws=deserialize(prefix*"-before.bin")
    ws.scratch.perturbations.workspace_id=objectid(ws)
    records=[inspect_point(ws,"before")]
    terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
    failed=deserialize(prefix*".bin")
    println("REPLAY terminal=",terminal," same_point=",isequal(ws.primal,failed.primal),
        " same_basis=",ws.basis.basic_indices==failed.basis.basic_indices && ws.basis.states==failed.basis.states)
    @assert isequal(ws.primal,failed.primal)
    @assert ws.basis.basic_indices==failed.basis.basic_indices
    @assert ws.basis.states==failed.basis.states
    @assert !isnothing(terminal) && terminal.status==NUMERICAL_ERROR
    @assert ws.iterations==failed.iterations==8464
    for tag in ("reconstructed","prediction","balanced","correction","rounded")
        path=prefix*"-8464-"*tag*".bin"
        isfile(path) || continue
        ws.primal .= deserialize(path)
        if tag=="rounded"
            captured=copy(ws.primal)
            ws.primal .= deserialize(prefix*"-8464-correction.bin")
            rounded_ok=JSimplex._round_primal_bound_trial_inward!(ws)
            @assert isequal(ws.primal,captured)
            println("ROUNDING_REPLAY completed=",rounded_ok," same_point=true")
        end
        push!(records,inspect_point(ws,tag))
    end
    open(output,"w") do io
        TOML.print(io,Dict("scope"=>"One-pivot replay and exact diagnostic certificates; no state precision change",
            "records"=>records))
    end
end
main(ARGS...)
