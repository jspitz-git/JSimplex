include(joinpath(@__DIR__, "runtime_reduced_continuation.jl"))

function load_snapshot()
    path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
    snapshot = get(ENV, "RUNTIME_SNAPSHOT_PATH",
                   joinpath(@__DIR__, "runtime_reduced_failure_state.tsv"))
    original = read_mps(path)
    reduced = J.presolve_problem(J.relax_integrality(original))
    reduced isa J.PresolveFailure && error("presolve failed: $reduced")
    scaled, _ = J.scale_problem(reduced.problem)
    problem = J._minimization_problem(scaled)
    options = SolverOptions(iteration_limit=100_000, time_limit=600.0,
                            basis_update=:suhl_suhl,
                            basis_refactorization=:native,
                            refactorization_interval=50, verbose=false)
    workspace = J.initialize_workspace(problem, options)
    base_costs = copy(workspace.costs)
    fill!(workspace.basis.basic_indices, 0)
    seen = 0
    open(snapshot) do input
        readline(input) == "index\tbasis_row\tstate\tcost\treduced_cost\tprimal" ||
            error("unexpected snapshot header")
        for (index, line) in enumerate(eachline(input))
            seen = index
            fields = split(line, '\t')
            length(fields) == 6 || error("invalid snapshot row $index")
            parse(Int, fields[1]) == index || error("unexpected variable index $index")
            row = parse(Int, fields[2])
            workspace.basis.states[index] = getfield(J, Symbol(fields[3]))
            workspace.costs[index] = parse(Float64, fields[4])
            workspace.reduced_costs[index] = parse(Float64, fields[5])
            workspace.primal[index] = parse(Float64, fields[6])
            if row != 0
                workspace.basis.basic_indices[row] == 0 || error("duplicate basis row $row")
                workspace.basis.basic_indices[row] = index
            end
        end
    end
    seen == length(workspace.basis.states) || error("wrong snapshot variable count: $seen")
    all(index -> index != 0, workspace.basis.basic_indices) || error("missing basis row")
    J._validate_basis(workspace)
    cost_overrides = count(x -> !iszero(x), workspace.costs .- base_costs)
    # The snapshot records working costs but not this workspace flag.
    workspace.perturbed = cost_overrides > 0
    println("MODEL size=", size(problem.A), " nnz=", nnz(problem.A))
    println("SNAPSHOT variables=", length(workspace.basis.states),
            " cost_overrides=", cost_overrides,
            " dual_infeasibility=", J.dual_infeasibility_summary(workspace),
            " primal_infeasibility=", J.primal_infeasibility_summary(workspace),
            " iteration_metadata=not_saved")
    return workspace
end

function audit_snapshot()
    workspace = load_snapshot()
    audit_dual_loss(workspace)
end

abspath(PROGRAM_FILE) == abspath(@__FILE__) && audit_snapshot()
