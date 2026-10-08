using JSimplex,Serialization,TOML,LinearAlgebra
const JS=JSimplex
function main(before_path,after_path,output)
    a,b=deserialize(before_path),deserialize(after_path)
    @assert a.basis.basic_indices==b.basis.basic_indices && a.basis.states==b.basis.states
    artificial=findall(!iszero,a.problem.objective)
    violations(x)=sort([(index=j,value=x[j],violation=max(JS._lower_violation(b.lower[j],x[j]),JS._upper_violation(b.upper[j],x[j]))) for j in eachindex(x)];by=x->x.violation,rev=true)[1:10]
    ws=JS.initialize_workspace(b.problem,b.options)
    ws.basis=deepcopy(b.basis); ws.lower=copy(b.lower);ws.upper=copy(b.upper);ws.costs=copy(b.costs)
    JS.recompute!(ws;refactorize=true)
    fresh=copy(ws.primal)
    function examine(x)
        ws.primal.=x
        Dict("primal_infeasibility"=>JS.primal_infeasibility(ws),
            "point_certified"=>JS._legacy_primal_point_certified(ws),
            "row_consistent"=>JS._legacy_primal_row_consistent(ws,ws.options.primal_tolerance),
            "model_feasible"=>JS._legacy_primal_model_feasible(ws),
            "artificial_sum"=>sum(x[artificial]),"artificial_min"=>minimum(x[artificial]),
            "artificial_max"=>maximum(x[artificial]),
            "violations"=>[Dict("index"=>v.index,"value"=>v.value,"violation"=>v.violation,"artificial"=>v.index in artificial) for v in violations(x)])
    end
    clipped=copy(a.primal);clipped[artificial].=0
    result=Dict("before"=>examine(a.primal),"after"=>examine(b.primal),"clipped_before"=>examine(clipped),
        "point_change_inf"=>norm(a.primal-b.primal,Inf),"artificial_count"=>length(artificial),
        "basis_same"=>true,"fresh_reconstruction"=>examine(fresh))
    open(output,"w") do io;TOML.print(io,result;sorted=true);end
    println(result)
end
Base.invokelatest(main,ARGS...)
