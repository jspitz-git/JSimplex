function driver_problem(n=1;dense=false,T=Float64)
    A=dense ? sparse(Matrix{T}(I,n,n)+fill(T(1)/T(128),n,n)) : spdiagm(0=>ones(T,n),-1=>fill(T(1)/T(16),max(n-1,0)))
    J.LinearProblem(A,ones(T,n);row_lower=ones(T,n),name=dense ? "engine-dense" : "engine-sparse")
end
driver_options(T=Float64;kwargs...)=J.SolverOptions(T;pricing=:devex,basis_update=:pfi,basis_refactorization=:native,simplex_strategy=:legacy,presolve=false,scaling=:off,verbose=false,kwargs...)
mutable struct MainHookProbe
    calls::Int
end
(p::MainHookProbe)(ws,stop)=(p.calls+=1;nothing)
