using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "Phase one keeps removal work within the shared budget" begin
    for limit in (0,1,2),offset in (0,11)
        p=LinearProblem(sparse(reshape([1.0,1.0],2,1)),[1.0];row_lower=ones(2),row_upper=ones(2))
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
        d=JSimplex.SimplexDiagnostics()
        options=SolverOptions(;algorithm=:primal,verbose=false,iteration_limit=100)
        ws=JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;
            numerical_policy=policy,diagnostics=d,iteration_offset=offset,refactorization_offset=7))
        budget=JSimplex.SimplexRunBudget(ws);budget.iteration_limit=offset+limit
        result=JSimplex.run_phase_one!(ws,budget,policy,()->false)
        @test result.status == (limit<2 ? ITERATION_LIMIT : OPTIMAL)
        @test result.iterations == limit
        @test budget.iterations == offset+limit
        @test budget.refactorizations == ws.refactorizations+7
        @test JSimplex.event_count(d,:artificial_removed) == (limit==2 ? 1 : 0)
        @test ws.options === options
        @test length(ws.basis.states)==3
        @test ws.problem === p
    end
end

@testset "Cancellation during artificial removal preserves original workspace" begin
    for throwing in (false,true)
        p=LinearProblem(sparse(reshape([1.0,1.0],2,1)),[1.0];row_lower=ones(2),row_upper=ones(2))
        completed=Ref(false)
        d=JSimplex.SimplexDiagnostics(;observer=(reason,ws)->(reason==:artificial_removed && (completed[]=true)))
        policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
        ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        original_basis=copy(ws.basis.basic_indices);original_values=copy(ws.primal)
        budget=JSimplex.SimplexRunBudget(ws)
        failure=SingularException(913)
        stop=()->begin
            completed[] && throwing && throw(failure)
            completed[]
        end
        if throwing
            try
                JSimplex.run_phase_one!(ws,budget,policy,stop)
                @test false
            catch exception
                @test exception === failure
            end
        else
            result=JSimplex.run_phase_one!(ws,budget,policy,stop)
            @test result.status == TIME_LIMIT
        end
        @test completed[]
        @test ws.basis.basic_indices==original_basis
        @test ws.primal==original_values
        @test ws.iterations==2
        @test budget.iterations==2
        @test JSimplex._recomputed_basis_reliable(ws)
    end
end

@testset "Phase one handles nearly dependent rows and meaningful tiny prices" begin
    for T in (Float64,Rational{BigInt})
        tiny=T(1//10^9)
        delta=T(1//10^5)
        models=(
            (LinearProblem(sparse(T[1 1;1 1+delta]),T[1,2];row_lower=T[2,2+delta],row_upper=T[2,2+delta]),T(3)),
            (LinearProblem(sparse(reshape(T[tiny],1,1)),T[1];row_lower=T[1]),inv(tiny)),
            (LinearProblem(spdiagm(0=>ones(T,2)),T[1,2];column_lower=[Bound{T}(nothing),Bound{T}(nothing)],
                column_upper=[Bound(T(3)),Bound{T}(nothing)],row_lower=T[2,1],row_upper=T[2,1]),T(4)))
        for (p,objective) in models,algorithm in (:primal,:dual),presolve in (false,true)
            policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true,crash=true)
            options=SolverOptions(T;algorithm,presolve,verbose=false,scaling=:off)
            result=JSimplex._solve_diagnosed(p,nothing;options,numerical_policy=policy)
            @test result.status==OPTIMAL
            @test result.objective_value ≈ objective
        end
    end
end

@testset "Phase one preserves stored BigFloat precision" begin
    p,policy= setprecision(BigFloat,256) do
        delta=BigFloat(2)^(-180)
        p=LinearProblem(sparse(reshape(BigFloat[1,1],2,1)),BigFloat[1];
            row_lower=fill(1+delta,2),row_upper=fill(1+delta,2))
        p,JSimplex.NumericalPolicy(BigFloat;simplex_strategy=:adaptive,phase_one=true)
    end
    setprecision(BigFloat,64) do
        options=SolverOptions(BigFloat;algorithm=:primal,verbose=false)
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy)
        ws=JSimplex._initialize_crash_workspace(p,options,progress)
        result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test result.status==OPTIMAL
        @test ws.primal[1]==bound_value(p.row_lower[1])
        @test precision(ws.primal[1])>=256
        @test precision(BigFloat)==64
    end
end
