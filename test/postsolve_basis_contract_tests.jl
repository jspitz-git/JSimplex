using Test, JSimplex, SparseArrays, LinearAlgebra

function contract_fixture(T=Float64; k=40, manager=:huangfu_hall, limit=1000)
    delta=T(1//8)
    A=spzeros(T,k+1,2k+1)
    for i in 1:k
        A[i,i]=A[i,k+i]=one(T)
    end
    A[k+1,2k+1]=one(T)
    p=LinearProblem(A,vcat(zeros(T,2k),one(T));
        row_lower=vcat(zeros(T,k),one(T)),row_upper=vcat(zeros(T,k),nothing),
        column_upper=vcat(fill(delta,2k),nothing))
    o=SolverOptions(T;basis_update=manager,verbose=false,presolve=false,
        scaling=:off,iteration_limit=limit)
    b=JSimplex.Basis(vcat(collect(1:k),3k+2),vcat(fill(JSimplex.BASIC,k),
        fill(JSimplex.AT_UPPER,k),fill(JSimplex.AT_LOWER,k+1),JSimplex.BASIC))
    target=vcat(zeros(T,k),fill(delta,k),one(T))
    return p,o,b,target
end

function contract_workspace(T=Float64;diagnostics=nothing,kwargs...)
    p,o,b,target=contract_fixture(T;kwargs...)
    w=JSimplex.initialize_workspace(p,o;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    w.basis=JSimplex.Basis(b.basic_indices,b.states)
    JSimplex.recompute!(w;refactorize=true)
    return w,target
end

@testset "Partial postsolve basis is completed before original objective" begin
    p,o,b,target=contract_fixture()
    auxiliary_starts=Ref(0)
    primal_starts=Ref(0)
    diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
        if event==:phase_dual && w.problem!==p
            auxiliary_starts[]+=1
            @test all(iszero,w.problem.objective)
            @test w.problem.A==p.A && w.problem.A!==p.A
        elseif event==:phase_primal && w.problem===p
            primal_starts[]+=1
            @test JSimplex.primal_infeasibility(w)<=o.primal_tolerance
        end
    end)
    r=JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;
        target_primal=target)
    @test r.status==OPTIMAL && r.objective_value==1
    @test JSimplex._original_primal_feasible(p,r.primal,o.primal_tolerance)
    @test auxiliary_starts[]==1
    @test primal_starts[]==1
    @test r.iterations==40
end

@testset "Projection exposes a partial basis without accepting it" begin
    @test isdefined(JSimplex,:_construct_postsolve_basis!)
    if isdefined(JSimplex,:_construct_postsolve_basis!)
        w,target=contract_workspace()
        r=JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        @test r.state==JSimplex._POSTSOLVE_PARTIAL
        @test r.exchanges==1 && w.iterations==32
        @test !JSimplex._original_primal_feasible(w.problem,w.primal[1:length(target)],w.options.primal_tolerance)
        w,target=contract_workspace(;k=1)
        r=JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        @test r.state==JSimplex._POSTSOLVE_ACCEPTED && r.exchanges==1
        w,target=contract_workspace()
        before=deepcopy(w.basis)
        r=JSimplex._construct_postsolve_basis!(w,target,()->true;repair_feasibility=true)
        @test r.state==JSimplex._POSTSOLVE_STOPPED
        @test w.basis.basic_indices==before.basic_indices && w.basis.states==before.states
        r=JSimplex._construct_postsolve_basis!(w,[NaN],()->false)
        @test r.state==JSimplex._POSTSOLVE_REJECTED
    end
end

using Test,JSimplex,SparseArrays
p=LinearProblem(sparse([1.0;;]),[0.0];row_upper=[2.0],column_upper=[1.0])
o=SolverOptions(verbose=false,presolve=false,scaling=:off)
w=JSimplex.initialize_workspace(p,o)
w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_UPPER])
JSimplex.recompute!(w;refactorize=true)
@testset "Feasible hint does not certify a different infeasible basis" begin
 @test JSimplex._original_primal_feasible(p,[1.0],o.primal_tolerance)
 @test w.primal[1]==2.0
 @test JSimplex._construct_postsolve_basis!(w,[1.0],()->false).state!=JSimplex._POSTSOLVE_ACCEPTED
 @test isnothing(JSimplex._project_postsolve_basis!(w,[1.0],()->false))
end
