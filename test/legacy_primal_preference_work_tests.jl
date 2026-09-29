using JSimplex,Test,SparseArrays

@testset "Weak preference work is bounded for similarly scaled columns" begin
    for columns in (16,256)
        A=sparse(vcat(fill(1e-10,1,columns),ones(1,columns)))
        problem=LinearProblem(A,-collect(Float64,columns:-1:1);
            row_upper=[0.0,Inf],column_upper=ones(columns))
        options=SolverOptions(algorithm=:primal,simplex_strategy=:adaptive,
            pricing=:steepest_edge,verbose=false)
        diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true)
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;diagnostics,
                numerical_policy=JSimplex.NumericalPolicy(Float64;adaptive_pricing=true)))
        calls=diagnostics.kernel_calls[:ftran]
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test diagnostics.kernel_calls[:ftran]-calls<=12
        @test ws.basis.basic_indices[1]==1
        @test ws.refactorizations==0
        @test isempty(ws.scratch.rejected_entering)
    end
end

@testset "Exhaustion after fresh pricing retains the refresh budget" begin
    problem=LinearProblem(sparse([1e-14 0.0;0.0 1.0;1.0 0.0]),[-2.0,1.0];
        row_upper=[0.0,1.0,Inf],column_upper=[1.0,1.0])
    options=SolverOptions(algorithm=:primal,simplex_strategy=:adaptive,
        basis_update=:pfi,pricing=:steepest_edge,verbose=false)
    ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;
                numerical_policy=JSimplex.NumericalPolicy(eltype(problem.objective);adaptive_pricing=true)))
    # Candidate 1 is deferred. Candidate 2 appears improving only in the stale
    # prices, and its spurious row-1 pivot forces a fresh factorization. Pricing
    # then exhausts the current exclusions inside the recursive retry.
    ws.reduced_costs[2]=-1.0
    ws.factorization.base=JSimplex._factorize_basis(sparse([-1.0 1.0 0.0;0.0 -1.0 0.0;0.0 0.0 -1.0]))
    JSimplex.replace_column!(ws.factorization,[1.0,0.0,0.0],1)
    terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
    @test terminal.status==NUMERICAL_ERROR
    @test ws.refactorizations==1
    @test ws.iterations==0
    @test ws.basis.basic_indices==[3,4,5]
    @test isempty(ws.scratch.rejected_entering)
end

@testset "Cancellation during preference clears exclusions" begin
    problem=LinearProblem(sparse([1e-10 -1.0;1.0 0.0]),[-2.0,-1.0];
        row_upper=[0.0,Inf],column_upper=[1.0,1.0])
    cancelled=Ref(false)
    observer=(reason,ws)->(reason==:pivot_rejected && (cancelled[]=true);nothing)
    diagnostics=JSimplex.SimplexDiagnostics(;observer)
    options=SolverOptions(algorithm=:primal,simplex_strategy=:adaptive,verbose=false)
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics,
                numerical_policy=JSimplex.NumericalPolicy(Float64;adaptive_pricing=true)))
    terminal=JSimplex._primal_iteration!(ws,()->cancelled[],options.dual_tolerance)
    @test terminal.status==TIME_LIMIT
    @test ws.iterations==0
    @test isempty(ws.scratch.rejected_entering)
    @test ws.basis.basic_indices==[3,4]
end
