using JSimplex, LinearAlgebra, SparseArrays
const J = JSimplex
const TARGET_ITERATION = 23_000
const FIRST_TRACE_ITERATION = 22_206
const FAILURE_ITERATION = 22_256
const WATCHED = (19_825, 19_826, 50_165, 57_787)
const MAX_CORRECTIONS = 80

started_ns = time_ns()
seconds_since_start() = (time_ns() - started_ns) / 1.0e9
path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
options = SolverOptions(iteration_limit=100_000, time_limit=6000.0,
    basis_update=:suhl_suhl, basis_refactorization=:native,
    refactorization_interval=50, verbose=false)
println("Julia=", VERSION, " machine=", Sys.MACHINE, " path=", path)
println("OPTIONS iteration_limit=", options.iteration_limit,
        " time_limit=", options.time_limit, " basis_update=", options.basis_update,
        " basis_refactorization=", options.basis_refactorization,
        " refactorization_interval=", options.refactorization_interval,
        " verbose=", options.verbose)
original = read_mps(path)
reduced = J.presolve_problem(J.relax_integrality(original))
reduced isa J.PresolveFailure && error("presolve failed: $reduced")
scaled, _ = J.scale_problem(reduced.problem)
problem = J._minimization_problem(scaled)
workspace = J.initialize_workspace(problem, options)
println("REDUCED size=", size(problem.A), " nnz=", nnz(problem.A),
        " factor=", typeof(workspace.factorization),
        " backend=", typeof(workspace.factorization.base),
        " setup_seconds=", seconds_since_start())
flush(stdout)

# Match the prior audit without calculating any extra solves during the
# first 22,256 iterations. The callback also implements the experiment cap.
trace = Tuple{Int,Int,Int,Int}[]
previous_basic = Ref{Any}(nothing)
last_seen = Ref(-1)
last_progress = Ref(-1)
stop_reason = Ref(:none)
function stop()
    i = workspace.iterations
    if i == FIRST_TRACE_ITERATION && !isempty(workspace.factorization.updates)
        return false
    end
    if FIRST_TRACE_ITERATION <= i <= FAILURE_ITERATION && i != last_seen[]
        basic = copy(workspace.basis.basic_indices)
        if i > FIRST_TRACE_ITERATION
            changed = findall(previous_basic[] .!= basic)
            length(changed) == 1 || error("unexpected basis change at $i: $changed")
            row = only(changed)
            push!(trace, (i, row, previous_basic[][row], basic[row]))
        end
        previous_basic[] = basic
        last_seen[] = i
    end
    if i > FAILURE_ITERATION && i % 50 == 0 && i != last_progress[]
        println("PROGRESS iteration=", i,
                " refactorizations=", workspace.refactorizations,
                " updates=", length(workspace.factorization.updates),
                " elapsed_seconds=", seconds_since_start())
        last_progress[] = i
        flush(stdout)
    end
    if i >= TARGET_ITERATION
        stop_reason[] = :target
        return true
    end
    if seconds_since_start() >= options.time_limit
        stop_reason[] = :time_limit
        return true
    end
    return false
end

function prior_trace()
    expected = Tuple{Int,Int,Int,Int}[]
    log_path = joinpath(@__DIR__, "runtime_pivot_audit.log")
    for line in eachline(log_path)
        matched = match(r"^MEASURE iteration=(\d+).*pivot=\((\d+), (\d+), (\d+),", line)
        isnothing(matched) && continue
        push!(expected, ntuple(j -> parse(Int, matched.captures[j]), 4))
    end
    return expected
end

# These independent calculations duplicate the mathematical procedure in
# runtime_bigfloat_refinement.jl. They never call basis_matrix or recompute!.
function independent_basis(A::SparseMatrixCSC{Float64,Int}, basic::Vector{Int})
    m, n = size(A)
    rows, columns, values = Int[], Int[], Float64[]
    for (basis_column, variable) in enumerate(basic)
        if variable <= n
            for p in A.colptr[variable]:(A.colptr[variable + 1] - 1)
                push!(rows, A.rowval[p])
                push!(columns, basis_column)
                push!(values, A.nzval[p])
            end
        else
            push!(rows, variable - n)
            push!(columns, basis_column)
            push!(values, -1.0)
        end
    end
    return sparse(rows, columns, values, m, m)
end

function transpose_residual!(residual, B, big_values, solution, rhs)
    for j in eachindex(rhs)
        sum = BigFloat(0)
        for p in B.colptr[j]:(B.colptr[j+1]-1)
            sum += big_values[p] * solution[B.rowval[p]]
        end
        residual[j] = sum - rhs[j]
    end
    return maximum(abs, residual)
end

function refine_transpose(B, factor, rhs_float, bits, event)
    setprecision(BigFloat, bits) do
        big_values = BigFloat.(B.nzval)
        rhs = BigFloat.(rhs_float)
        solution = BigFloat.(transpose(factor) \ rhs_float)
        residual = similar(rhs)
        scale = max(BigFloat(1), maximum(abs, rhs))
        target = BigFloat(10)^(-(bits == 256 ? 40 : 90))
        for step in 0:MAX_CORRECTIONS
            absolute = transpose_residual!(residual, B, big_values, solution, rhs)
            relative = absolute / scale
            println("REFINE event=", event, " bits=", bits, " step=", step,
                    " abs_res=", absolute, " rel_res=", relative)
            if isfinite(relative) && relative <= target
                println("REFINE_END event=", event, " bits=", bits,
                        " converged=true corrections=", step,
                        " final_abs_res=", absolute)
                flush(stdout)
                return solution, true
            end
            step == MAX_CORRECTIONS && break
            correction = transpose(factor) \ Float64.(residual)
            all(isfinite, correction) || break
            solution .-= BigFloat.(correction)
        end
        println("REFINE_END event=", event, " bits=", bits,
                " converged=false target=", target)
        flush(stdout)
        return solution, false
    end
end

function reduced_prices(A, costs, dual, bits)
    setprecision(BigFloat, bits) do
        m, n = size(A)
        values = BigFloat.(A.nzval)
        prices = Vector{BigFloat}(undef, n + m)
        for j in 1:n
            sum = BigFloat(0)
            for p in A.colptr[j]:(A.colptr[j+1]-1)
                sum += values[p] * dual[A.rowval[p]]
            end
            prices[j] = BigFloat(costs[j]) - sum
        end
        for i in 1:m
            prices[n+i] = BigFloat(costs[n+i]) + dual[i]
        end
        return prices
    end
end

function bad_prices(prices, w)
    T = eltype(prices)
    tolerance = T(w.options.dual_tolerance)
    bad = Int[]
    sum_bad = zero(T)
    for i in eachindex(prices)
        state = w.basis.states[i]
        state == J.BASIC && continue
        J._is_fixed(w.lower[i], w.upper[i]) && continue
        violation = state == J.AT_LOWER ? max(-prices[i], zero(T)) :
                    state == J.AT_UPPER ? max(prices[i], zero(T)) : abs(prices[i])
        if violation > tolerance
            push!(bad, i)
            sum_bad += violation
        end
    end
    return bad, sum_bad
end

function try_refinement!(w, event)
    event_started_ns = time_ns()
    before_bad, before_sum = J.dual_infeasibility_summary(w)
    println("RECOVERY_START event=", event, " iteration=", w.iterations,
            " refactorizations=", w.refactorizations,
            " updates=", length(w.factorization.updates),
            " float64_dinf=", before_bad, " float64_count=", before_sum)
    flush(stdout)
    isempty(w.factorization.updates) || return false, "basis not freshly refactorized"
    B = independent_basis(w.problem.A, copy(w.basis.basic_indices))
    factor = lu(B)
    rhs = w.costs[w.basis.basic_indices]
    results = Dict{Int,Any}()
    for bits in (256, 512)
        dual, converged = refine_transpose(B, factor, rhs, bits, event)
        if !converged
            results[bits] = (converged=false, bad=Int[], prices=nothing)
            continue
        end
        prices = reduced_prices(w.problem.A, w.costs, dual, bits)
        finite = all(isfinite, prices)
        bad, sum_bad = finite ? bad_prices(prices, w) : (Int[], BigFloat(NaN))
        for i in WATCHED
            println("WATCH event=", event, " bits=", bits, " index=", i,
                    " state=", w.basis.states[i], " stored_rc=", w.reduced_costs[i],
                    " refined_rc=", prices[i])
        end
        println("FEASIBILITY event=", event, " bits=", bits,
                " finite=", finite, " bad=", bad, " sum=", sum_bad)
        results[bits] = (converged=finite, bad=bad, prices=prices)
    end
    if !results[256].converged || !results[512].converged
        return false, "refinement did not converge to finite prices"
    end
    if results[256].bad != results[512].bad
        return false, "256/512-bit feasibility disagrees"
    end
    if !isempty(results[512].bad)
        return false, "both refinements remain dual infeasible"
    end
    # Convert before touching the workspace; roundoff at this last conversion
    # must not reintroduce a violation at the solver's Float64 tolerance.
    replacement = Float64.(results[512].prices)
    all(isfinite, replacement) || return false, "Float64 conversion is nonfinite"
    replacement[w.basis.basic_indices] .= 0.0
    converted_bad, converted_sum = bad_prices(replacement, w)
    isempty(converted_bad) || return false, "Float64 conversion lost feasibility"
    max_gap = maximum(abs(results[256].prices[i] - results[512].prices[i])
                      for i in eachindex(replacement))
    w.reduced_costs .= replacement     # The only workspace mutation in this function.
    applied_sum, applied_count = J.dual_infeasibility_summary(w)
    applied_count == 0 || error("replaced prices are unexpectedly infeasible")
    println("RECOVERY_APPLIED event=", event, " iteration=", w.iterations,
            " max_256_512_gap=", max_gap,
            " converted_dinf=", converted_sum,
            " applied_dinf=", applied_sum, " applied_count=", applied_count,
            " seconds=", (time_ns() - event_started_ns) / 1.0e9)
    flush(stdout)
    return true, "dual-feasible refined prices applied"
end

terminal = J.make_dual_feasible!(workspace, stop)
isnothing(terminal) && (terminal = J._dual_optimize!(workspace, stop))
println("FIRST_END status=", terminal.status, " message=", terminal.message,
        " iteration=", workspace.iterations,
        " refactorizations=", workspace.refactorizations,
        " dinf=", J.dual_infeasibility_summary(workspace),
        " elapsed_seconds=", seconds_since_start())
expected = prior_trace()
trace_matches = length(expected) == 50 && trace == expected
baseline_matches = trace_matches && workspace.iterations == FAILURE_ITERATION &&
    workspace.refactorizations == 446 && terminal.status == J.NUMERICAL_ERROR &&
    terminal.message == "dual feasibility lost" &&
    isempty(workspace.factorization.updates)
println("BASELINE_CHECK expected_pivots=", length(expected),
        " observed_pivots=", length(trace), " trace_matches=", trace_matches,
        " baseline_matches=", baseline_matches)
flush(stdout)

function finish_experiment!(workspace, terminal, baseline_matches, stop_reason, stop)
    applied = 0
    attempts = 0
    last_recovered_iteration = -1
    experiment_status = :NUMERICAL_ERROR
    experiment_reason = "baseline did not match"
    if baseline_matches
        while true
            if stop_reason[] == :target && workspace.iterations >= TARGET_ITERATION
                experiment_status = :TARGET_REACHED
                experiment_reason = "experiment iteration cap reached"
                break
            elseif stop_reason[] == :time_limit
                experiment_status = :TIME_LIMIT
                experiment_reason = "6000-second experiment cap reached"
                break
            elseif terminal.status != J.NUMERICAL_ERROR || terminal.message != "dual feasibility lost"
                experiment_status = Symbol(string(terminal.status))
                experiment_reason = terminal.message
                break
            elseif workspace.iterations == last_recovered_iteration
                experiment_status = :NUMERICAL_ERROR
                experiment_reason = "dual feasibility lost again without a completed pivot"
                break
            end
            attempts += 1
            success, reason = try
                try_refinement!(workspace, attempts)
            catch exception
                println("RECOVERY_EXCEPTION event=", attempts,
                        " exception=", sprint(showerror, exception))
                false, "refinement raised an exception"
            end
            if !success
                experiment_status = :NUMERICAL_ERROR
                experiment_reason = reason
                break
            end
            applied += 1
            last_recovered_iteration = workspace.iterations
            terminal = J._dual_optimize!(workspace, stop)
            println("CONTINUATION_END status=", terminal.status,
                    " message=", terminal.message, " iteration=", workspace.iterations,
                    " refactorizations=", workspace.refactorizations,
                    " dinf=", J.dual_infeasibility_summary(workspace),
                    " elapsed_seconds=", seconds_since_start())
            flush(stdout)
        end
    end
    println("EXPERIMENT_END status=", experiment_status, " reason=", experiment_reason,
            " iteration=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " refinement_attempts=", attempts, " refinements_applied=", applied,
            " solver_status=", terminal.status, " solver_message=", terminal.message,
            " elapsed_seconds=", seconds_since_start())
    flush(stdout)
end
finish_experiment!(workspace, terminal, baseline_matches, stop_reason, stop)
