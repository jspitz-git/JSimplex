module JSimplexDevSuite

using JSimplex
using Printf
include("datasets.jl")
include("reference_glpk.jl")

export parse_suite_args, select_datasets, suite_main, solve_with_glpk, glpk_status

const USAGE = """
Usage: julia --project=dev dev/run_suite.jl [--dataset NAME] [--tag TAG]
       [--data-root PATH] [--compare-glpk]
Repeat --dataset or --tag to select their union; datasets and tags intersect.
With no selectors, run the quick tag. Names are sorted and deduplicated.
All instances run as LP relaxations. --data-root overrides artifact data only.
"""

function parse_suite_args(args)
    datasets = String[]
    tags = String[]
    data_root = nothing
    compare_glpk = false
    help = false
    index = 1
    while index <= length(args)
        argument = args[index]
        if argument == "--compare-glpk"
            compare_glpk = true
        elseif argument in ("--help", "-h")
            help = true
        else
            parts = split(argument, '='; limit=2)
            option = parts[1]
            option in ("--dataset", "--tag", "--data-root") ||
                throw(ArgumentError("Unknown argument '$argument'; use --help for supported options."))
            if length(parts) == 2
                value = parts[2]
            else
                index += 1
                index <= length(args) || throw(ArgumentError("Missing value for $option; use --help."))
                value = args[index]
            end
            (!isempty(strip(value)) && !startswith(value, "--")) ||
                throw(ArgumentError("Missing value for $option; supply $option VALUE."))
            if option == "--dataset"
                push!(datasets, value)
            elseif option == "--tag"
                push!(tags, value)
            else
                isnothing(data_root) || throw(ArgumentError("Repeated --data-root; supply one data root."))
                data_root = String(value)
            end
        end
        index += 1
    end
    return (; datasets, tags, data_root, compare_glpk, help)
end

function select_datasets(manifest, options)
    datasets = get(manifest, "datasets", Dict())
    for name in options.datasets
        haskey(datasets, name) || throw(ArgumentError("Unknown dataset '$name'; choose --dataset from dev/datasets.toml."))
    end
    tags = isempty(options.datasets) && isempty(options.tags) ? ["quick"] : options.tags
    for tag in tags
        any(tag in get(entry, "tags", []) for entry in values(datasets)) ||
            throw(ArgumentError("Unknown tag '$tag'; choose --tag from dev/datasets.toml."))
    end
    names = isempty(options.datasets) ? collect(keys(datasets)) : unique(options.datasets)
    selected = sort!(filter(name -> isempty(tags) ||
        any(tag in get(datasets[name], "tags", []) for tag in tags), names))
    isempty(selected) && throw(ArgumentError("No datasets match these selectors; change --dataset or --tag."))
    return selected
end

function objective_matches(actual, reference)
    return actual isa Real && reference isa Real && isfinite(actual) &&
           isfinite(reference) && abs(actual - reference) <= max(1e-7, 1e-7 * abs(reference))
end

function check_solution(entry, solution, reference=nothing)
    failures = String[]
    if haskey(entry, "expected_status")
        string(solution.status) == entry["expected_status"] ||
            push!(failures, "expected status $(entry["expected_status"]), got $(solution.status)")
    elseif !(solution.status in (OPTIMAL, INFEASIBLE, UNBOUNDED))
        push!(failures, "solver did not finish: $(solution.status)")
    end
    if haskey(entry, "expected_objective") &&
       !objective_matches(solution.objective_value, entry["expected_objective"])
        push!(failures, "expected objective $(entry["expected_objective"]), got $(solution.objective_value)")
    end
    if !isnothing(reference)
        reference.status == solution.status ||
            push!(failures, "GLPK status $(reference.raw_status) ($(reference.status)) differs from $(solution.status)")
        if reference.status == OPTIMAL && !objective_matches(solution.objective_value, reference.objective)
            push!(failures, "GLPK objective $(reference.objective) differs from $(solution.objective_value)")
        end
    end
    return failures
end

function suite_main(args=ARGS;
                    manifest_path=joinpath(@__DIR__, "datasets.toml"),
                    repository_root=normpath(joinpath(@__DIR__, "..")),
                    io=stdout, err=stderr)
    try
        options = parse_suite_args(args)
        if options.help
            print(io, USAGE)
            return 0
        end
        manifest = load_dataset_manifest(manifest_path)
        names = select_datasets(manifest, options)
        println(io, "instance\tstatus\tobjective\titerations\telapsed_seconds\tresult")
        failed = 0
        for name in names
            try
                path = resolve_dataset(manifest, name; repository_root, data_root=options.data_root)
                problem = read_mps(path)
                solution = solve(problem; relax_integrality=true)
                reference = options.compare_glpk ? solve_with_glpk(path) : nothing
                failures = check_solution(manifest["datasets"][name], solution, reference)
                passed = isempty(failures)
                failed += !passed
                objective = isnothing(solution.objective_value) ? "-" : @sprintf("%.12g", solution.objective_value)
                @printf(io, "%s\t%s\t%s\t%d\t%.6f\t%s\n", name, string(solution.status),
                        objective, solution.statistics.iterations, solution.statistics.elapsed_seconds,
                        passed ? "PASS" : "FAIL")
                for failure in failures
                    println(err, "$name: $failure")
                end
            catch exception
                exception isa InterruptException && rethrow()
                failed += 1
                println(io, "$name\tERROR\t-\t-\t-\tFAIL")
                println(err, "$name: ", sprint(showerror, exception))
            end
        end
        println(io, "Summary: $(length(names) - failed) passed, $failed failed, $(length(names)) total.")
        return failed == 0 ? 0 : 1
    catch exception
        exception isa InterruptException && rethrow()
        println(err, sprint(showerror, exception))
        return 1
    end
end

end # module JSimplexDevSuite

if abspath(PROGRAM_FILE) == @__FILE__
    exit(JSimplexDevSuite.suite_main())
end
