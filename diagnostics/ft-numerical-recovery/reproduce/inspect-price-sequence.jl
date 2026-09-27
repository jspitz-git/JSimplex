# Inspect post-pivot prices and the preceding pivot on saved matrices.
# Native factors are rebuilt on this host; this is not a bitwise Windows replay.
# Usage: julia --project=. inspect-price-sequence.jl report.toml snapshot.bin ...
using JSimplex, Serialization, LinearAlgebra, TOML
report = TOML.parsefile(popfirst!(ARGS))
function inspect(path)
    data=deserialize(path)
    for key in (:run_id, :source_revision, :input_sha256, :julia, :architecture)
        @assert getproperty(data, key) == report[string(key)]
    end
    ws=JSimplex.initialize_workspace(data.problem,data.options)
    ws.basis=deepcopy(data.basis)
    ws.costs .= data.costs; ws.lower .= data.lower; ws.upper .= data.upper
    ws.perturbed=data.perturbed
    B=JSimplex.basis_matrix(ws); factor=lu(B)
    prices=JSimplex._refined_dual_prices(ws,factor,B,256,()->false)
    isnothing(prices) && error("Refinement failed")
    violations=Tuple{Float64,Int,Float64,Float64}[]
    for i in eachindex(prices)
        s=ws.basis.states[i]
        (s==JSimplex.BASIC || JSimplex._is_fixed(ws.lower[i],ws.upper[i])) && continue
        infeas=s==JSimplex.AT_LOWER ? -prices[i] : s==JSimplex.AT_UPPER ? prices[i] : abs(prices[i])
        infeas>ws.options.dual_tolerance && push!(violations,(Float64(infeas),i,Float64(prices[i]),data.prices[i]))
    end
    sort!(violations,rev=true)
    println("POST iter=",data.iteration," updates=",length(data.factorization.updates)," row=",data.row," entering=",data.entering," step=",data.last_step," violations=",length(violations)," top=",first(violations,min(5,length(violations))))
    if hasproperty(data,:prior_basis)
        ws.basis=deepcopy(data.prior_basis)
        B=JSimplex.basis_matrix(ws); factor=lu(B)
        before=JSimplex._refined_dual_prices(ws,factor,B,256,()->false)
        entering=data.entering; leaving=ws.basis.basic_indices[data.row]
        rhs=copy(JSimplex._pipeline_column_rhs!(ws,entering))
        direction=JSimplex._refined_primal_direction(factor,B,rhs,256,()->false)
        tableau=JSimplex._refined_tableau_row(ws,factor,B,data.row,256,()->false)
        println("PIVOT iter=",data.iteration," leaving=",leaving," pivot=",data.direction[data.row]," tableau=",data.tableau[entering]," refined_pivot=",Float64(direction[data.row])," refined_tableau=",Float64(tableau.tableau[entering])," before_entering_price=",Float64(before[entering])," after_leaving_price=",Float64(prices[leaving])," stored_after_leaving_price=",data.prices[leaving])
    end
    flush(stdout)
end
foreach(inspect,ARGS)
