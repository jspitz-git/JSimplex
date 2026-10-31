using Test, JSimplex, SparseArrays

# Independent equations x_i+y_i=0 (or 2delta) each need a separate pivot.
# z >= 1 supplies the useful projected column that cleanup must retain.
function postsolve_multiple_fixture(T=Float64; k=6, manager=:huangfu_hall,
                                    side=:lower, limit=100, strategy=:legacy)
    delta=T(1//8)
    rhs=side==:lower ? zero(T) : 2delta
    A=spzeros(T,k+1,2k+1)
    for i in 1:k
        A[i,i]=A[i,k+i]=one(T)
    end
    A[k+1,2k+1]=one(T)
    p=LinearProblem(A,vcat(zeros(T,2k),one(T));
        row_lower=vcat(fill(rhs,k),one(T)),row_upper=vcat(fill(rhs,k),nothing),
        column_upper=vcat(fill(delta,2k),nothing))
    o=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false,
        presolve=false,scaling=:off,iteration_limit=limit,simplex_strategy=strategy)
    b=JSimplex.Basis(vcat(collect(1:k),3k+2),vcat(fill(JSimplex.BASIC,k),
        fill(side==:lower ? JSimplex.AT_UPPER : JSimplex.AT_LOWER,k),
        fill(JSimplex.AT_LOWER,k+1),JSimplex.BASIC))
    target=vcat(fill(side==:lower ? zero(T) : delta,k),
                fill(side==:lower ? delta : zero(T),k),one(T))
    return p,o,b,target
end

function postsolve_multiple_workspace(T=Float64; diagnostics=nothing, kwargs...)
    p,o,b,target=postsolve_multiple_fixture(T;kwargs...)
    ws=JSimplex.initialize_workspace(p,o;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    k=length(b.basic_indices)-1
    # State after exchanging the final row activity for z, before repair.
    indices=copy(b.basic_indices); indices[end]=2k+1
    states=copy(b.states); states[2k+1]=JSimplex.BASIC; states[end]=JSimplex.AT_LOWER
    ws.basis=JSimplex.Basis(indices,states)
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Postsolve repairs several independent bound violations" begin
    for T in (Float32,Float64), side in (:lower,:upper),
        manager in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        p,o,b,target=postsolve_multiple_fixture(T;manager,side)
        starts=Tuple{Vector{Int},Int}[]
        diag=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            event==:phase_primal && push!(starts,(copy(ws.basis.basic_indices),
                last(JSimplex.primal_infeasibility_summary(ws))))
        end)
        r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;
            target_primal=target)
        @test r.status==OPTIMAL
        @test r.objective_value==one(T)
        @test r.primal==vcat(fill(side==:lower ? zero(T) : T(1//8),12),one(T))
        @test r.iterations==6
        @test JSimplex.event_count(diag,:phase_auxiliary)==0
        @test length(starts)==1
        @test !isempty(starts) && 13 in only(starts)[1] && only(starts)[2]==0
    end
end

@testset "Multiple-bound repair respects global and local budgets" begin
    for remaining in (0,5,6,7)
        ws=postsolve_multiple_workspace(;limit=7+remaining)
        ws.iterations=7
        options,costs,lower,upper=ws.options,ws.costs,copy(ws.lower),copy(ws.upper)
        @test JSimplex._try_postsolve_feasibility_pivot!(ws,()->false)==(remaining>=6)
        @test ws.iterations==7+min(remaining,6)
        @test ws.options===options && ws.costs===costs
        @test ws.lower==lower && ws.upper==upper
    end
    # An optional attempt must remain bounded even with many independent errors.
    ws=postsolve_multiple_workspace(;k=40,limit=1000)
    @test !JSimplex._try_postsolve_feasibility_pivot!(ws,()->false)
    @test ws.iterations==32
    @test last(JSimplex.primal_infeasibility_summary(ws))==8
end

@testset "Multiple-bound repair preserves generic arithmetic and state" begin
    for T in (BigFloat,Rational{BigInt}), strategy in (:legacy,:adaptive)
        ws=postsolve_multiple_workspace(T;manager=:pfi,strategy)
        options,costs,policy=ws.options,ws.costs,ws.progress.numerical_policy
        @test JSimplex._try_postsolve_feasibility_pivot!(ws,()->false)
        @test ws.primal[1:13]==vcat(zeros(T,12),one(T))
        @test ws.iterations==6
        @test ws.options===options && ws.costs===costs && ws.progress.numerical_policy===policy
    end
end

@testset "Multiple-bound repair restores state when interrupted mid-attempt" begin
    for action in (:stop,:throw)
        stopped=Ref(false)
        diag=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
            if event==:pivot_completed && ws.iterations==2
                action==:stop ? (stopped[]=true) : throw(JSimplex.SingularException(1))
            end
        end)
        ws=postsolve_multiple_workspace(;diagnostics=diag)
        options,costs=ws.options,ws.costs
        if action==:throw
            @test_throws JSimplex.DiagnosticObserverFailure JSimplex._try_postsolve_feasibility_pivot!(ws,()->stopped[])
        else
            @test !JSimplex._try_postsolve_feasibility_pivot!(ws,()->stopped[])
        end
        @test ws.iterations==2
        @test ws.options===options && ws.costs===costs && !ws.perturbed
        @test !any(ws.scratch.steepest_valid)
    end
    ws=postsolve_multiple_workspace()
    ws.primal[1]=NaN
    @test !JSimplex._try_postsolve_feasibility_pivot!(ws,()->false)
    @test ws.iterations==0
end
