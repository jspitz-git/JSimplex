# Run in a fresh Julia process, in the environment used by the failing solve:
# julia --project=. capture.jl C:/disk_d/tmp/runtime.mps C:/disk_d/tmp/runtime-capture
# This diagnostic stops at postsolve; it does not return a solver solution.
module RuntimePrimalCapture
using JSimplex, Serialization, LinearAlgebra, SHA, TOML, Pkg
const JS = JSimplex
const output_prefix = Ref("")
struct Captured <: Exception end

function write_report(path, report)
    open(path, "w") do io
        TOML.print(io, report; sorted=true)
    end
end

function environment(input)
    root = dirname(dirname(pathof(JS)))
    revision = if ispath(joinpath(root, ".git"))
        try strip(read(`git -C $root rev-parse HEAD`, String)) catch; "unavailable" end
    else
        "unavailable"
    end
    dependencies = Pkg.dependencies()
    package = get(dependencies, Base.PkgId(JS).uuid, nothing)
    return Dict(
        "julia" => string(VERSION), "architecture" => string(Sys.ARCH),
        "kernel" => string(Sys.KERNEL), "julia_threads" => Threads.nthreads(),
        "cpu" => Sys.CPU_NAME, "opt_level" => Int(Base.JLOptions().opt_level),
        "debug_level" => Int(Base.JLOptions().debug_level),
        "blas_threads" => BLAS.get_num_threads(), "blas" => sprint(show, BLAS.get_config()),
        "source_path" => pathof(JS), "revision" => revision,
        "package_version" => string(Base.pkgversion(JS)),
        "package_tree_hash" => isnothing(package) ? "unavailable" : string(package.tree_hash),
        "dependency_versions" => Dict(dep.name => string(dep.version)
            for dep in values(dependencies) if dep.name in
                ("SuiteSparse_jll", "OpenBLAS_jll", "libblastrampoline_jll", "MKL_jll")),
        "project" => something(Base.active_project(), "unavailable"),
        "input_sha256" => bytes2hex(open(sha256, input)),
        "source_sha256" => Dict(f => bytes2hex(open(sha256, joinpath(root, "src", f)))
            for f in readdir(joinpath(root, "src")) if endswith(f, ".jl")),
    )
end

function inspect(handoff, prefix)
    d = handoff
    ws = JS.initialize_workspace(JS._minimization_problem(d.problem), d.options)
    ws.iterations, ws.refactorizations = d.iterations, d.refactorizations
    ws.basis = JS.Basis(d.basis.basic_indices, d.basis.states)
    JS.recompute!(ws; refactorize=true)
    report = Dict{String,Any}(
        "iterations" => d.iterations,
        "restored_infeasibility" => JS.primal_infeasibility(ws),
        "target_feasible" => JS._original_primal_feasible(d.problem,
            d.target_primal, d.options.primal_tolerance),
    )
    result = @timed JS._project_postsolve_basis!(ws, d.target_primal, () -> false)
    report["projection_accepted"] = !isnothing(result.value)
    report["exchanges"] = something(result.value, -1)
    report["projection_seconds"] = result.time
    report["projection_compile_seconds"] = result.compile_time
    report["projection_bytes"] = result.bytes
    report["projected_infeasibility"] = JS.primal_infeasibility(ws)
    n = size(d.problem.A, 2)
    report["projected_original_feasible"] = JS._original_primal_feasible(
        d.problem, ws.primal[1:n], d.options.primal_tolerance)
    target_activities = d.problem.A * d.target_primal
    violations = Dict{String,Any}[]
    for j in eachindex(ws.primal)
        violation = max(JS._lower_violation(ws.lower[j], ws.primal[j]),
                        JS._upper_violation(ws.upper[j], ws.primal[j]))
        violation > d.options.primal_tolerance || continue
        names, slot = j <= n ? (d.problem.column_names, j) : (d.problem.row_names, j-n)
        push!(violations, Dict("index" => j, "value" => ws.primal[j],
            "violation" => violation, "state" => string(ws.basis.states[j]),
            "name" => isempty(names) ? string(slot) : names[slot],
            "lower" => string(ws.lower[j]), "upper" => string(ws.upper[j]),
            "target" => j <= n ? d.target_primal[j] : target_activities[j-n]))
    end
    report["violations"] = violations
    serialize(prefix * ".projection.bin", (;basis=ws.basis, primal=ws.primal,
        prices=ws.reduced_costs, dual=ws.scratch.rho))
    write_report(prefix * ".projection.toml", report)
    println("Projection accepted: ", report["projection_accepted"],
        "; infeasibility: ", report["projected_infeasibility"])
    return report
end

function capture(problem, basis, options, iterations, refactorizations, target_primal)
    d = (;problem, basis, options, iterations, refactorizations, target_primal)
    prefix = output_prefix[]
    # Save the input first, even if projection inspection itself fails.
    serialize(prefix * ".handoff.bin", d)
    println("Saved postsolve input: ", prefix * ".handoff.bin")
    flush(stdout)
    inspect(d, prefix)
    throw(Captured())
end

function main(input, prefix)
    output_prefix[] = abspath(prefix)
    for suffix in (".environment.toml", ".handoff.bin", ".projection.bin", ".projection.toml")
        ispath(output_prefix[] * suffix) && error("Use a fresh output prefix: " * prefix)
    end
    mkpath(dirname(output_prefix[]))
    write_report(output_prefix[] * ".environment.toml", environment(input))
    # Diagnostic-only interception. The ordinary reduced solve is unchanged;
    # the process ends after inspecting the first original-model handoff.
    @eval JS function cleanup_original(problem::LinearProblem{T}, basis::Basis,
            options::SolverOptions{T}, context::SolveContext,
            iterations::Int, refactorizations::Int;
            target_primal::Union{Nothing,Vector{T}}=nothing) where T
        return Main.RuntimePrimalCapture.capture(problem, basis, options,
            iterations, refactorizations, target_primal)
    end
    problem = read_mps(input; format=:free)
    options = SolverOptions(iteration_limit=1_000_000, time_limit=36000.0,
        basis_update=:huangfu_hall, basis_refactorization=:native,
        pricing=:steepest_edge, algorithm=:primal, refactorization_interval=240)
    try
        solution = Base.invokelatest(solve, problem; options, relax_integrality=true)
        error("Solve ended before the expected handoff: $(solution.status): $(solution.message)")
    catch exception
        exception isa Captured || rethrow()
    end
    println("Capture complete; no final optimization result was requested.")
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    length(ARGS) == 2 || error("Expected: input.mps output_prefix")
    RuntimePrimalCapture.main(ARGS...)
end
