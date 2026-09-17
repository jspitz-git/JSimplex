using JSimplex, LinearAlgebra, SparseArrays
const J = JSimplex
const TARGETS = (22_206, 22_232, 22_233, 22_256)
const WATCHED = (19_825, 19_826, 50_165, 57_787)
const MAX_CORRECTIONS = 80

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

# The callback only copies state. All factorization and BigFloat work happens
# after the simplex has terminated, and never calls basis_matrix or recompute!.
workspace = J.initialize_workspace(problem, options)
println("factor=", typeof(workspace.factorization),
        " backend=", typeof(workspace.factorization.base))
snapshots = Dict{Int, Any}()
pivots = Tuple{Int, Int, Int, Int}[]
previous_basic = Ref{Any}(nothing)
last_seen = Ref(-1)
function stop()
    i = workspace.iterations
    # Iteration 22206 has a regular refactorization: use its completed state.
    i == 22_206 && !isempty(workspace.factorization.updates) && return false
    if 22_206 <= i <= 22_256 && i != last_seen[]
        basic = copy(workspace.basis.basic_indices)
        if i > 22_206
            changed = findall(previous_basic[] .!= basic)
            length(changed) == 1 || error("unexpected pivot at $i: $changed")
            row = only(changed)
            push!(pivots, (i, row, previous_basic[][row], basic[row]))
        end
        if i in TARGETS
            snapshots[i] = (basic=basic, states=copy(workspace.basis.states),
                            costs=copy(workspace.costs),
                            stored_rc=copy(workspace.reduced_costs),
                            updates=length(workspace.factorization.updates))
            println("SNAPSHOT iteration=", i, " updates=", snapshots[i].updates)
            flush(stdout)
        end
        previous_basic[] = basic
        last_seen[] = i
    end
    return false
end
terminal = J.make_dual_feasible!(workspace, stop)
isnothing(terminal) && (terminal = J._dual_optimize!(workspace, stop))
println("END status=", terminal.status, " message=", terminal.message,
        " iterations=", workspace.iterations,
        " refactorizations=", workspace.refactorizations,
        " pivot_count=", length(pivots))
for pivot in pivots
    println("PIVOT iteration=", pivot[1], " row=", pivot[2],
            " leave=", pivot[3], " enter=", pivot[4])
end
flush(stdout)
Set(keys(snapshots)) == Set(TARGETS) || error("missing snapshots")
length(pivots) == 50 || error("missing pivots")
terminal.status == J.NUMERICAL_ERROR || error("unexpected terminal status")
workspace.iterations == 22_256 || error("unexpected terminal iteration")

# Construct B independently from the captured basic indices. Slack columns
# have coefficient -1 in JSimplex's Ax - s = 0 convention.
function independent_basis(A::SparseMatrixCSC{Float64,Int}, basic::Vector{Int})
    m, n = size(A)
    rows, columns, values = Int[], Int[], Float64[]
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

function refine_transpose(B, factor, rhs_float, bits, iteration, kind)
    setprecision(BigFloat, bits) do
        big_values = BigFloat.(B.nzval)
        rhs = BigFloat.(rhs_float)
        solution = BigFloat.(transpose(factor) \ rhs_float)
        residual = similar(rhs)
        scale = max(BigFloat(1), maximum(abs, rhs))
        target = BigFloat(10)^(-(bits == 256 ? 40 : 90))
        converged = false
        for step in 0:MAX_CORRECTIONS
            absolute = transpose_residual!(residual, B, big_values, solution, rhs)
            relative = absolute / scale
            println("REFINE iteration=", iteration, " kind=", kind,
                    " bits=", bits, " step=", step,
                    " abs_res=", absolute, " rel_res=", relative)
            if relative <= target
                converged = true
                break
            end
            step == MAX_CORRECTIONS && break
            correction = transpose(factor) \ Float64.(residual)
            all(isfinite, correction) || break
            solution .-= BigFloat.(correction)
        end
        println("REFINE_END iteration=", iteration, " kind=", kind,
                " bits=", bits, " converged=", converged,
                " target=", target)
        flush(stdout)
        return solution, converged
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

function report_prices(iteration, bits, snapshot, prices)
    setprecision(BigFloat, bits) do
        tolerance = BigFloat(options.dual_tolerance)
        bad = Int[]
        for i in eachindex(prices)
            state = snapshot.states[i]
            state == J.BASIC && continue
            J._is_fixed(workspace.lower[i], workspace.upper[i]) && continue
            violation = state == J.AT_LOWER ? max(-prices[i], BigFloat(0)) :
                        state == J.AT_UPPER ? max(prices[i], BigFloat(0)) : abs(prices[i])
            if violation > tolerance
                push!(bad, i)
                println("BAD iteration=", iteration, " bits=", bits,
                        " index=", i, " state=", state,
                        " cost=", snapshot.costs[i], " rc=", prices[i],
                        " violation=", violation)
            end
        end
        for i in WATCHED
            println("WATCH iteration=", iteration, " bits=", bits,
                    " index=", i, " state=", snapshot.states[i],
                    " cost=", snapshot.costs[i],
                    " stored_rc=", snapshot.stored_rc[i],
                    " refined_rc=", prices[i])
        end
        println("BAD_SUMMARY iteration=", iteration, " bits=", bits,
                " count=", length(bad), " indices=", bad)
        flush(stdout)
        return bad
    end
end

function report_float64_prices(iteration, snapshot, A, factor)
    m, n = size(A)
    dual = transpose(factor) \ snapshot.costs[snapshot.basic]
    prices = vcat(snapshot.costs[1:n] - transpose(A) * dual,
                  snapshot.costs[(n+1):(n+m)] + dual)
    bad = Int[]
    for i in eachindex(prices)
        state = snapshot.states[i]
        state == J.BASIC && continue
        J._is_fixed(workspace.lower[i], workspace.upper[i]) && continue
        violation = state == J.AT_LOWER ? max(-prices[i], 0.0) :
                    state == J.AT_UPPER ? max(prices[i], 0.0) : abs(prices[i])
        violation > options.dual_tolerance && push!(bad, i)
    end
    for i in WATCHED
        println("FLOAT64_WATCH iteration=", iteration, " index=", i,
                " state=", snapshot.states[i], " rc=", prices[i])
    end
    println("FLOAT64_BAD iteration=", iteration, " count=", length(bad),
            " indices=", bad)
    flush(stdout)
end

function tableau_coefficients(A, row_solution, indices, bits)
    setprecision(BigFloat, bits) do
        n = size(A, 2)
        values = BigFloat.(A.nzval)
        result = Dict{Int,BigFloat}()
        for i in indices
            if i <= n
                sum = BigFloat(0)
                for p in A.colptr[i]:(A.colptr[i+1]-1)
                    sum += values[p] * row_solution[A.rowval[p]]
                end
                result[i] = sum
            else
                result[i] = -row_solution[i-n]
            end
        end
        return result
    end
end

results = Dict{Tuple{Int,Int},Any}()
for iteration in TARGETS
    snapshot = snapshots[iteration]
    B = independent_basis(problem.A, snapshot.basic)
    factor = lu(B)                 # independent, fresh Float64 sparse LU
    cB = snapshot.costs[snapshot.basic]
    println("BASIS iteration=", iteration, " size=", size(B),
            " nnz=", nnz(B), " factor=", typeof(factor))
    flush(stdout)
    report_float64_prices(iteration, snapshot, problem.A, factor)
    for bits in (256, 512)
        dual, converged = refine_transpose(B, factor, cB, bits, iteration, "dual")
        prices = reduced_prices(problem.A, snapshot.costs, dual, bits)
        bad = report_prices(iteration, bits, snapshot, prices)
        results[(iteration,bits)] = (bad=bad, watched=prices[collect(WATCHED)],
                                    converged=converged)
        if iteration == 22_232
            unit = zeros(Float64, size(B, 1))
            unit[9_223] = 1.0
            rho, row_converged = refine_transpose(B, factor, unit, bits,
                                                  iteration, "tableau_row_9223")
            coefficients = tableau_coefficients(problem.A, rho,
                                                (WATCHED..., 1_408), bits)
            for i in (WATCHED..., 1_408)
                println("TABLEAU iteration=", iteration, " bits=", bits,
                        " row=9223 index=", i, " coefficient=", coefficients[i])
            end
            println("TABLEAU_END iteration=", iteration, " bits=", bits,
                    " converged=", row_converged)
        end
        flush(stdout)
    end
    lo, hi = results[(iteration,256)], results[(iteration,512)]
    signs_match = all(sign(lo.watched[j]) == sign(hi.watched[j])
                      for j in eachindex(lo.watched))
    println("COMPARE_PRECISION iteration=", iteration,
            " both_converged=", lo.converged && hi.converged,
            " same_bad_indices=", lo.bad == hi.bad,
            " watched_signs_match=", signs_match)
    flush(stdout)
end
