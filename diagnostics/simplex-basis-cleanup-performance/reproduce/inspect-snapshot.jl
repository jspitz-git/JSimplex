using JSimplex, Serialization, LinearAlgebra
function main(path)
    println("SNAPSHOT ",path)
    data=deserialize(path)
    ws=JSimplex.initialize_workspace(data.problem,data.options)
    ws.basis=deepcopy(hasproperty(data,:prior_basis) ? data.prior_basis : data.basis)
    ws.costs .= data.costs; ws.lower .= data.lower; ws.upper .= data.upper
    ws.perturbed=data.perturbed
    JSimplex.recompute!(ws;refactorize=true)
    println("iteration=",data.iteration," fresh_dinf=",JSimplex.dual_infeasibility(ws),
        " fresh_pinf=",JSimplex.primal_infeasibility(ws))
    row,entering=data.row,data.entering
    if 1<=row<=length(ws.basis.basic_indices) && entering>0
        rhs=copy(JSimplex._pipeline_column_rhs!(ws,entering))
        direction=JSimplex.forward_solve(ws.factorization,rhs)
        unit=zeros(length(direction));unit[row]=1.0
        rho=JSimplex.transpose_solve(ws.factorization,unit)
        println("stored_forward_pivot=",data.direction[row]," stored_row_pivot=",data.tableau[entering],
            " fresh_forward_pivot=",direction[row]," fresh_row_pivot=",dot(rhs,rho),
            " stored_row_residual_ratio=",JSimplex._dual_row_residual_ratio(ws,data.rho,row),
            " fresh_row_residual_ratio=",JSimplex._dual_row_residual_ratio(ws,rho,row),
            " stored_direction_norm=",norm(data.direction,Inf)," fresh_direction_norm=",norm(direction,Inf))
        B=JSimplex.basis_matrix(ws)
        println("stored_forward_residual=",norm(B*data.direction-rhs,Inf),
            " fresh_forward_residual=",norm(B*direction-rhs,Inf))
    end
    if data.options.algorithm==:dual && JSimplex.dual_infeasibility(ws)>ws.options.dual_tolerance
        B=JSimplex.basis_matrix(ws);factor=lu(B)
        stop=()->false
        prices=JSimplex._refined_dual_prices(ws,factor,B,256,stop)
        n=size(ws.problem.A,2)
        for i in eachindex(ws.costs)
            state=ws.basis.states[i]
            state==JSimplex.BASIC && continue
            JSimplex._is_fixed(ws.lower[i],ws.upper[i]) && continue
            if !JSimplex._dual_price_feasible(state,ws.reduced_costs[i],ws.options.dual_tolerance)
                original=i<=n ? ws.problem.objective[i] : 0.0
                println("VIOLATION index=",i," state=",state," price=",ws.reduced_costs[i],
                    " refined_price=",isnothing(prices) ? nothing : prices[i],
                    " original_cost=",original," working_cost=",ws.costs[i],
                    " cost_shift=",ws.costs[i]-original)
            end
        end
    end
end
foreach(main,ARGS)
