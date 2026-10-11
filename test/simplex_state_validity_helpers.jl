function state_validity_fixture(::Type{T}=Float64; rows=2, pricing=:steepest_edge,
                                diagnostics=nothing, policy=JSimplex.NumericalPolicy(T)) where T
    p=LinearProblem(spdiagm(0=>ones(T,rows)),ones(T,rows);row_lower=ones(T,rows))
    options=SolverOptions(T;algorithm=:dual,pricing,verbose=false,presolve=false,scaling=:off)
    progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy)
    return JSimplex.initialize_workspace(p,options;progress)
end
