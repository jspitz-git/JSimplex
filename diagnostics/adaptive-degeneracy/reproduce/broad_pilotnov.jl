# Reconcile an independent feasible point with the presolve rejection. This is
# a tolerance-policy diagnostic, not an exact-rational feasibility proof.
using JSimplex,TOML,LinearAlgebra,SHA,Test
BLAS.set_num_threads(1)
const FAILURES=Dict{String,Any}[]
function capture_failure(problem,row,lo,hi,nlo,nhi)
    l=problem.row_lower[row];u=problem.row_upper[row]
    push!(FAILURES,Dict("row"=>row,"name"=>problem.row_names[row],
        "lower"=>isfinite(l) ? l.value : -Inf,"upper"=>isfinite(u) ? u.value : Inf,
        "minimum"=>nlo==0 ? Float64(lo) : -Inf,"maximum"=>nhi==0 ? Float64(hi) : Inf,
        "lower_gap"=>isfinite(l) && nhi==0 ? Float64(JSimplex._exact_rational(l.value)-hi) : -Inf,
        "upper_gap"=>isfinite(u) && nlo==0 ? Float64(lo-JSimplex._exact_rational(u.value)) : -Inf,
        "current_rows"=>size(problem.A,1),"current_columns"=>size(problem.A,2)))
end
source=read(joinpath(dirname(pathof(JSimplex)),"presolve_propagation.jl"),String)
needle="            return _propagation_failure(problem, row, keep,\n                \"contradicts current column bounds\")"
@assert count(needle,source)==1
source=replace(source,needle=>"            Main.capture_failure(problem,row,min_sum,max_sum,min_unbounded,max_unbounded)\n"*needle)
Base.include_string(JSimplex,source,"diagnostic_presolve_gap.jl")
function main(input,pointfile,output)
    p=JSimplex.read_mps(input);d=TOML.parsefile(pointfile)
    names=Dict(name=>i for (i,name) in enumerate(d["column_names"]))
    @assert length(names)==size(p.A,2)
    x=Float64[d["primal"][names[name]] for name in p.column_names]
    activity=p.A*x
    row_violation=maximum(max(JSimplex._lower_violation(p.row_lower[i],activity[i]),
        JSimplex._upper_violation(p.row_upper[i],activity[i])) for i in eachindex(activity))
    column_violation=maximum(max(JSimplex._lower_violation(p.column_lower[i],x[i]),
        JSimplex._upper_violation(p.column_upper[i],x[i])) for i in eachindex(x))
    feasible=JSimplex._original_primal_feasible(p,x,1e-7)
    reduced=JSimplex.presolve_problem(p)
    @testset "pilotnov tolerance consistency diagnosis" begin
        @test feasible
        @test reduced isa JSimplex.PresolveFailure
        @test reduced.status==JSimplex.INFEASIBLE
    end
    report=Dict("input_sha256"=>bytes2hex(open(sha256,input)),"reference_point_sha256"=>bytes2hex(open(sha256,pointfile)),
        "feasible_at_solver_tolerance"=>feasible,"primal_tolerance"=>1e-7,
        "maximum_row_violation"=>row_violation,"maximum_column_violation"=>column_violation,
        "objective"=>dot(p.objective,x)+p.objective_constant,"presolve_status"=>string(reduced.status),
        "presolve_message"=>reduced.message,"failures"=>FAILURES)
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
end
Base.invokelatest(main,ARGS...)
