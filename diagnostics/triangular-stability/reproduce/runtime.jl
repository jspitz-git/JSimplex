using JSimplex,LinearAlgebra,SHA,TOML,Logging
function main(manager,output)
    ispath(output) && error("Choose a fresh report path")
    entry=first(TOML.parsefile(joinpath(@__DIR__,"../../basis-selective-preparation/reproduce/external-inputs.toml"))["cases"])
    @assert bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
    warm=read_mps(entry["path"])
    for update in (:forrest_tomlin,:suhl_suhl), algorithm in (:primal,:dual)
        println("HARNESS warm_start ",update," ",algorithm);flush(stdout)
        warm_options=SolverOptions(;algorithm,basis_update=update,
            basis_refactorization=:native,simplex_strategy=:legacy,
            pricing=:steepest_edge,refactorization_interval=80,verbose=false)
        warm_result=with_logger(NullLogger()) do
            Base.invokelatest(solve,warm;options=warm_options,relax_integrality=true)
        end
        @assert warm_result.status==OPTIMAL
        println("HARNESS warm_done ",update," ",algorithm);flush(stdout)
    end
    input="/home/jspitz/mps/runtime.mps"
    digest=bytes2hex(open(sha256,input))
    @assert digest=="d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68"
    println("HARNESS read_start");flush(stdout)
    problem=read_mps(input)
    println("HARNESS read_done");flush(stdout)
    options=SolverOptions(algorithm=:dual,basis_update=Symbol(manager),
        basis_refactorization=:native,refactorization_interval=1600,
        pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,
        time_limit=1800.0,iteration_limit=1_000_000,verbose=false)
    maximum_point=Ref(0.0); completed_pivots=Ref(0)
    observer=(reason,workspace)->begin
        if workspace !== nothing && reason==:pivot_completed
            maximum_point[]=max(maximum_point[],maximum(abs,workspace.primal))
            completed_pivots[]+=1
            if completed_pivots[]%1600==0
                println("PROGRESS pivots=",completed_pivots[]," max_primal=",maximum_point[]);flush(stdout)
            end
        end
        nothing
    end
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    println("HARNESS solve_start diagnosed");flush(stdout)
    measured=@timed Base.invokelatest(JSimplex._solve_diagnosed,problem,diagnostics;
        options,relax_integrality=true)
    result=measured.value
    optimal=result.status==OPTIMAL
    certified=optimal && JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    matched=optimal && isapprox(result.objective_value,51425691.76210454;rtol=1e-8,atol=1e-7)
    report=Dict("status"=>string(result.status),"message"=>result.message,
        "manager"=>manager,"interval"=>1600,"backend"=>"native","algorithm"=>"dual",
        "input_sha256"=>digest,"original_primal_feasible"=>certified,"objective_matches"=>matched,
        "iterations"=>result.statistics.iterations,"seconds"=>measured.time,
        "compile_seconds"=>measured.compile_time,"allocated_bytes"=>measured.bytes,
        "maximum_completed_primal_magnitude"=>maximum_point[],
        "events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),
        "diagnostics_enabled"=>true,"same_process_warmup"=>true,"verbose"=>false,
        "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
    optimal && (report["objective"]=result.objective_value)
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
    @assert optimal && certified && matched
end
Base.invokelatest(main,ARGS...)
