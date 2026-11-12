using Logging

@testset "Unmatchable hint retains useful exchanges with an honest count" begin
    for T in (Float32,Float64)
        p=LinearProblem(sparse(reshape(T[1,1],1,2)),zeros(T,2);
            row_lower=T[1],row_upper=T[1],column_upper=[T(2)^(-18),nothing])
        o=SolverOptions(T;verbose=false,presolve=false,scaling=:off)
        w=JSimplex.initialize_workspace(p,o);target=T[T(2)^(-21),1]
        r=JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
        @test r.state==JSimplex._POSTSOLVE_ACCEPTED && r.exchanges==1
        @test w.basis.basic_indices==[2]
        @test JSimplex._original_primal_feasible(p,w.primal[1:2],o.primal_tolerance)
    end
end

@testset "Caller propagates auxiliary observer failure without a second solve" begin
    p,o,b,target=contract_fixture()
    owner=Ref{Any}(nothing);aux=Ref(0);original_primal=Ref(0)
    exception=SingularException(79)
    diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
        if event==:phase_dual && w.problem===p
            owner[]=w
        elseif event==:phase_dual && w.problem!==p
            aux[]+=1
        elseif event==:phase_primal && w.problem===p
            original_primal[]+=1
        end
        event==:pivot_completed && w.problem!==p && w.iterations==34 && throw(exception)
    end)
    before=contract_model(p);basis=deepcopy(b)
    caught=try
        JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf,diag),0,0;target_primal=target)
        nothing
    catch e
        e
    end
    @test caught isa JSimplex.DiagnosticObserverFailure && caught.cause===exception
    @test aux[]==1 && original_primal[]==0 && owner[].iterations==34
    @test b.basic_indices==basis.basic_indices && b.states==basis.states && contract_model(p)==before
end

struct PartialBasisThrowingLogger <: AbstractLogger
    exception::Exception
end
Logging.min_enabled_level(::PartialBasisThrowingLogger)=Logging.Info
Logging.shouldlog(::PartialBasisThrowingLogger,args...)=true
Logging.catch_exceptions(::PartialBasisThrowingLogger)=false
function Logging.handle_message(logger::PartialBasisThrowingLogger,level,message,args...;kwargs...)
    startswith(string(message),"Discarding partial postsolve basis") && throw(logger.exception)
end
@testset "Failure reporting preserves caller numerical-exception identity" begin
    for exception in (SingularException(91),ZeroPivotException(92))
        p,_,b,target=contract_fixture()
        o=SolverOptions(verbose=true,presolve=false,scaling=:off)
        p.row_lower[1]=p.row_upper[1]=Bound(1.0)
        before=contract_model(p);basis=deepcopy(b)
        caught=try
            with_logger(PartialBasisThrowingLogger(exception)) do
                JSimplex.cleanup_original(p,b,o,JSimplex.SolveContext(time_ns(),Inf),0,0;target_primal=target)
            end
            nothing
        catch e
            e
        end
        @test caught===exception
        @test b.basic_indices==basis.basic_indices && b.states==basis.states && contract_model(p)==before
    end
end

@testset "Recovery keeps clock and outer retry offsets" begin
    p,o,b,target=contract_fixture()
    aux=Ref{Any}(nothing)
    diag=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
        event==:phase_dual && w.problem!==p && (aux[]=w)
    end)
    pr=JSimplex.SimplexProgressContext(p;diagnostics=diag,iteration_offset=100,refactorization_offset=50)
    w=JSimplex.initialize_workspace(p,o;progress=pr)
    w.basis=JSimplex.Basis(b.basic_indices,b.states);JSimplex.recompute!(w;refactorize=true)
    @test JSimplex._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true).state==JSimplex._POSTSOLVE_PARTIAL
    r=JSimplex._complete_postsolve_basis!(w,()->false)
    @test r.status==OPTIMAL && r.iterations==40 && w.iterations==40
    @test aux[].progress.start_ns==pr.start_ns
    @test aux[].progress.iteration_offset==100 && aux[].progress.refactorization_offset==50
    @test aux[].options.time_limit==o.time_limit && aux[].options.iteration_limit==o.iteration_limit
    before=contract_numeric(w);refs=w.refactorizations
    r=JSimplex._complete_postsolve_basis!(w,JSimplex._SolveDeadline(pr.start_ns,0.0))
    @test r.status==TIME_LIMIT && w.iterations==40 && w.refactorizations==refs && contract_numeric(w)==before
end

@testset "Boosted, refinement and staged workspaces cannot enter new recovery" begin
    w,_=contract_workspace(;k=1)
    for policy in (JSimplex.NumericalPolicy(Float64;precision_boosting=true),
                   JSimplex.NumericalPolicy(Float64;lp_refinement=true))
        p=w.problem;o=w.options
        q=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        @test !JSimplex._postsolve_partial_allowed(q)
        @test JSimplex._complete_postsolve_basis!(q,()->false).status==NUMERICAL_ERROR
    end
    staged=JSimplex._new_candidate_workspace(w)
    @test JSimplex._is_staged_workspace(staged)
    @test !JSimplex._postsolve_partial_allowed(staged)
    @test JSimplex._complete_postsolve_basis!(staged,()->false).status==NUMERICAL_ERROR
end
