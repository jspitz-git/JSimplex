using Test, JSimplex, SparseArrays, LinearAlgebra

function native_dual_reconstruction_fixture(T; manager=:pfi, max_refinements=3,
                                             diagnostics=nothing)
    tiny = T === Float32 ? T(1e-20) : T(1e-66)
    noise = T === Float32 ? T(1e-10) : T(1e-30)
    # B' * [-tiny, tiny] = [0, tiny]. A residual correction loses the first
    # tiny coordinate when subtracting noise; clearing both erases real data.
    B = sparse(T[1 0; 1 1])
    problem = LinearProblem(B, T[0, tiny]; row_lower=T[1, 2], row_upper=T[1, 2])
    options = SolverOptions(T; algorithm=:dual, basis_update=manager,
        basis_refactorization=:native, verbose=false, presolve=false, scaling=:off)
    policy = JSimplex.NumericalPolicy(T; max_refinements)
    ws = JSimplex.initialize_workspace(problem, options;
        progress=JSimplex.SimplexProgressContext(problem; diagnostics, numerical_policy=policy))
    ws.basis = JSimplex.Basis([1, 2], [JSimplex.BASIC, JSimplex.BASIC,
        JSimplex.AT_LOWER, JSimplex.AT_LOWER])
    JSimplex.recompute!(ws; refactorize=true)
    ws.scratch.rho .= T[noise, tiny]
    return ws, B, tiny
end

native_dual_published_state(ws) = deepcopy((ws.primal, ws.scratch.row_solution,
    ws.scratch.rho, ws.reduced_costs, ws.costs, ws.lower, ws.upper,
    ws.basis.basic_indices, ws.basis.states))

@testset "Driver BTRAN reconstruction preserves tiny nonzero costs" begin
    for T in (Float32, Float64), manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws, B, tiny = native_dual_reconstruction_fixture(T; manager, diagnostics)
        rhs = ws.costs[ws.basis.basic_indices]
        raw = copy(ws.scratch.rho)
        @test !JSimplex._native_cleanup_solve!(raw, ws, B, rhs, ()->false; transposed=true)
        @test raw == ws.scratch.rho
        saved = deepcopy((ws.costs, ws.lower, ws.upper, ws.basis))
        attempts = JSimplex.event_count(diagnostics, :correction_attempt)
        @test JSimplex._try_native_cleanup_recompute!(ws, ()->false)
        @test ws.scratch.rho ≈ T[-tiny, tiny]
        @test transpose(B) * ws.scratch.rho ≈ rhs
        @test JSimplex._recomputed_basis_reliable(ws)
        @test ws.primal[1:2] == ones(T, 2)
        @test ws.reduced_costs[1:2] == zeros(T, 2)
        @test isequal(saved[1:3], (ws.costs, ws.lower, ws.upper))
        @test ws.basis.basic_indices == saved[4].basic_indices
        @test ws.basis.states == saved[4].states
        @test ws.iterations == 0
        @test JSimplex.event_count(diagnostics, :correction_attempt) == attempts + 1
    end
end

@testset "Driver BTRAN reconstruction keeps cancellation and rejection private" begin
    for T in (Float32, Float64)
        ws, _, _ = native_dual_reconstruction_fixture(T)
        calls = Ref(0)
        @test JSimplex._try_native_cleanup_recompute!(ws, ()->begin calls[] += 1; false end)
        total = calls[]
        for throwing in (false, true), boundary in 1:total
            ws, _, _ = native_dual_reconstruction_fixture(T)
            before = native_dual_published_state(ws)
            calls[] = 0
            failure = ErrorException("cancel dual reconstruction")
            stop = ()->begin
                calls[] += 1
                if calls[] == boundary
                    throwing && throw(failure)
                    return true
                end
                false
            end
            result = try JSimplex._try_native_cleanup_recompute!(ws, stop) catch e; e end
            @test result === (throwing ? failure : false)
            @test isequal(before, native_dual_published_state(ws))
        end
        for mode in (:budget, :checked, :bad_factor, :nonfinite)
            ws, B, _ = native_dual_reconstruction_fixture(T;
                max_refinements=mode === :budget ? 0 : 3)
            if mode === :checked
                JSimplex._install_driver_policy!(ws, JSimplex.NumericalPolicy(T; solve_refinement=true))
            elseif mode === :bad_factor
                JSimplex.refactorize!(ws.factorization, -B)
                ws.scratch.rho .= one(T)
            elseif mode === :nonfinite
                ws.scratch.rho[1] = T(NaN)
            end
            before = native_dual_published_state(ws)
            @test !JSimplex._try_native_cleanup_recompute!(ws, ()->false)
            @test isequal(before, native_dual_published_state(ws))
        end
    end
end
