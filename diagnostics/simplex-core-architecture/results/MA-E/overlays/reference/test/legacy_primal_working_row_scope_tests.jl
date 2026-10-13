using Test,JSimplex,SparseArrays

function perturbed_row_value_workspace(T,sign,update)
    margin = T(1e-5)
    problem = LinearProblem(sparse(T(sign).*reshape(T[-1.007e-5,-0.01],1,2)),T[0,-1];
        row_lower=T[sign>0 ? 0 : -Inf],row_upper=T[sign>0 ? Inf : 0],
        column_lower=T[1,0],column_upper=T[1,Inf])
    ws = JSimplex.initialize_workspace(problem,SolverOptions(T;algorithm=:primal,
        basis_update=update,basis_refactorization=:native,primal_tolerance=T(1e-7),verbose=false))
    journal = JSimplex.PerturbationJournal(ws)
    journal.bounds = JSimplex.BoundPerturbationState(ws)
    b = journal.bounds
    if sign > 0
        b.active_lower[3] = Bound(-margin)
    else
        b.active_upper[3] = Bound(margin)
    end
    ws.lower,ws.upper = b.active_lower,b.active_upper
    b.active = true
    ws.scratch.perturbations = journal
    ws.perturbed = true
    return ws
end

@testset "Owned working bounds permit a stable zero-step row pivot" begin
    for T in (Float32,Float64), sign in (-1,1), update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws = perturbed_row_value_workspace(T,sign,update)
        saved = copy(ws.primal)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test !JSimplex._original_primal_feasible(ws.problem,ws.primal[1:2],ws.options.primal_tolerance)
        terminal = JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance)
        @test isnothing(terminal)
        @test ws.basis.basic_indices == [2]
        @test ws.primal[3] == saved[3]
        @test abs(ws.primal[2]) <= eps(T)
        @test JSimplex._legacy_primal_point_certified(ws)
        JSimplex.recompute!(ws;refactorize=true)
        @test ws.primal[3] == saved[3]
        @test abs(ws.primal[2]) <= eps(T)
        JSimplex.restore_perturbations!(ws,ws.scratch.perturbations)
        @test JSimplex._nonbasic_value(ws,3) == zero(T)
        @test !JSimplex._legacy_primal_point_certified(ws)
    end
end

@testset "Row preservation requires the owned active bound journal" begin
    ws = perturbed_row_value_workspace(Float64,1,:pfi)
    ws.iterations = 1
    ws.basis.states[3] = JSimplex.AT_LOWER
    journal = ws.scratch.perturbations
    ws.scratch.perturbations = nothing
    @test JSimplex._nonbasic_value(ws,3) == -1e-5
    ws.scratch.perturbations = journal
    journal.bounds.active = false
    @test JSimplex._nonbasic_value(ws,3) == -1e-5
    journal.bounds.active = true
    ws.primal[3] = -1e-5-2ws.options.primal_tolerance
    @test JSimplex._nonbasic_value(ws,3) == -1e-5
    ws.primal[1] = 1.0-eps(Float64)
    @test JSimplex._nonbasic_value(ws,1) == 1.0
    ws.primal[3] = -1e-5-7e-8
    journal.workspace_id = UInt(0)
    @test_throws ArgumentError JSimplex._nonbasic_value(ws,3)
end
