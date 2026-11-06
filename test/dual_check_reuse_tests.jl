module DualCheckReuseTests

using JSimplex, SparseArrays, Test
const JS = JSimplex
const managers = (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub, :huangfu_hall)
deadline() = JS._guard_stop_callback(JS._SolveDeadline(time_ns(), Inf))
budget_stop(ws, stop) = JS._guard_stop_callback(JS._BasisBudgetStop(JS.SimplexRunBudget(ws), ws, stop))

function workspace(manager; T=Float64, observer=nothing, policy=nothing, kwargs...)
    lp = LinearProblem(sparse(T[1 0; 0 1]), T[1,10]; row_lower=T[1,-Inf])
    options = SolverOptions(T; algorithm=:dual, pricing=:devex, basis_update=manager,
        simplex_strategy=:legacy, presolve=false, scaling=:off, verbose=false, kwargs...)
    diagnostics = isnothing(observer) ? nothing : JS.SimplexDiagnostics(; observer)
    progress = JS.SimplexProgressContext(lp; diagnostics,
        numerical_policy=isnothing(policy) ? JS.NumericalPolicy(T, options) : policy)
    return JS.initialize_workspace(lp, options; progress)
end

@testset "Corrected BTRAN and finite state across a completed dual pivot" begin
    for manager in managers
        w = workspace(manager)
        # The actual basis is -I. This stale factor requires a row correction.
        stale = sparse([-1.0 1e-5; 0.0 -1.0])
        w.factorization = JS._basis_factorization(stale, Val(manager), Val(:native))
        stop = budget_stop(w, budget_stop(w, deadline()))
        @test JS._can_reuse_dual_entry_validation(w, stop)
        @test JS._dual_optimize!(w, stop).status == OPTIMAL
        @test w.iterations == 1 && w.refactorizations == 0
        @test w.basis.basic_indices == [1,4] && w.primal[1] ≈ 1.0
        @test JS._finite_workspace(w)

        # Changing a finite rho *after* its correction was accepted invalidates
        # the row result. The original second residual must force a rebuild.
        modified = Ref(false)
        observed = workspace(manager; observer=(event, state)->begin
            if event == :correction && !modified[]
                state.scratch.rho[1] = 0.0
                modified[] = true
            end
        end)
        observed.factorization = JS._basis_factorization(stale, Val(manager), Val(:native))
        @test !JS._can_reuse_dual_checks(observed, deadline())
        @test JS._dual_optimize!(observed, deadline()).status == OPTIMAL
        @test modified[] && observed.refactorizations > 0
        @test observed.primal == w.primal

        # Commit observers run after the weight check but before the post-pivot check.
        observed = workspace(manager; observer=(event, state)->begin
            event == :pivot_completed && (state.pricing_weights[1] = 0.0)
        end)
        @test JS.dual_iteration!(observed, deadline()).status == NUMERICAL_ERROR
        @test observed.iterations == 1
    end
end

@testset "Budget wrappers preserve cancellation, exceptions and mutating callbacks" begin
    for field in (:costs, :reduced_costs, :primal, :pricing_weights)
        ws = workspace(:pfi)
        mutate = () -> begin
            if ws.iterations > 0
                getproperty(ws,field)[1] = field == :pricing_weights ? -1.0 : NaN
            end
            return false
        end
        stop = budget_stop(ws, budget_stop(ws, JS._guard_stop_callback(mutate)))
        @test !JS._can_reuse_dual_entry_validation(ws, stop)
        @test JS._dual_optimize!(ws, stop).status == NUMERICAL_ERROR
    end
    ws = workspace(:pfi)
    budget = JS.SimplexRunBudget(ws)
    budget.time_limit_seconds = 0.0
    stop = JS._guard_stop_callback(JS._BasisBudgetStop(budget, ws, ()->error("expired budget called its parent")))
    @test JS._dual_optimize!(ws, stop).status == TIME_LIMIT
    @test ws.iterations == 0

    failure = ErrorException("stop callback")
    stop = budget_stop(ws, JS._guard_stop_callback(()->throw(failure)))
    @test_throws failure JS._dual_optimize!(ws, stop)
    @test stop.exception === failure
end

@testset "Full checks on unverified paths and after rebuilding" begin
    w = workspace(:forrest_tomlin)
    row, rho, values = w.scratch.tableau_row, w.scratch.rho, w.problem.A.nzval
    @test JS._can_reuse_corrected_row(w, deadline(), row, rho)
    for (out, multiplier) in ((rho,rho), (values,rho), (row,values))
        @test !JS._can_reuse_corrected_row(w, deadline(), out, multiplier)
    end
    for ws in (workspace(:pfi; T=Float32), workspace(:pfi; basis_refactorization=:markowitz),
               workspace(:pfi; simplex_strategy=:adaptive), workspace(:pfi; partial_pricing=true),
               workspace(:pfi; policy=JS.NumericalPolicy(Float64; solve_refinement=true)))
        @test !JS._can_reuse_dual_checks(ws, deadline())
    end

    ws = workspace(:pfi)
    ws.primal[1] = Inf
    @test JS._dual_after_iteration!(ws, deadline(), 0.0, false, false, 1).status == NUMERICAL_ERROR

    # Publishing the finite upper bound zero into primal must still fail the
    # positive-weight check when a caller made these two buffers overlap.
    lp = LinearProblem(sparse(reshape([-1.0],1,1)), [1.0]; row_upper=[0.0])
    alias_ws = JS.initialize_workspace(lp, ws.options)
    alias_ws.primal .= 1.0
    alias_ws.pricing_weights = alias_ws.primal
    @test JS._finite_workspace(alias_ws)
    @test JS.dual_iteration!(alias_ws, deadline()).status == NUMERICAL_ERROR
    @test alias_ws.iterations == 1 && alias_ws.pricing_weights[2] == 0

    # A rebuild invalidates the prior check of *all* fields, even when only
    # a finite primal entry was written during pivot publication.
    ws = workspace(:pfi; refactorization_interval=1)
    JS.replace_column!(ws.factorization, [1.0,0.0], 1)
    ws.costs[1] = NaN
    @test JS._dual_after_iteration!(ws, deadline(), 0.0, false, false, 1).status == NUMERICAL_ERROR
    @test ws.refactorizations == 1
end
end
