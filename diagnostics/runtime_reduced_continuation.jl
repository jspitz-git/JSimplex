using JSimplex, LinearAlgebra, SparseArrays

const J = JSimplex

function price_violation(workspace, index, price)
    state = workspace.basis.states[index]
    if state == J.BASIC || J._is_fixed(workspace.lower[index], workspace.upper[index])
        return zero(price)
    elseif state == J.AT_LOWER
        return max(zero(price), -price)
    elseif state == J.AT_UPPER
        return max(zero(price), price)
    end
    return abs(price)
end

function report_prices(workspace, label, prices)
    tolerance = BigFloat(workspace.options.dual_tolerance)
    count = 0
    total = BigFloat(0)
    for index in eachindex(prices)
        violation = price_violation(workspace, index, prices[index])
        violation > tolerance || continue
        count += 1
        total += violation
        if count <= 10
            println("BAD_PRICE source=", label, " index=", index,
                    " state=", workspace.basis.states[index],
                    " stored=", workspace.reduced_costs[index],
                    " price=", prices[index], " violation=", violation)
        end
    end
    println("PRICE_SUMMARY source=", label, " count=", count,
            " total=", total, " tolerance=", tolerance)
    flush(stdout)
    return count, total
end

function independent_basis(workspace)
    A = workspace.problem.A
    rows, columns, values = Int[], Int[], Float64[]
    row_count, column_count = size(A)
    for (basis_column, variable) in enumerate(workspace.basis.basic_indices)
        if variable <= column_count
            for position in A.colptr[variable]:(A.colptr[variable + 1] - 1)
                push!(rows, A.rowval[position])
                push!(columns, basis_column)
                push!(values, A.nzval[position])
            end
        else
            push!(rows, variable - column_count)
            push!(columns, basis_column)
            push!(values, -1.0)
        end
    end
    return sparse(rows, columns, values, row_count, row_count)
end

function independent_refinement(workspace, B, factor, bits)
    return setprecision(BigFloat, bits) do
        rhs_float = workspace.costs[workspace.basis.basic_indices]
        rhs = BigFloat.(rhs_float)
        values = BigFloat.(B.nzval)
        dual = BigFloat.(transpose(factor) \ rhs_float)
        residual = similar(rhs)
        scale = max(BigFloat(1), maximum(abs, rhs))
        target = BigFloat(10)^(-(bits == 256 ? 40 : 90))
        for correction in 0:80
            for column in eachindex(rhs)
                total = BigFloat(0)
                for position in B.colptr[column]:(B.colptr[column + 1] - 1)
                    total += values[position] * dual[B.rowval[position]]
                end
                residual[column] = total - rhs[column]
            end
            error = maximum(abs, residual) / scale
            if correction <= 4 || correction % 8 == 0 || error <= target
                println("REFINE bits=", bits, " correction=", correction,
                        " relative_residual=", error, " target=", target)
                flush(stdout)
            end
            if !isfinite(error)
                return (prices=nothing, corrections=correction, reason="nonfinite residual")
            elseif error <= target
                A = workspace.problem.A
                row_count, column_count = size(A)
                matrix_values = BigFloat.(A.nzval)
                prices = Vector{BigFloat}(undef, column_count + row_count)
                for column in 1:column_count
                    total = BigFloat(0)
                    for position in A.colptr[column]:(A.colptr[column + 1] - 1)
                        total += matrix_values[position] * dual[A.rowval[position]]
                    end
                    prices[column] = BigFloat(workspace.costs[column]) - total
                end
                for row in 1:row_count
                    prices[column_count + row] =
                        BigFloat(workspace.costs[column_count + row]) + dual[row]
                end
                return (prices=prices, corrections=correction, reason="converged")
            elseif correction == 80
                return (prices=nothing, corrections=correction, reason="correction limit")
            end
            step = transpose(factor) \ Float64.(residual)
            if !all(isfinite, step)
                return (prices=nothing, corrections=correction, reason="nonfinite Float64 correction")
            end
            dual .-= BigFloat.(step)
        end
    end
end

function audit_dual_loss(workspace)
    println("AUDIT_START iteration=", workspace.iterations,
            " refactorizations=", workspace.refactorizations,
            " updates=", length(workspace.factorization.updates),
            " perturbed=", workspace.perturbed)
    report_prices(workspace, "stored_Float64", workspace.reduced_costs)
    B = independent_basis(workspace)
    factor = try
        lu(B)
    catch exception
        println("AUDIT_LU_FAILURE type=", typeof(exception),
                " message=", sprint(showerror, exception))
        println("AUDIT_END")
        flush(stdout)
        return
    end
    println("AUDIT_LU_SUCCESS min_abs_U_diagonal=", minimum(abs, diag(factor.U)))
    results = Dict{Int,Any}()
    for bits in (256, 512)
        result = independent_refinement(workspace, B, factor, bits)
        results[bits] = result
        println("REFINE_END bits=", bits, " corrections=", result.corrections,
                " reason=", result.reason,
                " production_limit_32_sufficient=", result.corrections <= 32)
        isnothing(result.prices) || report_prices(workspace, "BigFloat_$(bits)", result.prices)
    end
    low, high = results[256].prices, results[512].prices
    if !isnothing(low) && !isnothing(high)
        gap, index = setprecision(BigFloat, 512) do
            findmax(abs.(low .- high))
        end
        println("PRECISION_AGREEMENT max_gap=", gap, " index=", index,
                " allowed=", BigFloat(workspace.options.dual_tolerance) / 8)
        converted = Float64.(high)
        report_prices(workspace, "refined_Float64", converted)
    end
    println("PRODUCTION_REFINE_ACCEPTED=",
            J._try_refine_dual_prices!(workspace, () -> false))
    println("AUDIT_END")
    flush(stdout)
end

function save_failure_snapshot(workspace;
                               path=get(ENV, "RUNTIME_SNAPSHOT_PATH",
                                        joinpath(@__DIR__, "runtime_reduced_failure_state.tsv")),
                               announce=true)
    basis_row = zeros(Int, length(workspace.basis.states))
    for (row, index) in enumerate(workspace.basis.basic_indices)
        basis_row[index] = row
    end
    open(path, "w") do output
        println(output, "index\tbasis_row\tstate\tcost\treduced_cost\tprimal")
        for index in eachindex(basis_row)
            println(output, index, '\t', basis_row[index], '\t',
                    workspace.basis.states[index], '\t',
                    repr(workspace.costs[index]), '\t',
                    repr(workspace.reduced_costs[index]), '\t',
                    repr(workspace.primal[index]))
        end
    end
    if announce
        println("FAILURE_SNAPSHOT path=", path, " variables=", length(basis_row))
        flush(stdout)
    end
end

function independent_dual_summary(workspace)
    B = J.basis_matrix(workspace)
    factor = lu(B)
    prices = J._refined_dual_prices(workspace, factor, B, 256, () -> false)
    isnothing(prices) && return nothing
    tolerance = BigFloat(workspace.options.dual_tolerance)
    worst = zero(BigFloat)
    worst_index = 0
    count = 0
    total = zero(BigFloat)
    for index in eachindex(prices)
        violation = price_violation(workspace, index, prices[index])
        isfinite(violation) || return nothing
        if violation > tolerance
            count += 1
            total += violation
            if violation > worst
                worst = violation
                worst_index = index
            end
        end
    end
    if count > 0
        high = J._refined_dual_prices(workspace, factor, B, 512, () -> false)
        isnothing(high) && return nothing
        maximum(abs.(prices .- high)) <= tolerance / 8 || return nothing
        price_violation(workspace, worst_index, high[worst_index]) > tolerance ||
            return nothing
    end
    return (count=count, total=total, worst_index=worst_index, worst=worst)
end

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
    trace_start = parse(Int, get(ENV, "RUNTIME_TRACE_START", "29647"))
    trace_end = parse(Int, get(ENV, "RUNTIME_TRACE_END", "29675"))
    capture_start = parse(Int, get(ENV, "RUNTIME_CAPTURE_START", "0"))
    capture_end = parse(Int, get(ENV, "RUNTIME_CAPTURE_END", "0"))
    capture_start == 0 || (0 < capture_start <= capture_end) ||
        error("RUNTIME_CAPTURE_START and RUNTIME_CAPTURE_END must define a positive range")
    capture_paths = (
        get(ENV, "RUNTIME_CAPTURE_PATH_A", joinpath(@__DIR__, "runtime_reduced_capture_a.tsv")),
        get(ENV, "RUNTIME_CAPTURE_PATH_B", joinpath(@__DIR__, "runtime_reduced_capture_b.tsv")),
    )
    capture_paths[1] != capture_paths[2] || error("capture paths must differ")
    capture_count = Ref(0)
    last_capture = Ref(-1)
    scan_start = parse(Int, get(ENV, "RUNTIME_SCAN_START", "29647"))
    scan_interval = parse(Int, get(ENV, "RUNTIME_SCAN_INTERVAL", "1"))
    scan_start == 0 || (scan_start > 0 && scan_interval > 0) ||
        error("RUNTIME_SCAN_START and RUNTIME_SCAN_INTERVAL must be positive")
    scan_paths = (
        get(ENV, "RUNTIME_SCAN_GOOD_PATH", joinpath(@__DIR__, "runtime_reduced_scan_good.tsv")),
        get(ENV, "RUNTIME_SCAN_BAD_PATH", joinpath(@__DIR__, "runtime_reduced_scan_bad.tsv")),
    )
    scan_paths[1] != scan_paths[2] || error("scan paths must differ")
    last_scan = Ref(-1)
    scan_count = Ref(0)
    watched = parse(Int, get(ENV, "RUNTIME_WATCH_VARIABLE", "46746"))
    watched_2 = parse(Int, get(ENV, "RUNTIME_WATCH_VARIABLE_2", "16925"))
    1 <= watched <= length(workspace.basis.states) ||
        error("RUNTIME_WATCH_VARIABLE is outside the working variable range")
    1 <= watched_2 <= length(workspace.basis.states) ||
        error("RUNTIME_WATCH_VARIABLE_2 is outside the working variable range")
    println("DIAGNOSTIC_CONFIG source=", @__FILE__,
            " trace=", (trace_start, trace_end),
            " capture=", (capture_start, capture_end),
            " scan=", (scan_start, scan_interval),
            " watch=", (watched, watched_2),
            " capture_paths=", capture_paths,
            " scan_paths=", scan_paths)
    flush(stdout)
    last_trace = Ref(-1)
    previous_basic = Ref{Union{Nothing,Vector{Int}}}(nothing)
    function stop()
        iteration = workspace.iterations
        if scan_start > 0 && iteration >= scan_start &&
           (iteration - scan_start) % scan_interval == 0 && iteration != last_scan[]
            last_scan[] = iteration
            scan_count[] += 1
            stored = J.dual_infeasibility_summary(workspace)
            if stored[1] > workspace.options.dual_tolerance
                println("INDEPENDENT_SCAN_SKIPPED iteration=", iteration,
                        " stored=", stored)
                flush(stdout)
            else
                summary = try
                    independent_dual_summary(workspace)
                catch exception
                    J._is_numerical_exception(exception) || rethrow()
                    nothing
                end
                if isnothing(summary) || summary.count > 0
                    save_failure_snapshot(workspace; path=scan_paths[2], announce=false)
                    println("INDEPENDENT_SCAN_STOP iteration=", iteration,
                            " refactorizations=", workspace.refactorizations,
                            " updates=", length(workspace.factorization.updates),
                            " stored=", stored,
                            " refined=", summary,
                            " path=", scan_paths[2])
                    flush(stdout)
                    return true
                end
                save_failure_snapshot(workspace; path=scan_paths[1], announce=false)
                println("INDEPENDENT_SCAN iteration=", iteration,
                        " refactorizations=", workspace.refactorizations,
                        " updates=", length(workspace.factorization.updates),
                        " stored=", stored,
                        " refined=", summary,
                        " path=", scan_paths[1])
                flush(stdout)
            end
        end
        if capture_start > 0 && capture_start <= iteration <= capture_end &&
           iteration != last_capture[] &&
           J.dual_infeasibility(workspace) <= workspace.options.dual_tolerance
            slot = mod1(capture_count[] + 1, 2)
            save_failure_snapshot(workspace; path=capture_paths[slot], announce=false)
            capture_count[] += 1
            last_capture[] = iteration
            println("STORED_FEASIBLE_SNAPSHOT iteration=", iteration,
                    " path=", capture_paths[slot],
                    " refactorizations=", workspace.refactorizations,
                    " updates=", length(workspace.factorization.updates))
            flush(stdout)
        end
        if trace_start <= iteration <= trace_end && iteration != last_trace[]
            basic = workspace.basis.basic_indices
            changes = isnothing(previous_basic[]) ? Int[] :
                findall(previous_basic[] .!= basic)
            pivot = length(changes) == 1 ?
                (changes[1], previous_basic[][changes[1]], basic[changes[1]]) : changes
            println("TRACE iteration=", iteration,
                    " refactorizations=", workspace.refactorizations,
                    " updates=", length(workspace.factorization.updates),
                    " pivot=", pivot,
                    " dinf=", J.dual_infeasibility_summary(workspace),
                    " watch_index=", watched,
                    " watch_state=", workspace.basis.states[watched],
                    " watch_rc=", workspace.reduced_costs[watched],
                    " watch_cost=", workspace.costs[watched],
                    " watch_primal=", workspace.primal[watched],
                    " watch2_index=", watched_2,
                    " watch2_state=", workspace.basis.states[watched_2],
                    " watch2_rc=", workspace.reduced_costs[watched_2],
                    " watch2_cost=", workspace.costs[watched_2],
                    " watch2_primal=", workspace.primal[watched_2],
                    " perturbed=", workspace.perturbed)
            flush(stdout)
            previous_basic[] = copy(basic)
            last_trace[] = iteration
        end
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
    println("CAPTURE_SUMMARY count=", capture_count[],
            " last_iteration=", last_capture[])
    println("SCAN_SUMMARY count=", scan_count[], " last_iteration=", last_scan[])
    flush(stdout)
    if terminal.status == J.NUMERICAL_ERROR && terminal.message == "dual feasibility lost"
        save_failure_snapshot(workspace)
        audit_dual_loss(workspace)
    elseif get(ENV, "RUNTIME_AUDIT_AT_END", "0") == "1"
        save_failure_snapshot(workspace)
        audit_dual_loss(workspace)
    end
end

abspath(PROGRAM_FILE) == abspath(@__FILE__) && main()
