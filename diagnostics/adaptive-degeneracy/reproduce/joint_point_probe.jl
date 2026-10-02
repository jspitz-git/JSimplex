# Diagnostic feasibility probe only. No factor solve, pivot or adaptive transition.
using JSimplex, SparseArrays, Serialization, LinearAlgebra, TOML, SHA
BLAS.set_num_threads(1)
const ROOT=dirname(dirname(pathof(JSimplex)))

function point_workspace(path)
    saved=deserialize(path)
    ws=JSimplex.initialize_workspace(saved.problem,saved.options;
        progress=JSimplex.SimplexProgressContext(saved.problem;numerical_policy=saved.policy))
    ws.basis=deepcopy(saved.basis)
    ws.primal .= saved.primal
    ws.lower .= saved.lower; ws.upper .= saved.upper; ws.costs .= saved.costs
    ws.reduced_costs .= saved.reduced_costs
    ws.scratch.perturbations=deepcopy(saved.perturbations)
    isnothing(ws.scratch.perturbations) || (ws.scratch.perturbations.workspace_id=objectid(ws))
    return ws
end

# Compensated products and sums in the input floating type, without fast-math.
function row_value(Arow,row,x)
    total=zero(eltype(x)); correction=zero(eltype(x))
    for k in nzrange(Arow,row)
        product=Arow.nzval[k]*x[Arow.rowval[k]]
        error=fma(Arow.nzval[k],x[Arow.rowval[k]],-product)
        next=total+product; part=next-total
        correction+=(total-(next-part))+(product-part)+error
        total=next
    end
    return total+correction
end

function interval(lower,upper,tol)
    lo=isfinite(lower) ? last(JSimplex._primal_difference_bounds(JSimplex.bound_value(lower),tol)) : -Inf
    hi=isfinite(upper) ? first(JSimplex._primal_sum_bounds(JSimplex.bound_value(upper),tol)) : Inf
    return lo,hi
end

function joint_projection!(ws; sweeps=8, margin_fraction=0.25, movement_factor=8.0)
    x=ws.primal; original=copy(x); T=eltype(x); tol=ws.options.primal_tolerance
    Arow=sparse(transpose(ws.problem.A)); n=size(ws.problem.A,2)
    basic=ws.basis.states .== JSimplex.BASIC
    # Existing certificates choose original model bounds unless an owned shift is active.
    working=JSimplex._has_active_bound_perturbations(ws.scratch.perturbations)
    working && JSimplex._check_perturbation_owner(ws,ws.scratch.perturbations)
    model_lower=working ? ws.lower : vcat(ws.problem.column_lower,ws.problem.row_lower)
    model_upper=working ? ws.upper : vcat(ws.problem.column_upper,ws.problem.row_upper)
    lower=fill(T(-Inf),n); upper=fill(T(Inf),n)
    for j in 1:n
        lo,hi=interval(ws.lower[j],ws.upper[j],tol)
        ml,mh=interval(model_lower[j],model_upper[j],tol)
        radius=T(movement_factor)*max(tol,eps(T)*max(one(T),abs(original[j])))
        lower[j]=max(lo,ml,original[j]-radius)
        upper[j]=min(hi,mh,original[j]+radius)
    end
    trace=Dict{String,Any}[]
    certified=false
    for sweep in 1:sweeps
        corrections=0; blocked=0
        for j in 1:n
            basic[j] || continue
            lo,hi=lower[j],upper[j]
            lo<=hi || continue
            margin=min(T(margin_fraction)*tol,(hi-lo)/4)
            x[j]=clamp(x[j],lo+margin,hi-margin)
        end
        for row in axes(Arow,2)
            activity=n+row
            lo,hi=interval(model_lower[activity],model_upper[activity],tol)
            if basic[activity]
                # There must also be an admissible stored activity within tolerance.
                sl,sh=interval(ws.lower[activity],ws.upper[activity],2tol)
                lo=max(lo,sl);hi=min(hi,sh)
            else
                lo=max(lo,last(JSimplex._primal_difference_bounds(x[activity],tol)))
                hi=min(hi,first(JSimplex._primal_sum_bounds(x[activity],tol)))
            end
            lo<=hi || (blocked+=1;continue)
            margin=min(T(margin_fraction)*tol,(hi-lo)/4)
            value=row_value(Arow,row,x)
            target=clamp(value,lo+margin,hi-margin)
            isfinite(value) && isfinite(target) || (blocked+=1;continue)
            target==value && continue
            scale=zero(T)
            for k in nzrange(Arow,row)
                j=Arow.rowval[k];basic[j] || continue
                scale=max(scale,abs(Arow.nzval[k]))
            end
            scale>0 && isfinite(scale) || (blocked+=1;continue)
            norm=zero(T)
            for k in nzrange(Arow,row)
                j=Arow.rowval[k];basic[j] || continue
                norm+=(Arow.nzval[k]/scale)^2
            end
            multiplier=((target-value)/scale)/norm
            isfinite(multiplier) || (blocked+=1;continue)
            for k in nzrange(Arow,row)
                j=Arow.rowval[k];basic[j] || continue
                x[j]=clamp(x[j]+multiplier*(Arow.nzval[k]/scale),lower[j],upper[j])
            end
            corrections+=1
        end
        for row in axes(Arow,2)
            activity=n+row;basic[activity] || continue
            lo,hi=interval(ws.lower[activity],ws.upper[activity],tol)
            x[activity]=clamp(row_value(Arow,row,x),lo,hi)
        end
        certified=JSimplex._legacy_primal_point_certified(ws)
        push!(trace,Dict("sweep"=>sweep,"row_corrections"=>corrections,"blocked"=>blocked,
            "certified"=>certified,"maximum_change"=>maximum(abs.(x-original))))
        println(trace[end]);flush(stdout)
        certified && break
    end
    @assert isequal(x[.!basic],original[.!basic])
    result=Dict("certified"=>certified,"trace"=>trace,
        "nonbasic_unchanged"=>isequal(x[.!basic],original[.!basic]))
    x .= original
    return result
end

function main(paths,output)
    records=Dict{String,Any}[]
    for path in paths
        println("SNAPSHOT ",path);flush(stdout)
        ws=point_workspace(path)
        record=Dict("path"=>path,"sha256"=>bytes2hex(open(sha256,path)),
            "initially_certified"=>JSimplex._legacy_primal_point_certified(ws),
            "probe"=>joint_projection!(ws))
        push!(records,record)
    end
    open(output,"w") do io
        TOML.print(io,Dict("scope"=>"Diagnostic joint projection from saved mathematical points; no basis continuation",
            "records"=>records))
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main(ARGS[1:end-1],ARGS[end])
end
