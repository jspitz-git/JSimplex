# Apply captured directions to the common workspace at the end of a failed pass.
# Use the retained baseline capture; a corrected pass has already completed its flip.
using JSimplex, Serialization, TOML, LinearAlgebra
BLAS.set_num_threads(1)
length(ARGS)==2 || error("Expected probe snapshot and output TOML")
data=deserialize(ARGS[1]);ws=data.workspace
records=Dict{String,Any}[]
for item in data.directions
    j,d,column=item.entering,item.direction,item.column
    opposite=d>0 ? ws.upper[j] : ws.lower[j]
    limit=isfinite(opposite) ? (JSimplex.bound_value(opposite)-ws.primal[j])/d : Inf
    choices=Dict{String,Any}[]
    limiter=0
    for (row,index) in enumerate(ws.basis.basic_indices)
        movement=-d*column[row];iszero(movement) && continue
        bound=movement>0 ? ws.upper[index] : ws.lower[index]
        isfinite(bound) || continue
        raw=(JSimplex.bound_value(bound)-ws.primal[index])/movement
        relaxed=JSimplex._primal_relaxed_step(raw,ws.options.primal_tolerance,movement)
        if isfinite(relaxed) && max(0.0,relaxed)<limit
            limit=max(0.0,relaxed);limiter=row
        end
        push!(choices,Dict("row"=>row,"index"=>index,"pivot"=>column[row],
            "raw"=>raw,"step"=>max(0.0,raw),"relaxed"=>relaxed))
    end
    admissible=filter(x->x["step"]<=limit,choices)
    sort!(admissible;by=x->-abs(x["pivot"]))
    selected=nothing
    for c in admissible
        c["snap_ok"]=JSimplex._primal_bound_snap_feasible(ws,j,d,column,c["row"])
        if c["snap_ok"]
            selected=c;break
        end
    end
    record=Dict{String,Any}("entering"=>j,"limit"=>limit,"limiter"=>limiter,
        "admissible_count"=>length(admissible),"largest_candidates"=>first(admissible,min(5,length(admissible))))
    if !isnothing(selected)
        record["harris"]=selected
        violations=Dict{String,Any}[]
        for (r,index) in enumerate(ws.basis.basic_indices)
            value=ws.primal[index]-d*column[r]*selected["step"]
            v=max(JSimplex._lower_violation(ws.lower[index],value),JSimplex._upper_violation(ws.upper[index],value))
            if v>ws.options.primal_tolerance
                push!(violations,Dict("row"=>r,"index"=>index,"violation"=>v,"value"=>value,
                    "before"=>ws.primal[index],"pivot"=>column[r],
                    "lower"=>isfinite(ws.lower[index]) ? JSimplex.bound_value(ws.lower[index]) : "-Inf",
                    "upper"=>isfinite(ws.upper[index]) ? JSimplex.bound_value(ws.upper[index]) : "Inf"))
            end
        end
        record["violations"]=violations
    end
    if isfinite(opposite)
        flip_step=(JSimplex.bound_value(opposite)-ws.primal[j])/d
        before=copy(ws.primal)
        try
            for (r,index) in enumerate(ws.basis.basic_indices)
                ws.primal[index]-=d*column[r]*flip_step
            end
            ws.primal[j]=JSimplex.bound_value(opposite)
            record["flip_step"]=flip_step
            record["flip_point_certified"]=JSimplex._legacy_primal_point_certified(ws)
            record["flip_max_bound_violation"]=maximum(index->max(
                JSimplex._lower_violation(ws.lower[index],ws.primal[index]),
                JSimplex._upper_violation(ws.upper[index],ws.primal[index])),eachindex(ws.primal))
        finally
            copyto!(ws.primal,before)
        end
    end
    push!(records,record)
end
open(io->TOML.print(io,Dict("records"=>records)),ARGS[2],"w")
println("Analyzed ",length(records)," ratio decisions")
