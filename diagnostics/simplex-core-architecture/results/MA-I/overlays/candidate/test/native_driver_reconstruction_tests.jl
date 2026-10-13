using Test,JSimplex,SparseArrays,LinearAlgebra

function native_driver_reconstruction_fixture(T;algorithm=:primal,manager=:pfi,diagnostics=nothing,max_refinements=3,coupled=false)
    tiny=T===Float32 ? T(1e-20) : T(1e-66)
    noise=T===Float32 ? T(1e-10) : T(1e-30)
    A=coupled ? sparse(T[1 1;0 1]) : sparse(T[1 0;0 1])
    rhs=coupled ? T[0,tiny] : T[tiny,1]
    # The accurate basic point still violates the first lower bound.
    p=LinearProblem(A,zeros(T,2);row_lower=rhs,row_upper=rhs,column_lower=T[1,-Inf])
    options=SolverOptions(T;algorithm,basis_update=manager,basis_refactorization=:native,
        verbose=false,presolve=false,scaling=:off)
    policy=JSimplex.NumericalPolicy(T;max_refinements)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
    ws.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal[1]=noise
    return ws,A,rhs,tiny
end

@testset "Driver reconstruction certifies an infeasible basis without erasing tiny data" begin
    for T in (Float32,Float64), algorithm in (:primal,:dual), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        diagnostics=JSimplex.SimplexDiagnostics()
        ws,A,rhs,tiny=native_driver_reconstruction_fixture(T;algorithm,manager,diagnostics)
        saved=copy(ws.primal[1:2]);x=copy(saved)
        @test !JSimplex._native_cleanup_solve!(x,ws,A,rhs,()->false)
        @test x==saved
        attempts=JSimplex.event_count(diagnostics,:correction_attempt)
        accepted=JSimplex._try_native_cleanup_recompute!(ws,()->false)
        @test accepted
        @test ws.primal[1:2]==T[tiny,1]
        reliable=JSimplex._recomputed_basis_reliable(ws)
        @test reliable
        @test !JSimplex._legacy_primal_point_certified(ws)
        @test JSimplex.event_count(diagnostics,:correction_attempt)==attempts+1
        @test ws.iterations==0
    end
end

native_driver_published_state(ws)=deepcopy((ws.primal,ws.scratch.row_solution,ws.scratch.rho,
    ws.reduced_costs,ws.costs,ws.lower,ws.upper,ws.basis.basic_indices,ws.basis.states))

@testset "Driver local reconstruction publishes only a complete certified state" begin
    for T in (Float32,Float64)
        ws,_,_,_=native_driver_reconstruction_fixture(T)
        calls=Ref(0)
        @test JSimplex._try_native_cleanup_recompute!(ws,()->begin calls[]+=1;false end)
        total=calls[]
        # Exercise every cancellation boundary, including after FTRAN succeeds.
        for throwing in (false,true), boundary in 1:total
            ws,_,_,_=native_driver_reconstruction_fixture(T)
            before=native_driver_published_state(ws);calls[]=0
            error=ErrorException("cancel driver reconstruction")
            stop=()->begin
                calls[]+=1
                if calls[]==boundary
                    throwing && throw(error)
                    return true
                end
                false
            end
            result=try JSimplex._try_native_cleanup_recompute!(ws,stop) catch e; e end
            @test result === (throwing ? error : false)
            @test isequal(before,native_driver_published_state(ws))
        end
        for failure in (:dual,:factor,:budget,:checked)
            ws,A,_,_=native_driver_reconstruction_fixture(T;
                max_refinements=failure==:budget ? 0 : 3)
            if failure==:dual
                ws.scratch.rho[1]=T(NaN)
            elseif failure==:factor
                JSimplex.refactorize!(ws.factorization,-A)
                ws.primal[1:2].=one(T)
            elseif failure==:checked
                ws.progress=JSimplex.SimplexProgressContext(ws.problem;
                    numerical_policy=JSimplex.NumericalPolicy(T;solve_refinement=true))
            end
            before=native_driver_published_state(ws)
            @test !JSimplex._try_native_cleanup_recompute!(ws,()->false)
            @test isequal(before,native_driver_published_state(ws))
        end
    end
end

@testset "Local reconstruction starts before rejected homogeneous clearing" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws,A,rhs,tiny=native_driver_reconstruction_fixture(T;manager,coupled=true)
        # A one-ulp factor error leaves a tiny first-coordinate artifact after
        # correction. Clearing the homogeneous row also erases its genuine
        # tiny neighbor; local reconstruction must start from the raw trial.
        approximate=copy(A);approximate[1,1]=nextfloat(one(T))
        JSimplex.refactorize!(ws.factorization,approximate)
        before=copy(ws.primal[1:2]);x=copy(before)
        rejected=JSimplex._native_cleanup_solve!(x,ws,A,rhs,()->false)
        @test !rejected
        @test x==before
        accepted=JSimplex._try_native_cleanup_recompute!(ws,()->false)
        @test accepted
        @test ws.primal[1:2]==T[-tiny,tiny]
        @test JSimplex._recomputed_basis_reliable(ws)
    end
end
