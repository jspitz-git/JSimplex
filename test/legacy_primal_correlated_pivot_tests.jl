using JSimplex, Test, SparseArrays

@testset "Correlated forward and transpose errors cannot install a singular basis" begin
    for T in (Float32,Float64), update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        problem=LinearProblem(sparse(reshape(T[0,1e9],2,1)),T[-1];
            row_upper=T[0,Inf],column_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=update,pricing=:steepest_edge,verbose=false)
        ws=JSimplex.initialize_workspace(problem,options)
        # Model an error below the row residual tolerance in a freshly built
        # factor. Both solve directions agree on a false pivot above zero_tol.
        drift=T(1.25)*options.zero_tolerance/T(1e9)
        ws.factorization.base=JSimplex._factorize_basis(sparse(T[-1 drift;0 -1]))
        @test isempty(ws.factorization.updates)
        terminal=JSimplex._primal_iteration_unchecked!(ws,()->false,
            options.dual_tolerance,true,false)
        @test !isnothing(terminal)
        if !isnothing(terminal)
            @test terminal.status==NUMERICAL_ERROR
        end
        @test ws.basis.basic_indices==[2,3]
        @test ws.iterations==0
        @test ws.primal[1]==zero(T)
    end
end

@testset "Accurate small pivots in scaled columns remain usable" begin
    for T in (Float32,Float64), update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(T;algorithm=:primal,simplex_strategy=:legacy,
            basis_update=update,pricing=:steepest_edge,verbose=false)
        small=T(1.25)*options.zero_tolerance
        problem=LinearProblem(sparse(reshape(T[small,1e9],2,1)),T[-1];
            row_upper=T[0,Inf],column_upper=T[1])
        ws=JSimplex.initialize_workspace(problem,options)
        @test isnothing(JSimplex._primal_iteration!(ws,()->false,options.dual_tolerance))
        @test ws.basis.basic_indices==[1,3]
        @test ws.primal[1]==zero(T)
        @test ws.refactorizations==0
    end
end

@testset "A strong pivot does not request a direction correction" begin
    p=LinearProblem(sparse(reshape([1.0],1,1)),[-1.0];row_upper=[1.0])
    options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,verbose=false)
    diagnostics=JSimplex.SimplexDiagnostics(;kernel_timing=true)
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    calls=diagnostics.kernel_calls[:ftran]
    @test JSimplex._legacy_primal_pivot_row_ok!(ws,1,1,-1.0,()->false;column=[-1.0])
    @test diagnostics.kernel_calls[:ftran]==calls
end

@testset "Cancellation of a weak-pivot probe cannot publish the exchange" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(algorithm=:primal,basis_update=manager,
            simplex_strategy=:legacy,verbose=false)
        small=1.25options.zero_tolerance
        p=LinearProblem(sparse(reshape([small,1e9],2,1)),[-1.0];
            row_upper=[0.0,Inf],column_upper=[1.0])
        cancelled=Ref(false)
        observer=(event,ws)->(event==:correction_attempt && (cancelled[]=true);nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        ws=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;diagnostics))
        before=copy(ws.primal)
        terminal=JSimplex._primal_iteration_unchecked!(ws,()->cancelled[],options.dual_tolerance,true,false)
        @test !isnothing(terminal) && terminal.status==TIME_LIMIT
        @test ws.primal==before
        @test ws.basis.basic_indices==[2,3]
        @test isempty(ws.factorization.updates)
        @test ws.iterations==0
    end
end
