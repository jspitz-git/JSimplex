using Test,JSimplex,SparseArrays

function dual_entry_phase_fixture(T;manager=:pfi,diagnostics=nothing,limit=8)
    p=LinearProblem(sparse(reshape(T[1],1,1)),T[1];row_lower=T[1])
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false,
        iteration_limit=limit,scaling=:off,presolve=false,simplex_strategy=:adaptive)
    policy=JSimplex.NumericalPolicy(T;adaptive_stalling=true,adaptive_pricing=true,
        adaptive_primal_perturbation=true,adaptive_dual_perturbation=true,phase_one=true)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.iterations=7
    return ws
end

@testset "Explicit dual entry follows its phase with inherited primal options" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), postsolve in (false,true)
        managers=T===Float64 ? (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub) : (:pfi,)
        for manager in managers
            observed=Symbol[]
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->
                event==:pivot_proposed && push!(observed,ws.options.algorithm))
            ws=dual_entry_phase_fixture(T;manager,diagnostics)
            options=ws.options;policy=ws.progress.numerical_policy
            @test JSimplex.primal_infeasibility(ws)==one(T)
            @test JSimplex.dual_infeasibility(ws)==zero(T)
            result=postsolve ? JSimplex.cleanup_original(ws.problem,ws.basis,options,
                JSimplex.SolveContext(time_ns(),Inf,diagnostics,policy),7,0) :
                JSimplex._solve_continuous_dual!(ws,()->false)
            @test result.status==OPTIMAL
            @test result.primal==T[1]
            @test result.objective_value==one(T)
            @test result.iterations==8
            @test observed==[:dual]
            @test ws.options===options
            @test ws.progress.numerical_policy===policy
        end
    end
end

@testset "Direct primal cleanup after dual optimization keeps native primal safeguards" begin
    for requested in (:primal,:dual), interruption in (:none,:cancel,:throw)
        injected=Ref(false);modes=Symbol[];primal_guards=Bool[]
        stopped=Ref(false);failure=ErrorException("stop direct primal cleanup")
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            if event==:pivot_completed && !injected[]
                # Model a valid working-cost shift during the dual kernel,
                # after entry has already excluded the adaptive driver path.
                injected[]=true
                ws.costs[2]=0.0;ws.perturbed=true
                ws.basis.states[2]=JSimplex.AT_LOWER
                JSimplex.recompute!(ws)
            elseif event==:pivot_proposed
                push!(modes,ws.options.algorithm)
                if injected[]
                    push!(primal_guards,JSimplex._native_phase_transfer_enabled(ws))
                    interruption==:cancel && (stopped[]=true)
                    interruption==:throw && throw(failure)
                end
            end
        end)
        p=LinearProblem(sparse([1.0 0.0]),[1.0,-1.0];row_lower=[1.0],column_upper=[Inf,1.0])
        options=SolverOptions(algorithm=requested,verbose=false,scaling=:off,presolve=false)
        policy=JSimplex.NumericalPolicy(Float64)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
        result=try JSimplex._solve_continuous_dual!(ws,()->stopped[]) catch e; e end
        @test injected[]
        if interruption==:throw
            @test result isa JSimplex.DiagnosticObserverFailure
            @test result.cause===failure
        elseif interruption==:cancel
            @test result.status==TIME_LIMIT
            @test result.iterations==1
        else
            @test result.status==OPTIMAL
            @test result.primal==[1.0,1.0]
            @test result.objective_value==0.0
        end
        @test modes==[:dual,:primal]
        @test primal_guards==[true]
        @test ws.options===options
    end
end

@testset "Dual entry preserves budgets and restores options on interruption" begin
    ws=dual_entry_phase_fixture(Float64;limit=7);options=ws.options
    limited=JSimplex._solve_continuous_dual!(ws,()->false)
    @test limited.status==ITERATION_LIMIT
    @test limited.iterations==7
    @test ws.options===options
    ws=dual_entry_phase_fixture(Float64);options=ws.options
    stopped=JSimplex._solve_continuous_dual!(ws,()->true)
    @test stopped.status==TIME_LIMIT
    @test stopped.iterations==7
    @test ws.options===options
    for failure in (ErrorException("stop dual entry"),JSimplex.SingularException(29))
        ws=dual_entry_phase_fixture(Float64);options=ws.options
        caught=try JSimplex._solve_continuous_dual!(ws,()->throw(failure)) catch e; e end
        @test caught===failure
        @test ws.options===options
        observed=Symbol[]
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            if event==:phase_dual
                push!(observed,ws.options.algorithm)
                throw(failure)
            end
        end)
        ws=dual_entry_phase_fixture(Float64;diagnostics);options=ws.options
        caught=try JSimplex._solve_continuous_dual!(ws,()->false) catch e; e end
        @test caught isa JSimplex.DiagnosticObserverFailure
        @test caught.cause===failure
        @test observed==[:dual]
        @test ws.options===options
    end
end
