# Fixtures and the caller regression live in postsolve_basis_contract_tests.jl.
contract_numeric(w)=deepcopy((w.basis.basic_indices,w.basis.states,w.primal,
    w.costs,w.lower,w.upper,w.reduced_costs))
contract_model(p)=deepcopy((p.A,p.objective,p.row_lower,p.row_upper,
    p.column_lower,p.column_upper,p.variable_domains))

@testset "Feasibility recovery owns its entire matrix and model" begin
    for T in (Float32,Float64)
        p,_,_,_=contract_fixture(T;k=1)
        before=contract_model(p)
        q=JSimplex._postsolve_feasibility_problem(p)
        @test q.A==p.A && q.A!==p.A
        for field in (:colptr,:rowval,:nzval)
            @test !Base.mightalias(getfield(q.A,field),getfield(p.A,field))
        end
        for field in (:objective,:row_lower,:row_upper,:column_lower,:column_upper,:variable_domains,:row_names,:column_names)
            @test getfield(q,field)!==getfield(p,field)
        end
        q.A.nzval[1]=T(7)
        q.row_lower[1]=Bound(T(-3))
        @test contract_model(p)==before
    end
end

@testset "Partial recovery preserves source state across native managers" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
        w,target=contract_workspace(T;manager)
        construction=JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        @test construction.state==JSimplex._POSTSOLVE_PARTIAL && w.iterations==32
        before=contract_numeric(w);model=contract_model(w.problem)
        options,policy=w.options,w.progress.numerical_policy
        refs=w.refactorizations
        r=JSimplex._complete_postsolve_basis!(w,()->false)
        @test r.status==OPTIMAL && r.iterations==40
        @test JSimplex._original_primal_feasible(w.problem,r.primal,options.primal_tolerance)
        @test contract_numeric(w)==before && contract_model(w.problem)==model
        @test w.options===options && w.progress.numerical_policy===policy
        @test w.iterations==r.iterations && w.refactorizations==r.refactorizations>refs
        @test !Base.mightalias(r.primal,w.primal)
        @test !Base.mightalias(r.basis.basic_indices,w.basis.basic_indices)
    end
end

@testset "Owned recovery charges failed work and preserves cancellation" begin
    for action in (:limit,:stop,:throw)
        flag=Ref(false);seen=Ref(0);captured=Ref{Any}(nothing)
        diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
            # Independent model identity is known before recovery is invoked.
            if event==:phase_dual && all(iszero,w.problem.objective)
                seen[]+=1;captured[]=w
            end
            if captured[]===w && event==:pivot_completed && w.iterations==34
                action==:stop && (flag[]=true)
                action==:throw && throw(SingularException(77))
            end
        end)
        w,target=contract_workspace(;diagnostics=diag,limit=action==:limit ? 34 : 1000)
        @test JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true).state==JSimplex._POSTSOLVE_PARTIAL
        before=contract_numeric(w);model=contract_model(w.problem);refs=w.refactorizations
        if action==:throw
            caught=try JSimplex._complete_postsolve_basis!(w,()->flag[]);nothing;catch exception;exception;end
            @test caught isa JSimplex.DiagnosticObserverFailure
            @test caught.cause isa SingularException && caught.cause.info==77
        else
            r=JSimplex._complete_postsolve_basis!(w,()->flag[])
            @test r.status==(action==:limit ? ITERATION_LIMIT : TIME_LIMIT)
            @test isnothing(r.primal) && isnothing(r.objective_value)
        end
        @test seen[]==1 && w.iterations==34 && w.refactorizations>refs
        @test contract_numeric(w)==before && contract_model(w.problem)==model
    end
    w,_=contract_workspace();before=contract_numeric(w)
    r=JSimplex._complete_postsolve_basis!(w,()->true)
    @test r.status==TIME_LIMIT && w.iterations==0 && contract_numeric(w)==before
    exception=SingularException(71)
    caught=try JSimplex._complete_postsolve_basis!(w,()->throw(exception));nothing;catch e;e;end
    @test caught===exception && contract_numeric(w)==before
end

@testset "Caller spends the shared budget without restarting feasibility" begin
    for limit in (32,34),T in (Float32,Float64)
        p,o,b,target=contract_fixture(T;limit)
        aux=Ref(0);original_primal=Ref(0)
        diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
            event==:phase_dual && w.problem!==p && (aux[]+=1)
            event==:phase_primal && w.problem===p && (original_primal[]+=1)
        end)
        before=deepcopy((b.basic_indices,b.states));model=contract_model(p)
        r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;target_primal=target)
        @test r.status==ITERATION_LIMIT && r.iterations==limit
        @test isnothing(r.primal) && isnothing(r.objective_value)
        @test aux[]==(limit>32 ? 1 : 0) && original_primal[]==0
        @test (b.basic_indices,b.states)==before && contract_model(p)==model
    end
end

@testset "Infeasible auxiliary falls back once to inherited basis" begin
    p,o,b,target=contract_fixture(;k=40)
    # A genuine infeasible original equation, not a mocked recovery result.
    p.row_lower[1]=p.row_upper[1]=Bound(1.0)
    aux=Ref(0);fallback=Ref(false);charged=Ref(0)
    diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
        if event==:phase_dual && w.problem!==p
            aux[]+=1;charged[]=w.iterations
        elseif event==:phase_dual && w.problem===p && aux[]>0
            fallback[]=true
            @test w.basis.basic_indices==b.basic_indices && w.basis.states==b.states
            @test w.iterations>=charged[]
        end
    end)
    model=contract_model(p);basis=deepcopy(b)
    r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),7,2;target_primal=target)
    @test r.status!=OPTIMAL && isnothing(r.primal)
    @test aux[]==1 && fallback[]
    @test r.iterations>=charged[]>=7 && r.refactorizations>=2
    @test contract_model(p)==model && b.basic_indices==basis.basic_indices && b.states==basis.states
end

@testset "New recovery does not enable unsupported policies" begin
    for T in (Float64,BigFloat,Rational{BigInt}),strategy in (:legacy,:adaptive)
        w,target=contract_workspace(T;k=1)
        o=w.options
        w.options=SolverOptions(T;basis_update=:huangfu_hall,verbose=false,presolve=false,scaling=:off,simplex_strategy=strategy)
        before=contract_numeric(w)
        if T!=Float64 || strategy!=:legacy
            @test !JSimplex._postsolve_partial_allowed(w)
            @test JSimplex._complete_postsolve_basis!(w,()->false).status==NUMERICAL_ERROR
            @test contract_numeric(w)==before && w.iterations==0
        end
    end
    w,_=contract_workspace(;k=1)
    w=JSimplex.initialize_workspace(w.problem,w.options;progress=JSimplex.SimplexProgressContext(
        w.problem;numerical_policy=JSimplex.NumericalPolicy(Float64;numerical_profile=:checked)))
    @test !JSimplex._postsolve_partial_allowed(w)
end
