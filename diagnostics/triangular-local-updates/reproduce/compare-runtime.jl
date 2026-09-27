using JSimplex, Logging, SHA, TOML
module Reference
include(joinpath(ENV["JSIMPLEX_BASELINE_SOURCE"], "JSimplex.jl"))
end

function run_case(mod, input, output, label)
    warm = Ref(true)
    started = Ref(UInt64(0))
    samples = Dict{String,Any}[]
    observer = function(reason, ws)
        warm[] && return
        milestone = reason == :pivot_completed && ws.iterations % 5000 == 0
        phase = reason in (:phase_dual, :phase_primal, :phase_cleanup, :phase_one)
        (milestone || phase) || return
        row = Dict{String,Any}("event" => string(reason),
            "wall_seconds" => (time_ns() - started[]) / 1e9)
        if !isnothing(ws) && hasproperty(ws, :iterations)
            row["iteration"] = ws.iterations
            row["refactorizations"] = ws.refactorizations
        end
        push!(samples, row)
        println(label, " ", row); flush(stdout)
    end
    options = mod.SolverOptions(algorithm=:dual, simplex_strategy=:legacy,
        basis_update=:bartels_golub, basis_refactorization=:native,
        pricing=:steepest_edge, refactorization_interval=80,
        iteration_limit=1_000_000, time_limit=1500.0, verbose=false)
    fixture = joinpath(dirname(dirname(pathof(JSimplex))), "test/fixtures/solver/afiro.mps")
    with_logger(NullLogger()) do
        mod._solve_diagnosed(mod.read_mps(fixture),
            mod.SimplexDiagnostics(;observer, kernel_timing=true); options)
    end
    problem = mod.read_mps(input)
    d = mod.SimplexDiagnostics(;observer, kernel_timing=true)
    GC.gc()
    warm[] = false
    started[] = time_ns()
    result = with_logger(NullLogger()) do
        mod._solve_diagnosed(problem, d; options, relax_integrality=true)
    end
    wall = (time_ns() - started[]) / 1e9
    certified = result.status == mod.OPTIMAL &&
        mod._original_primal_feasible(problem, result.primal, options.primal_tolerance)
    report = Dict{String,Any}("implementation" => label, "baseline_revision" => "e1b1567",
        "input_sha256" => bytes2hex(open(sha256, input)), "julia" => string(VERSION),
        "status" => string(result.status), "iterations" => result.statistics.iterations,
        "refactorizations" => result.statistics.refactorizations,
        "seconds" => result.statistics.elapsed_seconds, "wall_seconds" => wall,
        "original_primal_certified" => certified, "samples" => samples,
        "counts" => Dict(string(k) => v for (k,v) in d.counts if v != 0),
        "kernel_seconds" => Dict(string(k) => v / 1e9 for (k,v) in d.kernel_nanoseconds if v != 0))
    isnothing(result.objective_value) || (report["objective"] = result.objective_value)
    open(output, "w") do io; TOML.print(io, report); end
    println(label, " FINAL ", result.status, " iterations=", result.statistics.iterations,
        " seconds=", result.statistics.elapsed_seconds, " certified=", certified); flush(stdout)
    @assert certified
    return report
end

function main()
    input, output = ARGS
    lowercase(basename(realpath(input))) in ("big.mps", "largo.mps", "anymod.mps") &&
        error("Excluded large model")
    mkpath(output)
    before = run_case(Reference.JSimplex, input, joinpath(output, "runtime-before.toml"), "baseline")
    after = run_case(JSimplex, input, joinpath(output, "runtime-after.toml"), "current")
    @assert before["objective"] == after["objective"]
    @assert before["iterations"] == after["iterations"]
    @assert before["refactorizations"] == after["refactorizations"]
    @assert before["counts"] == after["counts"]
end
main()
