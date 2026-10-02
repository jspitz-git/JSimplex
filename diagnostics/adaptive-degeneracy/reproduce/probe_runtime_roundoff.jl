# Replay the captured pivot, then test an adjacent-value point in native precision.
using JSimplex,Serialization,LinearAlgebra,SparseArrays,SHA
BLAS.set_num_threads(1)
include(joinpath(@__DIR__,"pricing_isolation.jl"))
isolate_pricing_trials!()
function main(prefix)
ws=deserialize(prefix*"-before.bin")
ws.scratch.perturbations.workspace_id=objectid(ws)
terminal=JSimplex._primal_iteration!(ws,()->false,zero(Float64))
failed=deserialize(prefix*".bin")
println("REPLAY terminal=",terminal," same_point=",isequal(ws.primal,failed.primal),
    " same_basis=",ws.basis.basic_indices==failed.basis.basic_indices)
@assert isequal(ws.primal,failed.primal)
tolerance=ws.options.primal_tolerance
for tag in ("reconstructed","prediction","correction")
    ws.primal .= tag=="reconstructed" ? failed.primal : deserialize(prefix*"-point-"*tag*".bin")
    println("CANDIDATE tag=",tag)
adjusted=0
for j in ws.basis.basic_indices
    old=ws.primal[j]
    value=JSimplex._lower_violation(ws.lower[j],old)>tolerance ? nextfloat(old) :
        JSimplex._upper_violation(ws.upper[j],old)>tolerance ? prevfloat(old) : old
    if value!=old
        println("ADJACENT index=",j," old=",old," new=",value,
            " bound_violation=",max(JSimplex._lower_violation(ws.lower[j],value),
                JSimplex._upper_violation(ws.upper[j],value)))
        adjusted+=1
        ws.primal[j]=value
    end
end
println("PROBE adjusted=",adjusted," certified=",JSimplex._legacy_primal_point_certified(ws),
    " model=",JSimplex._legacy_primal_model_feasible(ws),
    " rows=",JSimplex._legacy_primal_row_consistent(ws,tolerance))

n=size(ws.problem.A,2)
lo,hi=JSimplex._primal_row_bounds(ws.problem.A,ws.primal[1:n],Val(false))
for row in eachindex(lo)
    lower,upper=ws.lower[n+row],ws.upper[n+row]
    JSimplex._primal_interval_within_bounds(lo[row],hi[row],lower,upper,tolerance) && continue
    indices,coefficients=findnz(ws.problem.A[row,:])
    exact=sum(Rational{BigInt}(a)*Rational{BigInt}(ws.primal[j]) for (j,a) in zip(indices,coefficients))
    violation=max(isfinite(lower) ? Rational{BigInt}(JSimplex.bound_value(lower))-exact : 0//1,
        isfinite(upper) ? exact-Rational{BigInt}(JSimplex.bound_value(upper)) : 0//1)
    violation>Rational{BigInt}(tolerance) || continue
    println("MODEL_ROW row=",row," stored=",ws.primal[n+row]," exact=",Float64(exact),
        " violation=",Float64(violation)," excess=",Float64(violation-Rational{BigInt}(tolerance)),
        " lower=",lower," upper=",upper," indices=",indices," coefficients=",coefficients,
        " values=",ws.primal[indices])
end

end
end
main(only(ARGS))
