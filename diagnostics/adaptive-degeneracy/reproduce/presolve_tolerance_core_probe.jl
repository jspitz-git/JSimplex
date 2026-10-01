# Separate presolve proof policy from the remaining simplex infeasibility policy.
using JSimplex,Test,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
p=LinearProblem(sparse(reshape([1024.0],1,1)),[0.0];
    row_lower=[1024.25],variable_domains=[JSimplex.BINARY])
tolerance=1/1024
witness=[1+1/4096]
report=Dict{String,Any}("witness"=>witness,"tolerance"=>tolerance,
    "witness_certified"=>JSimplex._original_primal_feasible(p,witness,tolerance),
    "records"=>Dict{String,Any}[])
for algorithm in (:dual,:primal), presolve in (false,true)
    phases=String[]
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
        event in (:phase_one,:phase_primal,:phase_dual,:phase_cleanup) && push!(phases,string(event))
    end)
    options=SolverOptions(;algorithm,presolve,primal_tolerance=tolerance,verbose=false,scaling=:off)
    r=JSimplex._solve_diagnosed(p,diagnostics;relax_integrality=true,options)
    push!(report["records"],Dict("algorithm"=>string(algorithm),"presolve"=>presolve,
        "status"=>string(r.status),"message"=>r.message,"iterations"=>r.statistics.iterations,
        "phases"=>phases,"events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts)))
end
open(only(ARGS),"w") do io;TOML.print(io,report);end
TOML.print(stdout,report)
