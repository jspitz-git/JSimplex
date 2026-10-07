using Test,JSimplex,SparseArrays,LinearAlgebra

function native_reprice_workspace(T;manager=:pfi,diagnostics=nothing,max_refinements=3)
    B=Matrix{T}(I,2,2)
    problem=LinearProblem(sparse(hcat(B,B[:,1],-B[:,2])),T[0,0,0,1];
        row_lower=T[0,-1],row_upper=T[0,-1],column_lower=[nothing,zero(T),zero(T),zero(T)])
    options=SolverOptions(T;algorithm=:dual,basis_update=manager,pricing=:steepest_edge,verbose=false)
    policy=JSimplex.NumericalPolicy(T;max_refinements)
    live=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    live.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,fill(JSimplex.AT_LOWER,4)...])
    JSimplex.recompute!(live;refactorize=true)
    ws=JSimplex._candidate_workspace(live)
    # A cancelled BTRAN coefficient can invent a zero-cost candidate whose
    # true FTRAN pivot is zero. The corrected row must choose the real -1 pivot.
    ws.scratch.rho.=T[-1e-3,1]
    JSimplex.price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
    JSimplex.forward_solve!(ws.scratch.row_solution,ws.factorization,T[1,0])
    entering,flips,_=JSimplex._configured_dual_ratio_test(ws,ws.scratch.tableau_row,-one(T),one(T))
    @test entering==3
    live,ws,flips
end

@testset "Native corrected tableau can replace a disproved ratio candidate" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        live,ws,flips=native_reprice_workspace(T;manager)
        before=(copy(live.primal),copy(live.costs),copy(live.basis.basic_indices),live.iterations)
        decision=JSimplex._try_native_dual_tableau!(ws,2,3,-one(T),one(T),flips,()->false;reselect=true)
        @test decision !== false
        if decision !== false
            @test decision.entering_index==4
            @test isempty(decision.flips)
            @test decision.pivot == -one(T)
            @test ws.scratch.tableau_row[3] == zero(T)
            @test ws.scratch.tableau_row[4] == -one(T)
            @test JSimplex.basis_matrix(ws)*ws.scratch.row_solution==ws.problem.A[:,4]
            @test transpose(JSimplex.basis_matrix(ws))*ws.scratch.rho==T[0,1]
        end
        @test before==(live.primal,live.costs,live.basis.basic_indices,live.iterations)
    end
end

@testset "Reselection remains private on rejection, cancellation and observer failure" begin
    for T in (Float32,Float64), mode in (:disabled,:no_candidate,:cancel,:throw)
        cancelled=Ref(false)
        observer=(event,ws)->begin
            if event==:correction
                mode==:cancel && (cancelled[]=true)
                mode==:throw && error("reprice observer")
            end
            nothing
        end
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        live,ws,flips=native_reprice_workspace(T;diagnostics,max_refinements=mode==:disabled ? 0 : 3)
        mode==:no_candidate && (ws.upper[4]=ws.lower[4])
        before=(copy(ws.scratch.rho),copy(ws.scratch.row_solution),copy(ws.scratch.tableau_row),copy(flips))
        original=(copy(live.primal),copy(live.costs),copy(live.basis.basic_indices),live.iterations)
        if mode==:throw
            @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} JSimplex._try_native_dual_tableau!(ws,2,3,-one(T),one(T),flips,()->false;reselect=true)
        else
            @test JSimplex._try_native_dual_tableau!(ws,2,3,-one(T),one(T),flips,()->cancelled[];reselect=true) === false
        end
        @test before==(ws.scratch.rho,ws.scratch.row_solution,ws.scratch.tableau_row,flips)
        @test original==(live.primal,live.costs,live.basis.basic_indices,live.iterations)
    end
end

@testset "Fresh staged native guard is required for reselection" begin
    live,ws,flips=native_reprice_workspace(Float64)
    @test JSimplex._try_native_dual_tableau!(live,2,3,-1.0,1.0,flips,()->false;reselect=true) === false
    JSimplex.replace_column!(ws.factorization,[1.0,0.0],1)
    @test JSimplex._try_native_dual_tableau!(ws,2,3,-1.0,1.0,flips,()->false;reselect=true) === false
end

@testset "Native tableau row uses the configured bounded correction budget" begin
    for T in (Float32,Float64),budget in (1,3)
        live,ws,flips=native_reprice_workspace(T;max_refinements=budget)
        error=T===Float32 ? T(0.05) : T(1e-5)
        # Model a fresh factor whose inverse action has a small relative error.
        # One correction does not pass the unchanged row residual test; the
        # configured remaining corrections do. No wider arithmetic is needed.
        ws.factorization.base=JSimplex._factorize_basis(sparse(Matrix{T}(I,2,2)/(one(T)+error)))
        JSimplex.transpose_solve!(ws.scratch.rho,ws.factorization,T[0,1])
        JSimplex.price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
        JSimplex.forward_solve!(ws.scratch.row_solution,ws.factorization,T[0,-1])
        decision=JSimplex._try_native_dual_tableau!(ws,2,4,-one(T),one(T),flips,()->false;reselect=true)
        @test (decision!==false)==(budget==3)
        if decision!==false
            @test decision.entering_index==4
            @test JSimplex._dual_row_residual_ratio(ws,ws.scratch.rho,2)<=one(T)
        end
    end
end

@testset "Corrected ratio decisions replace pending bound flips" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        B=Matrix{T}(I,2,2)
        problem=LinearProblem(sparse(hcat(B,B[:,1],-B[:,2],-B[:,2])),T[0,0,0,1,2];
            row_lower=T[0,-1],row_upper=T[0,-1],
            column_lower=[nothing,zero(T),zero(T),zero(T),zero(T)],
            column_upper=[nothing,nothing,nothing,T(0.25),nothing])
        options=SolverOptions(T;algorithm=:dual,basis_update=manager,pricing=:steepest_edge,verbose=false)
        live=JSimplex.initialize_workspace(problem,options)
        live.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,fill(JSimplex.AT_LOWER,5)...])
        JSimplex.recompute!(live;refactorize=true)
        ws=JSimplex._candidate_workspace(live)
        ws.scratch.rho.=T[-1e-3,1]
        JSimplex.price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
        JSimplex.forward_solve!(ws.scratch.row_solution,ws.factorization,T[1,0])
        entering,flips,_=JSimplex._configured_dual_ratio_test(ws,ws.scratch.tableau_row,-one(T),one(T))
        @test entering==3 && isempty(flips)
        decision=JSimplex._try_native_dual_tableau!(ws,2,entering,-one(T),one(T),flips,()->false;reselect=true)
        @test decision !== false
        if decision !== false
            @test decision.entering_index==5 && decision.flips==[4]
            @test decision.pivot == -one(T)
            @test ws.primal[4]==zero(T) && ws.basis.states[4]==JSimplex.AT_LOWER
            @test JSimplex._apply_bound_flips!(ws,decision.flips,()->false)
            @test ws.primal[4]==T(0.25) && ws.basis.states[4]==JSimplex.AT_UPPER
            @test ws.primal[2]==T(-0.75)
            @test ws.problem.A*ws.primal[1:5]==T[0,-1]
            @test JSimplex.basis_matrix(ws)*ws.scratch.row_solution==ws.problem.A[:,5]
        end
        @test live.primal[4]==zero(T) && live.primal[2]==-one(T)
    end
end

@testset "Cancellation during a later BTRAN correction remains private" begin
    attempts=Ref(0)
    observer=(event,ws)->(event==:correction_attempt && (attempts[]+=1);nothing)
    live,ws,flips=native_reprice_workspace(Float64;diagnostics=JSimplex.SimplexDiagnostics(;observer))
    ws.factorization.base=JSimplex._factorize_basis(sparse(Matrix{Float64}(I,2,2)/(1+1e-5)))
    JSimplex.transpose_solve!(ws.scratch.rho,ws.factorization,[0.0,1.0])
    JSimplex.price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
    before=(copy(ws.scratch.rho),copy(ws.scratch.row_solution),copy(ws.scratch.tableau_row),copy(flips))
    @test JSimplex._try_native_dual_tableau!(ws,2,4,-1.0,1.0,flips,()->attempts[]>=2;reselect=true) === false
    @test attempts[]==2
    @test before==(ws.scratch.rho,ws.scratch.row_solution,ws.scratch.tableau_row,flips)
end

@testset "Fresh factors must pass the same dual row residual check as updated factors" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        live,ws,flips=native_reprice_workspace(T;manager)
        # The fresh inverse actions agree on a false pivot in column 3, but
        # B' * rho != e_2. Correcting the row before the ratio test selects 4.
        ws.factorization.base=JSimplex._factorize_basis(sparse(T[1 0;0.001 1]))
        @test isempty(ws.factorization.updates)
        terminal=JSimplex._dual_iteration_unchecked!(ws,()->false,true,false)
        @test isnothing(terminal)
        @test ws.iterations==1 && ws.basis.basic_indices==[1,4]
        @test ws.primal[3]==zero(T) && ws.primal[4]==one(T)
        @test ws.problem.A*ws.primal[1:4]==T[0,-1]
    end
end
