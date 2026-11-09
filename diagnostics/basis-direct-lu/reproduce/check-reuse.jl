using JSimplex, LinearAlgebra, SparseArrays, Test
const JS = JSimplex
Base.include(JS, joinpath(@__DIR__, "direct.jl"))
@assert only(ARGS) in ("direct", "normalized")
const normalize = only(ARGS) == "normalized"
JS._install_trial_direct!(; normalize)

@testset "Published direct basis authorizes only the verified dual checks" begin
    for manager in (:forrest_tomlin, :suhl_suhl, :bartels_golub), pricing in (:devex, :dantzig, :steepest_edge)
        lp = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 10.0]; row_lower=[1.0, -Inf])
        options = SolverOptions(algorithm=:dual, pricing=pricing, basis_update=manager,
            simplex_strategy=:legacy, presolve=false, refactorization_interval=1)
        ws = JS.initialize_workspace(lp, options)
        f = ws.factorization
        stop = JS._guard_stop_callback(JS._SolveDeadline(time_ns(), Inf))
        eligible() = JS._can_reuse_dual_checks(ws, stop)
        @test f isa JS.TrialDirectFactor
        @test f.base.normalize_requested == normalize == !isnothing(f.base.diagonal)
        @test eligible()
        @test !JS._can_reuse_dual_checks(ws, JS._guard_stop_callback(() -> false))
        @test !JS._can_reuse_corrected_row(ws, stop, ws.scratch.rho, ws.scratch.rho)

        # The same live object can lose and regain eligibility on publication.
        B = spdiagm(0 => [-1.0, -1.0])
        JS.refactorize!(f, spdiagm(0 => [nextfloat(1.0), 1.0]))
        @test ws.factorization === f && !isnothing(f.base.fallback)
        @test !eligible()
        @test_throws LinearAlgebra.SingularException JS.refactorize!(f, spzeros(2,2))
        @test !eligible()
        JS.refactorize!(f, B)
        @test isnothing(f.base.fallback) && eligible()

        # A rejected normalization retains the unnormalized U. Only the
        # normalization request and the diagonal actually published matter.
        b = f.base
        f.base = JS.TrialLowerBackend(b.lower, b.row_order, b.scaling, b.divide_scaling,
            b.diagonal, !normalize, b.fallback, b.work)
        @test !eligible()
        f.base = b
        @test JS._dual_optimize!(ws, stop).status == OPTIMAL
        @test ws.refactorizations > 0 && eligible()
        diag = JS.SimplexDiagnostics(; observer=(event, w) ->
            event == :pivot_completed && (pricing == :dantzig ? (w.costs[1] = NaN) : (w.pricing_weights[1] = 0.0)))
        # Test the post-pivot check before a scheduled rebuild recomputes weights.
        observed_options = SolverOptions(algorithm=:dual, pricing=pricing, basis_update=manager,
            simplex_strategy=:legacy, presolve=false, refactorization_interval=160)
        observed = JS.initialize_workspace(lp, observed_options; progress=JS.SimplexProgressContext(lp; diagnostics=diag))
        @test !JS._can_reuse_dual_checks(observed, stop)
        @test JS.dual_iteration!(observed, stop).status == NUMERICAL_ERROR
    end
end

# The shared fixed-pricing regressions also execute with the actual installed
# direct backend, including both DSE recovery failure paths.
include(joinpath(@__DIR__, "../../../test/dual_fixed_pricing_check_reuse_tests.jl"))
