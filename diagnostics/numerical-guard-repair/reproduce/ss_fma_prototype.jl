# Diagnostic-only arithmetic variants; production sources stay unchanged.
using JSimplex
mode=popfirst!(ARGS)
source=read(joinpath(dirname(pathof(JSimplex)),"triangular_factorization.jl"),String)
if mode in ("elimination","both")
    a=findfirst("function _eliminate_triangular_row_spike!",source).start
    b=findnext("\nfunction replace_column!",source,a).start-1
    body=replace(source[a:b],"spike[trailing] + multiplier * value"=>"fma(multiplier,value,spike[trailing])")
    Base.include_string(JSimplex,body,"diagnostic-fma-elimination")
end
if mode in ("application","both")
    @eval JSimplex @inline _compiled_row_operation!(vector,target,source,multiplier,::Val{:add}) =
        (vector[target] = fma(multiplier,vector[source],vector[target]))
    a=findfirst("function _apply_row_update!(vector::Vector, update::ForrestTomlinUpdate)",source).start
    b=findnext("\nfunction _apply_row_update!(vector::Vector, update::BartelsGolubUpdate)",source,a).start-1
    body=replace(source[a:b],"vector[last] += update.multipliers[i] * vector[update.indices[i]]"=>
        "vector[last] = fma(update.multipliers[i],vector[update.indices[i]],vector[last])",
        "vector[update.indices[i]] += update.multipliers[i] * bottom"=>
        "vector[update.indices[i]] = fma(update.multipliers[i],bottom,vector[update.indices[i]])")
    Base.include_string(JSimplex,body,"diagnostic-fma-application")
end
include("ss_replay_probe.jl")
