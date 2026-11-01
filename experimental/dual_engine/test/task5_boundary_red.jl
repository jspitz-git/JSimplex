using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
mutable struct LateFailureProbe
    fail::Bool
    triggered::Bool
end
struct LateFailureFactor{F}
    inner::F
    probe::LateFailureProbe
end
Base.getproperty(f::LateFailureFactor,k::Symbol)=k in (:inner,:probe) ? getfield(f,k) : getproperty(getfield(f,:inner),k)
function J.forward_solve!(out,f::LateFailureFactor,rhs)
    J.forward_solve!(out,f.inner,rhs)
    if f.probe.fail
        f.probe.triggered=true;sleep(5.05);throw(SingularException(83))
    end
    out
end
J.transpose_solve!(out,f::LateFailureFactor,rhs)=J.transpose_solve!(out,f.inner,rhs)
J.forward_solve(f::LateFailureFactor,rhs)=J.forward_solve(f.inner,rhs)
J.transpose_solve(f::LateFailureFactor,rhs)=J.transpose_solve(f.inner,rhs)
struct LateFailureHook
    probe::LateFailureProbe
end
function (h::LateFailureHook)(ws,stop)
    terminal=J._dual_optimize!(ws,stop)
    factor=LateFailureFactor(ws.factorization,h.probe)
    owned=J.SimplexWorkspace((k==:factorization ? factor : k==:iterations ? 17 : k==:refactorizations ? 9 : getfield(ws,k) for k in fieldnames(typeof(ws)))...)
    J._DualEngineHandoff(owned,terminal,true)
end
function late_boundary_case(probe,limit)
    p=J.LinearProblem(sparse(ones(1,1)),[1.];row_lower=[1.])
    o=J.SolverOptions(Float64;pricing=:devex,basis_update=:pfi,simplex_strategy=:legacy,presolve=false,scaling=:off,verbose=false,time_limit=limit)
    start=time_ns();progress=J.SimplexProgressContext(p;start_ns=start,numerical_policy=J.NumericalPolicy(Float64;crash=true))
    J._solve_continuous_dual(p,o;progress,stop_requested=J._SolveDeadline(start,limit),dual_engine=LateFailureHook(probe))
end
@testset "Task5 reviewed exception boundaries" begin
    run=J.DualRunResult{Float64}(J.NUMERICAL_ERROR,nothing,nothing,0,0,"initialization failure")
    boundary=J._DualEngineBoundary{Float64,Nothing}(nothing,nothing,true)
    @test run.status==J.NUMERICAL_ERROR
    actual=try J._dual_recover_original(boundary,nothing,run,()->false) catch ex;ex end
    @test actual===run
    # Explicit warm native lifecycle compiles identical hook/factor/clock types.
    warm=late_boundary_case(LateFailureProbe(false,false),Inf)
    @test warm.status==J.OPTIMAL
    probe=LateFailureProbe(true,false);actual=late_boundary_case(probe,5.)
    @test probe.triggered
    @test actual.status==J.TIME_LIMIT
    @test actual.iterations==17 && actual.refactorizations==9
end
