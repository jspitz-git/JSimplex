function driver_problem(n=1;dense=false,T=Float64)
    A=dense ? sparse(Matrix{T}(I,n,n)+fill(T(1)/T(128),n,n)) : spdiagm(0=>ones(T,n),-1=>fill(T(1)/T(16),max(n-1,0)))
    J.LinearProblem(A,ones(T,n);row_lower=ones(T,n),name=dense ? "engine-dense" : "engine-sparse")
end
driver_options(T=Float64;kwargs...)=J.SolverOptions(T;pricing=:devex,basis_update=:pfi,basis_refactorization=:native,simplex_strategy=:legacy,presolve=false,scaling=:off,verbose=false,kwargs...)
mutable struct MainHookProbe
    calls::Int
end
(p::MainHookProbe)(ws,stop)=(p.calls+=1;nothing)

struct TerminalFaultFactor{F}
    inner::F
end
Base.getproperty(f::TerminalFaultFactor,k::Symbol)=k==:inner ? getfield(f,k) : getproperty(getfield(f,:inner),k)
J.forward_solve!(out,f::TerminalFaultFactor,rhs) = J.forward_solve!(out,f.inner,rhs)
function J.transpose_solve!(out,f::TerminalFaultFactor,rhs)
    J.transpose_solve!(out,f.inner,rhs);fill!(out,0.);out
end
J.forward_solve(f::TerminalFaultFactor,rhs)=J.forward_solve(f.inner,rhs)
function J.transpose_solve(f::TerminalFaultFactor,rhs)
    out=J.transpose_solve(f.inner,rhs);fill!(out,0.);out
end
mutable struct TerminalFaultHook
    calls::Int
end
function (hook::TerminalFaultHook)(ws,stop)
    hook.calls+=1;terminal=J._dual_optimize!(ws,stop)
    factor=TerminalFaultFactor(ws.factorization)
    owned=J.SimplexWorkspace((k==:factorization ? factor : getfield(ws,k) for k in fieldnames(typeof(ws)))...)
    J._DualEngineHandoff(owned,terminal,true)
end
struct NoPayloadHook end
function (::NoPayloadHook)(ws,stop)
    ws.iterations=17;ws.refactorizations=9
    J._DualEngineHandoff(ws,J.DualTermination(J.NUMERICAL_ERROR,"deliberate unsafe handoff"),false)
end
