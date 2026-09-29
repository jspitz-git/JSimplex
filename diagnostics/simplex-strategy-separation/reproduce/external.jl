using JSimplex, Test, TOML, SHA, Logging, LinearAlgebra
length(ARGS) == 1 || error("Expected a fresh output TOML path")
output = only(ARGS)
ispath(output) && error("Output already exists")
manifest = TOML.parsefile("diagnostics/basis-selective-preparation/reproduce/external-inputs.toml")
report = Dict{String,Any}("julia"=>string(VERSION), "architecture"=>string(Sys.ARCH),
    "julia_threads"=>Threads.nthreads(), "blas_threads"=>BLAS.get_num_threads(),
    "cases"=>Dict{String,Any}[],
    "source_sha256"=>Dict(name=>bytes2hex(open(sha256,joinpath("src",name)))
        for name in ("simplex_numerics.jl","simplex_driver.jl","primal_simplex.jl","dual_simplex.jl")))
@testset "External reference optima with separated strategies" begin
    for entry in manifest["cases"]
        entry["id"] == "miplib/pk1" && continue
        @test bytes2hex(open(sha256,entry["path"])) == entry["sha256"]
        p = read_mps(entry["path"])
        strategies = entry["id"] == "mps/fast0507" ? (:legacy,) : (:legacy,:adaptive)
        for algorithm in (:primal,:dual), strategy in strategies,
            manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
            options = SolverOptions(;algorithm,simplex_strategy=strategy,basis_update=manager,
                basis_refactorization=:native,pricing=:steepest_edge,
                refactorization_interval=80,iteration_limit=10000,time_limit=60.0,verbose=false)
            result = with_logger(NullLogger()) do
                solve(p;options,relax_integrality=true)
            end
            case = Dict{String,Any}("id"=>entry["id"],"input_sha256"=>entry["sha256"],
                "algorithm"=>string(algorithm),"strategy"=>string(strategy),"manager"=>string(manager),
                "status"=>string(result.status),"iterations"=>result.statistics.iterations,
                "seconds"=>result.statistics.elapsed_seconds)
            @test result.status == OPTIMAL
            if result.status == OPTIMAL
                case["objective"] = result.objective_value
                case["reference_objective"] = entry["objective"]
                case["original_primal_certified"] = JSimplex._original_primal_feasible(p,result.primal,options.primal_tolerance)
                @test case["original_primal_certified"]
                @test isapprox(result.objective_value,entry["objective"];rtol=1e-8,atol=1e-7)
            end
            push!(report["cases"],case)
            open(output,"w") do io
                TOML.print(io,report)
            end
            println(entry["id"]," ",algorithm," ",strategy," ",manager," ",result.status);flush(stdout)
        end
    end
end
