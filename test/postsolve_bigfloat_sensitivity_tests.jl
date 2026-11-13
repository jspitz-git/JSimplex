module BigFloatProjectionTests
using JSimplex,Test,SparseArrays,LinearAlgebra
const JS=JSimplex
function fixture(bits,manager,backend;false_pivot=false,diagnostics=nothing)
    setprecision(BigFloat,bits) do
        T=BigFloat;o=SolverOptions(T;algorithm=:primal,basis_update=manager,
            basis_refactorization=backend,verbose=false,presolve=false,scaling=:off)
        small=T(1.25)*o.zero_tolerance;scale=T(2)^bits
        p=LinearProblem(sparse(reshape(T[false_pivot ? 0 : small,scale],2,1)),T[0];
            row_upper=T[0,Inf],column_upper=T[1])
        w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;diagnostics))
        if false_pivot
            f=JS._basis_factorization(sparse(T[-1 small/scale;0 -1]),o)
            w.factorization.base=f.base
        end
        p,o,w,T[1]
    end
end
@testset "BigFloat projection sensitivity across precision and backends" begin
    for bits in (64,128,240,512),manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall),
        wrong in (false,true)
        setprecision(BigFloat,bits) do
            p,o,w,target=fixture(bits,manager,:native;false_pivot=wrong)
            before=deepcopy((p.A,p.objective,w.basis.basic_indices,w.basis.states))
            cache=w.scratch.pivot_quality_cache;policy=w.progress.numerical_policy
            r=JS._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
            @test r.state==(wrong ? JS._POSTSOLVE_REJECTED : JS._POSTSOLVE_ACCEPTED)
            @test r.exchanges==(wrong ? 0 : 1)
            @test w.scratch.pivot_quality_cache===cache && w.progress.numerical_policy===policy
            @test isequal((p.A,p.objective),before[1:2]) && precision(BigFloat)==bits
            wrong && @test isequal((w.basis.basic_indices,w.basis.states),before[3:4])
            !wrong && @test JS._original_primal_feasible(p,w.primal[1:1],o.primal_tolerance)
        end
    end
    for (stored,working) in ((256,64),(64,256)),backend in (:native,:markowitz),wrong in (false,true)
        p,o,w,target=fixture(stored,:huangfu_hall,backend;false_pivot=wrong)
        old=deepcopy((p.A,p.objective,target));precisions=map(precision,p.A.nzval)
        setprecision(BigFloat,working) do
            r=JS._construct_postsolve_basis!(w,target,()->false;repair_feasibility=true)
            @test r.state==(wrong ? JS._POSTSOLVE_REJECTED : JS._POSTSOLVE_ACCEPTED)
            @test isequal(old,(p.A,p.objective,target)) && map(precision,p.A.nzval)==precisions
            @test precision(BigFloat)==working
        end
    end
end
@testset "BigFloat projection cancellation and observer exceptions" begin
    for mode in (:stop,:throw)
        setprecision(BigFloat,128) do
            cancelled=Ref(false);calls=Ref(0);exception=SingularException(933)
            diag=JS.SimplexDiagnostics(;observer=(event,w)->begin
                if event===:correction_attempt
                    calls[]+=1
                    mode===:stop ? (cancelled[]=true) : throw(exception)
                end
                nothing
            end)
            p,o,w,t=fixture(128,:huangfu_hall,:native;false_pivot=true,diagnostics=diag)
            before=deepcopy((w.basis.basic_indices,w.basis.states))
            r=try;JS._construct_postsolve_basis!(w,t,()->cancelled[];repair_feasibility=true);catch e;e;end
            @test calls[]==1
            @test mode===:stop ? r isa JS._PostsolveBasisResult && r.state==JS._POSTSOLVE_STOPPED :
                r isa JS.DiagnosticObserverFailure && r.cause===exception
            @test isequal(before,(w.basis.basic_indices,w.basis.states)) && isnothing(w.scratch.pivot_quality_cache)
        end
    end
end
end
