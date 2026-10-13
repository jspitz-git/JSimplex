function s2d_reference_price_audit(ws::JSimplex.SimplexWorkspace{T},predicted) where T
    all(i -> iszero(predicted[i]),ws.basis.basic_indices) || return false
    B = JSimplex._PriceAuditMatrix(ws.problem.A)
    values = vcat(ws.scratch.rho,predicted)
    scratch = JSimplex.SolveQualityScratch(T,length(ws.costs))
    return JSimplex.solve_quality!(scratch,B,values,ws.costs,ws.progress.numerical_policy).reliable
end
