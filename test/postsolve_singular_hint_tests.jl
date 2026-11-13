module PostsolveSingularHintTests
using JSimplex, Test, SparseArrays, LinearAlgebra, Logging
const JS=JSimplex


function singular_hint_fixture(manager=:huangfu_hall)
    p=LinearProblem(sparse([1.0 1.0;1.0 1.0]),[1.0,2.0];
        row_lower=[1.0,1.0],row_upper=[1.0,1.0])
    o=SolverOptions(algorithm=:dual,basis_update=manager,basis_refactorization=:native,
        pricing=:steepest_edge,refactorization_interval=240,verbose=false,
        presolve=false,scaling=:off,simplex_strategy=:legacy)
    b=JS.Basis([1,2],[JS.BASIC,JS.BASIC,JS.AT_LOWER,JS.AT_LOWER])
    p,o,b,[1.0,0.0]
end

@testset "Singular inherited hint can recover without solving from slack basis" begin
    for manager in (:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub,:pfi)
        p,o,b,target=singular_hint_fixture(manager)
        before=deepcopy((p.A,b.basic_indices,b.states))
        r=JS.cleanup_original(p,b,o,JS.SolveContext(time_ns(),Inf),17,3;target_primal=target)
        @test r.status==OPTIMAL
        if r.status==OPTIMAL
            @test r.objective_value==1.0
            @test JS._original_primal_feasible(p,r.primal,o.primal_tolerance)
        end
        @test isequal(before,(p.A,b.basic_indices,b.states))
        @test r.iterations>=17 && r.refactorizations>=3
    end
end


function hint_owner(;T=Float64,manager=:huangfu_hall,backend=:native,
                    policy=JS.NumericalPolicy(T),limit=1000,diagnostics=nothing)
    p=LinearProblem(sparse(T[1 1;1 1]),T[1,2];row_lower=T[1,1],row_upper=T[1,1])
    o=SolverOptions(T;algorithm=:dual,basis_update=manager,basis_refactorization=backend,
        pricing=:steepest_edge,verbose=false,presolve=false,scaling=:off,
        simplex_strategy=:legacy,iteration_limit=limit)
    pr=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics,
        iteration_offset=11,refactorization_offset=13)
    w=JS.initialize_workspace(p,o;progress=pr)
    w.basis=JS.Basis([1,2],[JS.BASIC,JS.BASIC,JS.AT_LOWER,JS.AT_LOWER])
    w.iterations=17;w.refactorizations=3
    w,T[1,0]
end
owned_numbers(w)=(w.basis.basic_indices,w.basis.states,w.costs,w.lower,w.upper,
    w.primal,w.reduced_costs,w.pricing_weights,w.scratch.rho)

@testset "Private hint recovery owns state but shares read-only model" begin
    for manager in (:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub,:pfi)
        owner,target=hint_owner(;manager)
        original=deepcopy(owned_numbers(owner));factor=owner.factorization
        q=JS._repair_postsolve_hint(owner,target,()->false)
        @test !isnothing(q)
        if !isnothing(q)
            @test q!==owner && q.factorization!==factor && owner.factorization===factor
            @test q.problem===owner.problem && q.problem.A===owner.problem.A
            @test all(a!==b for (a,b) in zip(owned_numbers(owner),owned_numbers(q)))
            @test isequal(original,owned_numbers(owner))
            @test q.progress===owner.progress && q.options===owner.options
            @test JS._finite_workspace(q) && JS._recomputed_basis_reliable(q)
            @test q.iterations==17 && owner.iterations==17 && owner.refactorizations==q.refactorizations
        end
    end
end

@testset "Unsupported precision, policy and backend preserve old path" begin
    for T in (Float32,BigFloat)
        w,t=hint_owner(;T);before=deepcopy(owned_numbers(w))
        @test isnothing(JS._repair_postsolve_hint(w,t,()->false))
        @test isequal(before,owned_numbers(w)) && w.refactorizations==3
    end
    for policy in (JS.NumericalPolicy(Float64;precision_boosting=true),
                   JS.NumericalPolicy(Float64;lp_refinement=true),
                   JS.NumericalPolicy(Float64;recovery=true))
        w,t=hint_owner(;policy)
        @test isnothing(JS._repair_postsolve_hint(w,t,()->false))
    end
    w,t=hint_owner(;backend=:markowitz)
    @test isnothing(JS._repair_postsolve_hint(w,t,()->false))
    w,t=hint_owner();w.lower[1]=Bound(0.25)
    @test isnothing(JS._repair_postsolve_hint(w,t,()->false))
end

@testset "Stopped and exhausted recovery cannot publish a trial" begin
    w,t=hint_owner();before=deepcopy(owned_numbers(w))
    @test isnothing(JS._repair_postsolve_hint(w,t,()->true))
    @test isequal(before,owned_numbers(w)) && w.refactorizations==3
    w,t=hint_owner(;limit=17)
    @test isnothing(JS._repair_postsolve_hint(w,t,()->false)) && w.refactorizations==3
    # Cancellation after actual refactorization retains work, not trial state.
    cancelled=Ref(false);armed=Ref(false)
    diag=JS.SimplexDiagnostics(;observer=(event,w)->begin
        armed[] && event===:refactor_other && (cancelled[]=true)
        nothing
    end)
    w,t=hint_owner(;diagnostics=diag);before=deepcopy(owned_numbers(w));f=w.factorization
    armed[]=true
    @test isnothing(JS._repair_postsolve_hint(w,t,()->cancelled[]))
    @test isequal(before,owned_numbers(w)) && w.factorization===f && w.refactorizations==4
    count=Ref(0)
    diag=JS.SimplexDiagnostics(;observer=(event,w)->(event===:postsolve_hint_attempt && (count[]+=1);nothing))
    policy=JS.NumericalPolicy(Float64;max_pivot_candidates=1)
    w,t=hint_owner(;policy,diagnostics=diag)
    @test !isnothing(JS._repair_postsolve_hint(w,t,()->false)) && count[]==1
    w,t=hint_owner();before=deepcopy(owned_numbers(w));t[1]=NaN
    @test isnothing(JS._repair_postsolve_hint(w,t,()->false)) && isequal(before,owned_numbers(w))
end

struct HintThrowingLogger <: AbstractLogger
    exception::Exception
end
Logging.min_enabled_level(::HintThrowingLogger)=Logging.Debug
Logging.shouldlog(::HintThrowingLogger,args...)=true
Logging.catch_exceptions(::HintThrowingLogger)=false
function Logging.handle_message(l::HintThrowingLogger,level,message,args...;kwargs...)
    string(message)=="Refactorizing basis" && throw(l.exception)
end
@testset "Caller numerical exceptions retain identity" begin
    for exception in (SingularException(71),ZeroPivotException(72))
        w,t=hint_owner();before=deepcopy(owned_numbers(w))
        caught=try
            JS._repair_postsolve_hint(w,t,()->throw(exception));nothing
        catch e;e;end
        @test caught===exception && isequal(before,owned_numbers(w))
        caught=try
            with_logger(HintThrowingLogger(exception)) do
                JS._repair_postsolve_hint(w,t,()->false)
            end
            nothing
        catch e;e;end
        @test caught===exception && isequal(before,owned_numbers(w))
    end
    armed=Ref(false);exception=SingularException(73)
    diag=JS.SimplexDiagnostics(;observer=(event,w)->begin
        armed[] && event===:postsolve_hint_attempt && throw(exception)
        nothing
    end)
    w,t=hint_owner(;diagnostics=diag);armed[]=true
    caught=try;JS._repair_postsolve_hint(w,t,()->false);nothing;catch e;e;end
    @test caught isa JS.DiagnosticObserverFailure && caught.cause===exception
end

@testset "A repaired factor is not an infeasibility or optimality proof" begin
    w,t=hint_owner()
    w.problem.column_upper.=[Bound(0.0),Bound(0.0)]
    w.upper[1:2].=w.problem.column_upper
    q=JS._repair_postsolve_hint(w,t,()->false)
    @test !isnothing(q)
    if !isnothing(q)
        @test JS._recomputed_basis_reliable(q)
        @test !JS._original_primal_feasible(w.problem,q.primal[1:2],w.options.primal_tolerance)
    end
end

@testset "Hint success observer can cancel before returning a trial" begin
    cancelled=Ref(false)
    diagnostics=JS.SimplexDiagnostics(;observer=(event,w)->begin
        event===:postsolve_hint_repaired && (cancelled[]=true)
        nothing
    end)
    p=LinearProblem(sparse([1.0 1.0;1.0 1.0]),[1.0,2.0];
        row_lower=[1.0,1.0],row_upper=[1.0,1.0])
    o=SolverOptions(verbose=false,presolve=false,scaling=:off)
    w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;diagnostics))
    w.basis=JS.Basis([1,2],[JS.BASIC,JS.BASIC,JS.AT_LOWER,JS.AT_LOWER])
    original=deepcopy((w.basis.basic_indices,w.basis.states,w.primal,w.costs))
    factor=w.factorization
    q=JS._repair_postsolve_hint(w,[1.0,0.0],()->cancelled[])
    @test cancelled[]
    @test isnothing(q)
    @test isequal(original,(w.basis.basic_indices,w.basis.states,w.primal,w.costs)) && w.factorization===factor
end
end
