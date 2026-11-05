module DualSmallPivotRetryTests
using JSimplex, Test, SparseArrays, LinearAlgebra
const JS = JSimplex

# Inject only the certification outcome for this test's callback type. Pricing,
# staging, factor updates and bounded recovery all use the production code.
mutable struct CertificateControl
    mode::Symbol
    calls::Int
    stopped::Bool
end
CertificateControl(mode) = CertificateControl(mode, 0, false)
(control::CertificateControl)() = control.stopped

function JS._stabilize_small_dual_pivot!(w::JS.SimplexWorkspace{Float64},
        i::Int, p::Float64, t::Float64, d::Float64,
        stop::JS._StopCallback{CertificateControl})
    control = stop.callback
    control.calls += 1
    control.mode == :throw && error("test certificate exception")
    if control.mode == :cancel
        control.stopped = true
        return false
    end
    (control.mode == :all || (control.mode == :first && i == 1)) && return false
    return invoke(JS._stabilize_small_dual_pivot!,
        Tuple{JS.SimplexWorkspace{Float64},Int,Float64,Float64,Float64,Any},
        w, i, p, t, d, stop)
end

function fixture()
    p = LinearProblem(sparse([1.0 1.0]), [1.0, 1.0]; row_lower=[1.0])
    options = SolverOptions(algorithm=:dual, simplex_strategy=:legacy, pricing=:devex,
        basis_update=:forrest_tomlin, basis_refactorization=:native,
        refactorization_interval=160, verbose=false, presolve=false)
    diagnostics = JS.SimplexDiagnostics()
    w = JS.initialize_workspace(p, options;
        progress=JS.SimplexProgressContext(p; diagnostics))
    return w, diagnostics
end

snapshot_values(w) = deepcopy((w.costs, w.lower, w.upper, w.primal, w.reduced_costs,
    w.basis.basic_indices, w.basis.states, w.iterations))

@testset "Uncertified dual pivot uses bounded recovery" begin
    @testset "Alternate pivot commits without weakening policy" begin
        w, diagnostics = fixture()
        options, policy = repr(w.options), repr(w.progress.numerical_policy)
        @test isnothing(JS.dual_iteration!(w, CertificateControl(:first)))
        @test w.iterations == 1
        @test w.basis.basic_indices == [2]
        @test JS.event_count(diagnostics, :pivot_rejected) > 0
        @test JS.event_count(diagnostics, :pivot_completed) == 1
        @test isempty(w.scratch.rejected_entering) && isempty(w.scratch.rejected_rows)
        @test repr(w.options) == options && repr(w.progress.numerical_policy) == policy
        @test JS.dual_infeasibility(w) <= w.options.dual_tolerance
        @test JS._original_primal_feasible(w.problem, w.primal[1:2], w.options.primal_tolerance)
        @test JS.basis_matrix(w) * JS.forward_solve!(zeros(1), w.factorization, [1.0]) ≈ [1.0]
    end

    @testset "Repeated rejection is bounded and atomic" begin
        w, diagnostics = fixture()
        saved = snapshot_values(w)
        control = CertificateControl(:all)
        result = JS.dual_iteration!(w, control)
        @test result.status == NUMERICAL_ERROR
        @test result.message == "bounded pivot validation and basis recovery attempts exhausted"
        @test snapshot_values(w) == saved
        policy = w.progress.numerical_policy
        @test control.calls <= 1 + policy.max_pivot_candidates^2 * (policy.max_recovery_rounds + 1)
        @test JS.event_count(diagnostics, :pivot_completed) == 0
        @test isempty(w.scratch.rejected_entering) && isempty(w.scratch.rejected_rows)
        @test JS.basis_matrix(w) * JS.forward_solve!(zeros(1), w.factorization, [1.0]) ≈ [1.0]
    end

    @testset "Cancellation and exceptions preserve live state" begin
        w, diagnostics = fixture()
        saved = snapshot_values(w)
        control = CertificateControl(:cancel)
        @test JS.dual_iteration!(w, control).status == TIME_LIMIT
        @test control.calls == 1 && snapshot_values(w) == saved
        @test JS.event_count(diagnostics, :pivot_rejected) == 0
        @test_throws ErrorException JS.dual_iteration!(w, CertificateControl(:throw))
        @test snapshot_values(w) == saved
        stop = JS._guard_stop_callback(CertificateControl(:throw))
        @test_throws ErrorException JS._transactional_simplex_step!(w, stop) do staged, guard
            JS._dual_iteration_unchecked!(staged, guard)
        end
        @test snapshot_values(w) == saved
    end

    @testset "Accepted pivot needs no recovery stage" begin
        w, diagnostics = fixture()
        @test isnothing(JS.dual_iteration!(w, CertificateControl(:off)))
        @test w.iterations == 1
        @test JS.event_count(diagnostics, :pivot_rejected) == 0
        @test isnothing(w.scratch.stage_values) && isnothing(w.scratch.stage_scratch)
    end
end
end
