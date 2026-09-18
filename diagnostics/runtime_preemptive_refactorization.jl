using JSimplex, LinearAlgebra, SparseArrays

const J = JSimplex
const BEFORE_PIVOT = 23_201
const AFTER_PIVOT = BEFORE_PIVOT + 1
const BAD_ROW = 25_632
const BAD_ENTERING = 57_784

function main()
    path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
    started_ns = time_ns()
    options = SolverOptions(iteration_limit=100_000, time_limit=6000.0,
                            basis_update=:suhl_suhl,
                            basis_refactorization=:native,
                            refactorization_interval=50, verbose=false)
    println("START Julia=", VERSION, " machine=", Sys.MACHINE,
            " julia_threads=", Threads.nthreads(),
            " blas_threads=", BLAS.get_num_threads(), " path=", path)
    original = read_mps(path)
    reduced = J.presolve_problem(J.relax_integrality(original))
    reduced isa J.PresolveFailure && error("presolve failed: $reduced")
    scaled, _ = J.scale_problem(reduced.problem)
    problem = J._minimization_problem(scaled)
    workspace = J.initialize_workspace(problem, options)
    println("MODEL size=", size(problem.A), " nnz=", nnz(problem.A))

    timed_out() = (time_ns() - started_ns) / 1.0e9 >= options.time_limit
    before_stop() = workspace.iterations >= BEFORE_PIVOT || timed_out()
    terminal = J.make_dual_feasible!(workspace, before_stop)
    isnothing(terminal) && (terminal = J._dual_optimize!(workspace, before_stop))
    println("BEFORE status=", terminal.status, " message=", terminal.message,
            " iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " updates=", length(workspace.factorization.updates),
            " dinf=", J.dual_infeasibility_summary(workspace))
    flush(stdout)
    workspace.iterations == BEFORE_PIVOT || return

    old_basic = copy(workspace.basis.basic_indices)
    B = J.basis_matrix(workspace)
    rhs = zeros(Float64, size(B, 1))
    rhs[BAD_ENTERING - size(problem.A, 2)] = -1.0
    updated_direction = J.forward_solve(workspace.factorization, rhs)
    println("UPDATED_OLD_DIRECTION row=", BAD_ROW,
            " pivot=", updated_direction[BAD_ROW],
            " norm_inf=", norm(updated_direction, Inf),
            " residual_inf=", norm(B * updated_direction - rhs, Inf))
    try
        direction = lu(B) \ rhs
        println("FRESH_OLD_DIRECTION row=", BAD_ROW,
                " pivot=", direction[BAD_ROW],
                " norm_inf=", norm(direction, Inf),
                " residual_inf=", norm(B * direction - rhs, Inf))
    catch exception
        println("FRESH_OLD_LU failure=", sprint(showerror, exception))
    end
    flush(stdout)

    # Rebuild the same basis before choosing the next leaving and entering
    # variables. This changes no model data or basis index.
    try
        J.recompute!(workspace; refactorize=true)
    catch exception
        println("REFACTORIZE failure=", sprint(showerror, exception))
        return
    end
    println("REFACTORIZED iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " updates=", length(workspace.factorization.updates),
            " dinf=", J.dual_infeasibility_summary(workspace))
    flush(stdout)

    after_stop() = workspace.iterations >= AFTER_PIVOT || timed_out()
    terminal = J._dual_optimize!(workspace, after_stop)
    changed = findall(old_basic .!= workspace.basis.basic_indices)
    println("AFTER status=", terminal.status, " message=", terminal.message,
            " iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " updates=", length(workspace.factorization.updates),
            " changed_rows=", changed,
            " dinf=", J.dual_infeasibility_summary(workspace))
    if length(changed) == 1
        row = only(changed)
        entering = workspace.basis.basic_indices[row]
        println("PIVOT row=", row, " leaving=", old_basic[row],
                " entering=", entering,
                " updated_column_pivot=", workspace.scratch.row_solution[row],
                " updated_row_pivot=", workspace.scratch.tableau_row[entering])
        try
            lu(J.basis_matrix(workspace))
            println("NEW_LU success=true")
        catch exception
            println("NEW_LU success=false exception=", sprint(showerror, exception))
        end
    end
    println("END elapsed_seconds=", (time_ns() - started_ns) / 1.0e9)
    flush(stdout)
end

main()
