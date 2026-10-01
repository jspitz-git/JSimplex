# Diagnose both sides of a captured direction-price disagreement independently.
using JSimplex,Serialization,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
function probe(prefix)
    ws=deserialize(prefix*"-rejected.bin");data=deserialize(prefix*"-direction.bin")
    B=JSimplex.basis_matrix(ws);cb=ws.costs[ws.basis.basic_indices]
    rhs=zeros(length(cb));JSimplex._pivot_column!(rhs,ws,data.entering)
    policy=ws.progress.numerical_policy
    function quality(x,b;transposed=false)
        JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(Float64,length(b)),B,x,b,policy,transposed)
    end
    function prices(y)
        p=similar(ws.reduced_costs);JSimplex._recompute_reduced_costs!(p,ws,y);p
    end
    dual=similar(rhs);JSimplex.transpose_solve!(dual,ws.factorization,cb)
    initial_dual=copy(dual);initial_prices=prices(dual)
    direction=copy(data.column)
    println("PREFIX ",prefix," dimensions=",size(B)," iteration=",ws.iterations," entering=",data.entering)
    println("INITIAL cached=",ws.reduced_costs[data.entering]," fresh=",initial_prices[data.entering],
        " implied=",ws.costs[data.entering]-dot(cb,direction)," BTRAN=",quality(dual,cb;transposed=true)," FTRAN=",quality(direction,rhs))
    println("BTRAN_REPAIR ",JSimplex._native_cleanup_solve!(dual,ws,B,cb,()->false;transposed=true),
        " quality=",quality(dual,cb;transposed=true)," change=",maximum(abs,dual-initial_dual)," selected_price=",prices(dual)[data.entering])
    println("FTRAN_REPAIR ",JSimplex._native_cleanup_solve!(direction,ws,B,rhs,()->false),
        " quality=",quality(direction,rhs)," change=",maximum(abs,direction-data.column),
        " implied=",ws.costs[data.entering]-dot(cb,direction))
    for (label,candidate_prices,candidate_direction) in (("old prices, repaired direction",ws.reduced_costs,direction),
        ("fresh prices, old direction",initial_prices,data.column),("repaired both",prices(dual),direction))
        saved=copy(ws.reduced_costs);copyto!(ws.reduced_costs,candidate_prices)
        println("AGREEMENT ",label," ",JSimplex._legacy_primal_direction_price_ok(ws,data.entering,candidate_direction,data.tolerance))
        copyto!(ws.reduced_costs,saved)
    end
    setprecision(BigFloat,256) do
        matrix=Matrix{BigFloat}(B)
        refdual=transpose(matrix)\BigFloat.(cb);refdirection=matrix\BigFloat.(rhs)
        refprice=BigFloat(ws.costs[data.entering])-dot(refdual,BigFloat.(rhs))
        println("REFERENCE price=",refprice," native_dual_error=",maximum(abs,BigFloat.(initial_dual)-refdual),
            " corrected_dual_error=",maximum(abs,BigFloat.(dual)-refdual),
            " native_direction_error=",maximum(abs,BigFloat.(data.column)-refdirection),
            " corrected_direction_error=",maximum(abs,BigFloat.(direction)-refdirection))
        exact_dual_residual=transpose(Rational{BigInt}.(B))*Rational{BigInt}.(dual)-Rational{BigInt}.(cb)
        println("EXACT corrected_dual=",all(iszero,exact_dual_residual))
    end
    flush(stdout)
end
foreach(probe,ARGS)
