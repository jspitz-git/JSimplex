using JSimplex, Test, SparseArrays

@testset "Legacy primal rejects a price contradicted by its direction" begin
    for T in (Float32, Float64), manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub),
        sign in (-1, 1)
        s=T(sign)
        problem=LinearProblem(sparse(reshape(T[s,s],1,2)),T[0,-s];
            row_upper=T[1],column_lower=fill(sign>0 ? zero(T) : T(-Inf),2),
            column_upper=fill(sign>0 ? T(Inf) : zero(T),2))
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,pricing=:steepest_edge,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        # A rounded transpose/pricing result makes the zero-cost column look
        # better than the genuinely improving column. Its FTRAN is accurate.
        ws.reduced_costs[1]=-2s
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(T))
        @test isnothing(terminal)
        @test ws.basis.basic_indices==[2]
        @test ws.primal[1]==zero(T)
        @test ws.primal[2]==s
        @test ws.iterations==1
        @test ws.refactorizations==0
    end
end

@testset "An inaccurate price cannot force a flip or an unboundedness failure" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        bounded in (false,true)
        problem=LinearProblem(sparse(reshape(T[0,1],1,2)),T[0,-1];
            row_upper=T[1],column_upper=T[bounded ? 0.5 : Inf,Inf])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        ws.reduced_costs[1]=-T(2)
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(T))
        @test isnothing(terminal)
        @test ws.basis.basic_indices==[2]
        @test ws.primal[1]==zero(T)
        @test ws.primal[2]==one(T)
        @test ws.iterations==1
    end
end

@testset "Phase-I pricing retains genuine tiny improving costs" begin
    for T in (Float32, Float64), manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        problem=LinearProblem(sparse(reshape(T[1],1,1)),T[-1e-30];row_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,zero(T)))
        @test ws.primal[1]==one(T)
        @test ws.iterations==1
    end
end

@testset "Consistent prices near cancellation remain usable" begin
    for T in (Float32, Float64), manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub)
        problem=LinearProblem(sparse(reshape(T[1,1],1,2)),T[1,1-4eps(T)];
            row_lower=T[1],row_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        ws.basis.basic_indices[1]=1
        ws.basis.states[1]=JSimplex.BASIC;ws.basis.states[3]=JSimplex.AT_LOWER
        JSimplex.recompute!(ws;refactorize=true)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,zero(T)))
        @test ws.basis.basic_indices==[2]
        @test ws.primal[2]==one(T)
    end
end

@testset "Multi-term cancellation uses the native accumulation allowance" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        large=inv(eps(T))*T(2)
        problem=LinearProblem(sparse(T[1 0 0 1;0 1 0 1;0 0 1 1]),
            T[large,1,-large,2];row_upper=ones(T,3))
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        for row in 1:3
            ws.basis.states[ws.basis.basic_indices[row]]=JSimplex.AT_UPPER
            ws.basis.basic_indices[row]=row
            ws.basis.states[row]=JSimplex.BASIC
        end
        JSimplex.recompute!(ws;refactorize=true)
        column=ones(T,3)
        # The two legitimate evaluation orders differ by one, far beyond a
        # relative tolerance on their results. Their exact-input value is one.
        transpose_price=T(2)-((large+one(T))-large)
        direction_price=((T(2)-large)-one(T))+large
        @test transpose_price==T(2)
        @test direction_price==one(T)
        @test abs(transpose_price-direction_price) > sqrt(eps(T))*abs(transpose_price)
        ws.reduced_costs[4]=transpose_price
        @test JSimplex._legacy_primal_direction_price_ok(ws,4,column,zero(T))
        ws.reduced_costs[4]=T(1e7)
        @test !JSimplex._legacy_primal_direction_price_ok(ws,4,column,zero(T))
    end
end

@testset "A contradicted price refreshes an updated basis once and reprices" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        problem=LinearProblem(sparse(T[1 0 0;0 1 0]),T[-3,-1,0];row_upper=ones(T,2))
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,refactorization_interval=80,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,zero(T)))
        @test ws.basis.basic_indices[1]==1
        @test !isempty(ws.factorization.updates)
        refs=ws.refactorizations
        ws.reduced_costs[3]=-T(100)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,zero(T)))
        @test ws.refactorizations==refs+1
        @test ws.iterations==2
        @test ws.basis.basic_indices==[1,2]
        @test ws.primal[1:3]==T[1,1,0]
        @test JSimplex.primal_infeasibility(ws)<=options.primal_tolerance
    end
end
