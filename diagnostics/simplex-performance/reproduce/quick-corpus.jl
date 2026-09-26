using JSimplex,Test,Logging,TOML,SHA
entries=TOML.parsefile(joinpath(@__DIR__,"quick-inputs.toml"))["cases"]
records=Dict{String,Any}[]
@testset "External LP relaxations against hash-matched independent references" begin
    for entry in entries
        @test bytes2hex(open(sha256,entry["path"]))==entry["sha256"]
        problem=read_mps(entry["path"])
        for algorithm in (:primal,:dual),strategy in (:legacy,:adaptive)
            options=SolverOptions(;algorithm,simplex_strategy=strategy,time_limit=60.0,verbose=false)
            result=with_logger(NullLogger()) do;solve(problem;options,relax_integrality=true);end
            optimal=result.status==OPTIMAL
            certified=optimal && JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
            matched=optimal && isapprox(result.objective_value,entry["objective"];atol=1e-7,rtol=1e-8)
            @test optimal
            @test certified
            @test matched
            row=Dict{String,Any}("id"=>entry["id"],"original_path"=>entry["original_path"],"input_sha256"=>entry["sha256"],
                "algorithm"=>string(algorithm),"strategy"=>string(strategy),"status"=>string(result.status),
                "original_primal_certified"=>certified,"reference_objective"=>entry["objective"],"objective_matches"=>matched,
                "seconds"=>result.statistics.elapsed_seconds,"iterations"=>result.statistics.iterations)
            optimal && (row["objective"]=result.objective_value)
            push!(records,row);println(row);flush(stdout)
            open(joinpath(@__DIR__,"quick-corpus.toml"),"w") do io;TOML.print(io,Dict("cases"=>records));end
        end
    end
end
