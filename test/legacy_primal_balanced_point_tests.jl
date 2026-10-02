using JSimplex, Test, SparseArrays

function conflicting_point(T, manager=:pfi)
    tolerance = T === Float32 ? T(1e-4) : T(1e-7)
    problem = LinearProblem(sparse(reshape(T[1, 1], 2, 1)), T[0];
        column_lower=T[-1], row_upper=T[0, 0])
    options = SolverOptions(T; algorithm=:primal, basis_update=manager,
        primal_tolerance=tolerance, verbose=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    ws = JSimplex.initialize_workspace(problem, options;
        progress=JSimplex.SimplexProgressContext(problem; diagnostics))
    ws.basis = JSimplex.Basis([1, 3], [JSimplex.BASIC, JSimplex.AT_UPPER, JSimplex.BASIC])
    JSimplex.recompute!(ws; refactorize=true)
    # A reconstruction violates upper bounds; the prediction obeys the bounds
    # but misses the fixed first row activity. There is a certified point between.
    ws.primal .= T[1.5tolerance, 0, 1.5tolerance]
    candidate = T[-1.5tolerance, 0]
    return ws, candidate, diagnostics
end

@testset "Conflicting point errors admit a certified native recovery" begin
    for T in (Float32, Float64), manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        ws, candidate, diagnostics = conflicting_point(T, manager)
        saved_candidate = copy(candidate)
        @test !JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex._restore_legacy_primal_point!(ws, candidate, ()->false)
        # Independent equations and bounds, without assuming a particular trial.
        tol = ws.options.primal_tolerance
        @test -1-tol <= ws.primal[1] <= tol
        @test abs(ws.primal[1]-ws.primal[2]) <= tol
        @test abs(ws.primal[1]-ws.primal[3]) <= tol
        @test ws.primal[3] <= tol
        @test ws.primal[2] == 0
        @test ws.scratch.row_solution == ws.primal[ws.basis.basic_indices]
        @test candidate == saved_candidate
        @test JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex.event_count(diagnostics, :primal_point_preserved) == 1
        @test JSimplex.event_count(diagnostics, :primal_point_balanced) == 1
    end
end

@testset "Uncertified and cancelled recovery trials roll back" begin
    for T in (Float32, Float64), mode in (:invalid, :nonfinite, :stop, :throw)
        ws, candidate, diagnostics = conflicting_point(T)
        original = copy(ws.primal)
        cache = copy(ws.scratch.row_solution)
        mode == :invalid && (candidate .= T(-1))
        mode == :nonfinite && (candidate .= T(Inf))
        saved_candidate = copy(candidate)
        stop = ()->begin
            if mode in (:stop, :throw) && JSimplex._legacy_primal_point_certified(ws)
                mode == :throw && error("cancel certified point trial")
                return true
            end
            false
        end
        if mode == :throw
            @test_throws ErrorException("cancel certified point trial") JSimplex._restore_legacy_primal_point!(ws, candidate, stop)
        else
            @test !JSimplex._restore_legacy_primal_point!(ws, candidate, stop)
        end
        @test ws.primal == original
        @test ws.scratch.row_solution == cache
        @test candidate == saved_candidate
        @test JSimplex.event_count(diagnostics, :primal_point_preserved) == 0
        @test JSimplex.event_count(diagnostics, :primal_point_balanced) == 0
    end
end
