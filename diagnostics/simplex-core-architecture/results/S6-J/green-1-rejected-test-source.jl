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

# Test-only entry to transactional retry; native public entry is tested separately.
function explicit_dual_retry_test!(ws,stop_requested,retry_entries::Base.RefValue{Int})
    # Same public entry preparation and exception contract; choose retry as the
    # operation under test instead of relying on a native disagreement to enter it.
    stop=JSimplex._guard_stop_callback(stop_requested)
    stop() && return JSimplex.DualTermination(JSimplex.TIME_LIMIT,"time limit reached")
    JSimplex._prepare_auto_pricing!(ws,:dual;stop) ||
        return JSimplex.DualTermination(JSimplex.TIME_LIMIT,"time limit reached during pricing recovery")
    try
        if !JSimplex._finite_workspace(ws)
            JSimplex._recover_invalid_dse_weights!(ws,stop) || return JSimplex._numerical_failure()
            JSimplex._finite_workspace(ws) || return JSimplex._numerical_failure()
        end
        return JSimplex._measure_basis_iteration!(ws) do
            retry_entries[] += 1
            JSimplex._retry_simplex_step!(ws,stop,:dual,ws.options.dual_tolerance,false,true)
        end
    catch exception
        exception === stop.exception && rethrow()
        JSimplex._is_numerical_exception(exception) || rethrow()
        return JSimplex.DualTermination(JSimplex.NUMERICAL_ERROR,sprint(showerror,exception))
    end
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

@testset "Explicit dual retry remains bounded and unpublished" begin
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
        retry_entries=Ref(0)
        ws=duplicate_dual_column_workspace(;manager,policy,diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),copy(ws.basis.states),
                copy(ws.basis.basic_indices),ws.iterations,ws.refactorizations)
        if mode==:callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} explicit_dual_retry_test!(ws,()->cancelled[],retry_entries)
        elseif mode==:numerical_callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{SingularException} explicit_dual_retry_test!(ws,()->cancelled[],retry_entries)
        else
            terminal=explicit_dual_retry_test!(ws,()->cancelled[],retry_entries)
            @test terminal.status==(mode==:cancelled ? JSimplex.TIME_LIMIT : JSimplex.NUMERICAL_ERROR)
        end
        @test rejected[]==1
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,
                       ws.basis.basic_indices,ws.iterations,ws.refactorizations)
        @test retry_entries[]==1
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

@testset "Cancellation after explicit dual retry refresh cannot publish a pivot" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        cancelled=Ref(false)
        observer=(event,ws)->(event==:refactor_pivot && (cancelled[]=true);nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer)
        retry_entries=Ref(0)
        ws=duplicate_dual_column_workspace(;manager,diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),
                copy(ws.basis.states),copy(ws.basis.basic_indices))
        refs=ws.refactorizations
        terminal=explicit_dual_retry_test!(ws,()->cancelled[],retry_entries)
        @test terminal.status==JSimplex.TIME_LIMIT
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,ws.basis.basic_indices)
        @test ws.iterations==0
        @test ws.refactorizations==refs+1
        @test get(diagnostics.counts,:pivot_completed,0)==0
        @test get(diagnostics.counts,:bound_flipped,0)==0
        @test retry_entries[]==1
        @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
    end
end

@testset "Explicit dual retry preserves entry and successful publication" begin
    state=ws->(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),copy(ws.basis.states),
        copy(ws.basis.basic_indices),ws.iterations,ws.refactorizations,
        copy(ws.scratch.rejected_rows),copy(ws.scratch.rejected_entering),length(ws.factorization.updates))
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0])
        options=SolverOptions(;algorithm=:dual,basis_update=manager,pricing=:dantzig,verbose=false)
        fresh()=JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;diagnostics=JSimplex.SimplexDiagnostics()))
        direct=fresh();ordinary=fresh();entries=Ref(0)
        @test isnothing(explicit_dual_retry_test!(direct,()->false,entries))
        @test isnothing(JSimplex.dual_iteration!(ordinary,()->false))
        @test isequal(state(direct),state(ordinary))
        @test direct.iterations==1 && direct.primal[1]==1.0
        @test JSimplex._original_primal_feasible(direct,direct.primal[1:1])
        @test entries[]==1
        cancelled=fresh();before=state(cancelled);entries=Ref(0)
        @test explicit_dual_retry_test!(cancelled,()->true,entries).status==JSimplex.TIME_LIMIT
        @test isequal(before,state(cancelled))
        @test entries[]==0
        failed=fresh();failure=SingularException(813);entries=Ref(0)
        caught=try explicit_dual_retry_test!(failed,()->throw(failure),entries) catch e;e end
        @test caught===failure
        @test entries[]==0
        invalid=fresh();invalid.primal[1]=NaN;entries=Ref(0)
        @test explicit_dual_retry_test!(invalid,()->false,entries).status==JSimplex.NUMERICAL_ERROR
        @test invalid.iterations==0
        @test entries[]==0
    end
end
