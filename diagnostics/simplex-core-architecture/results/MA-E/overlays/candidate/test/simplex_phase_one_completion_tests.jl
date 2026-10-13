using Test,JSimplex,SparseArrays

@testset "Phase one checks cancellation after entry recomputation" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[0.0])
    policy=JSimplex.NumericalPolicy(Float64;phase_one=true)
    ws=JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    checks=Ref(0)
    result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->(checks[]+=1;checks[]>1))
    @test result.status==TIME_LIMIT
    @test ws.iterations==0
end

@testset "Phase one solves from a violated structural basis" begin
    for T in (Float64,Rational{BigInt}),infeasible in (false,true)
        p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];column_lower=T[2,0],
            row_lower=T[2,0],row_upper=infeasible ? [Bound(T(2)),Bound{T}(nothing)] : fill(Bound{T}(nothing),2))
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true)
        options=SolverOptions(T;algorithm=:primal,verbose=false)
        basis=JSimplex.Basis([1,4],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.BASIC])
        ws=JSimplex.initialize_from_basis(p,basis,options;policy)
        budget=JSimplex.SimplexRunBudget(ws)
        phase=JSimplex.run_phase_one!(ws,budget,policy,()->false)
        @test phase.status==(infeasible ? INFEASIBLE : OPTIMAL)
        @test length(ws.basis.states)==4
        if !infeasible
            result=JSimplex.run_from_basis!(ws,budget,policy,()->false)
            @test result.status==OPTIMAL
            @test result.objective_value==T(2)
        end
    end
end

@testset "Partially feasible crash basis is extended without slack restart" begin
    for T in (Float64,Rational{BigInt})
        p=LinearProblem(sparse(reshape(T[1,1],2,1)),T[1];row_lower=T[1,2],row_upper=T[1,2])
        policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,crash=true,phase_one=true)
        d=JSimplex.SimplexDiagnostics()
        options=SolverOptions(T;algorithm=:primal,verbose=false)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        crash,expired=JSimplex._crash_workspace(ws,()->false)
        @test !expired
        @test JSimplex.event_count(d,:crash_accepted)==1
        @test !JSimplex._start_primal_feasible(crash)
        phase,map=JSimplex._phase_one_workspace(crash,policy,()->false)
        @test length(map.artificial_columns)==1
        @test JSimplex._start_primal_feasible(phase)
        result=JSimplex.run_phase_one!(crash,JSimplex.SimplexRunBudget(crash),policy,()->false)
        # Floating interval arithmetic cannot prove an exactly zero A' y
        # coefficient on an unbounded variable. Keep that proof inconclusive.
        @test result.status==(T <: Rational ? INFEASIBLE : NUMERICAL_ERROR)
        T <: AbstractFloat && @test occursin("certificate is inconclusive",result.message)
    end
end
