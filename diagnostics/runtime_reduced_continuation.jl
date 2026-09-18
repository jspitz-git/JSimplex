using JSimplex, LinearAlgebra, SparseArrays

const J = JSimplex

function main()
    path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
    target = parse(Int, get(ENV, "RUNTIME_TARGET_ITERATIONS", "30000"))
    time_limit = parse(Float64, get(ENV, "RUNTIME_TIME_LIMIT", "600.0"))
    target > 0 || error("RUNTIME_TARGET_ITERATIONS must be positive")
    time_limit > 0 || error("RUNTIME_TIME_LIMIT must be positive")
    started_ns = time_ns()
    options = SolverOptions(iteration_limit=100_000, time_limit=time_limit,
                            basis_update=:suhl_suhl,
                            basis_refactorization=:native,
                            refactorization_interval=50, verbose=false)
    println("START Julia=", VERSION, " machine=", Sys.MACHINE,
            " julia_threads=", Threads.nthreads(),
            " blas_threads=", BLAS.get_num_threads(),
            " target=", target, " time_limit=", time_limit,
            " path=", path)
    original = read_mps(path)
    reduced = J.presolve_problem(J.relax_integrality(original))
    reduced isa J.PresolveFailure && error("presolve failed: $reduced")
    scaled, _ = J.scale_problem(reduced.problem)
    problem = J._minimization_problem(scaled)
    workspace = J.initialize_workspace(problem, options)
    println("MODEL size=", size(problem.A), " nnz=", nnz(problem.A))
    flush(stdout)

    last_report = Ref(-1)
    function stop()
        iteration = workspace.iterations
        if iteration > 0 && iteration != last_report[] &&
           (iteration % 500 == 0 || iteration >= target)
            println("CHECKPOINT iteration=", iteration,
                    " refactorizations=", workspace.refactorizations,
                    " updates=", length(workspace.factorization.updates),
                    " pinf=", J.primal_infeasibility_summary(workspace),
                    " dinf=", J.dual_infeasibility_summary(workspace),
                    " elapsed_seconds=", (time_ns() - started_ns) / 1.0e9)
            flush(stdout)
            last_report[] = iteration
        end
        return iteration >= target ||
               (time_ns() - started_ns) / 1.0e9 >= time_limit
    end

    terminal = J.make_dual_feasible!(workspace, stop)
    isnothing(terminal) && (terminal = J._dual_optimize!(workspace, stop))
    println("END status=", terminal.status, " message=", terminal.message,
            " target_reached=", workspace.iterations >= target,
            " iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " pinf=", J.primal_infeasibility_summary(workspace),
            " dinf=", J.dual_infeasibility_summary(workspace),
            " elapsed_seconds=", (time_ns() - started_ns) / 1.0e9)
    flush(stdout)
end

main()
