# Opt-in: julia --project=dev dev/iteration_allocations.jl afiro adlittle
module JSimplexIterationAllocations

using JSimplex, Logging, TOML
include("allocations.jl")
using .JSimplexAllocations: measure_allocations

export audit_iterations, iteration_allocation_main

function prepare_workspace(problem, algorithm, basis_update, pricing, pivots)
    options = SolverOptions(; algorithm, basis_update, pricing, presolve=false,
                            scaling=:off, verbose=false, iteration_limit=10_000)
    guard = JSimplex._guard_stop_callback(() -> false)
    artificial_count = 0
    phase = "original_problem"
    terminal = nothing
    workspace = if algorithm == :dual
        w = JSimplex.initialize_workspace(problem, options)
        terminal = JSimplex.make_dual_feasible!(w, guard)
        w
    else
        w, artificial_count, _ = JSimplex._primal_phase_one(problem, options,
            JSimplex.SimplexProgressContext(problem), guard)
        if artificial_count > 0
            phase = "primal_phase_one"
            terminal = JSimplex._primal_optimize!(w, guard, 0.0)
            if terminal.status == OPTIMAL
                n = size(problem.A, 2)
                artificial_sum = sum(@view w.primal[n+1:n+artificial_count])
                if !isfinite(artificial_sum) || artificial_sum > options.primal_tolerance ||
                   !JSimplex._original_optimality_certified(w, w.primal[1:n+artificial_count])
                    terminal = JSimplex.DualTermination(NUMERICAL_ERROR, "phase I did not establish feasibility")
                else
                    for index in n+1:n+artificial_count
                        w.upper[index] = Bound(0.0)
                        w.problem.column_upper[index] = Bound(0.0)
                        w.problem.objective[index] = 0.0
                    end
                    w.problem.objective[1:n] .= problem.objective
                    JSimplex._restore_original_costs!(w)
                    JSimplex.recompute!(w)
                    terminal = nothing
                    phase = "primal_phase_two_with_fixed_artificials"
                end
            end
        end
        w
    end
    initial_iterations = workspace.iterations
    for _ in 1:pivots
        isnothing(terminal) || break
        terminal = algorithm == :dual ? JSimplex.dual_iteration!(workspace, guard) :
            JSimplex._primal_iteration!(workspace, guard, options.dual_tolerance)
    end
    metadata = Dict{String,Any}(
        "algorithm" => string(algorithm), "basis_update" => string(basis_update),
        "pricing" => string(pricing), "requested_steps" => pivots,
        "completed_steps" => workspace.iterations - initial_iterations,
        "iterations" => workspace.iterations, "updates" => length(workspace.factorization.updates),
        "artificial_columns" => artificial_count,
        "phase" => phase,
        "preparation_status" => isnothing(terminal) ? "READY" : string(terminal.status),
    )
    return workspace, metadata, terminal
end

function entering_column!(workspace, entering)
    column = workspace.scratch.row_rhs
    fill!(column, 0.0)
    A = workspace.problem.A
    if entering <= size(A, 2)
        for position in A.colptr[entering]:(A.colptr[entering+1]-1)
            column[A.rowval[position]] = A.nzval[position]
        end
    else
        column[entering-size(A, 2)] = -1.0
    end
    return JSimplex.forward_solve!(workspace.scratch.row_solution, workspace.factorization, column)
end

function audit_snapshot(workspace, metadata, replay; samples=3, profile=false, runnable=true)
    m = size(workspace.problem.A, 1)
    rows = Dict{String,Any}[]
    preparation = Function[]
    function prepare!(action)
        push!(preparation, action)
        action(workspace)
        return nothing
    end
    function record(stage, f; pristine=false)
        # Replay real solver steps: copying a factor drops spare vector capacity
        # and would charge subsequent growth to the measured kernel.
        actions = pristine ? Function[] : copy(preparation)
        stage_setup = () -> begin
            state = replay()
            for action in actions
                action(state)
            end
            state
        end
        result = measure_allocations(f; setup=stage_setup, samples)
        result["stage"] = stage
        if stage == "iteration"
            probe = stage_setup()
            before = probe.iterations
            terminal = f(probe)
            result["completed_steps"] = probe.iterations - before
            result["status"] = isnothing(terminal) ? "CONTINUE" : string(terminal.status)
        end
        if profile && result["allocations"] > 0
            result["profile"] = JSimplexAllocations.allocation_profile(f, stage_setup; sample_rate=1.0)
        end
        push!(rows, result)
        return nothing
    end
    record("basis_matrix", JSimplex.basis_matrix)
    record("recompute", w -> (JSimplex.recompute!(w); nothing))
    record("refactorize", w -> (JSimplex.recompute!(w; refactorize=true); nothing))
    # A nonzero RHS exercises the updated factor rather than its zero-vector path.
    prepare!(w -> fill!(w.scratch.row_rhs, 1.0))
    record("forward_solve", w -> (JSimplex.forward_solve!(w.scratch.row_solution, w.factorization, w.scratch.row_rhs); nothing))
    record("transpose_solve", w -> (JSimplex.transpose_solve!(w.scratch.rho, w.factorization, w.scratch.row_rhs); nothing))
    m == 0 && return merge(metadata, Dict("stages" => rows, "pivot_available" => false))

    algorithm = Symbol(metadata["algorithm"])
    guard = JSimplex._guard_stop_callback(() -> false)
    entering, leaving = 0, 0
    if algorithm == :dual
        record("dual_edge_selection", JSimplex.dual_edge_selection)
        leaving = JSimplex.dual_edge_selection(workspace)
        let selected_row = max(leaving, 1)
            prepare!(w -> begin
                fill!(w.scratch.row_rhs, 0.0)
                w.scratch.row_rhs[selected_row] = 1.0
                JSimplex.transpose_solve!(w.scratch.rho, w.factorization, w.scratch.row_rhs)
            end)
        end
        record("price", w -> JSimplex.price!(w.scratch.tableau_row, w, w.scratch.rho))
        if leaving > 0 && runnable
            index = workspace.basis.basic_indices[leaving]
            below = JSimplex._lower_violation(workspace.lower[index], workspace.primal[index]) > 0
            bound = below ? workspace.lower[index] : workspace.upper[index]
            orientation = below ? -1.0 : 1.0
            violation = abs(workspace.primal[index]-bound_value(bound))
            prepare!(w -> JSimplex.price!(w.scratch.tableau_row, w, w.scratch.rho))
            record("dual_ratio", w -> JSimplex.dual_ratio_test(w, w.scratch.tableau_row, orientation))
            record("bound_flipping_ratio", w -> JSimplex._bound_flipping_ratio_test(w, w.scratch.tableau_row, orientation, violation))
            entering, _, _ = JSimplex._bound_flipping_ratio_test(workspace, workspace.scratch.tableau_row, orientation, violation)
            # Include pricing/cache initialization exactly as the next real step sees it.
            record("iteration", w -> JSimplex.dual_iteration!(w, guard); pristine=true)
        end
    else
        record("primal_pricing_before_probe", w -> JSimplex._primal_entering(w, w.options.dual_tolerance))
        prepare!(w -> JSimplex._primal_entering(w, w.options.dual_tolerance))
        entering, direction = JSimplex._primal_entering(workspace, workspace.options.dual_tolerance)
        record("primal_pricing", w -> JSimplex._primal_entering(w, w.options.dual_tolerance))
        if entering > 0 && runnable
            let entering = entering
                prepare!(w -> entering_column!(w, entering))
            end
            let entering = entering, direction = direction
                record("primal_ratio", w -> JSimplex._primal_ratio(w, entering, direction, w.scratch.row_solution))
            end
            _, leaving, _ = JSimplex._primal_ratio(workspace, entering, direction, workspace.scratch.row_solution)
            record("iteration", w -> JSimplex._primal_iteration!(w, guard, w.options.dual_tolerance); pristine=true)
        end
    end
    available = runnable && entering > 0 && leaving > 0
    if available
        let entering = entering
            prepare!(w -> entering_column!(w, entering))
        end
        available = abs(workspace.scratch.row_solution[leaving]) > workspace.options.zero_tolerance
        if available
            let leaving = leaving
                record("replace_column", w -> (JSimplex.replace_column!(w.factorization, w.scratch.row_solution, leaving;
                    zero_tolerance=w.options.zero_tolerance); nothing))
            end
        end
    end
    return merge(metadata, Dict("stages" => rows, "pivot_available" => available))
end

"""Measure Float64 iteration kernels without presolve, parsing, or state setup."""
function audit_iterations(problem::LinearProblem{Float64}; samples=3, steps=(0,5),
                          methods=(:pfi,), pricings=(:steepest_edge,), profile=false)
    samples > 0 || throw(ArgumentError("samples must be positive"))
    all(>=(0), steps) || throw(ArgumentError("steps must be nonnegative"))
    return with_logger(NullLogger()) do
        results = Dict{String,Any}[]
        for method in methods, pricing in pricings, algorithm in (:dual,:primal), count in steps
            workspace, metadata, terminal = prepare_workspace(problem, algorithm, method, pricing, count)
            if !isnothing(terminal) && terminal.status != OPTIMAL
                push!(results, merge(metadata, Dict("stages" => Dict{String,Any}[], "pivot_available" => false)))
                continue
            end
            replay = () -> first(prepare_workspace(problem, algorithm, method, pricing, count))
            push!(results, audit_snapshot(workspace, metadata, replay; samples, profile, runnable=isnothing(terminal)))
        end
        results
    end
end

function iteration_allocation_main(args=ARGS; io=stdout)
    names = String[]; samples = 3; pivots = 5; profile = false
    methods = (:pfi,); pricings = (:steepest_edge,); output = "iteration-allocations.toml"
    for arg in args
        if startswith(arg, "--samples=")
            samples = parse(Int, split(arg,'=';limit=2)[2])
        elseif startswith(arg, "--steps=")
            pivots = parse(Int, split(arg,'=';limit=2)[2])
        elseif startswith(arg, "--output=")
            output = split(arg,'=';limit=2)[2]
        elseif startswith(arg, "--basis-update=")
            value = split(arg,'=';limit=2)[2]
            methods = value == "all" ? (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub) : (Symbol(value),)
        elseif startswith(arg, "--pricing=")
            value = split(arg,'=';limit=2)[2]
            pricings = value == "all" ? (:dantzig,:devex,:steepest_edge) : (Symbol(value),)
        elseif arg == "--profile"
            profile = true
        elseif startswith(arg, "--")
            throw(ArgumentError("unknown option: $arg"))
        else
            push!(names, arg)
        end
    end
    samples > 0 || throw(ArgumentError("samples must be positive"))
    pivots >= 0 || throw(ArgumentError("steps must be nonnegative"))
    isempty(names) && push!(names, "afiro")
    manifest = JSimplexAllocations.load_dataset_manifest(joinpath(@__DIR__, "datasets.toml"))
    datasets = Dict{String,Any}()
    for name in unique(names)
        path = JSimplexAllocations.resolve_dataset(manifest, name; repository_root=dirname(@__DIR__))
        datasets[name] = audit_iterations(read_mps(path); samples, steps=unique((0,pivots)), methods, pricings, profile)
        println(io, name, ": ", length(datasets[name]), " iteration snapshots measured")
        flush(io)
    end
    report = Dict("julia_version"=>string(VERSION), "machine"=>Sys.MACHINE,
        "threads"=>Threads.nthreads(), "presolve"=>false, "scaling"=>"off",
        "basis_refactorization"=>"native", "state_setup"=>"deterministic_replay_outside_measurement", "datasets"=>datasets)
    open(file -> TOML.print(file, report; sorted=true), output, "w")
    return 0
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(JSimplexIterationAllocations.iteration_allocation_main())
end
