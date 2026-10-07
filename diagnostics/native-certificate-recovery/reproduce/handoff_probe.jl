using JSimplex, LinearAlgebra, SparseArrays, Serialization, TOML
const JS=JSimplex
function main(input,output)
    d=deserialize(input)
    ws=JS.initialize_workspace(JS._minimization_problem(d.problem),d.options)
    ws.basis=d.basis
    JS.recompute!(ws;refactorize=true)
    n=size(d.problem.A,2)
    cb=[j<=n ? d.problem.objective[j] : 0.0 for j in ws.basis.basic_indices]
    y=JS.transpose_solve(ws.factorization,cb)
    function examine(label)
        target=d.target_primal
        entry=Dict{String,Any}("stage"=>label,"primal_infeasibility"=>JS.primal_infeasibility(ws),
            "dual_infeasibility"=>JS.dual_infeasibility(ws),
            "target_feasible"=>JS._original_primal_feasible(ws.problem,target,ws.options.primal_tolerance),
            "recomputed_point_feasible"=>JS._original_primal_feasible(ws.problem,ws.primal[1:n],ws.options.primal_tolerance),
            "recomputed_basis_reliable"=>JS._recomputed_basis_reliable(ws),
            "maximum_point_difference"=>norm(ws.primal[1:n]-target,Inf),
            "target_certificate"=>JS._original_optimality_certified(ws,target))
        println(entry);flush(stdout)
        return entry
    end
    report=Dict{String,Any}("initial"=>examine("initial"))
    report["native_cleanup_recompute"]=JS._try_native_cleanup_recompute!(ws,()->false)
    report["after_repair"]=examine("after native recompute")
    projected=JS._project_postsolve_basis!(ws,d.target_primal,()->false)
    report["projection"]=isnothing(projected) ? "nothing" : string(projected)
    report["after_projection"]=examine("after projection")
    report["native_after_projection"]=JS._try_native_cleanup_recompute!(ws,()->false)
    report["after_projection_recompute"]=examine("after projection native recompute")
    ws.options=JS._phase_options(ws.options,:primal)
    report["point_correction"]=JS._try_native_primal_point_correction!(ws,()->false)
    report["after_point_correction"]=examine("after point correction")
    open(output,"w") do io;TOML.print(io,report;sorted=true);end
end
Base.invokelatest(main,ARGS...)
