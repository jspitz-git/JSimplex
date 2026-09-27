using JSimplex,Test,SparseArrays
@testset "Refactorization preserves unrelated steepest-edge weights" begin
    for columns in (16,256)
        A=spzeros(2,columns);A[2,:].=1.0
        problem=LinearProblem(A,-collect(Float64,columns:-1:1);row_upper=[0.0,1.0])
        options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,
            basis_update=:bartels_golub,pricing=:steepest_edge,refactorization_interval=80,verbose=false)
        diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true)
        ws=JSimplex.initialize_workspace(problem,options;
            progress=JSimplex.SimplexProgressContext(problem;diagnostics))
        ws.factorization.base=JSimplex._factorize_basis(sparse([-1.0 1.0;0.0 -1.0]))
        JSimplex.replace_column!(ws.factorization,[1.0,0.0],1)
        before=diagnostics.kernel_calls[:ftran]
        terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
        calls=diagnostics.kernel_calls[:ftran]-before
        @test isnothing(terminal)
        @test ws.primal[1]≈1.0
        @test all(iszero,ws.primal[2:columns])
        @test ws.refactorizations==1
        @test JSimplex.event_count(diagnostics,:refactor_residual)==1
        @test calls<=12
    end
end

@testset "Retry preserves usable estimates on a non-unit basis" begin
    columns=32
    A=spzeros(2,columns+1);A[1,1]=2.0;A[2,2:end].=1.0
    problem=LinearProblem(A,[0.0;-collect(Float64,columns:-1:1)];row_upper=[0.0,1.0])
    options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,
        basis_update=:pfi,pricing=:steepest_edge,refactorization_interval=80,verbose=false)
    diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true)
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;diagnostics))
    ws.basis.basic_indices[1]=1;ws.basis.states[1]=JSimplex.BASIC
    ws.basis.states[columns+2]=JSimplex.AT_UPPER
    JSimplex.recompute!(ws;refactorize=true);ws.refactorizations=0
    # Deliberately inaccurate but positive estimates remain useful for choosing
    # a candidate. Neither feasibility nor optimality is decided by these weights.
    ws.scratch.steepest_initialized=true
    fill!(ws.scratch.steepest_valid,true)
    fill!(ws.pricing_weights,1e6);ws.pricing_weights[2]=1e-4
    ws.factorization.base=JSimplex._factorize_basis(sparse([2.0 1.0;0.0 -1.0]))
    JSimplex.replace_column!(ws.factorization,[1.0,0.0],1)
    before=diagnostics.kernel_calls[:ftran]
    terminal=JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance)
    @test isnothing(terminal)
    @test ws.primal[2]≈1.0
    @test ws.refactorizations==1
    @test diagnostics.kernel_calls[:ftran]-before<=12
    @test JSimplex._original_primal_feasible(problem,ws.primal[1:columns+1],options.primal_tolerance)
    @test JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance).status==OPTIMAL
end
