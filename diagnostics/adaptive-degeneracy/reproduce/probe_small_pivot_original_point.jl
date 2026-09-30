# Diagnose original-coordinate violations independently of basis reconstruction.
using JSimplex, Serialization, LinearAlgebra, SparseArrays, TOML, SHA
BLAS.set_num_threads(1)
length(ARGS)==3 || error("Expected original target capture, pre-flip snapshot, output TOML")
data=deserialize(ARGS[1]);ws=deserialize(ARGS[2])
p=data.problem
presolved=JSimplex.presolve_problem(p)
scaled,scaling=JSimplex.scale_problem(presolved.problem)
working=JSimplex._minimization_problem(scaled)
@assert all(f->isequal(getfield(working,f),getfield(ws.problem,f)),fieldnames(typeof(working)))
before=JSimplex.postsolve_primal(presolved,JSimplex.unscale_primal(scaling,
    ws.primal[1:size(ws.problem.A,2)]))
function point_violations(p,x,tolerance)
    setprecision(BigFloat,256) do
        wide=BigFloat.(x)
        activity=BigFloat.(p.A)*wide
        records=Dict{String,Any}[]
        maxima=Dict{String,Float64}()
        counts=Dict{String,Int}()
        for (label,values,lower,upper,names) in (
            ("column",wide,p.column_lower,p.column_upper,p.column_names),
            ("row",activity,p.row_lower,p.row_upper,p.row_names))
            maximum_violation=BigFloat(0);count=0
            for i in eachindex(values)
                low=isfinite(lower[i]) ? BigFloat(JSimplex.bound_value(lower[i]))-values[i] : BigFloat(0)
                high=isfinite(upper[i]) ? values[i]-BigFloat(JSimplex.bound_value(upper[i])) : BigFloat(0)
                violation=max(BigFloat(0),low,high)
                maximum_violation=max(maximum_violation,violation)
                if violation>BigFloat(tolerance)
                    count+=1
                    push!(records,Dict("kind"=>label,"index"=>i,"name"=>names[i],
                        "violation"=>Float64(violation),"activity"=>Float64(values[i]),
                        "side"=>low>high ? "lower" : "upper"))
                end
            end
            maxima[label]=Float64(maximum_violation);counts[label]=count
        end
        sort!(records;by=x->-x["violation"])
        return Dict("certificate"=>JSimplex._original_primal_feasible(p,x,tolerance),
            "objective"=>JSimplex._restored_objective(p,x),"maximum_violation"=>maxima,
            "violations_above_tolerance"=>counts,"largest_violations"=>first(records,min(15,length(records))))
    end
end
report=Dict("target_sha256"=>bytes2hex(open(sha256,ARGS[1])),
    "before_sha256"=>bytes2hex(open(sha256,ARGS[2])),"reference_precision_bits"=>256,
    "primal_tolerance"=>data.options.primal_tolerance,
    "before_flips"=>point_violations(p,before,data.options.primal_tolerance),
    "after_flips"=>point_violations(p,data.target,data.options.primal_tolerance))
open(io->TOML.print(io,report),ARGS[3],"w")
for key in ("before_flips","after_flips")
    println(key," ",report[key]["violations_above_tolerance"]," ",report[key]["maximum_violation"])
end
