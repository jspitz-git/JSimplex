using JSimplex, Test, SparseArrays, LinearAlgebra

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

# This integer basis has exact dual prices [1,1,0,0,0,0]. Native BTRAN can
# reconstruct spurious small prices on otherwise zero-cost entering columns.
function native_price_roundoff_fixture(T,manager;genuine=false,max_refinements=3,diagnostics=nothing)
    B=T[-3 2 2 1 -3 0; 4 -2 -2 -1 3 0; 1 3 10 0 3 -3;
        -1 0 0 6 -2 1; 2 -3 -2 0 8 -1; -1 -3 1 3 2 4]
    unit=Matrix{T}(I,6,6)[:,3:6]
    A=sparse(hcat(B,unit,-unit,zeros(T,6)))
    costs=vcat(one(T),zeros(T,13),genuine ? -T(1e-30) : zero(T))
    rhs=B*ones(T,6)
    upper=vcat(fill(Bound{T}(nothing),14),Bound(one(T)))
    p=LinearProblem(A,costs;row_lower=rhs,row_upper=rhs,column_upper=upper)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false)
    policy=JSimplex.NumericalPolicy(T;max_refinements)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis=JSimplex.Basis(collect(1:6),vcat(fill(JSimplex.BASIC,6),fill(JSimplex.AT_LOWER,15)))
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal.=vcat(ones(T,6),zeros(T,9),rhs)
    return ws
end

@testset "Native price recovery removes BTRAN roundoff and retains tiny costs" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), genuine in (false,true)
        ws=native_price_roundoff_fixture(T,manager;genuine)
        saved=copy(ws.costs)
        @test JSimplex._legacy_primal_point_certified(ws)
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(T))
        @test genuine ? isnothing(terminal) : (!isnothing(terminal) && terminal.status==OPTIMAL)
        @test ws.primal[15]==(genuine ? one(T) : zero(T))
        @test ws.iterations==(genuine ? 1 : 0)
        @test ws.costs==saved
        @test JSimplex._legacy_primal_point_certified(ws)
        @test isempty(ws.scratch.rejected_entering)
    end
end

@testset "Native price recovery is atomic and respects policy limits" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        for mode in (:budget,:checked,:dual,:cancel,:exception)
            correcting=Ref(false)
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
                event==:correction_attempt && (correcting[]=true)
            end)
            ws=native_price_roundoff_fixture(Float64,manager;
                max_refinements=mode==:budget ? 0 : 3,diagnostics)
            mode==:checked && (ws.progress=JSimplex.SimplexProgressContext(ws.problem;
                numerical_policy=JSimplex.NumericalPolicy(Float64;solve_refinement=true),diagnostics))
            mode==:dual && (ws.options=JSimplex._phase_options(ws.options,:dual))
            saved=deepcopy((ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,
                ws.basis.basic_indices,ws.basis.states))
            failure=SingularException(924)
            stop=()->begin
                correcting[] && mode==:exception && throw(failure)
                correcting[] && mode==:cancel
            end
            result=try JSimplex._try_native_primal_price_recovery!(ws,stop) catch e; e end
            @test result === (mode==:exception ? failure : false)
            @test isequal(saved,(ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,
                ws.basis.basic_indices,ws.basis.states))
            @test JSimplex.event_count(diagnostics,:primal_prices_corrected)==0
            mode in (:cancel,:exception) && (@test correcting[])
        end
    end
end

@testset "Reliable and unchanged native prices do not restart pricing" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_upper=T[1])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false))
        ws.reduced_costs[1]=-one(T)
        before=copy(ws.reduced_costs)
        @test !JSimplex._try_native_primal_price_recovery!(ws,()->false)
        @test ws.reduced_costs==before
    end
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=native_price_roundoff_fixture(Float64,manager)
        @test JSimplex._try_native_primal_price_recovery!(ws,()->false)
        corrected=copy(ws.reduced_costs);dual=copy(ws.scratch.rho)
        @test !JSimplex._try_native_primal_price_recovery!(ws,()->false)
        @test ws.reduced_costs==corrected && ws.scratch.rho==dual
        @test transpose(Rational{BigInt}.(JSimplex.basis_matrix(ws)))*Rational{BigInt}.(dual)==
            Rational{BigInt}.(ws.costs[ws.basis.basic_indices])
    end
end

@testset "A repeated price disagreement cannot renew the recovery budget" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            # Fault injection after publication forces a second disagreement.
            event==:primal_prices_corrected && (ws.reduced_costs[7]=-1.0)
        end)
        ws=native_price_roundoff_fixture(Float64,manager;diagnostics)
        result=JSimplex._primal_iteration!(ws,()->false,0.0)
        @test !isnothing(result) && result.status==NUMERICAL_ERROR
        @test JSimplex.event_count(diagnostics,:primal_prices_corrected)==1
        @test JSimplex.event_count(diagnostics,:correction_attempt)==1
        @test ws.iterations==0
        @test isempty(ws.scratch.rejected_entering)
    end
end
