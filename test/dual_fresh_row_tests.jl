using Test,JSimplex,SparseArrays,LinearAlgebra

function fresh_dual_row_workspace(T,manager;boxed=false,diagnostics=nothing)
    B=Matrix{T}(I,2,2)
    A=boxed ? hcat(B,B[:,1],-B[:,2],-B[:,2]) : hcat(B,B[:,1],-B[:,2])
    costs=boxed ? T[0,0,0,1,2] : T[0,0,0,1]
    problem=LinearProblem(sparse(A),costs;row_lower=T[0,-1],row_upper=T[0,-1],
        column_lower=vcat([nothing],fill(zero(T),length(costs)-1)),
        column_upper=boxed ? [nothing,nothing,nothing,T(0.25),nothing] : fill(nothing,4))
    options=SolverOptions(T;algorithm=:dual,basis_update=manager,pricing=:steepest_edge,verbose=false)
    live=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics))
    live.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,fill(JSimplex.AT_LOWER,length(costs))...])
    JSimplex.recompute!(live;refactorize=true)
    ws=JSimplex._candidate_workspace(live)
    # Model a fresh factorization error. Both inverse actions agree on a false
    # pivot in duplicate column 3, but B' * rho fails the existing residual test.
    ws.factorization.base=JSimplex._factorize_basis(sparse(T[1 0;0.01 1]))
    live,ws
end

@testset "Fresh dual rows require the same residual check as updated rows" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),boxed in (false,true)
        live,ws=fresh_dual_row_workspace(T,manager;boxed)
        @test isempty(ws.factorization.updates)
        terminal=JSimplex._dual_iteration_unchecked!(ws,()->false,true,false)
        entering=boxed ? 5 : 4
        @test isnothing(terminal)
        @test ws.iterations==1 && ws.basis.basic_indices==[1,entering]
        @test ws.primal[3]==zero(T)
        @test ws.primal[entering]==(boxed ? T(0.75) : one(T))
        @test ws.problem.A*ws.primal[1:length(ws.problem.objective)]==T[0,-1]
        if boxed
            @test ws.primal[4]==T(0.25) && ws.basis.states[4]==JSimplex.AT_UPPER
        end
        @test live.primal[2]==-one(T) && live.iterations==0
    end
end

@testset "Stopping a fresh row correction preserves the time-limit status" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        cancelled=Ref(false)
        observer=(event,ws)->(event==:correction_attempt && (cancelled[]=true);nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        live,ws=fresh_dual_row_workspace(T,manager;diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.basis.basic_indices),ws.iterations)
        terminal=JSimplex._dual_iteration_unchecked!(ws,()->cancelled[],true,false)
        @test !isnothing(terminal) && terminal.status==TIME_LIMIT
        @test before==(ws.primal,ws.costs,ws.basis.basic_indices,ws.iterations)
        @test isempty(ws.factorization.updates)
        @test live.iterations==0
    end
end
