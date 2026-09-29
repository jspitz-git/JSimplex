# Run sequentially through the guarded Julia wrapper documented in the report.
include("../../dual-medium-transition/reproduce/inspect-and-continue.jl")

function check_model(path, manager, pricing, seconds, limit)
    options = SolverOptions(;algorithm=:dual, simplex_strategy=:legacy, pricing,
        basis_update=manager, basis_refactorization=:native,
        refactorization_interval=80, iteration_limit=limit, time_limit=seconds,
        verbose=false)
    problem = read_mps(path)
    records = Dict{String,Any}[]
    last = Ref{Any}(nothing)
    pricing_seen = Set{String}()
    max_interval = Ref(0)
    observer = function(event, ws)
        if event in (:pricing, :pivot_completed)
            last[] = ws
            push!(pricing_seen, string(J._effective_pricing(ws, :dual)))
            max_interval[] = max(max_interval[], ws.dual_refactorization_interval)
            if event == :pivot_completed && ws.iterations % 1000 == 0
                ps, pc = J.primal_infeasibility_summary(ws)
                ds, dc = J.dual_infeasibility_summary(ws)
                push!(records, Dict("iteration"=>ws.iterations,
                    "original_bounds"=>J._original_bounds_active(ws),
                    "pricing"=>string(J._effective_pricing(ws, :dual)),
                    "primal_sum"=>ps, "primal_count"=>pc,
                    "dual_sum"=>ds, "dual_count"=>dc))
            end
        end
    end
    diagnostics = J.SimplexDiagnostics(;observer)
    result = with_logger(NullLogger()) do
        J._solve_diagnosed(problem, diagnostics; options, relax_integrality=true)
    end
    report = Dict{String,Any}("input"=>path,
        "sha256"=>bytes2hex(open(sha256, path)), "manager"=>string(manager),
        "pricing_requested"=>string(pricing), "pricing_seen"=>sort!(collect(pricing_seen)),
        "status"=>string(result.status), "iterations"=>result.statistics.iterations,
        "seconds"=>result.statistics.elapsed_seconds, "time_limit"=>seconds,
        "iteration_limit"=>limit, "maximum_effective_interval"=>max_interval[],
        "records"=>records,
        "events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v != 0))
    if result.status == OPTIMAL
        report["objective"] = result.objective_value
        report["original_primal_certified"] = J._original_primal_feasible(
            problem, result.primal, options.primal_tolerance)
        @assert report["original_primal_certified"]
    end
    if !isnothing(last[])
        ws = last[]
        saved = (original_objective=ws.progress.objective,
            original_objective_constant=ws.progress.objective_constant,
            scaling=ws.progress.scaling)
        report["last_observed_point"] = point_metrics(ws, saved)
    end
    @assert max_interval[] <= 80
    @assert pricing == :dantzig || !("dantzig" in pricing_seen)
    println("MODEL ", basename(path), " ", manager, " ", pricing, " ", result.status,
        " iterations=", result.statistics.iterations); flush(stdout)
    return report
end

function main(mode, output)
    ispath(output) && error("Choose a fresh output file")
    mode in ("pk1", "medium", "external") || error("Expected pk1, medium, or external")
    report = Dict{String,Any}("julia"=>string(VERSION), "architecture"=>string(Sys.ARCH),
        "julia_threads"=>Threads.nthreads(), "blas_threads"=>BLAS.get_num_threads(),
        "source_sha256"=>bytes2hex(open(sha256, joinpath(dirname(pathof(J)), "dual_simplex.jl"))),
        "cases"=>Dict{String,Any}[])
    with_logger(NullLogger()) do
        solve(read_mps("test/fixtures/solver/afiro.mps");
            options=SolverOptions(algorithm=:dual, verbose=false))
    end
    cases = if mode == "medium"
        path = "/home/jspitz/mps/medium.mps"
        @assert bytes2hex(open(sha256, path)) ==
            "79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0"
        [(path, :pfi, :steepest_edge, 300.0, 1_000_000)]
    elseif mode == "pk1"
        [("test/fixtures/solver/miplib/pk1.mps", update, pricing, 30.0, 2000)
         for update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
         for pricing in (:steepest_edge, :dantzig)]
    else
        manifest = TOML.parsefile("diagnostics/basis-selective-preparation/reproduce/external-inputs.toml")
        entries = filter(e -> e["id"] != "miplib/pk1", manifest["cases"])
        for entry in entries
            @assert bytes2hex(open(sha256, entry["path"])) == entry["sha256"]
        end
        [(entry["path"], update, :steepest_edge, 60.0, 10000)
         for entry in entries
         for update in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)]
    end
    for (path, update, pricing, seconds, limit) in cases
        result = check_model(path, update, pricing, seconds, limit)
        push!(report["cases"], result)
        report["peak_rss"] = Sys.maxrss()
        open(output, "w") do io
            TOML.print(io, report)
        end
    end
end

length(ARGS) == 2 || error("Expected: pk1|medium|external output.toml")
main(ARGS...)
