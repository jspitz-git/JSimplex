using JSimplex,Test,SparseArrays
function shifted_point(T,manager=:pfi)
    tolerance=T===Float32 ? T(1e-4) : T(1e-7)
    margin=T(16)*tolerance
    problem=LinearProblem(sparse(reshape(T[1],1,1)),T[1];row_lower=T[-margin])
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,primal_tolerance=tolerance,verbose=false)
    ws=JSimplex.initialize_workspace(problem,options)
    ws.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    journal=JSimplex.PerturbationJournal(ws)
    journal.bounds=JSimplex.BoundPerturbationState(ws)
    journal.bounds.active_lower[1]=Bound(-margin)
    journal.bounds.active=true;journal.bounds.level=1
    ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
    ws.scratch.perturbations=journal;ws.perturbed=true
    JSimplex.recompute!(ws;refactorize=true)
    return ws,margin
end
@testset "Native point recovery certifies owned working bounds" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws,margin=shifted_point(T,manager)
        @test JSimplex.primal_infeasibility(ws)==0
        @test JSimplex._legacy_primal_row_consistent(ws,ws.options.primal_tolerance)
        @test !JSimplex._original_primal_feasible(ws,ws.primal[1:1])
        @test JSimplex._legacy_primal_point_certified(ws)
        ws.primal[1]=zero(T)
        @test JSimplex._restore_legacy_primal_point!(ws,T[-margin],()->false)
        @test ws.primal==T[-margin,-margin]
        ws.primal[1]=zero(T)
        @test JSimplex._try_native_primal_point_correction!(ws,()->false)
        @test ws.primal==T[-margin,-margin]
    end
end

@testset "Working-only points cannot certify the original result" begin
    ws,margin=shifted_point(Float64)
    @test JSimplex._legacy_primal_point_certified(ws)
    result=JSimplex._internal_solution(ws,OPTIMAL,"test working-only point")
    @test result.status==NUMERICAL_ERROR
    @test isnothing(result.primal) && isnothing(result.objective_value)
    journal=ws.scratch.perturbations
    ws.scratch.perturbations=nothing
    @test !JSimplex._legacy_primal_point_certified(ws)
    ws.scratch.perturbations=journal
    journal.bounds.active=false
    @test !JSimplex._legacy_primal_point_certified(ws)
    journal.active=true
    @test !JSimplex._legacy_primal_point_certified(ws)
    journal.active=false;journal.bounds.active=true
    owner=journal.workspace_id
    journal.workspace_id=UInt(0)
    @test_throws ArgumentError JSimplex._legacy_primal_point_certified(ws)
    journal.workspace_id=owner
    JSimplex.restore_perturbations!(ws,journal)
    @test JSimplex._original_bounds_active(ws)
    @test !JSimplex._legacy_primal_point_certified(ws)
end

@testset "Owned row shifts retain exact row cancellation checks" begin
    for T in (Float32,Float64), upper in (false,true)
        tolerance=T===Float32 ? T(1e-4) : T(1e-7)
        margin=T(16)*tolerance
        direction=upper ? one(T) : -one(T)
        large=T===Float32 ? T(2)^30 : T(2)^60
        A=sparse(reshape(T[large,direction*margin,-large],1,3))
        p=LinearProblem(A,zeros(T,3);column_lower=ones(T,3),
            row_lower=upper ? [Bound{T}(nothing)] : [Bound(zero(T))],
            row_upper=upper ? [Bound(zero(T))] : [Bound{T}(nothing)])
        options=SolverOptions(T;algorithm=:primal,primal_tolerance=tolerance,verbose=false)
        ws=JSimplex.initialize_workspace(p,options)
        journal=JSimplex.PerturbationJournal(ws)
        journal.bounds=JSimplex.BoundPerturbationState(ws)
        if upper
            journal.bounds.active_upper[4]=Bound(margin)
        else
            journal.bounds.active_lower[4]=Bound(-margin)
        end
        journal.bounds.active=true;journal.bounds.level=1
        ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
        ws.scratch.perturbations=journal;ws.perturbed=true
        ws.primal .= T[1,1,1,direction*margin]
        lo,hi=JSimplex._primal_row_bounds(A,ws.primal[1:3],Val(false))
        @test !JSimplex._within_primal_intervals(lo,hi,ws.lower[4:4],ws.upper[4:4],tolerance)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test !JSimplex._original_primal_feasible(ws,ws.primal[1:3])
        if upper
            ws.upper[4]=Bound(margin/2)
        else
            ws.lower[4]=Bound(-margin/2)
        end
        ws.primal[4]=direction*margin/2
        @test JSimplex.primal_infeasibility(ws)==0
        @test !JSimplex._legacy_primal_model_feasible(ws)
        @test !JSimplex._legacy_primal_point_certified(ws)
    end
end
