using Test, JSimplex, SparseArrays

@testset "A certified bounded move is not blocked by a below-threshold pivot" begin
    for T in (Float32,Float64), strategy in (:legacy,:adaptive),
        manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), reverse in (false,true),
        violated in (false,true)
        options=SolverOptions(T;algorithm=:primal,pricing=:steepest_edge,
            basis_update=manager,simplex_strategy=strategy,verbose=false)
        tiny=options.zero_tolerance/T(100)
        width=T(1e-5)
        offset=violated ? options.primal_tolerance/T(2) : zero(T)
        problem=LinearProblem(sparse(reshape(T[tiny],1,1)),T[reverse ? 1 : -1];
            row_lower=T[reverse ? offset : -Inf],row_upper=T[reverse ? Inf : -offset],
            column_lower=T[reverse ? -width : 0],column_upper=T[reverse ? 0 : width])
        policy=JSimplex.NumericalPolicy(T)
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
        ws.basis.states[1]=reverse ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
        JSimplex.recompute!(ws)
        direction=reverse ? -one(T) : one(T)
        @test JSimplex._primal_ratio(ws,1,direction,T[-tiny])==(width,0,JSimplex.BASIC)
        before=copy(ws.basis.basic_indices)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.iterations==1
        @test ws.basis.basic_indices==before
        @test ws.primal[1]==direction*width
        @test JSimplex._legacy_primal_point_certified(ws)
    end
end

@testset "A small pivot does not permit an infeasible bound flip" begin
    for T in (Float32,Float64)
        options=SolverOptions(T;algorithm=:primal,verbose=false)
        tiny=options.zero_tolerance/T(100)
        width=T(10)*options.primal_tolerance/tiny
        problem=LinearProblem(sparse(reshape(T[tiny],1,1)),T[-1];
            row_upper=T[0],column_upper=T[width])
        ws=JSimplex.initialize_workspace(problem,options)
        @test JSimplex._primal_ratio(ws,1,one(T),T[-tiny])[2]==1
        @test JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance).status==NUMERICAL_ERROR
        @test ws.iterations==0
        @test ws.primal[1]==0
    end
end

@testset "Finite flips preserve existing pivot and policy choices" begin
    for T in (Float32,Float64)
        options=SolverOptions(T;algorithm=:primal,verbose=false)
        for factor in (T(1)/T(100),T(100))
            coefficient=options.zero_tolerance*factor
            for upper in (T(1e-5),T(Inf))
                problem=LinearProblem(sparse(reshape(T[coefficient],1,1)),T[-1];
                    row_upper=T[0],column_upper=T[upper])
                policies=(JSimplex.NumericalPolicy(T;NamedTuple{(flag,)}((true,))...)
                    for flag in (:pivot_validation,:solve_refinement,:recovery,
                                 :incremental_primal,:incremental_primal_pivots))
                for policy in policies
                    ws=JSimplex.initialize_workspace(problem,options;
                        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
                    @test JSimplex._primal_ratio(ws,1,one(T),T[-coefficient])[2]==1
                end
                if factor>one(T) || !isfinite(upper)
                    ws=JSimplex.initialize_workspace(problem,options)
                    @test JSimplex._primal_ratio(ws,1,one(T),T[-coefficient])[2]==1
                end
            end
        end
    end
end

@testset "Other scalar types keep their ratio path" begin
    for T in (BigFloat,Rational{BigInt})
        options=SolverOptions(T;algorithm=:primal,verbose=false,
            primal_tolerance=T(1//10000000),zero_tolerance=T(1//1000000000000))
        coefficient=options.zero_tolerance/T(100)
        problem=LinearProblem(sparse(reshape(T[coefficient],1,1)),T[-1];
            row_upper=T[0],column_upper=T[1//100000])
        ws=JSimplex.initialize_workspace(problem,options)
        @test JSimplex._primal_ratio(ws,1,one(T),T[-coefficient])[2]==1
    end
end
