# Opt-in: julia --project=dev dev/allocations.jl afiro adlittle --output=allocations.toml
module JSimplexAllocations

using JSimplex, Profile, TOML
using JSimplex: MOI
include("datasets.jl")

export measure_allocations, audit_dataset, allocation_main

_timed_call(f, state) = @timed f(state)

"""Measure warmed calls, preparing fresh mutable state outside each measurement."""
function measure_allocations(f; setup=() -> nothing, samples::Int=5)
    samples > 0 || throw(ArgumentError("samples must be positive"))
    _timed_call(f, setup())
    _timed_call(f, setup())
    measurements = map(1:samples) do _
        state = setup()
        GC.gc()
        _timed_call(f, state)
    end
    result = Dict{String,Any}(
        "bytes" => minimum(t.bytes for t in measurements),
        "allocations" => minimum(Base.gc_alloc_count(t.gcstats) for t in measurements),
        "seconds" => minimum(t.time for t in measurements),
        "compile_seconds" => maximum(t.compile_time for t in measurements),
        "samples" => samples,
    )
    value = first(measurements).value
    if value isa JSimplex.Solution
        result["status"] = string(value.status)
        result["iterations"] = value.statistics.iterations
        isnothing(value.objective_value) || (result["objective"] = value.objective_value)
    elseif value isa JSimplex.PresolveFailure
        result["status"] = string(value.status)
    end
    return result
end

function allocation_profile(f, setup; sample_rate=0.01)
    0 < sample_rate <= 1 || throw(ArgumentError("sample rate must be in (0, 1]"))
    f(setup())
    state = setup()
    Profile.Allocs.clear()
    Profile.Allocs.@profile sample_rate=sample_rate f(state)
    totals = Dict{String,Tuple{Int,Int}}()
    source_root = joinpath(dirname(@__DIR__), "src") * "/"
    for allocation in Profile.Allocs.fetch().allocs
        index = findfirst(frame -> startswith(string(frame.file), source_root), allocation.stacktrace)
        site = if isnothing(index)
            "outside JSimplex/src"
        else
            frame = allocation.stacktrace[index]
            "$(relpath(string(frame.file), dirname(@__DIR__))):$(frame.line) $(frame.func)"
        end
        bytes, count = get(totals, site, (0, 0))
        totals[site] = (bytes + allocation.size, count + 1)
    end
    Profile.Allocs.clear()
    return [Dict("site" => site, "sampled_bytes" => bytes, "sampled_allocations" => count)
            for (site, (bytes, count)) in sort!(collect(totals); by=p -> last(p)[1], rev=true)]
end

# Construct a continuous MOI source from the same native LP, outside measurement.
# This avoids attributing another MPS parser's behavior to adapter translation.
function moi_source(problem)
    model = MOI.Utilities.Model{Float64}()
    variables = MOI.add_variables(model, length(problem.objective))
    for (index, variable) in enumerate(variables)
        lower, upper = problem.column_lower[index], problem.column_upper[index]
        isfinite(lower) && MOI.add_constraint(model, variable, MOI.GreaterThan(bound_value(lower)))
        isfinite(upper) && MOI.add_constraint(model, variable, MOI.LessThan(bound_value(upper)))
    end
    for (row, entries) in enumerate(JSimplex._row_entries(problem.A))
        terms = [MOI.ScalarAffineTerm(value, variables[column]) for (column, value) in entries]
        function_ = MOI.ScalarAffineFunction(terms, 0.0)
        lower, upper = problem.row_lower[row], problem.row_upper[row]
        if isfinite(lower) && isfinite(upper)
            MOI.add_constraint(model, function_, MOI.Interval(bound_value(lower), bound_value(upper)))
        elseif isfinite(lower)
            MOI.add_constraint(model, function_, MOI.GreaterThan(bound_value(lower)))
        elseif isfinite(upper)
            MOI.add_constraint(model, function_, MOI.LessThan(bound_value(upper)))
        end
    end
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(value, variables[index]) for (index, value) in enumerate(problem.objective)],
        problem.objective_constant,
    )
    MOI.set(model, MOI.ObjectiveFunction{typeof(objective)}(), objective)
    MOI.set(model, MOI.ObjectiveSense(), problem.objective_sense == MIN_SENSE ? MOI.MIN_SENSE : MOI.MAX_SENSE)
    return model
end

function audit_dataset(path; samples::Int=5, profile::String="", sample_rate=0.01,
                       basis_update::Symbol=:pfi, basis_refactorization::Symbol=:native)
    problem = read_mps(path)
    options = SolverOptions(; verbose=false, iteration_limit=10_000,
                            basis_update, basis_refactorization)
    source = moi_source(JSimplex.relax_integrality(problem))
    optimizer = JSimplex.Optimizer()
    workspace_setup = () -> JSimplex.initialize_workspace(problem, options)
    cases = [
        ("read_mps", _ -> read_mps(path), () -> nothing),
        ("moi_translation", _ -> JSimplex._translate_moi_model(optimizer, source), () -> nothing),
        ("presolve", _ -> JSimplex.presolve_problem(problem), () -> nothing),
        ("scaling", _ -> JSimplex.scale_problem(problem), () -> nothing),
        ("initialize", _ -> workspace_setup(), () -> nothing),
        ("recompute", w -> JSimplex.recompute!(w), workspace_setup),
        ("refactorize", w -> JSimplex.recompute!(w; refactorize=true), workspace_setup),
        ("forward_solve", w -> JSimplex.forward_solve!(w.scratch.row_solution,
            w.factorization, w.scratch.row_rhs), workspace_setup),
        ("transpose_solve", w -> JSimplex.transpose_solve!(w.scratch.row_solution,
            w.factorization, w.scratch.row_rhs), workspace_setup),
    ]
    for pass in (JSimplex._presolve_basic, JSimplex.reduce_singleton_rows,
                 JSimplex.aggregate_singleton_equalities, JSimplex.aggregate_sparse_equalities,
                 JSimplex.reduce_parallel_rows, JSimplex.reduce_dependent_rows,
                 JSimplex.substitute_free_doubleton, JSimplex.propagate_row_bounds,
                 JSimplex.reduce_dual_fixings)
        push!(cases, (string(nameof(pass)), _ -> pass(problem), () -> nothing))
    end
    presolved = JSimplex.presolve_problem(problem)
    if presolved isa JSimplex.PresolveResult
        reduced_solution = solve(presolved.problem; relax_integrality=true,
            options=SolverOptions(; verbose=false, presolve=false, iteration_limit=10_000,
                                   basis_update, basis_refactorization))
        if reduced_solution.status == OPTIMAL
            push!(cases, ("postsolve", _ -> JSimplex.postsolve_primal(presolved, reduced_solution.primal),
                          () -> nothing))
        end
    end
    for algorithm in (:dual, :primal), presolve in (true, false)
        solve_options = SolverOptions(; algorithm, presolve, verbose=false,
            iteration_limit=10_000, basis_update, basis_refactorization)
        label = "solve_$algorithm" * (presolve ? "" : "_no_presolve")
        push!(cases, (label, _ -> solve(problem; relax_integrality=true, options=solve_options),
                      () -> nothing))
    end
    isempty(profile) || any(case -> first(case) == profile, cases) ||
        throw(ArgumentError("unknown or unavailable profile stage: $profile"))
    results = Dict{String,Any}[]
    for (name, f, setup) in cases
        result = measure_allocations(f; setup, samples)
        result["stage"] = name
        if name == profile
            result["sample_rate"] = sample_rate
            result["profile"] = allocation_profile(f, setup; sample_rate)
        end
        push!(results, result)
    end
    return results
end

function allocation_main(args=ARGS; io=stdout)
    names = String[]
    samples, profile, output, sample_rate = 5, "", "", 0.01
    basis_update, basis_refactorization = :pfi, :native
    for arg in args
        if startswith(arg, "--samples=")
            samples = parse(Int, split(arg, '='; limit=2)[2])
        elseif startswith(arg, "--profile=")
            profile = split(arg, '='; limit=2)[2]
        elseif startswith(arg, "--output=")
            output = split(arg, '='; limit=2)[2]
        elseif startswith(arg, "--sample-rate=")
            sample_rate = parse(Float64, split(arg, '='; limit=2)[2])
        elseif startswith(arg, "--basis-update=")
            basis_update = Symbol(split(arg, '='; limit=2)[2])
        elseif startswith(arg, "--basis-refactorization=")
            basis_refactorization = Symbol(split(arg, '='; limit=2)[2])
        elseif startswith(arg, "--")
            throw(ArgumentError("unknown option: $arg"))
        else
            push!(names, arg)
        end
    end
    samples > 0 || throw(ArgumentError("samples must be positive"))
    0 < sample_rate <= 1 || throw(ArgumentError("sample rate must be in (0, 1]"))
    isempty(names) && push!(names, "afiro")
    manifest = load_dataset_manifest(joinpath(@__DIR__, "datasets.toml"))
    report = Dict{String,Any}("julia_version" => string(VERSION), "machine" => Sys.MACHINE,
        "threads" => Threads.nthreads(), "blas_threads" => JSimplex.BLAS.get_num_threads(),
        "basis_update" => string(basis_update), "basis_refactorization" => string(basis_refactorization),
        "datasets" => Dict{String,Any}())
    println(io, "dataset\tstage\tbytes\tallocations\tseconds\tstatus")
    for name in unique(names)
        path = resolve_dataset(manifest, name; repository_root=dirname(@__DIR__))
        results = audit_dataset(path; samples, profile=String(profile), sample_rate,
                                basis_update, basis_refactorization)
        report["datasets"][name] = results
        for row in results
            println(io, join((name, row["stage"], row["bytes"], row["allocations"],
                              row["seconds"], get(row, "status", "")), '\t'))
            if haskey(row, "profile")
                for site in first(row["profile"], min(15, length(row["profile"])))
                    println(io, "# sampled: ", site["sampled_bytes"], " bytes, ",
                            site["sampled_allocations"], " allocations: ", site["site"])
                end
            end
        end
    end
    isempty(output) || open(file -> TOML.print(file, report; sorted=true), output, "w")
    return 0
end

end # module

if abspath(PROGRAM_FILE) == @__FILE__
    exit(JSimplexAllocations.allocation_main())
end
