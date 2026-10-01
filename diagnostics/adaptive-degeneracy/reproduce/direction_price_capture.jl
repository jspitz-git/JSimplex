# Observe failed direction-price agreement without changing candidate selection.
path=joinpath(@__DIR__,"broad_corpus.jl")
Base.include_string(Main,first(split(read(path,String),"\nhashes=instrument!()")),path)
const PRICE_PREFIX=ARGS[4]
const PRICE_FAILURES=Dict{String,Any}[]
function capture_price_failure(ws,entering,column,tolerance)
    implied=ws.costs[entering]-dot(ws.costs[ws.basis.basic_indices],column)
    record=Dict{String,Any}("iteration"=>ws.iterations,"entering"=>entering,
        "cached"=>ws.reduced_costs[entering],"implied_dot"=>implied,"price_tolerance"=>tolerance,
        "basis_updates"=>length(ws.factorization.updates),"direction_norm"=>maximum(abs,column),
        "nonzero_basic_costs"=>count(!iszero,ws.costs[ws.basis.basic_indices]))
    push!(PRICE_FAILURES,record)
    # A final-state snapshot and direction survive even if candidate rejection
    # subsequently refactorizes the live workspace or overwrites its scratch.
    detach(ws,PRICE_PREFIX*"-rejected.bin")
    serialize(PRICE_PREFIX*"-direction.bin",(;entering,column=copy(column),tolerance))
    open(PRICE_PREFIX*"-prices.toml","w") do io;TOML.print(io,Dict("failures"=>PRICE_FAILURES));end
    println("PRICE_REJECT ",record);flush(stdout)
    nothing
end
hashes=instrument!()
source=read(joinpath(dirname(pathof(JSimplex)),"legacy_primal_pivot.jl"),String)
a=first(findfirst("function _legacy_primal_direction_price_ok",source))
boundary=findnext("\n# Repair only a demonstrated native BTRAN",source,a)
isnothing(boundary) && (boundary=findnext("\n# A forward residual",source,a))
b=first(boundary)-1
body=source[a:b]
body=replace(body,"function _legacy_primal_direction_price_ok"=>"function _diagnostic_original_direction_price_ok")
Base.include_string(JSimplex,body,"diagnostic_original_direction_price.jl")
Base.include_string(JSimplex,"""
function _legacy_primal_direction_price_ok(ws::SimplexWorkspace{T},entering::Int,column::Vector{T},tolerance::T) where {T<:Union{Float32,Float64}}
    result=_diagnostic_original_direction_price_ok(ws,entering,column,tolerance)
    result || Main.capture_price_failure(ws,entering,column,tolerance)
    return result
end
""","diagnostic_capture_direction_price.jl")
Base.invokelatest(main,ARGS,hashes)
