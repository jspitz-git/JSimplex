using JSimplex, Test, Logging, TOML, SHA, LinearAlgebra

function main(manifest, output)
    ispath(output) && error("Choose a fresh output path")
    entries = TOML.parsefile(manifest)["cases"]
    records = Dict{String,Any}[]
    source_hashes = Dict(name => bytes2hex(open(sha256,
        joinpath(dirname(pathof(JSimplex)), name)))
        for name in ("triangular_factorization.jl", "markowitz_factorization.jl"))
    @testset "External LP relaxations: native and Markowitz basis managers" begin
        for entry in entries
            path = realpath(entry["path"])
            lowercase(basename(path)) in ("big.mps", "largo.mps", "anymod.mps") &&
                error("Excluded large model")
            @test bytes2hex(open(sha256, path)) == entry["sha256"]
            problem = read_mps(path)
            for backend in (:native,), algorithm in (:primal, :dual),
                update in (:forrest_tomlin, :suhl_suhl, :bartels_golub, :pfi)
                options = SolverOptions(; algorithm, basis_update=update,
                    basis_refactorization=backend, simplex_strategy=:legacy,
                    pricing=:steepest_edge, refactorization_interval=80,
                    time_limit=180.0, verbose=false)
                result = with_logger(NullLogger()) do
                    Base.invokelatest(solve, problem; options, relax_integrality=true)
                end
                optimal = result.status == OPTIMAL
                certified = optimal && JSimplex._original_primal_feasible(
                    problem, result.primal, options.primal_tolerance)
                matched = optimal && isapprox(result.objective_value,
                    entry["objective"]; atol=1e-7, rtol=1e-8)
                @test optimal
                @test certified
                @test matched
                row = Dict{String,Any}("id"=>entry["id"],
                    "input_sha256"=>entry["sha256"], "algorithm"=>string(algorithm),
                    "basis_update"=>string(update), "backend"=>string(backend),
                    "status"=>string(result.status), "original_primal_certified"=>certified,
                    "reference_objective"=>entry["objective"], "objective_matches"=>matched,
                    "seconds"=>result.statistics.elapsed_seconds,
                    "iterations"=>result.statistics.iterations)
                optimal && (row["objective"] = result.objective_value)
                push!(records, row)
                println(row); flush(stdout)
                open(output, "w") do io
                    TOML.print(io, Dict("cases"=>records, "source_sha256"=>source_hashes,
                        "julia"=>string(VERSION), "architecture"=>string(Sys.ARCH),
                        "julia_threads"=>Threads.nthreads(), "blas_threads"=>BLAS.get_num_threads()))
                end
            end
        end
    end
end

length(ARGS) == 2 || error("Expected: prepared_manifest output.toml")
Base.invokelatest(main, ARGS...)
