# Trace the saved point through reversible scaling and presolve.
using JSimplex, Serialization, LinearAlgebra, SparseArrays, TOML, SHA
BLAS.set_num_threads(1)
length(ARGS)==3 || error("Expected target capture, pre-flip workspace, output TOML")
data=deserialize(ARGS[1]); ws=deserialize(ARGS[2]); p=data.problem
presolved=JSimplex.presolve_problem(p)
scaled,scaling=JSimplex.scale_problem(presolved.problem)
@assert all(f->isequal(getfield(JSimplex._minimization_problem(scaled),f),getfield(ws.problem,f)),fieldnames(typeof(scaled)))
source=read(joinpath(dirname(dirname(dirname(@__DIR__))),"diagnostics/adaptive-degeneracy/reproduce/probe_small_pivot_original_point.jl"),String)
a=first(findfirst("function point_violations",source)); b=first(findnext("\nreport=",source,a))
include_string(Main,source[a:b-1])
x=ws.primal[1:size(scaled.A,2)]; unscaled=JSimplex.unscale_primal(scaling,x)
report=Dict{String,Any}("target_sha256"=>bytes2hex(open(sha256,ARGS[1])),
    "workspace_sha256"=>bytes2hex(open(sha256,ARGS[2])),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
for (label,problem,point) in (("scaled",scaled,x),("unscaled",presolved.problem,unscaled),("original_before_flips",p,JSimplex.postsolve_primal(presolved,unscaled)),("original_after_flips",p,data.target))
    report[label]=point_violations(problem,point,ws.options.primal_tolerance)
    println(label," ",report[label]["violations_above_tolerance"]," ",report[label]["maximum_violation"]);flush(stdout)
end
names=copy(p.column_names); step_names=Vector{String}[]
for step in presolved.postsolve_stack
    push!(step_names,names)
    map=step isa JSimplex.PresolveMap ? step : step.map
    global names=names[map.columns]
end
original_before=JSimplex.postsolve_primal(presolved,unscaled)
retained_names=Set(names)
eliminated_violations=[p.column_names[j] for j in eachindex(original_before)
    if !(p.column_names[j] in retained_names) &&
       max(JSimplex._lower_violation(p.column_lower[j],original_before[j]),
           JSimplex._upper_violation(p.column_upper[j],original_before[j]))>ws.options.primal_tolerance]
report["eliminated_violations"]=eliminated_violations
selected_names=unique(vcat(["C6569","C6570","C6571"],eliminated_violations))
records=Dict{String,Any}[]
for name in selected_names
    j=findfirst(==(name),names)
    if !isnothing(j)
        push!(records,Dict("name"=>name,"stage"=>"scaled","index"=>j,"value"=>x[j],"factor"=>scaling.column_factors[j],"unscaled_value"=>unscaled[j]))
    end
end
point=unscaled
for k in reverse(eachindex(presolved.postsolve_stack))
    step=presolved.postsolve_stack[k]
    global point=JSimplex.postsolve_primal(step,point)
    for name in selected_names
        j=findfirst(==(name),step_names[k]);isnothing(j)&&continue
        record=Dict{String,Any}("name"=>name,"stage"=>string(typeof(step)),"step"=>k,"index"=>j,"value"=>point[j])
        if hasproperty(step,:records)
            for r in step.records
                r.column==j || continue
                record["coefficient"]=r.coefficient;record["rhs"]=r.rhs
                record["terms"]=[Dict("name"=>step_names[k][c],"coefficient"=>a,"value"=>point[c]) for (c,a) in r.terms]
            end
        end
        push!(records,record)
    end
end
clipped=copy(data.target)
for j in eachindex(clipped)
    isfinite(p.column_lower[j]) && (clipped[j]=max(clipped[j],JSimplex.bound_value(p.column_lower[j])))
    isfinite(p.column_upper[j]) && (clipped[j]=min(clipped[j],JSimplex.bound_value(p.column_upper[j])))
end
report["clipped"]=point_violations(p,clipped,ws.options.primal_tolerance)
println("CLIPPED ",report["clipped"]);flush(stdout)

report["column_trace"]=records
report["steps"]=string.(typeof.(presolved.postsolve_stack))
open(io->TOML.print(io,report),ARGS[3],"w")
println("Traced ",length(selected_names)," columns; eliminated violations: ",eliminated_violations);flush(stdout)
