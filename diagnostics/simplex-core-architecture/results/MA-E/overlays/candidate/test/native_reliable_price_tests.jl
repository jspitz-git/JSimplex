using Test,JSimplex,SparseArrays,LinearAlgebra

# Exact dual [1,1,1] has an ordinarily reliable but nonzero native residual.
# A combination of zero-cost basic columns exposes a spurious reduced price.
function reliable_price_fixture(T,manager;genuine=false,max_refinements=3,diagnostics=nothing)
    B=T[-4 -4 -2;-2 -5 2;7 9 0]
    a=B[:,2]+3B[:,3];rhs=B*ones(T,3)
    A=sparse(hcat(B,a,-a,zeros(T,3)))
    costs=T[1,0,0,0,0,genuine ? -T(1e-30) : zero(T)]
    upper=vcat(fill(Bound{T}(nothing),5),Bound(one(T)))
    problem=LinearProblem(A,costs;row_lower=rhs,row_upper=rhs,column_upper=upper)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false)
    policy=JSimplex.NumericalPolicy(T;max_refinements)
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    ws.basis=JSimplex.Basis(collect(1:3),vcat(fill(JSimplex.BASIC,3),fill(JSimplex.AT_LOWER,6)))
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal.=vcat(ones(T,3),zeros(T,3),rhs)
    return ws
end

@testset "Reliable BTRAN can still require price recovery" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),genuine in (false,true)
        diagnostics=JSimplex.SimplexDiagnostics()
        ws=reliable_price_fixture(T,manager;genuine,diagnostics)
        B=JSimplex.basis_matrix(ws);rhs=ws.costs[ws.basis.basic_indices]
        dual=similar(rhs);JSimplex.transpose_solve!(dual,ws.factorization,rhs)
        quality=JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(T,3),B,dual,rhs,
            ws.progress.numerical_policy,true)
        @test quality.reliable && quality.absolute_error>zero(T)
        @test any(!iszero,ws.reduced_costs[4:5])
        @test JSimplex._legacy_primal_point_certified(ws)
        costs=copy(ws.costs)
        terminal=JSimplex._primal_iteration!(ws,()->false,zero(T))
        @test genuine ? isnothing(terminal) : (!isnothing(terminal) && terminal.status==OPTIMAL)
        @test ws.primal[6]==(genuine ? one(T) : zero(T))
        @test ws.iterations==(genuine ? 1 : 0)
        @test ws.costs==costs
        @test JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex.event_count(diagnostics,:primal_prices_corrected)==1
        @test JSimplex.event_count(diagnostics,:correction_attempt)==1
    end
end

@testset "Forced reliable refinement must improve the residual" begin
    for T in (Float32,Float64),transposed in (false,true),mode in (:improve,:worsen,:unchanged,:stop,:exception)
        B=sparse(reshape(T[1],1,1))
        p=LinearProblem(B,T[0])
        correcting=Ref(false)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->
            event==:correction_attempt && (correcting[]=true))
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics))
        factor=mode==:worsen ? -B : mode==:unchanged ? B/eps(T)^2 : B
        JSimplex.refactorize!(ws.factorization,factor)
        rhs=T[1];x=T[nextfloat(one(T))];before=copy(x)
        # Existing callers preserve reliable solves without even attempting work.
        @test JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->false;transposed)
        @test x==before && !correcting[]
        failure=SingularException(945)
        stop=()->begin
            correcting[] && mode==:exception && throw(failure)
            correcting[] && mode==:stop
        end
        result=try JSimplex._native_cleanup_solve!(x,ws,B,rhs,stop;
            transposed,force_refinement=true) catch e;e end
        @test result === (mode==:exception ? failure : mode==:improve)
        @test x==(mode==:improve ? rhs : before)
        @test JSimplex.event_count(diagnostics,:correction_attempt)==1
    end
end

@testset "Reliable price refinement keeps policy limits and publication atomic" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),mode in (:budget,:checked,:dual,:stop,:exception,:repeat)
        correcting=Ref(false)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            event==:correction_attempt && (correcting[]=true)
            mode==:repeat && event==:primal_prices_corrected && (ws.reduced_costs[6]=-one(eltype(ws.primal)))
        end)
        ws=reliable_price_fixture(Float64,manager;diagnostics,
            max_refinements=mode==:budget ? 0 : 3)
        mode==:checked && JSimplex._install_driver_policy!(ws,JSimplex.NumericalPolicy(Float64;solve_refinement=true))
        mode==:dual && (ws.options=JSimplex._phase_options(ws.options,:dual))
        saved=deepcopy((ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,
            ws.basis.basic_indices,ws.basis.states))
        failure=SingularException(946)
        stop=()->begin
            correcting[] && mode==:exception && throw(failure)
            correcting[] && mode==:stop
        end
        if mode==:repeat
            terminal=JSimplex._primal_iteration!(ws,()->false,0.0)
            @test !isnothing(terminal) && terminal.status==NUMERICAL_ERROR
            @test JSimplex.event_count(diagnostics,:primal_prices_corrected)==1
            @test JSimplex.event_count(diagnostics,:correction_attempt)==1
            @test ws.iterations==0
        else
            result=try JSimplex._try_native_primal_price_recovery!(ws,stop) catch e;e end
            @test result === (mode==:exception ? failure : false)
            @test isequal(saved,(ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,
                ws.basis.basic_indices,ws.basis.states))
            @test JSimplex.event_count(diagnostics,:primal_prices_corrected)==0
        end
    end
end
