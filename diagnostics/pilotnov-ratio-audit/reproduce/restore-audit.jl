using JSimplex, Serialization, TOML
function audit(input,output)
 d=deserialize(input)
 p=d.continuous_problem
 activities=p.A*d.primal
 violations=Float64[]
 rows=Dict{String,Any}[]
 for i in eachindex(activities)
  violation=max(isfinite(p.row_lower[i]) ? JSimplex.bound_value(p.row_lower[i])-activities[i] : 0.0,
                isfinite(p.row_upper[i]) ? activities[i]-JSimplex.bound_value(p.row_upper[i]) : 0.0,0.0)
  push!(violations,violation)
  violation > d.typed_options.primal_tolerance && push!(rows,Dict("row"=>i,"activity"=>activities[i],"violation"=>violation))
 end
 columns=Dict{String,Any}[]
 for i in eachindex(d.primal)
  violation=max(isfinite(p.column_lower[i]) ? JSimplex.bound_value(p.column_lower[i])-d.primal[i] : 0.0,
                isfinite(p.column_upper[i]) ? d.primal[i]-JSimplex.bound_value(p.column_upper[i]) : 0.0,0.0)
  violation > d.typed_options.primal_tolerance && push!(columns,Dict("column"=>i,"value"=>d.primal[i],"violation"=>violation,"scaling_factor"=>d.scaling.column_factors[i]))
 end
 report=Dict("reduced"=>d.reduced,"retried_original"=>d.retried_original,
  "working_status"=>string(d.run.status),"tolerance"=>d.typed_options.primal_tolerance,
  "original_feasible"=>JSimplex._original_primal_feasible(p,d.primal,d.typed_options.primal_tolerance),
  "rows"=>rows,"columns"=>columns,"maximum_simple_row_violation"=>maximum(violations;init=0.0))
 open(output,"w") do io;TOML.print(io,report;sorted=true);end
 println(report)
end
Base.invokelatest(audit,ARGS...)
