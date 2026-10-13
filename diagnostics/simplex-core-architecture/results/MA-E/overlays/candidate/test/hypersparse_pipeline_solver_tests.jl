@testset "Both simplex algorithms certify block sparse LPs with the pipeline" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        algorithm in (:primal,:dual),pricing in (:dantzig,:devex,:steepest_edge)
        n = 24
        A = spdiagm(0=>ones(T,n),1=>T[isodd(i) ? 1//4 : 0 for i in 1:n-1])
        bound = A*ones(T,n)
        problem = algorithm == :primal ?
            LinearProblem(A,-ones(T,n);row_upper=bound) :
            LinearProblem(A,ones(T,n);row_lower=bound)
        options = SolverOptions(T;verbose=false,algorithm,pricing,basis_update=method,
            basis_refactorization=:markowitz,iteration_limit=200)
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            hypersparse=true,refactor_timing=false)
        diagnostics = JSimplex.SimplexDiagnostics(kernel_timing=true)
        ws = JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
        run = JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
        @test run.status == OPTIMAL
        @test run.primal ≈ ones(T,n)
        @test JSimplex._original_primal_feasible(ws,run.primal)
        @test JSimplex.primal_infeasibility(ws) <= options.primal_tolerance
        @test JSimplex.dual_infeasibility(ws) <= options.dual_tolerance
        @test get(diagnostics.kernel_calls,:hypersparse_ftran_sparse,0) > 0
        @test get(diagnostics.kernel_calls,:hypersparse_btran_sparse,0) > 0
        if pricing == :steepest_edge
            # Fixed-width rational primal weights are recomputed on demand;
            # their incremental transpose-weight recurrence is deliberately off.
            operation = algorithm == :primal && T !== Rational{Int64} ? :weight_btran : :weight_ftran
            @test sum(diagnostics.kernel_calls[key] for key in
                JSimplex.HYPERSPARSE_KERNEL_KEYS[findfirst(==(operation),JSimplex.HYPERSPARSE_OPERATIONS)]) > 0
        end
    end
end

@testset "Small dense and degenerate LPs retain original certificates" begin
    for algorithm in (:primal,:dual), T in (Float64,Rational{BigInt})
        problems = (
            LinearProblem(sparse(T[1 2;3 1]),T[-2,-1];row_upper=T[4,5]),
            LinearProblem(spdiagm(0=>ones(T,4),1=>-ones(T,3)),T[-1,0,0,0];row_upper=T[0,0,0,1]),
            LinearProblem(sparse(T[1 1;1 -1]),T[1,2];row_lower=T[2,0],row_upper=T[2,0]))
        for problem in problems
            options = SolverOptions(T;verbose=false,algorithm,presolve=false,iteration_limit=200)
            policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
                hypersparse=true,refactor_timing=false)
            result = JSimplex._solve_diagnosed(problem,nothing;options,numerical_policy=policy)
            reference = solve(problem;options)
            @test result.status == reference.status == OPTIMAL
            @test result.objective_value ≈ reference.objective_value
            @test JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
        end
    end
end

@testset "BFRT cancellation and support changes preserve the entering direction" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        A = sparse(T[1 -1 0;0 0 2])
        p = LinearProblem(A,zeros(T,3);column_upper=ones(T,3))
        policy = JSimplex.NumericalPolicy(T;hypersparse=true,solve_refinement=true)
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        ws.scratch.row_solution .= T[17,19]
        JSimplex._pipeline_changed!(ws,ws.scratch.row_solution)
        @test JSimplex._apply_bound_flips!(ws,[1,2])
        @test isempty(JSimplex._pipeline_vector!(ws,ws.scratch.row_rhs).indices)
        @test ws.primal[4:5] == zeros(T,2)
        @test JSimplex._apply_bound_flips!(ws,[3])
        @test JSimplex._pipeline_vector!(ws,ws.scratch.row_rhs).indices == [2]
        @test ws.primal[4:5] == T[0,2]
        @test ws.scratch.row_solution == T[17,19]
        @test JSimplex._pipeline_state(ws.scratch.hypersparse,:bfrt).calls == 2
    end
end

@testset "Hypersparse recovery shares limits and preserves callback failures" begin
    p = LinearProblem(spdiagm(0=>ones(24)),-ones(24);row_upper=ones(24))
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,hypersparse=true,
        refactor_timing=false)
    options = SolverOptions(algorithm=:primal,verbose=false,iteration_limit=2)
    ws = JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    budget = JSimplex.SimplexRunBudget(ws)
    run = JSimplex.run_from_basis!(ws,budget,policy,()->false)
    @test run.status == ITERATION_LIMIT
    @test ws.iterations == budget.iterations == 2
    saved = (copy(ws.primal),copy(ws.basis.basic_indices),copy(ws.basis.states))
    failure = OverflowError("caller failure")
    caught = try
        JSimplex._primal_iteration!(ws,()->throw(failure),options.dual_tolerance)
        nothing
    catch error
        error
    end
    @test caught === failure
    @test saved == (ws.primal,ws.basis.basic_indices,ws.basis.states)
end
