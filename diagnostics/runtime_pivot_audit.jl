using JSimplex, LinearAlgebra, SparseArrays
const J = JSimplex
const FIRST = 22_207
const LAST = 22_256

path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
options = SolverOptions(iteration_limit=100_000, time_limit=6000.0,
    basis_update=:suhl_suhl, basis_refactorization=:native,
    refactorization_interval=50, verbose=false)
println("Julia=", VERSION, " machine=", Sys.MACHINE, " path=", path)
original = read_mps(path)
reduced = J.presolve_problem(J.relax_integrality(original))
reduced isa J.PresolveFailure && error("presolve failed: $reduced")
scaled, _ = J.scale_problem(reduced.problem)
problem = J._minimization_problem(scaled)
println("reduced=", size(problem.A), " nnz=", nnz(problem.A))
flush(stdout)

# Build the actual basis without basis_matrix(workspace), which writes scratch arrays.
function independent_basis(A::SparseMatrixCSC{Float64,Int}, basic::Vector{Int})
    m, n = size(A)
    rows = Int[]
    columns = Int[]
    values = Float64[]
    for (basis_column, variable) in enumerate(basic)
        if variable <= n
            for position in A.colptr[variable]:(A.colptr[variable + 1] - 1)
                push!(rows, A.rowval[position])
                push!(columns, basis_column)
                push!(values, A.nzval[position])
            end
        else
            push!(rows, variable - n)
            push!(columns, basis_column)
            push!(values, -1.0)
        end
    end
    return sparse(rows, columns, values, m, m)
end

function fresh_measurement(w)
    A = w.problem.A
    _, n = size(A)
    basic = copy(w.basis.basic_indices)
    B = independent_basis(A, basic)
    factor = lu(B)
    cB = w.costs[basic]
    y = transpose(factor) \ cB
    reduced = vcat(w.costs[1:n] - transpose(A) * y, w.costs[(n+1):end] + y)
    bad = Int[]
    sum_bad = 0.0
    largest_difference = 0.0
    for i in eachindex(reduced)
        state = w.basis.states[i]
        state == J.BASIC && continue
        largest_difference = max(largest_difference, abs(reduced[i] - w.reduced_costs[i]))
        J._is_fixed(w.lower[i], w.upper[i]) && continue
        violation = state == J.AT_LOWER ? max(-reduced[i], 0.0) :
                    state == J.AT_UPPER ? max(reduced[i], 0.0) : abs(reduced[i])
        if violation > w.options.dual_tolerance
            push!(bad, i)
            sum_bad += violation
        end
    end

    nonbasic = copy(w.primal)
    nonbasic[basic] .= 0.0
    rhs = -(A * view(nonbasic, 1:n))
    rhs .+= view(nonbasic, (n+1):length(nonbasic))
    stored_residual = norm(B * w.primal[basic] - rhs, Inf)
    fresh_residual = norm(B * (factor \ rhs) - rhs, Inf)
    dual_residual = norm(transpose(B) * y - cB, Inf)
    return (; reduced, bad, sum_bad, largest_difference, stored_residual,
            fresh_residual, dual_residual, B, factor, y)
end

state_snapshot(w) = (
    basic=copy(w.basis.basic_indices), states=copy(w.basis.states),
    primal=copy(w.primal), reduced=copy(w.reduced_costs), costs=copy(w.costs),
)

function pivot_signature(w, before, i)
    changed = findall(before.basic .!= w.basis.basic_indices)
    length(changed) == 1 || error("expected one changed basis column at iteration $i: $changed")
    row = only(changed)
    leave, enter = before.basic[row], w.basis.basic_indices[row]
    flips = findall(index -> index != leave && index != enter &&
                             before.states[index] != w.basis.states[index],
                    eachindex(before.states))
    return (; iteration=i, row, leave, enter, flips,
            tableau_row=w.scratch.tableau_row[enter],
            tableau_column=w.scratch.row_solution[row])
end

function eligible(w, before, i, coefficient, cutoff)
    J._is_fixed(w.lower[i], w.upper[i]) && return false
    state = before.states[i]
    return (state == J.AT_LOWER && coefficient > cutoff) ||
           (state == J.AT_UPPER && coefficient < -cutoff) ||
           (state == J.FREE_NONBASIC && abs(coefficient) > cutoff)
end

# Read-only copy of the bound-flipping/Harris selection for the first event.
function ratio_decision(w, before, tableau_row, orientation, violation)
    cutoff = J._dual_pivot_cutoff(Float64)
    tolerance = w.options.dual_tolerance
    candidates = Int[]
    has_boxed = false
    for i in eachindex(tableau_row)
        coefficient = orientation * tableau_row[i]
        eligible(w, before, i, coefficient, cutoff) || continue
        push!(candidates, i)
        has_boxed |= isfinite(w.lower[i]) && isfinite(w.upper[i])
    end
    function harris()
        maximum_step = Inf
        for i in candidates
            coefficient = orientation * tableau_row[i]
            relaxed = (before.reduced[i] +
                       (coefficient < 0 ? -tolerance : tolerance)) / coefficient
            isfinite(relaxed) && (maximum_step = min(maximum_step, relaxed))
        end
        entering, largest = -1, 0.0
        for i in candidates
            coefficient = orientation * tableau_row[i]
            step = before.reduced[i] / coefficient
            if step <= maximum_step && abs(coefficient) > largest
                entering, largest = i, abs(coefficient)
            end
        end
        return entering, Int[], :harris, candidates
    end
    has_boxed || return harris()
    for i in candidates
        step = before.reduced[i] / (orientation * tableau_row[i])
        (!isfinite(step) || step < 0) && return harris()
    end
    sort!(candidates; by=i -> before.reduced[i] / (orientation * tableau_row[i]))
    flips = Int[]
    remaining = violation
    for i in candidates
        state = before.states[i]
        opposite = state == J.AT_LOWER ? w.upper[i] : w.lower[i]
        (state == J.FREE_NONBASIC || !isfinite(opposite)) &&
            return i, flips, :bound_flip, candidates
        width = J.bound_value(w.upper[i]) - J.bound_value(w.lower[i])
        gain = abs(tableau_row[i]) * width
        (!isfinite(width) || !isfinite(gain)) && return harris()
        remaining <= gain + w.options.primal_tolerance &&
            return i, flips, :bound_flip, candidates
        push!(flips, i)
        remaining -= gain
    end
    return -1, flips, :exhausted, candidates
end

function explain_first(w, before, previous, current, pivot)
    println("FIRST_BAD iteration=", pivot.iteration, " indices=", current.bad,
            " sum=", current.sum_bad)
    affected = sort!(union(previous.bad, current.bad))
    for i in affected
        println("VARIABLE index=", i,
                " before_state=", before.states[i],
                " before_stored_rc=", repr(before.reduced[i]),
                " before_fresh_rc=", repr(previous.reduced[i]),
                " before_cost=", repr(before.costs[i]),
                " after_state=", w.basis.states[i],
                " after_stored_rc=", repr(w.reduced_costs[i]),
                " after_fresh_rc=", repr(current.reduced[i]),
                " after_cost=", repr(w.costs[i]))
    end
    below = J._lower_violation(w.lower[pivot.leave], before.primal[pivot.leave]) > 0
    bound = below ? w.lower[pivot.leave] : w.upper[pivot.leave]
    delta = before.primal[pivot.leave] - J.bound_value(bound)
    orientation = below ? -1.0 : 1.0
    row = copy(w.scratch.tableau_row) # Tableau row used by the completed pivot.
    selected, flips, mode, candidates = ratio_decision(w, before, row, orientation, abs(delta))
    println("CAUSE_PIVOT row=", pivot.row, " leave=", pivot.leave,
            " enter=", pivot.enter, " below=", below, " delta=", repr(delta),
            " actual_flips=", pivot.flips, " ratio_mode=", mode,
            " ratio_enter=", selected, " ratio_flips=", flips,
            " candidates=", length(candidates))
    println("PIVOT_VALUES updated_row=", repr(pivot.tableau_row),
            " updated_column=", repr(pivot.tableau_column))
    unit = zeros(Float64, size(previous.B, 1)); unit[pivot.row] = 1.0
    n = size(w.problem.A, 2)
    column = pivot.enter <= n ? collect(w.problem.A[:, pivot.enter]) :
             [i == pivot.enter - n ? -1.0 : 0.0 for i in 1:length(unit)]
    rho_updated = copy(w.scratch.rho)
    rho_fresh = transpose(previous.factor) \ unit
    fresh_tableau_row = vcat(transpose(w.problem.A) * rho_fresh, -rho_fresh)
    fresh_row = fresh_tableau_row[pivot.enter]
    fresh_column = (previous.factor \ column)[pivot.row]
    println("PIVOT_FRESH row=", repr(fresh_row), " column=", repr(fresh_column))
    transported_y = previous.y +
                    (previous.reduced[pivot.enter] / fresh_row) * rho_fresh
    transported_residual = norm(transpose(current.B) * transported_y -
                                w.costs[w.basis.basic_indices], Inf)
    dual_difference = transported_y - current.y
    difference_residual = norm(transpose(current.B) * dual_difference, Inf)
    basis_transpose_norm = maximum(
        sum(abs, view(current.B.nzval, current.B.colptr[j]:(current.B.colptr[j+1]-1)))
        for j in 1:size(current.B, 2)
    )
    println("TRANSPORTED_DUAL residual=", repr(transported_residual),
            " fresh_residual=", repr(current.dual_residual),
            " y_difference=", repr(norm(dual_difference, Inf)),
            " difference_residual=", repr(difference_residual),
            " B_transpose_norm=", repr(basis_transpose_norm),
            " condition_lower_bound=",
            repr(basis_transpose_norm * norm(dual_difference, Inf) / difference_residual))
    println("ROW_SOLVE updated_residual=",
            norm(transpose(previous.B) * rho_updated - unit, Inf),
            " fresh_residual=", norm(transpose(previous.B) * rho_fresh - unit, Inf),
            " rho_difference=", norm(rho_updated - rho_fresh, Inf))
    fresh_before = merge(before, (reduced=previous.reduced,))
    fresh_selected, fresh_flips, fresh_mode, fresh_candidates =
        ratio_decision(w, fresh_before, fresh_tableau_row, orientation, abs(delta))
    println("FRESH_RATIO mode=", fresh_mode, " enter=", fresh_selected,
            " flips=", fresh_flips, " candidates=", length(fresh_candidates),
            " entering_rc=", repr(previous.reduced[pivot.enter]),
            " entering_step=", repr(previous.reduced[pivot.enter] /
                                    (orientation * fresh_row)))
    updated_dual_step = before.reduced[pivot.enter] / row[pivot.enter]
    fresh_dual_step = previous.reduced[pivot.enter] / fresh_row
    for i in affected
        transported_rc = i <= n ? w.costs[i] - dot(w.problem.A[:, i], transported_y) :
                                   w.costs[i] + transported_y[i-n]
        println("ROW_COEFFICIENT index=", i,
                " updated=", repr(row[i]), " fresh=", repr(fresh_tableau_row[i]),
                " predicted_updated_rc=", repr(before.reduced[i] - updated_dual_step * row[i]),
                " predicted_fresh_rc=", repr(previous.reduced[i] - fresh_dual_step * fresh_tableau_row[i]),
                " transported_rc=", repr(transported_rc))
    end
    remaining = abs(delta)
    for i in vcat(pivot.flips, pivot.enter)
        coefficient = orientation * row[i]
        step = before.reduced[i] / coefficient
        width = isfinite(w.lower[i]) && isfinite(w.upper[i]) ?
            J.bound_value(w.upper[i]) - J.bound_value(w.lower[i]) : Inf
        gain = abs(row[i]) * width
        println("BREAKPOINT index=", i, " state=", before.states[i],
                " rc=", repr(before.reduced[i]), " coefficient=", repr(coefficient),
                " step=", repr(step), " width=", repr(width),
                " gain=", repr(gain), " remaining_before=", repr(remaining))
        remaining -= gain
    end
    println("RESIDUALS_BEFORE stored_Bx=", previous.stored_residual,
            " fresh_Bx=", previous.fresh_residual,
            " fresh_Bty=", previous.dual_residual)
    println("RESIDUALS_AFTER stored_Bx=", current.stored_residual,
            " fresh_Bx=", current.fresh_residual,
            " fresh_Bty=", current.dual_residual)
end

function run_case(problem, options; observe::Bool)
    w = J.initialize_workspace(problem, options)
    println("RUN observe=", observe, " factor=", typeof(w.factorization),
            " backend=", typeof(w.factorization.base))
    trace = []
    last_seen = Ref(-1)
    before = Ref{Any}(nothing)
    previous_measurement = Ref{Any}(nothing)
    first_bad = Ref(0)
    function stop()
        i = w.iterations
        # At 22_206 the callback first runs after the pivot but before its
        # scheduled refactorization. Take the reference at the next callback.
        i == FIRST - 1 && !isempty(w.factorization.updates) && return false
        if FIRST - 1 <= i <= LAST && i != last_seen[]
            if i == FIRST - 1
                before[] = state_snapshot(w)
                if observe
                    previous_measurement[] = fresh_measurement(w)
                    println("REFERENCE iteration=", i,
                            " fresh_bad=", previous_measurement[].bad,
                            " updates=", length(w.factorization.updates))
                end
            else
                pivot = pivot_signature(w, before[], i)
                push!(trace, pivot)
                if observe
                    measurement = fresh_measurement(w)
                    println("MEASURE iteration=", i,
                            " updates=", length(w.factorization.updates),
                            " fresh_count=", length(measurement.bad),
                            " fresh_sum=", repr(measurement.sum_bad),
                            " max_rc_gap=", repr(measurement.largest_difference),
                            " stored_Bx=", repr(measurement.stored_residual),
                            " fresh_Bx=", repr(measurement.fresh_residual),
                            " fresh_Bty=", repr(measurement.dual_residual),
                            " pivot=", (pivot.row, pivot.leave, pivot.enter, pivot.flips))
                    if first_bad[] == 0 && !isempty(measurement.bad)
                        first_bad[] = i
                        explain_first(w, before[], previous_measurement[], measurement, pivot)
                    end
                    previous_measurement[] = measurement
                end
                before[] = state_snapshot(w)
            end
            last_seen[] = i
            flush(stdout)
        end
        return false
    end
    terminal = J.make_dual_feasible!(w, stop)
    isnothing(terminal) && (terminal = J._dual_optimize!(w, stop))
    println("END observe=", observe, " status=", terminal.status,
            " message=", terminal.message, " iterations=", w.iterations,
            " refactorizations=", w.refactorizations, " pivots_recorded=", length(trace),
            " first_bad=", first_bad[])
    flush(stdout)
    return (; trace, terminal, iterations=w.iterations,
            refactorizations=w.refactorizations, first_bad=first_bad[])
end

if get(ENV, "AUDIT_MEASURE_ONLY", "0") == "1"
    measured = run_case(problem, options; observe=true)
    println("MEASURE_ONLY count=", length(measured.trace), " first_bad=", measured.first_bad)
    length(measured.trace) == LAST - FIRST + 1 || error("missing pivot observations")
else
    control = run_case(problem, options; observe=false)
    measured = run_case(problem, options; observe=true)
    same_trace = control.trace == measured.trace
    same_terminal = (control.terminal.status, control.terminal.message,
                     control.iterations, control.refactorizations) ==
                    (measured.terminal.status, measured.terminal.message,
                     measured.iterations, measured.refactorizations)
    println("COMPARE same_trace=", same_trace, " same_terminal=", same_terminal,
            " count=", length(measured.trace), " first_bad=", measured.first_bad)
    same_trace && same_terminal && length(measured.trace) == LAST - FIRST + 1 ||
        error("instrumentation changed the pivot trace or termination")
end
