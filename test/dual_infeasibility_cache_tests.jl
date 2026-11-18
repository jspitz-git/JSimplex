module DualInfeasibilityCacheTests
using JSimplex, Test, SparseArrays, LinearAlgebra
const JS = JSimplex
const MANAGERS = (:huangfu_hall, :forrest_tomlin, :suhl_suhl, :bartels_golub, :pfi)
deadline() = JS._StopCallback(JS._SolveDeadline(time_ns(), Inf), nothing)

function pivot_fixture(T, manager; kwargs...)
    problem = LinearProblem(sparse(T[1 1]), T[1, 1]; row_lower=T[1])
    options = SolverOptions(T; algorithm=:dual, simplex_strategy=:legacy,
        basis_update=manager, basis_refactorization=:native, pricing=:devex,
        presolve=false, verbose=false, kwargs...)
    return JS.initialize_workspace(problem, options)
end

@testset "Production dual loop owns and closes its infeasibility cache" begin
    for T in (Float32, Float64), manager in MANAGERS
        w = pivot_fixture(T, manager)
        result = JS._dual_optimize!(w, deadline())
        @test result.status == OPTIMAL
        @test hasproperty(w.scratch, :dual_infeasibility) &&
            !isnothing(w.scratch.dual_infeasibility)
        if hasproperty(w.scratch, :dual_infeasibility_active)
            @test !w.scratch.dual_infeasibility_active
        end
    end
end

function flip_fixture(T, manager; pricing=:devex, kwargs...)
    problem = LinearProblem(sparse(T[1 -1 0 0; 0 0 1 0; 0 0 0 1; 0 0 0 0]),
        zeros(T, 4); row_lower=zeros(T, 4), row_upper=fill(T(10), 4),
        column_lower=zeros(T, 4), column_upper=T[2, 2, 0, 2])
    return JS.initialize_workspace(problem, SolverOptions(T; algorithm=:dual,
        basis_update=manager, basis_refactorization=:native, simplex_strategy=:legacy,
        pricing, presolve=false, verbose=false, kwargs...))
end

# Independent original logical-row traversal. Only scalar score arithmetic is shared.
function original_selection(w::JS.SimplexWorkspace{T}, scoring::Val{S}) where {T,S}
    selected = -1
    best = S === :scaled ? JS._primal_dantzig_score(one(T)) : zero(S)
    weighted = JS._effective_pricing(w, :dual) != :dantzig
    for (row, index) in enumerate(w.basis.basic_indices)
        row in w.scratch.rejected_rows && continue
        violation = max(JS._lower_violation(w.lower[index], w.primal[index]),
                        JS._upper_violation(w.upper[index], w.primal[index]))
        violation > w.options.primal_tolerance || continue
        score = JS._dual_pricing_score(violation, w.pricing_weights[index], weighted, scoring)
        if (S === :scaled && selected == -1) || score > best
            selected, best = row, score
        end
    end
    return selected
end

function check_state(w)
    c = JS._current_dual_infeasibility!(w)
    @test c === w.scratch.dual_infeasibility
    seen = falses(length(c.values))
    for pos in 1:c.count
        row = c.rows[pos]
        @test !seen[row] && c.positions[row] == pos
        seen[row] = true
    end
    for (row, index) in enumerate(w.basis.basic_indices)
        value = max(JS._lower_violation(w.lower[index], w.primal[index]),
                    JS._upper_violation(w.upper[index], w.primal[index]))
        @test isequal(value, c.values[row])
        @test seen[row] == (value > w.options.primal_tolerance) == (c.positions[row] != 0)
    end
    return c
end
same_numerics(a, b) = all(isequal(getproperty(a, k), getproperty(b, k)) for k in
    (:primal, :reduced_costs, :costs, :pricing_weights, :lower, :upper)) &&
    isequal(a.basis.basic_indices, b.basis.basic_indices) && isequal(a.basis.states, b.basis.states)

if isdefined(JS, :_begin_dual_infeasibility!)
    @testset "All native managers, precisions and fixed pricings" begin
        for T in (Float32, Float64), manager in MANAGERS, pricing in (:devex, :steepest_edge, :dantzig)
            w = flip_fixture(T, manager; pricing)
            baseline = flip_fixture(T, manager; pricing)
            @test JS._dual_infeasibility_allowed(w, deadline())
            @test isnothing(w.scratch.dual_infeasibility)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            @test w.scratch.dual_infeasibility_active && !previous
            @test isnothing(w.scratch.dual_infeasibility) # Allocate only on first use.
            for x in (w, baseline), (row, index) in enumerate(x.basis.basic_indices)
                x.primal[index] = -T(row)
            end
            @test JS._dual_edge_selection(w, Val(T)) == original_selection(baseline, Val(T))
            c = check_state(w)
            @test c.values !== w.primal && c.rows !== w.basis.basic_indices
            for flips in ([1], [1], [1, 2], [1, 2], [3], Int[])
                @test JS._apply_bound_flips!(w, flips) == JS._apply_bound_flips!(baseline, flips)
                @test same_numerics(w, baseline)
                @test c.valid
                @test check_state(w) === c
                @test JS._dual_edge_selection(w, Val(T)) == original_selection(baseline, Val(T))
            end
            column = T[1, 0, -1, 0]
            for step in (zero(T), one(T), -one(T))
                JS.update_primals!(w, column, 1, 1, step)
                JS.update_primals!(baseline, column, 1, 1, step)
                @test same_numerics(w, baseline)
                check_state(w)
            end
            JS.recompute!(w; refactorize=true)
            @test !c.valid && JS._dual_infeasibility_allowed(w, deadline())
            check_state(w)
            copy = flip_fixture(T, manager; pricing)
            old_copy_scope = JS._begin_dual_infeasibility!(copy, deadline())
            other = check_state(copy)
            JS._copy_pivot_state!(copy, w)
            @test !other.valid && other !== c
            @test other.values !== c.values && other.rows !== c.rows && other.positions !== c.positions
            check_state(copy)
            @test JS._dual_edge_selection(copy, Val(T)) == original_selection(w, Val(T))
            staged = JS._candidate_workspace(w)
            @test !JS._dual_infeasibility_allowed(staged, deadline())
            @test isnothing(staged.scratch.dual_infeasibility)
            JS._end_dual_infeasibility!(copy, old_copy_scope)
            JS._end_dual_infeasibility!(w, previous)
            @test !c.valid && !w.scratch.dual_infeasibility_active
            @test JS._current_dual_infeasibility!(w) === nothing
        end
    end

    @testset "Original ties, current weights, rejected rows and score extremes" begin
        for T in (Float32, Float64), pricing in (:devex, :steepest_edge, :dantzig)
            w = flip_fixture(T, :pfi; pricing)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            w.primal[w.basis.basic_indices] .= -one(T)
            c = check_state(w)
            for row in (1, 2, 1)
                index = w.basis.basic_indices[row]
                old = w.primal[index]
                w.primal[index] = -one(T) - old
                JS._dual_infeasibility_changed!(c, w, row, index, old)
            end
            @test JS._dual_edge_selection(w, Val(T)) == original_selection(w, Val(T))
            for weights in (fill(one(T), 4), fill(T(Inf), 4), T[NaN, 1, 2, 3], fill(floatmax(T), 4))
                w.pricing_weights[w.basis.basic_indices] .= weights
                for rejected in (Int[], [2], [1, 2, 3, 4])
                    w.scratch.rejected_rows = rejected
                    for scoring in (Val(T), Val(:scaled))
                        @test JS._dual_edge_selection(w, scoring) == original_selection(w, scoring)
                    end
                end
            end
            empty!(w.scratch.rejected_rows)
            index = w.basis.basic_indices[1]
            for value in (T(NaN), T(Inf), -zero(T), zero(T), -w.options.primal_tolerance)
                old = w.primal[index]; w.primal[index] = value
                JS._dual_infeasibility_changed!(c, w, 1, index, old)
                check_state(w)
                @test JS._dual_edge_selection(w, Val(T)) == original_selection(w, Val(T))
            end
            JS._end_dual_infeasibility!(w, previous)
        end
    end

    @testset "Failed flips publish neither state nor cache changes" begin
        for T in (Float32, Float64), manager in MANAGERS
            w = flip_fixture(T, manager)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            c = check_state(w)
            w.problem.A.nzval[1] = floatmax(T)
            primal, values, rows, positions = copy(w.primal), copy(c.values), copy(c.rows[1:c.count]), copy(c.positions)
            @test !JS._apply_bound_flips!(w, [1])
            @test isequal(w.primal, primal) && c.valid
            @test isequal(c.values, values) && c.rows[1:c.count] == rows && c.positions == positions
            JS._end_dual_infeasibility!(w, previous)
        end
    end

    @testset "Invalidation, nested authority and lazy unsupported paths" begin
        for T in (Float32, Float64)
            w = flip_fixture(T, :pfi)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            c = check_state(w)
            index = w.basis.basic_indices[1]
            for field in (:primal, :lower, :upper)
                setproperty!(w, field, copy(getproperty(w, field)))
                if field === :primal
                    w.primal[index] = -T(20)
                elseif field === :lower
                    w.lower[index] = Bound(-one(T))
                else
                    w.upper[index] = Bound(-T(50))
                end
                @test check_state(w) === c
            end
            w.basis = JS.Basis(w.basis.basic_indices, w.basis.states)
            reverse!(w.basis.basic_indices)
            check_state(w)
            opts = (; (key => getfield(w.options, key) for key in fieldnames(typeof(w.options)))...)
            w.options = SolverOptions(T; merge(opts, (primal_tolerance=T(40),))...)
            check_state(w)
            w.primal[w.basis.basic_indices[1]] = -T(100)
            w.refactorizations += 1
            check_state(w)
            inner = JS._begin_dual_infeasibility!(w, () -> false)
            @test inner && !w.scratch.dual_infeasibility_active
            w.primal[w.basis.basic_indices[1]] = -T(3)
            @test isnothing(JS._current_dual_infeasibility!(w))
            JS._end_dual_infeasibility!(w, inner)
            @test w.scratch.dual_infeasibility_active && !c.valid
            check_state(w)
            JS._end_dual_infeasibility!(w, previous)
            for kwargs in ((partial_pricing=true,), (pricing=:auto,), (simplex_strategy=:adaptive,),
                           (basis_refactorization=:markowitz,))
                # Build through a merged NamedTuple so the explicit defaults are unique.
                lp = w.problem
                options = merge((algorithm=:dual, simplex_strategy=:legacy, basis_update=:pfi,
                    basis_refactorization=:native, pricing=:devex, presolve=false, verbose=false), kwargs)
                unsupported = JS.initialize_workspace(lp, SolverOptions(T; options...))
                @test !JS._dual_infeasibility_allowed(unsupported, deadline())
                was_active = JS._begin_dual_infeasibility!(unsupported, deadline())
                @test isnothing(JS._current_dual_infeasibility!(unsupported))
                @test isnothing(unsupported.scratch.dual_infeasibility)
                JS._end_dual_infeasibility!(unsupported, was_active)
            end
            observer = (reason, state) -> nothing
            progress = JS.SimplexProgressContext(w.problem; diagnostics=JS.SimplexDiagnostics(; observer))
            observed = JS.initialize_workspace(w.problem, w.options; progress)
            @test !JS._dual_infeasibility_allowed(observed, deadline())
            @test !JS._dual_infeasibility_allowed(w, () -> false)
        end
        for T in (BigFloat, Rational{BigInt})
            w = flip_fixture(T, :pfi)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            @test !w.scratch.dual_infeasibility_active
            @test Core.Compiler.return_type(JS._current_dual_infeasibility!, Tuple{typeof(w)}) === Nothing
            @test JS._dual_edge_selection(w, Val(T)) == original_selection(w, Val(T))
            @test isnothing(w.scratch.dual_infeasibility)
            JS._end_dual_infeasibility!(w, previous)
        end
    end

    struct ReadOnlyCacheObserver
        fail::Bool
    end
    function (observer::ReadOnlyCacheObserver)(reason, w)
        if reason == :pivot_completed
            check_state(w)
            observer.fail && error("test observer failure")
        end
        return nothing
    end
    # Test-only admission for this read-only observer; arbitrary user observers
    # are rejected by the production default and the tests above.
    JS._dual_infeasibility_observer_safe(::ReadOnlyCacheObserver) = true

    @testset "All loop exits close authority; already feasible states stay lazy" begin
        for T in (Float32, Float64)
            w = flip_fixture(T, :pfi)
            @test JS._dual_optimize!(w, deadline()).status == OPTIMAL
            @test isnothing(w.scratch.dual_infeasibility)
            w = pivot_fixture(T, :pfi)
            stop = JS._StopCallback(JS._SolveDeadline(time_ns(), 0.0), nothing)
            @test JS._dual_optimize!(w, stop).status == TIME_LIMIT
            @test !w.scratch.dual_infeasibility_active && isnothing(w.scratch.dual_infeasibility)
            w = pivot_fixture(T, :pfi)
            w.primal[end] = T(NaN)
            @test JS._dual_optimize!(w, deadline()).status == NUMERICAL_ERROR
            @test !w.scratch.dual_infeasibility_active
            for fail in (false, true)
                p = LinearProblem(sparse(T[1 1]), T[1, 1]; row_lower=T[1])
                o = SolverOptions(T; algorithm=:dual, pricing=:devex, basis_update=:pfi,
                    presolve=false, verbose=false)
                diagnostics = JS.SimplexDiagnostics(observer=ReadOnlyCacheObserver(fail))
                w = JS.initialize_workspace(p, o; progress=JS.SimplexProgressContext(p; diagnostics))
                if fail
                    @test_throws JS.DiagnosticObserverFailure JS._dual_optimize!(w, deadline())
                else
                    @test JS._dual_optimize!(w, deadline()).status == OPTIMAL
                end
                @test !w.scratch.dual_infeasibility_active && !w.scratch.dual_infeasibility.valid
            end
        end
    end

    @testset "DSE to Devex and fixed-pricing whole-loop endpoints" begin
        for T in (Float32, Float64), manager in MANAGERS, pricing in (:devex, :steepest_edge, :dantzig)
            p = LinearProblem(sparse(T[1 0; 0 1]), T[1, 10]; row_lower=T[1, 2])
            o = SolverOptions(T; algorithm=:dual, pricing, basis_update=manager,
                presolve=false, scaling=:off, refactorization_interval=1, verbose=false)
            w, baseline = JS.initialize_workspace(p, o), JS.initialize_workspace(p, o)
            if pricing === :steepest_edge
                w.pricing_weights .= T(1e6)
                baseline.pricing_weights .= T(1e6)
            end
            @test JS._dual_optimize!(w, deadline()).status == OPTIMAL
            @test JS._dual_optimize_loop!(baseline, deadline()).status == OPTIMAL
            @test same_numerics(w, baseline)
            @test w.iterations == baseline.iterations && w.refactorizations == baseline.refactorizations
            @test JS._original_primal_feasible(p, w.primal[1:2], o.primal_tolerance)
            pricing === :steepest_edge && @test w.dual_devex_fallback == baseline.dual_devex_fallback
        end
    end

    function hot_selections(w, count)
        total = 0
        for _ in 1:count
            total += JS._dual_edge_selection(w, Val(eltype(w.primal)))
        end
        return total
    end
    function released_context()
        w = flip_fixture(Float64, :pfi)
        previous = JS._begin_dual_infeasibility!(w, deadline())
        c = JS._current_dual_infeasibility!(w)
        JS._end_dual_infeasibility!(w, previous)
        return WeakRef(w), WeakRef(c)
    end
    @testset "Owned cache has no warmed selection allocations or global retention" begin
        for T in (Float32, Float64), manager in MANAGERS
            w = flip_fixture(T, manager)
            previous = JS._begin_dual_infeasibility!(w, deadline())
            hot_selections(w, 10)
            @allocated hot_selections(w, 100)
            @test (@allocated hot_selections(w, 1000)) == 0
            c = w.scratch.dual_infeasibility
            @test sizeof(c.values) + sizeof(c.rows) + sizeof(c.positions) == 4 * (sizeof(T) + 2sizeof(Int))
            JS._end_dual_infeasibility!(w, previous)
        end
        w, c = released_context(); GC.gc()
        @test isnothing(w.value) && isnothing(c.value)
    end
end
end
