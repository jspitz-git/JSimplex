using JSimplex, LinearAlgebra

# Reconstruct the Windows reduced optimum from runtime_original_cost_fresh.tsv,
# then measure the restored basis after each inverse presolve step. Invoke with
# the path to runtime.mps, for example:
#   julia --project=. diagnostics/runtime_postsolve_basis_audit.jl /path/to/runtime.mps
# The basis snapshot was produced with one Julia and one BLAS thread.
const J = JSimplex
function main()
    BLAS.set_num_threads(1)
    length(ARGS) == 1 || error("pass the path to runtime.mps")
    original = J.relax_integrality(read_mps(only(ARGS)))
    result = J.identity_presolve(original)
    trace = Tuple{Any,Any}[]
    propagation_trace = J.PropagationTrace{Float64}()
    passes = (J._presolve_basic, J.reduce_singleton_rows,
              J.aggregate_singleton_equalities, J.aggregate_sparse_equalities,
              J.reduce_parallel_rows, J.reduce_dependent_rows,
              J.substitute_free_doubleton, J.propagate_row_bounds,
              J.reduce_dual_fixings)
    last_relevant_pass = length(passes)
    for _ in 1:12
        last_changed_pass = 0
        for (index, pass) in enumerate(passes)
            index > last_relevant_pass && break
            before = result.problem
            if pass === J.propagate_row_bounds
                dirty = isnothing(propagation_trace.reference) ?
                    trues(size(before.A, 1)) :
                    J._changed_propagation_rows(propagation_trace.reference, before,
                        propagation_trace.row_origin, propagation_trace.column_origin,
                        propagation_trace.pending)
                changed_columns = falses(size(before.A, 2))
                next = J._propagate_row_bounds(before, dirty, changed_columns)
                @assert !(next isa J.PresolveFailure)
                if !isempty(next.postsolve_stack)
                    push!(trace, (before, only(next.postsolve_stack)))
                    result = J._compose_presolve(result, next)
                    last_changed_pass = index
                    last_relevant_pass = length(passes)
                end
                J._reset_propagation_trace!(propagation_trace, next, changed_columns)
                continue
            end
            next = pass(before)
            @assert !(next isa J.PresolveFailure)
            isempty(next.postsolve_stack) && continue
            push!(trace, (before, only(next.postsolve_stack)))
            result = J._compose_presolve(result, next)
            J._advance_propagation_trace!(propagation_trace, next)
            last_changed_pass = index
            last_relevant_pass = length(passes)
        end
        last_changed_pass == 0 && break
        last_relevant_pass = last_changed_pass
    end
    println("steps=", length(trace), " final_dims=", size(result.problem.A))
    @assert length(trace) == length(result.postsolve_stack)
    for (i, pair) in enumerate(trace)
        @assert pair[2] === result.postsolve_stack[i]
    end
    reference = J.presolve_problem(original)
    @assert reference isa J.PresolveResult
    @assert result.problem.A == reference.problem.A
    @assert result.problem.objective == reference.problem.objective
    @assert result.problem.column_lower == reference.problem.column_lower
    @assert result.problem.column_upper == reference.problem.column_upper
    @assert result.problem.row_lower == reference.problem.row_lower
    @assert result.problem.row_upper == reference.problem.row_upper

    scaled, scaling = J.scale_problem(result.problem)
    m, n = size(scaled.A)
    basic = zeros(Int, m)
    states = Vector{J.VariableState}(undef, m + n)
    values = zeros(Float64, m + n)
    open(joinpath(@__DIR__, "runtime_original_cost_fresh.tsv")) do io
        readline(io)
        for line in eachline(io)
            fields = split(line, '\t')
            index, row = parse(Int, fields[1]), parse(Int, fields[2])
            states[index] = getproperty(J, Symbol(fields[3]))
            values[index] = parse(Float64, fields[6])
            row > 0 && (basic[row] = index)
        end
    end
    basis = J.Basis(basic, states)
    x = J.unscale_primal(scaling, values[1:n])

    function nonbasic_mismatch(problem, basis, x)
        _, n = size(problem.A)
        activity = problem.A * x
        count = 0
        total = 0.0
        maxdelta = 0.0
        worst = (0, 0.0)
        for index in eachindex(basis.states)
            state = basis.states[index]
            state == J.BASIC && continue
            lower = index <= n ? problem.column_lower[index] : problem.row_lower[index-n]
            upper = index <= n ? problem.column_upper[index] : problem.row_upper[index-n]
            actual = index <= n ? x[index] : activity[index-n]
            expected = state == J.AT_LOWER ? J.bound_value(lower) :
                       state == J.AT_UPPER ? J.bound_value(upper) : 0.0
            delta = abs(actual - expected)
            if delta > 1e-7
                count += 1
                total += delta
                if delta > maxdelta
                    maxdelta = delta
                    worst = (index, delta)
                end
            end
        end
        return count, total, worst
    end

    options = SolverOptions(verbose=false, basis_update=:suhl_suhl,
        basis_refactorization=:native, refactorization_interval=50)
    function basis_metrics(problem, basis, options)
        workspace = J.initialize_workspace(J._minimization_problem(problem), options)
        workspace.basis = basis
        J.recompute!(workspace; refactorize=true)
        return J.primal_infeasibility_summary(workspace),
               J.dual_infeasibility_summary(workspace)
    end

    println("final reduced mismatch=", nonbasic_mismatch(result.problem, basis, x),
        " basis_metrics=", basis_metrics(result.problem, basis, options))
    for i in length(trace):-1:1
        problem, step = trace[i]
        x = J.postsolve_primal(step, x)
        basis = J.restore_basis(step, basis)
        println("undo $i $(nameof(typeof(step))) dims=$(size(problem.A)) mismatch=",
            nonbasic_mismatch(problem, basis, x),
            " basis_metrics=", basis_metrics(problem, basis, options))
    end

    # Isolate the primal effect of releasing implied bounds. This is a
    # counterfactual workspace calculation, never a production solve: set the
    # nonbasic values to their postsolved values while retaining the original
    # matrix and restored basis.
    @assert J._original_primal_feasible(original, x, options.primal_tolerance)
    workspace = J.initialize_workspace(J._minimization_problem(original), options)
    workspace.basis = basis
    J.recompute!(workspace; refactorize=true)
    column_count = size(original.A, 2)
    reassigned = 0
    for index in 1:column_count
        abs(workspace.primal[index] - x[index]) > options.primal_tolerance || continue
        state = basis.states[index]
        if state == J.AT_LOWER
            workspace.lower[index] = J.Bound(x[index])
        elseif state == J.AT_UPPER
            workspace.upper[index] = J.Bound(x[index])
        else
            continue
        end
        reassigned += 1
    end
    J.recompute!(workspace)
    println("counterfactual reassigned_nonbasic=$reassigned basis_metrics=",
        (J.primal_infeasibility_summary(workspace), J.dual_infeasibility_summary(workspace)),
        " max_structural_difference=", maximum(abs.(workspace.primal[1:column_count] .- x)))

    projected = J.initialize_workspace(J._minimization_problem(original), options)
    projected.basis = basis
    J.recompute!(projected; refactorize=true)
    exchanges = J._project_postsolve_basis!(projected, x, () -> false)
    println("projected_basis exchanges=$exchanges basis_metrics=",
        (J.primal_infeasibility_summary(projected),
         J.dual_infeasibility_summary(projected)),
        " max_structural_difference=",
        maximum(abs.(projected.primal[1:column_count] .- x)))
end
main()
