using JSimplex,Test,SparseArrays,LinearAlgebra

function duplicate_dual_column_workspace(;strategy=:legacy,manager=:pfi,
        policy=nothing,diagnostics=nothing)
    # Independent four-row fixture: column 5 duplicates basic column 1, so
    # exchanging column 2 for column 5 has an exactly zero pivot.
    B=[0.7976562684646633 0.7976562684649653 0.0015056776313773224 0.6327753077629599;
       0.5177335268477845 0.5177335268478244 0.6443667761825296 0.6858186366935533;
       0.8652657188641331 0.8652657188642626 0.8354165933982676 0.5692906556126978;
       0.3498039507903441 0.3498039507907107 0.9287063361318404 0.8119167116587698]
    p=LinearProblem(sparse(hcat(B,B[:,1])),zeros(5);row_lower=-B[:,2],row_upper=-B[:,2])
    options=SolverOptions(algorithm=:dual,simplex_strategy=strategy,basis_update=manager,
        pricing=:dantzig,verbose=false)
    if isnothing(policy)
        adaptive=strategy==:adaptive
        policy=JSimplex.NumericalPolicy(Float64;adaptive_stalling=adaptive,
            adaptive_pricing=adaptive,adaptive_primal_perturbation=adaptive,
            adaptive_dual_perturbation=adaptive,phase_one=adaptive)
    end
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis.basic_indices .= 1:4
    ws.basis.states[1:4] .= JSimplex.BASIC
    ws.basis.states[6:9] .= JSimplex.AT_LOWER
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Dual cannot exchange a basic column for its exact duplicate" begin
    for strategy in (:legacy,:adaptive), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=duplicate_dual_column_workspace(;strategy,manager)
        @test issuccess(lu(Matrix{Rational{BigInt}}(JSimplex.basis_matrix(ws));check=false))
        @test ws.primal[2] < -0.9
        before=copy(ws.basis.basic_indices)
        terminal=JSimplex.dual_iteration!(ws,()->false)
        @test ws.basis.basic_indices == before
        @test ws.iterations == 0
        @test issuccess(lu(Matrix{Rational{BigInt}}(JSimplex.basis_matrix(ws));check=false))
        @test !isnothing(terminal) && terminal.status==JSimplex.NUMERICAL_ERROR
    end
end

@testset "Failed dual pivot recovery remains bounded and unpublished" begin
    for mode in (:exhausted,:cancelled,:callback_error,:numerical_callback_error), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        rejected=Ref(0);cancelled=Ref(false)
        observer=(event,ws)->begin
            if event==:pivot_rejected
                rejected[]+=1
                mode==:cancelled && (cancelled[]=true)
                mode==:callback_error && error("rejected pivot observer")
                mode==:numerical_callback_error && throw(SingularException(7))
            end
            nothing
        end
        policy=JSimplex.NumericalPolicy(Float64;max_pivot_candidates=mode==:cancelled ? 2 : 1,max_recovery_rounds=0)
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        ws=duplicate_dual_column_workspace(;manager,policy,diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),copy(ws.basis.states),
                copy(ws.basis.basic_indices),ws.iterations,ws.refactorizations)
        if mode==:callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} JSimplex.dual_iteration!(ws,()->cancelled[])
        elseif mode==:numerical_callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{SingularException} JSimplex.dual_iteration!(ws,()->cancelled[])
        else
            terminal=JSimplex.dual_iteration!(ws,()->cancelled[])
            @test terminal.status==(mode==:cancelled ? JSimplex.TIME_LIMIT : JSimplex.NUMERICAL_ERROR)
        end
        @test rejected[]==1
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,
                       ws.basis.basic_indices,ws.iterations,ws.refactorizations)
        @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
        @test isempty(ws.factorization.updates)
    end
end

@testset "Consistent small dual pivots retain the direct path" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        T in (BigFloat,Rational{BigInt}) && manager!=:pfi && continue
        coefficient=T(1//1000000)
        p=LinearProblem(sparse(reshape(T[coefficient],1,1)),T[0];row_lower=T[1])
        diagnostics=JSimplex.SimplexDiagnostics()
        options=SolverOptions(T;algorithm=:dual,basis_update=manager,pricing=:dantzig,verbose=false)
        ws=JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;diagnostics))
        @test isnothing(JSimplex.dual_iteration!(ws,()->false))
        @test ws.basis.basic_indices==[1]
        @test ws.primal[1]≈T(1000000)
        @test ws.refactorizations==0
        @test get(diagnostics.counts,:pivot_rejected,0)==0
        @test eltype(ws.primal)===T
    end
end

@testset "Cancellation after dual refresh cannot publish a pivot" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        cancelled=Ref(false)
        observer=(event,ws)->(event==:refactor_pivot && (cancelled[]=true);nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        ws=duplicate_dual_column_workspace(;manager,diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),
                copy(ws.basis.states),copy(ws.basis.basic_indices))
        refs=ws.refactorizations
        terminal=JSimplex.dual_iteration!(ws,()->cancelled[])
        @test terminal.status==JSimplex.TIME_LIMIT
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,ws.basis.basic_indices)
        @test ws.iterations==0
        @test ws.refactorizations==refs+1
        @test get(diagnostics.counts,:pivot_completed,0)==0
        @test get(diagnostics.counts,:bound_flipped,0)==0
        @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
    end
end
