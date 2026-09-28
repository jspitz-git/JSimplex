using JSimplex, LinearAlgebra, Logging, TOML, SHA, Test
Base.include(JSimplex,joinpath(@__DIR__,"direct.jl"))
JSimplex._install_trial_direct!()
function main(manifest,output)
    ispath(output) && error("Choose a fresh output path")
    records=Dict{String,Any}[]
    @testset "Direct LU trial independent LP trajectories" begin
        for entry in TOML.parsefile(manifest)["cases"]
            path=realpath(entry["path"])
            lowercase(basename(path)) in ("big.mps","largo.mps","anymod.mps") && error("Excluded model")
            @test bytes2hex(open(sha256,path))==entry["sha256"]
            problem=read_mps(path)
            # All methods are covered by matrix/history tests. This independent
            # solver trajectory checks the experimental installation and cleanup.
            options=SolverOptions(algorithm=:dual,basis_update=:forrest_tomlin,
                basis_refactorization=:native,simplex_strategy=:legacy,
                pricing=:steepest_edge,refactorization_interval=80,time_limit=180.0,verbose=false)
            result=with_logger(NullLogger()) do
                Base.invokelatest(solve,problem;options,relax_integrality=true)
            end
            @test result.status==OPTIMAL
            @test JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
            @test isapprox(result.objective_value,entry["objective"];rtol=1e-8,atol=1e-7)
            push!(records,Dict("id"=>entry["id"],"status"=>string(result.status),"iterations"=>result.statistics.iterations,
                "objective"=>result.objective_value,"seconds"=>result.statistics.elapsed_seconds,"input_sha256"=>entry["sha256"]))
            println(records[end]);flush(stdout)
            open(output,"w") do io;TOML.print(io,Dict("cases"=>records,"variant"=>"direct","manager"=>"forrest_tomlin"));end
        end
    end
end
Base.invokelatest(main,ARGS...)
