include(joinpath(@__DIR__, "runtime_snapshot_audit.jl"))

function refined_transpose(B, factor, rhs_float; bits=512)
    return setprecision(BigFloat, bits) do
        rhs = BigFloat.(rhs_float)
        dual = BigFloat.(transpose(factor) \ rhs_float)
        values = BigFloat.(B.nzval)
        residual = similar(rhs)
        scale = max(BigFloat(1), maximum(abs, rhs))
        for correction in 0:80
            for column in eachindex(rhs)
                total = BigFloat(0)
                for p in B.colptr[column]:(B.colptr[column + 1] - 1)
                    total += values[p] * dual[B.rowval[p]]
                end
                residual[column] = total - rhs[column]
            end
            relative_error = maximum(abs, residual) / scale
            if relative_error <= BigFloat("1e-90")
                println("SOLVE rhs_nonzero=", count(x -> x != 0, rhs_float),
                        " corrections=", correction, " relative_residual=", relative_error)
                return dual
            end
            correction == 80 && error("refinement did not converge")
            step = transpose(factor) \ Float64.(residual)
            all(isfinite, step) || error("nonfinite correction")
            dual .-= BigFloat.(step)
        end
    end
end

function column_dot(workspace, dual, index)
    A = workspace.problem.A
    _, n = size(A)
    if index <= n
        total = BigFloat(0)
        for p in A.colptr[index]:(A.colptr[index + 1] - 1)
            total += BigFloat(A.nzval[p]) * dual[A.rowval[p]]
        end
        return total
    end
    return -dual[index - n]
end

function price(workspace, dual, index)
    return BigFloat(workspace.costs[index]) - column_dot(workspace, dual, index)
end

function main_pivot_audit()
    w = load_snapshot()
    row, leaving, entering, watched = 14482, 46097, 26904, 24212
    println("PIVOT row=", row, " leaving=", leaving, " entering=", entering,
            " watched=", watched)
    println("SAVED_FINAL entry=", w.basis.basic_indices[row],
            " state_leaving=", w.basis.states[leaving],
            " state_watched=", w.basis.states[watched])
    w.basis.basic_indices[row] == entering || error("snapshot does not match logged pivot")
    println("COSTS leaving=", w.costs[leaving], " entering=", w.costs[entering],
            " watched=", w.costs[watched],
            " base_entering=", w.problem.objective[entering])
    println("BOUNDS entering=", w.lower[entering], ",", w.upper[entering],
            " leaving=", w.lower[leaving], ",", w.upper[leaving],
            " watched=", w.lower[watched], ",", w.upper[watched])
    w.basis.basic_indices[row] = leaving
    w.basis.states[leaving] = J.BASIC
    w.basis.states[entering] = J.AT_LOWER
    B = independent_basis(w)
    factor = lu(B)
    println("OLD_LU min_abs_U_diagonal=", minimum(abs, diag(factor.U)))
    dual = refined_transpose(B, factor, w.costs[w.basis.basic_indices])
    unit = zeros(Float64, size(B, 1))
    unit[row] = 1.0
    rho = refined_transpose(B, factor, unit)
    for index in (leaving, entering, watched)
        println("OLD_VARIABLE index=", index,
                " price=", price(w, dual, index),
                " tableau=", column_dot(w, rho, index))
    end
    old_enter = price(w, dual, entering)
    old_watched = price(w, dual, watched)
    pivot = column_dot(w, rho, entering)
    coeff = column_dot(w, rho, watched)
    dual_step = old_enter / pivot
    predicted = old_watched - dual_step * coeff
    println("PREDICTION dual_step=", dual_step,
            " entering_breakpoint=", abs(dual_step),
            " watched_breakpoint_if_prior_upper=", abs(old_watched / coeff),
            " predicted_watched_price=", predicted,
            " saved_float_watched_price=", w.reduced_costs[watched])
end

main_pivot_audit()
