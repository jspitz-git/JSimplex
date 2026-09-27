using JSimplex,Logging,TOML,SHA,LinearAlgebra
function main()
    path,seconds,output=ARGS[1:3]
    methods=Symbol.(split(get(ARGS,4,"bartels_golub,pfi,forrest_tomlin,suhl_suhl"),','))
    intervals=parse.(Int,split(get(ARGS,5,"20,80,320"),','))
    lowercase(basename(realpath(path))) in ("big.mps","largo.mps","anymod.mps") && error("Excluded large model")
    problem=read_mps(path)
    digest=bytes2hex(open(sha256,path))
    fixture=read_mps(joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps"))
    reports=Dict{String,Any}[]
    last_workspace=Ref{Any}(nothing);phase=Ref(:none)
    observer=function(reason,ws)
        last_workspace[]=ws
        reason in (:phase_one,:phase_primal,:phase_dual,:phase_auxiliary,:phase_cleanup) && (phase[]=reason)
        return nothing
    end
    for method in methods
        warm=SolverOptions(algorithm=:dual,basis_update=method,pricing=:steepest_edge,
            simplex_strategy=:legacy,verbose=false)
        with_logger(NullLogger()) do
            JSimplex._solve_diagnosed(fixture,JSimplex.SimplexDiagnostics(;kernel_timing=true,observer);options=warm)
        end
        for interval in intervals
            println("START method=",method," interval=",interval);flush(stdout)
            options=SolverOptions(algorithm=:dual,basis_update=method,pricing=:steepest_edge,
                simplex_strategy=:legacy,basis_refactorization=:native,refactorization_interval=interval,
                time_limit=parse(Float64,seconds),iteration_limit=1_000_000,verbose=false)
            last_workspace[]=nothing;phase[]=:none
            d=JSimplex.SimplexDiagnostics(;kernel_timing=true,observer)
            measured=@timed with_logger(NullLogger()) do
                JSimplex._solve_diagnosed(problem,d;options,relax_integrality=true)
            end
            result=measured.value
            row=Dict{String,Any}("method"=>string(method),"interval"=>interval,
                "status"=>string(result.status),"message"=>result.message,
                "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
                "seconds"=>result.statistics.elapsed_seconds,"outer_seconds"=>measured.time,
                "allocated_bytes"=>measured.bytes,"process_peak_rss"=>Sys.maxrss(),
                "kernel_seconds"=>Dict(string(k)=>v/1e9 for (k,v) in d.kernel_nanoseconds if v!=0),
                "counts"=>Dict(string(k)=>v for (k,v) in d.counts if v!=0))
            if !isnothing(last_workspace[])
                ws=last_workspace[]
                row["working_phase"]=string(phase[])
                row["working_rows"],row["working_columns"]=size(ws.problem.A)
                row["working_iterations"]=ws.iterations
                row["working_cost_objective"]=dot(ws.costs,ws.primal)
                row["working_primal_infeasibility"]=JSimplex.primal_infeasibility(ws)
                row["working_dual_infeasibility"]=JSimplex.dual_infeasibility(ws)
            end
            if result.status==OPTIMAL
                row["objective"]=result.objective_value
                row["original_primal_certified"]=JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
            end
            push!(reports,row);println(row);flush(stdout)
            open(output,"w") do io
                TOML.print(io,Dict("input"=>realpath(path),"input_sha256"=>digest,
                    "julia"=>string(VERSION),"requested_seconds"=>parse(Float64,seconds),"runs"=>reports))
            end
            last_workspace[]=nothing;ws=nothing
            GC.gc()
        end
    end
end
main()
