using JSimplex, Test, SparseArrays

function point_recovery_workspace(T, manager; observer=nothing)
    scale = T === Float32 ? T(1e3) : T(1e9)
    drift = T === Float32 ? T(1e-6) : T(1e-13)
    tolerance = T === Float32 ? T(1e-4) : T(1e-7)
    problem = LinearProblem(sparse(reshape(T[scale,scale],2,1)), T[-1];
        row_upper=T[scale,Inf])
    options = SolverOptions(T; algorithm=:primal, basis_update=manager,
        primal_tolerance=tolerance, verbose=false)
    diagnostics = JSimplex.SimplexDiagnostics(; observer)
    ws = JSimplex.initialize_workspace(problem, options;
        progress=JSimplex.SimplexProgressContext(problem; diagnostics))
    # A tiny error in an unchanged basis column passes the transpose check,
    # but the large row activity amplifies it beyond the primal tolerance.
    ws.factorization.base = JSimplex._factorize_basis(sparse(T[-1 drift;0 -1]))
    return ws, diagnostics
end

@testset "Native correction repairs an uncertified reconstruction and prediction" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        completed = Ref{Any}(nothing)
        observer = (event, ws)->begin
            if event == :pivot_completed
                completed[] = copy(ws.primal)
                @test JSimplex._legacy_primal_row_consistent(ws, ws.options.primal_tolerance)
                @test JSimplex._original_primal_feasible(ws.problem, ws.primal[1:1], ws.options.primal_tolerance)
            end
        end
        ws, diagnostics = point_recovery_workspace(T, manager; observer)
        tolerance = ws.options.primal_tolerance
        @test JSimplex._legacy_primal_row_consistent(ws, tolerance)
        terminal = JSimplex._primal_iteration!(ws, ()->false, ws.options.dual_tolerance)
        @test isnothing(terminal)
        @test ws.iterations == 1
        @test JSimplex.primal_infeasibility(ws) <= tolerance
        @test JSimplex._legacy_primal_row_consistent(ws, tolerance)
        @test JSimplex._original_primal_feasible(ws.problem, ws.primal[1:1], tolerance)
        @test JSimplex.event_count(diagnostics, :correction_attempt) == 1
        @test JSimplex.event_count(diagnostics, :correction) == 1
        @test JSimplex.event_count(diagnostics, :primal_point_corrected) == 1
        @test ws.refactorizations == 0
        @test ws.scratch.row_solution == ws.primal[ws.basis.basic_indices]
        @test completed[] == ws.primal
    end
end

@testset "An unrepairable point stops before another pricing call" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        # No binary floating value of x satisfies 3x == 1 at this tolerance.
        tolerance = eps(T)^2
        problem = LinearProblem(sparse(reshape(T[3],1,1)), T[-1]; row_upper=T[1])
        options = SolverOptions(T; algorithm=:primal, basis_update=manager,
            primal_tolerance=tolerance, verbose=false)
        computed = Ref{Any}(nothing)
        observer = (event,ws)->begin
            event == :correction_attempt && (computed[]=copy(ws.primal))
            event == :pivot_completed && (@test ws.scratch.selected_row == 1)
            nothing
        end
        diagnostics = JSimplex.SimplexDiagnostics(; observer)
        ws = JSimplex.initialize_workspace(problem, options;
            progress=JSimplex.SimplexProgressContext(problem; diagnostics))
        terminal = JSimplex._primal_iteration!(ws, ()->false, options.dual_tolerance)
        @test !isnothing(terminal) && terminal.status == NUMERICAL_ERROR
        @test JSimplex.event_count(diagnostics, :pricing) == 1
        @test JSimplex.event_count(diagnostics, :correction_attempt) == 1
        @test JSimplex.event_count(diagnostics, :correction) == 0
        @test ws.primal == computed[]
        @test ws.iterations == 1
        @test ws.refactorizations == 0
    end
end

@testset "Cancelling point correction preserves the reconstructed values" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        computed = Ref{Any}(nothing)
        observer = (event,ws)->(event == :correction_attempt && (computed[]=copy(ws.primal)); nothing)
        ws, diagnostics = point_recovery_workspace(Float64, manager; observer)
        stop = ()->JSimplex.event_count(diagnostics, :correction_attempt) > 0
        terminal = JSimplex._primal_iteration!(ws, stop, ws.options.dual_tolerance)
        @test !isnothing(terminal) && terminal.status == TIME_LIMIT
        @test ws.primal == computed[]
        @test JSimplex.event_count(diagnostics, :correction) == 0
        @test JSimplex.event_count(diagnostics, :pricing) == 1
    end
end

@testset "Late cancellation and exceptions roll back the correction trial" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), mode in (:stop,:throw)
        ws, diagnostics = point_recovery_workspace(Float64, manager)
        ws.primal[2] = 1.0
        original = copy(ws.primal)
        row_solution = copy(ws.scratch.row_solution)
        calls = Ref(0)
        stop = function()
            calls[] += 1
            if calls[] == 4
                @test ws.primal != original
                @test JSimplex._legacy_primal_point_certified(ws)
                mode == :throw && error("cancel corrected trial")
                return true
            end
            return false
        end
        if mode == :throw
            @test_throws ErrorException("cancel corrected trial") JSimplex._try_native_primal_point_correction!(ws, stop)
        else
            @test !JSimplex._try_native_primal_point_correction!(ws, stop)
        end
        @test calls[] == 4
        @test ws.primal == original
        @test ws.scratch.row_solution == row_solution
        @test JSimplex.event_count(diagnostics, :correction) == 0
        @test JSimplex.event_count(diagnostics, :primal_point_corrected) == 0
    end
end

@testset "Unrepairable fresh-factor points terminate candidate retries" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        path in (:rejected_candidate,:small_pivot)
        problem = LinearProblem(sparse(reshape(T[3],1,1)), T[-1]; row_upper=T[1])
        options = SolverOptions(T; algorithm=:primal, basis_update=manager,
            primal_tolerance=eps(T)^2, zero_tolerance=one(T), verbose=false)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws = JSimplex.initialize_workspace(problem, options;
            progress=JSimplex.SimplexProgressContext(problem; diagnostics))
        terminal = JSimplex._primal_iteration!(ws, ()->false, options.dual_tolerance)
        @test !isnothing(terminal) && terminal.status == NUMERICAL_ERROR
        @test !isempty(ws.factorization.updates)
        ws.scratch.selected_row = -1
        if path == :rejected_candidate
            terminal = JSimplex._legacy_primal_reject_candidate!(ws, 2, zeros(T,1),
                ()->false, options.dual_tolerance, false, false, :refactor_residual,
                "test candidate rejection")
        else
            # The upper-bound row enters with a genuine improving direction;
            # its pivot 1/3 is below the configured zero tolerance.
            ws.costs[2] = T(4)/T(3)
            ws.reduced_costs[2] = one(T)
            terminal = JSimplex._primal_iteration!(ws, ()->false, options.dual_tolerance)
            @test JSimplex.event_count(diagnostics, :refactor_pivot) == 1
        end
        @test !isnothing(terminal) && terminal.status == NUMERICAL_ERROR
        @test ws.refactorizations == 1
        @test JSimplex.event_count(diagnostics, :pricing) == (path == :small_pivot ? 2 : 1)
        @test ws.scratch.selected_row == 0
        @test isempty(ws.scratch.rejected_entering)
        @test JSimplex.event_count(diagnostics, :primal_point_corrected) == 0
    end
end
