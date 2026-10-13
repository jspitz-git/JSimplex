using Test, JSimplex, SparseArrays, LinearAlgebra

function native_certificate_fixture(T; algorithm=:dual, manager=:huangfu_hall,
                                    diagnostics=nothing, max_refinements=3, genuine=false)
    # B' * [scale,scale,scale] = [scale,0,0] exactly. Native BTRAN
    # nevertheless leaves an absolute stationarity error above tolerance.
    B = T[-4 -4 -2; -2 -5 2; 7 9 0]
    scale = T(2)^(T === Float32 ? 12 : 40)
    rhs = B * ones(T,3)
    problem = LinearProblem(sparse(hcat(B,zeros(T,3))), T[scale,0,0,genuine ? -1 : 0];
        row_lower=rhs,row_upper=rhs)
    options = SolverOptions(T; algorithm,basis_update=manager,presolve=false,scaling=:off,verbose=false)
    policy = JSimplex.NumericalPolicy(T; max_refinements)
    progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy,diagnostics)
    ws = JSimplex.initialize_workspace(problem,options;progress)
    ws.basis = JSimplex.Basis([1,2,3],vcat(fill(JSimplex.BASIC,3),fill(JSimplex.AT_LOWER,4)))
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal .= vcat(ones(T,3),zero(T),rhs)
    return ws, scale
end

certificate_published_state(ws) = deepcopy((ws.primal,ws.costs,ws.reduced_costs,ws.scratch.rho,
    ws.lower,ws.upper,ws.basis.basic_indices,ws.basis.states,ws.iterations,ws.refactorizations))

@testset "Terminal certificate repairs native stationarity in both algorithms" begin
    for T in (Float32,Float64), algorithm in (:dual,:primal),
        manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws,scale = native_certificate_fixture(T;algorithm,manager,diagnostics)
        y = JSimplex._original_dual_witness(ws)
        @test !JSimplex._original_witness_certified(ws.problem,ws.options,ws.basis,ws.primal[1:4],y)
        @test JSimplex._original_witness_certified(ws.problem,ws.options,ws.basis,ws.primal[1:4],fill(scale,3))
        before = certificate_published_state(ws)
        result = JSimplex._internal_solution(ws,OPTIMAL,"candidate")
        @test result.status == OPTIMAL
        @test result.primal == T[1,1,1,0]
        @test result.objective_value == scale
        @test certificate_published_state(ws) == before
        @test JSimplex.event_count(diagnostics,:correction_attempt) == 1
        @test !ws.progress.numerical_policy.solve_refinement
    end
end

@testset "Certificate recovery preserves genuine rejection and policy limits" begin
    for T in (Float32,Float64), algorithm in (:dual,:primal), mode in (:genuine,:budget,:deadline,:shifted)
        diagnostics = JSimplex.SimplexDiagnostics()
        ws,scale = native_certificate_fixture(T;algorithm,diagnostics,
            genuine=mode==:genuine,max_refinements=mode==:budget ? 0 : 3)
        mode==:deadline && (ws.options=JSimplex._remaining_options(ws.options;iterations=0,time_limit=0.0))
        mode==:shifted && fill!(ws.costs,-scale)
        before = certificate_published_state(ws)
        result = JSimplex._internal_solution(ws,OPTIMAL,"candidate")
        @test result.status == (mode==:shifted ? OPTIMAL : NUMERICAL_ERROR)
        @test certificate_published_state(ws) == before
        @test JSimplex.event_count(diagnostics,:correction_attempt) == (mode in (:budget,:deadline) ? 0 : 1)
        @test JSimplex.event_count(diagnostics,:certificate_corrected) == (mode==:shifted ? 1 : 0)
    end
end

@testset "Certificate recovery keeps interrupted witnesses private" begin
    for T in (Float32,Float64)
        ws,_ = native_certificate_fixture(T)
        primal = copy(ws.primal[1:4]); dual=JSimplex._original_dual_witness(ws)
        before = certificate_published_state(ws); saved_dual=copy(dual)
        calls=Ref(0)
        @test JSimplex._try_native_certificate_recovery(ws,primal,dual,()->begin calls[]+=1;false end)
        total=calls[]
        for throwing in (false,true), boundary in 1:total
            calls[]=0
            failure=ErrorException("interrupted certificate")
            stop=()->begin
                calls[]+=1
                if calls[]==boundary
                    throwing && throw(failure)
                    return true
                end
                false
            end
            result=try JSimplex._try_native_certificate_recovery(ws,primal,dual,stop) catch e;e end
            @test result === (throwing ? failure : false)
            @test certificate_published_state(ws) == before
            @test dual == saved_dual
        end
        policy=JSimplex.NumericalPolicy(T;solve_refinement=true)
        JSimplex._install_driver_policy!(ws,policy)
        @test !JSimplex._try_native_certificate_recovery(ws,primal,dual,()->false)
    end
end

@testset "Successful certificates never attempt native recovery" begin
    for algorithm in (:primal,:dual)
        p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0],row_upper=[1.0])
        diagnostics=JSimplex.SimplexDiagnostics()
        ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics))
        ws.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
        JSimplex.recompute!(ws;refactorize=true)
        @test JSimplex._internal_solution(ws,OPTIMAL,"candidate").status == OPTIMAL
        @test JSimplex.event_count(diagnostics,:correction_attempt)==0
        @test JSimplex.event_count(diagnostics,:certificate_corrected)==0
    end
end
