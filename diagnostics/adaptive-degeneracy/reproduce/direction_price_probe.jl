# Independent selected-price diagnostics; no production continuation overrides.
using JSimplex,Serialization,LinearAlgebra,SparseArrays,TOML
BLAS.set_num_threads(1)
const PREFIX=ARGS[1]
function price_report(ws,B,dual,label)
    prices=similar(ws.reduced_costs);JSimplex._recompute_reduced_costs!(prices,ws,dual)
    quality=JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,length(dual)),B,dual,ws.costs[ws.basis.basic_indices],ws.progress.numerical_policy;transposed=true)
    exact_residual=transpose(Rational{BigInt}.(B))*Rational{BigInt}.(dual)-Rational{BigInt}.(ws.costs[ws.basis.basic_indices])
    # Raw state/sign count includes fixed variables excluded by primal pricing.
    count_improving=count(eachindex(prices)) do j
        s=ws.basis.states[j]
        (s==JSimplex.AT_LOWER && prices[j]<0) || (s==JSimplex.AT_UPPER && prices[j]>0) || (s==JSimplex.FREE_NONBASIC && !iszero(prices[j]))
    end
    println(label," quality=",quality," exact_dual=",all(iszero,exact_residual)," improving=",count_improving," minmax=",extrema(prices));flush(stdout)
    (;prices,quality,exact=all(iszero,exact_residual))
end
function main()
    ws=deserialize(PREFIX*"-rejected.bin");data=deserialize(PREFIX*"-direction.bin")
    B=JSimplex.basis_matrix(ws);cb=ws.costs[ws.basis.basic_indices]
    rhs=zeros(length(cb));JSimplex._pivot_column!(rhs,ws,data.entering)
    dual=similar(rhs);JSimplex.transpose_solve!(dual,ws.factorization,cb)
    println("STATE dimensions=",size(B)," iteration=",ws.iterations," selected=",data.entering," cached=",ws.reduced_costs[data.entering]," tolerance=",data.tolerance)
    before=price_report(ws,B,dual,"native transpose")
    println("NATIVE_CLEANUP ",JSimplex._native_cleanup_solve!(dual,ws,B,cb,()->false;transposed=true))
    after=price_report(ws,B,dual,"corrected transpose")
    println("SELECTED corrected=",after.prices[data.entering]," implied=",ws.costs[data.entering]-dot(cb,data.column))
    println("PHASE point=",JSimplex._legacy_primal_point_certified(ws)," auxiliary_objective=",dot(ws.costs,ws.primal))
    setprecision(BigFloat,256) do
        wide=transpose(Matrix{BigFloat}(B))\BigFloat.(cb)
        price=BigFloat(ws.costs[data.entering])-dot(wide,BigFloat.(rhs))
        rounded=Float64.(wide)
        reference=price_report(ws,B,rounded,"rounded independent 256-bit solve")
        println("REFERENCE selected=",price," corrected_maxerror=",maximum(abs,BigFloat.(dual)-wide))
        serialize(PREFIX*"-probe.bin",(;dual,reference=rounded,prices=after.prices))
    end
end
main()
