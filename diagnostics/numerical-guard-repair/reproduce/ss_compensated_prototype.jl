# Independent native compensated application of the stored row operations.
using JSimplex
@eval JSimplex begin
    const PROBE_ROW_CALLS=Ref(0)
    function _probe_compensated_operation!(v,low,target,source,multiplier)
        product=multiplier*v[source]
        product_low=fma(multiplier,v[source],-product)+multiplier*low[source]
        total=v[target]+product;part=total-v[target]
        error=(v[target]-(total-part))+(product-part)+low[target]+product_low
        high=total+error
        low[target]=error-(high-total);v[target]=high
    end
end
source=read(joinpath(dirname(pathof(JSimplex)),"triangular_rows.jl"),String)
a=findfirst("function _finish_triangular_forward!",source).start
body=source[a:end]
body=replace(body,
    "    for (target, source, multiplier) in cache.operations\n        _compiled_row_operation!(destination, target, source, multiplier, operation)\n    end"=>
    "    PROBE_ROW_CALLS[]+=1\n    low=zeros(length(destination))\n    for (target,source,multiplier) in cache.operations\n        _probe_compensated_operation!(destination,low,target,source,multiplier)\n    end\n    destination .+= low",
    "    for (target, origin, multiplier) in Iterators.reverse(cache.operations)\n        _compiled_row_operation!(source, origin, target, multiplier, operation)\n    end"=>
    "    PROBE_ROW_CALLS[]+=1\n    low=zeros(length(source))\n    for (target,origin,multiplier) in Iterators.reverse(cache.operations)\n        _probe_compensated_operation!(source,low,origin,target,multiplier)\n    end\n    source .+= low")
Base.include_string(JSimplex,body,"compensated-finish-prototype")
include("ss_replay_probe.jl")
println("COMPENSATED_CALLS ",JSimplex.PROBE_ROW_CALLS[])
@assert JSimplex.PROBE_ROW_CALLS[]>0
