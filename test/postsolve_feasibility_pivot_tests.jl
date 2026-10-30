using Test, JSimplex, SparseArrays

function postsolve_single_violation_fixture(T=Float64; manager=:huangfu_hall,
                                            limit=100, side=:lower)
    # Projecting z onto its implied bound repairs the second row. The inherited
    # upper-bound state of y still forces basic x=-delta in x+y=0. One feasible
    # pivot can move y to zero while retaining the useful z basis column.
    delta=T(1//100)
    rhs=side==:lower ? zero(T) : 2delta
    p=LinearProblem(sparse(T[1 1 0; 0 0 1]),T[0,0,1];
        row_lower=T[rhs,1],row_upper=[rhs,nothing],
        column_upper=[delta,delta,nothing])
    o=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false,
        presolve=false,scaling=:off,iteration_limit=limit)
    b=JSimplex.Basis([1,5],JSimplex.VariableState[
        JSimplex.BASIC,side==:lower ? JSimplex.AT_UPPER : JSimplex.AT_LOWER,JSimplex.AT_LOWER,
        JSimplex.AT_LOWER,JSimplex.BASIC])
    return p,o,b,(side==:lower ? T[0,delta,1] : T[delta,0,1])
end

@testset "Insufficient postsolve repair retains the restored-basis fallback" begin
    # Fixing x=-1 through y makes z=1 exceed its upper bound 1/2. A second
    # pivot through w could fix z, but this optional repair owns only one pivot.
    p=LinearProblem(sparse([1.0 1 0 0 0; 0 1 1 1 0; 0 0 0 0 1]),[0.0,0,0,0,1];
        row_lower=[0.0,1,1],row_upper=[0.0,1,nothing],
        column_upper=[nothing,1.0,0.5,nothing,nothing])
    o=SolverOptions(algorithm=:primal,verbose=false,presolve=false,scaling=:off)
    b=JSimplex.Basis([1,3,8],JSimplex.VariableState[
        JSimplex.BASIC,JSimplex.AT_UPPER,JSimplex.BASIC,JSimplex.AT_LOWER,
        JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.BASIC])
    target=[0.0,1,0,0,1]
    ws=JSimplex.initialize_workspace(p,o)
    ws.basis=JSimplex.Basis(b.basic_indices,b.states)
    JSimplex.recompute!(ws;refactorize=true)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,target,()->false))
    costs=ws.costs
    @test !JSimplex._try_postsolve_feasibility_pivot!(ws,()->false)
    @test ws.iterations==1
    @test JSimplex.primal_infeasibility(ws)>o.primal_tolerance
    @test ws.costs===costs
    @test ws.options===o
    starts=Vector{Int}[]
    diag=JSimplex.SimplexDiagnostics(;observer=(event,state)->begin
        event==:phase_dual && push!(starts,copy(state.basis.basic_indices))
    end)
    r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;
                               target_primal=target)
    @test r.status==OPTIMAL
    @test r.objective_value==1.0
    @test length(starts)>=2
    @test starts[1]==[1,3,5]
    @test starts[2]==b.basic_indices
    @test r.iterations>=1
end

@testset "Postsolve repairs one violation without discarding projected columns" begin
    for T in (Float32,Float64), manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        side in (:lower,:upper)
        starts=Vector{Int}[]
        diag=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            event==:phase_primal && push!(starts,copy(ws.basis.basic_indices))
        end)
        p,o,b,target=postsolve_single_violation_fixture(T;manager,side)
        saved_target=copy(target)
        r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;
                                   target_primal=target)
        @test r.status==OPTIMAL
        @test r.primal==(side==:lower ? T[0,0,1] : T[T(1//100),T(1//100),1])
        @test r.objective_value==T(1)
        @test r.iterations==1
        @test JSimplex.event_count(diag,:phase_auxiliary)==0
        @test length(starts)==1
        @test !isempty(starts) && 3 in only(starts)
        @test b.basic_indices==[1,5]
        @test target==saved_target
    end
end

@testset "Postsolve feasibility pivot respects remaining iterations" begin
    for limit in (7,8)
        p,o,b,target=postsolve_single_violation_fixture(;limit)
        diag=JSimplex.SimplexDiagnostics()
        r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),7,0;
                                   target_primal=target)
        @test r.iterations<=limit
        @test r.status==(limit==7 ? ITERATION_LIMIT : OPTIMAL)
        @test JSimplex.event_count(diag,:feasibility_recovery)==(limit==7 ? 0 : 1)
        limit==8 && (@test r.objective_value==1.0)
    end
end

@testset "Postsolve repair restores the requested algorithm and adaptive pricing" begin
    for algorithm in (:primal,:dual), strategy in (:legacy,:adaptive)
        p,_,b,target=postsolve_single_violation_fixture()
        o=SolverOptions(;algorithm,simplex_strategy=strategy,pricing=:steepest_edge,verbose=false)
        phases=Symbol[]
        diag=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            event in (:phase_primal,:phase_dual) && push!(phases,ws.options.algorithm)
        end)
        r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;
                                   target_primal=target)
        @test r.status==OPTIMAL
        @test r.objective_value==1.0
        @test r.iterations==1
        @test phases==[:dual,:primal]
    end
end

@testset "Postsolve repair restores costs and options on stop and observer failure" begin
    for action in (:success,:stop,:throw)
        stopped=Ref(false)
        diag=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            if event==:phase_dual
                action==:stop && (stopped[]=true)
                action==:throw && throw(JSimplex.SingularException(1))
            end
        end)
        p,o,b,target=postsolve_single_violation_fixture()
        ws=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;diagnostics=diag))
        ws.basis=b
        JSimplex.recompute!(ws;refactorize=true)
        @test isnothing(JSimplex._project_postsolve_basis!(ws,target,()->false))
        costs=ws.costs
        saved_costs=copy(costs)
        point=copy(ws.primal)
        if action==:throw
            @test_throws JSimplex.DiagnosticObserverFailure JSimplex._try_postsolve_feasibility_pivot!(ws,()->stopped[])
        else
            @test JSimplex._try_postsolve_feasibility_pivot!(ws,()->stopped[])==(action==:success)
        end
        @test ws.options===o
        @test ws.costs===costs
        @test ws.costs==saved_costs
        @test !ws.perturbed
        if action==:success
            @test ws.primal[1:3]==[0.0,0.0,1.0]
            @test ws.iterations==1
            @test ws.reduced_costs[5]==1.0
        else
            @test ws.iterations==0
            @test ws.primal==point
        end
    end
end
