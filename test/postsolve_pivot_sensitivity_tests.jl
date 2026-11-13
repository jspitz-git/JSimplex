using JSimplex, Test, SparseArrays, LinearAlgebra

function postsolve_sensitivity_fixture(T,manager;real_pivot=false,diagnostics=nothing)
    o=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,verbose=false,presolve=false,scaling=:off,
        simplex_strategy=:legacy,pricing=:steepest_edge)
    small=T(1.25)*o.zero_tolerance
    p=LinearProblem(sparse(reshape(T[real_pivot ? small : 0,1e9],2,1)),zeros(T,1);
        row_upper=T[0,Inf],column_upper=T[1])
    w=JSimplex.initialize_workspace(p,o;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    if !real_pivot
        # The core primal regression uses the same below-residual-tolerance
        # factor drift. Projection must also reject its false nonzero pivot.
        drift=small/T(1e9)
        f=JSimplex._basis_factorization(sparse(T[-1 drift;0 -1]),o)
        w.factorization.base=f.base
    end
    p,o,w,T[1]
end

@testset "Postsolve rejects a sensitive false pivot before changing the basis" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
        p,o,w,target=postsolve_sensitivity_fixture(T,manager)
        before=deepcopy((w.basis.basic_indices,w.basis.states,p.A,p.objective))
        result=try
            JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        catch exception
            exception
        end
        @test result isa JSimplex._PostsolveBasisResult
        if result isa JSimplex._PostsolveBasisResult
            @test result.state==JSimplex._POSTSOLVE_REJECTED && result.exchanges==0
        end
        @test (w.basis.basic_indices,w.basis.states,p.A,p.objective)==before
        @test isempty(w.factorization.updates) && w.iterations==0
        @test JSimplex._original_primal_feasible(p,target,o.primal_tolerance)
    end
end

@testset "Postsolve still accepts accurate small pivots" begin
    for T in (Float32,Float64),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall)
        p,o,w,target=postsolve_sensitivity_fixture(T,manager;real_pivot=true)
        r=JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        @test r.state==JSimplex._POSTSOLVE_ACCEPTED && r.exchanges==1
        @test w.basis.basic_indices==[1,3]
        @test JSimplex._original_primal_feasible(p,w.primal[1:1],o.primal_tolerance)
    end
end

@testset "Postsolve pivot sensitivity preserves cancellation and observer provenance" begin
    for mode in (:stop,:throw)
        stopped=Ref(false);calls=Ref(0);exception=SingularException(991)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
            if event==:correction_attempt
                calls[]+=1
                mode==:stop ? (stopped[]=true) : throw(exception)
            end
        end)
        _,_,w,target=postsolve_sensitivity_fixture(Float64,:huangfu_hall;diagnostics)
        basis=deepcopy(w.basis)
        result=try
            JSimplex._construct_postsolve_basis!(w,target,()->stopped[];repair_feasibility=true)
        catch caught
            caught
        end
        @test calls[]==1
        if mode==:stop
            @test result isa JSimplex._PostsolveBasisResult && result.state==JSimplex._POSTSOLVE_STOPPED
        else
            @test result isa JSimplex.DiagnosticObserverFailure && result.cause===exception
        end
        @test w.basis.basic_indices==basis.basic_indices && w.basis.states==basis.states
        @test isempty(w.factorization.updates) && w.iterations==0
    end
end
