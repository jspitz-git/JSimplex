using Test, JSimplex, SparseArrays

function structural_zero_step_workspace(T, sign, manager)
    tolerance = T === Float32 ? T(1e-4) : T(1e-7)
    a, b = T(1.081631168), T(1.07184324)
    upper_activity = -T(19)*tolerance
    lower_activity = nextfloat(upper_activity+T(2)*tolerance)
    problem = LinearProblem(sparse(T[-a -b; -b -b]), T[sign,0];
        row_lower=sign>0 ? T[lower_activity,upper_activity] : T[-Inf,-Inf],
        row_upper=sign>0 ? T[Inf,Inf] : -T[lower_activity,upper_activity],
        column_lower=sign>0 ? T[0,0] : T[-Inf,-Inf],
        column_upper=sign>0 ? T[Inf,Inf] : T[0,0])
    ws = JSimplex.initialize_workspace(problem,SolverOptions(T;algorithm=:primal,
        basis_update=manager,basis_refactorization=:native,refactorization_interval=1,
        pricing=:dantzig,primal_tolerance=tolerance,verbose=false))
    ws.basis.basic_indices .= [1,2]
    ws.basis.states[1:2] .= JSimplex.BASIC
    ws.basis.states[3:4] .= sign>0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
    JSimplex.recompute!(ws;refactorize=true)
    # A certified approximate basis point. Snapping x1 to zero makes the two
    # remaining row conditions incompatible even at the original tolerance.
    x = -tolerance/T(2)
    y = -(upper_activity+tolerance-tolerance/T(1000))/b-x
    ws.primal .= T(sign).*T[x,y,lower_activity,upper_activity]
    return ws
end

@testset "Zero-step structural exits retain a certified approximate point" begin
    for T in (Float32,Float64), sign in (-1,1), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws = structural_zero_step_workspace(T,sign,manager)
        before = copy(ws.primal)
        @test JSimplex._legacy_primal_point_certified(ws)
        terminal = JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance)
        @test isnothing(terminal)
        @test ws.basis.basic_indices == [3,2]
        @test iszero(ws.scratch.last_primal_step)
        @test isequal(ws.primal,before)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.scratch.row_solution == ws.primal[ws.basis.basic_indices]
        @test JSimplex._nonbasic_value(ws,1) == before[1]
        # Retention cannot depend on the most recent step being zero: this
        # nonbasic value must also survive subsequent full reconstructions.
        ws.scratch.last_primal_step = one(T)
        candidate = copy(before[ws.basis.basic_indices])
        JSimplex.recompute!(ws;refactorize=true)
        @test ws.primal[1] == before[1]
        @test isnothing(JSimplex._finish_legacy_primal_point!(ws,candidate,()->false))
        @test isequal(ws.primal,before)
        @test JSimplex._legacy_primal_point_certified(ws)
    end
end

@testset "Positive structural exits still reach the exact bound" begin
    for T in (Float32,Float64), sign in (-1,1)
        p = LinearProblem(sparse(reshape(T[1,1],1,2)),T[sign,0];
            row_lower=T[sign/2],row_upper=T[sign/2],
            column_lower=sign>0 ? T[0,0] : T[-Inf,-Inf],
            column_upper=sign>0 ? T[Inf,Inf] : T[0,0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
        ws.basis.basic_indices[1] = 1
        ws.basis.states[1] = JSimplex.BASIC
        ws.basis.states[3] = JSimplex.AT_LOWER
        JSimplex.recompute!(ws;refactorize=true)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,ws.options.dual_tolerance))
        @test abs(ws.scratch.last_primal_step) == T(0.5)
        @test ws.primal[1] == zero(T)
        @test ws.primal[2] == T(sign/2)
        @test JSimplex._legacy_primal_point_certified(ws)
    end
end

@testset "Structural retention stays within native primal bound scope" begin
    for T in (Float32,Float64), sign in (-1,1)
        ws = structural_zero_step_workspace(T,sign,:pfi)
        ws.basis.states[1] = sign>0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
        ws.iterations = 1
        old = ws.primal[1]
        @test JSimplex._nonbasic_value(ws,1) == old
        ws.iterations = 0
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
        ws.iterations = 1
        ws.primal[1] = -T(sign)*2ws.options.primal_tolerance
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
        ws.primal[1] = T(sign)*ws.options.primal_tolerance/T(2)
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
        ws.primal[1] = old
        # Fixed structural variables keep their exact assignment.
        ws.lower[1] = Bound(zero(T));ws.upper[1] = Bound(zero(T))
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
    end
    for T in (Float32,Float64), algorithm in (:primal,:dual)
        p = LinearProblem(sparse(reshape(T[1],1,1)),T[0];column_lower=T[0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm,verbose=false))
        ws.iterations = 1
        ws.primal[1] = -ws.options.primal_tolerance/T(2)
        @test JSimplex._nonbasic_value(ws,1) == (algorithm==:primal ? ws.primal[1] : zero(T))
    end
end

@testset "Structural working bounds require the owned active journal" begin
    for T in (Float32,Float64), sign in (-1,1)
        ws = structural_zero_step_workspace(T,sign,:pfi)
        ws.basis.states[1] = sign>0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
        ws.iterations = 1
        journal = JSimplex.PerturbationJournal(ws)
        journal.bounds = JSimplex.BoundPerturbationState(ws)
        shifted = -T(sign)*T(1e-3)
        if sign>0
            journal.bounds.active_lower[1] = Bound(shifted)
        else
            journal.bounds.active_upper[1] = Bound(shifted)
        end
        ws.lower,ws.upper = journal.bounds.active_lower,journal.bounds.active_upper
        journal.bounds.active = true
        ws.scratch.perturbations = journal
        ws.perturbed = true
        ws.primal[1] = shifted-T(sign)*ws.options.primal_tolerance/T(2)
        old = ws.primal[1]
        @test JSimplex._nonbasic_value(ws,1) == old
        ws.scratch.perturbations = nothing
        @test JSimplex._nonbasic_value(ws,1) == shifted
        ws.scratch.perturbations = journal
        journal.bounds.active = false
        @test JSimplex._nonbasic_value(ws,1) == shifted
        journal.bounds.active = true
        journal.workspace_id = UInt(0)
        @test_throws ArgumentError JSimplex._nonbasic_value(ws,1)
        journal.workspace_id = objectid(ws)
        JSimplex.restore_perturbations!(ws,journal)
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
    end
end

@testset "Structural retention requires the certified point recovery path" begin
    for T in (Float32,Float64), flag in (:pivot_validation,:solve_refinement,:recovery,
                                       :incremental_primal,:incremental_primal_pivots)
        p = LinearProblem(sparse(reshape(T[1],1,1)),T[0];column_lower=T[0])
        policy = JSimplex.NumericalPolicy(T;flag=>true)
        progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy)
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false);progress)
        ws.iterations = 1
        ws.primal[1] = -ws.options.primal_tolerance/T(2)
        @test isnothing(JSimplex._legacy_primal_point_candidate(ws,1,0,zero(T),T[1]))
        @test JSimplex._nonbasic_value(ws,1) == zero(T)
    end
end

@testset "Relaxing an original fixed column does not authorize retention" begin
    for T in (Float32,Float64), sign in (-1,1)
        p = LinearProblem(sparse(reshape(T[1],1,1)),T[0];column_lower=T[0],column_upper=T[0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
        journal = JSimplex.PerturbationJournal(ws)
        journal.bounds = JSimplex.BoundPerturbationState(ws)
        journal.bounds.active_lower[1] = Bound(T(-1e-3))
        journal.bounds.active_upper[1] = Bound(T(1e-3))
        journal.bounds.active = true
        ws.lower,ws.upper = journal.bounds.active_lower,journal.bounds.active_upper
        ws.scratch.perturbations = journal
        ws.iterations = 1
        ws.basis.states[1] = sign>0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
        bound = -T(sign)*T(1e-3)
        ws.primal[1] = bound-T(sign)*ws.options.primal_tolerance/T(2)
        @test JSimplex._nonbasic_value(ws,1) == bound
    end
end

@testset "Unowned tighter bounds cannot retain an original-bound neighbor" begin
    for T in (Float32,Float64), sign in (-1,1)
        ws = structural_zero_step_workspace(T,sign,:pfi)
        ws.basis.states[1] = sign>0 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER
        ws.iterations = 1
        if sign>0
            ws.lower[1] = Bound(one(T))
        else
            ws.upper[1] = Bound(-one(T))
        end
        @test JSimplex._nonbasic_value(ws,1) == T(sign)
    end
end
