using Test, JSimplex, SparseArrays

function coupled_point_workspace(manager=:pfi)
    tolerance = 1e-7
    x = 1.5257939950526029e-6
    a = -1.179713648
    activity = a*x
    problem = LinearProblem(sparse([1,2,3], [1,1,2], [1.0,a,1.0], 3, 2), zeros(2);
        column_lower=[0.0,-1.0], row_lower=[-Inf,-1.6999999999999998e-6,-Inf],
        row_upper=[x,Inf,0.0])
    options = SolverOptions(;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,primal_tolerance=tolerance,verbose=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    ws = JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics))
    ws.basis = JSimplex.Basis([1,4,2], [JSimplex.BASIC,JSimplex.BASIC,
        JSimplex.AT_UPPER,JSimplex.BASIC,JSimplex.AT_UPPER])
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal .= [x,4tolerance,x,activity,0.0]
    candidate = JSimplex._pivot_quality_buffers(ws).trial
    candidate .= [prevfloat(prevfloat(x)),nextfloat(activity),2tolerance]
    return ws,candidate,diagnostics
end

@testset "Complementary prediction and correction errors" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws,candidate,diagnostics = coupled_point_workspace(manager)
        original = copy(ws.primal)
        saved_candidate = copy(candidate)
        @test !JSimplex._restore_legacy_primal_point!(ws,candidate,()->false)
        @test ws.primal == original
        @test !JSimplex._try_native_primal_point_correction!(ws,()->false)
        @test ws.primal == original
        candidate .= saved_candidate
        terminal = JSimplex._finish_legacy_primal_point!(ws,candidate,()->false)
        @test isnothing(terminal)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.primal[[3,5]] == original[[3,5]]
        @test ws.scratch.row_solution == ws.primal[ws.basis.basic_indices]
        @test JSimplex.event_count(diagnostics,:primal_correction_balanced) == 1
        # Check the actual second row in exact stored-coefficient arithmetic,
        # independently of its separately stored activity variable.
        q = Rational{BigInt}
        @test q(-1.179713648)*q(ws.primal[1]) >= q(-1.6999999999999998e-6)-q(1e-7)
        @test ws.primal[2] <= ws.options.primal_tolerance
    end
end

@testset "Coupled recovery rolls back unsuccessful and cancelled trials" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), mode in (:invalid,:stop,:throw)
        ws,candidate,diagnostics = coupled_point_workspace(manager)
        mode == :invalid && (candidate[3] = 8ws.options.primal_tolerance)
        original = copy(ws.primal)
        cache = copy(ws.scratch.row_solution)
        metadata = (copy(ws.lower),copy(ws.upper),copy(ws.costs),
            copy(ws.basis.basic_indices),copy(ws.basis.states))
        cancelled = Ref(false)
        stop = ()->begin
            cancelled[] && return true
            if mode in (:stop,:throw) && JSimplex._legacy_primal_point_certified(ws)
                mode == :throw && error("cancel coupled recovery")
                cancelled[] = true
                return true
            end
            false
        end
        if mode == :throw
            @test_throws ErrorException("cancel coupled recovery") JSimplex._finish_legacy_primal_point!(ws,candidate,stop)
        else
            terminal = JSimplex._finish_legacy_primal_point!(ws,candidate,stop)
            @test terminal.status == (mode == :stop ? TIME_LIMIT : NUMERICAL_ERROR)
        end
        @test ws.primal == original
        @test ws.scratch.row_solution == cache
        @test metadata == (ws.lower,ws.upper,ws.costs,ws.basis.basic_indices,ws.basis.states)
        @test JSimplex.event_count(diagnostics,:primal_correction_balanced) == 0
        @test JSimplex.event_count(diagnostics,:primal_bound_roundoff_corrected) == 0
    end
end
