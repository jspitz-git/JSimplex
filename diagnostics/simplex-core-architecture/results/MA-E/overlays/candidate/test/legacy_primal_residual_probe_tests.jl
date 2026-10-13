using JSimplex, Test, SparseArrays

@testset "Weak-pivot sensitivity uses finite residuals of an imperfect direction" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        target in (0, 0.5)
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=manager,pricing=:steepest_edge,verbose=false)
        small=T(1.25)*options.zero_tolerance
        problem=LinearProblem(sparse(reshape(T[small,0,1e9],3,1)),T[-1];
            row_upper=T[small*target,Inf,Inf],column_upper=T[1])
        ws=JSimplex.initialize_workspace(problem,options)
        # A tiny error in an unrelated homogeneous row has componentwise
        # backward error one. It leaves the real pivot and its correction intact.
        drift=eps(T)/T(1e9)
        ws.factorization.base=JSimplex._factorize_basis(sparse(T[-1 0 0;0 -1 drift;0 0 -1]))
        buffers=JSimplex._pivot_quality_buffers(ws)
        rhs=copy(JSimplex._pivot_column!(buffers.rhs,ws,1))
        column=zeros(T,3)
        JSimplex._ordinary_forward_solve!(column,ws.factorization,rhs)
        quality=JSimplex._compensated_solve_quality!(buffers.column,JSimplex._basis_matrix!(ws),
            column,rhs,ws.progress.numerical_policy,false)
        @test !isnothing(quality) && quality.finite && !quality.reliable
        @test quality.relative_error ≈ one(T)
        before=copy(column)
        @test JSimplex._legacy_primal_direction_pivot_ok!(ws,1,1,column,()->false)
        @test column==before
        terminal=JSimplex._primal_iteration_unchecked!(ws,()->false,options.dual_tolerance,true,false)
        @test isnothing(terminal)
        @test ws.basis.basic_indices==[1,3,4]
        @test ws.iterations==1
        @test ws.primal[1] ≈ T(target)
        @test JSimplex.primal_infeasibility(ws) <= options.primal_tolerance
        @test JSimplex._legacy_primal_row_consistent(ws,options.primal_tolerance)
        @test JSimplex._original_primal_feasible(problem,ws.primal[1:1],options.primal_tolerance)
    end
end
