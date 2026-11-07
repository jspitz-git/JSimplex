using JSimplex, LinearAlgebra, SparseArrays, Test
const JS = JSimplex
const direct = joinpath(@__DIR__, "..", "..", "basis-direct-lu", "reproduce", "direct.jl")
Base.include(JS, direct)
const normalize = only(ARGS) == "normalized"
JS._install_trial_direct!(; normalize)

@testset "Published direct basis authorizes only the verified dual checks" begin
    for manager in (:forrest_tomlin, :suhl_suhl, :bartels_golub)
        lp = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 10.0]; row_lower=[1.0, -Inf])
        options = SolverOptions(algorithm=:dual, pricing=:devex, basis_update=manager,
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
            event == :pivot_completed && (w.pricing_weights[1] = 0.0))
        observed = JS.initialize_workspace(lp, options; progress=JS.SimplexProgressContext(lp; diagnostics=diag))
        @test !JS._can_reuse_dual_checks(observed, stop)
        @test JS.dual_iteration!(observed, stop).status == NUMERICAL_ERROR
    end
end
