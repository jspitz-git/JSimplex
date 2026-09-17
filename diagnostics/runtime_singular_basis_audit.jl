using JSimplex, LinearAlgebra, SparseArrays

const J = JSimplex
const BEFORE_PIVOT = 23_205
const AFTER_PIVOT = BEFORE_PIVOT + 1

function options_with_interval(options, interval)
    return SolverOptions(Float64;
        primal_tolerance=options.primal_tolerance,
        dual_tolerance=options.dual_tolerance,
        zero_tolerance=options.zero_tolerance,
        iteration_limit=options.iteration_limit,
        time_limit=options.time_limit,
        refactorization_interval=interval,
        verbose=options.verbose,
        log_level=options.log_level,
        algorithm=options.algorithm,
        pricing=options.pricing,
        basis_update=options.basis_update,
        basis_refactorization=options.basis_refactorization,
        scaling=options.scaling,
        presolve=options.presolve)
end

function working_column(A, variable)
    row_count, column_count = size(A)
    if variable <= column_count
        return Vector(A[:, variable])
    end
    column = zeros(Float64, row_count)
    column[variable - column_count] = -1.0
    return column
end

function refine_forward(B, factor, rhs_float, bits)
    return setprecision(BigFloat, bits) do
        values = BigFloat.(B.nzval)
        rhs = BigFloat.(rhs_float)
        solution = BigFloat.(factor \ rhs_float)
        residual = similar(rhs)
        scale = max(one(BigFloat), maximum(abs, rhs))
        target = BigFloat(10)^(-(bits == 256 ? 40 : 90))
        for correction in 0:32
            residual .= -rhs
            for column in eachindex(solution)
                value = solution[column]
                for position in B.colptr[column]:(B.colptr[column + 1] - 1)
                    residual[B.rowval[position]] += values[position] * value
                end
            end
            relative = maximum(abs, residual) / scale
            println("REFINE bits=", bits, " correction=", correction,
                    " relative_residual=", relative)
            if isfinite(relative) && relative <= target
                return solution, true
            end
            correction == 32 && break
            step = factor \ Float64.(residual)
            all(isfinite, step) || break
            solution .-= BigFloat.(step)
        end
        return solution, false
    end
end

function checked_lu(label, matrix)
    try
        factor = lu(matrix)
        println(label, "_LU success=true")
        return factor
    catch exception
        println(label, "_LU success=false exception=", sprint(showerror, exception))
        return nothing
    end
end

function main()
    path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
    output = get(ENV, "RUNTIME_BASIS_OUTPUT",
                 joinpath(pwd(), "runtime_23206_basis.csv"))
    started_ns = time_ns()
    options = SolverOptions(iteration_limit=100_000, time_limit=6000.0,
                            basis_update=:suhl_suhl,
                            basis_refactorization=:native,
                            refactorization_interval=50, verbose=false)
    println("START Julia=", VERSION, " machine=", Sys.MACHINE,
            " path=", path, " output=", output)
    original = read_mps(path)
    reduced = J.presolve_problem(J.relax_integrality(original))
    reduced isa J.PresolveFailure && error("presolve failed: $reduced")
    scaled, _ = J.scale_problem(reduced.problem)
    problem = J._minimization_problem(scaled)
    workspace = J.initialize_workspace(problem, options)
    println("MODEL size=", size(problem.A), " nnz=", nnz(problem.A))
    stop() = workspace.iterations >= BEFORE_PIVOT ||
             (time_ns() - started_ns) / 1.0e9 >= options.time_limit
    terminal = J.make_dual_feasible!(workspace, stop)
    isnothing(terminal) && (terminal = J._dual_optimize!(workspace, stop))
    println("BEFORE status=", terminal.status, " message=", terminal.message,
            " iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " updates=", length(workspace.factorization.updates),
            " dinf=", J.dual_infeasibility_summary(workspace))
    flush(stdout)
    workspace.iterations == BEFORE_PIVOT || error("target basis was not reached")
    prior_updates = length(workspace.factorization.updates)
    prior_updates < options.refactorization_interval ||
        error("the basis should have been refactorized before this pivot")

    old_basic = copy(workspace.basis.basic_indices)
    old_basis = J.basis_matrix(workspace)
    old_factor = checked_lu("OLD", old_basis)

    # Only the refactorization interval changes for this one pivot. Keep it
    # above the post-pivot update count so the new basis can be inspected.
    workspace.options = options_with_interval(
        options, max(options.refactorization_interval, prior_updates + 2))
    step = J.dual_iteration!(workspace, () -> false)
    println("PIVOT status=", isnothing(step) ? "completed" : step.status,
            " message=", isnothing(step) ? "" : step.message,
            " iterations=", workspace.iterations,
            " updates=", length(workspace.factorization.updates))
    flush(stdout)
    workspace.iterations == AFTER_PIVOT || error("target pivot was not completed")
    new_basic = copy(workspace.basis.basic_indices)
    changed = findall(old_basic .!= new_basic)
    length(changed) == 1 || error("expected one basis column to change: $changed")
    row = only(changed)
    leaving, entering = old_basic[row], new_basic[row]
    println("CHANGE row=", row, " leaving=", leaving, " entering=", entering,
            " updated_column_pivot=", workspace.scratch.row_solution[row],
            " updated_row_pivot=", workspace.scratch.tableau_row[entering],
            " zero_tolerance=", options.zero_tolerance)

    open(output, "w") do io
        println(io, "row,old_basic,new_basic")
        for index in eachindex(old_basic)
            println(io, index, ',', old_basic[index], ',', new_basic[index])
        end
    end
    println("BASIS_FILE ", output)

    column = working_column(problem.A, entering)
    if !isnothing(old_factor)
        fresh_column = old_factor \ column
        println("FRESH_OLD_PIVOT value=", fresh_column[row],
                " finite=", all(isfinite, fresh_column))
        for bits in (256, 512)
            refined_column, converged = refine_forward(old_basis, old_factor, column, bits)
            println("REFINED_PIVOT bits=", bits, " converged=", converged,
                    " value=", refined_column[row])
        end
    end

    new_basis = J.basis_matrix(workspace)
    println("NEW_BASIS size=", size(new_basis), " nnz=", nnz(new_basis),
            " zero_columns=", count(j -> new_basis.colptr[j] == new_basis.colptr[j + 1],
                                    1:size(new_basis, 2)))
    checked_lu("NEW", new_basis)
    println("END elapsed_seconds=", (time_ns() - started_ns) / 1.0e9)
    flush(stdout)
end

main()
