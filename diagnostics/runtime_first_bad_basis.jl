using JSimplex, LinearAlgebra, SparseArrays

const J = JSimplex
const FIRST_CHECK = 23_156
const LAST_CHECK = 23_205

function save_basis(path, before, after)
    open(path, "w") do io
        println(io, "row,before_basic,after_basic")
        for row in eachindex(before)
            println(io, row, ',', before[row], ',', after[row])
        end
    end
end

function main()
    path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
    output = get(ENV, "RUNTIME_FIRST_BAD_BASIS_OUTPUT",
                 joinpath(pwd(), "runtime_first_bad_basis.csv"))
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
    flush(stdout)

    last_checked = Ref(FIRST_CHECK - 1)
    previous_basic = Ref{Vector{Int}}(Int[])
    failed = Ref(false)
    function stop()
        iteration = workspace.iterations
        if FIRST_CHECK <= iteration <= LAST_CHECK && iteration != last_checked[]
            current_basic = copy(workspace.basis.basic_indices)
            old_basic = isempty(previous_basic[]) ? current_basic : previous_basic[]
            changed = findall(old_basic .!= current_basic)
            if iteration > FIRST_CHECK
                length(changed) == 1 || error("unexpected basis change at $iteration: $changed")
            end
            row = isempty(changed) ? 0 : only(changed)
            B = J.basis_matrix(workspace)
            result = try
                lu(B)
                "success"
            catch exception
                string("failure: ", sprint(showerror, exception))
            end
            println("CHECK iteration=", iteration,
                    " updates=", length(workspace.factorization.updates),
                    " refactorizations=", workspace.refactorizations,
                    " basis_row=", row,
                    " leaving=", row == 0 ? 0 : old_basic[row],
                    " entering=", row == 0 ? 0 : current_basic[row],
                    " updated_pivot=", row == 0 ? NaN : workspace.scratch.row_solution[row],
                    " fresh_lu=", result)
            flush(stdout)
            if result != "success"
                save_basis(output, old_basic, current_basic)
                println("BASIS_FILE ", output)
                failed[] = true
            end
            previous_basic[] = current_basic
            last_checked[] = iteration
        end
        return failed[] || iteration >= LAST_CHECK ||
               (time_ns() - started_ns) / 1.0e9 >= options.time_limit
    end

    terminal = J.make_dual_feasible!(workspace, stop)
    isnothing(terminal) && (terminal = J._dual_optimize!(workspace, stop))
    println("END status=", terminal.status, " message=", terminal.message,
            " iterations=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " first_bad_basis=", failed[],
            " elapsed_seconds=", (time_ns() - started_ns) / 1.0e9)
    flush(stdout)
end

main()
