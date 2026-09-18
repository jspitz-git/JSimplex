using JSimplex, LinearAlgebra

# Compare cleanup from the same saved Windows reduced optimum with and without
# projection. In PowerShell, run from this worktree:
#   $env:JSIMPLEX_DIAG_BLAS_THREADS = "6"
#   $env:JSIMPLEX_DIAG_TIME_LIMIT = "900"
#   julia --project=. .\diagnostics\runtime_projection_continuation.jl `
#       "C:\path\to\runtime.mps" 2>&1 | Tee-Object .\diagnostics\runtime_projection_windows.log
# Per-run settings: JSIMPLEX_DIAG_BLAS_THREADS (default 1) and
# JSIMPLEX_DIAG_TIME_LIMIT (default 600 seconds). Each variant gets its own
# limit; "iterations_saved" is reported only if both variants finish OPTIMAL.
const J = JSimplex

function main()
    length(ARGS) == 1 || error("pass the path to runtime.mps")
    isdefined(J, :_project_postsolve_basis!) ||
        error("this JSimplex version does not contain postsolve basis projection")
    blas_threads = parse(Int, get(ENV, "JSIMPLEX_DIAG_BLAS_THREADS", "1"))
    blas_threads > 0 || error("JSIMPLEX_DIAG_BLAS_THREADS must be positive")
    BLAS.set_num_threads(blas_threads)
    cap_seconds = parse(Float64, get(ENV, "JSIMPLEX_DIAG_TIME_LIMIT", "600"))
    isfinite(cap_seconds) && cap_seconds > 0 ||
        error("JSIMPLEX_DIAG_TIME_LIMIT must be finite and positive")
    println("Julia=", VERSION, " kernel=", Sys.KERNEL,
        " threads=", Threads.nthreads(), " BLAS_threads=", BLAS.get_num_threads(),
        " JSimplex_path=", pathof(J), " per_run_time_limit=", cap_seconds, "s")
    println("Timing includes Julia compilation in the first variant; compare iterations primarily.")

    original = J.relax_integrality(read_mps(only(ARGS)))
    presolved = J.presolve_problem(original)
    presolved isa J.PresolveResult || error("presolve did not return a reduced LP")
    scaled, scaling = J.scale_problem(presolved.problem)
    rows, columns = size(scaled.A)
    basic = zeros(Int, rows)
    states = Vector{J.VariableState}(undef, rows + columns)
    values = zeros(Float64, rows + columns)
    seen = falses(rows + columns)
    open(joinpath(@__DIR__, "runtime_original_cost_fresh.tsv")) do io
        readline(io)
        for line in eachline(io)
            fields = split(line, '\t')
            index, row = parse(Int, fields[1]), parse(Int, fields[2])
            1 <= index <= length(seen) || error("snapshot index is outside the reduced LP")
            seen[index] && error("snapshot contains a duplicate variable index")
            seen[index] = true
            states[index] = getproperty(J, Symbol(fields[3]))
            values[index] = parse(Float64, fields[6])
            row > 0 && (basic[row] = index)
        end
    end
    all(seen) || error("the saved snapshot does not cover the reduced LP")
    all(index -> index != 0, basic) ||
        error("the saved snapshot does not define every reduced basis row")

    restored = J.restore_basis(presolved, J.Basis(basic, states))
    target = J.postsolve_primal(presolved,
        J.unscale_primal(scaling, values[1:columns]))
    options = SolverOptions(verbose=false, basis_update=:suhl_suhl,
        basis_refactorization=:native, refactorization_interval=50)
    prior_iterations = 44_145  # Iterations in the saved reduced optimum.

    function cleanup_run(label::String, project::Bool)
        # Independent model arrays, basis states and factorization for each arm.
        problem = J._minimization_problem(J.relax_integrality(original))
        workspace = J.initialize_workspace(problem, options)
        workspace.iterations = prior_iterations
        workspace.basis = J.Basis(copy(restored.basic_indices), copy(restored.states))
        started_ns = time_ns()
        stop_requested = () -> (time_ns() - started_ns) / 1e9 >= cap_seconds
        J.recompute!(workspace; refactorize=true)
        initial_pinf = J.primal_infeasibility_summary(workspace)
        initial_dinf = J.dual_infeasibility_summary(workspace)
        exchanges = 0
        if project
            exchanges = try
                J._project_postsolve_basis!(workspace, target, stop_requested)
            catch exception
                J._is_numerical_exception(exception) || rethrow()
                println("variant=projected projection_error=", sprint(showerror, exception))
                nothing
            end
            if isnothing(exchanges)
                status = stop_requested() ? J.TIME_LIMIT : J.NUMERICAL_ERROR
                println("variant=projected status=", status,
                    " message=basis projection could not be completed")
                return (; status, cleanup_iterations=0,
                        elapsed=(time_ns() - started_ns) / 1e9, objective=nothing)
            end
        end
        println("variant=", label, " initial_pinf=", initial_pinf,
            " initial_dinf=", initial_dinf, " exchanges=", exchanges,
            " start_pinf=", J.primal_infeasibility_summary(workspace),
            " start_dinf=", J.dual_infeasibility_summary(workspace),
            " max_structural_diff=",
            maximum(abs.(workspace.primal[1:length(target)] .- target)))
        flush(stdout)

        run = try
            J._solve_continuous_dual!(workspace, stop_requested)
        catch exception
            J._is_numerical_exception(exception) || rethrow()
            J.DualRunResult{Float64}(J.NUMERICAL_ERROR, nothing, nothing,
                workspace.iterations, workspace.refactorizations,
                sprint(showerror, exception))
        end
        cleanup_iterations = run.iterations - prior_iterations
        elapsed = (time_ns() - started_ns) / 1e9
        println("variant=", label, " status=", run.status,
            " cleanup_iterations=", cleanup_iterations,
            " cumulative_iterations=", run.iterations,
            " refactorizations=", run.refactorizations,
            " elapsed=", elapsed, " objective=", run.objective_value,
            " message=", run.message)
        flush(stdout)
        return (; status=run.status, cleanup_iterations, elapsed,
                objective=run.objective_value)
    end

    baseline = cleanup_run("restored", false)
    projected = cleanup_run("projected", true)
    if baseline.status == J.OPTIMAL && projected.status == J.OPTIMAL
        println("comparison=OPTIMAL_BOTH iterations_saved=",
            baseline.cleanup_iterations - projected.cleanup_iterations,
            " objective_difference=", projected.objective - baseline.objective)
    else
        println("comparison=INCONCLUSIVE restored_status=", baseline.status,
            " projected_status=", projected.status)
    end
end

main()
