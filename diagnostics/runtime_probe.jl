using JSimplex, LinearAlgebra, SparseArrays, Printf
const J = JSimplex

path = get(ENV, "RUNTIME_MPS", raw"C:\Disk_D\tmp\runtime.mps")
options = SolverOptions(iteration_limit=100_000, time_limit=6000.0,
    basis_update=:suhl_suhl, basis_refactorization=:native,
    refactorization_interval=50, verbose=false)
println("Julia=", VERSION, " machine=", Sys.MACHINE, " threads=", Threads.nthreads())
println("commit=c666364+ path=", path, " bytes=", filesize(path))
flush(stdout)
original = read_mps(path)
reduced = J.presolve_problem(J.relax_integrality(original))
reduced isa J.PresolveFailure && error("presolve failed: $reduced")
scaled, scaling = J.scale_problem(reduced.problem)
problem = J._minimization_problem(scaled)
println("original=", size(original.A), " nnz=", nnz(original.A),
        " reduced=", size(reduced.problem.A), " nnz=", nnz(reduced.problem.A),
        " scaled=", size(problem.A), " nnz=", nnz(problem.A))
flush(stdout)
w = J.initialize_workspace(problem, options)
println("factor=", typeof(w.factorization), " backend=", typeof(w.factorization.base))
const watched = (19825, 19826, 50165, 57787)

function violations(w)
    out = []
    for i in eachindex(w.basis.states)
        state = w.basis.states[i]
        state == J.BASIC && continue
        J._is_fixed(w.lower[i], w.upper[i]) && continue
        rc = w.reduced_costs[i]
        bad = state == J.AT_LOWER ? rc < -w.options.dual_tolerance :
              state == J.AT_UPPER ? rc > w.options.dual_tolerance :
              abs(rc) > w.options.dual_tolerance
        bad && push!(out, (i, state, rc, w.costs[i],
                           i <= size(w.problem.A, 2) ? w.problem.objective[i] : 0.0))
    end
    return out
end

function snapshot(w, label; pivot=false)
    dinf = J.dual_infeasibility_summary(w)
    pinf = J.primal_infeasibility_summary(w)
    println("SNAP ", label, " iter=", w.iterations, " updates=", length(w.factorization.updates),
            " refact=", w.refactorizations, " dinf=", dinf, " pinf=", pinf,
            " perturbed=", w.perturbed)
    bad = violations(w)
    for v in bad
        println("BAD index=", v[1], " state=", v[2], " rc=", repr(v[3]),
                " cost=", repr(v[4]), " original_scaled_cost=", repr(v[5]))
    end
    B = J.basis_matrix(w)
    n = size(w.problem.A, 2)
    x = w.primal
    primal_res = w.problem.A * view(x, 1:n) - view(x, n+1:length(x))
    y = J.transpose_solve(w.factorization, w.costs[w.basis.basic_indices])
    dual_res = transpose(B) * y - w.costs[w.basis.basic_indices]
    println("RESIDUAL Bx=b inf=", norm(primal_res, Inf),
            " Bty=cB inf=", norm(dual_res, Inf),
            " x_inf=", norm(x, Inf), " y_inf=", norm(y, Inf))
    if w.iterations >= 22255
        for i in watched
            direct_rc = i <= n ? w.costs[i] - dot(w.problem.A[:, i], y) :
                                   w.costs[i] + y[i-n]
            println("WATCH index=", i, " state=", w.basis.states[i],
                    " stored_rc=", repr(w.reduced_costs[i]),
                    " recomputed_rc=", repr(direct_rc),
                    " perturbed_cost=", repr(w.costs[i]),
                    " x=", repr(x[i]), " lower=", repr(w.lower[i]),
                    " upper=", repr(w.upper[i]))
        end
        if label == "before_refactor"
            fresh_y = transpose(B) \ w.costs[w.basis.basic_indices]
            println("FRESH_Y_DIFF inf=", norm(y - fresh_y, Inf),
                    " fresh_Bty_res=", norm(transpose(B)*fresh_y - w.costs[w.basis.basic_indices], Inf))
            for i in watched
                fresh_rc = i <= n ? w.costs[i] - dot(w.problem.A[:, i], fresh_y) :
                                      w.costs[i] + fresh_y[i-n]
                println("FRESH_RC index=", i, " rc=", repr(fresh_rc))
            end
        end
    end
    if pivot
        row = J.dual_edge_selection(w)
        if row > 0
            leave = w.basis.basic_indices[row]
            below = J._lower_violation(w.lower[leave], x[leave]) > 0
            bound = below ? w.lower[leave] : w.upper[leave]
            delta = x[leave] - J.bound_value(bound)
            unit = zeros(length(w.basis.basic_indices)); unit[row] = 1
            rho = J.transpose_solve(w.factorization, unit)
            trow = zeros(length(x)); J.price!(trow, w, rho)
            orientation = below ? -1.0 : 1.0
            enter, flips, exhausted = J._bound_flipping_ratio_test(w, trow, orientation, abs(delta))
            println("PIVOT row=", row, " leave=", leave, " below=", below,
                    " delta=", delta, " enter=", enter,
                    " flips=", flips, " exhausted=", exhausted)
            if w.iterations >= 22255
                for i in vcat(flips, enter > 0 ? [enter] : Int[])
                    coeff = orientation*trow[i]
                    width = isfinite(w.lower[i]) && isfinite(w.upper[i]) ?
                        J.bound_value(w.upper[i]) - J.bound_value(w.lower[i]) : Inf
                    println("RATIO index=", i, " state=", w.basis.states[i],
                            " rc=", repr(w.reduced_costs[i]), " coeff=", repr(coeff),
                            " step=", repr(w.reduced_costs[i]/coeff),
                            " width=", repr(width), " gain=", repr(abs(trow[i])*width))
                end
            end
            if enter > 0
                column = enter <= n ? collect(w.problem.A[:, enter]) :
                         [k == enter-n ? -1.0 : 0.0 for k in 1:size(w.problem.A,1)]
                tcol = J.forward_solve(w.factorization, column)
                exactrow = transpose(B) \ unit
                exactcol = B \ column
                step = w.reduced_costs[enter] / trow[enter]
                println("PIVOT_VALUES row=", repr(trow[enter]),
                        " col=", repr(tcol[row]),
                        " direct_row=", repr(dot(exactrow,column)),
                        " direct_col=", repr(exactcol[row]),
                        " rc=", repr(w.reduced_costs[enter]),
                        " ratio=", repr(step),
                        " primal_step=", repr(delta/tcol[row]))
    end
    return y
end
    end
    flush(stdout)
end

last_iter = Ref(-1)
last_pre = Ref(-1)
function stop()
    i = w.iterations
    if i >= 21800 && i != last_iter[]
        last_iter[] = i
        if i % 25 == 0 || i >= 22240 || J.dual_infeasibility(w) > w.options.dual_tolerance
            snapshot(w, "loop"; pivot=i>=22240)
        end
    end
    if i >= 21800 && length(w.factorization.updates) >= 50 && i != last_pre[]
        last_pre[] = i
        snapshot(w, "before_refactor"; pivot=i>=22240)
    end
    return false
end

terminal = J.make_dual_feasible!(w, stop)
println("make_dual_feasible=", terminal, " iter=", w.iterations)
if isnothing(terminal)
    terminal = J._dual_optimize!(w, stop)
end
snapshot(w, "terminal"; pivot=true)
println("TERMINAL status=", terminal.status, " message=", terminal.message,
        " iterations=", w.iterations, " refactorizations=", w.refactorizations)
