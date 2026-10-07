using JSimplex, LinearAlgebra, SHA, TOML
function main(output)
    input="/home/jspitz/mps/runtime.mps"
    @assert bytes2hex(open(sha256,input))=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    p=read_mps(input)
    options=SolverOptions(;algorithm=:dual,basis_update=:huangfu_hall,
        basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
        simplex_strategy=:legacy,partial_pricing=false,time_limit=1800.0,
        iteration_limit=1_000_000,verbose=false)
    timed=@timed solve(p;options,relax_integrality=true)
    r=timed.value
    report=Dict("status"=>string(r.status),"message"=>r.message,"seconds"=>timed.time,
        "compile_seconds"=>timed.compile_time,"iterations"=>r.statistics.iterations,
        "original_primal_feasible"=>r.status==OPTIMAL && JSimplex._original_primal_feasible(p,r.primal,options.primal_tolerance),
        "source_sha256"=>Dict(f=>bytes2hex(open(sha256,joinpath(dirname(pathof(JSimplex)),f))) for f in ("solver.jl","native_certificate_recovery.jl")))
    r.status==OPTIMAL && (report["objective"]=r.objective_value)
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
    println(report)
    @assert r.status==OPTIMAL && report["original_primal_feasible"]
end
Base.invokelatest(main,ARGS...)
